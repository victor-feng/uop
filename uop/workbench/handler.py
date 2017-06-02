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
            unit_name = res.get('msg').get('unit').get(u'名称')
            container_name = res.get('msg').get('virtual').get(u'名称')
            unit_domain = res.get('msg').get('unit').get(u'域名')
            # unit_domain = res.get('msg').get('unit').get(u'域名')
            mysql_ip = res.get('msg').get('res_mysql').get(u'IP地址')
            redis_ip = res.get('msg').get('res_redis').get(u'IP地址')
            mongo_ip = res.get('msg').get('res_mongo').get(u'IP地址')
            data = [
                # 部署实例层
                        {
                            'layerName': "deployInstance",
                            'children': [
                                {
                                    'name': unit_name,
                                    'imageUrl': 'deployInstance',
                                    #  提示信息
                                    'tooltip': unit_domain,
                                    #  关系
                                    'target': ['应用']
                                }
                            ]
                        },
                        #  集群层数据
                        {
                            'layerName': "clusterLayer",
                            'children': [
                                {
                                    'name': 'Mysql',
                                    'imageUrl': 'mysqlCluster',
                                    'tooltip': mysql_ip,
                                    'target': ['VM1', '应用']
                                },
                                {
                                    'name': '应用',
                                    'imageUrl': 'applicationCluster',
                                    'tooltip': '应用集群',
                                    'target': ['VM2']
                                },
                                {
                                    'name': 'Redis',
                                    'imageUrl': 'redisCluster',
                                    'tooltip': redis_ip,
                                    'target': ['VM3', '应用']
                                },
                                {
                                    'name': 'Mongo',
                                    'imageUrl': 'redisCluster',
                                    'tooltip': mongo_ip,
                                    'target': ['VM3', '应用']
                                },
                            ]
                        },
                        #  虚拟机层数据
                        {
                            'layerName': "virtualLayer",
                            'children': [
                                {
                                    'name': container_name,
                                    'imageUrl': 'virtual',
                                    'tooltip': 'VM1 192.168.33.77',
                                    'target': ['物理机1']
                                },

                                {
                                    'name': 'VM2',
                                    'imageUrl': 'virtual',
                                    'tooltip': 'VM2 192.168.33.78',
                                    'target': ['物理机1']
                                },
                                {
                                    'name': 'VM3',
                                    'imageUrl': 'virtual',
                                    'tooltip': 'VM3 192.168.33.38',
                                    'target': ['物理机2']
                                }
                            ]
                        },

                        #   物理机层数据
                        {
                            'layerName': "physicalLayer",
                            'children': [
                                {
                                    'name': '物理机1',
                                    'imageUrl': 'physical',
                                    'tooltip': '物理机1',
                                    'target': ['机架']
                                },

                                {
                                    'name': '物理机2',
                                    'imageUrl': 'physical',
                                    'tooltip': '物理机2',
                                    'target': ['机架']
                                }
                            ]
                        },
                        #  机架层
                        {
                            'layerName': "frameLayer",
                            'children': [
                                {
                                    'name': "机架",
                                    'imageUrl': '',
                                    'tooltip': '机架',
                                    'target': ['资源池']
                                }
                            ]
                        },
                        #  资源池层
                        {
                            'layerName': "resDomainLayer",
                            'children': [
                                {
                                    'name': "资源池",
                                    'imageUrl': 'resDomain',
                                    'tooltip': '资源池',
                                    'target': ['DC']
                                }
                            ]
                        },
                        #  数据中心层
                        {
                            'layerName': "dcLayer",
                            'children': [
                                {
                                    'name': "DC",
                                    'imageUrl': 'DC',
                                    'tooltip': '数据中心',
                                    'target': []
                                }
                            ]
                        }
                ]
        else:
            data = '查询结果不存在'

        return data


bench_api.add_resource(SourceUnitList, '/source_unit/<id>')
bench_api.add_resource(SourceUnitDetail, '/source_unit_detail/<id>')
