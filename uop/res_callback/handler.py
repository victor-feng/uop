# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.res_callback import res_callback_blueprint
from uop.models import User, ResourceModel
from uop.res_callback.errors import res_callback_errors
import requests
# from uop_backend.config import res_callback_url
res_callback_api = Api(res_callback_blueprint, errors=res_callback_errors)
res_callback_url = 'http://cmdb-test.syswin.com/cmdb/api/'


class UserRegister(Resource):
    """
    this is a test code
    """
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        parser.add_argument('first_name', type=str)
        parser.add_argument('last_name', type=str)
        args = parser.parse_args()

        email = args.email
        first_name = args.first_name
        last_name = args.first_name

        User(email=email, first_name=first_name, last_name=last_name).save()

        res = {
            "code": 200,
            "result": {
                "res": "success",
                "msg": "test info"
            }
        }
        return res, 200

    @classmethod
    def get(cls):
        return "test info", 409


class ResCallback(Resource):
    def post(self):
        data = {}
        res_data = json.loads(request.data)

        unit_name = res_data.get('unit_name')
        unit_id = res_data.get('unit_id')
        unit_des = res_data.get('unit_des')
        user_id = res_data.get('user_id')
        username = res_data.get('username')
        department = res_data.get('department')
        created_time = res_data.get('created_time')

        resource_id = res_data.get('resource_id')
        resource_name = res_data.get('resource_name')
        env = res_data.get('env')
        domain = res_data.get('domain')
        status = res_data.get('status')
        container = res_data.get('container')
        db_info = res_data.get('db_info')

        # get the contaner field
        container_username = container.get('username')
        container_password = container.get('password')
        container_ip = container.get('ip')
        container_name = container.get('container_name')
        image_addr = container.get('image_addr')
        # standard_ins = container.get('standard_ins')
        container_cpu = container.get('cpu')
        container_memory = container.get('memory')
        container_ins_id = container.get('ins_id')

        # get the db field
        mysql_info = db_info.get('mysql')
        redis_info = db_info.get('redis')
        mongo_info = db_info.get('mongodb')

        if not mysql_info:
            mysql_info = {}
        mysql_ins_id = mysql_info.get('ins_id', '')
        mysql_username = mysql_info.get('username', '')
        mysql_password = mysql_info.get('password', '')
        mysql_port = mysql_info.get('port', '')
        mysql_ip = mysql_info.get('ip', '')

        redis_ind_id = redis_info.get('ind_id', '')
        redis_username = redis_info.get('username', '')
        redis_password = redis_info.get('password', '')
        redis_port = redis_info.get('port', '')
        redis_ip = redis_info.get('ip', '')

        mongo_ind_id = mongo_info.get('ind_id', '')
        mongo_username = mongo_info.get('username', '')
        mongo_password = mongo_info.get('password', '')
        mongo_port = mongo_info.get('port', '')
        mongo_ip = mongo_info.get('ip', '')
        mongo_ref = unit_id  # 所属部署单元

        try:
            resource = ResourceModel.objects.get(res_id=resource_id)
            resource.reservation_status = status
            resource.save()
        except Exception as e:
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Resource find error."
                }
            }

        # item_id: project_item,layer:business,group:BusinessLine 部署单元
        """
        data_unit = {  # for unit
                '名称': unit_name,
                '部署单元编号': unit_id,
                '部署单元描述': unit_des,
                '创建人': username,
                '归属部门': department,
                '创建时间': created_time,
                }
        data_resource = {
                '资源名称': resource_name,
                '资源ID': resource_id,
                '部署环境': env,
                '域名': domain,
                '状态': status,
                }
        """
        data_unit = {
                'name': unit_name,
                'layer_id': 'business',
                'group_id': 'BusinessLine',
                'item_id': 'project_item',
                'property_list': [
                    {
                        'type': 'string',
                        'name': '名称',
                        'value': unit_name,
                        },
                    {
                        'type': 'string',
                        'name': '部署单元编号',
                        'value': unit_id,
                        },
                    {
                        'type': 'string',
                        'name': '部署单元描述',
                        'value': unit_des,
                        },
                    {
                        'type': 'string',
                        'name': '创建人',
                        'value': username,
                        },
                    {
                        'type': 'string',
                        'name': '归属部门',
                        'value': department,
                        },
                    {
                        'type': 'string',
                        'name': '创建时间',
                        'value': created_time,
                        },
                    {
                        'type': 'string',
                        'name': '资源名称',
                        'value': resource_name,
                        },
                    {
                        'type': 'string',
                        'name': '资源ID',
                        'value': resource_id,
                        },
                    {
                        'type': 'string',
                        'name': '部署环境',
                        'value': env,
                        },
                    {
                        'type': 'string',
                        'name': '域名',
                        'value': domain,
                        },
                    {
                        'type': 'string',
                        'name': '状态',
                        'value': status,
                        }
                    ]
                }

        """
        data_container = {
                '名称': container_name,
                '镜像地址': image_addr,
                # '实例规格': standard_ins,
                '用户名': username,
                '密码': password,
                'IP地址': ip,
                'CPU数量': cpu,
                '内存容量': memory,
                '实例id': ins_id,
                '所属部署单元': unit_id,
                }
        """
        data_container = {
                'name': container_name,
                'layer_id': 'iaas',
                'group_id': 'server',
                'item_id': 'docker',
                'property_list': [
                    {
                        'type': 'string',
                        'name': '名称',
                        'value': container_name,
                        },
                    {
                        'type': 'string',
                        'name': '镜像地址',
                        'value': image_addr,
                        },
                    {
                        'type': 'string',
                        'name': '用户名',
                        'value': container_username,
                        },
                    {
                        'type': 'string',
                        'name': '密码',
                        'value': container_password,
                        },
                    {
                        'type': 'string',
                        'name': 'IP地址',
                        'value': container_ip,
                        },
                    {
                        'type': 'int',
                        'name': 'CPU数量',
                        'value': container_cpu,
                        },
                    {
                        'type': 'int',
                        'name': '内存容量',
                        'value': container_memory,
                        },
                    {
                        'type': 'string',
                        'name': '实例ID',
                        'value': container_ins_id,
                        },
                    {
                        'type': 'string',
                        'name': '所属部署单元',
                        'value': unit_id,
                        }
                    ]
                }

        """
        data_mysql = {
                '实例id': ins_id,
                '用户名': username,
                '密码': password,
                '端口': port,
                'IP地址': ip,
                '所属部署单元': unit_id
                }
        """
        data_mysql = {
                'name': mysql_username,
                'layer_id': 'paas',
                'group_id': 'database',
                'item_id': 'mysql_item',
                'property_list': [
                    {
                        'type': 'string',
                        'name': '实例id',
                        'value': mysql_ins_id,
                        },
                    {
                        'type': 'string',
                        'name': '用户名',
                        'value': mysql_username,
                        },
                    {
                        'type': 'string',
                        'name': '密码',
                        'value': mysql_password,
                        },
                    {
                        'type': 'int',
                        'name': '端口',
                        'value': mysql_port,
                        },
                    {
                        'type': 'string',
                        'name': 'IP地址',
                        'value': mysql_ip,
                        },
                    {
                        'type': 'string',
                        'name': '所属部署单元ID',
                        'value': unit_id,
                        },
                    ]
                }
        unit_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_unit))
        res = json.loads(unit_res.text)
        print res
        container_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_container))
        res = json.loads(container_res.text)
        print res
        mysql_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_mysql))
        res = json.loads(mysql_res.text)

        return res

    def get(self):
        data = requests.get(res_callback_url + 'repo_list/')
        res = json.loads(data.text)
        return res


res_callback_api.add_resource(UserRegister, '/users')
res_callback_api.add_resource(ResCallback, '/res')
