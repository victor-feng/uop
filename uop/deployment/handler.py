# -*- coding: utf-8 -*-

import uuid
import requests
import json
import datetime
import os
import logging
import random

import copy
from flask import request, send_from_directory
from flask_restful import reqparse, Api, Resource
from flask import current_app
from uop.deployment import deployment_blueprint
from uop.models import Deployment, ResourceModel, DisconfIns, ComputeIns, Deployment, Approval, Capacity
from uop.deployment.errors import deploy_errors
from uop.disconf.disconf_api import *
from config import APP_ENV, configs
from uop.util import get_CRP_url



deployment_api = Api(deployment_blueprint, errors=deploy_errors)

def format_resource_info(items):
    resource_info = {}
    for item in items.get('items'):
        colunm = {}
        for i in item.get('column'):
            if i.get('p_code') is not None:
                colunm[i.get('p_code')] = i.get('value')
        if item.get('item_id') == "docker":
            if colunm.get('ip_address', '127.0.0.1') == "172.28.36.44":
                logging.info("####items:{}".format(items))
            resource_info.setdefault('docker', []).append({'ip_address': colunm.get('ip_address', '127.0.0.1')})
        else:
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
            elif item.get('item_id') == 'mongodb_instance':
                resource_info[item.get('item_id')]['vip'] = colunm.get('ip_address', '127.0.0.1')
    # logging.info("####resource_info:{}".format(resource_info))
    return resource_info


def get_resource_by_id_mult(p_codes):
    CMDB_URL = current_app.config['CMDB_URL']
    url = CMDB_URL + 'cmdb/api/repo_relation/'
    headers = {'Content-Type': 'application/json'}
    data = {
        'layer_count': 3,
        'total_count': 50,
        'reference_sequence': [{'child': 2}, {'bond': 1}],
        'item_filter': ['docker', 'mongodb_cluster', 'mysql_cluster', 'redis_cluster', 'mongodb_instance'],
        'columns_filter': {
            'mysql_cluster': ['mysql_cluster_wvip', 'mysql_cluster_rvip', 'username', 'password', 'port'],
            'mongodb_cluster': ['mongodb_cluster_ip1', 'mongodb_cluster_ip2', 'mongodb_cluster_ip3', 'username',
                                'password', 'port'],
            'mongodb_instance': ['ip_address', 'username', 'password', 'port'],
            'redis_cluster': ['redis_cluster_vip', 'username', 'password', 'port'],
            'docker': ['ip_address', 'username', 'password', 'port'],
        },
        'p_codes': p_codes
    }
    data_str = json.dumps(data)
    err_msg = None
    try:
        result = requests.post(url, headers=headers, data=data_str)
        # logging.info("@@@@result:{}".format(result.json()))
    except requests.exceptions.ConnectionError as rq:
        err_msg = rq.message
    except Exception as e:
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
            'layer_count': 10,
            'total_count': 50,
            'reference_type':["dependent"],
            'reference_sequence': [{'child': 3}, {'bond': 2}, {'parent': 5}],
            'item_filter': ['docker', 'mongodb_cluster', 'mysql_cluster', 'redis_cluster', 'mongodb_instance'],
            'columns_filter': {
                'mysql_cluster': ['mysql_cluster_wvip', 'mysql_cluster_rvip', 'username', 'password', 'port'],
                'mongodb_cluster': ['mongodb_cluster_ip1', 'mongodb_cluster_ip2', 'mongodb_cluster_ip3', 'username',
                                    'password', 'port','ip_address'],
                'mongodb_instance': ['ip_address', 'username', 'password', 'port', "dbtype"],
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
        logging.info('data: '+json.dumps(result))
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


def deploy_to_crp(deploy_item, resource_info, resource_name, database_password, appinfo, disconf_server_info):
    res_obj = ResourceModel.objects.get(res_id=deploy_item.resource_id)
    data = {
        "deploy_id": deploy_item.deploy_id,
        "appinfo": appinfo,
        "disconf_server_info": disconf_server_info,
        "dns":[],
    }
    if appinfo: # 判断nginx信息，没有则不推送dns配置
        for app_info in res_obj.compute_list:
            dns_info = {'domain': app_info.domain,
                        'domain_ip': app_info.domain_ip
                        }
            data['dns'].append(dns_info)

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
            "vip": resource_info['mongodb_instance']['vip'],
            "port": resource_info['mongodb_cluster']['port'],
            # TODO test data
            "db_username": resource_name,
            "db_password": database_password,
            # "db_username": 'victor',
            # "db_password": '123456',
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
                        'ins_name': obj.ins_name,
                        'ip': obj.ips,
                    }
                )
            except AttributeError as e:
                print e
        data['docker'] = docker_list

    err_msg = None
    result = None
    try:
        CPR_URL = get_CRP_url(res_obj['env'])
        url = CPR_URL + "api/deploy/deploys"
        headers = {
            'Content-Type': 'application/json',
        }
        #上传disconf配置文件
        upload_disconf_files_to_crp(disconf_info_list=disconf_server_info,env=res_obj['env'])

        file_paths = []
        if deploy_item.mysql_context:
            file_paths.append(('mysql',deploy_item.mysql_context))
        if deploy_item.redis_context:
            file_paths.append(('redis', deploy_item.redis_context))
        if deploy_item.mongodb_context:
            file_paths.append(('mongodb', deploy_item.mongodb_context))

        if file_paths:
            res = upload_files_to_crp(file_paths, res_obj['env'])
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


