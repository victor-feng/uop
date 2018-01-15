# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
import os
from uop.log import Log
from uop.util import TimeToolkit, response_data
from config import configs, APP_ENV
from datetime import datetime
from uop.models import Cmdb, Token
from uop.res_callback.handler import *
import base64

curdir = os.path.dirname(os.path.abspath(__file__))
__all__ = [
    "get_uid_token", "Aquery", "get_entity",
    "subgrath_data", "package_data", "get_entity_from_file",
    "fix_instance", "delete_instance"
]

CMDB2_URL = configs[APP_ENV].CMDB2_URL
CMDB2_USER = configs[APP_ENV].CMDB2_OPEN_USER
CMDB2_VIEWS = configs[APP_ENV].CMDB2_VIEWS
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


#临时从本地文件读取数据
def get_data_from_file(td):
    '''
    临时从文本里获取数据
    :param td:
    :return:
    '''
    with open(curdir + "/json.txt", "rb") as fp:
        whole_data = json.load(fp)["data"]
    instance_id = td["data"]["instance"]["instance_id"]
    model_id = int(td["data"]["instance"]["model_id"])
    # Log.logger.info("whole_data:{},{}\n, instance_id:{}".format(whole_data, type(whole_data), instance_id))
    data = [wd for wd in whole_data if str(wd["parent_id"]) == str(instance_id)]
    data = data[0] if data else {"instance": [], "model_id": model_id + 1} #假数据中只需+1
    data.update(property=id_property[int(model_id + 1)])
    return data


#临时将数据写入本地文件
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
        with open(curdir + "/json.txt", "rb") as fp:
            whole_data = json.load(fp)["data"]
        Log.logger.info("whole_data:{}\nparent_id:{}\nproperty:{},{}".format(whole_data, parent_id, property, type(property)))
        data = [p for p in property if str(p["code"]) == "name"][0]
        node = [wd for wd in whole_data if str(wd["parent_id"]) == str(parent_id)]
        if node:
            node = node[0]
            node_id_list = [int(n["instance_id"]) for n in node["instance"]]
            new_id = str(max(node_id_list) + 1)
        else:
            node = {
                "parent_id": int(parent_id),
                "model_id": int(model_id),
                "instance":[],
            }
            new_id = str(model_id) + '1'
        new_instance = {
            "name": data["value"],
            "instance_id": new_id
        }
        node["instance"].append(new_instance)
        for k, v in enumerate(whole_data):
            if str(v["parent_id"]) == str(parent_id):
                whole_data[k] = node
                break
        else:
            whole_data.append(node)
        Log.logger.info("node:{},type:{}".format(node, type(node)))
        Log.logger.info("new whole_data: {}".format(whole_data))
        with open(curdir + "/json.txt", "w") as fp:
            json.dump({"data": whole_data}, fp)
    except Exception as exc:
        Log.logger.error("push_data_to_file: {}".format(str(exc)))
    return node


# 获取uid，token,并缓存
def get_uid_token(flush=False):
    cmdb_info = Cmdb.objects.filter(username=CMDB2_USER)
    tu = Token.objects.all()
    username, password, uid, token = "", "","", ""
    for ci in cmdb_info:
        username = ci.username
        password = base64.b64decode(ci.password)
    for one in tu:
        uid, token = one.uid, one.token
    if uid and token and not flush:
        return uid, token
    url = CMDB2_URL + "cmdb/openapi/login/"
    data = {
        "username": username,
        "password": password,
        "sign": "",
        "timestamp": TimeToolkit.local2utctimestamp(datetime.now())
    }
    data_str = json.dumps(data)
    try:
        Log.logger.info("login data:{}".format(data))
        ret = requests.post(url, data=data_str)
        Log.logger.info(ret.json())
        if ret.json()["code"] == 0:
            uid, token = ret.json()["data"]["uid"], ret.json()["data"]["token"]
            one = Token.objects.filter(uid=uid)
            if one:
                for _ in one:
                    _.update_one(token=token)
            else:
                tu = Token(uid=uid, token=token)
                tu.save()
    except Exception as exc:
        Log.logger.error("get uid from CMDB2.0 error:{}".format(str(exc)))
    return uid, token


# 将实体信息数据导入文件
def push_entity_to_file(data):
    entity_list = []
    try:
        for d in data:
            for dc in d.get("children", []):
                if not dc.get("children"):
                    entity_list.append({
                        "code": dc.get("code",""),
                        "name": dc.get("name",""),
                        "id": dc.get("id",""),
                        "property": dc.get("parameters",[])
                    })
                else:
                    processs_chidren_final(entity_list, dc.get("children"))
                    # with open(curdir + "/.entity.txt", "w") as fp:
                    #     json.dump({"entity": entity_list}, fp) # 后期CMDB2.0稳定后，考虑加入文件缓存，或redis
    except Exception as exc:
        Log.logger.error("push_entity_to_file error:{} ".format(str(exc)))
    # Log.logger.info("push_entity_to_file entity_list:{} ".format(entity_list))
    return {"entity": entity_list}


