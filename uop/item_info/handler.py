# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
import sys
import os
from uop.log import Log
from uop.util import TimeToolkit
from config import configs, APP_ENV
from datetime import datetime
from flask import jsonify


__all__ = [
    "get_uid_token", "Aquery", "get_entity",
    "subgrath_data", "package_data"
]
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CMDB2_MODULE ={
    0: "Person",
    1: "department", #部门
    3: "Moudle", #模块
    2: "yewu", #业务
    4: "project", #工程
}

id_property = {
    2: [
        {
            "id": 1,
            "name": u"名称",
            "code": "name",
            "value_type": "str"
        },
        {
            "id": 2,
            "name": u"英文名称",
            "code": "e-name",
            "value_type": "str"
        },
    ],
    3: [
        {
            "id": 1,
            "name": u"名称",
            "code": "name",
            "value_type": "str"
        },
        {
            "id": 2,
            "name": u"英文名称",
            "code": "e-name",
            "value_type": "str"
        },
    ],
    4: [
        {
            "id": 1,
            "name": u"名称",
            "code": "name",
            "value_type": "str"
        },
        {
            "id": 2,
            "name": u"英文名称",
            "code": "e-name",
            "value_type": "str"
        },
    ],
    5: [
        {
            "id": 1,
            "name": u"名称",
            "code": "name",
            "value_type": "str"
        },
        {
            "id": 2,
            "name": u"英文名称",
            "code": "e-name",
            "value_type": "str"
        },
    ],
}


def get_data_from_file(td):
    '''
    临时从文本里获取数据
    :param td:
    :return:
    '''
    curdir = os.path.dirname(os.path.abspath(__file__))
    with open(curdir + "/json.txt", "rb") as fp:
        whole_data = json.load(fp)["data"]
    instance_id = td["data"]["instance"]["instance_id"]
    model_id = td["data"]["instance"]["model_id"]
    # Log.logger.info("whole_data:{},{}\n, instance_id:{}".format(whole_data, type(whole_data), instance_id))
    data = [wd for wd in whole_data if str(wd["parent_id"]) == str(instance_id)][0]
    data.update(property=id_property[data["model_id"]])
    return data

def push_data_to_file(parent_id, model_id, property):
    '''
    向文本里写数据
    :param property:
    [
    {   "name" : "实例中文名",
        ""
    }
    ]
    :return:
    '''
    try:
        curdir = os.path.dirname(os.path.abspath(__file__))
        with open(curdir + "/json.txt", "rb") as fp:
            whole_data = json.load(fp)["data"]
        Log.logger.info("whole_data:{},{}\n, instance_id:{}".format(whole_data, type(whole_data), parent_id))
        data = [p for p in property if str(p["code"]) == "name"]
        node = [wd for wd in whole_data if str(wd["parent_id"]) == str(parent_id)][0]
        instance_list = [n["instance"] for n in node]
        node_id_list = [n["instance_id"] for n in instance_list]
        new_id = str(max(node_id_list) + 1)
        new_instance = {
            "name": data["value"],
            "instance_id": new_id
        }
        node["instance"].append(new_instance)
        for k, v in enumerate(whole_data):
            if str(v["parent_id"]) == str(parent_id):
                whole_data[k] = node
                break
        Log.logger.info("new whole_data: {}".format(whole_data))
        with open(curdir + "/json.txt", "w") as fp:
            json.dump({"data": whole_data}, fp)
    except Exception as exc:
        Log.logger.error("push_data_to_file: {}".format(str(exc)))
    return node

# 获取uid，token
def get_uid_token(username="admin", password="admin", sign=""):
    uid, token = 0, 0
    url = CMDB2_URL + "cmdb/openapi/login/"
    data = {
        "username": username,
        "password": password,
        "sign": sign,
        "timestamp": TimeToolkit.local2utctimestamp(datetime.now())
    }
    data_str = json.dumps(data)
    try:
        ret = requests.post(url, data=data_str)
        Log.logger.info(ret.json())
        uid, token = ret.json()["data"]["uid"], ret.json()["data"]["token"]
    except Exception as exc:
        Log.logger.error("get uid from CMDB2.0 error:{}".format(str(exc)))
    return uid, token


