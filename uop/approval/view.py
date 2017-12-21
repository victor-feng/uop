# -*- coding: utf-8 -*-

import json

import uuid
import datetime
import requests
import random
from flask_restful import reqparse, Api, Resource
from uop.log import Log
from uop.approval import approval_blueprint
from uop import models
from uop.approval.errors import approval_errors
from uop.approval.handler import attach_domain_ip
from uop.util import get_CRP_url

approval_api = Api(approval_blueprint, errors=approval_errors)


# CPR_URL = current_app.config['CRP_URL']
# CPR_URL = configs[APP_ENV].CRP_URL


class ApprovalList(Resource):
    def post(self):
        code = 0
        res = ""
        msg = {}
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('resource_id', type=str)
            parser.add_argument('project_id', type=str)
            parser.add_argument('department_id', type=str)
            parser.add_argument('creator_id', type=str)
            args = parser.parse_args()

            approval_id = str(uuid.uuid1())
            resource_id = args.resource_id
            project_id = args.project_id
            department_id = args.department_id
            creator_id = args.creator_id
            create_date = datetime.datetime.now()
            # approve_uid
            # approve_date
            # annotations
            approval_status = "processing"
            models.Approval(approval_id=approval_id, resource_id=resource_id,
                            project_id=project_id, department_id=department_id,
                            creator_id=creator_id, create_date=create_date,
                            approval_status=approval_status).save()

            resource = models.ResourceModel.objects.get(res_id=resource_id)
            resource.approval_status = "processing"
            resource.save()
            code = 200
        except Exception as e:
            Log.logger.exception("[UOP] ApprovalList failed, Exception: %s", e.args)
            code = 500
            res = "Failed to add a approval"

        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }

        return ret, code


class ApprovalInfo(Resource):
    def put(self, res_id):
        code = 0
        res = ""
        msg = {}
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('approve_uid', type=str)
            parser.add_argument('agree', type=bool)
            parser.add_argument('annotations', type=str)
            parser.add_argument('docker_network_id', type=str)
            parser.add_argument('mysql_network_id', type=str)
            parser.add_argument('redis_network_id', type=str)
            parser.add_argument('mongodb_network_id', type=str)
            args = parser.parse_args()

            approval = models.Approval.objects.filter(capacity_status="res").get(resource_id=res_id)
            resource = models.ResourceModel.objects.get(res_id=res_id)
            if approval:
                approval.approve_uid = args.approve_uid
                approval.approve_date = datetime.datetime.now()
                approval.annotations = args.annotations
                docker_network_id = args.docker_network_id
                mysql_network_id = args.mysql_network_id
                redis_network_id = args.redis_network_id
                mongodb_network_id = args.mongodb_network_id
                if args.agree:
                    approval.approval_status = "success"
                    resource.approval_status = "success"
                    approval.annotations=args.annotations
                else:
                    approval.approval_status = "failed"
                    resource.approval_status = "failed"
                    approval.annotations = args.annotations
                approval.save()
                if docker_network_id:
                    resource.docker_network_id = docker_network_id.strip()
                if mysql_network_id:
                    resource.mysql_network_id = mysql_network_id.strip()
                if redis_network_id:
                    resource.redis_network_id = redis_network_id.strip()
                if mongodb_network_id:
                    resource.mongodb_network_id = mongodb_network_id.strip()
                resource.save()
                code = 200
            else:
                code = 410
                res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 500
            res = "Failed to approve the resource."
        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }

        return ret, code

    def get(self, res_id):
        code = 0
        res = ""
        msg = {}
        try:
            approval = models.Approval.filter(capacity_status="res").objects.get(resource_id=res_id)

            if approval:
                msg["creator_id"] = approval.creator_id
                msg["create_date"] = str(approval.create_date)
                status = approval.approval_status
                msg["approval_status"] = status
                if status == "success" or status == "failed":
                    msg["approve_uid"] = approval.approve_uid
                    msg["approve_date"] = str(approval.approve_date)
                    msg["annotations"] = approval.annotations
                code = 200
            else:
                code = 410
                res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 500
        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }

        return ret, code


