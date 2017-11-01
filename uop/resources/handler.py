# -*- coding: utf-8 -*-
import json
import requests
import copy
import time
import random
import logging
from flask import request, make_response
from flask import redirect
from flask import jsonify
import uuid
from urllib2 import unquote
import datetime
import hashlib
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with

from uop.deployment.handler import get_resource_by_id, get_resource_by_id_mult
from uop.resources import resources_blueprint
from uop.models import ResourceModel, DBIns, ComputeIns, Deployment, NetWorkConfig
from uop.resources.errors import resources_errors
from uop.util import get_CRP_url
from config import APP_ENV, configs

CMDB_URL = configs[APP_ENV].CMDB_URL
CRP_URL = configs[APP_ENV].CRP_URL
# TODO: move to global conf
dns_env = {'develop': '172.28.5.21', 'test': '172.28.18.212'}
resources_api = Api(resources_blueprint, errors=resources_errors)


def make_random_database_password():
    return str(random.randint(100000, 999999)) + chr(random.randint(65, 90)) + chr(
        random.randint(97, 122)) + '!'

def _match_condition_generator(args):
    match = dict()
    if args.user_id or args.resource_name or args.project or args.formStatus or args.approval_status\
            or (args.start_time and args.end_time):
        match_cond = dict()
        match_dict = dict()
        match_list = []
        if args.user_id:
            match_cond['user_id'] = args.user_id
        if args.resource_name:
            match_cond['resource_name'] = args.resource_name
        if args.project:
            match_cond['project'] = args.project
        if args.formStatus:
            match_cond['application_status'] = args.formStatus
        if args.approval_status:
            match_cond['approval_status'] = args.approval_status
        if args.start_time and args.end_time:
            created_date_dict = dict()
            created_date_dict['$gte'] = datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
            created_date_dict['$lte'] = datetime.datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
            match_cond['created_date'] = created_date_dict
        match_list.append(match_cond)
        match_dict['$and'] = match_list
        match['$match'] = match_dict
    return match


