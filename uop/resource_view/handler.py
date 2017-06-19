# -*- coding: utf-8 -*-
import json
import requests
from flask_restful import reqparse, Api, Resource
from uop.resource_view import resource_view_blueprint
from uop.resource_view.errors import resource_view_errors
from uop.log import Log
from config import APP_ENV, configs
from uop.models import ResourceModel


resource_view_api = Api(resource_view_blueprint, errors=resource_view_errors)
CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB_RELATION = CMDB_URL+'cmdb/api/repo_relation/'


class ResourceView(Resource):
    @classmethod
    def _response_data_not_fount(cls):
        res = {
                'code': 2015,
                'result': {
                    'res': None,
                    'msg': u'数据不存在'
                    }
                }
        return res

    @classmethod
    def get(cls, res_id):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('reference_type', type=str, action='append', location='args')
            parser.add_argument('item_filter', type=str, action='append', location='args')
            parser.add_argument('columns_filter', type=str, location='args')
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
            if args.item_filter:
                for item_filter in args.item_filter:
                    if param_str == "?":
                        param_str += "item_filter="+item_filter
                    else:
                        param_str += "&item_filter="+item_filter
            if args.columns_filter:
                if param_str == "?":
                    param_str += "columns_filter="+args.columns_filter
                else:
                    param_str += "&columns_filter="+args.columns_filter
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

            resource_instance = ResourceModel.objects.filter(res_id=res_id).first()
            cmdb_p_code = resource_instance.cmdb_p_code

            if param_str == "?":
                # req_str = CMDB_RELATION + cmdb_p_code + '/'
                layer_and_total_count = '?layer_count=10&total_count=50'
                reference_types = '&reference_type=dependent'
                reference_sequence = '&reference_sequence=[{\"child\": 3},{\"bond\": 2},{\"parent\": 5}]'
                item_filter = ''
                columns_filter = '&columns_filter={' +\
                                 '\"project_item\":[\"名称\"],' +\
                                 '\"deploy_instance\":[\"名称\"],' +\
                                 '\"app_cluster\":[\"名称\"],' +\
                                 '\"mysql_cluster\":[\"IP地址\",\"端口\"],' +\
                                 '\"mongo_cluster\":[\"IP地址\",\"端口\"],' +\
                                 '\"redis_cluster\":[\"IP地址\",\"端口\"],' +\
                                 '\"mysql_instance\":[\"IP地址\",\"端口\",\"角色\"],' +\
                                 '\"mongo_instance\":[\"IP地址\",\"端口\",\"角色\"],' +\
                                 '\"redis_instance\":[\"IP\"],' +\
                                 '\"virtual_server\":[\"IP地址\",\"主机名\"],' +\
                                 '\"docker\":[\"IP地址\",\"主机名\"],' +\
                                 '\"physical_server\":[\"IP地址\",\"设备型号\"],' +\
                                 '\"rack\":[\"机柜编号\"],' +\
                                 '\"idc_item\":[\"名称\",\"机房地址\"]' +\
                                 '}'
                req_str = CMDB_RELATION + cmdb_p_code + layer_and_total_count + reference_types + reference_sequence +\
                          item_filter + columns_filter
            else:
                req_str = CMDB_RELATION + cmdb_p_code + param_str

            Log.logger.debug("The Request Body is: " + req_str)

            ci_relation_query = requests.get(req_str)
            Log.logger.debug(ci_relation_query)
            Log.logger.debug(ci_relation_query.content)
            ci_relation_query_decode = ci_relation_query.content.decode('unicode_escape')
            result = json.loads(ci_relation_query_decode)
        except Exception as e:
            Log.logger.error(e.message)
            return cls._response_data_not_fount(), 500

        return result, 200


resource_view_api.add_resource(ResourceView, '/res_view/<res_id>')
