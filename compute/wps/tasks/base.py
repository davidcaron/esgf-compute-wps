#! /usr/bin/env python

import json
from functools import partial

import celery
from celery import shared_task
from celery.utils.log import get_task_logger

from wps import models
from wps import WPSError

logger = get_task_logger('wps.tasks.base')

__ALL__ = [
    'FAILURE',
    'RETRY',
    'SUCCESS',
    'ALL',
    'REGISTRY',
    'get_process',
    'register_process',
    'CWTBaseTask',
    'cwt_shared_task',
]

FAILURE = 1
RETRY = 2
SUCCESS = 4
ALL = FAILURE | RETRY | SUCCESS

REGISTRY = {}

class AccessError(WPSError):
    def __init__(self, url, reason):
        msg = 'Error accessing "{url}": {reason}'

        super(AccessError, self).__init__(msg, url=url, reason=reason)

class MissingJobError(WPSError):
    def __init__(self, job_id):
        msg = 'Error job with id "{id}" does not exist'

        super(MissingJobError, self).__init__(msg, job_id=job_id)

def get_process(identifier):
    try:
        return REGISTRY[identifier]
    except KeyError as e:
        raise WPSError('Missing process "{identifier}"', identifier=identifier)

def register_process(identifier, abstract=None):
    if abstract is None:
        abstract = ''

    def wrapper(func):
        REGISTRY[identifier] = func

        func.IDENTIFIER = identifier

        func.ABSTRACT = abstract

        return func
    
    return wrapper

class CWTBaseTask(celery.Task):
    def __can_publish(self, pub_type):
        publish = getattr(self, 'PUBLISH', None)

        if publish is None:
            return False

        return (publish & pub_type) > 0

    def __get_job(self, **kwargs):
        try:
            job = models.Job.objects.get(kwargs['job_id'])
        except (models.Job.DoesNotExist, KeyError) as e:
            if isinstance(e, KeyError):
                logger.exception('Job ID was not passed to the process')
            else:
                logger.exception('Job "{id}" does not exist'.format(job_id=kwargs.get('job_id')))

            return None
        else:
            return job

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        if not self.__can_publish(RETRY):
            return

        job = self.__get_job(**kwargs)

        if job is not None:
            job.retry(exc)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        if not self.__can_publish(FAILURE):
            return

        job = self.__get_job(**kwargs)

        if job is not None:
            job.failed(str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        if not self.__can_publish(SUCCESS):
            return

        job = self.__get_job(**kwargs)

        if job is not None:
            job.succeeded(json.dumps(retval.values()[0]))

cwt_shared_task = partial(shared_task,
                          bind=True,
                          base=CWTBaseTask,
                          autoretry_for=(AccessError,),
                          retry_kwargs={'max_retries': 3})
