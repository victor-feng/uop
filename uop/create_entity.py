# -*- coding: utf-8 -*-
import datetime
import os
import json
import traceback
import requests
import base64
from models import EntityCache, Cmdb, Token, db
from util import TimeToolkit

curdir = os.path.dirname(os.path.abspath(__file__))


CMDB2_URL = "http://cmdb2-test.syswin.comvictor/"
CMDB2_USER = "uop"


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
        "timestamp": TimeToolkit.local2utctime(datetime.now())
    }
    data_str = json.dumps(data)
    try:
        # Log.logger.info("login data:{}".format(data))
        ret = requests.post(url, data=data_str, timeout=5)
        # Log.logger.info(ret.json())
        if ret.json()["code"] == 0:
            uid, token = ret.json()["data"]["uid"], ret.json()["data"]["token"]
            one = Token.objects.filter(uid=uid)
            if one:
                Token.objects(uid=uid).update_one(token=token, token_date=TimeToolkit.local2utctimestamp(datetime.now()))
            else:
                tu = Token(uid=uid, token=token, token_date=TimeToolkit.local2utctimestamp(datetime.now()))
                tu.save()
    except Exception as exc:
        pass
    return uid, token


def get_cmdb2_entity():

    uid, token = get_uid_token()
    url = CMDB2_URL + "cmdb/openapi/entity/group/"
    data = {
      "uid": uid,
      "token": token,
      "sign": "",
      "data": {
        "name": ""
      }
    }
    entity_dict = {}
    entity_list = []
    """
    dev not exist
    """
    entity_dict['codis'] = ""
    entity_dict['apache'] = ""
    entity_dict['zookeeper'] = ""
    res = requests.post(url, data=json.dumps(data)).json()
    #Log.logger.info("The cmdb2 entity res is {}".format(res))
    with db.app.app_context():
        if res["code"] == 0:
            for i in res["data"]:
                if i["children"]:
                    for j in i["children"]:
                        code = j["code"]
                        children_id = j["id"]
                        host = children_id if code == "host" else ""
                        Person = children_id if code == "Person" else ""
                        department = children_id if code == "department" else ""
                        yewu = children_id if code == "yewu" else ""
                        Module = children_id if code == "Module" else ""
                        project = children_id if code == "project" else ""
                        container = children_id if code == "container" else ""
                        virtual_device = children_id if code == "virtual_device" else ""
                        if host:
                            entity_dict['host'] = host
                        if Person:
                            entity_dict['Person'] = Person
                        if department:
                            entity_dict['department'] = department
                        if yewu:
                            entity_dict['yewu'] = yewu
                        if Module:
                            entity_dict['Module'] = Module
                        if project:
                            entity_dict['project'] = project
                        if container:
                            entity_dict['container'] = container
                        if virtual_device:
                            entity_dict['virtual_device'] = virtual_device
                        if j["children"]:
                            for a in j["children"]:
                                code = a["code"]
                                children_id = a["id"]
                                mysql = children_id if code == "mysql" else ""
                                redis = children_id if code == "redis" else ""
                                tomcat = children_id if code == "tomcat" else ""
                                rabbitmq = children_id if code == "rabbitmq" else ""
                                mongodb = children_id if code == "mongodb" else ""
                                nginx = children_id if code == "nginx" else ""
                                codis = children_id if code == "codis" else ""
                                apache = children_id if code == "apache" else ""
                                zookeeper = children_id if code == "zookeeper" else ""
                                mycat = children_id if code == "mycat" else ""
                                if mysql:
                                    entity_dict['mysql'] = mysql
                                if redis:
                                    entity_dict['redis'] = redis
                                if tomcat:
                                    entity_dict['tomcat'] = tomcat
                                if rabbitmq:
                                    entity_dict['rabbitmq'] = rabbitmq
                                if mongodb:
                                    entity_dict['mongodb'] = mongodb
                                if nginx:
                                    entity_dict['nginx'] = nginx
                                if codis:
                                    entity_dict['codis'] = codis
                                if apache:
                                    entity_dict['apache'] = apache
                                if zookeeper:
                                    entity_dict['zookeeper'] = zookeeper
                                if mycat:
                                    entity_dict['mycat'] = mycat
    # Log.logger.info("The entity dict is {}".format(entity_dict))
    entity_list.append(entity_dict)
    entity_data = json.dumps(entity_list)
    try:
        entity_obj = EntityCache(
            entity=entity_data,
            created_time=TimeToolkit.local2utctimestamp(datetime.datetime.now())
        )
        entity_obj.save()
        # 临时写入 文件
        with open(curdir + "/entity.txt", "w") as f:
            json.dump(entity_dict, f)
    except Exception as e:
        msg = traceback.format_exc()
        pass

if __name__ == '__main__':
    get_cmdb2_entity()

