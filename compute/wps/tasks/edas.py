#! /usr/bin/env python

import shutil
from xml.etree import ElementTree as ET

import cdms2
import cwt
import zmq
from celery.utils.log import get_task_logger

from wps import settings
from wps import processes

logger = get_task_logger('wps.tasks.edas')

def check_exceptions(data):
    if '<exceptions>' in data:
        index = data.index('!')

        data = data[index+1:]

        root = ET.fromstring(data)

        exceptions = root.findall('./exceptions/*')

        if len(exceptions) > 0:
            raise Exception(exceptions[0].text)

def initialize_socket(context, socket_type, host, port):
    sock = context.socket(socket_type)

    sock.connect('tcp://{}:{}'.format(host, port))

    return sock

def listen_edas_output(poller, job):
    edas_output_path = None

    job.update_status('Listening for EDAS status')

    while True:
        events = dict(poller.poll(settings.EDAS_TIMEOUT * 1000))

        if len(events) == 0:
            raise Exception('EDAS timed out')

        data = events.keys()[0].recv()

        check_exceptions(data)

        parts = data.split('!')

        if 'file' in parts:
            sub_parts = parts[-1].split('|')

            edas_output_path = sub_parts[-1]

            break
        elif 'response' in parts:
            job.update_status('EDAS heartbeat')
        
    job.update_status('Received success from EDAS backend')

    return edas_output_path

@processes.cwt_shared_task()
def edas_submit(self, data_inputs, identifier, **kwargs):
    self.PUBLISH = processes.ALL

    req_sock = None

    sub_sock = None

    edas_output_path = None

    user, job = self.initialize(kwargs.get('user_id'), kwargs.get('job_id'), credentials=False)

    context = zmq.Context.instance()

    try:
        req_sock = initialize_socket(context, zmq.REQ, settings.EDAS_HOST, settings.EDAS_REQ_PORT)

        sub_sock = initialize_socket(context, zmq.SUB, settings.EDAS_HOST, settings.EDAS_RES_PORT)

        sub_sock.setsockopt(zmq.SUBSCRIBE, b'{}'.format(job.id))

        poller = zmq.Poller()

        poller.register(sub_sock)

        extra = '{"response":"file"}'

        req_sock.send(str('{}!execute!{}!{}!{}'.format(job.id, identifier, data_inputs, extra)))

        job.update_status('Sent requested to EDAS backend')

        data = req_sock.recv()

        check_exceptions(data)

        edas_output_path = listen_edas_output(poller, job)

        if edas_output_path is None:
            raise Exception('Failed to receive output from EDAS')
    except:
        raise
    finally:
        if req_sock is not None:
            req_sock.close()

        if sub_sock is not None:
            poller.unregister(sub_sock)

            sub_sock.close()
            
    output_path = self.generate_output_path()

    shutil.move(edas_output_path, output_path)

    output_url = self.generate_output_url(output_path)

    var_name = None

    try:
        with cdms2.open(output_path) as infile:
            var_name = infile.variables.keys()[0]
    except:
        raise Exception('Error with accessing EDAS output file')

    output_var = cwt.Variable(output_url, var_name)

    return output_var.parameterize()
