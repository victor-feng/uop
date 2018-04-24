# -*- coding: utf-8 -*-

import json
import copy
import requests
import datetime
import time
import traceback
from uop.models import ResourceModel, StatusRecord,OS_ip_dic,Deployment, Cmdb, ViewCache, Statusvm, HostsCache
from uop.deployment.handler import attach_domain_ip
from uop.util import async, response_data, TimeToolkit
from uop.log import Log
from config import configs, APP_ENV
from threading import Lock

save_lock = Lock()
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CMDB2_USER = configs[APP_ENV].CMDB2_OPEN_USER
CMDB2_VIEWS = configs[APP_ENV].CMDB2_VIEWS
CMDB2_ENTITY = configs[APP_ENV].CMDB2_ENTITY
__all__ = [
    "transition_state_logger", "transit_request_data",
    "transit_repo_items", "do_transit_repo_items",
    "get_resources_all_pcode", "filter_status_data",
    "push_vm_docker_status_to_cmdb", "deploy_to_crp",
    "crp_data_cmdb", "format_data_cmdb", "get_relations"
]

# Transition state Log debug decorator
def transition_state_logger(func):
    def wrapper(self, *args, **kwargs):
        Log.logger.debug("Transition state is turned in " + self.state)
        ret = func(self, *args, **kwargs)
        Log.logger.debug("Transition state is turned out " + self.state)
        return ret
    return wrapper


# Transit request_data from the JSON nest structure to the chain structure with items_sequence and porerty_json_mapper
def transit_request_data(items_sequence, porerty_json_mapper, request_data):
    """
    :param items_sequence:  []
    :param porerty_json_mapper:  {}
    :param request_data:
    :return:
    """
    if request_data is None:
        return
    if not (isinstance(items_sequence, list) or isinstance(items_sequence, dict) or isinstance(items_sequence, set)) \
            or not (isinstance(request_data, list) or isinstance(request_data, dict)) \
            or not isinstance(porerty_json_mapper, dict):
        raise Exception("Need input dict for porerty_json_mapper and request_data in transit_request_data.")
    request_items = []
    if isinstance(items_sequence, list) or isinstance(items_sequence, set):
        for one_item_sequence in items_sequence:
            if isinstance(one_item_sequence, dict):
                item_mapper_keys = one_item_sequence.keys()  # deploy_instance
            elif isinstance(one_item_sequence, basestring):
                item_mapper_keys = [one_item_sequence]
            else:
                raise Exception("Error items_sequence_list_config")
            for item_mapper_key in item_mapper_keys:
                if isinstance(one_item_sequence, basestring):
                    context = None
                else:
                    context = one_item_sequence.get(item_mapper_key)
                item_mapper_body = porerty_json_mapper.get(item_mapper_key)
                if item_mapper_body is not None:
                    if isinstance(request_data, list) or isinstance(request_data, set):
                        for one_req in request_data:
                            item = {}
                            sub_item = copy.deepcopy(one_req)
                            item[item_mapper_key] = sub_item
                            request_items.append(item)
                            if context is not None and sub_item is not None:
                                request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                    else:
                        item = {}
                        current_item = copy.deepcopy(request_data)
                        item[item_mapper_key] = current_item
                        request_items.append(item)
                        if context is not None:
                            if hasattr(current_item, item_mapper_key):
                                sub_item = current_item.get(item_mapper_key)
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                            else:
                                sub_item = current_item
                                if sub_item is not None:
                                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                else:
                    if request_data is not None:
                        sub_item = request_data.get(item_mapper_key)
                        if context is not None and sub_item is not None:
                            request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
    elif isinstance(items_sequence, dict):
        items_sequence_keys = items_sequence.keys()
        for items_sequence_key in items_sequence_keys:
            context = items_sequence.get(items_sequence_key)
            item_mapper_body = porerty_json_mapper.get(items_sequence_key)
            if item_mapper_body is not None:
                current_items = copy.deepcopy(request_data)
                if hasattr(item_mapper_body, items_sequence_key):
                    current_items_keys = current_items.keys()
                    for current_item_key in current_items_keys:
                        if current_item_key == items_sequence_key:
                            current_item_body = current_items.get(current_item_key)
                            if current_item_body is not None and len(current_item_body) > 0:
                                item = current_items
                                request_items.append(item)
                else:
                    current_item_body = current_items
                    if current_item_body is not None and len(current_item_body) > 0:
                        item = {}
                        item[items_sequence_key] = current_item_body
                        request_items.append(item)
                    if context is not None:
                        if hasattr(current_items, items_sequence_key):
                            sub_item = current_items.get(items_sequence_key)
                            if sub_item is not None:
                                request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
                        else:
                            sub_item = current_items
                            if sub_item is not None:
                                request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))
            if context is not None and request_data is not None:
                sub_item = request_data.get(items_sequence_key)
                if sub_item is not None:
                    request_items.extend(transit_request_data(context, porerty_json_mapper, sub_item))

    return request_items


