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
import datetime
import hashlib
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with

from uop.deployment.handler import get_resource_by_id, get_resource_by_id_mult
from uop.resources import resources_blueprint
from uop.models import ResourceModel, DBIns, ComputeIns, Deployment
from uop.resources.errors import resources_errors
from uop.util import get_CRP_url
from config import APP_ENV, configs

CMDB_URL = configs[APP_ENV].CMDB_URL
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
        match_cond['deleted'] = 0
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
            if ResourceModel.objects.filter(resource_name=resource_name, env=env).filter(deleted=0).count():
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
                if ResourceModel.objects(compute_list__match={'ins_name': insname}).filter(deleted=0).count() > 0:
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
            resources = ResourceModel.objects.filter(**condition).filter(deleted=0).order_by('-created_date')
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
            resources = ResourceModel.objects.filter(deleted=0).get(res_id=res_id)
            if len(resources):
                env_ = get_CRP_url(resources.env)
                os_ins_list = resources.os_ins_list
                crp_url = '%s%s'%(env_, 'api/resource/deletes')
                crp_data = {
                        "resources_id": resources.res_id,
                        "os_inst_id_list": resources.os_ins_list,
                        "vid_list": resources.vid_list,
                }
                try:
                    deploy = Deployment.objects.filter(deleted=0).get(resource_id=res_id)
                except Exception as e:
                    deploy = None

                if deploy:
                    deploy.deleted = 1
                    deploy.save()
                # 调用CRP 删除资源
                crp_data = json.dumps(crp_data)
                requests.delete(crp_url, data=crp_data)
                resources.deleted = 1
                # 修改ins_name 唯一键
                compute_list = resources.compute_list
                for compute_ in compute_list:
                     ins_name = 'delete_%s_%s'%(compute_.ins_name, time.time())
                     compute_.ins_name = ins_name
                resources.compute_list = compute_list
                resources.save()
                # 回写CMDB
                cmdb_url = '%s%s%s'%(CMDB_URL, 'cmdb/api/repores_delete/', resources.cmdb_p_code)
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


class ResourceDetail(Resource):
    @classmethod
    def get(cls, res_id):
        result = {}
        try:
            resources = ResourceModel.objects.filter(res_id=res_id, deleted=0)
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
                result['database_password'] = make_random_database_password()

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
            resource_application = ResourceModel.objects.get(res_id=res_id, deleted=0)
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
            resources = ResourceModel.objects.get(res_id=res_id, deleted=0)
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
            resources = ResourceModel.objects.filter(user_id=user_id, deleted=0)
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
        logging.info("####resource_info:{}".format(resource_info))
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
        resource_type = request.args.get('resource_type')
        resource_name = request.args.get('resource_name')
        item_name = request.args.get('item_name')
        item_code = request.args.get('item_code')
        #  create_date = request.args.get('create_date')
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        resource_status = request.args.get('resource_status')
        result_list = []
        query = {
            'approval_status': 'success',
        }

        def comparable_time(s):
                return datetime.datetime.strptime(s, "%Y-%m-%dT%H:%M:%S.000Z")

        try:
            if user_id:
                query['user_id'] = user_id
            if resource_name:
                query['resource_name'] = resource_name
            if item_name:
                query['project'] = item_name
            if item_code:
                query['project_id'] = item_code
            resources = ResourceModel.objects.filter(**query).order_by('-create_date')

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
            flag, resources_dic= get_resource_by_id_mult([res.cmdb_p_code for res in resources])
            if not flag:
                code = 500
                ret = {
                    'code': code,
                    'result': {
                        'res': 'fail',
                        'msg': '批量查询CMDB接口失败！'
                    }
                }
                return ret, code
            for res in resources:
                rcd = res.created_date
                if start_time:
                    if res.created_date < comparable_time(start_time):
                        continue
                if end_time:
                    if res.created_date > comparable_time(end_time):
                        continue
                resource_info = resources_dic.get(res.cmdb_p_code, {})
                result = {}
                result['create_date'] = datetime.datetime.strftime(res.created_date, '%Y-%m-%d %H:%M:%S')
                result['resource_name'] = res.resource_name
                result['item_name'] = res.project
                result['item_code'] = res.project_id
                result['id'] = res.res_id
                if not resource_type:
                    result_list.extend(self.get_source_item(res.compute_list, result, resource_info, 'docker'))
                    result_list.extend(self.get_source_item(res.resource_list, result, resource_info, 'db'))
                else :
                    if resource_type == 'docker':
                        source_list = res.compute_list
                    else:
                        source_list = res.resource_list
                    result_list.extend(self.get_source_item(source_list, result, resource_info, resource_type))


        code = 200
        ret = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': result_list
            }
        }
        return ret, code


    def get_source_item(self, source_list, result, resource_info, source_type):
        result_list = []
        for source in source_list:
            if source.quantity == 0:
                continue
            result = copy.copy(result)
            if source_type == 'docker':
                type = source_type
                result['resource_ip'] = resource_info.get(source_type, {'ip_address': '127.0.0.1'}).get('ip_address')
            else:
                if source_type == 'db':
                    type = source.ins_type
                elif source_type == 'mysqlandmongo':
                    if source.ins_type == 'redis':
                        continue
                    else:
                        type = source.ins_type
                else:
                    if source.ins_type == source_type:
                        type = source.ins_type
                    else:
                        continue
                _ip = 'ip'
                if type == 'redis':
                    _ip = 'vip'
                elif type == 'mysql':
                    _ip = 'wvip'
                elif type == 'mongodb':
                    _ip = 'vip1'
                ip = type + '_cluster'
                result['resource_ip'] = resource_info.get(ip, {}).get(_ip, '127.0.0.1')
            result['resource_type'] = type
            result['resource_config'] = [
                {'name': 'CPU', 'value': str(source.cpu) + '核'},
                {'name': '内存', 'value': str(source.mem) + 'GB'},
            ]
            result['resource_status'] = '运行中'
            result_list.append(result)
        return result_list



resources_api.add_resource(ResourceApplication, '/')
resources_api.add_resource(ResourceDetail, '/<string:res_id>/')
resources_api.add_resource(ResourceRecord, '/fakerecords/<string:user_id>/')
resources_api.add_resource(GetDBInfo, '/get_dbinfo/<string:res_id>/')
resources_api.add_resource(GetMyResourcesInfo, '/get_myresources/')
