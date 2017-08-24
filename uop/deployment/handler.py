# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os
import logging
import random

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

def format_resource_info(items):
    resource_info = {}
    colunm = {}
    for item in items.get('items'):
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

    return resource_info


def get_resource_by_id_mult(p_codes):
    CMDB_URL = current_app.config['CMDB_URL']
    url = CMDB_URL + 'cmdb/api/repo_relation/'
    headers = {'Content-Type': 'application/json'}
    data = {
        'layer_count': 3,
        'total_count': 50,
        'reference_sequence': [{'child': 2}, {'bond': 1}],
        'item_filter': ['docker', 'mongodb_cluster', 'mysql_cluster', 'redis_cluster'],
        'columns_filter': {
            'mysql_cluster': ['mysql_cluster_wvip', 'mysql_cluster_rvip', 'username', 'password', 'port'],
            'mongodb_cluster': ['mongodb_cluster_ip1', 'mongodb_cluster_ip2', 'mongodb_cluster_ip3', 'username', 'password', 'port'],
            'redis_cluster': ['redis_cluster_vip', 'username', 'password', 'port'],
            'docker': ['ip_address', 'username', 'password', 'port'],
        },
        'p_codes': p_codes,
    }
    data_str = json.dumps(data)
    err_msg = None
    try:
        result = requests.post(url, headers=headers, data=data_str)
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message.message
    except BaseException as e:
        err_msg = e.message
    if err_msg:
        return False, err_msg

    result = result.json()
    data = result.get('result', {}).get('res', {})
    code = result.get('code', -1)
    if code == 2002:
        resources_dic = {}
        for p_code, items in data.items():
            resource_info = format_resource_info(items)
            resources_dic[p_code] = resource_info

        return True, resources_dic
    else:
        return False, None



def get_resource_by_id(resource_id):
    err_msg = None
    resource_info = {}
    resource = ResourceModel.objects.get(res_id=resource_id)
    try:
        headers = {'Content-Type': 'application/json'}
        data = {
            'layer_count': 3,
            'total_count': 50,
            'reference_sequence': [{'child': 2}, {'bond': 1}],
            'item_filter': ['docker', 'mongodb_cluster', 'mysql_cluster', 'redis_cluster'],
            'columns_filter': {
                'mysql_cluster': ['mysql_cluster_wvip', 'mysql_cluster_rvip', 'username', 'password', 'port'],
                'mongodb_cluster': ['mongodb_cluster_ip1', 'mongodb_cluster_ip2', 'mongodb_cluster_ip3', 'username',
                                    'password', 'port'],
                'redis_cluster': ['redis_cluster_vip', 'username', 'password', 'port'],
                'docker': ['ip_address', 'username', 'password', 'port'],
            },
        }
        data_str = json.dumps(data)
        CMDB_URL = current_app.config['CMDB_URL']
        url = CMDB_URL + 'cmdb/api/repo_relation/' + resource.cmdb_p_code + '/'
        logging.debug('UOP get_db_info: url is %(url)s, data is %(data)s', {'url': url, 'data': data})

        result = requests.get(url, headers=headers, data=data_str)
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
            resource_info = format_resource_info(data)
        else:
            err_msg = 'resource('+resource_id+') not found.'

    logging.debug('UOP get_db_info: resource_info is %(ri)s', {'ri': resource_info})
    return err_msg, resource_info


