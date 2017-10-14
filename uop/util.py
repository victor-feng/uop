# -*- coding: utf-8 -*-

from flask import current_app
import IPy
import requests
from uop.models import NetWorkConfig

def get_CRP_url(env=None):
    if env:
        CPR_URL = current_app.config['CRP_URL'][env]
    else:
        CPR_URL = current_app.config['CRP_URL']['dev']
    return CPR_URL

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
        crp_url = '%s%s'%(env_, 'api/openstack/port/count?network_id=%s'%(vlan_id))
        cur_res = requests.get(crp_url,  headers=headers)
        if cur_res.get('code') == 200:
            count = cur_res.result.res
            if total_count > int(count):
                network_id = vlan_id
                break
    return network_id

