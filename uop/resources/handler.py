# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
import copy
import time
import random
import datetime
from uop.log import Log
from uop.util import async, response_data
from config import APP_ENV, configs
from uop.models import ResourceModel, Statusvm,OS_ip_dic,Deployment
from uop.item_info.handler import delete_instance, get_uid_token
from flask import jsonify
import  xlsxwriter
import uuid
import sys,os
from uop.util import get_CRP_url

reload(sys)
sys.setdefaultencoding('utf-8')

CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB2_URL = configs[APP_ENV].CMDB2_URL
CRP_URL = configs[APP_ENV].CRP_URL
UPLOAD_FOLDER=configs[APP_ENV].UPLOAD_FOLDER
ENTITY  = configs[APP_ENV].CMDB2_ENTITY

__all__ = [
    "make_random_database_password", "_match_condition_generator",
]

status_dict={
    "active":u"运行中",
    "error":u"错误",
    "shutoff":u"关机",
    "failed":u"虚机不存在",
    "rebuild":u"部署中",
    '':u'',
    "ok":u"运行中",
}

field_dict={
    "resource_type":u"实例类型",
	"resource_name":u"资源名称",
	"env":u"所属环境",
	"project_name":u"所属工程",
    "module_name":u"所属模块",
    "business_name":u"所属业务",
    "domain":u"域名",
	"create_date":u"创建日期",
    "update_time":u"修改日期",
	"resource_ip":u"IP",
    "ip":u"IP",
	"resource_config":u"配置",
	"resource_status":u"状态",
}

class ExcelException(object):
    pass


def make_random_database_password():
    return str(random.randint(100000, 999999)) + chr(random.randint(65, 90)) + chr(
        random.randint(97, 122)) + '!'


def _match_condition_generator(args):
    match = dict()
    if args.user_id or args.resource_name or args.project or args.formStatus or args.approval_status\
            or (args.start_time and args.end_time):
        match_cond = dict()
        match_dict = dict()
        match_list = []
        if args.user_id:
            match_cond['user_id'] = args.user_id
        if args.resource_name:
            match_cond['resource_name'] = args.resource_name
        if args.project:
            match_cond['project'] = args.project
        if args.formStatus:
            match_cond['application_status'] = args.formStatus
        if args.approval_status:
            match_cond['approval_status'] = args.approval_status
        if args.department:
            match_cond["department"]=args.department
        if args.project_name:
            match_cond["project_name"] = args.project_name
        if args.module_name:
            match_cond["module_name"] = args.module_name
        if args.start_time and args.end_time:
            created_date_dict = dict()
            created_date_dict['$gte'] = datetime.datetime.strptime(args.start_time, "%Y-%m-%d %H:%M:%S")
            created_date_dict['$lte'] = datetime.datetime.strptime(args.end_time, "%Y-%m-%d %H:%M:%S")
            match_cond['created_date'] = created_date_dict
        match_list.append(match_cond)
        match_dict['$and'] = match_list
        match['$match'] = match_dict
    return match


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


def get_from_cmdb2(args, filters, download=False):
    url = CMDB2_URL + "cmdb/openapi/resourcs/list/"
    response = {
        "code": 2002,
        "result": {
            "msg": "success",
            "res": {
                "current_page": filters["page_num"],
                "object_list": [],
                "total_page": 0
            }
        }
    }
    Log.logger.info("download:{}".format(download))
    try:
        Log.logger.info("args:{}".format( args))
        ret = requests.post(url, data=json.dumps(args), timeout=5).json()
        if ret["code"] != 0:
            response["code"] = ret["code"]
            response["result"]["msg"] = ret["msg"]
        Log.logger.info(u"ret：{}".format(ret))
        resources = ResourceModel.objects.filter(department=filters["dep"], env=filters["env"],is_deleted=0)
        cmdb2_resource_id_list = []
        for res in resources:
            for id in res.cmdb2_resource_id:
                cmdb2_resource_id_list.append(str(id))
        data = [r for r in ret["data"] if str(r.get("id")) in cmdb2_resource_id_list] if filters["dep"] != "admin" else ret["data"]
        if download:
            # Log.logger.error("parse_data_uop:{}".format(data))
            return parse_data_uop(data, filters)
        else:
            Log.logger.error("download:{}".format(download))
            object_list, total_page = pageinit(data, int(filters["page_num"]), int(filters["page_count"]))
            response["result"]["res"]["object_list"] = [{k.lower(): v for k, v in ol.items()} for ol in object_list]
            response["result"]["res"]["total_page"] = total_page
            return jsonify(response)
    except Exception as exc:
        response["code"] = 500
        response["result"]["msg"] = str(exc)
        Log.logger.info("get_from_cmdb2 error:{}".format(str(exc)))
        return  [] if download else jsonify(response)


