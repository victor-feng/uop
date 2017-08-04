# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os
import logging

from flask import request, send_from_directory
from flask_restful import reqparse, Api, Resource
from flask import current_app
from uop.deployment import deployment_blueprint
from uop.models import Deployment, ResourceModel, DisconfIns
from uop.deployment.errors import deploy_errors
from uop.disconf.disconf_api import *
from config import APP_ENV, configs


#CPR_URL = configs[APP_ENV].CRP_URL
#CMDB_URL = configs[APP_ENV].CMDB_URL
#UPLOAD_FOLDER = configs[APP_ENV].UPLOAD_FOLDER

#CPR_URL = current_app.config['CRP_URL']
#CMDB_URL = current_app.config['CMDB_URL']
#UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']

deployment_api = Api(deployment_blueprint, errors=deploy_errors)


def get_resource_by_id(resource_id):
    err_msg = None
    resource_info = {}
    resource = ResourceModel.objects.get(res_id=resource_id)
    try:
        # url = CMDB_URL+'cmdb/api/repo_store/?resource_id='+resource_id

        CMDB_URL = current_app.config['CMDB_URL']
        url = CMDB_URL + 'cmdb/api/repo_relation/' + resource.cmdb_p_code + \
              '?layer_count=3&total_count=50' +\
              '&reference_sequence=[{\"child\": 2},{\"bond\": 1}]' +\
              '&item_filter=docker&item_filter=mongodb_cluster&item_filter=mysql_cluster&item_filter=redis_cluster' +\
              '&columns_filter={\"mysql_cluster\":[\"mysql_cluster_wvip\",\"mysql_cluster_rvip\",\"username\",\"password\",\"port\"],' +\
              ' \"mongodb_cluster\":[\"mongodb_cluster_ip1\",\"mongodb_cluster_ip2\",\"mongodb_cluster_ip3\",\"username\",\"password\",\"port\"],' +\
              ' \"redis_cluster\":[\"redis_cluster_vip\",\"username\",\"password\",\"port\"],' +\
              ' \"docker\":[\"ip_address\",\"username\",\"password\",\"port\"]}'

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
                    if i.get('p_code') is not None:
                        colunm[i.get('p_code')] = i.get('value')

                resource_info[item.get('item_id')] = {
                    'user': colunm.get('username', 'root'),
                    'password': colunm.get('password', '123456'),
                    'port': colunm.get('port', '3306'),
                }
                if item.get('item_id') == 'mysql_cluster':
                    resource_info[item.get('item_id')]['wvip'] = colunm.get('mysql_cluster_wvip', '127.0.0.1')
                    resource_info[item.get('item_id')]['rvip'] = colunm.get('mysql_cluster_rvip', '127.0.0.1')
                elif item.get('item_id') == 'mongodb_cluster':
                    resource_info[item.get('item_id')]['vip1'] = colunm.get('mongodb_cluster_ip1', '127.0.0.1')
                    resource_info[item.get('item_id')]['vip2'] = colunm.get('mongodb_cluster_ip2', '127.0.0.1')
                    resource_info[item.get('item_id')]['vip3'] = colunm.get('mongodb_cluster_ip3', '127.0.0.1')
                elif item.get('item_id') == 'redis_cluster':
                    resource_info[item.get('item_id')]['vip'] = colunm.get('redis_cluster_vip', '127.0.0.1')
                elif item.get('item_id') == 'docker':
                    resource_info[item.get('item_id')]['ip_address'] = colunm.get('ip_address', '127.0.0.1')

        else:
            err_msg = 'resource('+resource_id+') not found.'

    return err_msg, resource_info


def deploy_to_crp(deploy_item, resource_info):
    data = {
        "deploy_id": deploy_item.deploy_id,
    }
    if resource_info.get('mysql_cluster'):
        data['mysql'] = {
            "ip": resource_info['mysql_cluster']['wvip'],
            "port": resource_info['mysql_cluster']['port'],
            "host_user": "root",
            "host_password": "123456",
            "mysql_user": resource_info['mysql_cluster']['user'],
            "mysql_password": resource_info['mysql_cluster']['password'],
            "database": "mysql",
        }
    if resource_info.get('mongodb_cluster'):
        data['mongodb'] = {
            "vip1": resource_info['mongodb_cluster']['vip1'],
            "vip2": resource_info['mongodb_cluster']['vip2'],
            "vip3": resource_info['mongodb_cluster']['vip3'],
            "port": resource_info['mongodb_cluster']['port'],
            "host_username": "root",
            "host_password": "123456",
            "mongodb_username": resource_info['mongodb_cluster']['user'],
            "mongodb_password": resource_info['mongodb_cluster']['password'],
            "database": "mongodb",
        }
    if resource_info.get('docker'):
        data['docker'] = {
            "image_url": deploy_item.app_image,
            "ip": resource_info['docker']['ip_address']
        }

    err_msg = None
    result = None
    try:

        CPR_URL = current_app.config['CRP_URL']
        url = CPR_URL + "api/deploy/deploys"
        headers = {
            'Content-Type': 'application/json',
        }
        file_paths = []
        if deploy_item.mysql_context:
            file_paths.append(('mysql',deploy_item.mysql_context))
        if deploy_item.redis_context:
            file_paths.append(('redis', deploy_item.redis_context))
        if deploy_item.mongodb_context:
            file_paths.append(('mongodb', deploy_item.mongodb_context))

        if file_paths:
            res = upload_files_to_crp(file_paths)
            cont = json.loads(res.content)
            if cont.get('code') == 200:
                for type, path_filename in cont['file_info'].items():
                    data[type]['path_filename'] = path_filename
            elif cont.get('code') == 500:
                return 'upload sql file failed', result
        print url + ' ' + json.dumps(headers)
        data_str = json.dumps(data)
        result = requests.post(url=url, headers=headers, data=data_str)
        result = json.dumps(result.json())
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message

    return err_msg, result


