# -*- coding: utf-8 -*-
import json
import requests
import datetime
from uop.log import Log
from flask import current_app
from uop.models import PermissionList

def add_person(name, user_id, department, contact_info, privilege):
    """
        cmdb1.0临时跳过了将用户权限信息入库操作
    """
    return True # 直接返回
    success = False
    already_exist = False
    CMDB_URL = current_app.config['CMDB_URL']
    CMDB_API = CMDB_URL+'cmdb/api/'
    req = CMDB_API + "repo_detail?item_id=person_item&p_code=user_id&value=" + user_id
    res = requests.get(str(req))
    ret_query_decode = res.content.decode('unicode_escape')
    ret = json.loads(ret_query_decode)
    if res.status_code == 200:
        repoitem_person = ret.get("result").get("res")
        if len(repoitem_person) is not 0:
            already_exist = True
            success = True

    if already_exist is False:
        data = {}
        data["name"] = u"人"
        data["layer_id"] = "Organization"
        data["group_id"] = "OrganizationLine"
        data["item_id"] = "person_item"

        property_list = []
        property_list.append({"type": "string", "p_code": "name", "name": u"姓名", "value": name})
        property_list.append({"type": "string", "p_code": "user_id", "name": u"员工工号", "value": user_id})
        property_list.append({"type": "string", "p_code": "department", "name": u"部门", "value": department})
        property_list.append({"type": "string", "p_code": "contact_info", "name": u"联系方式", "value": contact_info})
        property_list.append({"type": "string", "p_code": "privilege", "name": u"权限", "value": privilege})
        property_list.append({"type": "string", "p_code": "create_time", "name": u"创建时间",
                              "value": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        data["property_list"] = property_list
        data_str = json.dumps(data)


        CMDB_URL = current_app.config['CMDB_URL']
        CMDB_API = CMDB_URL+'cmdb/api/'

        res = requests.post(CMDB_API + "repo/", data=data_str)
        ret = eval(res.content.decode('unicode_escape'))
        if res.status_code == 200:
            success = True
    return success


def deal_children_data(data):
    res_list=[]
    try:
        for d in data:
            d=d.to_json()
            res_list.append(d)
    except Exception as e:
        Log.logger.error("UOP User deal children data error,error msg is %s" % str(e))
    return res_list


def get_menu_list(role):
    """
    根据角色获取菜单列表
    :param role:
    :return:
    """
    meau_list = []
    try:
        Permssions=PermissionList.objects.filter(role=role,prem_type="meau")
        for premssion in Permssions:
            meau_dict = {}
            name=premssion.name
            url=premssion.url
            _id=premssion.id
            buttons=premssion.buttons
            icons=premssion.icons
            children=premssion.menu2_permssion
            children=deal_children_data(children)
            meau_dict["name"] = name
            meau_dict["url"] = url
            meau_dict["id"] = _id
            meau_dict["buttons"] = buttons
            meau_dict["icons"] = icons
            meau_dict["children"] = children
            meau_list.append(meau_dict)
        return  meau_list
    except Exception as e:
        Log.logger.error("UOP User get menu list error,error msg is %s" % str(e) )
        return  meau_list