def update_statusvm(vm):
    res_id = vm.resource_id
    vms = Statusvm.objects.filter(resource_id=res_id)
    old_osid_list = []
    if vms:
        old_osid_list = [v.osid for v in vms]
    try:
        res = ResourceModel.objects.get(res_id = res_id)
    except Exception as exc:
        return vm.osid, vm.ip

    flag = [i for i in res.os_ins_ip_list if i.os_ins_id == vm.osid]
    new_osip = [i for i in res.os_ins_ip_list if i.os_ins_id not in  old_osid_list]
    if not flag: # 重启变了osid
        try:
            no = new_osip.pop()
            vm.osid, vm.ip = no.os_ins_id, no.ip
            vm.save()
            return no.os_ins_id, no.ip
        except Exception as exc:
            Log.logger.error("update_statusvm error:{}".format(exc))
            return vm.osid, vm.ip
    else:
        return vm.osid, vm.ip


def get_from_uop(args):
    domain, resource_type, resource_name, module_name,business_name, project_name, start_time, end_time, status, page_num, page_count, env, user_id, department, ip = \
        args.domain, args.resource_type, args.resource_name, args.module_name,args.business_name,args.project_name, args.start_time, args.end_time,args.resource_status, args.page_num, args.page_count, args.env, args.user_id, args.department, args.ip
    query, result_list = {}, []

    try:
        attach_key = lambda v, query, key, filter: query.update({key: v}) if filter else ""

        attach_key(department, query, "department", str(department) != "admin")
        attach_key(user_id, query, "user_id", user_id and user_id != "admin")
        attach_key(env, query, "env", env)
        attach_key(resource_name.decode(encoding="utf-8") if resource_name else "", query, "resource_name__icontains", resource_name)
        attach_key(domain.decode(encoding="utf-8") if domain else "", query, "domain__icontains", domain)
        attach_key(business_name.decode(encoding="utf-8") if business_name else "", query, "business_name__icontains", business_name)
        attach_key(module_name.decode(encoding="utf-8") if module_name else "", query, "module_name__icontains", module_name)
        attach_key(project_name.decode(encoding="utf-8") if project_name else "", query, "project_name__icontains", project_name)
        attach_key(status, query, "status", status)
        attach_key(ip, query, "ip", ip)
        if resource_type in ["mysqlandmongo", "cache"]:
            if resource_type == "mysqlandmongo":
                query['os_type__in'] = ["mysql", "mongodb"]
            else:
                query['os_type'] = "redis"
        else:
            if resource_type:
                query['os_type'] = str(resource_type)
        if start_time:
            start_time = datetime.datetime.strptime(str(start_time), "%Y-%m-%dT%H:%M:%S.000Z")
            query["create_time__gte"] = start_time
        if end_time:
            end_time = datetime.datetime.strptime(str(end_time), "%Y-%m-%dT%H:%M:%S.000Z")
            query["create_time__lte"] = end_time
        Log.logger.info("query:{}".format(query))
        total_count = Statusvm.objects.filter(**query).count()
        if page_num and page_count:
            skip_count = (int(page_num) - 1) * int(page_count)
            resources = Statusvm.objects.filter(**query).order_by('-create_time').skip(skip_count).limit(int(page_count))
        else:
            resources = Statusvm.objects.filter(**query).order_by('-create_time')
        def get_cloud(res_id, flag=False):
            res = ResourceModel.objects.filter(res_id=res_id,is_deleted=0)
            # Log.logger.info("res:{}".format(res))
            if res:
                if not flag:
                    for r in res:
                        return r.cloud if r.cloud else "1"
                else:
                    for r in res:
                        if isinstance(r.compute_list, int):
                            return False
                        for app in r.compute_list:
                            return app.domain, app.domain_ip,app.namespace,app.domain_path
                    return False
            return False if flag else "1"

        # Log.logger.info("resources:{}".format(resources))
        for pi in resources:
            tmp_result = {}
            tmp_result['resource_ip'] = pi.ip
            tmp_result['osid'] = pi.osid
            domain, domain_ip,namespace,domain_path = get_cloud(pi.resource_id, True) if get_cloud(pi.resource_id, True) else (pi.domain, pi.domain_ip,None,None)
            if domain_path and "/" not in domain:
                domain = domain + "/" + domain_path
            tmp_result['domain'] = domain
            tmp_result['domain_ip'] = domain_ip
            tmp_result['namespace'] = namespace
            tmp_result['resource_type'] = pi.os_type
            tmp_result['resource_config'] = [
                {'name': 'CPU', 'value': str(pi.cpu) + u'核'},
                {'name': u'内存', 'value': str(pi.mem) + 'GB'},
            ]
            tmp_result['create_date'] = datetime.datetime.strftime(pi.create_time, '%Y-%m-%d %H:%M:%S')
            tmp_result['update_time'] = datetime.datetime.strftime(pi.update_time, '%Y-%m-%d %H:%M:%S')
            tmp_result['resource_name'] = pi.resource_name
            tmp_result['business_name'] = pi.business_name
            tmp_result['module_name'] = pi.module_name
            tmp_result['project_name'] = pi.project_name
            tmp_result['resource_status'] = pi.status
            tmp_result['view_id'] = pi.resource_view_id
            tmp_result['view_num'] = pi.view_num
            tmp_result['resource_id'] = pi.resource_id
            tmp_result['env'] = pi.env
            tmp_result['cloud'] = pi.cloud if pi.cloud else get_cloud(pi.resource_id)
            tmp_result['volume_size'] = pi.volume_size
            tmp_result['namespace'] = pi.namespace
            tmp_result['wvip'] = pi.wvip
            tmp_result['rvip'] = pi.rvip
            tmp_result['vip'] = pi.vip
            # osid, ip = update_statusvm(pi)
            # tmp_result['osid'] = osid
            # tmp_result['resource_ip'] = ip
            result_list.append(tmp_result)
        # Log.logger.info("result_list:{}".format(result_list))
        # if page_num and page_count:
        #     page_info, total_page = pageinit(result_list, int(page_num), int(page_count))
        # else:
        #     page_info = result_list
        # total_page = len(result_list)
        content = {
            "total_count": total_count,
            "object_list": result_list,
            "current_page": page_num
        }
        res = response_data(200, "success", content)
    except Exception as exc:
        code = 500
        Log.logger.error("Statusflush error:{}".format(str(exc)))
        res = response_data(code, str(exc), "")
    return res


