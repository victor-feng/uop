# -*- coding: utf-8 -*-
import uuid
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.deployment import deployment_blueprint
from uop.models import Deployment
from uop.deployment.errors import deploy_errors

deployment_api = Api(deployment_blueprint, errors=deploy_errors)


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
                    'project_name': deployment.project_name,
                    'environment': deployment.environment,
                    'exec_tag': deployment.exec_tag,
                    'exec_context': deployment.exec_context,
                    'app_image': deployment.app_image,
                    'created_time': str(deployment.created_time)
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
        parser.add_argument('deploy_name', type=str, required=True,
                            help='No deploy name provided', location='json')
        parser.add_argument('initiator', type=str, location='json')
        parser.add_argument('project_name', type=str, location='json')
        parser.add_argument('environment', type=str, location='json')
        parser.add_argument('exec_tag', type=str, location='json')
        parser.add_argument('exec_context', type=str, location='json')
        parser.add_argument('app_image', type=str, location='json')
        args = parser.parse_args()

        deploy_name = args.deploy_name
        initiator = args.initiator
        project_name = args.project_name
        environment = args.environment
        exec_tag = args.exec_tag
        exec_context = args.exec_context
        app_image = args.app_image

        try:
            Deployment(
                deploy_id=str(uuid.uuid1()),
                deploy_name=deploy_name,
                initiator=initiator,
                project_name=project_name,
                environment=environment,
                exec_tag=exec_tag,
                exec_context=exec_context,
                app_image=app_image).save()

            # TODO：deploy to CRP

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