class Reservation(Resource):
    def post(self):
        code = 0
        res = ""
        msg = {}
        parser = reqparse.RequestParser()
        parser.add_argument('resource_id', type=str)
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()
        resource_id = args.resource_id
        new_computelist = args.compute_list
        try:
            resource = models.ResourceModel.objects.get(res_id=resource_id)
            # if new_computelist:
            #     flag = attach_domain_ip(new_computelist, resource)
            #     if not flag:
            #         res = "some application does not deplay the nginx ip."
            #         code = 500
            #         ret = {
            #             "code": code,
            #             "result": {
            #                 "res": res
            #             }
            #         }
            #         return ret, code
            # resource = models.ResourceModel.objects.get(res_id=resource_id)
            item_info = models.ItemInformation.objects.get(item_name=resource.project)
        except Exception as e:
            Log.logger.error(str(e))
            code = 410
            res = "Failed to find the rsource"
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }
            return ret, code

        data = dict()
        data['set_flag'] = 'res'
        data['unit_id'] = resource.project_id
        data['unit_name'] = resource.project
        data['unit_des'] = ''
        data['user_id'] = resource.user_id
        data['username'] = resource.user_name
        data['department'] = resource.department
        data['created_time'] = str(resource.created_date)
        data['resource_id'] = resource.res_id
        data['resource_name'] = resource.resource_name
        data['domain'] = resource.domain
        data['env'] = resource.env
        data['docker_network_id'] = resource.docker_network_id
        data['mysql_network_id'] = resource.mysql_network_id
        data['redis_network_id'] = resource.redis_network_id
        data['mongodb_network_id'] = resource.mongodb_network_id
        data['cmdb_repo_id'] = item_info.item_id
        resource_list = resource.resource_list
        compute_list = resource.compute_list
        if resource_list:
            res = []
            for db_res in resource_list:
                res.append(
                    {
                        "instance_name": db_res.ins_name,
                        "instance_id": db_res.ins_id,
                        "instance_type": db_res.ins_type,
                        "cpu": db_res.cpu,
                        "mem": db_res.mem,
                        "disk": db_res.disk,
                        "quantity": db_res.quantity,
                        "version": db_res.version,
                        "volume_size": db_res.volume_size

                    }
                )
            data['resource_list'] = res
        if compute_list:
            com = []
            for db_com in compute_list:
                meta = json.dumps(db_com.docker_meta)
                com.append(
                    {
                        "instance_name": db_com.ins_name,
                        "instance_id": db_com.ins_id,
                        "cpu": db_com.cpu,
                        "mem": db_com.mem,
                        "image_url": db_com.url,
                        "quantity": db_com.quantity,
                        "domain": db_com.domain,
                        "port": db_com.port,
                        "domain_ip": db_com.domain_ip,
                        "meta": meta,
                    }
                )
            data['compute_list'] = com

        data_str = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
            CPR_URL = get_CRP_url(data['env'])
            msg = requests.post(CPR_URL + "api/resource/sets", data=data_str, headers=headers)
        except Exception as e:
            res = "failed to connect CRP service."
            code = 500
            ret = {
                "code": code,
                "result": {
                    "res": res
                }
            }
            return ret, code
        if msg.status_code != 202:
            code = msg.status_code
            res = "Failed to reserve resource."
        else:
            resource.reservation_status = "reserving"
            resource.save()
            code = 200
            res = "Success in reserving resource."
        ret = {
            "code": code,
            "result": {
                "res": res
            }
        }
        return ret, code