@async
def delete_uop(res_id):
    Log.logger.info("Start delete statusvm res id is {}".format(res_id))
    res = Statusvm.objects.filter(resource_id=res_id)
    try:
        if res:
            for r in res:
                r.delete()
    except Exception as exc:
        Log.logger.error("Delete resource error:{}".format(str(exc)))


def parse_data_uop(data, filters):
    data = [dict({k.lower(): v for k, v in ol.items()},**filters) for ol in data]
    return data


def to_unicode(value):
    try:
        """将字符转为 unicode 编码
        @param {string} value 将要被转码的值
        @return {unicode} 返回转成 unicode 的字符串
        """
        if value == None:
            return None
        if isinstance(value, unicode):
            return value
        # 字符串类型,需要按它原本的编码来解码出 unicode,编码不对会报异常
        if isinstance(value, str):
            for encoding in ("utf-8", "gbk", "cp936", sys.getdefaultencoding(), "gb2312", "gb18030", "big5", "latin-1", "ascii"):
                try:
                    value = value.decode(encoding)
                    break # 如果上面这句执行没错，说明是这种编码
                except:
                    pass
        # 其它类型
        return value
    except Exception,e:
        err_msg='execute to_unicode error: %s' % str(e)
        Log.logger.error("to_unicode:{}".format(str(e)))
        raise ExcelException(err_msg)


