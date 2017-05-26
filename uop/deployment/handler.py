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
deployment_api = Api(deployment_blueprint, errors=deploy_errors)


def get_resource_by_id(resource_id):
    url = 'http://cmdb-test.syswin.com/cmdb/api/items?resource_id=' + resource_id
    headers = {'Content-Type': 'application/json'}
    result = requests.post(url, headers=headers)
    print result.json()


def deploy_to_crp(deploy_item):

    # todo:from CMDB get data

    data = {
        "deploy_id": deploy_item.deploy_id,
        "mysql": {
            "ip": "172.28.29.46",
            "port": "3306",
            "host_user": "root",
            "host_password": "123456",
            "mysql_user": "root",
            "mysql_password": "Syswin#123",
            "database": "mysql",
            "sql_script": deploy_item.exec_context
        },
        "docker": {
            "image_url": deploy_item.app_image,
            "ip": "172.28.29.46"
        }
    }
    data_str = json.dumps(data)
    try:
        headers = {'Content-Type': 'application/json'}
        result = requests.post(
            CPR_URL + "api/deploy/deploys",
            headers=headers, data=data_str)
        result = json.dumps(result.json())
    except Exception as e:
        result = e.message

    print 'deployment(' + deploy_item.deploy_id + ') apply to crp, request body:' + data_str + ' result:' + result


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
                deploy_to_crp(deploy_item)

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


if __name__ == '__main__':
    get_resource_by_id('')