def upload_files_to_crp(file_paths, env):

    CPR_URL = get_CRP_url(env)
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


def upload_disconf_files_to_crp(disconf_info_list,env):
    """
    上传disconf文件到crp
    :param disconf_info:
    :param env:
    :return:
    """
    CPR_URL = get_CRP_url(env)
    url = CPR_URL + "api/deploy/upload"
    try:
        res = []
        for disconf_info in disconf_info_list:
            disconf_type = 'disconf'
            disconf_admin_content = disconf_info.get('disconf_admin_content','')
            disconf_content = disconf_info.get('disconf_content','')
            if len(disconf_admin_content.strip()) == 0 and len(disconf_content.strip()) == 0:
                continue
            else:
                if len(disconf_admin_content.strip()) != 0:
                    if os.path.exists(disconf_admin_content):
                        data = dict(
                            type = disconf_type,
                            disconf_file_path = disconf_admin_content,
                        )
                        files = {'file': open(disconf_admin_content,'rb')}
                        result = requests.post(url=url, files=files, data=data)

                    else:
                        raise ServerError('disconf admin file does not exist')
                else:
                    if os.path.exists(disconf_content):
                        data = dict(
                            type = disconf_type,
                            disconf_file_path = disconf_content,
                        )
                        files = {'file': open(disconf_content,'rb')}
                        result = requests.post(url=url, files=files, data=data)
                    else:
                        raise ServerError('disconf content file does not exist')
                res.append(result)
        return res
    except Exception as e:
        raise ServerError(e.args)






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


