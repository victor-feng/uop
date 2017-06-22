# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os

from flask import request
from flask_restful import reqparse, Api, Resource
from uop.deployment import deployment_blueprint
from uop.models import Deployment, ResourceModel
from uop.deployment.errors import deploy_errors
from config import APP_ENV, configs

CPR_URL = configs[APP_ENV].CRP_URL
CMDB_URL = configs[APP_ENV].CMDB_URL
UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER

deployment_api = Api(deployment_blueprint, errors=deploy_errors)


def get_resource_by_id(resource_id):
    err_msg = None
    resource_info = {}
    resource = ResourceModel.objects.get(res_id=resource_id)
    try:
        # url = CMDB_URL+'cmdb/api/repo_store/?resource_id='+resource_id
        url = CMDB_URL + 'cmdb/api/repo_relation/' + resource.cmdb_p_code + \
              '?layer_count=3&total_count=50' +\
              '&reference_sequence=[{\"child\": 2},{\"bond\": 1}]' +\
              '&item_filter=docker&item_filter=mongo_cluster&item_filter=mysql_cluster&item_filter=redis_cluster' +\
              '&columns_filter={\"mysql_cluster\":[\"IP地址\",\"用户名\",\"密码\",\"端口\"],' +\
              ' \"mongo_cluster\":[\"IP地址\",\"用户名\",\"密码\",\"端口\"],' +\
              ' \"redis_cluster\":[\"IP地址\",\"用户名\",\"密码\",\"端口\"],' +\
              ' \"docker\":[\"IP地址\",\"用户名\",\"密码\",\"端口\"]}'

        headers = {'Content-Type': 'application/json'}
        print url+' '+json.dumps(headers)
        result = requests.get(url, headers=headers)
        result = result.json()
        data = result.get('result', {}).get('res', {})
        code = result.get('code', -1)
        print 'data: '+json.dumps(result)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    else:
        if code == 2002:
            for item in data.get('items'):
                colunm = {}
                for i in item.get('column'):
                    if i.get('name') is not None:
                        colunm[i.get('name')] = i.get('value')

                resource_info[item.get('item_id')] = {
                    'ip': colunm.get('IP地址'.decode('utf-8'), '127.0.0.1'),
                    'user': colunm.get('用户名'.decode('utf-8'), 'root'),
                    'password': colunm.get('密码'.decode('utf-8'), '123456'),
                    'port': colunm.get('端口'.decode('utf-8'), '3306'),
                }

        else:
            err_msg = 'resource('+resource_id+') not found.'

    return err_msg, resource_info