def deal_myresource_to_excel(data, field_list):
    try:
        excel_name="myresource_" + str(uuid.uuid1()) +'.xlsx'
        download_dir = os.path.join(UPLOAD_FOLDER, 'excel')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        excel = "%s/%s" % (download_dir,excel_name)
        workbook = xlsxwriter.Workbook(excel)
        worksheetResource = workbook.add_worksheet(u'我的资源')
        worksheetResource.set_column(0, 31, 18)
        head = workbook.add_format(
            {'border': 1, 'align': 'center', 'bg_color': '6699ff', 'font_size': 10, 'font_name': u'微软雅黑', 'bold': True,
             'text_wrap': True, 'valign': 'vcenter'})
        body = workbook.add_format({'border': 1, 'align': 'center', 'font_size': 10, 'font_name': u'微软雅黑'})
        head_cols=[]
        # Log.logger.info("deal_myresource_to_excel:{}".format(data))
        if len(field_list) == 0:
            field_list=["resource_type","resource_name","business_name","env","project_name","create_date","resource_ip","resource_config","resource_status","update_time","domain","module_name"]
        for field in field_list:
            head_cols.append(field_dict.get(field))
        res_list=deal_data(data, field_list)
        # Log.logger.error("res_list:{}".format(res_list))
        for i in range(0,len(head_cols)):
            h_col = to_unicode(head_cols[i])
            worksheetResource.write(0,i,h_col,head)
        for j in range(0,len(res_list)):
            for i in range(0,len(head_cols)):
                res=to_unicode(res_list[j][i])
                worksheetResource.write(1 + j, i, res, body)
        workbook.close()
        return "success",excel_name
    except Exception as e:
        err_msg= "deal my resource to excel error: %s" % str(e)
        Log.logger.error("deal_myresource_to_excel:{}".format(str(e)))
        return  err_msg,excel_name


def deal_data(data,field_list):
    res_list=[]
    Log.logger.info("deal_data:{}".format(data))
    try:
        for d in data:
            res=[]
            for field in field_list:
                if field == 'resource_config':
                    resource_config = d.get('resource_config') if d.get('resource_config') else [
                                    {
                                        "name": "CPU",
                                        "value": ""
                                    },
                                    {
                                        "name": "\u5185\u5b58",
                                        "value": ""
                                    }
                                ]
                    cpu_name=resource_config[0].get('name')
                    cpu_value = resource_config[0].get('value').split('\\')[0] + u'核'
                    mem_name = "内存"
                    mem_value = resource_config[1].get('value')
                    config="%s:%s %s:%s"% (cpu_name,cpu_value,mem_name,mem_value)
                    res.append(config)
                elif field == "resource_status":
                    status = status_dict[d.get('resource_status', '')]
                    res.append(status)
                else:
                    field_data = d.get(field,'')
                    res.append(field_data)
            res_list.append(res)
        return res_list
    except Exception as e:
        err_msg= "deal my resource data error: %s" % str(e)
        Log.logger.error("deal_data:{}".format(str(e)))
        raise ExcelException(err_msg)

@async
def delete_cmdb1(code):
    if CMDB_URL:
        cmdb_url = '%s%s%s' % (CMDB_URL, 'cmdb/api/repores_delete/', code)
        requests.delete(cmdb_url)