def attach_domain_ip(compute_list, res):
        old_compute_list = res.compute_list
        appinfo = []
        # flag = False
        # for c in compute_list:
        #     # if not c.get("domain_ip", ""):
        #     #     return False, appinfo
        #     if c.get("domain_ip", ""):
        #         flag = True
        #         break
        # if not flag:
        #     return False, appinfo #不需要上传nginx配置，直接返回，不做入库操作
        try:
            for i in old_compute_list:
                tmp = [x for x in compute_list if str(x["ins_id"]) == str(i.ins_id) and x.get("domain_ip", "")]
                if len(tmp) > 0:
                    tmp=tmp[0]
                    tmp["ips"] = i.ips
                    appinfo.append(tmp) # 将配置了nginx IP的 app传回，以便传回crp进行配置推送
            for i in xrange(0, len(old_compute_list)): # 更新resources表中的镜像url和可能配置nginx IP信息
                match_one = filter(lambda x: x["ins_id"] == old_compute_list[i].ins_id, compute_list)[0]
                o = old_compute_list[i]
                old_compute_list.remove(old_compute_list[i])
                compute = ComputeIns(ins_name=o.ins_name, ips=o.ips, ins_id=o.ins_id, cpu=o.cpu, mem=o.mem,
                                             url=match_one["url"], domain=o.domain, quantity=o.quantity, port=o.port, domain_ip=match_one.get("domain_ip", ""))
                old_compute_list.insert(i, compute)
                res.save()
            return appinfo
        except Exception as e:
            logging.error( "attach domain_ip to appinfo error:{}".format(e.args))
            return []


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
        parser.add_argument('approve_status', type=str, location='args')

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
        if args.approve_status:
            condition['approve_status'] = args.approve_status

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
                                                        disconf_content = disconf_info.disconf_content,
                                                        disconf_admin_content = disconf_info.disconf_admin_content,
                                                        disconf_server_name = disconf_info.disconf_server_name,
                                                        disconf_version = disconf_info.disconf_version,
                                                        disconf_id = disconf_info.disconf_id,
                                                        disconf_env = disconf_info.disconf_env,
                                                        disconf_app_name=disconf_info.disconf_app_name
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
                    'app_image': eval(str(deployment.app_image)),
                    # 'app_image': type(deployment.app_image),
                    'created_time': str(deployment.created_time),
                    'deploy_result': deployment.deploy_result,
                    'apply_status': deployment.apply_status,
                    'approve_status': deployment.approve_status,
                    'disconf': disconf,
                    'database_password': deployment.database_password,
                    'is_deleted':deployment.is_deleted,
                    'is_rollback':deployment.is_rollback
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
        parser.add_argument('app_image', type=list, location='json')

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

        #deploy_result = 'deploying'

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
                #修改deploy_result状态为部署中
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.deploy_result='deploying'
                deploy_obj.save()
            #disconf配置
                #1、将disconf信息更新到数据库
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                for instance_info in disconf:
                    for disconf_info_front in instance_info.get('dislist'):
                        disconf_id = disconf_info_front.get('disconf_id')
                        for disconf_info in deploy_obj.disconf_list:
                            if disconf_info.disconf_id == disconf_id:
                                disconf_info.disconf_admin_content = disconf_info_front.get('disconf_admin_content')
                                disconf_info.disconf_server_name = disconf_info_front.get('disconf_server_name')
                                disconf_info.disconf_server_url = disconf_info_front.get('disconf_server_url')
                                disconf_info.disconf_server_user = disconf_info_front.get('disconf_server_user')
                                disconf_info.disconf_server_password = disconf_info_front.get('disconf_server_password')
                                disconf_info.disconf_env = disconf_info_front.get('disconf_env')
                                disconf_info.disconf_app_name = disconf_info_front.get('disconf_app_name')
                deploy_obj.save()

                #将computer信息如IP，更新到数据库
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.app_image = str(app_image)
                deploy_obj.save()
                resource = ResourceModel.objects.get(res_id=resource_id)
                appinfo = attach_domain_ip(app_image, resource)

                #2、把配置推送到disconf
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                disconf_server_info = []
                for disconf_info in deploy_obj.disconf_list:
                    if (len(disconf_info.disconf_name.strip()) == 0) or (len(disconf_info.disconf_content.strip()) == 0):
                        continue
                    else:
                        server_info = {'disconf_server_name':disconf_info.disconf_server_name,
                                       'disconf_server_url':disconf_info.disconf_server_url,
                                       'disconf_server_user':disconf_info.disconf_server_user,
                                       'disconf_server_password':disconf_info.disconf_server_password,
                                       'disconf_admin_content':disconf_info.disconf_admin_content,
                                       'disconf_content':disconf_info.disconf_content,
                                       'disconf_env':disconf_info.disconf_env,
                                       'disconf_version':disconf_info.disconf_version,
                                       'ins_name':disconf_info.ins_name,
                                       'disconf_app_name': disconf_info.disconf_app_name,
                                       }
                        disconf_server_info.append(server_info)
                        '''
                        server_info = {'disconf_server_name':'172.28.11.111',
                                       'disconf_server_url':'http://172.28.11.111:8081',
                                       'disconf_server_user':'admin',
                                       'disconf_server_password':'admin',
                                       }

                        disconf_api_connect = DisconfServerApi(server_info)
                        if disconf_info.disconf_env.isdigit():
                            env_id = disconf_info.disconf_env
                        else:
                            env_id = disconf_api_connect.disconf_env_id(env_name=disconf_info.disconf_env)
                        result,message = disconf_api_connect.disconf_add_app_config_api_file(
                                                        app_name=disconf_info.ins_name,
                                                        myfilerar=disconf_admin_name,
                                                        version=disconf_info.disconf_version,
                                                        env_id=env_id
                                                        )

                    disconf_result.append(dict(result=result,message=message))
                        '''
                deploy_obj.save()
                #message = disconf_result
                message = disconf_server_info

            ##推送到crp
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'success'
                err_msg, resource_info = get_resource_by_id(deploy_obj.resource_id)

                if not err_msg:
                    err_msg, result = deploy_to_crp(deploy_obj, resource_info, resource_name, database_password, appinfo, disconf_server_info)
                    if err_msg:
                        deploy_obj.deploy_result = 'deploy_fail'
                        print 'deploy_to_crp err: '+ err_msg
                    else:
                        print 'deploy_to_crp response: '+ result
                else:
                    raise Exception(err_msg)
                deploy_obj.save()

            elif action == 'admin_approve_forbid':  # 管理员审批不通过
                deploy_obj = Deployment.objects.get(deploy_id=dep_id)
                deploy_obj.approve_status = 'fail'
                deploy_obj.deploy_result = 'not_deployed'
                deploy_obj.save()
                message = 'approve_forbid success'

            elif action == 'save_to_db':  # 部署申请
                deploy_result = 'deploy_to_approve'
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
                    app_image=str(app_image),
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
                        disconf_server_url = disconf_info.get('disconf_server_url')
                        disconf_server_user = disconf_info.get('disconf_server_user')
                        disconf_server_password = disconf_info.get('disconf_server_password')
                        disconf_version = disconf_info.get('disconf_version')
                        disconf_env = disconf_info.get('disconf_env')
                        disconf_app_name = disconf_info.get('disconf_app_name')
                        disconf_id = str(uuid.uuid1())
                        disconf_ins = DisconfIns(ins_name=ins_name, ins_id=ins_id,
                                                 disconf_tag=disconf_tag,
                                                 disconf_name = disconf_name,
                                                 disconf_content = disconf_content,
                                                 disconf_admin_content = disconf_admin_content,
                                                 disconf_server_name = disconf_server_name,
                                                 disconf_server_url = disconf_server_url,
                                                 disconf_server_user = disconf_server_user,
                                                 disconf_server_password = disconf_server_password,
                                                 disconf_version = disconf_version,
                                                 disconf_env = disconf_env,
                                                 disconf_id = disconf_id,
                                                 disconf_app_name=disconf_app_name,
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
    
    @classmethod
    def delete(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('deploy_id', type=str)
        parser.add_argument('user', type=str)

        args = parser.parse_args()
        user = args.user
        deploy_id = args.deploy_id
        logging.info("delete deployment:{}".format(deploy_id))
        print "delete deployment:{}".format(deploy_id)
        # if user == "admin":
        #     logging.info("user is admin:will delete deployment immediately")
        #     return cls.delete()
        try:
            deploy = Deployment.objects.get(deploy_id=deploy_id)
            if len(deploy):

                env_ = get_CRP_url(deploy.environment)
                crp_url = '%s%s' % (env_, 'api/deploy/deploys')
                disconf_list = deploy.disconf_list
                disconfs = []
                for dis in disconf_list:
                    dis_ = dis.to_json()
                    disconfs.append(eval(dis_))
                crp_data = {
                    "disconf_list": disconfs,
                    "resources_id": '',
                    "domain_list": [],
                }
                resm = ResourceModel.objects.filter(res_id=deploy.resource_id)
                if resm:
                    for res in resm:
                        crp_data['resources_id'] = res.res_id
                        compute_list = res.compute_list
                        domain_list = []
                        for compute in compute_list:
                            domain = compute.domain
                            domain_ip = compute.domain_ip
                            domain_list.append({"domain": domain, 'domain_ip': domain_ip})
                            crp_data['domain_list'] = domain_list
                        # 调用CRP 删除nginx资源
                        crp_data = json.dumps(crp_data)
                        requests.delete(crp_url, data=crp_data)
                deploy.delete()

                # 回写CMDB
                # cmdb_url = '%s%s%s'%(CMDB_URL, 'api/repores_delete/', resources.res_id)
                # requests.delete(cmdb_url)
        except Exception as e:
            logging.info('----Scheduler_utuls _delete_deploy  function Exception info is %s' % (e))
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Delete deployment  application failed.'
                }
            }
            return ret, 500
        # try:
        #     deploy = Deployment.objects.get(deploy_id=deploy_id)
        #     if len(deploy):
        #         env_ = get_CRP_url(deploy.environment)
        #         crp_url = '%s%s'%(env_, 'api/deploy/deploys')
        #         disconf_list = deploy.disconf_list
        #         disconfs = []
        #         for dis in disconf_list:
        #             dis_ = dis.to_json()
        #             disconfs.append(eval(dis_))
        #         crp_data = {
        #                 "disconf_list" : disconfs,
        #                 "resources_id": '',
        #                 "domain_list":[],
        #                 "resources_id": ''
        #         }
        #         res = ResourceModel.objects.get(res_id=deploy.resource_id)
        #         if res:
        #             #if hasattr(res, 'disconf_list'):
        #             #crp_data['disconf_list'] = res.disconf_list
        #             crp_data['resources_id'] = res.res_id
        #             compute_list = res.compute_list
        #             domain_list = []
        #             for compute in compute_list:
        #                 domain = compute.domain
        #                 domain_ip = compute.domain_ip
        #                 domain_list.append({"domain": domain, 'domain_ip': domain_ip})
        #             crp_data['domain_list'] = domain_list
        #
        #         deploy.delete()
        #         # 调用CRP 删除资源
        #         crp_data = json.dumps(crp_data)
        #         requests.delete(crp_url, data=crp_data)
        #         # 回写CMDB
        #         #cmdb_url = '%s%s%s'%(CMDB_URL, 'api/repores_delete/', resources.res_id)
        #         #requests.delete(cmdb_url)
        #
        #     else:
        #         ret = {
        #             'code': 200,
        #             'result': {
        #                 'res': 'success',
        #                 'msg': 'deployment not found.'
        #             }
        #         }
        #         return ret, 200
        # except Exception as e:
        #     print e
        #     ret = {
        #         'code': 500,
        #         'result': {
        #             'res': 'fail',
        #             'msg': 'Delete deployment  application failed.'
        #         }
        #     }
        #     return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Delete deployment application success.'
            }
        }
        return ret, 200

    @classmethod
    def put(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('deploy_id', type=str)
        parser.add_argument('action', type=str)
        parser.add_argument('user', type=str)
        args = parser.parse_args()
        deploy_id = args.deploy_id
        user = args.user
        action=args.action

        try:
            deploy = Deployment.objects.get(deploy_id=deploy_id)
            if len(deploy):
                if action == 'delete':
                    delete_time = datetime.datetime.now()
                    deploy.is_deleted = 1
                    deploy.deleted_time = delete_time
                elif action=='revoke':
                    deploy.is_deleted = 0
                deploy.save()

            else:
                ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'deployment not found.'
                    }
                }
                return ret, 200
        except Exception as e:
            print e
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Put deployment  application failed.'
                }
            }
            return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Put deployment application success.'
            }
        }
        return ret, 200