#A类视图查询
def Aquery(data):
    '''
    A 类视图 查询
    :param data:
    :return:
    '''
    query_result = {}
    data_str = json.dumps(data)
    url = CMDB2_URL + "cmdb/openapi/query/instance/"  # 查询 A类视图 查到下一层关系
    try:
        ret = get_data_from_file(data)
        # ret = requests.post(url, data=data_str).json()
        # if ret["code"] != 0:  # 过期，重新获取uid,token
        #     data["uid"], data["token"] = get_uid_token()
        #     data_str = json.dumps(data)
            # ret = requests.post(url, data=data_str).json()
        query_result = ret
    except Exception as exc:
        Log.logger.error("get data from CMDB2.0 error:{}".format(str(exc)))
    return query_result


#获取实体属性
def get_entity(req_data):
    '''
    获取单个实体属性信息
    {
        "id": 实体id
        "name": 实体名
        "code": 实体英文名
        "parameters":[
            {
                'id': 属性id
                'name': 属性名
                'code': 属性编码
                'value_type': 属性类型
            }
        ]
    }
    :param req_data:
    :return:
    '''
    url = CMDB2_URL + "cmdb/openapi/entity/"
    data_str = json.dumps(req_data)
    entity_info = {}
    try:
        ret = requests.post(url, data=data_str).json()
        if ret["code"] != 0:
            req_data["uid"], req_data["code"] = get_uid_token()
            data_str = json.dumps(req_data)
            ret = requests.post(url, data=data_str).json()
        Log.logger.info("get entity info from CMDB2.0: {}".format(ret))
        entity_info = ret["data"]["parameters"]
    except Exception as exc:
        Log.logger.error("get entity info from CMDB2.0 error: {}".format(exc))
    return entity_info


#插入子图
def subgrath_data(args):
    '''
    插入子图数据，并返回图结果
    :param args:
    :return:
    '''
    entity_id, instance_id, property, uid, token = \
        args.model_id, args.instance_id, args.property, args.uid, args.token
    if not uid or not token:
        uid, token = get_uid_token()
    url = CMDB2_URL + "cmdb/openapi/graph/"
    format_data, graph_data = {}, {}
    data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "instance": [
                {
                    "entity_id": entity_id,
                    "instance_id": "",
                    "parameters":[
                        {}
                    ]
                }
            ],
            "relation": []
        }
    }
    data_str = json.dumps(data)
    try:
        # ret = requests.post(url, data=data_str).json()
        graph_data=push_data_to_file(instance_id, entity_id, property)
        format_data = package_data(graph_data, data)
    except Exception as exc:
        Log.logger.error("graph_data: {}".format(graph_data))
    return format_data


#组装业务工程模块接口数据
def package_data(ret, ut):
    '''
    传给前端的数据格式
    "uid": 1,
    "token": wtf,
    "module_id":123, #实体id
    "instance":[
        {
        "name":u"toon基础",
        "instance_id":123-1 #实例id
        },
        {
        "name":u"企通",
        "instance_id":123-2
        },
    ],
    ]
    '''
    # data = {
    #     "uid": 1,
    #     "token": 'wtf',
    #     "parent_id":2,
    #     "entity_id":3, #实体id
    #     "instance":[
    #         {
    #             "name":u"toon基础",
    #             "instance_id":'1231' #实例id
    #         },
    #         {
    #             "name":u"企通",
    #             "instance_id":'1232'
    #         },
    #         {
    #             "name": u"政通",
    #             "instance_id": '1233'
    #         },
    #         {
    #             "name": u"食尚",
    #             "instance_id": '1234'
    #         },
    #     ],
    # }
    ret.update(ut)
    ret.pop("data")
    return ret
