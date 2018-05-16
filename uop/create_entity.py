# -*- coding: utf-8 -*-
import datetime
import os
import json
import traceback
import requests
from uop.models import EntityCache
from uop.item_info.handler import get_uid_token
from config import APP_ENV, configs
from uop.log import Log
from uop.util import TimeToolkit

curdir = os.path.dirname(os.path.abspath(__file__))

CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CMDB2_USER = configs[APP_ENV].CMDB2_OPEN_USER
CMDB2_VIEWS = configs[APP_ENV].CMDB2_VIEWS
CRP_URL = configs[APP_ENV].CRP_URL


def get_cmdb2_entity():
    Log.logger.info("-------start cache the entity--------")
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
        Log.logger.info("Current dir is {}".format(curdir))
        with open(curdir + "/entity.txt", "w") as f:
            json.dump(entity_dict, f)
    except Exception as e:
        msg = traceback.format_exc()
        Log.logger.info("The entity save error is {}".format(msg))

if __name__ == '__main__':
    get_cmdb2_entity()