# Transit request_items from JSON property to CMDB item property p_code with property_json_mapper
def transit_repo_items(property_json_mapper, request_items):
    if not isinstance(property_json_mapper, dict) and not isinstance(request_items, list):
        raise Exception("Need input dict for property_json_mapper and list for request_items in transit_repo_items.")
    property_mappers_list = []
    for request_item in request_items:
        item_id = request_item.keys()[0]
        repo_property = {}
        item_property_mapper = property_json_mapper.get(item_id)
        item_property_keys = item_property_mapper.keys()
        for item_property_key in item_property_keys:
            value = request_item.get(item_id)
            if value is not None:
                repo_json_property = value.get(item_property_mapper.get(item_property_key))
                if repo_json_property is not None:
                    repo_property[item_property_key] = repo_json_property
        if len(repo_property) >= 1:
            repo_item = {}
            repo_item[item_id] = repo_property
            property_mappers_list.append(repo_item)
    return property_mappers_list


def do_transit_repo_items(items_sequence_list, property_json_mapper, request_data):
    request_items = transit_request_data(items_sequence_list, property_json_mapper, request_data)
    property_mappers_list = transit_repo_items(property_json_mapper, request_items)
    return property_mappers_list


def get_resources_all_pcode():
    resources = ResourceModel.objects.filter(is_deleted=0)
    pcode_list = []
    for res in resources:
        code = res.cmdb_p_code
        if code:
            pcode_list.append(code)
    return pcode_list


def filter_status_data(p_code, id, num):
    data = {
        "vm_status":[]
    }
    # Log.logger.info("filter_status_data.p_code:{}".format(p_code))
    res = ResourceModel.objects.filter(cmdb_p_code=p_code,is_deleted=0)
    for r in res:
        osid_ip_list = r.os_ins_ip_list
        compute_list = r.compute_list
        view_id, view_num = "", ""
        # Log.logger.info("filter_status_data.p_code:{}".format(osid_ip_list))
        if r.cloud == "2" and r.resource_type == "app":
            dirty = Statusvm.objects.filter(resource_id=r.res_id)
            if dirty:
                for d in dirty:
                    d.delete()
        for oi in osid_ip_list:
            meta = {}
            meta["resource_id"] = r.res_id
            meta["user_id"] = r.user_id
            meta["resource_name"] = r.resource_name
            meta["department"] = r.department
            meta["project_name"] = r.project_name
            meta["module_name"] = r.module_name
            meta["business_name"] = r.business_name
            meta["project_id"] = r.project_id
            meta["resource_view_id"] = "" if id == "@" else id
            meta["view_num"] = "" if num == "@" else num
            if compute_list:
                meta["domain"] = compute_list[0].domain
            meta["create_time"] =  datetime.datetime.strftime(r.created_date, '%Y-%m-%d %H:%M:%S')
            try:
                meta["cpu"] = str(oi.cpu)
                meta["mem"] = str(oi.mem)
            except:
                meta["cpu"] = "2"
                meta["mem"] = "4"
            meta["env"] = r.env
            meta["osid"] = oi.os_ins_id
            meta["ip"] = oi.ip
            meta["os_type"] = r.resource_type
            meta["status"] = "active"
            data["vm_status"].append(meta)
            vm = Statusvm.objects.filter(osid=meta["osid"])
            if not vm:
                Statusvm.created_status(**meta)
    Log.logger.info("Save to cmdb1.0 data is {}".format(data))
    return data