def deploy_to_crp(deploy_item, resource_info, file_data):
    data = {
        "deploy_id": deploy_item.deploy_id,
        "mysql": {
            "ip": resource_info['mysql_cluster']['ip'],
            "port": resource_info['mysql_cluster']['port'],
            "host_user": "root",
            "host_password": "123456",
            "mysql_user": resource_info['mysql_cluster']['user'],
            "mysql_password": resource_info['mysql_cluster']['password'],
            "database": "mysql",
            "sql_script": deploy_item.mysql_context
        },
        "redis": {
            "sql_script": deploy_item.redis_context
        },
        "mongo": {
            "sql_script": deploy_item.mongodb_context
        },
        "docker": {
            "image_url": deploy_item.app_image,
            "ip": resource_info['docker']['ip']
        }
    }

    err_msg = None
    result = None
    try:
        url = CPR_URL + "api/deploy/deploys"
        headers = {
            'Content-Type': 'application/json',
        }
        data_str = json.dumps(data)
        res = upload_files_to_crp(file_data)
        if res.code == 200:
            for type, filename_list in res.file_info.items():
                data[type]['filenames'] = filename_list
        elif res.code == 500:
            return 'upload sql file failed', result
        print url + ' ' + json.dumps(headers)
        result = requests.post(url=url, headers=headers, data=data_str)
        result = json.dumps(result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message

    return err_msg, result

def upload_files_to_crp(file_data):
    url = CPR_URL + "api/deploy/upload"
    files = []
    for db_type, filenames in file_data.items():
        for idx, filename in enumerate(filenames):
            files.append((db_type + '_' + str(idx), open(os.path.join(UPLOAD_FOLDER, db_type, filename), 'rb')))

    if files:
        data = {'action': 'upload'}
        result = requests.post(url=url, files=files, data=data)
        return result
    else:
        return {'code': -1}



class DeploymentListAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        parser.add_argument('initiator', type=str, location='args')
        parser.add_argument('deploy_name', type=str, location='args')
        parser.add_argument('project_name', type=str, location='args')
        parser.add_argument('resource_name', type=str, location='args')
        parser.add_argument('deploy_result', type=str, location='args')
        parser.add_argument('environment', type=str, location='args')
        parser.add_argument('start_time', type=str, location='args')
        parser.add_argument('end_time', type=str, location='args')

        args = parser.parse_args()
        condition = {}
        if args.user_id:
            condition['user_id'] = args.user_id
        if args.initiator:
            condition['initiator'] = args.initiator
        if args.deploy_name:
            condition['deploy_name'] = args.deploy_name
        if args.project_name:
            condition['project_name'] = args.project_name
        if args.resource_name:
            condition['resource_name'] = args.resource_name
        if args.deploy_result:
            condition['deploy_result'] = args.deploy_result
        if args.environment:
            condition['environment'] = args.environment
        if args.start_time and args.end_time:
            condition['created_time__gte'] = args.start_time
            condition['created_time__lte'] = args.end_time

        deployments = []
        try:
            for deployment in Deployment.objects.filter(**condition).order_by('-created_time'):
                deployments.append({
                    'deploy_id': deployment.deploy_id,
                    'deploy_name': deployment.deploy_name,
                    'initiator': deployment.initiator,
                    'user_id': deployment.user_id,
                    'project_id': deployment.project_id,
                    'project_name': deployment.project_name,
                    'resource_id': deployment.resource_id,
                    'resource_name': deployment.resource_name,
                    'environment': deployment.environment,
                    'release_notes': deployment.release_notes,
                    'mysql_tag': deployment.mysql_tag,
                    'mysql_context': deployment.mysql_context,
                    'redis_tag': deployment.redis_tag,
                    'redis_context': deployment.redis_context,
                    'mongodb_tag': deployment.mongodb_tag,
                    'mongodb_context': deployment.mongodb_context,
                    'app_image': deployment.app_image,
                    'created_time': str(deployment.created_time),
                    'deploy_result': deployment.deploy_result,
                    'apply_status': deployment.apply_status,
                    'approve_status': deployment.approve_status,
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
        parser.add_argument('action', type=str, choices=('save_to_db', 'admin_approve', 'deploy_to_crp'), required=True,
                            help='No action(save_to_db/deploy_to_crp) provided', location='json')
        parser.add_argument('deploy_name', type=str, required=True,
                            help='No deploy name provided', location='json')
        parser.add_argument('initiator', type=str, location='json')
        parser.add_argument('user_id', type=str, location='json')
        parser.add_argument('project_id', type=str, required=True,
                            help='No project id provided', location='json')
        parser.add_argument('project_name', type=str, location='json')
        parser.add_argument('resource_id', type=str, required=True,
                            help='No resource id provided', location='json')
        parser.add_argument('resource_name', type=str, location='json')
        parser.add_argument('environment', type=str, location='json')
        parser.add_argument('release_notes', type=str, location='json')
        parser.add_argument('mysql_tag', type=str, location='json')
        parser.add_argument('mysql_context', type=str, location='json')
        parser.add_argument('redis_tag', type=str, location='json')
        parser.add_argument('redis_context', type=str, location='json')
        parser.add_argument('mongodb_tag', type=str, location='json')
        parser.add_argument('mongodb_context', type=str, location='json')
        parser.add_argument('app_image', type=str, location='json')
        parser.add_argument('file_name', type=str, location='json')

        parser.add_argument('apply_status', type=str, location='json')
        parser.add_argument('approve_status', type=str, location='json')
        parser.add_argument('dep_id', type=str, location='json')

        args = parser.parse_args()

        action = args.action
        deploy_name = args.deploy_name
        initiator = args.initiator
        user_id = args.user_id
        project_id = args.project_id
        project_name = args.project_name
        resource_id = args.resource_id
        resource_name = args.resource_name
        environment = args.environment
        release_notes = args.release_notes
        mysql_tag = args.mysql_tag
        mysql_context = args.mysql_context
        redis_tag = args.redis_tag
        redis_context = args.redis_context
        mongodb_tag = args.mongodb_tag
        mongodb_context = args.mongodb_context
        app_image = args.app_image
        file_name = args.file_name

        apply_status = args.apply_status
        approve_status = args.approve_status
        dep_id = args.id

        if action == 'deploy_to_crp':
            deploy_result = 'deploying'
        elif action == 'save_to_db':
            deploy_result = 'not_deployed'
        elif action == 'admin_approve':
            deploy_result = 'not_deployed'
        else:
            deploy_result = 'unknown'

        try:
            deploy_item = Deployment(
                deploy_id=str(uuid.uuid1()),
                deploy_name=deploy_name,
                initiator=initiator,
                user_id=user_id,
                project_id=project_id,
                project_name=project_name,
                resource_id=resource_id,
                resource_name=resource_name,
                created_time=datetime.datetime.now(),
                environment=environment,
                release_notes=release_notes,
                mysql_tag=mysql_tag,
                mysql_context=mysql_context,
                redis_tag=redis_tag,
                redis_context=redis_context,
                mongodb_tag=mongodb_tag,
                mongodb_context=mongodb_context,
                app_image=app_image,
                deploy_result=deploy_result,
                apply_status=apply_status,
                approve_status=approve_status,
            )

            if action == 'deploy_to_crp':
                # 需要传过来部署id

                deploy_obj = Deployment.objects.get(deploy_id=dep_id)

                err_msg, resource_info = get_resource_by_id(
                    deploy_obj.resource_id)
                if not err_msg:
                    err_msg, result = deploy_to_crp(deploy_obj, resource_info, file_name)
                    if err_msg:
                        deploy_obj.deploy_result = 'fail'
                        deploy_obj.approve_status = 'fail'
                        print 'deploy_to_crp err: '+err_msg
                    else:
                        print 'deploy_to_crp response: '+result
                        deploy_obj.approve_status = 'success'
                    deploy_obj.save()
                if err_msg:
                    raise Exception(err_msg)
            elif action == 'admin_approve':  # 管理员审批
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'success'
                deploy_obj.save()
            elif action == 'save_to_db':  # 部署申请
                deploy_item.save()

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
                    "msg": deploy_item.deploy_id,
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


class DeploymentListByByInitiatorAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('initiator', type=str, location='args')
        args = parser.parse_args()

        condition = {}
        if args.initiator:
            condition['initiator'] = args.initiator

        pipeline = [
            {
                '$match': condition
            },
            {
                '$sort': {'created_time': 1}
            },
            {
                '$group': {
                    '_id': {'resource_id': "$resource_id"},
                    'created_time': {'$last': "$created_time"},
                    'deploy_id': {'$last': "$deploy_id"},
                    'deploy_name': {'$last': "$deploy_name"},
                    'resource_id': {'$last': "$resource_id"},
                    'resource_name': {'$last': "$resource_name"},
                    'project_id': {'$last': "$project_id"},
                    'project_name': {'$last': "$project_name"},
                    'initiator': {'$last': "$initiator"},
                    'environment': {'$last': "$environment"},
                    'release_notes': {'$last': "$release_notes"},
                    'app_image': {'$last': "$app_image"},
                    'deploy_result': {'$last': "$deploy_result"},
                }
            },
        ]

        rst = []
        try:
            for _deployment in Deployment._get_collection().aggregate(pipeline):
                rst.append({
                    "resource_id": _deployment['resource_id'],
                    "resource_name": _deployment['resource_name'],
                    "deploy_id": _deployment['deploy_id'],
                    "deploy_name": _deployment['deploy_name'],
                    "deploy_result": _deployment['deploy_result'],
                    "project_id": _deployment['project_id'],
                    "project_name": _deployment['project_name'],
                    "created_time": str(_deployment['created_time']),
                    "initiator": _deployment['initiator'],
                    "environment": _deployment['environment'],
                    "app_image": _deployment['app_image']
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
            return rst, 200

        # try:
        #     deploy_list = {}
        #     for deployment in Deployment.objects.filter(**condition):
        #
        #         def _get_deployment_dict(_deployment):
        #             return {
        #                 "resource_id": _deployment.resource_id,
        #                 "resource_name": _deployment.resource_name,
        #                 "deploy_id": _deployment.deploy_id,
        #                 "deploy_name": _deployment.deploy_name,
        #                 "deploy_result": _deployment.deploy_result,
        #                 "project_id": _deployment.project_id,
        #                 "project_name": _deployment.project_name,
        #                 "created_time": str(_deployment.created_time),
        #                 "initiator": _deployment.initiator,
        #                 "environment": _deployment.environment,
        #                 "app_image": _deployment.app_image
        #             }
        #
        #         if not deploy_list.get(deployment.resource_id, None):
        #             deploy_list[deployment.resource_id] = [_get_deployment_dict(deployment)]
        #         else:
        #             deploy_list[deployment.resource_id].append(_get_deployment_dict(deployment))
        #
        #     rst = []
        #     for _, d_value in deploy_list.items():
        #         d_lst = sorted(d_value, reverse=True, key=lambda x: x['created_time'])
        #         rst.append(d_lst[0])
        # except Exception as e:
        #     res = {
        #         "code": 400,
        #         "result": {
        #             "res": "failed",
        #             "msg": e.message
        #         }
        #     }
        #     return res, 400
        # else:
        #     return rst, 200


class Upload(Resource):
    def post(self):
        try:
            file = request.files['file']
            type = request.form['file_type']
            file.save(os.path.join(UPLOAD_FOLDER, type, file.filename))
        except Exception as e:
            return {
                'code': 500,
                'msg': e.message
            }
        return {
            'code': 200,
            'msg': '上传成功！',
            'type': type,
        }



deployment_api.add_resource(DeploymentListAPI, '/deployments')
deployment_api.add_resource(DeploymentAPI, '/deployments/<deploy_id>')
deployment_api.add_resource(DeploymentListByByInitiatorAPI, '/getDeploymentsByInitiator')
deployment_api.add_resource(Upload, '/upload')