def processs_chidren_final(entity_list, children):
    # entity_list = copy.deepcopy(entity_list)
    Log.logger.info("in processs_chidren_final")
    for c in children:
        if not c.get("children"):
            entity_list.append({
                "code": c.get("code", ""),
                "name": c.get("name", ""),
                "id": c.get("id", ""),
                "property": c.get("parameters", [])
            })
        else:
            processs_chidren_final(entity_list, c.get("chidren"))


def get_entity_from_file(data):
    filters = {
        "Person":       "d8098981df71428784e65427",
        "department":   "9a544097f789495e8ee4f5eb",
        "yewu":         "c73339db70cc4647b515eaca",
        "Module":       "9e97b54a4a54472e9e913d4e",
        "project":      "59c0af57133442e7b34654a3",
        "host":         "b593293378c74ba6827847d3",
        "container":    "d0f338299fa34ce2bf5dd873",
        "virtual_device":"d4ad23e58f31497ca3ad2bab",
        "tomcat":   "d1b11a713e8842b2b93fe397",
        "mysql": "e5024d360b924e0c8de3c6a8",
        "redis": "de90d618f7504723b677f196",
        "mongodb": "9bc4a41eb6364022b2f2c093",
    }
    sort_key = ["Person", "department", "yewu", "Module", "project"]
    sort_key.extend(list(set(filters.keys()) ^ set(sort_key)))
    assert(isinstance(filters, dict))
    # if not os.path.exists(curdir + "/.entity.txt"):
    #     whole_entity = get_entity()
    # else:
    #     with open(curdir + "/.entity.txt", "rb") as fp:
    #         whole_entity = json.load(fp)["entity"]
    whole_entity = get_entity(data)["entity"] # CMDB2.0模型不稳定，暂时不使用文件缓存后其他缓存
    Log.logger.info("get entity info from CMDB2.0: {}".format(len(whole_entity)))
    compare_entity = map(lambda  x:{'id': x["id"], "name": x["name"], "code": x["code"], "property": str(x["property"])}, whole_entity)
    single_entity = filter(lambda x:set(x.values()) & set(filters.values()), compare_entity)
    if len(single_entity) == len(filters.keys()): # 缓存的实体id没问题，直接补充字段返回
        single_entity = map(lambda x:{'id': x["id"], "name": x["name"], "code": x["code"], "property": eval(str(x["property"]))}, single_entity)
        single_entity = list(
            (lambda item, key:((filter(lambda x: x["code"] == k, item)[0] for k in key)))(single_entity, sort_key)
        ) # 排个序
    else:
        single_entity = u"CMDB2.0 基础模型数据有变，联系管理员解决"
    return single_entity


#A类视图查询
def Aquery(args):
    '''
    A 类视图 查询
    :param data:
    :return:
    '''
    name, code, uid, token, instance_id, model_id, self_model_id = \
        args.name, args.code, args.uid, args.token, args.instance_id, args.model_id, args.self_model_id
    url_list = CMDB2_URL + "cmdb/openapi/instance/list/"
    url_instance = CMDB2_URL + "cmdb/openapi/query/instance/"  # 如果传instance_id，调用这个直接拿到下一层数据
    if not uid or not token:
        uid, token = get_uid_token()
    data_list =  {
        "uid": uid,
        "token": token,
        "sign":"",
        "data":{
            "instance":[{
                "instance_id":"",
                "name": name #工号
            }],
            "entity":{
                "model_id": self_model_id
            }
        }
    }
    data_instance = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "instance": {
                "model_id": self_model_id ,
                "instance_id": instance_id
            }
        }
    }
    data_list_str = json.dumps(data_list)
    data_instance_str = json.dumps(data_instance)
    try:
        if instance_id:
            Log.logger.info("url_instance request data:{}".format(data_instance))
            ret = requests.post(url_instance, data=data_instance_str)
            Log.logger.info("url_instance return:{}".format(ret.json()))
            data = analyze_data(ret.json()["data"], model_id)
        else:
            Log.logger.info("url_list request data:{}".format(data_list))
            ret = requests.post(url_list, data=data_list_str)
            Log.logger.info("url_list return:{}".format(ret.json()))
            data = analyze_data(ret.json()["data"], model_id, flag=True)
    except Exception as exc:
        Log.logger.error("Aquery error:{}".format(str(exc)))
        data = str(exc)
    data.update({"uid": uid, "token": token})
    result = response_data(200, "success", data)
    return result


#从B类视图中解析出A类数据
def analyze_data(data, entity_id, flag=False):
    ret = {
        "instance":[]
    }
    if flag: # list接口的数据
        instance = map(lambda x: {"instance_id": x.get("id"), "name": x.get("name"), "property": x.get("parameters")}, data) # 拿到名字为name的用户的实例id，理论上只有一个
    else: # instance接口的数据
        data = filter(lambda x: x.get("entity_id") == entity_id, data)
        if data:
            data = data[0] # 理论上一层下只有一个实体id
            instance = list(dequeued_list(data["instance"], lambda x: x.get("id"))) # 根据实例id去重
        else:
            instance = []
    ret["instance"] = instance
    return ret


