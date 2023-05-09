import requests
import logging
import json
from yaml import full_load

log_level = logging.INFO
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=log_level)

class Rundeck(object):

    def __init__(self, url: str, token: str, api_version: int):
        self.url = url
        self.token = token
        self.api_version = api_version

    def getDataFrom(self, endpoint: str, accept_format:str = 'json') -> dict:
        response = None
        session = requests.Session()

        try:

            request_url = f'{self.url}/api/{self.api_version}{endpoint}'

            if accept_format == 'json':
                accept = 'application/json'
            elif accept_format == 'yaml':
                accept = 'text/yaml'
            else:
                raise Exception('The accept format is not valid')
                
            response = session.get(
                request_url,
                headers = {
                    'Accept': accept,
                    'X-Rundeck-Auth-Token': self.token
                },
                verify = False
            )
            
            if accept_format == 'json':
                response_request = response.json()
            elif accept_format == 'yaml':
                response_request = full_load(response.text)

            if response_request and isinstance(response_request, dict) and response_request.get('error') is True:
                raise Exception(response_request.get('message'))

            return response_request
        
        except json.JSONDecodeError as error:
            logging.critical(f'Invalid JSON Response from {request_url}')
        except Exception as error:
            logging.critical(f'Error getting data from {endpoint}: {error}')

    def listProjects(self) -> list:

        endpoint = '/projects'
        projects = [project['name'] for project in self.getDataFrom(endpoint)]
        
        return projects
    
    def listJobs(self) -> list:

        jobs = []
        for project in self.listProjects():

            endpoint = f'/project/{project}/jobs'
            jobs += self.getDataFrom(endpoint)
        
        return jobs

    def getJobDefinition(self, job_id) -> dict:

        endpoint = f'/job/{job_id}'
        job_definition = self.getDataFrom(endpoint, accept_format='yaml')
        
        return job_definition[0]

    def getjobExecutions(self, job_id, results_total) -> list:

        endpoint = f'/job/{job_id}/executions?max={results_total}'
        job_executions = self.getDataFrom(endpoint)
        
        return job_executions['executions']