def deploy_to_crp(deploy_item, resource_info, resource_name, database_password):
    res_obj = ResourceModel.objects.get(res_id=deploy_item.resource_id)
    data = {
        "deploy_id": deploy_item.deploy_id,
    }
    if resource_info.get('mysql_cluster'):
        data['mysql'] = {
            "ip": resource_info['mysql_cluster']['wvip'],
            "port": resource_info['mysql_cluster']['port'],
            "database_user": resource_name,
            "database_password": database_password,
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
        # data['docker'] = {
        #     "image_url": deploy_item.app_image,
        #     "ip": resource_info['docker']['ip_address']
        # }
        docker_list = []
        for obj in res_obj.compute_list:
            try:
                docker_list.append(
                    {
                        'url': obj.url,
                        'ip': obj.ips,
                    }
                )
            except AttributeError as e:
                print e
        data['docker'] = docker_list

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
        logging.debug("Data args is " + str(data))
        logging.debug("Data args is " + str(data_str))
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
        if (len(file_name) == 0) and (len(file_content) == 0):
            upload_file = ''
        elif (len(file_name) == 0) and (len(file_content) != 0):
            raise ServerError('disconf name can not be null.')
        elif (len(file_name) != 0) and (len(file_content) == 0):
            raise ServerError('disconf content can not be null.')
        else:
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
        parser.add_argument('approval_status', type=str, location='args')

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
        if args.approval_status:
            condition['approve_status'] = args.approval_status

        deployments = []
        try:

            for deployment in Deployment.objects.filter(**condition).order_by('-created_time'):
                #返回disconf的json
                disconf = []
                for disconf_info in deployment.disconf_list:
                    server_name = disconf_info.disconf_server_name
                    if (server_name is None) or (len(server_name.strip()) == 0):
                        server_name = '172.28.11.111'
                    disconf_api_connect = DisconfServerApi(server_name)
                    instance_info = dict(ins_name = disconf_info.ins_name,
                                         ins_id = disconf_info.ins_id,
                                         dislist = [dict(disconf_tag = disconf_info.disconf_tag,
                                                        disconf_name = disconf_info.disconf_name,
                                                        disconf_content = disconf_info.disconf_content,
                                                        disconf_admin_content = disconf_info.disconf_admin_content,
                                                        disconf_server_name = disconf_info.disconf_server_name,
                                                        disconf_version = disconf_info.disconf_version,
                                                        disconf_id = disconf_info.disconf_id,
                                                        disconf_env = disconf_api_connect.disconf_env_name(env_id=disconf_info.disconf_env)
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
                    'database_password': deployment.database_password,
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
        parser.add_argument('database_password',type=str, location='json')


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
        database_password = args.database_password

        approve_suggestion = args.approve_suggestion
        apply_status = args.apply_status
        approve_status = args.approve_status
        if args.dep_id:
            dep_id = args.dep_id

        deploy_result = 'deploying'

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
            #disconf配置
                #1、由于管理员要重新上传文件，所以需要重新获取文件名称
                for instance_info in disconf:
                    for disconf_info in instance_info.get('dislist'):
                        disconf_id = instance_info.get('disconf_id')
                        disconf_obj = DisconfIns.objects.get(disconf_id)
                        disconf_obj.disconf_admin_content = disconf_info.get('disconf_admin_content')
                        disconf_obj.disconf_server_name = disconf_info.get('disconf_server_name')
                        disconf_obj.save()

                print

                """
                #3、把配置推送到disconf
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                disconf_result = []
                for disconf_info in deploy_obj.disconf_list:
                    if (len(disconf_info.disconf_name.strip()) == 0) or (len(disconf_info.disconf_content.strip()) == 0):
                        continue
                    else:
                        disconf_admin_name = exchange_disconf_name(disconf_info.disconf_admin_content)
                        #server_name = disconf_info.disconf_server_name
                        server_name = '172.28.11.111'
                        if (server_name is None) or (len(server_name.strip()) == 0):
                            server_name = '172.28.11.111'
                        disconf_api_connect = DisconfServerApi(server_name)
                        result,message = disconf_api_connect.disconf_add_app_config_api_file(
                                                        app_name=disconf_info.ins_name,
                                                        myfilerar=disconf_admin_name,
                                                        version=disconf_info.disconf_version,
                                                        env_id=disconf_info.disconf_env
                                                        )

                    disconf_result.append(dict(result=result,message=message))
                deploy_obj.save()
                message = disconf_result

            #CRP配置
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'success'
                err_msg, resource_info = get_resource_by_id(deploy_obj.resource_id)
                if not err_msg:
                    err_msg, result = deploy_to_crp(deploy_obj, resource_info, resource_name, database_password)
                    if err_msg:
                        deploy_obj.deploy_result = 'fail'
                        print 'deploy_to_crp err: '+err_msg
                    else:
                        print 'deploy_to_crp response: '+result
                else:
                    raise Exception(err_msg)
                deploy_obj.save()
                """
            elif action == 'admin_approve_forbid':  # 管理员审批不通过
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'fail'
                deploy_obj.deploy_result = 'not_deployed'
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
                    database_password=database_password,
                )

                for instance_info in disconf:
                    for disconf_info in instance_info.get('dislist'):
                        #以内容形式上传，需要将内容转化为文本
                        if disconf_info.get('disconf_tag') == 'tag':
                            file_name = disconf_info.get('disconf_name')
                            file_content = disconf_info.get('disconf_content')
                            ins_name = instance_info.get('ins_name')
                            upload_file = disconf_write_to_file(file_name=file_name,
                                                                file_content=file_content,
                                                                instance_name=ins_name,
                                                                type='disconf')
                            disconf_info['disconf_content'] = upload_file
                            disconf_info['disconf_admin_content'] = ''
                        #以文本形式上传，只需获取文件名
                        else:
                            file_name = disconf_info.get('disconf_name')
                            if len(file_name.strip()) == 0:
                                upload_file = ''
                                disconf_info['disconf_content'] = upload_file
                                disconf_info['disconf_admin_content'] = upload_file

                        ins_name = instance_info.get('ins_name')
                        ins_id = instance_info.get('ins_id')
                        disconf_tag=disconf_info.get('disconf_tag')
                        disconf_name = disconf_info.get('disconf_name')
                        disconf_content = disconf_info.get('disconf_content')
                        disconf_admin_content = disconf_info.get('disconf_admin_content')
                        disconf_server_name = disconf_info.get('disconf_server_name')
                        disconf_version = disconf_info.get('disconf_version')
                        disconf_env = disconf_info.get('disconf_env')
                        disconf_id = str(uuid.uuid1())
                        disconf_ins = DisconfIns(ins_name=ins_name, ins_id=ins_id,
                                                 disconf_tag=disconf_tag,
                                                 disconf_name = disconf_name,
                                                 disconf_content = disconf_content,
                                                 disconf_admin_content = disconf_admin_content,
                                                 disconf_server_name = disconf_server_name,
                                                 disconf_version = disconf_version,
                                                 disconf_env = disconf_env,
                                                 disconf_id = disconf_id,
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
                disconf_uid = str(uuid.uuid1())
                instance_name = request.form.get('instance_name')
                user_id = request.form.get('user_id')
                index = request.form.get('index')
                filename = '{file_name},{uuid}'.format(file_name=file.filename,uuid=disconf_uid)
                upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], type, instance_name, user_id)
                if not os.path.exists(upload_path):
                    os.makedirs(upload_path)
                path = os.path.join(upload_path,filename)
            else:
                filename = file.filename + '_' + uid
                index = request.form.get('index')
                path = os.path.join(UPLOAD_FOLDER, type, filename)
                if not os.path.exists(os.path.join(UPLOAD_FOLDER, type)):
                    os.makedirs(os.path.join(UPLOAD_FOLDER, type))
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
