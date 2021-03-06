#! /usr/bin/env python

import collections
import datetime
import json
import re

import cdms2
import cdtime
import requests
from django.core.cache import cache
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods

from . import common
from wps import WPSError
from wps import tasks

logger = common.logger

TIME_AXIS_IDS = ('time', 't')

def retrieve_axes(user, dataset_id, query_variable, query_files):
    cache_id = '{}|{}'.format(dataset_id, query_variable)

    axes = cache.get(cache_id)

    if axes is None:
        logger.info('Dataset variable "{}" not in cache'.format(cache_id))

        query_files = sorted(query_files)

        try:
            query_files_reduced = [query_files[0], query_files[-1]]
        except IndexError:
            raise WPSError('No files associated with "{variable}" of dataset "{dataset}"', variable=query_variable, dataset=dataset_id)

        start = datetime.datetime.now()

        axes = {}

        tasks.load_certificate(user)

        logger.info('Retrieving axis range for dataset "{}"'.format(dataset_id))

        base_units = None

        for i, url in enumerate(query_files_reduced):
            try:
                logger.debug('Opening file "{}"'.format(url))

                with cdms2.open(url) as infile:
                    header = infile[query_variable]

                    if i == 0:
                        for x in header.getAxisList():
                            axis_data = {
                                'id': x.id,
                                # Need to convert start/stop to str otherwise Django JsonResponse throws up
                                'start': str(x[0]),
                                'stop': str(x[-1]),
                                'id_alt': (x.attributes.get('axis', None) or x.id).lower(),
                                'units': x.attributes.get('units', None)
                            }

                            axes[x.id] = axis_data

                            if x.isTime():
                                base_units = axis_data['units']
                    else:
                        time = header.getAxisList(axes=('time'))

                        if len(time) == 0:
                            logger.debug('No time axis to set stop value')

                            continue

                        # Convert last time value to be relative to the first files units
                        remapped_time = cdtime.reltime(time[0][-1], time[0].attributes.get('units', None))

                        remapped_time = remapped_time.torel(base_units, time[0].getCalendar())

                        old_stop = axes[time[0].id]['stop']

                        axes[time[0].id]['stop'] = remapped_time.value

                        logger.info('Extending time from "{}" to "{}"'.format(old_stop, remapped_time))
            except cdms2.CDMSError as e:
                raise WPSError('Error opening file "{url}": {error}', url=url, error=e.message)

        cache.set(cache_id, axes, 24*60*60)

        logger.debug('retrieve_axes elapsed time {}'.format(datetime.datetime.now()-start))
    else:
        logger.info('Axes for "{}" retrieved from cache'.format(cache_id))

    return axes

def search_solr(dataset_id, index_node, shard=None, query=None):
    data = cache.get(dataset_id)

    if data is None:
        logger.info('Dataset "{}" not in cache'.format(dataset_id))

        start = datetime.datetime.now()

        params = {
            'type': 'File',
            'dataset_id': dataset_id,
            'format': 'application/solr+json',
            'offset': 0,
            'limit': 8000
        }

        if query is not None and len(query.strip()) > 0:
            params['query'] = query.strip()

        if shard is not None and len(shard.strip()) > 0:
            params['shards'] = '{}/solr'.format(shard.strip())
        else:
            params['distrib'] = 'false'

        url = 'http://{}/esg-search/search'.format(index_node)

        logger.info('Requesting "{}"'.format(url))

        try:
            response = requests.get(url, params)
        except requests.ConnectionError:
            raise Exception('Connection timed out')
        except requests.RequestWPSError as e:
            raise Exception('Request failed: "{}"'.format(e))

        #with open('./data/solr_full.json', 'w') as outfile:
        #    outfile.write(response.content)

        try:
            data = json.loads(response.content)
        except:
            raise Exception('Failed to load JSON response')

        # Cache for 1 day
        cache.set(dataset_id, data, 24*60*60)

        logger.debug('search_solr elapsed time {}'.format(datetime.datetime.now()-start))
    else:
        logger.info('Dataset "{}" retrieved from cache'.format(dataset_id))

    return data['response']['docs']

def parse_solr_docs(docs):
    variables = collections.OrderedDict()

    for doc in docs:
        var = doc['variable'][0]

        for item in doc['url']:
            url, mime, urlType = item.split('|')

            if urlType.lower() == 'opendap':
                url = url.replace('.html', '')

                if var in variables:
                    variables[var]['files'].append(url)
                else:
                    variables[var] = {'id': var, 'files': [url], 'axes': None}

    return variables

@require_http_methods(['GET'])
@ensure_csrf_cookie
def search_variable(request):
    try:
        common.authentication_required(request)

        try:
            dataset_id = request.GET['dataset_id']

            index_node = request.GET['index_node']

            query_variable = request.GET['variable']
        except KeyError as e:
            raise common.MissingParameterError(name=e.message)

        shard = request.GET.get('shard', None)

        query = request.GET.get('query', None)

        docs = search_solr(dataset_id, index_node, shard, query)

        dataset_variables = parse_solr_docs(docs)

        query_files = dataset_variables[query_variable]['files']

        axes = retrieve_axes(request.user, dataset_id, query_variable, query_files)
    except WPSError as e:
        logger.exception('Error retrieving ESGF search results')

        return common.failed(e.message)
    else:
        return common.success(axes.values())

@require_http_methods(['GET'])
@ensure_csrf_cookie
def search_dataset(request):
    try:
        common.authentication_required(request)

        try:
            dataset_id = request.GET['dataset_id']

            index_node = request.GET['index_node']
        except KeyError as e:
            raise common.MissingParameterError(name=e.message)

        shard = request.GET.get('shard', None)

        query = request.GET.get('query', None)

        docs = search_solr(dataset_id, index_node, shard, query)

        dataset_variables = parse_solr_docs(docs)

        try:
            query_variable = dataset_variables.keys()[0]
        except IndexError as e:
            raise WPSError('Dataset "{dataset_id}" returned no variables', dataset_id=dataset_id)
    except WPSError as e:
        logger.exception('Error retrieving ESGF search results')

        return common.failed(e.message)
    else:
        return common.success(dataset_variables)
