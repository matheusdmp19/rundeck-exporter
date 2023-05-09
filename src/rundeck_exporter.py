from os import getenv
from time import sleep
import re
import logging

from rundeck_client import Rundeck

from prometheus_client.core import GaugeMetricFamily, REGISTRY
from prometheus_client import start_http_server

'''
export RUNDECK_URL='http://localhost:4440'
export RUNDECK_TOKEN='k6nz3bEMAUt9hfaQvnosjpOoVP2czGYJ'
export RUNDECK_API_VERSION=40
'''

log_level = logging.INFO
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=log_level)

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

        ''' Job Metrics'''        
        jobs = self.rd.listJobs()
        for job in jobs:

            ''' Job scheduling information '''
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

            default_job_labels = ['job_name',
                                  'job_id', 
                                  'project_name',
                                  'schedule_enabled'
                                  ]
            default_job_labels_values = [job_exported['name'], 
                             job_exported['id'], 
                             job_exported['project'],
                             job_exported['schedule_enabled']
                             ]
            schedule_labels_values = [job_exported['schedule_weekday'],
                             job_exported['schedule_hour'],
                             job_exported['schedule_minute'],
                             job_exported['schedule_seconds']
                             ]

            ''' Job scheduling information metric'''
            job_scheduling_info = GaugeMetricFamily("job_scheduling_info", "Job scheduling info", 
                                                    labels=
                                                    self.default_labels + default_job_labels +
                                                    ['job_schedule_weekday',
                                                    'job_schedule_hour',
                                                    'job_schedule_minute',
                                                    'job_schedule_seconds'                                                 
                                                    ])
            job_scheduling_info.add_metric(self.default_labels_values + default_job_labels_values + schedule_labels_values, 1.0)
            
            ''' Last executions status per Job '''
            list_executions = self.rd.getJobExecutions(job['id'], 15)
            
            status = {'succeeded': 0, 'failed': 0, 'aborted': 0, 'running': 0}
            
            job_exported['status_last_succeeded_execution'] = 0
            job_exported['status_last_two_succeededs_executions'] = 0
            job_exported['status_last_fifteen_succeededs_executions'] = 0

            job_exported['status_last_failed_execution'] = 0
            job_exported['status_last_two_faileds_executions'] = 0
            job_exported['status_last_fifteen_faileds_executions'] = 0

            job_exported['status_last_aborted_execution'] = 0
            job_exported['status_last_two_aborteds_executions'] = 0
            job_exported['status_last_fifteen_aborteds_executions'] = 0
            
            for i, execution in enumerate(list_executions):

                if execution['status'] == 'succeeded':
                    status['succeeded'] += 1
                if execution['status'] == 'failed':
                    status['failed'] += 1
                if execution['status'] == 'aborted':
                    status['aborted'] += 1
                if execution['status'] == 'running':
                    status['running'] += 1

                if i == 0:
                    job_exported['status_last_succeeded_execution'] = status['succeeded']
                    job_exported['status_last_failed_execution'] = status['failed']
                    job_exported['status_last_aborted_execution'] = status['aborted']
                if i == 1:
                    job_exported['status_last_two_succeededs_executions'] = status['succeeded']
                    job_exported['status_last_two_faileds_executions'] = status['failed']
                    job_exported['status_last_two_aborteds_executions'] = status['aborted']
                if i == 14:
                    job_exported['status_last_fifteen_succeededs_executions'] = status['succeeded']
                    job_exported['status_last_fifteen_faileds_executions'] = status['failed']
                    job_exported['status_last_fifteen_aborteds_executions'] = status['aborted']
            

            ''' status_last_succeeded_execution metric'''
            status_last_succeeded_execution = GaugeMetricFamily("status_last_succeeded_execution", 
                                                                "Status of the last successful execution of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_succeeded_execution.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_succeeded_execution'])
            
            ''' status_last_two_succeededs_executions metric'''
            status_last_two_succeededs_executions = GaugeMetricFamily("status_last_two_succeededs_executions", 
                                                                "Status of the last two successful executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_two_succeededs_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_two_succeededs_executions'])
            
            ''' status_last_fifteen_succeededs_executions metric'''
            status_last_fifteen_succeededs_executions = GaugeMetricFamily("status_last_fifteen_succeededs_executions", 
                                                                "Status of the last fifteen successful executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_fifteen_succeededs_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_fifteen_succeededs_executions'])

            ''' status_last_failed_execution metric'''
            status_last_failed_execution = GaugeMetricFamily("status_last_failed_execution", 
                                                                "Status of the last failed execution of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_failed_execution.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_failed_execution'])

            ''' status_last_two_faileds_executions metric'''
            status_last_two_faileds_executions = GaugeMetricFamily("status_last_two_faileds_executions", 
                                                                "Status of the last two failed executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_two_faileds_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_two_faileds_executions'])

            ''' status_last_fifteen_faileds_executions metric'''
            status_last_fifteen_faileds_executions = GaugeMetricFamily("status_last_fifteen_faileds_executions", 
                                                                "Status of the last fifteen failed executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_fifteen_faileds_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_fifteen_faileds_executions'])
            
            ''' status_last_aborted_execution metric'''
            status_last_aborted_execution = GaugeMetricFamily("status_last_aborted_execution", 
                                                                "Status of the last aborted execution of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_aborted_execution.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_aborted_execution'])
            
            ''' status_last_two_aborteds_executions metric'''
            status_last_two_aborteds_executions = GaugeMetricFamily("status_last_two_aborteds_executions", 
                                                                "Status of the last two aborted executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_two_aborteds_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_two_aborteds_executions'])
            
            ''' status_last_fifteen_aborteds_executions metric'''
            status_last_fifteen_aborteds_executions = GaugeMetricFamily("status_last_fifteen_aborteds_executions", 
                                                                "Status of the last fifteen aborted executions of the job",
                                                                labels = self.default_labels + default_job_labels)
            status_last_fifteen_aborteds_executions.add_metric(self.default_labels_values + default_job_labels_values, 
                                                       job_exported['status_last_fifteen_aborteds_executions'])
            

            ''' Running Executions and date-started info'''
            job_exported['running_execution'] = 0
            job_exported['execution_avg_duration'] = 0
            job_exported['execution_start_date'] = 0
            job_exported['running_execution_id'] = 0
            
            running_execution = self.rd.getJobRunningExecutions(job_exported['project'], job_exported['id'], 1)
            if len(running_execution['executions']) > 0:
                job_exported['running_execution'] = 1.0
                job_exported['execution_avg_duration'] = running_execution['executions'][0]['job']['averageDuration']
                job_exported['execution_start_date'] = running_execution['executions'][0]['date-started']['unixtime']
                job_exported['running_execution_id'] = str(running_execution['executions'][0]['id'])

                ''' job_running_execution metric'''
                job_running_execution = GaugeMetricFamily("job_running_execution",
                                                          "Job Running Execution",
                                                          labels = self.default_labels + 
                                                          default_job_labels +
                                                          ['execution_id'])
                
                job_running_execution.add_metric(self.default_labels_values + 
                                                 default_job_labels_values + 
                                                 [job_exported['running_execution_id']], 1.0)
                
                ''' job_running_execution_avg_duration metric'''
                job_running_execution_avg_duration = GaugeMetricFamily("job_running_execution_avg_duration", 
                                                                    "Job Running Execution Average Duration",
                                                                    labels = self.default_labels + 
                                                                        default_job_labels +
                                                                        ['execution_id'])
                job_running_execution_avg_duration.add_metric(self.default_labels_values + 
                                                 default_job_labels_values + 
                                                 [job_exported['running_execution_id']], 
                                                 job_exported['execution_avg_duration'])
                
                ''' job_running_execution_start_date metric'''
                job_running_execution_start_date = GaugeMetricFamily("job_running_execution_start_date", 
                                                                    "Job Running Execution Start Date",
                                                                    labels = self.default_labels + 
                                                                        default_job_labels +
                                                                        ['execution_id'])
                job_running_execution_start_date.add_metric(self.default_labels_values + 
                                                 default_job_labels_values + 
                                                 [job_exported['running_execution_id']], 
                                                 job_exported['execution_start_date'])
                
                # Exposing metrics
                yield job_running_execution
                yield job_running_execution_avg_duration
                yield job_running_execution_start_date
            
            # Exposing metrics
            yield job_scheduling_info
            yield status_last_succeeded_execution
            yield status_last_two_succeededs_executions
            yield status_last_fifteen_succeededs_executions
            yield status_last_failed_execution
            yield status_last_two_faileds_executions
            yield status_last_fifteen_faileds_executions
            yield status_last_aborted_execution
            yield status_last_two_aborteds_executions
            yield status_last_fifteen_aborteds_executions

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
