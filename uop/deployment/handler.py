# -*- coding: utf-8 -*-

import uuid
import requests
import json

from flask_restful import reqparse, Api, Resource
from uop.deployment import deployment_blueprint
from uop.models import Deployment
from uop.deployment.errors import deploy_errors
from config import APP_ENV, configs

CPR_URL = configs[APP_ENV].CRP_URL
CMDB_URL = configs[APP_ENV].CMDB_URL

deployment_api = Api(deployment_blueprint, errors=deploy_errors)


def get_resource_by_id(resource_id):
    err_msg = None
    resource_info = {}
    try:
        url = CMDB_URL+'cmdb/api/repo_store/?resource_id='+resource_id
        headers = {'Content-Type': 'application/json'}
        print url+' '+json.dumps(headers)
        result = requests.get(url, headers=headers)
        result = result.json()
        print 'data: '+json.dumps(result)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    else:
        if result:
            _container = result.get('container', {})
            _mysql = result.get('db_info', {}).get('mysql', {})
            resource_info['mysql_ip'] = _mysql.get('ip', None)
            resource_info['mysql_port'] = _mysql.get('port', None)
            resource_info['mysql_user'] = _mysql.get('username', None)
            resource_info['mysql_password'] = _mysql.get('password', None)
            resource_info['docker_ip'] = _container.get('ip', None)
        else:
            err_msg = 'resource('+resource_id+') not found.'

    return err_msg, resource_info


def deploy_to_crp(deploy_item, resource_info):
    data = {
        "deploy_id": deploy_item.deploy_id,
        "mysql": {
            "ip": resource_info['mysql_ip'],
            "port": resource_info['mysql_port'],
            "host_user": "root",
            "host_password": "123456",
            "mysql_user": resource_info['mysql_user'],
            "mysql_password": resource_info['mysql_password'],
            "database": "mysql",
            "sql_script": deploy_item.exec_context
        },
        "docker": {
            "image_url": deploy_item.app_image,
            "ip": resource_info['docker_ip']
        }
    }
    try:
        data_str = json.dumps(data)
        url = CPR_URL + "api/deploy/deploys"
        headers = {'Content-Type': 'application/json'}
        print url + ' ' + json.dumps(headers) + ' ' + data_str
        result = requests.post(url=url, headers=headers, data=data_str)
        result = json.dumps(result.json())
    except requests.exceptions.ConnectionError as rq:
        result = rq.message.message
    except BaseException as e:
        result = e.message

    print 'response: '+result


class DeploymentListAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('initiator', type=str, location='args')
        parser.add_argument('deploy_name', type=str, location='args')
        parser.add_argument('project_name', type=str, location='args')
        parser.add_argument('start_time', type=str, location='args')
        parser.add_argument('end_time', type=str, location='args')

        args = parser.parse_args()
        condition = {}
        if args.initiator:
            condition['initiator'] = args.initiator
        if args.deploy_name:
            condition['deploy_name'] = args.deploy_name
        if args.project_name:
            condition['project_name'] = args.project_name
        if args.start_time and args.end_time:
            condition['created_time__gte'] = args.start_time
            condition['created_time__lt'] = args.end_time

        deployments = []
        try:
            for deployment in Deployment.objects.filter(**condition):
                deployments.append({
                    'deploy_id': deployment.deploy_id,
                    'deploy_name': deployment.deploy_name,
                    'initiator': deployment.initiator,
                    'project_id': deployment.project_id,
                    'project_name': deployment.project_name,
                    'resource_id': deployment.resource_id,
                    'resource_name': deployment.resource_name,
                    'environment': deployment.environment,
                    'exec_tag': deployment.exec_tag,
                    'exec_context': deployment.exec_context,
                    'app_image': deployment.app_image,
                    'created_time': str(deployment.created_time),
                    'deploy_result': deployment.deploy_result
                })
        except Exception as e:
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            return deployments, 200

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('action', type=str, choices=('save_to_db', 'deploy_to_crp'), required=True,
                            help='No action(save_to_db/deploy_to_crp) provided', location='json')
        parser.add_argument('deploy_name', type=str, required=True,
                            help='No deploy name provided', location='json')
        parser.add_argument('initiator', type=str, location='json')
        parser.add_argument('project_id', type=str, required=True,
                            help='No project id provided', location='json')
        parser.add_argument('project_name', type=str, location='json')
        parser.add_argument('resource_id', type=str, required=True,
                            help='No resource id provided', location='json')
        parser.add_argument('resource_name', type=str, location='json')
        parser.add_argument('environment', type=str, location='json')
        parser.add_argument('exec_tag', type=str, location='json')
        parser.add_argument('exec_context', type=str, location='json')
        parser.add_argument('app_image', type=str, location='json')
        args = parser.parse_args()

        action = args.action
        deploy_name = args.deploy_name
        initiator = args.initiator
        project_id = args.project_id
        project_name = args.project_name
        resource_id = args.resource_id
        resource_name = args.resource_name
        environment = args.environment
        exec_tag = args.exec_tag
        exec_context = args.exec_context
        app_image = args.app_image

        if action == 'deploy_to_crp':
            deploy_result = 'deploying'
        else:
            deploy_result = 'not_deployed'

        try:
            deploy_item = Deployment(
                deploy_id=str(uuid.uuid1()),
                deploy_name=deploy_name,
                initiator=initiator,
                project_id=project_id,
                project_name=project_name,
                resource_id=resource_id,
                resource_name=resource_name,
                environment=environment,
                exec_tag=exec_tag,
                exec_context=exec_context,
                app_image=app_image,
                deploy_result=deploy_result)
            deploy_item.save()

            if action == 'deploy_to_crp':
                err_msg, resource_info = get_resource_by_id(deploy_item.resource_id)
                if not err_msg:
                    deploy_to_crp(deploy_item, resource_info)
                else:
                    raise Exception(err_msg)

        except Exception as e:
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.message
                }
            }
            return res, 400
        else:
            res = {
                "code": 200,
                "result": {
                    "res": "success",
                    "msg": "create deployment success"
                }
            }
            return res, 200


class DeploymentAPI(Resource):

    def put(self, deploy_id):
        pass

    def delete(self, deploy_id):
        res_code = 204
        deploys = Deployment.objects(deploy_id=deploy_id)
        if deploys.count() > 0:
            deploys.delete()
        else:
            res_code = 404
        return "", res_code


deployment_api.add_resource(DeploymentListAPI, '/deployments')
deployment_api.add_resource(DeploymentAPI, '/deployments/<deploy_id>')