class ResourceApplication(Resource):
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('resource_name', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('project_id', type=str)
        parser.add_argument('department', type=str)
        parser.add_argument('user_name', type=str)
        parser.add_argument('user_id', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('formStatus', type=str)
        parser.add_argument('approval_status', type=str)
        parser.add_argument('resource_list', type=list, location='json')
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()

        resource_name = args.resource_name
        project = args.project
        project_id = args.project_id
        department = args.department
        department_id = '1'
        res_id = str(uuid.uuid1())
        user_name = args.user_name
        user_id = args.user_id
        domain = args.domain
        env = args.env
        created_date = datetime.datetime.now()
        application_status = args.formStatus
        approval_status = "unsubmit"
        resource_list = args.resource_list
        compute_list = args.compute_list

        try:
            if ResourceModel.objects.filter(resource_name=resource_name, env=env).count():
                res = {
                    'code': 200,
                    'result': {
                        'res': 'fail',
                        'msg': '该资源名称在所选环境已存在',
                        'res_name': resource_name
                    }
                }
                return res, 200
        except Exception as e:
            print e
            return
        resource_application = ResourceModel(resource_name=resource_name, project=project, department=department,
                                             department_id=department_id, res_id=res_id, project_id=project_id,
                                             user_name=user_name, user_id=user_id, domain=domain, env=env,
                                             application_status=application_status, approval_status=approval_status,
                                             reservation_status="unreserved", created_date=created_date)
        for resource in resource_list:
            # m = hashlib.md5()
            ins_name = resource.get('res_name', '未知名称')
            # m.update(ins_name)
            # ins_name = m.hexdigest()
            # ins_id = resource.get('res_id')
            ins_id = str(uuid.uuid1())
            ins_type = resource.get('res_type')
            cpu = resource.get('cpu')
            mem = resource.get('mem')
            disk = resource.get('disk')
            quantity = resource.get('quantity')
            version = resource.get('version')
            db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
                           quantity=quantity, version=version)
            resource_application.resource_list.append(db_ins)

        ins_name_list = []
        if compute_list:
            for compute in compute_list:
                ins_name = compute.get('ins_name')
                ins_name_list.append(ins_name)
                # ins_id = compute.get('ins_id')
                ins_id = str(uuid.uuid1())
                cpu = compute.get('cpu')
                mem = compute.get('mem')
                url = compute.get('url')
                domain = compute.get('domain')
                domain_ip = compute.get('domain_ip')
                quantity = compute.get('quantity')
                port = compute.get('port')
                meta_str = compute.get('meta')
                try:
                    meta = json.dumps(meta_str)
                except Exception as e:
                    code = 500
                    res = {
                        'code': code,
                        'result': {
                            'res': 'fail',
                            'msg': 'meta is not JSON object!'
                        }
                    }
                    return res, code
                compute_ins = ComputeIns(ins_name=ins_name, ins_id=ins_id, cpu=cpu, mem=mem,url=url, domain=domain,
                                         domain_ip=domain_ip, quantity=quantity, port=port, docker_meta=meta_str)
                resource_application.compute_list.append(compute_ins)

        if ins_name_list:
            ins_name_list2 = list(set(ins_name_list))
            if len(ins_name_list) != len(ins_name_list2):
                code = 200
                res = {
                    'code': code,
                    'result': {
                        'res': 'fail',
                        'msg': '集群名称重复'
                    }
                }
                return res, code
        try:
            for insname in ins_name_list:
                if ResourceModel.objects(compute_list__match={'ins_name': insname}).filter(env=env).count() > 0:
                    code = 200
                    res = {
                        'code': code,
                        'result': {
                            'res': 'fail',
                            'msg': '集群名称重复'
                        }
                    }
                    return res, code
        except Exception as e:
            code = 500
            res = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': 'Query DB error.'
                }
            }
            return res, code

        try:
            resource_application.save()
        except Exception as e:
            code = 200
            res = {
                "code": code,
                "result": {
                       'res': 'fail',
                       'msg': 'Create resource application fail. ' + e.message
                }
            }
            return res, code

        res = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Create resource application success.',
                'res_id': res_id,
                'res_name': resource_name
            }
        }

        return res, 200

    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('user_id', type=str, location='args')
        parser.add_argument('resource_name', type=str, location='args')
        parser.add_argument('project', type=str, location='args')
        parser.add_argument('start_time', type=str, location='args')
        parser.add_argument('end_time', type=str, location='args')
        parser.add_argument('agg_by', type=str, location='args')
        # parser.add_argument('application_status', type=str, location='args')
        parser.add_argument('formStatus', type=str, location='args')
        parser.add_argument('approval_status', type=str, location='args')
        parser.add_argument('name', type=str, location='args')
        parser.add_argument('env', type=str, location='args')

        args = parser.parse_args()
        agg_by = args.agg_by
        # agg_match = args.agg_match
        condition = {}
        if args.user_id:
            condition['user_id'] = args.user_id
        if args.resource_name:
            condition['resource_name'] = args.resource_name
        if args.project:
            condition['project'] = args.project
        if args.start_time and args.end_time:
            condition['created_date__gte'] = args.start_time
            condition['created_date__lt'] = args.end_time
        # if args.application_status:
        #     condition['application_status'] = args.application_status
        if args.formStatus:
            condition['application_status'] = args.formStatus
        if args.approval_status:
            condition['approval_status'] = args.approval_status
        if args.name:
            condition['user_name'] = args.name
        if args.env:
            condition['env'] = args.env

        if agg_by:
            pipeline = []
            group1 = dict()
            group2 = dict()
            group1_id_dict = dict()
            agg_dict = dict()
            group2_id_dict = dict()
            group2_ret_dict = dict()
            group2_group_dict = dict()
            agg_dict[agg_by] = '$' + agg_by
            agg_exprs = request.args.getlist('agg_expr')
            for agg_expr in agg_exprs:
                agg_dict[agg_expr] = '$' + agg_expr
            group1_id_dict['_id'] = agg_dict
            group1['$group'] = group1_id_dict

            group2_id_dict[agg_by] = '$_id.' + agg_by
            agg_dict = {}
            for agg_expr in agg_exprs:
                agg_dict[agg_expr] = '$_id.' + agg_expr
            group2_ret_dict['$addToSet'] = agg_dict
            group2_group_dict['_id'] = group2_id_dict
            group2_group_dict['ret'] = group2_ret_dict
            group2['$group'] = group2_group_dict

            match = _match_condition_generator(args)
            if match:
                pipeline.append(match)

            pipeline.append(group1)
            pipeline.append(group2)

            result = ResourceModel._get_collection().aggregate(pipeline)
            code = 200
            ret = {
                'code': code,
                'result': {
                    'res': 'success',
                    'msg': list(result)
                }
            }
            return ret, code

        result_list = []
        try:
            resources = ResourceModel.objects.filter(**condition).order_by('-created_date')
        except Exception as e:
            print e
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret
        if len(resources):
            for res in resources:
                result = dict()
                result['name'] = res.user_name
                result['date'] = str(res.created_date)
                result['resource'] = res.resource_name
                result['formStatus'] = res.application_status
                result['approval_status'] = res.approval_status
                result['project'] = res.project
                result['project_id'] = res.project_id
                result['id'] = res.res_id
                result['reservation_status'] = res.reservation_status
                result['env'] = res.env
                result['is_deleted'] = res.is_deleted
                resource_id=res.res_id
                deploys=Deployment.objects.filter(resource_id=resource_id).order_by("-created_time")
                if deploys:
                    dep=deploys[0]
                    deploy_result=dep.deploy_result
                    result['reservation_status'] = deploy_result
                result_list.append(result)
        code = 200
        ret = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': result_list
            }
        }
        return ret, code
        
    @classmethod
    def delete(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str)
        args = parser.parse_args()
        res_id = args.res_id

        try:
            resources = ResourceModel.objects.get(res_id=res_id)
            if len(resources):
                os_ins_list = resources.os_ins_list
                deploys = Deployment.objects.filter(resource_id=res_id)
                for deploy in deploys:
                    env_ = get_CRP_url(deploy.environment)
                    crp_url = '%s%s'%(env_, 'api/deploy/deploys')
                    disconf_list = deploy.disconf_list
                    disconfs = []
                    for dis in disconf_list:
                        dis_ = dis.to_json()
                        disconfs.append(eval(dis_))
                    crp_data = {
                        "disconf_list" : disconfs,
                        "resources_id": res_id,
                        "domain_list":[],
                    }
                    compute_list = resources.compute_list
                    domain_list = []
                    for compute in compute_list:
                        domain = compute.domain
                        domain_ip = compute.domain_ip
                        domain_list.append({"domain": domain, 'domain_ip': domain_ip})
                    crp_data['domain_list'] = domain_list
                    crp_data = json.dumps(crp_data)
                    requests.delete(crp_url, data=crp_data)
                    #deploy.delete()
                # 调用CRP 删除资源
                crp_data = {
                        "resources_id": resources.res_id,
                        "os_inst_id_list": resources.os_ins_list,
                        "vid_list": resources.vid_list,
                }
                env_ = get_CRP_url(resources.env)
                crp_url = '%s%s'%(env_, 'api/resource/deletes')
                crp_data = json.dumps(crp_data)
                requests.delete(crp_url, data=crp_data)
                cmdb_p_code = resources.cmdb_p_code
                resources.delete()
                # 回写CMDB
                cmdb_url = '%s%s%s'%(CMDB_URL, 'cmdb/api/repores_delete/', cmdb_p_code)
                requests.delete(cmdb_url)
            else:
                ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'Resource not found.'
                    }
                }
                return ret, 200
        except Exception as e:
            print e
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Delete resource application failed.'
                }
            }
            return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Delete resource application success.'
            }
        }
        return ret, 200

    @classmethod
    def put(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str)
        parser.add_argument('action', type=str)
        args = parser.parse_args()
        res_id = args.res_id
        action=args.action
        try:
            resources = ResourceModel.objects.get(res_id=res_id)
            if len(resources):
                if action=='delete':
                    delete_time=datetime.datetime.now()
                    resources.is_deleted=1
                    resources.deleted_date=delete_time
                elif action=='revoke':
                    resources.is_deleted = 0
                resources.save()
            else:
                ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'Resource not found.'
                    }
                }
                return ret, 200
        except Exception as e:
            print e
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Put resource application failed.'
                }
            }
            return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Put resource application success.'
            }
        }
        return ret, 200