class ReservationAPI(Resource):
    def put(self, res_id):
        code = 0
        res = ""
        msg = {}
        try:
            resource = models.ResourceModel.objects.get(res_id=res_id)
        except Exception as e:
            code = 410
            res = "Failed to find the rsource"
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }
            return ret, code
        data = dict()
        data['set_flag'] = 'res'
        data['unit_id'] = resource.project_id
        data['unit_name'] = resource.project
        data['unit_des'] = ''
        data['user_id'] = resource.user_id
        data['username'] = resource.user_name
        data['department'] = resource.department
        data['created_time'] = str(resource.created_date)
        data['resource_id'] = resource.res_id
        data['resource_name'] = resource.resource_name
        data['domain'] = resource.domain
        data['env'] = resource.env
        data['docker_network_id'] = resource.docker_network_id
        data['mysql_network_id'] = resource.mysql_network_id
        data['redis_network_id'] = resource.redis_network_id
        data['mongodb_network_id'] = resource.mongodb_network_id
        resource_list = resource.resource_list
        compute_list = resource.compute_list
        if resource_list:
            res = []
            for db_res in resource_list:
                res.append(
                    {
                        "instance_name": db_res.ins_name,
                        "instance_id": db_res.ins_id,
                        "instance_type": db_res.ins_type,
                        "cpu": db_res.cpu,
                        "mem": db_res.mem,
                        "disk": db_res.disk,
                        "quantity": db_res.quantity,
                        "version": db_res.version,
                        "volume_size": db_res.volume_size
                    }
                )
            data['resource_list'] = res
        if compute_list:
            com = []
            for db_com in compute_list:
                meta = json.dumps(db_com.docker_meta)
                com.append(
                    {
                        "instance_name": db_com.ins_name,
                        "instance_id": db_com.ins_id,
                        "cpu": db_com.cpu,
                        "mem": db_com.mem,
                        "image_url": db_com.url,
                        "quantity": db_com.quantity,
                        "port": db_com.port,
                        "meta": meta,
                    }
                )
            data['compute_list'] = com

        data_str = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
            CPR_URL = get_CRP_url(data['env'])
            msg = requests.post(CPR_URL + "api/resource/sets", data=data_str, headers=headers)
        except Exception as e:
            res = "failed to connect CRP service."
            code = 500
            ret = {
                "code": code,
                "result": {
                    "res": res
                }
            }
            return ret, code
        if msg.status_code != 202:
            resource.reservation_status = "unreserved"
            resource.save()
            code = msg.status_code
            res = "Failed to reserve resource."
        else:
            resource.reservation_status = "reserving"
            resource.save()
            code = 200
            res = "Success in reserving resource."
        ret = {
            "code": code,
            "result": {
                "res": res
            }
        }
        return ret, code


class ReservationMock(Resource):
    def post(self):
        code = 0
        res = ""
        msg = {}
        parser = reqparse.RequestParser()
        parser.add_argument('resource_id', type=str)
        args = parser.parse_args()
        resource_id = args.resource_id
        try:
            resource = models.ResourceModel.objects.get(res_id=resource_id)
        except Exception as e:
            code = 410
            res = "Failed to find the rsource"
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }
            return ret, code
        # MOCE
        code = 200
        ret = {
            "code": code,
            "result": {
                "res": res,
                "msg": msg
            }
        }
        return ret, code


class CapacityInfoAPI(Resource):
    def put(self):
        code = 0
        res = ""
        msg = {}
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('approval_id', type=str)
            parser.add_argument('approve_uid', type=str)
            parser.add_argument('agree', type=bool)
            parser.add_argument('annotations', type=str)
            parser.add_argument('docker_network_id', type=str)
            args = parser.parse_args()
            approval_id = args.approval_id
            approval = models.Approval.objects.get(approval_id=approval_id)
            deployment = models.Deployment.objects.get(deploy_id=approval_id)
            # deploy_name=deployment.deploy_name
            if approval:
                approval.approve_uid = args.approve_uid
                approval.approve_date = datetime.datetime.now()
                approval.annotations = args.annotations
                docker_network_id = args.docker_network_id
                resource = models.ResourceModel.objects.get(res_id=approval.resource_id)
                # resource.deploy_name = deploy_name
                if args.agree:
                    approval.approval_status = "%s_success" % (approval.capacity_status)
                    compute_list = resource.compute_list
                    for compute_ in compute_list:
                        capacity_list = compute_.capacity_list
                        for capacity_ in capacity_list:
                            if capacity_.capacity_id == approval_id:
                                capacity_.network_id = docker_network_id.strip()
                    deployment.approve_status = "%s_success" % (approval.capacity_status)
                    deployment.approve_suggestion = args.annotations
                    if approval.capacity_status == "increase":
                        deployment.deploy_result = "increasing"
                    elif approval.capacity_status == "reduce":
                        deployment.deploy_result = "reducing"
                    # 管理员审批通过后修改resource表deploy_name,更新当前版本
                    deploy_name = deployment.deploy_name
                    resource = models.ResourceModel.objects.get(res_id=approval.resource_id)
                    resource.deploy_name = deploy_name
                    resource.save()
                else:
                    approval.approval_status = "%s_failed" % (approval.capacity_status)
                    deployment.approve_status = "%s_failed" % (approval.capacity_status)
                    deployment.approve_suggestion = args.annotations
                    if approval.capacity_status == "increase":
                        deployment.deploy_result = "not_increased"
                    elif approval.capacity_status == "reduce":
                        deployment.deploy_result = "not_reduced"
                approval.save()
                deployment.save()
                code = 200
            else:
                code = 410
                res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 500
            res = "Failed to approve the resource."
        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }

        return ret, code