def push_vm_docker_status_to_cmdb(url, id, num, p_code=None):
    if not p_code:
        Log.logger.info("push_vm_docker_status_to_cmdb pcode is null")
        return
    data = filter_status_data(p_code, id, num)  # save to uop
    # Log.logger.info("Start push vm and docker status to CMDB, data:{}".format(data))
    try:
        ret = requests.post(url, data=json.dumps(data)).json()
        # Log.logger.info("push CMDB vm and docker status result is:{}".format(ret))
    except Exception as exc:
        Log.logger.error("push_vm_docker_status_to_cmdb pcode is error:{}".format(exc))


@async
def deploy_to_crp(resource_id,url,set_flag,cloud,increase_ips=[]):
    try:
        resource = ResourceModel.objects.get(res_id=resource_id)
        compute_list = resource.compute_list
        resource_name = resource.resource_name
        deploy_name = resource.deploy_name
        project_name = resource.project_name
        env = resource.env
        deps = Deployment.objects.filter(resource_id=resource_id).order_by('-created_time')
        dep = deps[0]
        deploy_id = dep.deploy_id
        app_image=dep.app_image
        app_image=eval(app_image)
        appinfo = attach_domain_ip(app_image, resource,None)
        Log.logger.debug(appinfo)
        data = {}
        docker_list=[]
        for compute in compute_list:
            ips = compute.ips
            if increase_ips:
                ips=increase_ips
            docker_list.append(
                {
                    'url': compute.url,
                    'ins_name': compute.ins_name,
                    'ip': ips,
                    'health_check': compute.health_check,
                    'host_env': compute.host_env,
                    'language_env': compute.language_env,
                    'deploy_source': compute.deploy_source,
                    'database_config': compute.database_config

                }
            )
        data["deploy_id"] = deploy_id
        data["set_flag"] = set_flag
        data["appinfo"] = appinfo
        data['docker'] = docker_list
        data["mysql"] = []
        data["mongodb"] = []
        data["dns"] = []
        data["disconf_server_info"] = []
        data["deploy_type"] = set_flag
        data["cloud"] = cloud
        data["resource_name"] = resource_name
        data["deploy_name"] = deploy_name
        data["project_name"] = project_name
        data["environment"] = env
        headers = {'Content-Type': 'application/json',}
        data_str = json.dumps(data)
        Log.logger.debug("Data args is " + str(data))
        Log.logger.debug("URL args is " + url)
        if cloud == '2' and set_flag == "increase":
            result = requests.post(url=url, headers=headers, data=data_str)
        else:
            result = requests.put(url=url, headers=headers, data=data_str)
        Log.logger.debug(result)
    except Exception as e:
        Log.logger.error("[UOP] Resource deploy_nginx_to_crp failed, Excepton: %s", e.args)


