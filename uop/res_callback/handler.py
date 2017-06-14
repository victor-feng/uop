# -*- coding: utf-8 -*-
import json
import random
import uuid
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
# res_callback_url = 'http://172.28.11.111:8002/cmdb/api/'


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
        cmdb_repo_id = res_data.get('cmdb_repo_id')

        # get the container and db
        container = res_data.get('container')
        db_info = res_data.get('db_info')

        # get the contaner field
        container_username = container.get('username')
        container_password = container.get('password')
        container_ip = container.get('ip')
        container_name = container.get('container_name')
        image_addr = container.get('image_addr')
        container_cpu = container.get('cpu')
        container_memory = container.get('memory')
        container_ins_id = container.get('ins_id')
        physical_server = container.get('physical_server')

        # get the db field
        mysql_info = db_info.get('mysql')
        redis_info = db_info.get('redis')
        mongo_info = db_info.get('mongodb')

        if not mysql_info:
            mysql_info = {}
        if not redis_info:
            redis_info = {}
        if not mongo_info:
            mongo_info = {}
        mysql_ins_id = mysql_info.get('ins_id', '')
        mysql_username = mysql_info.get('username', '')
        mysql_password = mysql_info.get('password', '')
        mysql_port = mysql_info.get('port', '')
        mysql_ip = mysql_info.get('ip', '')
        mysql_physical = mysql_info.get('physical_server')

        redis_ind_id = redis_info.get('ins_id', '')
        redis_username = redis_info.get('username', '')
        redis_password = redis_info.get('password', '')
        redis_port = redis_info.get('port', '')
        redis_ip = redis_info.get('ip', '')
        redis_physical = redis_info.get('physical_server')

        mongo_ind_id = mongo_info.get('ins_id', '')
        mongo_username = mongo_info.get('username', '')
        mongo_password = mongo_info.get('password', '')
        mongo_port = mongo_info.get('port', '')
        mongo_ip = mongo_info.get('ip', '')
        mongo_physical = mongo_info.get('physical_server')
        code = 2002
        res = 'successful'
        ret_id_13 = ''
        ret_id_14 = ''
        ret_id_15 = ''
        ret_id_4 = ''
        ret_id_5 = ''
        ret_id_3 = ''
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
            return ret
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
                        },
                    {
                        'type': 'reference',
                        'reference_ci': 'deploy_instance',
                        'reference_id': str(uuid.uuid4()),
                        'name': '包含部署实例',
                        }
                    ]
                } 

        deploy_instance = {
                'name': resource_name,
                'item_id': 'deploy_instance',
                'group_id': 'BusinessLine',
                'property_list': [
                    {
                        'type': 'string',
                        'name': '名称',
                        'value': resource_name,
                        },
                    {
                        'type': 'string',
                        'name': '部署实例ID',
                        'value': resource_id,
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
                        'name': '预留状态',
                        'value': status,
                        },
                    {
                        'type': 'string',
                        'name': '部署状态',
                        'value': '',
                        },
                    {
                        'type': 'reference',
                        'reference_ci': 'project_item',
                        'reference_id': cmdb_repo_id,
                        'name': '归属部署单元',
                        },
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

        if str(status) == 'ok':
          try:
            deploy_instance_res = requests.post(res_callback_url + 'repo/', data=json.dumps(deploy_instance))
            res_11 = json.loads(deploy_instance_res.text)
            ret_id = res_11.get('result').get('id')
            print '部署实例',ret_id

            app_cluster = {
                    'name': '应用集群',
                    'item_id': 'app_cluster',
                    'group_id': 'BusinessLine',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'app',
                            },
                        {
                            'type': 'string',
                            'name': '部署单元编号',
                            'value': '',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'deploy_instance',
                            'reference_id': ret_id,
                            'name': '归属部署实例',
                            }
                        ]
                    }
            app_cluster_res = requests.post(res_callback_url + 'repo/', data=json.dumps(app_cluster))
            res_7 = json.loads(app_cluster_res.text)
            ret_id_7 = res_7.get('result').get('id')
            print '应用集群',ret_id_7

            mysql_cluster = {
                    'name': 'mysql集群',
                    'item_id': 'mysql_cluster',
                    'group_id': 'database',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'mysql',
                            },
                        {
                            'type': 'string',
                            'name': '集群id',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '端口',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '版本',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '角色',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '最大连接数',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '最大错误连接数',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '超时等待时间',
                            'value': '',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'deploy_instance',
                            'reference_id': ret_id,
                            'name': '归属部署实例',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'app_cluster',
                            'reference_id': ret_id_7,
                            'name': '依赖应用集群',
                            },
                        ]
                    }
            mysql_cluster_res = requests.post(res_callback_url + 'repo/', data=json.dumps(mysql_cluster))
            res_8 = json.loads(mysql_cluster_res.text)
            ret_id_8 = res_8.get('result').get('id')
            print 'mysql集群',ret_id_8

            redis_cluster = {
                    'name': 'redis集群',
                    'item_id': 'redis_cluster',
                    'group_id': 'BusinessLine',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'redis',
                            },
                        {
                            'type': 'string',
                            'name': '集群id',
                            'value': '',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'deploy_instance',
                            'reference_id': ret_id,
                            'name': '归属部署实例',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'app_cluster',
                            'reference_id': ret_id_7,
                            'name': '依赖应用集群',
                            }
                        ]
                    }

            redis_cluster_res = requests.post(res_callback_url + 'repo/', data=json.dumps(redis_cluster))
            res_9 = json.loads(redis_cluster_res.text)
            ret_id_9 = res_9.get('result').get('id')
            print 'redis集群',ret_id_9
            mongo_cluster = {
                    'name': 'mongo集群',
                    'item_id': 'mongo_cluster',
                    'group_id': 'BusinessLine',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'mongo',
                            },
                        {
                            'type': 'string',
                            'name': '部署单元编号',
                            'value': '',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'deploy_instance',
                            'reference_id': ret_id,
                            'name': '归属部署实例',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'app_cluster',
                            'reference_id': ret_id_7,
                            'name': '依赖应用集群',
                            }
                        ]
                    }


            mongo_cluster_res = requests.post(res_callback_url + 'repo/', data=json.dumps(mongo_cluster))
            res_10 = json.loads(mongo_cluster_res.text)
            ret_id_10 = res_10.get('result').get('id')
            print 'mongo集群',ret_id_10

            # 实例
            data_app = {
                    'name': '应用实例',
                    'p_code': 'app_instance',
                    'group': 'database',
                    'item_id': 'app_instance',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': '',
                            },
                        {
                            'type': 'string',
                            'name': '端口',
                            'value': '',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'app_cluster',
                            'reference_id': ret_id_7,
                            'name': '所在应用集群',
                            }
                        ]
                    }

            data_app_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_app))
            res_6 = json.loads(data_app_res.text)
            ret_id_6 = res_6.get('result').get('id')
            print '应用实例',ret_id_6


            data_mysql = {
                    'name': 'mysql',
                    'layer_id': 'paas',
                    'group_id': 'database',
                    'item_id': 'mysql_instance',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '实例ID',
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
                        {
                            'type': 'string',
                            'name': '资源ID',
                            'value': resource_id,
                            },
                        {
                            'type': 'string',
                            'name': '所属服务器',
                            'value': mysql_physical,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mysql_cluster',
                            'reference_id': ret_id_8,
                            'name': '所在MySQL集群',
                            },
                        ]
                    }
            if mysql_info:
                mysql_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_mysql))
                res_3 = json.loads(mysql_res.text)
                ret_id_3 = res_3.get('result').get('id')
                print 'mysql', ret_id_3

            data_redis = {
                    'name': 'redis',
                    'layer_id': 'paas',
                    'group_id': 'database',
                    'item_id': 'redis_instance',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '实例ID',
                            'value': redis_ind_id,
                            },
                        {
                            'type': 'string',
                            'name': '用户名',
                            'value': redis_username,
                            },
                        {
                            'type': 'string',
                            'name': '密码',
                            'value': redis_password,
                            },
                        {
                            'type': 'int',
                            'name': '端口',
                            'value': redis_port,
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': redis_ip,
                            },
                        {
                            'type': 'string',
                            'name': '所属部署单元ID',
                            'value': unit_id,
                            },
                        {
                            'type': 'string',
                            'name': '资源ID',
                            'value': resource_id,
                            },
                        {
                            'type': 'string',
                            'name': '所属服务器',
                            'value': redis_physical,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'redis_cluster',
                            'reference_id': ret_id_9,
                            'name': '所在Redis集群',
                            },
                        ],
                    }
            if redis_info:
                redis_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_redis))
                res_4 = json.loads(redis_res.text)
                ret_id_4 = res_4.get('result').get('id')
                print 'redis', ret_id_4
            data_mongo = {
                    'name': 'mongo',
                    'layer_id': 'paas',
                    'group_id': 'database',
                    'item_id': 'mongo_instance',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '实例id',
                            'value': mongo_ind_id,
                            },
                        {
                            'type': 'string',
                            'name': '用户名',
                            'value': mongo_username,
                            },
                        {
                            'type': 'string',
                            'name': '密码',
                            'value': mongo_password,
                            },
                        {
                            'type': 'string',
                            'name': '端口',
                            'value': mongo_port,
                            },
                        {
                            'type': 'int',
                            'name': 'IP地址',
                            'value': mongo_ip,
                            },
                        {
                            'type': 'string',
                            'name': '所属部署单元ID',
                            'value': unit_id,
                            },
                        {
                            'type': 'string',
                            'name': '资源ID',
                            'value': resource_id,
                            },
                        {
                            'type': 'string',
                            'name': '所属服务器',
                            'value': mongo_physical,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mongo_cluster',
                            'reference_id': ret_id_10,
                            'name': '所在Mongo集群',
                            }
                        ],
                    }
            if mongo_info:
                mongo_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_mongo))
                res_5 = json.loads(mongo_res.text)
                ret_id_5 = res_5.get('result').get('id')
                print 'mongo',ret_id_5

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
                            'type': 'string',
                            'name': 'CPU数量',
                            'value': str(container_cpu),
                            },
                        {
                            'type': 'string',
                            'name': '内存容量',
                            'value': str(container_memory),
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
                            },
                        {
                            'type': 'string',
                            'name': '所属服务器',
                            'value': physical_server,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'app_instance',
                            'reference_id': ret_id_6,
                            'name': '关联应用实例',
                            },
                        ]
                    }
            if container:
                container_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_container))
                res_2 = json.loads(container_res.text)
                ret_id_2 = res_2.get('result').get('id')
                print 'container',ret_id_2

            vm_mysql = {
                    'name': 'mysql虚拟机',
                    'item_id': 'virtual_server',
                    'group_id': 'server',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'mysql虚拟机',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': mysql_ip,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mysql_instance',
                            'reference_id': ret_id_3,
                            'name': '关联mysql实例',
                            }
                        ]
                    }
            if mysql_ip:
                vm_mysql_res = requests.post(res_callback_url + 'repo/', data=json.dumps(vm_mysql))
                res_13 = json.loads(vm_mysql_res.text)
                ret_id_13 = res_13.get('result').get('id')
                print 'mysql虚拟机', ret_id_13
            vm_redis = {
                    'name': 'redis虚拟机',
                    'item_id': 'virtual_server',
                    'group_id': 'server',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'redis虚机',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': redis_ip,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'redis_instance',
                            'reference_id': ret_id_4,
                            'name': '关联redis实例',
                            }
                        ]
                    }
            if redis_ip:
                vm_redis_res = requests.post(res_callback_url + 'repo/', data=json.dumps(vm_redis))
                res_14 = json.loads(vm_redis_res.text)
                ret_id_14 = res_14.get('result').get('id')
                print 'redis虚拟机',ret_id_14
            vm_mongo = {
                    'name': 'mongo虚拟机',
                    'item_id': 'virtual_server',
                    'group_id': 'server',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': 'mongo虚机',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': mongo_ip,
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mongo_instance',
                            'reference_id': ret_id_5,
                            'name': '关联mongo实例',
                            },
                        ]
                    }
            if mongo_ip:
                vm_mongo_res = requests.post(res_callback_url + 'repo/', data=json.dumps(vm_mongo))
                res_15 = json.loads(vm_mongo_res.text)
                ret_id_15 = res_15.get('result').get('id')
                print 'mongo虚拟机',ret_id_15

            data_physical_server = {
                    'name': '物理机',
                    'item_id': 'physical_server',
                    'group_id': 'server',
                    'property_list': [
                        {
                            'type': 'string',
                            'name': '名称',
                            'value': '物理机',
                            },
                        {
                            'type': 'string',
                            'name': 'IP地址',
                            'value': physical_server
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'docker',
                            'reference_id': ret_id_2,
                            'name': '包含Docker',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mysql_virtual_server',
                            'reference_id': ret_id_13,
                            'name': '包含mysql虚拟机',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'redis_virtual_server',
                            'reference_id': ret_id_14,
                            'name': '包含redis虚拟机',
                            },
                        {
                            'type': 'reference',
                            'reference_ci': 'mongo_virtual_server',
                            'reference_id': ret_id_15,
                            'name': '包含mongo虚拟机',
                            },
                        ]
                    }
            physical_server_res = requests.post(res_callback_url + 'repo/', data=json.dumps(data_physical_server))
            res_12 = json.loads(physical_server_res.text)
            ret_id_12 = res_12.get('result').get('id')
            print '物理机',ret_id_12
            res = 'successful'
          except Exception, e:
            code = 2003
            res = '存储错误'
        try:
            resource = ResourceModel.objects.get(res_id=resource_id)
            resource.reservation_status = status
            resource.cmdb_p_code = ret_id
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
            return ret
        data_response = {
                'code': code,
                'res': res,
                }
        return data_response

    def get(self):
        data = requests.get(res_callback_url + 'repo_list/')
        res = json.loads(data.text)
        return res


res_callback_api.add_resource(UserRegister, '/users')
res_callback_api.add_resource(ResCallback, '/res')
