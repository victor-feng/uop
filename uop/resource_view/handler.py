# -*- coding: utf-8 -*-
import json
import requests
from flask_restful import reqparse, Api, Resource
from uop.resource_view import resource_view_blueprint
from uop.resource_view.errors import resource_view_errors
from uop.log import Log
from config import APP_ENV, configs


resource_view_api = Api(resource_view_blueprint, errors=resource_view_errors)
CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB_RELATION = CMDB_URL+'cmdb/api/repo_relation/'


class ResourceView(Resource):
    @classmethod
    def get(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('reference_type', type=str, action='append', location='args')
        parser.add_argument('layer_count', type=str, location='args')
        parser.add_argument('total_count', type=str, location='args')

        args = parser.parse_args()
        param_str = "?"
        if args.reference_type:
            for reference_type in args.reference_type:
                if param_str == "?":
                    param_str += "reference_type="+reference_type
                else:
                    param_str += "&reference_type="+reference_type
        if args.layer_count:
            if param_str == "?":
                param_str += "layer_count="+args.layer_count
            else:
                param_str += "&layer_count="+args.layer_count
        if args.total_count:
            if param_str == "?":
                param_str += "total_count="+args.total_count
            else:
                param_str += "&total_count="+args.total_count

        if param_str == "?":
            req_str = CMDB_RELATION + id + '/'
        else:
            req_str = CMDB_RELATION + id + param_str

        ci_relation_query = requests.get(req_str)
        Log.logger.debug(ci_relation_query)
        Log.logger.debug(ci_relation_query.content)
        ci_relation_query_decode = ci_relation_query.content.decode('unicode_escape')
        result = json.loads(ci_relation_query_decode)

        return result, 200

        # res = []
        # data = []
        # if unit_data:
        #     # import ipdb;ipdb.set_trace()
        #     res = json.loads(unit_data.text)
        #     unit_name = res.get('msg').get('unit').get(u'资源名称')
        #     unit_domain = res.get('msg').get('unit').get(u'域名')
        #     container_name = res.get('msg').get('virtual').get(u'名称')
        #     container_ip = res.get('msg').get('virtual').get(u'IP地址')
        #     # unit_domain = res.get('msg').get('unit').get(u'域名')
        #     mysql_ip = res.get('msg').get('res_mysql').get(u'IP地址')
        #     redis_ip = res.get('msg').get('res_redis').get(u'IP地址')
        #     mongo_ip = res.get('msg').get('res_mongo').get(u'IP地址')
        #
        #     if not mysql_ip:
        #         mysql_ip = []
        #     if not redis_ip:
        #         redis_ip = []
        #     if not mongo_ip:
        #         mongo_ip = []
        #     if not unit_domain:
        #         unit_domain = []
        #     if unit_name:
        #         unit_name = unit_name[0]
        #     else:
        #         unit_name = ''
        #     # 部署实例层
        #     deploy_data = {
        #                     'layerName': "deployInstance",
        #                     'children': [
        #                         {
        #                             'name': unit_name,
        #                             'imageUrl': 'deployInstance',
        #                             #  提示信息
        #                             'tooltip': unit_domain,
        #                             #  关系
        #                             'target': ['Mysql', 'Redis', 'Mongo']
        #                         }
        #                     ]
        #                 }
        #     # 集群层
        #     aggregation_data = {
        #                     'layerName': "clusterLayer",
        #                     'children': [
        #                         {
        #                             'name': 'Mysql',
        #                             'imageUrl': 'mysqlCluster',
        #                             'tooltip': mysql_ip,
        #                             'target': container_name
        #                         },
        #                         {
        #                             'name': 'Redis',
        #                             'imageUrl': 'redisCluster',
        #                             'tooltip': redis_ip,
        #                             'target': container_name
        #                         },
        #                         {
        #                             'name': 'Mongo',
        #                             'imageUrl': 'mongoCluster',
        #                             'tooltip': mongo_ip,
        #                             'target': container_name
        #                         },
        #                     ]
        #                 }
        #     # 虚机层
        #     virtual_data = {
        #                     'layerName': "virtualLayer",
        #                     'children': [
        #                         {
        #                             'name': container_name[0],
        #                             'imageUrl': 'virtual',
        #                             'tooltip': container_ip,
        #                             'target': []
        #                         },
        #
        #                         # {
        #                         #     'name': '',
        #                         #     'imageUrl': '',
        #                         #     'tooltip': '',
        #                         #     'target': []
        #                         # },
        #                         # {
        #                         #     'name': '',
        #                         #     'imageUrl': '',
        #                         #     'tooltip': '',
        #                         #     'target': []
        #                         # }
        #                     ]
        #                 }
        #     # 物理机层
        #     physical_data = {
        #                     'layerName': "",
        #                     'children': [
        #                         {
        #                             'name': '',
        #                             'imageUrl': '',
        #                             'tooltip': [],
        #                             'target': []
        #                         },
        #
        #                         {
        #                             'name': '',
        #                             'imageUrl': '',
        #                             'tooltip': [],
        #                             'target': []
        #                         }
        #                     ]
        #                 }
        #     # 机架层
        #     rack_data = {
        #                     'layerName': "",
        #                     'children': [
        #                         {
        #                             'name': "",
        #                             'imageUrl': '',
        #                             'tooltip': [],
        #                             'target': []
        #                         }
        #                     ]
        #                 }
        #     # 资源池层
        #     resource_pool = {
        #                     'layerName': "",
        #                     'children': [
        #                         {
        #                             'name': "",
        #                             'imageUrl': '',
        #                             'tooltip': [],
        #                             'target': []
        #                         }
        #                     ]
        #                 }
        #     # 数据中心层
        #     data_center = {
        #                     'layerName': "",
        #                     'children': [
        #                         {
        #                             'name': "",
        #                             'imageUrl': '',
        #                             'tooltip': [],
        #                             'target': []
        #                         }
        #                     ]
        #                 }
        #     data.append(deploy_data)
        #     data.append(aggregation_data)
        #     data.append(virtual_data)
        # else:
        #     data = '查询结果不存在'
        # print deploy_data, type(deploy_data)
        # return data


resource_view_api.add_resource(ResourceView, '/res_view/<id>')