def upload_files_to_crp(file_paths):

    CPR_URL = current_app.config['CRP_URL']
    url = CPR_URL + "api/deploy/upload"
    files = []
    for db_type, path in file_paths:
        files.append((db_type, open(path, 'rb')))

    if files:
        data = {'action': 'upload'}
        result = requests.post(url=url, files=files, data=data)
        return result
    else:
        return {'code': -1}


def disconf_write_to_file(file_name, file_content, instance_name, type):
    try:
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], type, instance_name)
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)
        upload_file = os.path.join(upload_dir,file_name)
        with open(upload_file, 'wb') as f:
            f.write(file_content)
    except Exception as e:
        raise ServerError(e.message)
    return upload_file


class DeploymentListAPI(Resource):

    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        parser.add_argument('deploy_id', type=str, location='args')
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
        if args.deploy_id:
            condition['deploy_id'] = args.deploy_id
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
                #返回disconf的json
                disconf = []
                for disconf_info in deployment.disconf_list:
                    instance_info = dict(ins_name = disconf_info.ins_name,
                                         ins_id = disconf_info.ins_id,
                                         dislist = [dict(disconf_tag = disconf_info.disconf_tag,
                                                        disconf_name = disconf_info.disconf_name,
                                                        disconf_content = disconf_info.disconf_content
                                                        )]
                                         )
                    if len(disconf) == 0:
                        disconf.append(instance_info)
                    else:
                        for disconf_choice in disconf:
                            if disconf_choice.get('ins_name') == instance_info.get('ins_name'):
                                disconf_choice.get('dislist').extend(instance_info.get('dislist'))
                                break
                        else:
                            disconf.append(instance_info)
                ################
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
                    'disconf': disconf,
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
        parser.add_argument('action', type=str, choices=('save_to_db', 'admin_approve_allow', 'admin_approve_forbid'), required=True,
                            help='No action(save_to_db/admin_approve_allow/admin_approve_forbid) provided', location='json')
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
        parser.add_argument('mysql_exe_mode', type=str, location='json')
        parser.add_argument('mysql_context', type=str, location='json')
        parser.add_argument('redis_exe_mode', type=str, location='json')
        parser.add_argument('redis_context', type=str, location='json')
        parser.add_argument('mongodb_exe_mode', type=str, location='json')
        parser.add_argument('mongodb_context', type=str, location='json')
        parser.add_argument('app_image', type=str, location='json')

        parser.add_argument('approve_suggestion', type=str, location='json')
        parser.add_argument('apply_status', type=str, location='json')
        parser.add_argument('approve_status', type=str, location='json')
        parser.add_argument('dep_id', type=str, location='json')
        parser.add_argument('disconf',type=list, location='json')


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
        mysql_exe_mode = args.mysql_exe_mode
        mysql_context = args.mysql_context
        redis_exe_mode = args.redis_exe_mode
        redis_context = args.redis_context
        mongodb_exe_mode = args.mongodb_exe_mode
        mongodb_context = args.mongodb_context
        app_image = args.app_image
        disconf = args.disconf

        approve_suggestion = args.approve_suggestion
        apply_status = args.apply_status
        approve_status = args.approve_status
        if args.dep_id:
            dep_id = args.dep_id

        deploy_result = 'not_deployed'

        UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
        uid = str(uuid.uuid1())
        def write_file(uid, context, type):
            path = os.path.join(UPLOAD_FOLDER, type, 'script_' + uid)
            with open(path, 'wb') as f:
                f.write(context)
            return path
        if mysql_exe_mode == 'tag' and  mysql_context:
            mysql_context = write_file(uid, mysql_context, 'mysql')
        if redis_exe_mode == 'tag' and  redis_context:
            redis_context = write_file(uid, redis_context, 'redis')
        if mongodb_exe_mode == 'tag' and  mongodb_context:
            mongodb_context = write_file(uid, mongodb_context, 'mongodb')

        try:
            # 管理员审批通过 直接部署到CRP
            if action == 'admin_approve_allow':  # 管理员审批通过
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'success'
                #disconf配置
                disconf_result = []
                for disconf_info in deploy_obj.disconf_list:
                    result,message = disconf_add_app_config_api_file(
                                                    app_name=disconf_info.ins_name,
                                                    filename=disconf_info.disconf_name,
                                                    myfilerar=disconf_info.disconf_content)

                    disconf_result.append(dict(result=result,message=message))
                message = disconf_result
                #CRP配置
                err_msg, resource_info = get_resource_by_id(deploy_obj.resource_id)
                if not err_msg:
                    err_msg, result = deploy_to_crp(deploy_obj, resource_info)
                    if err_msg:
                        deploy_obj.deploy_result = 'fail'
                        print 'deploy_to_crp err: '+err_msg
                    else:
                        print 'deploy_to_crp response: '+result
                else:
                    raise Exception(err_msg)
                deploy_obj.deploy_result = 'deploying'
                deploy_obj.save()
                #message = 'deploy success'

            elif action == 'admin_approve_forbid':  # 管理员审批不通过
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'fail'
                deploy_obj.deploy_result = deploy_result
                deploy_obj.save()
                message = 'approve_forbid success'

            elif action == 'save_to_db':  # 部署申请
                deploy_item = Deployment(
                    deploy_id=uid,
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
                    mysql_tag=mysql_exe_mode,
                    mysql_context=mysql_context,
                    redis_tag=redis_exe_mode,
                    redis_context=redis_context,
                    mongodb_tag=mongodb_exe_mode,
                    mongodb_context=mongodb_context,
                    app_image=app_image,
                    deploy_result=deploy_result,
                    apply_status=apply_status,
                    approve_status=approve_status,
                    approve_suggestion=approve_suggestion,
                )

                for instance_info in disconf:
                    for disconf_info in instance_info.get('dislist'):
                        if disconf_info.get('disconf_tag') == 'tag':
                            file_name = disconf_info.get('disconf_name')
                            file_content = disconf_info.get('disconf_content')
                            ins_name = instance_info.get('ins_name')
                            upload_file = disconf_write_to_file(file_name=file_name,
                                                                file_content=file_content,
                                                                instance_name=ins_name,
                                                                type='disconf')
                            disconf_info['disconf_content'] = upload_file
                        else:
                            upload_dir = current_app.config['UPLOAD_FOLDER']
                            file_name = disconf_info.get('disconf_name')
                            ins_name = instance_info.get('ins_name')
                            type = 'disconf'
                            upload_file = os.path.join(upload_dir,type,ins_name,file_name)
                            disconf_info['disconf_content'] = upload_file

                        ins_name = instance_info.get('ins_name')
                        ins_id = instance_info.get('ins_id')
                        disconf_tag=disconf_info.get('disconf_tag')
                        disconf_name = disconf_info.get('disconf_name')
                        disconf_content = disconf_info.get('disconf_content')
                        disconf_ins = DisconfIns(ins_name=ins_name, ins_id=ins_id,
                                                 disconf_tag=disconf_tag,
                                                 disconf_name = disconf_name,
                                                 disconf_content = disconf_content
                                                 )
                        deploy_item.disconf_list.append(disconf_ins)

                deploy_item.save()
                message = 'save_to_db success'
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
                    "res": message,
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
        logging.info("[UOP] come into uop/deployment/handler.py, args: %s", args)

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
            uid = str(uuid.uuid1())
            UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']

            file = request.files['file']
            type = request.form['file_type']

            if type == 'disconf':
                instance_name = request.form.get('instance_name')
                index = request.form.get('index')
                filename = file.filename
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], type, instance_name)
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                path = os.path.join(upload_path,filename)
            else:
                filename = file.filename + '_' + uid
                index = request.form.get('index')
                path = os.path.join(UPLOAD_FOLDER, type, filename)
            file.save(path)
        except Exception as e:
            return {
                'code': 500,
                'msg': e.message
            }
        return {
            'code': 200,
            'msg': '上传成功！',
            'type': type,
            'path': path,
            'index': index,
        }


class Download(Resource):
    def get(self,file_name):
        try:
            download_dir = current_app.config['UPLOAD_FOLDER']
            if os.path.isfile(os.path.join(download_dir, file_name)):
                return send_from_directory(download_dir, file_name, as_attachment=True)
            else:
                raise ServerError('file not exist.')
        except Exception as e:
            ret = {
                    'code': 500,
                    'msg': e.message
                  }
            return ret

deployment_api.add_resource(DeploymentListAPI, '/deployments')
deployment_api.add_resource(DeploymentAPI, '/deployments/<deploy_id>')
deployment_api.add_resource(DeploymentListByByInitiatorAPI, '/getDeploymentsByInitiator')
deployment_api.add_resource(Upload, '/upload')
deployment_api.add_resource(Download, '/download/<file_name>')