# 解析crp传回来的数据录入CMDB2.0
@async
def crp_data_cmdb(args, cmdb1_url):
    assert(isinstance(args, dict))
    Log.logger.info("###data:{}".format(args))
    # models_list = get_entity_from_file(args)
    CMDB_STATUS_URL = cmdb1_url + 'cmdb/api/vmdocker/status/'
    res_id = args.get('resource_id')
    resource = ResourceModel.objects.get(res_id=res_id)
    try:
        url = CMDB2_URL + "cmdb/openapi/graph/"
        module_id = args.get("module_id")
        if module_id:
            # 其他资源
            data = get_relations(CMDB2_VIEWS["9"][0])  # B13
            Log.logger.info("Get relations for B13..{}".format(data))
        else:
            data = get_relations(CMDB2_VIEWS["1"][0]) # B7
        models_list = data["entity"]
        status = args.get('status')
        error_msg = args.get('error_msg')
        set_flag = args.get('set_flag')
        resource_type = args.get('resource_type')
        physical_server_model_id = filter(lambda x: x["code"] == "host", models_list)[0]["entity_id"]
        env = resource.env
        cloud = resource.cloud
        flag = False
        if status != "ok":
            return
        if set_flag in ["increase", "reduce"]:
            if cloud == "2" and resource_type == "app":
                flag = True
            if not flag: # 按照常规扩缩容
                Log.logger.info("Virtual cloud increase".format(data))
                instances, relations = [], []
                statusvm = Statusvm.objects.filter(resource_id=res_id)
                docker_model = filter(lambda x: x["code"] == "container", models_list)[0]
                if statusvm:
                    for sv in statusvm:
                        tomcat_instance_id = sv.resource_view_id
                tomcat_level = {
                    "instance_id": tomcat_instance_id,
                    "model_id": CMDB2_ENTITY["tomcat"],
                    "_id": ""
                }
                for ct in args["container"]:
                    attach = {
                        "image_name": ct.get("image_url", ""),
                        "create_date": args.get("created_time", "")
                    }
                    for index, ins in enumerate(ct["instance"]):
                        ins["baseinfo"] = ins.get("instance_name")
                        i, r = format_data_cmdb(data["relations"], ins, docker_model, attach, len(instances), tomcat_level, physical_server_model_id)
                        instances.append(i)
                        relations.extend(r)
            else:
                Log.logger.info("Docker cloud increase".format(data))
                instances, relations = post_datas_cmdb(url, args, models_list, data["relations"])
        else:
            Log.logger.info("Start post datas to cmdb2,models_list is {}".format(models_list))
            instances, relations = post_datas_cmdb(url, args, models_list, data["relations"])
            Log.logger.info("End post datas to cmdb2,instance is {}\n relations is {}\n".format(instances, relations))
        uid, token = get_uid_token()
        data = {
            "uid": uid,
            "token": token,
            "sign":"",
            "data": {
                "relation": relations,
                "instance": instances
            }
        }
        data_str = json.dumps(data)
        ret = []

        Log.logger.info("post 'graph data' to cmdb/openapi/graph/ request:{}".format(data))
        ret = requests.post(url, data=data_str, timeout=5).json()
        if ret["code"] == 0:
            Log.logger.info("Save to CMDB2.0 successfully,{}".format(ret))
            db_flag = True if args.get("db_info") and set(args.get("db_info").keys()) & set(["mysql", "redis", "mongodb"])  else False
            if cloud == 1:
                push_vm_docker_status_to_cmdb(CMDB_STATUS_URL, "@", "@", resource.cmdb_p_code)
            else:
                # save uop and cmdb1
                save_resource_id(ret["data"]["instance"], res_id, cmdb1_url, set_flag, flag, db_flag)
        else: # 即便CMDB2失败，保存我的资源到UOP表
            Log.logger.info("Save to CMDB2.0 failed and save to uop and save to cmdb1.0")
            push_vm_docker_status_to_cmdb(CMDB_STATUS_URL, "@", "@", resource.cmdb_p_code)
            Log.logger.error("[CMDB2.0 graph error]:{}".format(ret))
    except Exception as exc:
        #即使往cmdb2写入数据失败，也往uop里面写入数据
        push_vm_docker_status_to_cmdb(CMDB_STATUS_URL, "@", "@", resource.cmdb_p_code)
        msg = traceback.format_exc()
        Log.logger.error("post 'graph data' to cmdb/openapi/graph/ error:{}".format(msg))


def save_resource_id(instances, res_id, cmdb1_url, set_flag, flag, db_flag):
    Log.logger.info("CMDB2.O instance_id: {}".format(instances))
    resource = ResourceModel.objects(res_id=res_id)
    res = ResourceModel.objects.get(res_id=res_id)
    get_view_num = lambda x: x[0] if x else ""
    instance = [ins for ins in instances if ins["_id"] == 1][0] if not db_flag else \
        [ins for ins in instances if ins["_id"] == 2][0]
    Log.logger.info("###Instance is {}".format(instance))
    if res.cloud == "2" or set_flag not in ["increase", "reduce"]: # 所有资源的第一次预留，和k8s的扩容
        view_id = str(instance["instance_id"])
        view_num = get_view_num(
                [view[0] for index, view in CMDB2_VIEWS.items() if view[2] == str(instance["model_id"])]
        ),
        Log.logger.info("###The view num is {}".format(view_num))
        view_num = view_num[0] if isinstance(view_num, tuple) else view_num
    if set_flag in ["increase"] and not flag: # 虚拟化云的扩容
        sv = Statusvm.objects.filter(resource_id=res_id)
        if sv:
            for s in sv:
                view_id, view_num = s.resource_view_id, s.view_num
                break
    Log.logger.info("resource_view_id:{}, view_num{}".format(view_id, view_num))
    CMDB_STATUS_URL = cmdb1_url + 'cmdb/api/vmdocker/status/'

    push_vm_docker_status_to_cmdb(CMDB_STATUS_URL, view_id, view_num, res.cmdb_p_code)
    def get_ip(ins):
        try:
            for os_ip in res.os_ins_ip_list:
                if os_ip.ip in str(ins["parameters"]):
                    os_ip.instance_id = ins["instance_id"]
                    os_ip.save()
            for p in ins["parameters"]:
                if p["code"].upper() == "IP":
                    return p["value"]
        except Exception as exc:
            Log.logger.error("get_ip error:{}".format(str(exc)))
        return ""
    ins_id = [ins["instance_id"] + "@_" + get_ip(ins) for ins in instances if ins["instance_id"]]
    if ins_id:
        try:
            with save_lock:
                resource.update_one(cmdb2_resource_id=ins_id)
            Log.logger.debug("[CMDB2.0 create graph SUCCESS]")
        except Exception as exc:
            Log.logger.error("save 'graph data' to UOP error:{}".format(str(exc)))
    else:
        Log.logger.warning("[CMDB2 插入预留数据出错，返回了空的实例id，请联系管理员查看CMDB2]")