@async
def delete_cmdb2(res_id):
    resource = ResourceModel.objects.filter(res_id=res_id,is_deleted=0)
    instance_list = []
    if resource:
        null = [instance_list.extend(res.cmdb2_resource_id) for res in resource if res.cmdb2_resource_id]
    class args(object):
        delete_list = instance_list
    ret = delete_instance(args)
    Log.logger.info("testdeltecmdb:{}".format(ret))


def get_counts():
    url = CMDB2_URL + "cmdb/openapi/entity/statistic/"
    uid, token = get_uid_token()
    data ={
            "uid": uid,
            "token": token,
            "sign": "",
            "data": [{
                "id": id,
                "parameters": [{
                    "code": "",
                    "condition": "",
                    "value": ""
                }]
            }for id in ENTITY.values()]
    }

    try:
        Log.logger.info("get_counts from CMDB2 data:{}".format(data))
        ret = requests.post(url, data=json.dumps(data), timeout=5).json()
        if ret["code"] == 0:
            Log.logger.info("get_counts from CMDB2 ret:{}".format(ret))
            dd = [dict(ins, entity=[k for k, v in ENTITY.items() if v == str(ins["id"])][0])
                  for ins in ret["result"]["data"]]
        else:
            dd = ret
        #获取部署数据库和应用数量
        res_list,msg=get_deploy_counts()
        if not msg :
            dd.extend(res_list)
            response = response_data(200, "success", dd)
        else:
            response = response_data(500, "fail", msg)
    except Exception as exc:
        Log.logger.error("UOP get counts error:{}".format(exc))
        response = response_data(500, "fail", exc)
    return response

def get_deploy_counts():
    res_list = []
    msg = None
    try:
        type_mapping={
            "app" : ["app", "kvm"],
            "database" : ["mysql", "redis","mongodb"],
        }
        for type in type_mapping:
            data = {}
            count = ResourceModel.objects.filter(approval_status="success",resource_type__in=type_mapping[type],is_deleted=0).count()
            data["count"] = count
            data["entity"] = type
            data["id"] = ""
            res_list.append(data)
    except Exception as e:
        msg = str(e)
    return res_list,msg
@async
def updata_deployment_info(resource_name,env,url):
    try:
        for i in range(6):
            time.sleep(10)
            info_url = "{}api/openstack/k8s/deploymentpod?deployment_name={}".format(url, resource_name)
            ret = requests.get(info_url)
            response = ret.json()
            res_list = response["result"]["data"]["res_list"]
            Log.logger.info("##Deployment info is {}".format(res_list))
            if response.get('code') == 200:
                resource = ResourceModel.objects.get(resource_name=resource_name, env=env)
                os_ins_ip_list = resource.os_ins_ip_list
                compute_list = resource.compute_list
                os_ins_list = []
                ips=[]
                osid_ip = [(res.get("pod_name"), res.get("pod_ip"),res.get("status"),res.get("node_name"))for res in res_list]
                vmid_ip = osid_ip
                for os_ins in os_ins_ip_list:
                    cpu = getattr(os_ins, "cpu")
                    mem = getattr(os_ins, "mem")
                    if osid_ip:
                        one = osid_ip.pop()
                        os_ins_list.append(OS_ip_dic(
                                ip=one[1],
                                os_ins_id=one[0],
                                os_type="docker",
                                cpu=cpu,
                                mem=mem,
                                instance_id=os_ins.instance_id if getattr(os_ins, "instance_id") else "",
                                physical_server=one[3])
                        )
                for compute in compute_list:
                    compute.ips = ips
                    compute.save()
                resource.os_ins_ip_list = os_ins_list
                resource.save()
                #更新Statusvm表数据
                vms = Statusvm.objects.filter(resource_name=resource_name)
                for vm in vms:
                    if vmid_ip:
                        one = vmid_ip.pop()
                        vm.update(status=one[2], osid=one[0], ip=one[1],physical_server=one[3])
    except Exception as e:
        err_msg = "Update deployment info to resource error {e}".format(e=str(e))
        Log.logger.error(err_msg)