class ResourceDetail(Resource):
    @classmethod
    def get(cls, res_id):
        result = {}
        try:
            resources = ResourceModel.objects.filter(res_id=res_id)
        except Exception as e:
            print e
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret
        if len(resources):
            deploies = Deployment.objects.filter(resource_id=res_id).order_by('+created_date')
            if len(deploies):
                deploy = deploies.first()
                database_password = deploy.database_password
            else:
                database_password = make_random_database_password()
            for resource in resources:
                result['resource_name'] = resource.resource_name
                result['project'] = resource.project
                result['project_id'] = resource.project_id
                result['department'] = resource.department
                result['department_id'] = resource.department_id
                result['res_id'] = res_id
                result['user_name'] = resource.user_name
                result['user_id'] = resource.user_id
                result['domain'] = resource.domain
                result['env'] = resource.env
                result['application_status'] = resource.application_status
                result['approval_status'] = resource.approval_status
                result['database_password'] = database_password
                result['docker_network_name']=""
                result['mysql_network_name'] = ""
                result['redis_network_name'] = ""
                result['mongodb_network_name'] = ""
                docker_network_id=resource.docker_network_id
                mysql_network_id = resource.mysql_network_id
                redis_network_id = resource.redis_network_id
                mongodb_network_id = resource.mongodb_network_id
                if docker_network_id:
                    network=NetWorkConfig.objects.filter(vlan_id=docker_network_id).first()
                    docker_network_name=network.name
                    result['docker_network_name'] = docker_network_name
                if mysql_network_id:
                    network=NetWorkConfig.objects.filter(vlan_id=mysql_network_id).first()
                    mysql_network_name=network.name
                    result['mysql_network_name'] = mysql_network_name
                if redis_network_id:
                    network=NetWorkConfig.objects.filter(vlan_id=redis_network_id).first()
                    redis_network_name=network.name
                    result['redis_network_name'] = redis_network_name
                if mongodb_network_id:
                    network=NetWorkConfig.objects.filter(vlan_id=mongodb_network_id).first()
                    mongodb_network_name=network.name
                    result['mongodb_network_name'] = mongodb_network_name
                    
                resource_list = resource.resource_list
                compute_list = resource.compute_list
                if resource_list:
                    res = []
                    for db_res in resource_list:
                        res.append(
                            {
                                "res_name": db_res.ins_name,
                                "res_id": db_res.ins_id,
                                "res_type": db_res.ins_type,
                                "cpu": db_res.cpu,
                                "mem": db_res.mem,
                                "disk": db_res.disk,
                                "quantity": db_res.quantity,
                                "version": db_res.version
                            }
                        )
                if compute_list:
                    com = []
                    for db_com in compute_list:
                        com.append(
                            {
                                "ins_name": db_com.ins_name,
                                "ins_id": db_com.ins_id,
                                "cpu": db_com.cpu,
                                "mem": db_com.mem,
                                "url": db_com.url,
                                "domain": db_com.domain,
                                "quantity": db_com.quantity,
                                "port": db_com.port,
                                "meta": db_com.docker_meta,
                            }
                        )
                result['resource_list'] = res
                result['compute_list'] = com
                code = 200
                ret = {
                    'code': code,
                    'result': {
                        'res': 'success',
                        'msg': result
                    }
                }
        else:
            code = 200
            result = []
            ret = {
                'code': code,
                'result': {
                    'res': 'success',
                    'msg': result
                }
            }
        return ret, code

    @classmethod
    def put(cls, res_id):
        try:
            resource_application = ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            print e
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret
        if not len(resource_application):
            code = 200
            ret = {
                'code': code,
                'result': {
                    'res': 'success',
                    'msg': "Resource not find."
                }
            }
            return ret, 200

        parser = reqparse.RequestParser()
        parser.add_argument('resource_name', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('department', type=str)
        # parser.add_argument('department_id', type=str)
        # parser.add_argument('res_id', type=str)
        parser.add_argument('user_name', type=str)
        parser.add_argument('user_id', type=str)
        parser.add_argument('domain', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('application_status', type=str)
        parser.add_argument('approval_status', type=str)
        parser.add_argument('resource_list', type=list, location='json')
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()

        resource_application.resource_name = args.resource_name
        resource_application.project = args.project
        resource_application.department = args.department
        resource_application.user_name = args.user_name
        resource_application.user_id = args.user_id
        resource_application.domain = args.domain
        resource_application.env = args.env
        resource_application.application_status = args.application_status
        # resource_application.approval_status = args.approval_status
        resource_list = args.resource_list
        compute_list = args.compute_list

        # try:
        #     resource_application.update(pull_all__resource_list=resource_application.resource_list)
        #     ResourceModel.objects(res_id=res_id).update_one(pull__resource_list=resource_application.resource_list)
        #     # resource_application.update(pull_all__compute_list=resource_application.compute_list)
        # except Exception as e:
        #     print e
        #     return
        resource_application.resource_list = []
        resource_application.compute_list = []

        for resource in resource_list:
            ins_name = resource.get('res_name')
            # ins_id = resource.get('res_id')
            ins_id = str(uuid.uuid1())
            ins_type = resource.get('res_type')
            cpu = resource.get('cpu')
            mem = resource.get('mem')
            disk = resource.get('disk')
            quantity = resource.get('quantity')
            version = resource.get('version')
            db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
                           quantity=quantity, version=version)
            resource_application.resource_list.append(db_ins)

        for compute in compute_list:
            ins_name = compute.get('ins_name')
            # ins_id = compute.get('ins_id')
            ins_id = str(uuid.uuid1())
            cpu = compute.get('cpu')
            mem = compute.get('mem')
            url = compute.get('url')
            quantity = compute.get('quantity')
            port = compute.get('port')
            compute_ins = ComputeIns(ins_name=ins_name, ins_id=ins_id, cpu=cpu, mem=mem, url=url,
                                     quantity=quantity, port=port)
            resource_application.compute_list.append(compute_ins)

        try:
            resource_application.save()
        except Exception as e:
            print e
            code = 500
            res = {"code": code,
                   "result": {
                       'res': 'fail',
                       'msg': 'Create resource application fail.'
                   }
            }
            return res, code

        res = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Create resource application success.',
                'res_name': args.resource_name
            }
        }

        return res, 200

    @classmethod
    def delete(cls, res_id):
        try:
            resources = ResourceModel.objects.get(res_id=res_id)
            if len(resources):
                resources.delete()
            else:
                ret = {
                    'code': 200,
                    'result': {
                        'res': 'success',
                        'msg': 'Resource not found.'
                    }
                }
                return ret, 200
        except Exception as e:
            print e
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Delete resource application failed.'
                }
            }
            return ret, 500
        ret = {
            'code': 200,
            'result': {
                'res': 'success',
                'msg': 'Delete resource application success.'
            }
        }
        return ret, 200