class CapacityReservation(Resource):
    def post(self):
        code = 0
        res = ""
        msg = {}
        parser = reqparse.RequestParser()
        parser.add_argument('resource_id', type=str)
        parser.add_argument('approval_id', type=str)
        parser.add_argument('compute_list', type=list, location='json')
        args = parser.parse_args()
        resource_id = args.resource_id
        approval_id = args.approval_id
        try:
            resource = models.ResourceModel.objects.get(res_id=resource_id)
            item_info = models.ItemInformation.objects.get(item_name=resource.project)
        except Exception as e:
            Log.logger.error(str(e))
            code = 410
            res = "Failed to find the rsource"
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }
            return ret, code

        data = dict()
        data['set_flag'] = 'increase'
        data['unit_id'] = resource.project_id
        # data['network_id'] = resource.network_id.strip()
        data['unit_name'] = resource.project
        data['unit_des'] = ''
        data['user_id'] = resource.user_id
        data['username'] = resource.user_name
        data['department'] = resource.department
        data['created_time'] = str(resource.created_date)
        data['resource_id'] = resource.res_id
        data['resource_name'] = resource.resource_name
        data['domain'] = resource.domain
        data['env'] = resource.env
        data['docker_network_id'] = resource.docker_network_id
        data['mysql_network_id'] = resource.mysql_network_id
        data['redis_network_id'] = resource.redis_network_id
        data['mongodb_network_id'] = resource.mongodb_network_id
        data['cmdb_repo_id'] = item_info.item_id
        resource_list = resource.resource_list
        compute_list = resource.compute_list
        number = 0
        if resource_list:
            res = []
            for db_res in resource_list:
                res.append(
                    {
                        "instance_name": db_res.ins_name,
                        "instance_id": db_res.ins_id,
                        "instance_type": db_res.ins_type,
                        "cpu": db_res.cpu,
                        "mem": db_res.mem,
                        "disk": db_res.disk,
                        "quantity": 0,
                        "version": db_res.version,
                        "volume_size": db_res.volume_size
                    }
                )
            data['resource_list'] = res
        ips = []
        if compute_list:
            com = []
            for db_com in compute_list:
                # for i in range(0, db_com.quantity):
                meta = json.dumps(db_com.docker_meta) if db_com.docker_meta else ""
                capacity_list = db_com.capacity_list
                for capacity_ in capacity_list:
                    if capacity_.capacity_id == approval_id:
                        number = abs(capacity_.begin_number - capacity_.end_number)
                        com.append(
                            {
                                "instance_name": db_com.ins_name,
                                "instance_id": db_com.ins_id,
                                "cpu": db_com.cpu,
                                "mem": db_com.mem,
                                "image_url": db_com.url,
                                "quantity": number,
                                "domain": db_com.domain,
                                "port": db_com.port,
                                "domain_ip": db_com.domain_ip,
                                "meta": meta,
                            })
                        ips.extend([ip for ip in db_com.ips])

            data['compute_list'] = com

        data_str = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
            approval = models.Approval.objects.get(approval_id=approval_id)
            if approval.capacity_status == 'increase':
                CPR_URL = get_CRP_url(data['env'])
                msg = requests.post(CPR_URL + "api/resource/sets", data=data_str, headers=headers)
            elif approval.capacity_status == 'reduce':
                reduce_list = []
                for os_ins in resource.os_ins_ip_list:
                    if os_ins.ip in ips:
                        reduce_list.append(os_ins)
                reduce_list = random.sample(reduce_list, number)
                os_inst_id_list = []
                reduce_list = [eval(reduce_.to_json()) for reduce_ in reduce_list]
                for os_ip_dict in reduce_list:
                    os_inst_id = os_ip_dict["os_ins_id"]
                    os_inst_id_list.append(os_inst_id)
                crp_data = {
                    "resources_id": resource.res_id,
                    "os_ins_ip_list": reduce_list,
                    "vid_list": [],
                    "set_flag": 'reduce'
                }
                env_ = get_CRP_url(resource.env)
                crp_url = '%s%s' % (env_, 'api/resource/deletes')
                crp_data = json.dumps(crp_data)
                msg = requests.delete(crp_url, data=crp_data)
        except Exception as e:
            res = "failed to connect CRP service."
            code = 500
            ret = {
                "code": code,
                "result": {
                    "res": res
                }
            }
            return ret, code
        if msg.status_code != 202:
            code = msg.status_code
            res = "Failed to reserve resource."
        else:
            resource.reservation_status = "reserving"
            resource.save()
            code = 200
            res = "Success in reserving resource."
        ret = {
            "code": code,
            "result": {
                "res": res
            }
        }
        return ret, code


