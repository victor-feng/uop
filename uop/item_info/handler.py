# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
from uop.log import Log
from uop.util import TimeToolkit
from config import configs
from datetime import datetime
from flask import jsonify
import sys

def get_uid_token(dev, username="admin", password="admin123456", sign=""):
    CMDB2_URL = configs[dev].CMDB2_URL
    uid_token = {
        "code": -1,
        "data": {
            "uid":0,
            "token":""
        }
    }
    url = CMDB2_URL + "/cmdb/api/login/"
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
        return ret.json()
    except Exception as exc:
        uid_token["msg"] = str(exc)
        Log.logger.error("get uid from CMDB2.0 error:{}".format(str(exc)))
        return uid_token
