# -*- coding: utf-8 -*-
import json
import requests
import copy
import time
import random
from uop.log import Log
from flask import request, make_response, current_app
from flask import redirect
from flask import jsonify
import uuid
from urllib2 import unquote
import datetime
import hashlib
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.resources.handler import *
from uop.deployment.handler import get_resource_by_id, get_resource_by_id_mult
from uop.resources import resources_blueprint
from uop.models import ResourceModel, DBIns, ComputeIns, Deployment, NetWorkConfig,Approval
from uop.resources.errors import resources_errors
from uop.scheduler_util import flush_crp_to_cmdb, flush_crp_to_cmdb_by_osid
from uop.util import get_CRP_url
from config import APP_ENV, configs
from uop.log import Log

CMDB_URL = configs[APP_ENV].CMDB_URL
CRP_URL = configs[APP_ENV].CRP_URL
# TODO: move to global conf
dns_env = {'develop': '172.28.5.21', 'test': '172.28.18.212'}
resources_api = Api(resources_blueprint, errors=resources_errors)


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
        env = args.env
        created_date = datetime.datetime.now()
        application_status = args.formStatus
        approval_status = "unsubmit"
        resource_list = args.resource_list
        compute_list = args.compute_list
        resource_application = ResourceModel(resource_name=resource_name, project=project, department=department,
                                             department_id=department_id, res_id=res_id, project_id=project_id,
                                             user_name=user_name, user_id=user_id,env=env,
                                             application_status=application_status, approval_status=approval_status,
                                             reservation_status="unreserved", created_date=created_date)
        for resource in resource_list:
            ins_name = resource.get('res_name', '未知名称')
            ins_id = str(uuid.uuid1())
            ins_type = resource.get('res_type')
            cpu = resource.get('cpu')
            mem = resource.get('mem')
            disk = resource.get('disk')
            quantity = resource.get('quantity')
            version = resource.get('version')
            volume_size = resource.get('volume_size', 0)
            db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
                           quantity=quantity, version=version, volume_size=volume_size)
            resource_application.resource_list.append(db_ins)

        ins_name_list = []
        if compute_list:
            for compute in compute_list:
                ins_name = compute.get('ins_name')
                ins_name_list.append(ins_name)
                ins_id = str(uuid.uuid1())
                cpu = compute.get('cpu')
                mem = compute.get('mem')
                url = compute.get('url')
                domain = compute.get('domain')
                domain_ip = compute.get('domain_ip')
                quantity = compute.get('quantity')
                port = compute.get('port')
                meta_str = compute.get('meta')
                health_check=compute.get('health_check',0)
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
                compute_ins = ComputeIns(ins_name=ins_name, ins_id=ins_id, cpu=cpu, mem=mem, url=url, domain=domain,
                                         domain_ip=domain_ip, quantity=quantity, port=port, docker_meta=meta_str,health_check=health_check)
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
        parser.add_argument('page_num', type=int, location='args')
        parser.add_argument('page_size', type=int, location='args')
        parser.add_argument('instance_status', type=str, location='args')

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
        res={}
        try:
            total_count = 0
            if args.page_num and args.page_size:
                skip_count = (args.page_num - 1) * args.page_size
                if args.instance_status:
                    if args.user_id:
                        total_count=ResourceModel.objects.filter(user_id=args.user_id,approval_status__in=["success","failed","revoke"]).count()
                        resources = ResourceModel.objects.filter(user_id=args.user_id,approval_status__in=["success","failed","revoke"]).order_by('-created_date').skip(
                            skip_count).limit(args.page_size)
                    else:
                        total_count = ResourceModel.objects.filter(approval_status__in=["success", "failed","revoke"]).count()
                        resources = ResourceModel.objects.filter(approval_status__in=["success", "failed", "revoke"]).order_by('-created_date').skip(
                            skip_count).limit(args.page_size)
                else:
                    total_count=ResourceModel.objects.filter(**condition).count()
                    resources = ResourceModel.objects.filter(**condition).order_by('-created_date').skip(
                        skip_count).limit(
                        int(args.page_size))
            else:
                if args.instance_status:
                    resources = ResourceModel.objects.filter(user_id=args.user_id,approval_status__in=["success", "failed", "revoke"]).order_by(
                    '-created_date')
                else:
                    resources = ResourceModel.objects.filter(**condition).order_by('-created_date')
            res["total_count"]=total_count
        except Exception as e:
            err_msg=str(e.args)
            Log.logger.error(err_msg)
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'failed',
                    'msg': "Resource find error.%s" % err_msg
                }
            }
            return ret,500
        if len(resources):
            for resource in resources:
                result = dict()
                result['name'] = resource.user_name
                result['date'] = str(resource.created_date)
                result['resource'] = resource.resource_name
                result['formStatus'] = resource.application_status
                result['approval_status'] = resource.approval_status
                result['project'] = resource.project
                result['project_id'] = resource.project_id
                result['id'] = resource.res_id
                result['reservation_status'] = resource.reservation_status
                result['env'] = resource.env
                result['is_rollback'] = resource.is_rollback
                resource_id = resource.res_id
                deploys = Deployment.objects.filter(resource_id=resource_id).order_by("-created_time")
                if deploys:
                    dep = deploys[0]
                    if int(dep.is_rollback) == 0:
                        deploy_result = dep.deploy_result
                    elif int(dep.is_rollback) == 1:
                        deps = Deployment.objects.filter(resource_id=resource_id, is_rollback=0).order_by(
                            "-created_time")
                        if len(deploys) > 1 and len(deps) > 0:
                            deploy_result = deps[0].deploy_result
                        else:
                            deploy_result = 'set_success'
                    result['reservation_status'] = deploy_result
                result_list.append(result)
            res["result_list"]=result_list
        code = 200
        ret = {
            'code': code,
            'result': {
                'msg': 'success',
                'res': res
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
            os_inst_ip_list = []
            resources = ResourceModel.objects.get(res_id=res_id)
            if len(resources):
                deploys = Deployment.objects.filter(resource_id=res_id)
                for deploy in deploys:
                    env_ = get_CRP_url(deploy.environment)
                    crp_url = '%s%s' % (env_, 'api/deploy/deploys')
                    disconf_list = deploy.disconf_list
                    disconfs = []
                    for dis in disconf_list:
                        dis_ = dis.to_json()
                        disconfs.append(eval(dis_))
                    crp_data = {
                        "disconf_list": disconfs,
                        "resources_id": res_id,
                        "domain_list": [],
                        "set_flag": 'res'
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
                    # deploy.delete()
                # 调用CRP 删除资源
                os_ins_ip_list = resources.os_ins_ip_list
                for os_ip in os_ins_ip_list:
                    os_ip_dict = {}
                    os_ip_dict["os_ins_id"] = os_ip["os_ins_id"]
                    os_ip_dict["os_vol_id"] = os_ip["os_vol_id"]
                    os_inst_ip_list.append(os_ip_dict)
                crp_data = {
                    "resources_id": resources.res_id,
                    "os_ins_ip_list": os_inst_ip_list,
                    "vid_list": resources.vid_list,
                    "set_flag": 'res'
                }
                env_ = get_CRP_url(resources.env)
                crp_url = '%s%s' % (env_, 'api/resource/deletes')
                crp_data = json.dumps(crp_data)
                requests.delete(crp_url, data=crp_data)
                cmdb_p_code = resources.cmdb_p_code
                resources.delete()
                # 回写CMDB
                cmdb_url = '%s%s%s' % (CMDB_URL, 'cmdb/api/repores_delete/', cmdb_p_code)
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
            # print e
            Log.logger.error(str(e))
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
        """
        预留失败或者撤销时，重新申请时更新数据库
        :return:
        """
        parser = reqparse.RequestParser()
        parser.add_argument('res_id', type=str)
        parser.add_argument('resource_name', type=str)
        parser.add_argument('project', type=str)
        parser.add_argument('project_id', type=str)
        parser.add_argument('department', type=str)
        parser.add_argument('user_name', type=str)
        parser.add_argument('user_id', type=str)
        parser.add_argument('env', type=str)
        parser.add_argument('formStatus', type=str)
        parser.add_argument('approval_status', type=str)
        parser.add_argument('resource_list', type=list, location='json')
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()
        res_id = args.res_id
        resource_name = args.resource_name
        project = args.project
        project_id = args.project_id
        department = args.department
        user_name = args.user_name
        user_id = args.user_id
        env = args.env
        application_status = args.formStatus
        approval_status = "processing"
        compute_list = args.compute_list
        resource_list = args.resource_list
        try:
            resource = ResourceModel.objects.get(res_id=res_id)
            if resource:
                resource.resource_name=resource_name
                resource.project=project
                resource.project_id=project_id
                resource.department=department
                resource.user_name=user_name
                resource.user_id=user_id
                resource.env=env
                resource.application_status=application_status
                resource.approval_status = approval_status
                resource.compute_list=[]
                resource.resource_list=[]
                for compute in compute_list:
                    ins_name = compute.get('ins_name')
                    ins_id = str(uuid.uuid1())
                    cpu = compute.get('cpu')
                    mem = compute.get('mem')
                    url = compute.get('url')
                    domain = compute.get('domain')
                    domain_ip = compute.get('domain_ip')
                    quantity = compute.get('quantity')
                    port = compute.get('port')
                    meta_str = compute.get('meta')
                    health_check = compute.get('health_check', 0)
                    compute_ins = ComputeIns(ins_name=ins_name, ins_id=ins_id, cpu=cpu, mem=mem, url=url, domain=domain,
                                             domain_ip=domain_ip, quantity=quantity, port=port, docker_meta=meta_str,
                                             health_check=health_check)
                    resource.compute_list.append(compute_ins)
                for res in resource_list:
                    ins_name = res.get('res_name', '未知名称')
                    ins_id = str(uuid.uuid1())
                    ins_type = res.get('res_type')
                    cpu = res.get('cpu')
                    mem = res.get('mem')
                    disk = res.get('disk')
                    quantity = res.get('quantity')
                    version = res.get('version')
                    volume_size = res.get('volume_size', 0)
                    db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
                                   quantity=quantity, version=version, volume_size=volume_size)
                    resource.resource_list.append(db_ins)
                resource.save()
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
            err_msg=str(e)
            Log.logger.error(err_msg)
            ret = {
                'code': 500,
                'result': {
                    'res': 'fail',
                    'msg': 'Put resource application failed. %s' % err_msg
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
            resource = ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            Log.logger.error(str(e))
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }
            return ret
        deploies = Deployment.objects.filter(resource_id=res_id).order_by('+created_date')
        first_deploy = True
        if len(deploies):
            deploy = deploies.first()
            database_password = deploy.database_password
            first_deploy = False
        else:
            database_password = make_random_database_password()
        result['first_deploy'] = first_deploy
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
        result['docker_network_name'] = ""
        result['mysql_network_name'] = ""
        result['redis_network_name'] = ""
        result['mongodb_network_name'] = ""
        docker_network_id = resource.docker_network_id
        mysql_network_id = resource.mysql_network_id
        redis_network_id = resource.redis_network_id
        mongodb_network_id = resource.mongodb_network_id
        if docker_network_id:
            network = NetWorkConfig.objects.filter(vlan_id=docker_network_id).first()
            docker_network_name = network.name
            result['docker_network_name'] = docker_network_name
        if mysql_network_id:
            network = NetWorkConfig.objects.filter(vlan_id=mysql_network_id).first()
            mysql_network_name = network.name
            result['mysql_network_name'] = mysql_network_name
        if redis_network_id:
            network = NetWorkConfig.objects.filter(vlan_id=redis_network_id).first()
            redis_network_name = network.name
            result['redis_network_name'] = redis_network_name
        if mongodb_network_id:
            network = NetWorkConfig.objects.filter(vlan_id=mongodb_network_id).first()
            mongodb_network_name = network.name
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
                        "version": db_res.version,
                        "volume_size": db_res.volume_size
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
                        "health_check": db_com.health_check,
                    }
                )
        result['resource_list'] = res
        result['compute_list'] = com
        result['annotations'] = ""
        try:
            approvals=Approval.objects.filter(resource_id=res_id,approval_status__in=["success","failed"]).order_by('-created_date')
        except Exception as e:
            Log.logger.error(str(e))
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Approval find error."
                }
            }
            return ret
        if approvals:
            approval=approvals[0]
            annotations=approval.annotations
            result['annotations'] = annotations

        code = 200
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
            # print e
            Log.logger.error(str(e))
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
            volume_size = resource.get('volume_size', 0)
            db_ins = DBIns(ins_name=ins_name, ins_id=ins_id, ins_type=ins_type, cpu=cpu, mem=mem, disk=disk,
                           quantity=quantity, version=version, volume_size=volume_size)
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
            # print e
            Log.logger.error(str(e))
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
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str, location='args')
            parser.add_argument('options', type=str, location='args')
            args = parser.parse_args()
            # print args
            Log.logger.debug("delete args:{}".format(args))
            # parser.add_argument('resource_name', type=str, location='args')
            resources = ResourceModel.objects.get(res_id=res_id)
            if len(resources):
                cur_id = resources.user_id
                flag = resources.is_rollback
                if args.user_id == cur_id:  # 相同账户可以撤回或者删除自己的申请
                    if args.options == "rollback":
                        resources.is_rollback = 0 if flag == 1 else 1
                        resources.approval_status="revoke"
                        resources.save()
                        ret = {
                            'code': 200,
                            'result': {
                                'res': 'success',
                                'msg': 'Rollback success .'
                            }
                        }
                        return ret, 200
                        # elif options == "delete":
                        #     resources.delete()
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
            # print e
            Log.logger.error(str(e))
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
            # print e
            Log.logger.error(str(e))
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
        resource_type = request.args.get('resource_type', "")
        resource_database = request.args.get('mysqlandmongo', "")
        resource_cache = request.args.get('cache', "")
        resource_type = resource_database or resource_cache or resource_type
        resource_name = request.args.get('resource_name', "")
        item_name = request.args.get('item_name', "")
        # item_code = request.args.get('item_code',"")
        start_time = request.args.get('start_time', "")
        end_time = request.args.get('end_time', "")
        resource_status = request.args.get('resource_status', "")
        page_num = request.args.get('page_num', 1)
        env = request.args.get('env', "")
        page_count = request.args.get('page_count', 10)
        result_list = []
        url = CMDB_URL + "cmdb/api/vmdocker/status/?resource_type={}&resource_name={}&item_name={}&start_time={}&end_time={}&resource_status={}&page_num={}\
            &page_count={}&env={}&user_id={}".format(resource_type, resource_name, item_name, start_time, end_time,
                                                     resource_status, page_num, page_count, env, user_id)
        ret = requests.get(url)
        Log.logger.info("ret:{}".format(ret.json()))
        return ret.json()

    def put(self):
        code = 200
        ret = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': ""
            }
        }
        user_id = request.json.get('user_id')
        osid = request.json.get('osid', "")
        env = request.json.get('env', "")
        operation = request.json.get('operation', "")
        resource_id = request.json.get('resource_id', "")
        resource_ip = request.json.get('resource_ip', "")
        Log.logger.info(
            "get_myresource put parameters: user_id:{}, osid:{}, env:{}, operation:{}".format(user_id, osid, env,
                                                                                              operation))
        if operation not in ["start", "stop", "restart"]:
            ret["result"]["msg"] = "parameter error"
            ret["result"]["res"] = "operation must be one of start|stop|restart"
            return ret, 500
        if not osid or not osid or not user_id:
            ret["result"]["msg"] = "some parameters is null"
            ret["result"]["res"] = "osid:{}, user_id:{}, env:{}".format(osid, user_id, env)
            return ret, 500
        url = get_CRP_url(env)
        manager_url = url + "api/vm_operation/operations"

        data = {
            "vm_uuid": osid,
            "operation": operation,
        }
        headers = {'Content-Type': 'application/json'}
        data_str = json.dumps(data)
        ret = requests.post(manager_url, data=data_str, headers=headers)
        # 操作成功 调用查询docker状态的接口
        response = ret.json()
        if response.get('code') == 200:
            flush_crp_to_cmdb_by_osid(osid, env)
            cmdb_url = CMDB_URL + "cmdb/api/vmdocker/status/"
            if operation == 'start':
                status = 'startting'
            elif operation == 'stop':
                status = 'stopping'
            ret = requests.put(cmdb_url, data=json.dumps({"osid_status": [{osid: status}]})).json()

        return response


