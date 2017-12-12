# -*- coding: utf-8 -*-

import json
import copy
import requests
import datetime
from uop.models import User, ResourceModel, StatusRecord,OS_ip_dic,Deployment
from uop.deployment.handler import attach_domain_ip
from uop.util import async
from uop.log import Log


__all__ = [
    "transition_state_logger", "transit_request_data",
    "transit_repo_items", "do_transit_repo_items",
    "get_resources_all_pcode", "filter_status_data",
    "push_vm_docker_status_to_cmdb", "deploy_nginx_to_crp"
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
                item_mapper_keys = one_item_sequence.keys()
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
    resources = ResourceModel.objects.all()
    pcode_list = []
    for res in resources:
        code = res.cmdb_p_code
        if code:
            pcode_list.append(code)
    return pcode_list

def filter_status_data(p_code):
    data = {
        "vm_status":[]
    }
    Log.logger.info("filter_status_data.p_code:{}".format(p_code))
    res = ResourceModel.objects.filter(cmdb_p_code=p_code)
    for r in res:
        osid_ip_list = r.os_ins_ip_list
        Log.logger.info("filter_status_data.p_code:{}".format(osid_ip_list))
        for oi in osid_ip_list:
            meta = {}
            meta["resource_id"] = r.res_id
            meta["user_id"] = r.user_id
            meta["resource_name"] = r.resource_name
            meta["item_name"] = r.project
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
            meta["os_type"] = oi.os_type
            meta["status"] = "active"
            data["vm_status"].append(meta)
    return data

@async
def push_vm_docker_status_to_cmdb(url, p_code=None):
    if not p_code:
        Log.logger.info("push_vm_docker_status_to_cmdb pcode is null")
        return
    data = filter_status_data(p_code)
    Log.logger.info("Start push vm and docker status to CMDB, data:{}".format(data))
    try:
        ret = requests.post(url, data=json.dumps(data)).json()
        Log.logger.info("push CMDB vm and docker status result is:{}".format(ret))
    except Exception as exc:
        Log.logger.error("push_vm_docker_status_to_cmdb pcode is error:{}".format(exc))

@async
def deploy_nginx_to_crp(resource_id,url,set_flag):
    try:
        resource = ResourceModel.objects.get(res_id=resource_id)
        deps = Deployment.objects.filter(resource_id=resource_id).order_by('-created_time')
        dep = deps[0]
        deploy_id = dep.deploy_id
        app_image=dep.app_image
        app_image=eval(app_image)
        appinfo = attach_domain_ip(app_image, resource,None)
        Log.logger.debug(appinfo)
        data = {}
        data["deploy_id"] = deploy_id
        data["set_flag"] = set_flag
        data["appinfo"] = appinfo
        headers = {'Content-Type': 'application/json',}
        data_str = json.dumps(data)
        Log.logger.debug("Data args is " + str(data))
        Log.logger.debug("URL args is " + url)
        result = requests.put(url=url, headers=headers, data=data_str)
        Log.logger.debug(result)
    except Exception as e:
        Log.logger.error("[UOP] Resource deploy_nginx_to_crp failed, Excepton: %s", e.args)