# 列表字典按键去重
def dequeued_list(item, key):
    assert(isinstance(item, list))
    unique = set()
    for i, v in enumerate(item):
        if key(v) not in unique:
            unique.add(key(v))
            new = {"instance_id": v.get("id"), "name": v.get("name"), "property": v.get("parameters")}
            yield new


#获取所有模型实体的id及属性信息存到文件
def get_entity(data):
    '''
    [
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
    ]
    :param req_data:
    :return:
    '''
    url = CMDB2_URL + "cmdb/openapi/entity/group/"
    uid, token = data.get("uid"), data.get("token")
    if not uid and not token:
        uid, token = get_uid_token()
    req_data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "name":"",
            "code":"",
            "id":""
        }
    }
    data_str = json.dumps(req_data)
    entity_info = {}
    try:
        ret = requests.post(url, data=data_str).json()
        if ret["code"] != 0:
            req_data["uid"], req_data["code"] = get_uid_token(True)
            data_str = json.dumps(req_data)
            ret = requests.post(url, data=data_str).json()
        # Log.logger.info("get entity info from CMDB2.0: {}".format(ret))
        entity_info = push_entity_to_file(ret.get("data"))
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
    next_model_id, last_model_id, property, uid, token, last_instance_id= \
        args.next_model_id, args.last_model_id, args.property, args.uid, args.token, args.last_instance_id
    url = CMDB2_URL + "cmdb/openapi/graph/"
    format_data, graph_data = {}, {}
    data = get_relations(CMDB2_VIEWS["3"][0])
    if not uid and not token:
        data["uid"], data["token"] = get_uid_token()
    models_list = get_entity_from_file(data)
    if isinstance(models_list, str):
        return models_list
    model = filter(lambda x:x["id"] == next_model_id, models_list)[0]
    item = {}
    nouse = map(lambda pro: item.setdefault(pro["code"], pro["value"]), property)
    up_level = {
        "model_id": last_model_id,
        "instance_id": last_instance_id
    }
    i, r = format_data_cmdb(data["relations"], item, model, {}, 0, up_level)
    data.pop("relations")
    data["data"] = {
        "instance":[i],
        "relation":r
    }
    data_str = json.dumps(data)
    try:
        Log.logger.info("graph_data request: {}".format(data))
        ret = requests.post(url, data=data_str).json()
        Log.logger.info("graph_data result: {}".format(ret))
    except Exception as exc:
        ret = []
        Log.logger.error("graph_data: {}".format(graph_data))
    return ret


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


def fix_instance(args):
    url = CMDB2_URL + "cmdb/openapi/graph/"
    model_id, instance_id, property, uid, token = \
        args.model_id, args.instance_id, args.property, args.uid, args.token
    if not uid or not token:
        uid, token = get_uid_token()
    data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "instance": [
                {
                    "model_id": model_id,
                    "instance_id": instance_id,
                    'parameters': list(
                        (
                            lambda property:
                            (
                                {
                                    "code": pro["code"],
                                    "value": pro["value"]
                                }
                                for pro in property
                            )
                        )(property)
                    )
                }
            ]
        }
    }
    data_str = json.dumps(data)
    try:
        Log.logger.info("post 'fix instances data' to cmdb/openapi/graph/ request:{}".format(data))
        instance = requests.post(url, data=data_str).json()
        Log.logger.info("post return json:{}".format(instance))
        instance = instance["data"]["instance"]
        Log.logger.info("post 'fix instances data' to cmdb/openapi/graph/ result:{}".format(instance))
    except Exception as exc:
        instance = []
        Log.logger.error("post 'fix instances data' to cmdb/openapi/graph/ error:{}".format(str(exc)))
    data.pop("data")
    data.update({
        "instance": instance
    })
    return data


def delete_instance(args):
    url = CMDB2_URL + "cmdb/openapi/graph/"
    delete_list = args.delete_list
    assert(isinstance(delete_list, list))
    uid, token = get_uid_token()
    data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "instance": delete_list
        }
    }
    data_str = json.dumps(data)
    try:
        Log.logger.info("delete 'instances' to cmdb/openapi/graph/ request:{}".format(data))
        instance = requests.delete(url, data=data_str).json()
        Log.logger.info("delete return json:{}".format(instance))
        Log.logger.info("delete 'instances' to cmdb/openapi/graph/ result:{}".format(instance))
    except Exception as exc:
        instance = []
        Log.logger.error("delete 'instances' to cmdb/openapi/graph/ error:{}".format(str(exc)))
    data.pop("data")
    data.update({
        "instance": instance
    })
    return data











