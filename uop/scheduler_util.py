# -*- coding: utf-8 -*-

import datetime
import logging
from uop.util import get_CRP_url
from uop.models import ResourceModel, Deployment

# 删除 资源的 定时任务 调用接口
def delete_res_handler():
    logging.info('----------------delete_res_handler----------------')
    yestoday = datetime.datetime.now() - datetime.timedelta(days = 1)
    resources = ResourceModel.objects.filter(is_deleted=1).filter(deleted_date__lte=yestoday)
    deploies = Deployment.objects.filter(is_deleted=1).filter(deleted_time__lte=yestoday)
    logging.info('-----------deploies---------------:%s'%(deploies))
    logging.info('-----------resources---------------:%s'%(resources))
    with app.app_context():
        for resource in resources:
            _delete_res(resource.res_id)
    for deploy in deploies:
        _delete_deploy(deploy.deploy_id)
 
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
            logging.info('wwwwwwwwwwwwwwww')
            # 回写CMDB
            #cmdb_url = '%s%s%s'%(CMDB_URL, 'api/repores_delete/', resources.res_id)
            #requests.delete(cmdb_url)
    except Exception as e:
        logging.info('----Scheduler_utuls _delete_deploy  function Exception info is %s'%(e))

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
                deploy.delete()
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
            logging.info('fffffffffffffffffff')
    except Exception as e:
        logging.info('---- Scheduler_utuls  _delete_res  function Exception info is %s'%(e))

    