def delete_resource_deploy(res_id):
    domain = None
    os_inst_ip_list = []
    try:
        resources_obj = ResourceModel.objects.filter(res_id=res_id)
        if len(resources_obj):
            resources=resources_obj[0]
            resource_type=resources.resource_type
            cloud = resources.cloud
            deploys = Deployment.objects.filter(resource_id=res_id).order_by("-created_time")
            for deploy in deploys:
                environment = deploy.environment
                env_ = get_CRP_url(environment)
                crp_url = '%s%s' % (env_, 'api/deploy/deploys')
                disconf_list = deploy.disconf_list
                disconfs = []
                for dis in disconf_list:
                    dis_ = dis.to_json()
                    disconfs.append(eval(dis_))
                crp_data = {
                    "disconf_list": disconfs,
                    "resource_id": res_id,
                    "domain_list": [],
                    "set_flag": 'res',
                    "environment":environment,
                }
                compute_list = resources.compute_list
                domain_list = []
                for compute in compute_list:
                    domain = compute.domain
                    domain_ip = compute.domain_ip
                    domain_list.append({"domain": domain, 'domain_ip': domain_ip})
                d_count = ResourceModel.objects.filter(domain=domain, is_deleted=0).count()
                if d_count <= 1:
                    crp_data['domain_list'] = domain_list
                crp_data = json.dumps(crp_data)
                requests.delete(crp_url, data=crp_data)
                # deploy.delete()
            # 调用CRP 删除资源
            namespace = None
            compute_list = resources.compute_list
            for compute in compute_list:
                namespace = compute.namespace
            os_ins_ip_list = resources.os_ins_ip_list
            for os_ip in os_ins_ip_list:
                os_ip_dict = {}
                os_ip_dict["os_ins_id"] = os_ip["os_ins_id"]
                os_ip_dict["os_vol_id"] = os_ip["os_vol_id"]
                os_inst_ip_list.append(os_ip_dict)
            crp_data = {
                "resource_id": resources.res_id,
                "resource_name": resources.resource_name,
                "resource_type": resource_type,
                "cloud": cloud,
                "os_ins_ip_list": os_inst_ip_list,
                "vid_list": resources.vid_list,
                "set_flag": 'res',
                'syswin_project': 'uop',
                'namespace': namespace,
            }
            env_ = get_CRP_url(resources.env)
            crp_url = '%s%s' % (env_, 'api/resource/deletes')
            crp_data = json.dumps(crp_data)
            requests.delete(crp_url, data=crp_data)
            reservation_status = resources.reservation_status
            #如果预留失败的直接删除数据库的记录
            if reservation_status in ["set_fail","unreserved","approval_fail","revoke","reserving"]:
                if reservation_status == "reserving" and cloud == "2" and resource_type == "app":
                    resources.reservation_status = "deleting"
                    resources.save()
                else:
                    resources.update(is_deleted=1,deleted_date=datetime.datetime.now(),reservation_status="delete_success")
            else:
                resources.reservation_status = "deleting"
                resources.save()
                if deploys:
                    dep=deploys[0]
                    dep.deploy_result = "deleting"
                    dep.save()
            #cmdb_p_code = resources.cmdb_p_code
            #resources.is_deleted = 1
            #resources.deleted_date = datetime.datetime.now()
            #resources.save()
            # 回写CMDB
            #delete_cmdb1(cmdb_p_code)
            #delete_uop(res_id)
            #delete_cmdb2(res_id)
        else:
            ret = {
                'code': 200,
                'result': {
                    'res': 'success',
                    'msg': 'Resource not found.'
                }
            }
            return ret, 200
    except Exception as e:
        Log.logger.error(str(e))
        ret = {
            'code': 500,
            'result': {
                'res': 'fail',
                'msg': 'Delete resource application failed.'
            }
        }
        return ret, 500
    ret = {
        'code': 200,
        'result': {
            'res': 'success',
            'msg': 'Delete resource application success.'
        }
    }
    return ret, 200