class RollBackInfoAPI(Resource):
    # 审批过后更新审批表的信息
    def put(self):
        code = 0
        res = ""
        msg = {}
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('deploy_id', type=str)
            parser.add_argument('approve_uid', type=str)
            parser.add_argument('agree', type=bool)
            parser.add_argument('annotations', type=str)
            args = parser.parse_args()
            deploy_id = args.deploy_id
            approvals = models.Approval.objects.filter(approval_id=deploy_id).order_by('-create_date')
            deployment = models.Deployment.objects.get(deploy_id=deploy_id)
            if approvals:
                approval = approvals[0]
                approval.approve_uid = args.approve_uid
                approval.approve_date = datetime.datetime.now()
                approval.annotations = args.annotations
                if args.agree:
                    approval.approval_status = "rollback_success"
                    deployment.approve_status = "rollback_success"
                    # 审批通过状态改为回滚中
                    deployment.deploy_result = "rollbacking"
                    deployment.approve_suggestion = args.annotations
                    # 管理员审批通过后修改resource表deploy_name,更新当前版本
                    deploy_name = deployment.deploy_name
                    resource = models.ResourceModel.objects.get(res_id=approval.resource_id)
                    resource.deploy_name = deploy_name
                    resource.save()
                else:
                    approval.approval_status = "rollback_fail"
                    deployment.approve_status = "rollback_fail"
                    # 审批不通过状态修改
                    deployment.deploy_result = "not_rollbacked"
                    deployment.approve_suggestion = args.annotations
                    # 管理员审批不通过时修改回滚时的当前版本为审批不通过的版本
                    # deps = models.Deployment.objects.filter(resource_id=approval.resource_id,approve_status__in=["success","rollback_success","reduce_success","increase_success"]).order_by('-created_time')
                    # if deps:
                    #    dep = deps[0]
                    # deploy_name = dep.deploy_name
                    # resource = models.ResourceModel.objects.get(res_id=approval.resource_id)
                    # resource.deploy_name = deploy_name
                    # resource.save()
                approval.save()
                deployment.save()
                code = 200
            else:
                code = 410
                res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 500
            res = "Failed to approve the rollback %s." % e
        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }

        return ret, code


