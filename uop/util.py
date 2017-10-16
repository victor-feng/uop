# -*- coding: utf-8 -*-

from flask import current_app
import IPy
import requests
import json
from uop.models import NetWorkConfig
import threading

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
    ip = IPy.IP(sub_network)
    total_count = ip.len()
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


#def check_network_use(env):
#    networks = NetWorkConfig.objects.filter(env=env)
#    headers = {'Content-Type': 'application/json'}
#    network_id = ''
#    for network in networks:
#        vlan_id = network.vlan_id
#        sub_network = network.sub_network
#        ip = IPy.IP(sub_network)
#        total_count = ip.len()
#        env_ = get_CRP_url(env)
#        crp_url = '%s%s'%(env_, 'api/openstack/port/count')
#        data = {'network_id': vlan_id}
#        data_str = json.dumps(data)
#        cur_res = requests.get(crp_url, data=data_str,  headers=headers)
#        cur_res = json.loads(cur_res.content)
#        if cur_res.get('code') == 200:
#            count = cur_res.get('result').get('res')
#            if total_count > int(count):
#                network_id = vlan_id
#                break
#    return network_id