class ResourceRecord(Resource):
    @classmethod
    def get(cls, user_id):
        result_list = []
        try:
            resources = ResourceModel.objects.filter(user_id=user_id)
        except Exception as e:
            print e
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret
        if len(resources):
            for res in resources:
                result = dict()
                result['name'] = res.user_name
                result['date'] = res.created_date
                result['resource'] = res.resource_name
                result['formStatus'] = res.application_status
                result['approvalStatus'] = res.approval_status
                result['project'] = res.project
                result['project_id'] = res.project_id
                result['id'] = res.res_id
                result_list.append(result)
        code = 200
        ret = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': result_list
            }
        }
        return ret, code


class GetDBInfo(Resource):
    def get(cls, res_id):
        err_msg, resource_info = get_resource_by_id(res_id)
        mysql_ip = {
            'wvip': resource_info.get('mysql_cluster', {'wvip': '127.0.0.1'}).get('wvip'),
            'rvip': resource_info.get('mysql_cluster', {'rvip': '127.0.0.1'}).get('rvip'),
        }
        redis_ip = {
            'vip': resource_info.get('redis_cluster', {'vip': '127.0.0.1'}).get('vip')
        }
        mongodb_ip = {
            'vip1': resource_info.get('mongodb_cluster', {'vip1': '127.0.0.1'}).get('vip1'),
            'vip2': resource_info.get('mongodb_cluster', {'vip2': '127.0.0.1'}).get('vip2'),
            'vip3': resource_info.get('mongodb_cluster', {'vip3': '127.0.0.1'}).get('vip3'),
            'vip': resource_info.get('mongodb_instance', {'vip': '127.0.0.1'}).get('vip'),
        }
        data = {
            'mysql_ip': mysql_ip,
            'redis_ip': redis_ip,
            'mongodb_ip': mongodb_ip,
        }
        if err_msg:
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': err_msg
                }
            }
        else:
            code = 200
            ret = {
                'code': code,
                'result': {
                    'res': 'success',
                    'msg': data
                }
            }
        return ret, code