class DeploymentAPI(Resource):

    def put(self, deploy_id):
        pass

    def delete(self, deploy_id):
        res_code = 204
        parser = reqparse.RequestParser()
        parser.add_argument('options', type=str)
        parser.add_argument('user_id', type=str)
        args = parser.parse_args()
        deploys = Deployment.objects.filter(deploy_id=deploy_id)
        if deploys:
            for deploy in deploys:
                if args.options == "rollback" and args.user_id == deploy.user_id:
                    flag = deploy.is_rollback
                    repo = ResourceModel.objects.filter(res_id=deploy.resource_id)
                    if repo:
                        for r in repo:
                            r.reservation_status = "set_success"
                            r.save()
                        deploy.is_rollback = 1 if flag == 0 else 0
                    else:
                        deploy.is_rollback = 1 if flag == 0 else 0
                        ret = {
                            'code': 203,
                            'result': {
                                'res': 'success rollback, but resource not found',
                                'msg': 'The deployment for its resource had been deleted.'
                            }
                        }
                        return ret, 200
                    deploy.save()
            ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'Rollback deployment success.'
                    }
            }
            return ret, 200
            # deploys.delete()
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
                'msg': e.args
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

class CapacityAPI(Resource):
    '容量改变 扩容或者缩容 的提交申请'
    @classmethod
    def put(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('cluster_id', type=str)
        parser.add_argument('number', type=str)
        parser.add_argument('res_id', type=str)
        parser.add_argument('department_id', type=str)
        parser.add_argument('creator_id', type=str)
        parser.add_argument('project_id', type=str)
        parser.add_argument('initiator', type=str)
        parser.add_argument('project_name', type=str)

        args = parser.parse_args()
        project_id = args.project_id
        department_id = args.department_id
        creator_id = args.creator_id
        cluster_id = args.cluster_id
        number = args.number
        res_id = args.res_id
        initiator = args.initiator
        project_name = args.project_name
        try:
            resources = ResourceModel.objects.filter(res_id=res_id)
            if len(resources):
                resource = resources[0]
                compute_list = resource.compute_list
                for compute_ in compute_list:
                    if compute_.ins_id == cluster_id:
                        if int(number) > int(compute_.quantity):
                            num = int(number) - int(compute_.quantity)
                            capacity_status = 'increate'
                        else:
                            num = int(compute_.quantity) - int(number)
                            capacity_status = 'reduce'
                        approval_id = str(uuid.uuid1())
                        capacity = Capacity(capacity_id=approval_id, numbers=num)
                        capacity_list = compute_.capacity_list
                        capacity_list.append(capacity)
                        resource.save()

                        approval_status = '%sing'%(capacity_status)
                        create_date = datetime.datetime.now()
                        deployments = Deployment.objects.filter(resource_id=res_id).order_by('-created_time')
                        if deployments:
                            old_deployment = deployments[0]
                            deploy_item = Deployment(
                                deploy_id=approval_id,
                                deploy_name=old_deployment.deploy_name,
                                initiator=old_deployment.initiator,
                                user_id=old_deployment.user_id,
                                project_id=old_deployment.project_id,
                                project_name=old_deployment.project_name,
                                resource_id=old_deployment.resource_id,
                                resource_name=old_deployment.resource_name,
                                created_time=old_deployment.created_time,
                                environment=old_deployment.environment,
                                release_notes=old_deployment.release_notes,
                                mysql_tag=old_deployment.mysql_tag,
                                mysql_context=old_deployment.mysql_context,
                                redis_tag=old_deployment.redis_tag,
                                redis_context=old_deployment.redis_context,
                                mongodb_tag=old_deployment.mongodb_tag,
                                mongodb_context=old_deployment.mongodb_context,
                                app_image=old_deployment.app_image,
                                deploy_result="deploy_to_approve",
                                apply_status="success",
                                approve_status=approval_status,
                                approve_suggestion=old_deployment.approve_suggestion,
                                database_password=old_deployment.database_password,
                                disconf_list=old_deployment.disconf_list
                            )
                            deploy_item.save()
                        Approval(approval_id=approval_id, resource_id=res_id,
                            project_id=project_id,department_id=department_id,
                            creator_id=creator_id,create_date=create_date,
                            approval_status=approval_status, capacity_status=capacity_status).save()
            else:
                ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'resource not found.'
                    }
                }
                return ret, 200
        except Exception as e:
            print e
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Put deployment  application failed.'
                }
            }
            return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Put deployment capacity application success.'
            }
        }
        return ret, 200

   # '资源实例的集群信息'
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str, location='args')
        args = parser.parse_args()
        res_id = args.res_id
        rst = []
        try:
            resource = ResourceModel.objects.get(res_id=res_id)
            if len(resource):
                compute_list = resource.compute_list
                for compute_ in compute_list:
                    quantity = compute_.quantity
                    ins_name = compute_.ins_name
                    rst.append({"quantity": quantity, "ins_name": ins_name, 'res_id': res_id, "ins_id": compute_.ins_id, "resource_name": resource.resource_name})
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

