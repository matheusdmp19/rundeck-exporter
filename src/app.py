from os import getenv
from time import sleep
import re
import logging

from rundeck_client import Rundeck

from prometheus_client.core import GaugeMetricFamily, REGISTRY, CounterMetricFamily
from prometheus_client import start_http_server

'''
export RUNDECK_URL='http://localhost:4440'
export RUNDECK_TOKEN='k6nz3bEMAUt9hfaQvnosjpOoVP2czGYJ'
export RUNDECK_API_VERSION=40
'''

log_level = logging.INFO
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=log_level)

# totalRandomNumber = 0

class RundeckMetricsCollector(object):
    '''Class for collect Rundeck metrics info'''

    def __init__(self):

        self.rundeck_url = getenv('RUNDECK_URL')
        self.rundeck_token = getenv('RUNDECK_TOKEN')
        self.rundeck_api_version = getenv('RUNDECK_API_VERSION')

        self.instance_address = re.findall(r'https?://([\w\d:._-]+)', self.rundeck_url)[0]
        self.default_labels = ['instance_address']
        self.default_labels_values = [self.instance_address]

        self.rd = Rundeck(self.rundeck_url, self.rundeck_token, self.rundeck_api_version)

    def collect(self):

        ''' Job scheduling information metric  '''
        jobs = self.rd.listJobs()
        for job in jobs:

            job_definition = self.rd.getJobDefinition(job['id'])

            job_exported = {}
            job_exported['name'] = job['name']
            job_exported['id'] = job['id']
            job_exported['project'] = job['project']
            job_exported['schedule_enabled'] = str(job_definition['scheduleEnabled'])
            job_exported['schedule_weekday'] = job_definition['schedule']['weekday']['day']
            job_exported['schedule_hour'] = job_definition['schedule']['time']['hour']
            job_exported['schedule_minute'] = job_definition['schedule']['time']['minute']
            job_exported['schedule_seconds'] = job_definition['schedule']['time']['seconds']

            labels_values = [job_exported['name'], 
                             job_exported['id'], 
                             job_exported['project'],
                             job_exported['schedule_enabled'],
                             job_exported['schedule_weekday'],
                             job_exported['schedule_hour'],
                             job_exported['schedule_minute'],
                             job_exported['schedule_seconds']
                             ]

            job_scheduling_info = GaugeMetricFamily("job_scheduling_info", "Job scheduling info", 
                                                    labels=
                                                    self.default_labels +
                                                    ['job_name', 
                                                    'job_id', 
                                                    'project_name',
                                                    'schedule_enabled', 
                                                    'job_schedule_weekday',
                                                    'job_schedule_hour',
                                                    'job_schedule_minute',
                                                    'job_schedule_seconds'                                                 
                                                    ])
            job_scheduling_info.add_metric(self.default_labels_values + labels_values, 1.0)
            
            yield job_scheduling_info

        # count = CounterMetricFamily("random_number_2", "A random number 2.0", labels=['randomNum'])
        # global totalRandomNumber
        # totalRandomNumber += 1
        # count.add_metric(['random_num'], totalRandomNumber)
        # yield count

    def run():

        try:
            REGISTRY.register(RundeckMetricsCollector())

            logging.info(f'Rundeck exporter server started')
            start_http_server(9622, registry=REGISTRY)

            while True:
                sleep(1)
        except OSError as os_error:
            logging.critical(f'Error starting exporter: {os_error}')
        except KeyboardInterrupt:
            logging.info('Rundeck exporter execution finished.')

if __name__ == "__main__":
    RundeckMetricsCollector.run()