class Dockerlogs(Resource):
    def get(self):
        env = request.args.get('env')
        osid = request.args.get('osid')
        user_id = request.args.get('user_id')
        crp_url = get_CRP_url(env)
        url = crp_url + "api/openstack/docker/logs/"
        data = json.dumps({
            "osid": osid
        })
        try:
            Log.logger.info("osid:{}".format(data))
            ret = requests.post(url, data=data, headers={'Content-Type': 'application/json'}, timeout=60)
            Log.logger.info("ret:{}".format(ret.json()))
        except Exception as exc:
            Log.logger.error(str(exc))
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': str(exc)
                }
            }
            return ret, 200
        else:
            ret = ret.json()
            cmdb_url = CMDB_URL + "cmdb/api/vmdocker/status/"
            if ret["code"] == 400:
                try:
                    ack = requests.delete(cmdb_url, data=data)
                    if ack.json()["code"] == 2002:
                        ret["result"]["msg"] = "Instance could not be found, and will delete from cmdb"
                    else:
                        Log.logger.info("delete docker resource from cmdb error:{}".format(ack.json()))
                except Exception as exc:
                    Log.logger.error("delete docker resource from cmdb error:{}".format(str(exc)))
            return ret


resources_api.add_resource(ResourceApplication, '/')
resources_api.add_resource(ResourceDetail, '/<string:res_id>/')
resources_api.add_resource(ResourceRecord, '/fakerecords/<string:user_id>/')
resources_api.add_resource(GetDBInfo, '/get_dbinfo/<string:res_id>/')
resources_api.add_resource(GetMyResourcesInfo, '/get_myresources/')
resources_api.add_resource(Dockerlogs, '/get_myresources/docker/logs/')