class CapacityInfoAPI(Resource):

   # '获取扩容详情'
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('approval_id', type=str, location='args')
        parser.add_argument('res_id', type=str, location='args')
        args = parser.parse_args()
        approval_id = args.approval_id
        res_id = args.res_id
        rst_dict = {}
        rst = []
        cur_capacity_list = []
        try:
            resource = ResourceModel.objects.get(res_id=res_id)
            if len(resource):
                compute_list = resource.compute_list
                for compute_ in compute_list:
                    capacity_list = compute_.capacity_list
                    for capacity_ in capacity_list:
                        tmp = {'cluster_id': compute_.ins_id, 'ins_name': compute_.ins_name,
                               'cpu': compute_.cpu, 'mem': compute_.mem, 'url': compute_.url,
                               'port':compute_.port, "capacity_id": capacity_.capacity_id,
                               "quantity": compute_.quantity, 'domain_ip': compute_.domain_ip,
                               'domain': compute_.domain }
                        tmp['meta'] = compute_.docker_meta if getattr(compute_, "docker_meta", "") else ""
                        if capacity_.capacity_id == approval_id:
                            cur_data = tmp
                            tmp2= copy.deepcopy(tmp)
                            tmp2["quantity"] = int(compute_.quantity) + int(capacity_.numbers)
                            rst.append(tmp2)
                        tmp_app = Approval.objects.filter(approval_id=capacity_.capacity_id, approval_status__contains='success')
                        if tmp_app:
                            cur_capacity_list.append(tmp2)

                if len(cur_capacity_list) > 1:
                    cur_data = cur_capacity_list[-1]
                rst.insert(0, cur_data)
                rst_dict["resource_name"] = resource.resource_name
                rst_dict["project"] = resource.project
                rst_dict["compute_list"] = rst
                rst_dict["env"] = resource.env
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
            return rst_dict, 200


deployment_api.add_resource(DeploymentListAPI, '/deployments')
deployment_api.add_resource(DeploymentAPI, '/deployments/<deploy_id>/')
deployment_api.add_resource(DeploymentListByByInitiatorAPI, '/getDeploymentsByInitiator')
deployment_api.add_resource(Upload, '/upload')
deployment_api.add_resource(Download, '/download/<file_name>')
deployment_api.add_resource(CapacityAPI, '/capacity')
deployment_api.add_resource(CapacityInfoAPI, '/capacity/info')