def post_datas_cmdb(url, raw, models_list, relations_model):
    '''
    构建crp资源预留后返回的数据，已实现tomcat--->容器的存储
    目前按照code， 取实体信息，后期code
    :param url:
    :param raw: crp data
    :param models_list: entity list
    :param relations:
    :return:
    '''
    physical_server_model_id = filter(lambda x: x["code"] == "host", models_list)[0]["entity_id"]

    instances, relations = [], []

    # 一次预留生成的所有应用资源对应一个tomcat实例
    raw["baseinfo"] = raw["resource_name"]
    raw["create_date"] = raw["created_time"]
    module_id = raw["module_id"]

    docker_model = filter(lambda x: x["code"] == "container", models_list)[0]
    tomcat_model = filter(lambda x: x["code"] == "tomcat", models_list)[0]
    project_model = filter(lambda x: x["code"] == "project", models_list)[0]
    project_level = {
        "instance_id": raw["project_id"],
        "model_id": project_model["entity_id"],
        "_id": ""
    }
    tomcat, r = format_data_cmdb(relations_model, raw, tomcat_model, {}, len(instances), project_level)
    instances.append(tomcat)
    relations.extend(r)

    # docker数据解析
    for ct in raw["container"]:
        attach = {
            "image_name": ct.get("image_url", ""),
            "create_date": raw.get("created_time", "")
        }
        for index, ins in enumerate(ct["instance"]):
            ins["baseinfo"] = ins.get("instance_name")
            i, r = format_data_cmdb(relations_model, ins, docker_model, attach, len(instances), tomcat, physical_server_model_id)
            instances.append(i)
            relations.extend(r)

    # 中间件、虚拟机数据解析
    virtual_server_model = filter(lambda x: x["code"] == "virtual_device", models_list)[0]
    Log.logger.info("The virtual server model is {}".format(virtual_server_model))
    for db_name, db_contents in raw["db_info"].items():
        # Log.logger.info("now analyze {} data".format(db_name))
        db_model = filter(lambda x: x["code"] == db_name, models_list)[0] # db_name 设置保持与cmdb一致
        attach = {
            "version": db_contents["version"],
            "create_date": raw.get("created_time", ""),
            "baseinfo": db_contents["cluster_name"],
            "write_ip": db_contents.get("wvip", ""),
            "read_ip": db_contents.get("rvip", "")
        }
        virtual_server = {
            "memory": db_contents["mem"],
            "cpu": db_contents["cpu"],
            "disk": db_contents["disk"],
            "create_date": raw.get("created_time", "")
        }

        if raw["module_id"]:
            # module
            Log.logger.info("Raw modele id is exist {}, raw data is {}".format(raw['module_id'], raw))
            module_model = filter(lambda x: x["code"] == "Module", models_list)[0]
            module_level = {
                "instance_id": raw["module_id"],
                "model_id": module_model["entity_id"],
                "_id": ""
            }
            up_db, r = format_data_cmdb(relations_model, raw, db_model, {}, len(instances), module_level, physical_server_model_id)
            Log.logger.info("up_db is {}, r is {}".format(up_db, r))
            instances.append(up_db)
            relations.extend(r)
        else:
            up_db, r = format_data_cmdb(relations_model, db_contents, db_model, attach, len(instances), project_level, physical_server_model_id)
            instances.append(up_db)
            relations.extend(r)

        for index, db in enumerate(db_contents["instance"]):
            Log.logger.info("============")
            db["baseinfo"] = db.get("instance_name")
            i, r = format_data_cmdb(relations_model, db, virtual_server_model, virtual_server, len(instances), up_db, physical_server_model_id)
            instances.append(i)
            relations.extend(r)
    # Log.logger.info("[CMDB2.0 format DATA] instance:{}\n[CMDB2.0 format DATA] relations:{}\n".format(instances, relations))
    return instances, relations


