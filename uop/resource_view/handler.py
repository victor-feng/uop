# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
from flask import current_app
from uop.log import Log
from uop.models import ResourceModel
from uop.util import response_data
from config import configs, APP_ENV
from uop.item_info.handler import get_uid_token


CMDB2_URL = configs[APP_ENV]

__all__ = [
    "response_data_not_found", "cmdb_graph_search", "cmdb2_graph_search"
]

def response_data_not_found():

    res = {
        'code': 2015,
        'result': {
            'res': None,
            'msg': u'数据不存在'
        }
    }
    return res


# cmdb1.0 图搜素
def cmdb_graph_search(args, res_id):
    try:
        param_str = "?"
        if args.reference_sequence:
            if param_str == "?":
                param_str += "reference_sequence=" + args.reference_sequence
            else:
                param_str += "&reference_sequence=" + args.reference_sequence
        if args.reference_type:
            for reference_type in args.reference_type:
                if param_str == "?":
                    param_str += "reference_type=" + reference_type
                else:
                    param_str += "&reference_type=" + reference_type
        if args.item_filter:
            for item_filter in args.item_filter:
                if param_str == "?":
                    param_str += "item_filter=" + item_filter
                else:
                    param_str += "&item_filter=" + item_filter
        if args.columns_filter:
            if param_str == "?":
                param_str += "columns_filter=" + args.columns_filter
            else:
                param_str += "&columns_filter=" + args.columns_filter
        if args.layer_count:
            if param_str == "?":
                param_str += "layer_count=" + args.layer_count
            else:
                param_str += "&layer_count=" + args.layer_count
        if args.total_count:
            if param_str == "?":
                param_str += "total_count=" + args.total_count
            else:
                param_str += "&total_count=" + args.total_count

        resource_instance = ResourceModel.objects.filter(res_id=res_id).first()
        cmdb_p_code = resource_instance.cmdb_p_code

        if cmdb_p_code is None:
            Log.logger.warning("The data of cmdb_p_code is not found for resource id " + res_id)
            return response_data_not_found(), 200
        else:
            CMDB_URL = current_app.config['CMDB_URL']
            CMDB_RELATION = CMDB_URL + 'cmdb/api/repo_relation/'
            if param_str == "?":
                # req_str = CMDB_RELATION + cmdb_p_code + '/'
                layer_and_total_count = '/?layer_count=10&total_count=200'
                reference_types = '&reference_type=dependent'
                reference_sequence = '&reference_sequence=[{\"child\": 3},{\"bond\": 2},{\"parent\": 5}]'
                item_filter = ''
                columns_filter = '&columns_filter={' + \
                                 '\"project_item\":[\"name\"],' + \
                                 '\"deploy_instance\":[\"name\"],' + \
                                 '\"app_cluster\":[\"name\"],' + \
                                 '\"mysql_cluster\":[\"mysql_cluster_wvip\",\"mysql_cluster_rvip\",\"port\"],' + \
                                 '\"mongodb_cluster\":[\"mongodb_cluster_ip1\",\"mongodb_cluster_ip2\",\"mongodb_cluster_ip3\",\"port\"],' + \
                                 '\"redis_cluster\":[\"redis_cluster_vip\",\"port\"],' + \
                                 '\"mysql_instance\":[\"ip_address\",\"port\",\"mysql_dbtype\"],' + \
                                 '\"mongodb_instance\":[\"ip_address\",\"port\",\"dbtype\"],' + \
                                 '\"redis_instance\":[\"ip_address\",\"port\",\"dbtype\"],' + \
                                 '\"virtual_server\":[\"ip_address\",\"hostname\"],' + \
                                 '\"docker\":[\"ip_address\",\"hostname\"],' + \
                                 '\"physical_server\":[\"ip_address\",\"device_type\"],' + \
                                 '\"rack\":[\"rack_number\"],' + \
                                 '\"idc_item\":[\"name\",\"idc_address\"]' + \
                                 '}'
                req_str = CMDB_RELATION + cmdb_p_code + layer_and_total_count + reference_types + reference_sequence + \
                          item_filter + columns_filter
            else:
                req_str = CMDB_RELATION + cmdb_p_code + param_str

            Log.logger.debug("The Request Body is: " + req_str)

            ci_relation_query = requests.get(req_str)
            Log.logger.debug(ci_relation_query)
            Log.logger.debug(ci_relation_query.content)
            ci_relation_query_decode = ci_relation_query.content.decode('unicode_escape')
            result = json.loads(ci_relation_query_decode)
            return result
    except Exception as e:
        Log.logger.error(str(e))
        return response_data_not_found()


# cmdb2.0 图搜素
def cmdb2_graph_search(args, res_id):
    view_dict = {
        "B3": "e7a8ed688f2e4c19a3aa3a65", # 资源 --> 机房
        "B2": "",
        "B1": "",
    }
    url = CMDB2_URL + "cmdb/openapi/scene_graph/action/"
    uid, token = get_uid_token()
    data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "id": view_dict["B3"],
            "name": "",
            "entity": []
        }
    }
    data_str = json.dumps(data)
    try:
        ret = requests.post(url, data=data_str)
        result = response_data(200, ret.json(), "")
    except Exception as exc:
        Log.logger.error("cmdb2_graph_search error:{}".format(str(exc)))
        result = response_data(200, str(exc), "")
    return result