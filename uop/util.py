# -*- coding: utf-8 -*-

from flask import current_app,jsonify
import IPy
import time
import requests
import json
from models import db

import threading
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from uop.models import NetWorkConfig, EntityCache


def get_entity_cache():
    with db.app.app_context():
        entity = EntityCache.objects().order_by("created_time").first()
        CMDB2_ENTITY = {
            "Person": entity.Person,
            "department": entity.department,
            "yewu": entity.yewu,
            "Module": entity.Module,
            "project": entity.project,
            "host": entity.host,
            "container": entity.container,
            "virtual_device": entity.virtual_device,
            "tomcat": entity.tomcat,
            "mysql": entity.mysql,
            "redis": entity.redis,
            "mongodb": entity.mongodb,
            "nginx": entity.nginx,
        }
        CMDB2_VIEWS = {
            # 注意：定时任务只会缓存1，2，3 三个视图下的基础模型数据
            "1": ("B7", u"工程 --> 物理机，用于拿到各层间实体关系信息", entity.project),  # （视图名，描述，起点实体id）
            "2": ("B6", u"部门 --> 资源，用于分级展示业务模块工程", entity.department),
            "3": ("B5", u"人 --> 部门 --> 工程", entity.Person),

            "4": ("B8", u"tomcat --> 机房，展示tomcat资源视图", entity.tomcat),
            "5": ("B9", u"mysql --> 机房，展示mysql资源视图", entity.mysql),
            "6": ("B10", u"mongodb--> 机房，展示mongodb资源视图", entity.mongodb),
            "7": ("B11", u"redis --> 机房，展示redis资源视图", entity.redis),
            "8": ("B12", u"物理机信息", entity.host),
            "9": ("B13", u"模块 --> 物理机，用于拿到各层间实体关系信息", entity.Module),
            "10": ("B14", u"nginx --> 机房，展示nginx资源视图", entity.nginx)
            # "5": ("B3", u"资源 --> 机房"),
        }
    return CMDB2_ENTITY, CMDB2_VIEWS


def async(fun):
    def wraps(*args, **kwargs):
        thread = threading.Thread(target=fun, args=args, kwargs=kwargs)
        thread.daemon = False
        thread.start()
        return thread
    return wraps


def get_CRP_url(env=None):
    if env:
        CPR_URL = current_app.config['CRP_URL'][env]
    else:
        CPR_URL = current_app.config['CRP_URL']['dev']
    return CPR_URL

def get_network_used(env, sub_network, vlan_id):
    sub_networks = sub_network.split(',')
    total_count = 0
    sub_networks = sub_networks[0:1]
    for net in sub_networks:
        ip = IPy.IP(net)
        _count = ip.len()
        total_count = total_count + _count
    headers = {'Content-Type': 'application/json'}
    env_ = get_CRP_url(env)
    crp_url = '%s%s'%(env_, 'api/openstack/port/count')
    data = {'network_id': vlan_id}
    data_str = json.dumps(data)
    cur_res = requests.get(crp_url, data=data_str,  headers=headers)
    cur_res = json.loads(cur_res.content)
    count = 0
    if cur_res.get('code') == 200:
        count = cur_res.get('result').get('res')
    return count, total_count


def check_network_use(env):
    networks = NetWorkConfig.objects.filter(env=env)
    headers = {'Content-Type': 'application/json'}
    network_id = ''
    for network in networks:
        vlan_id = network.vlan_id
        sub_network = network.sub_network
        ip = IPy.IP(sub_network)
        total_count = ip.len()
        env_ = get_CRP_url(env)
        crp_url = '%s%s'%(env_, 'api/openstack/port/count')
        data = {'network_id': vlan_id}
        data_str = json.dumps(data)
        cur_res = requests.get(crp_url, data=data_str,  headers=headers)
        cur_res = json.loads(cur_res.content)
        if cur_res.get('code') == 200:
            count = cur_res.get('result').get('res')
            if total_count > int(count):
                network_id = vlan_id
                break
    return network_id


class TimeToolkit(object):
    @staticmethod
    def utctimestamp2str(utctimestamp):
        utcs = float(utctimestamp) / 1000
        time_array = time.localtime(utcs)
        utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
        datetime_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
        _localtime = datetime_time + timedelta(hours=8)
        localtime = datetime.strftime(_localtime, "%Y-%m-%d %H:%M:%S")

        return localtime

    @staticmethod
    def utctimestamp2local(utctimestamp):
        utcs = long(utctimestamp) / 1000
        time_array = time.localtime(utcs)
        utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
        datetime_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")
        localtime = datetime_time + timedelta(hours=8)

        return localtime

    @staticmethod
    def timestramp2local(timestrap):
        _timestrap = long(timestrap)
        time_array = time.localtime(_timestrap)
        utc_time = time.strftime("%Y-%m-%d %H:%M:%S", time_array)
        datetime_time = datetime.strptime(utc_time, "%Y-%m-%d %H:%M:%S")

        return datetime_time

    @staticmethod
    def get_utc_milli_ts():
        return long(time.mktime(datetime.utcnow().timetuple())) * 1000

    @staticmethod
    def local2utctimestamp(dt, duration=None, flag=None):
        if duration:
            delta = dt + relativedelta(months=int(duration))
        else:
            delta = dt
        print delta
        if flag:
            utc_delta = delta
        else:
            utc_delta = delta + timedelta(hours=-8)
        return utc_delta

    @staticmethod
    def local2utctime(dt, flag=None):
        if flag:
            dt = dt + timedelta(hours=-8)
        return time.mktime(dt.timetuple())


def response_data(code, msg, data):
    ret = {
        "code": code,
        "result": {
            "msg": msg,
            "data": data,
        }
    }
    return ret

def pageinit(items, offset, limit):
    if offset < 0 or limit < 0:
        return []
    assert isinstance(items, list)
    total_len = len(items)
    pages = total_len / limit
    o_page = 1 if total_len % limit else 0
    total_pages = pages + o_page
    total_pages = total_pages if total_pages else 1
    if total_pages > offset:
        pre = (offset - 1) * limit
        last = offset * limit
        page_contents = items[pre:last]
    elif total_pages == offset:
        pre = (offset - 1) * limit
        page_contents = items[pre:]
    else:
        page_contents = []
    return page_contents, total_pages