def judge_value_format(item, pro, attach):
    """
    :param item: crp data
    :param pro:  cmdb entity parameters data
    :param attach: {
                        "image_name": ct.get("image_url", ""),
                        "create_date": args.get("created_time", "")
                }
    :return:
    """
    value_type = {
        "string": "",
        "int": 0,
        "double": 0
    }
    Log.logger.info("The item data is {}".format(item))
    if isinstance(item, list):
        if item:
            item = item[0]
        else:
            return value_type.get(str(pro["value_type"]))

    if str(pro["value_type"]) in value_type.keys():
        get_code = lambda x: x[0] if x else ""  # 由于CMDB模型code经常变动，会有一些字段存不进去的bug，后期处理
        code = get_code(list(
            (
                c for c in [str(pro["code"]).lower(), str(pro["code"]), str(pro["code"]).upper()] if
            item.get(c) or attach.get(c)
            )
        ))  # 由于CMDB模型code经常变动，会有一些字段存不进去的bug，后期处理
        one = item.get(code) if item.get(code) else attach.get(code)
        if one:
            # Log.logger.info("one data:{}".format(one))
            if str(pro["value_type"]) == "string":
                return str(one).decode(encoding="utf-8")
            elif str(pro["value_type"]) == "int":
                return int(one)
            else:  # 时间戳
                try:
                    time_str = one.split('.')[0]
                    time_date = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    return TimeToolkit.local2utctime(time_date)
                except Exception as exc:
                    return int(str(time.time()).split(".")[0])
        else:
            return value_type.get(str(pro["value_type"]))  # 统一空值类型
    else:
        return ""


def get_host_instance_id(name_ip):
    name, ip = name_ip.split("@")
    url = CMDB2_URL + "cmdb/openapi/scene_graph/action/"
    uid, token = get_uid_token()
    view_num = CMDB2_VIEWS["8"][0] # 物理机视图num
    res_id = CMDB2_VIEWS["8"][2] # 物理机实体id
    data = {
        "uid": uid,
        "token": token,
        "sign": "",
        "data": {
            "id": "",
            "name": view_num,
            "entity": [
                {
                    "id": res_id,
                    "parameters": [{
                        "code": "IP" if ip else "baseInfo",
                        "value": ip if ip else name
                    }]
                }
            ]
        }
    }
    data_str = json.dumps(data)
    try:

        cache_match = HostsCache.objects.filter(ip=ip) if ip else HostsCache.objects.filter(name=name)
        if cache_match:
            for cm in cache_match:
                return cm.instance_id
        Log.logger.info("cmdb2_graph_search request data:{}".format(data))
        ret_data = requests.post(url, data=data_str, timeout=5).json()["data"]
        Log.logger.info("####data:{}".format(ret_data))
        psid = ret_data["instance"][0]["instance_id"]
        host = HostsCache(instance_id=psid, name=name, ip=ip, cache_date=TimeToolkit.local2utctimestamp(datetime.datetime.now()))
        host.save()
    except Exception as exc:
        psid = ""
        msg = traceback.format_exc()
        Log.logger.error("data error:{}".format(msg))
    return psid