class RollBackReservation(Resource):
    # 获取回滚的详情
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('deploy_id', type=str, location='args')
        args = parser.parse_args()
        deploy_id = args.deploy_id
        try:
            results = {}
            deployment = models.Deployment.objects.get(deploy_id=deploy_id)
            resource_id = deployment.resource_id
            resource = models.ResourceModel.objects.get(res_id=resource_id)
            deploy_name = deployment.deploy_name
            deploy_name=deploy_name.strip().split('@')[0]
            resource_id = deployment.resource_id
            resource_name = deployment.resource_name
            project_id = deployment.project_id
            project_name = deployment.project_name
            environment = deployment.environment
            release_notes = deployment.release_notes
            app_image = eval(deployment.app_image)
            approve_suggestion = deployment.approve_suggestion
            compute_list = resource.compute_list
            for compute in compute_list:
                for app in app_image:
                    if app["ins_id"] == compute["ins_id"]:
                        app["ips"] = compute["ips"]
                        app["domain_ip"] = compute["domain_ip"]
                        app["quantity"] = compute["quantity"]
            results["resource_id"] = resource_id
            results["deploy_name"] = deploy_name
            results["resource_name"] = resource_name
            results["project_id"] = project_id
            results["project_name"] = project_name
            results["environment"] = environment
            results["release_notes"] = release_notes
            results["compute_list"] = app_image
            results["approve_suggestion"] = approve_suggestion
        except Exception as e:
            res = {
                "code": 400,
                "result": {
                    "res": "failed",
                    "msg": e.args
                }
            }
            return res, 400
        else:
            return results, 200

    # 将回滚的数据发送到crp
    def post(self):
        code = 200
        res = ""
        msg = {}
        parser = reqparse.RequestParser()
        parser.add_argument('resource_id', type=str)
        parser.add_argument('deploy_id', type=str)
        parser.add_argument('compute_list', type=list, location='json')
        parser.add_argument('deploy_name', type=str)
        args = parser.parse_args()
        resource_id = args.resource_id
        deploy_id = args.deploy_id
        deploy_name = args.deploy_name
        compute_list = args.compute_list
        data = {}
        try:
            resource = models.ResourceModel.objects.get(res_id=resource_id)
            resource.deploy_name = deploy_name
            env = resource.env
            res_compute_list = resource.compute_list
            for res_compute in res_compute_list:
                for compute in compute_list:
                    if res_compute["ins_id"] == compute["ins_id"]:
                        res_compute["url"] = compute["url"]
                        res_compute["port"] = compute["port"]
                        res_compute["domain"] = compute["domain"]
            resource.save()
            # ----------
            appinfo = []
            docker_list = []
            for compute in compute_list:
                domain_ip = compute.get('domain_ip')
                if domain_ip:
                    appinfo.append(compute)
                docker_list.append(
                    {
                        'url': compute.get("url"),
                        'ins_name': compute.get("ins_name"),
                        'ip': compute.get("ips"),
                    }
                )
            data["appinfo"] = appinfo
            data['docker'] = docker_list
            data["mysql"] = []
            data["mongodb"] = []
            data["dns"] = []
            data["disconf_server_info"] = []
            data["deploy_id"] = deploy_id
            data["deploy_type"] = "rollback"
            CPR_URL = get_CRP_url(env)
            url = CPR_URL + "api/deploy/deploys"
            headers = {
                'Content-Type': 'application/json',
            }
            data_str = json.dumps(data)
            Log.logger.debug("Data args is " + str(data))
            result = requests.post(url=url, headers=headers, data=data_str)
            Log.logger.debug("Result is " + str(result))
        except Exception as e:
            code = 500
            res = "Failed the rollback post data to crp. %s" % e
        finally:
            ret = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": msg
                }
            }
        return ret, code


approval_api.add_resource(ApprovalList, '/approvals')
approval_api.add_resource(ApprovalInfo, '/approvals/<string:res_id>')
approval_api.add_resource(Reservation, '/reservation')
approval_api.add_resource(ReservationAPI, '/reservation/<string:res_id>')
# approval_api.add_resource(ReservationMock, '/reservation')
approval_api.add_resource(CapacityInfoAPI, '/capacity/approvals')
approval_api.add_resource(CapacityReservation, '/capacity/reservation')
approval_api.add_resource(RollBackInfoAPI, '/rollback/approvals')
approval_api.add_resource(RollBackReservation, '/rollback/reservation')