class GetMyResourcesInfo(Resource):
    def get(self):
        user_id = request.args.get('user_id')
        resource_type = request.args.get('resource_type',"")
        resource_database = request.args.get('mysqlandmongo',"")
        resource_cache = request.args.get('cache', "")
        resource_type = resource_database or resource_cache or resource_type
        resource_name = request.args.get('resource_name',"")
        item_name = request.args.get('item_name',"")
        # item_code = request.args.get('item_code',"")
        start_time = request.args.get('start_time',"")
        end_time = request.args.get('end_time',"")
        resource_status = request.args.get('resource_status',"")
        page_num=request.args.get('page_num',1)
        env = request.args.get('env',"")
        page_count=request.args.get('page_count',10)
        result_list = []
        url = CMDB_URL + "cmdb/api/vmdocker/status/?resource_type={}&resource_name={}&item_name={}&start_time={}&end_time={}&resource_status={}&page_num={}\
            &page_count={}&env={}&user_id={}".format(resource_type, resource_name, item_name, start_time, end_time, resource_status, page_num, page_count, env, user_id)
        ret = requests.get(url)
        logging.info("ret:{}".format(ret.json()))
        return ret.json()
        # query = {
        #     'approval_status': 'success',
        # }
        #
        # def comparable_time(s):
        #         return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")
        #
        # try:
        #     if user_id:
        #         query['user_id'] = user_id
        #     if resource_name:
        #         query['resource_name'] = resource_name
        #     if item_name:
        #         query['project'] = item_name
        #     if item_code:
        #         query['project_id'] = item_code
        #     resources = ResourceModel.objects.filter(**query).order_by('-created_date')
        #
        # except Exception as e:
        #     print e
        #     code = 500
        #     ret = {
        #         'code': code,
        #         'result': {
        #             'res': 'fail',
        #             'msg': "Resource find error."
        #         }
        #     }
        #     return ret
        # if len(resources):
        #     flag, resources_dic= get_resource_by_id_mult([res.cmdb_p_code for res in resources])
        #     if not flag:
        #         code = 500
        #         logging.error("@@@@result:{}".format(resources_dic))
        #         ret = {
        #             'code': code,
        #             'result': {
        #                 'res': 'fail',
        #                 'msg': '批量查询CMDB接口失败！'
        #             }
        #         }
        #         return ret, code
        #     for res in resources:
        #         rcd = res.created_date
        #         if start_time:
        #             if rcd < comparable_time(start_time):
        #                 continue
        #         if end_time:
        #             if rcd > comparable_time(end_time):
        #                 continue
        #         resource_info = resources_dic.get(res.cmdb_p_code, {})
        #         result = {}
        #         result['create_date'] = datetime.datetime.strftime(res.created_date, '%Y-%m-%d %H:%M:%S')
        #         result['resource_name'] = res.resource_name
        #         result['item_name'] = res.project
        #         result['item_code'] = res.project_id
        #         result['id'] = res.res_id
        #         if not resource_type:
        #             result_list.extend(self.get_source_item(res.compute_list, result, resource_info, 'docker'))
        #             result_list.extend(self.get_source_item(res.resource_list, result, resource_info, 'db'))
        #         else :
        #             if resource_type == 'docker':
        #                 source_list = res.compute_list
        #             else:
        #                 source_list = res.resource_list
        #             result_list.extend(self.get_source_item(source_list, result, resource_info, resource_type))
        # total_count=len(result_list)
        # if page_num and page_count:
        #     page_num=int(page_num)
        #     page_count=int(page_count)
        #     if result_list:
        #         result_list=self._get_vm_status(page_num,page_count,result_list,resource_status)
        # code = 200
        # ret = {
        #     'code': code,
        #     'result': {
        #         "res": 'success',
        #         "msg": result_list,
        #         "total_count":total_count,
        #     }
        # }
        # return ret, code

    # def _deal_os_ip_item(self,os_ins_ip_list):
    #     res_list=[]
    #     res_dic={}
    #     for os_ip_dic in os_ins_ip_list:
    #         os_ins_id=os_ip_dic["os_ins_id"]
    #         os_type=os_ip_dic["os_type"]
    #         ip=os_ip_dic["ip"]
    #         res_dic[ip]=[os_ins_id,os_type]
    #         res_list.append(res_dic)
    #     return res_list
    #
    # def _get_vm_status(self,page_num,page_count,result_list,resource_status):
    #     try:
    #         results=[]
    #         ed_ins_ids=[]
    #         result_list=result_list[(page_num-1)*page_count:page_num*page_count]
    #         for result in result_list:
    #             res_id=result["id"]
    #             resource_ip=result["resource_ip"]
    #             resource=ResourceModel.objects.get(res_id=res_id)
    #             os_ins_ip_list=resource.os_ins_ip_list
    #             env=resource.env
    #             os_ins_ip_list=self._deal_os_ip_item(os_ins_ip_list)
    #             for os_ip_dic in os_ins_ip_list:
    #                 os_ip_list = os_ip_dic.get(resource_ip, [])
    #                 if os_ip_list:
    #                     os_ins_id=os_ip_list[0]
    #                     os_type=os_ip_list[1]
    #                     if os_type == "docker":
    #                         data={"os_inst_id":os_ins_id}
    #                         data_str=json.dumps(data)
    #                         headers = {'Content-Type': 'application/json'}
    #                         if os_ins_id not in ed_ins_ids:
    #                             res = requests.get(CRP_URL[env]+'api/openstack/nova/state', data=data_str, headers=headers)
    #                             ed_ins_ids.append(os_ins_id)
    #                             res=json.loads(res.content)
    #                             vm_state=res["result"]["vm_state"]
    #                             result['resource_status'] = vm_state
    #                     else:
    #                         result['resource_status'] = 'active'
    #                 else:
    #                     result['resource_status'] = 'active'
    #             results.append(result)
    #         if resource_status:
    #             status_results=[]
    #             for result in results:
    #                 res_status=result["resource_status"]
    #                 if resource_status == res_status:
    #                     status_results.append(result)
    #             results=status_results
    #         return results
    #     except Exception as e:
    #         logging.error('get vm status err: %s' % e.args)
    #
    # def __get_vm_status(self, page_num, page_count, result_list, resource_status):
    #     try:
    #         results = []
    #         ed_ins_ids = []
    #         res_list = []
    #         result_list = result_list[(page_num - 1) * page_count:page_num * page_count]
    #         for result in result_list:
    #             res_id = result["id"]
    #             resource_ip = result["resource_ip"]
    #             resource = ResourceModel.objects.get(res_id=res_id)
    #             os_ins_ip_list = resource.os_ins_ip_list
    #             env = resource.env
    #             os_ins_ip_list = self._deal_os_ip_item(os_ins_ip_list)
    #             for os_ip_dic in os_ins_ip_list:
    #                 os_ip_list = os_ip_dic.get(resource_ip, [])
    #                 if os_ip_list:
    #                     os_ins_id = os_ip_list[0]
    #                     os_type = os_ip_list[1]
    #                     if os_type == "docker":
    #                         if os_ins_id not in ed_ins_ids:
    #                             result["os_ins_id"] = os_ins_id
    #                             ed_ins_ids.append(os_ins_id)
    #                     else:
    #                         result["os_ins_id"] = os_ins_id
    #                 else:
    #                     result["os_ins_id"] = ''
    #             result["resource_status"] = "active"
    #             results.append(result)
    #         data = {"os_inst_ids": ed_ins_ids}
    #         data_str = json.dumps(data)
    #         headers = {'Content-Type': 'application/json'}
    #         res = requests.get(CRP_URL[env] + 'api/openstack/nova/state', data=data_str, headers=headers)
    #         res = json.loads(res.content)
    #         os_inst_status_dic = res["result"]["os_inst_status_dic"]
    #         for result in results:
    #             for os_id, os_status in os_inst_status_dic.items():
    #                 if result["os_ins_id"] == os_id:
    #                     result["resource_status"] = os_status
    #             res_list.append(result)
    #         if resource_status:
    #             status_results=[]
    #             for result in res_list:
    #                 res_status=result["resource_status"]
    #                 if resource_status == res_status:
    #                     status_results.append(result)
    #             res_list=status_results
    #         return res_list
    #     except Exception as e:
    #         logging.error('get vm status err: %s' % e.args)
    #         return []
    #
    # def get_source_item(self, source_list, result, resource_info, source_type):
    #     result_list = []
    #     # logging.info("&&&resource info:{}".format(resource_info))
    #     if source_type == 'docker':
    #         docker_counts_ip_list = resource_info.get(source_type, [])
    #     for source in source_list:
    #         if source.quantity == 0:
    #             continue
    #         result = copy.copy(result)
    #         if source_type == 'docker':
    #             logging.info("&&&resource info:{}".format(resource_info))
    #             type = source_type
    #             if not docker_counts_ip_list:
    #                 continue
    #             try:
    #                 for i in range(source.quantity):
    #                     tmp_result = copy.copy(result)
    #                     current_ip = docker_counts_ip_list.pop().get("ip_address")
    #                     if current_ip == '127.0.0.1':
    #                         continue
    #                     tmp_result['resource_ip'] = current_ip
    #                     tmp_result['resource_type'] = type
    #                     tmp_result['resource_config'] = [
    #                         {'name': 'CPU', 'value': str(source.cpu) + '核'},
    #                         {'name': '内存', 'value': str(source.mem) + 'GB'},
    #                     ]
    #                     tmp_result['resource_status'] = '运行中'
    #                     result_list.append(tmp_result)
    #             except Exception as exc:
    #                 logging.error("$$$get_source_item docker ip error:{}".format(exc))
    #         else:
    #             if source_type == 'db':
    #                 type = source.ins_type
    #             elif source_type == 'mysqlandmongo':
    #                 if source.ins_type == 'redis':
    #                     continue
    #                 else:
    #                     type = source.ins_type
    #             else:
    #                 if source.ins_type == source_type:
    #                     type = source.ins_type
    #                 else:
    #                     continue
    #             _ip = 'ip'
    #             _ip_ = 'vip'
    #             if type == 'redis':
    #                 _ip = 'vip'
    #             elif type == 'mysql':
    #                 _ip = 'wvip'
    #             elif type == 'mongodb':
    #                 _ip = 'vip1'
    #             ip = type + '_cluster'
    #             ins = type + '_instance'
    #             tempip = resource_info.get(ip, {}).get(_ip)
    #             tempip_ = resource_info.get(ins, {}).get(_ip_)
    #             relip = tempip_ if tempip == '127.0.0.1' else tempip
    #             if not relip:
    #                 continue
    #             result['resource_ip'] = relip
    #             result['resource_type'] = type
    #             result['resource_config'] = [
    #                 {'name': 'CPU', 'value': str(source.cpu) + '核'},
    #                 {'name': '内存', 'value': str(source.mem) + 'GB'},
    #             ]
    #             result['resource_status'] = '运行中'
    #             result_list.append(result)
    #     return result_list
            



resources_api.add_resource(ResourceApplication, '/')
resources_api.add_resource(ResourceDetail, '/<string:res_id>/')
resources_api.add_resource(ResourceRecord, '/fakerecords/<string:user_id>/')
resources_api.add_resource(GetDBInfo, '/get_dbinfo/<string:res_id>/')
resources_api.add_resource(GetMyResourcesInfo, '/get_myresources/')