def format_data_cmdb(relations, item, model, attach, index, up_level, physical_server_model_id=None):
    '''

    :param relations: 从视图中缓存下来的所有实体关系信息
    :param item:   crp中当前层数据,例如：tomcat，docker，mysql等
    :param model:   当前层数据对应的实体信息
    :param attach: crp中当前层数据的补充信息
    :param index: 第几个实例
    :param up_level: 上一层实例信息
    :param physical_server_model_id: 可能存在的物理机实例id
    :return: 解析好的实例，及与实例相关的关系信息列表
    '''
    rels = []
    host_instance_id = "2a4d89e3e48b471da0ea41c1" # prod 测试用物理机
    # host_instance_id = "07a9542730b04cf099ea82ec" #  test 用物理机test
    i = {
        "model_id": model["entity_id"],
        "instance_id": "",
        "_id": index + 1,
        'parameters': list(
            (
                lambda property, item, attach:
                (
                    {
                        "value_type": str(pro["value_type"]),
                        "code": str(pro["code"]),
                        "value": judge_value_format(item, pro, attach)
                    }
                    for pro in property
                )
            )(model["parameters"], item, attach)
        )
    }
    if item.get("physical_server") and physical_server_model_id:  # 添加物理机的关系,目前没有物理机，暂时传名字作为id，后期用接口查物理机id
        Log.logger.info("crp data item is {}".format(item))
        psid = get_host_instance_id(item.get("physical_server"))
        host_instance_id = psid if psid else host_instance_id
        Log.logger.info("physical_server_model_id is {} , Host instance id is {}\n.".format(
            physical_server_model_id, host_instance_id))
        r = [
            dict(
                rel, start_id = i["_id"],
                end_instance_id = host_instance_id, # i.get("physical_server")
                end_id=""
            )
            for rel in relations if rel["start_model_id"] == i["model_id"] and rel["end_model_id"] == physical_server_model_id
        ]
        if not r:
            r = [
                dict(
                    rel, end_id=i["_id"],
                    start_instance_id=host_instance_id, # i.get("physical_server")
                    start_id=""
                )
                for rel in relations if rel["end_model_id"] == i["model_id"] and rel["start_model_id"] == physical_server_model_id
            ]
        rels.extend(r)
    # 添加普通上下层关系
    if up_level:
        Log.logger.info("##################")
        r = [
            dict(rel, start_id=i["_id"], end_instance_id=up_level.get("instance_id",""), end_id=up_level.get("_id",""))
            for rel in relations if
            rel["start_model_id"] == i["model_id"] and rel["end_model_id"] == up_level["model_id"]
        ]
        if not r:
            r = [
                dict(rel, end_id=i["_id"], start_instance_id=up_level.get("instance_id",""), start_id=up_level.get("_id",""))
                for rel in relations if rel["end_model_id"] == i["model_id"] and rel["start_model_id"] == up_level["model_id"]
            ]
        rels.extend(r)
    # Log.logger.info("Analyzed {}th data from crp:{} \n.".format(i["_id"], i))
    # Log.logger.info("Analyzed {}th data's relations from crp:{} \n.".format(i["_id"], rels))
    return i, rels


# B类视图list，获取已经定义的关系列表
def get_relations(view_id):
    '''
    按视图名字查询, id会有变动，保证名字不变就好
    :param view_id:
    :param uid:
    :param token:
    :return:
    '''
    Log.logger.info("get_relations from {} view".format(view_id))
    views = ViewCache.objects.filter(view_id=view_id)
    relations = []
    data  = {}
    for view in views:
        relations = json.loads(view.relation)
        entity = json.loads(view.entity)
    if not relations:
        uid, token = get_uid_token()
        url = CMDB2_URL + "cmdb/openapi/scene_graph/list/"
        data = {
            "uid": uid,
            "token": token,
            "sign": "",
            "data": {
                "id": "",
                "name": view_id
            }
        }
        data_str = json.dumps(data)
        try:
            ret = requests.post(url, data=data_str, timeout=5).json()
            if ret["code"] == 0:
                relations = ret["data"][0]["relation"]  # 获取视图关系实体信息
                entity = ret["data"][0]["entity"]  # 获取视图实体信息
                view = ViewCache(view_id=view_id, relation=json.dumps(relations), entity=json.dumps(entity), cache_date=TimeToolkit.local2utctimestamp(datetime.datetime.now()))
                view.save()
            elif ret["code"] == 121:
                data["uid"], data["token"] = get_uid_token(True)
                data_str = json.dumps(data)
                ret = requests.post(url, data=data_str, timeout=5).json()
                relations = ret["data"][0]["relation"]  # 获取视图关系实体信息,
                entity = ret["data"][0]["entity"]  # 获取视图实体信息
                view = ViewCache(view_id=view_id, relation=json.dumps(relations), entity=json.dumps(entity), cache_date=TimeToolkit.local2utctimestamp(datetime.datetime.now()))
                view.save()
            else:
                Log.logger.info("get_relations data:{}".format(ret))
        except Exception as exc:
            Log.logger.error("get_relations error: {}".format(str(exc)))
    data["relations"] = relations
    data["entity"] = entity
    return data


from uop.item_info.handler import *