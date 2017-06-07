# -*- coding: utf-8 -*-
import json
import requests
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.workbench import bench_blueprint
from uop.models import User, ItemInformation
from uop.workbench.errors import user_errors

bench_api = Api(bench_blueprint, errors=user_errors)
url = 'http://cmdb-test.syswin.com/cmdb/api/repo_list/'


class SourceUnitList(Resource):
    def get(self):
        unit_data = requests.get(url+id+'/')
        if unit_data:
            # import ipdb;ipdb.set_trace()
            res = json.loads(unit_data.text)
            mysql_ip = res.get('msg').get('res_mysql').get(u'IP地址')
            redis_ip = res.get('msg').get('res_redis').get(u'IP地址')
            mongo_ip = res.get('msg').get('res_mongo').get(u'IP地址')
            data = {
                    'mysql_ip': mysql_ip,
                    'redis_ip': redis_ip,
                    'mongo_ip': mongo_ip,
                    }
        else:
            data = '查询结果不存在'
        return data


class SourceUnitDetail(Resource):
    def get(self, id):
        res = []
        unit_data = requests.get(url+id+'/')
        if unit_data:
            # import ipdb;ipdb.set_trace()
            res = json.loads(unit_data.text)
            unit_name = res.get('msg').get('unit').get(u'资源名称')
            unit_domain = res.get('msg').get('unit').get(u'域名')
            container_name = res.get('msg').get('virtual').get(u'名称')
            container_ip = res.get('msg').get('virtual').get(u'IP地址')
            # unit_domain = res.get('msg').get('unit').get(u'域名')
            mysql_ip = res.get('msg').get('res_mysql').get(u'IP地址')
            redis_ip = res.get('msg').get('res_redis').get(u'IP地址')
            mongo_ip = res.get('msg').get('res_mongo').get(u'IP地址')

            # 部署实例层
            deploy_data = {
                            'layerName': "deployInstance",
                            'children': [
                                {
                                    'name': unit_name,
                                    'imageUrl': 'deployInstance',
                                    #  提示信息
                                    'tooltip': unit_domain,
                                    #  关系
                                    'target': ['Mysql', 'Redis', 'Mongo']
                                }
                            ]
                        },
            # 集群层
            aggregation_data = {
                            'layerName': "clusterLayer",
                            'children': [
                                {
                                    'name': 'Mysql',
                                    'imageUrl': 'mysqlCluster',
                                    'tooltip': mysql_ip,
                                    'target': container_name
                                },
                                {
                                    'name': 'Redis',
                                    'imageUrl': 'redisCluster',
                                    'tooltip': redis_ip,
                                    'target': container_name
                                },
                                {
                                    'name': 'Mongo',
                                    'imageUrl': 'mongoCluster',
                                    'tooltip': mongo_ip,
                                    'target': container_name
                                },
                            ]
                        },
            # 虚机层
            virtual_data = {
                            'layerName': "virtualLayer",
                            'children': [
                                {
                                    'name': container_name,
                                    'imageUrl': 'virtual',
                                    'tooltip': container_ip,
                                    'target': []
                                },

                                # {
                                #     'name': '',
                                #     'imageUrl': '',
                                #     'tooltip': '',
                                #     'target': []
                                # },
                                # {
                                #     'name': '',
                                #     'imageUrl': '',
                                #     'tooltip': '',
                                #     'target': []
                                # }
                            ]
                        },
            # 物理机层
            physical_data = {
                            'layerName': "",
                            'children': [
                                {
                                    'name': '',
                                    'imageUrl': '',
                                    'tooltip': '',
                                    'target': []
                                },

                                {
                                    'name': '',
                                    'imageUrl': '',
                                    'tooltip': '',
                                    'target': []
                                }
                            ]
                        },
            # 机架层
            rack_data = {
                            'layerName': "",
                            'children': [
                                {
                                    'name': "",
                                    'imageUrl': '',
                                    'tooltip': '',
                                    'target': []
                                }
                            ]
                        },
            # 资源池层
            resource_pool = {
                            'layerName': "",
                            'children': [
                                {
                                    'name': "",
                                    'imageUrl': '',
                                    'tooltip': '',
                                    'target': []
                                }
                            ]
                        },
            # 数据中心层
            data_center = {
                            'layerName': "",
                            'children': [
                                {
                                    'name': "",
                                    'imageUrl': '',
                                    'tooltip': '',
                                    'target': []
                                }
                            ]
                        }
            data = [
                # 部署实例层
                deploy_data,
                #  集群层数据
                aggregation_data,
                #  虚拟机层数据
                virtual_data,
                # #   物理机层数据
                # physical_data,
                # #  机架层
                # rack_data,
                # #  资源池层
                # resource_pool,
                # #  数据中心层
                # data_center,
            ]
        else:
            data = '查询结果不存在'

        return data


bench_api.add_resource(SourceUnitList, '/source_unit/<id>')
bench_api.add_resource(SourceUnitDetail, '/source_unit_detail/<id>')
