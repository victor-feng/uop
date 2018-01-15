# -*- coding: utf-8 -*-

import datetime

import json
import requests
from models import db
from uop.util import get_CRP_url
from uop.models import ResourceModel, Deployment, Cmdb, ViewCache
from uop.item_info.handler import get_uid_token
from config import APP_ENV, configs
from uop.log import Log
from uop.util import async

CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CMDB2_USER = configs[APP_ENV].CMDB2_OPEN_USER
CMDB2_VIEWS = configs[APP_ENV].CMDB2_VIEWS

# 删除 资源的 定时任务 调用接口
def delete_res_handler():
    Log.logger.info('----------------delete_res_handler----------------')
    yestoday = datetime.datetime.now() - datetime.timedelta(days = 1)
    resources = ResourceModel.objects.filter(is_deleted=1).filter(deleted_date__lte=yestoday)
    #deploies = Deployment.objects.filter(is_deleted=1).filter(deleted_time__lte=yestoday)
    #Log.logger.info('-----------deploies---------------:%s'%(deploies))
    #Log.logger.info('-----------resources---------------:%s'%(resources))
    with db.app.app_context():
        for resource in resources:
            _delete_res(resource.res_id)
        #for deploy in deploies:
        #    _delete_deploy(deploy.deploy_id)

def _delete_deploy(deploy_id):
    try:
        deploy = Deployment.objects.get(deploy_id=deploy_id)
        if len(deploy):
            env_ = get_CRP_url(deploy.environment)
            crp_url = '%s%s'%(env_, 'api/deploy/deploys')
            disconf_list = deploy.disconf_list
            disconfs = []
            for dis in disconf_list:
                dis_ = dis.to_json()
                disconfs.append(eval(dis_))
            crp_data = {
                "disconf_list" : disconfs,
                "resources_id": '',
                "domain_list":[],
                "resources_id": ''
            }
            res = ResourceModel.objects.get(res_id=deploy.resource_id)
            if res:
                crp_data['resources_id'] = res.res_id
                compute_list = res.compute_list
                domain_list = []
                for compute in compute_list:
                    domain = compute.domain
                    domain_ip = compute.domain_ip
                    domain_list.append({"domain": domain, 'domain_ip': domain_ip})
                    crp_data['domain_list'] = domain_list
                    
            deploy.delete()
            # 调用CRP 删除资源
            crp_data = json.dumps(crp_data)
            requests.delete(crp_url, data=crp_data)
            # 回写CMDB
            #cmdb_url = '%s%s%s'%(CMDB_URL, 'api/repores_delete/', resources.res_id)
            #requests.delete(cmdb_url)
    except Exception as e:
        Log.logger.info('----Scheduler_utuls _delete_deploy  function Exception info is %s'%(e))

def _delete_res(res_id):
    try:
        resources = ResourceModel.objects.get(res_id=res_id)
        if len(resources):
            os_ins_list = resources.os_ins_list
            deploys = Deployment.objects.filter(resource_id=res_id)
            for deploy in deploys:
                env_ = get_CRP_url(deploy.environment)
                crp_url = '%s%s'%(env_, 'api/deploy/deploys')
                disconf_list = deploy.disconf_list
                disconfs = []
                for dis in disconf_list:
                    dis_ = dis.to_json()
                    disconfs.append(eval(dis_))
                crp_data = {
                    "disconf_list" : disconfs,
                    "resources_id": res_id,
                    "domain_list":[],
                }
                compute_list = resources.compute_list
                domain_list = []
                for compute in compute_list:
                    domain = compute.domain
                    domain_ip = compute.domain_ip
                    domain_list.append({"domain": domain, 'domain_ip': domain_ip})
                    crp_data['domain_list'] = domain_list
                crp_data = json.dumps(crp_data)
                requests.delete(crp_url, data=crp_data)
                #deploy.delete()
            # 调用CRP 删除资源
            crp_data = {
                    "resources_id": resources.res_id,
                    "os_inst_id_list": resources.os_ins_list,
                    "vid_list": resources.vid_list,
            }
            env_ = get_CRP_url(resources.env)
            crp_url = '%s%s'%(env_, 'api/resource/deletes')
            crp_data = json.dumps(crp_data)
            requests.delete(crp_url, data=crp_data)
            cmdb_p_code = resources.cmdb_p_code
            resources.delete()
            # 回写CMDB
            cmdb_url = '%s%s%s'%(CMDB_URL, 'cmdb/api/repores_delete/', cmdb_p_code)
            requests.delete(cmdb_url)   
    except Exception as e:
        Log.logger.info('---- Scheduler_utuls  _delete_res  function Exception info is %s'%(e))

# 刷新 虚拟机 状态的 调用接口
def flush_crp_to_cmdb():
    Log.logger.info('----------------flush_crp_to_cmdb job/5min----------------')
    resources = ResourceModel.objects.all()
    env_list = set([])
    osid_status = []
    with db.app.app_context():
        for resource in resources:
            env_list.add(resource.env)
        try:
            for env in env_list:
                if not env:
                    continue
                env_ = get_CRP_url(env)
                crp_url = '%s%s' % (env_, 'api/openstack/nova/states')
                ret = requests.get(crp_url).json()["result"]["vm_info_dict"]
                meta = {k: v[-1] for k,v in ret.items()}
                osid_status.append(meta)
                # Log.logger.info("####meta:{}".format(meta))
            cmdb_url = CMDB_URL + "cmdb/api/vmdocker/status/"
            if osid_status:
                ret = requests.put(cmdb_url, data=json.dumps({"osid_status": osid_status})).json()
                Log.logger.info("flush_crp_to_cmdb result is:{}".format(ret))
            else:
                Log.logger.info("flush_crp_to_cmdb crp->openstack result is null")
        except Exception as exc:
            Log.logger.error("flush_crp_to_cmdb error:{}".format(exc))


def flush_crp_to_cmdb_by_osid(osid, env):
    url = get_CRP_url(env)
    crp_url = '%s%s' % (url, 'api/openstack/nova/state?os_inst_id='+ osid)
    ret = requests.get(crp_url).json()
    Log.logger.info("flush_crp_to_cmdb_by_osid crp result is:{}".format(ret))
    if ret.get('code') == 200:
        status = ret["result"]["vm_state"]
        cmdb_url = CMDB_URL + "cmdb/api/vmdocker/status/"
        ret = requests.put(cmdb_url, data=json.dumps({"osid_status": [{osid: status}]})).json()
        Log.logger.info("flush_crp_to_cmdb_by_osid cmdb result is:{}".format(ret))


# B类视图list，获取已经定义的关系列表
def get_relations():
    '''
    按视图名字查询, id会有变动，保证名字不变就好
    :param view_id:
    :param uid:
    :param token:
    :return:
    '''
    uid, token = get_uid_token()
    for id in [view[0] for num, view in CMDB2_VIEWS.items()]:
        get_one_view(uid, token, id)


@async
def get_one_view(uid, token, view_id):
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
        ret = requests.post(url, data=data_str).json()
        Log.logger.info("get_relations data:{}".format(ret))
        if ret["code"] == 0:
            relations = ret["data"][0]["relation"]  # 获取视图关系实体信息,
            view = ViewCache(view_id=view_id, content=json.dumps(relations))
            view.save()
    except Exception as exc:
        Log.logger.error("graph_data error: {}".format(str(exc)))