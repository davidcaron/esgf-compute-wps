#! /usr/bin/env python

import json
import re
import signal
from functools import partial
from contextlib import contextmanager

import cdms2
import celery
import cwt
from celery import shared_task
from celery.utils.log import get_task_logger

from wps import models
from wps import AccessError
from wps import WPSError
from wps.tasks import credentials

logger = get_task_logger('wps.tasks.base')

REGISTRY = {}

def get_process(identifier):
    try:
        return REGISTRY[identifier]
    except KeyError as e:
        raise WPSError('Missing process "{identifier}"', identifier=identifier)

def register_process(identifier, **kwargs):
    def wrapper(func):
        REGISTRY[identifier] = func

        func.IDENTIFIER = identifier

        func.ABSTRACT = kwargs.get('abstract', '')

        func.INPUT = kwargs.get('data_inputs')

        func.OUTPUT = kwargs.get('process_outputs')

        func.PROCESS = kwargs.get('process')

        func.METADATA = kwargs.get('metadata', {})

        return func

    return wrapper

class Timeout(object):
    def __init__(self, seconds, url):
        self.seconds = seconds
        self.url = url

    def handle_timeout(self, signum, frame):
        raise AccessError(url, '')

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)
    
    def __exit__(self, exc_type, exc_value, traceback):
        signal.alarm(0)

class CWTBaseTask(celery.Task):

    def get_axis_list(self, variable):
        return variable.getAxisList()

    def get_variable(self, infile, var_name):
        return infile[var_name]

    @contextmanager
    def open(self, uri):
        with Timeout(30, uri):
            fd = cdms2.open(uri)

        try:
            yield fd
        finally:
            fd.close()

    def load_credentials(self, user_id):
        user = self.load_user(user_id)

        credentials.load_certificate(user)

        return user

    def load_user(self, user_id):
        try:
            user = models.User.objects.get(pk=user_id)
        except models.User.DoesNotExist:
            raise WPSError('User "{id}" does not exist', id=user_id)

        return user

    def load_job(self, job_id):
        try:
            job = models.Job.objects.get(pk=job_id)
        except models.Job.DoesNotExist:
            raise WPSError('Job "{id}" does not exist', id=job_id)

        return job

    def update(self, job, fmt, *args, **kwargs):
        percent = kwargs.get('percent', 0)

        message = fmt.format(*args)

        job.update(message, percent)

        logger.info('%s %r', message, percent)

    def parse_uniform_arg(self, value, default_start, default_n):
        result = re.match('^(\d\.?\d?)$|^(-?\d\.?\d?):(\d\.?\d?):(\d\.?\d?)$', value)

        if result is None:
            raise WPSError('Failed to parse uniform argument {value}', value=value)

        groups = result.groups()

        if groups[1] is None:
            delta = int(groups[0])

            default_n = default_n / delta
        else:
            default_start = int(groups[1])

            default_n = int(groups[2])

            delta = int(groups[3])

        start = default_start + (delta / 2.0)

        return start, default_n, delta

    def generate_grid(self, gridder, chunk):
        try:
            grid_type, grid_param = gridder.grid.split('~')
        except AttributeError:
            return None
        except ValueError:
            raise WPSError('Error generating grid "{name}"', name=gridder.grid)

        if grid_type.lower() == 'uniform':
            result = re.match('^(.*)x(.*)$', grid_param)

            if result is None:
                raise WPSError('Failed to parse uniform configuration from {value}', value=grid_param)

            try:
                start_lat, nlat, delta_lat = self.parse_uniform_arg(result.group(1), -90.0, 180.0)
            except WPSError:
                raise

            try:
                start_lon, nlon, delta_lon = self.parse_uniform_arg(result.group(2), 0.0, 360.0)
            except WPSError:
                raise

            grid = cdms2.createUniformGrid(start_lat, nlat, delta_lat, start_lon, nlon, delta_lon)

            logger.info('Created target uniform grid {} from lat {}:{}:{} lon {}:{}:{}'.format(
                grid.shape, start_lat, delta_lat, nlat, start_lon, delta_lon, nlon))
        else:
            try:
                nlats = int(grid_param)
            except ValueError:
                raise WPSError('Error converting gaussian parameter to an int')

            grid = cdms2.createGaussianGrid(nlats)

            logger.info('Created target gaussian grid {}'.format(grid.shape))

        target = cdms2.MV2.ones(grid.shape)

        target.setAxisList(grid.getAxisList())

        domain = {}

        for axis in chunk.getAxisList():
            if not axis.isTime():
                domain[axis.id] = (axis[0], axis[-1])

        target = target(**domain)

        return target.getGrid()

    def __get_job(self, **kwargs):
        try:
            job = models.Job.objects.get(pk=kwargs['job_id'])
        except KeyError:
            logger.exception('Job ID was not passed to the process %r', kwargs)

            return None
        except models.Job.DoesNotExist:
            logger.exception('Job "{id}" does not exist'.format(job_id=kwargs.get('job_id')))

            return None
        else:
            return job

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        job = self.__get_job(**kwargs)

        if job is not None:
            job.retry(exc)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job = self.__get_job(**kwargs)

        if job is not None:
            job.failed(str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        pass

cwt_shared_task = partial(shared_task, bind=True, base=CWTBaseTask)
