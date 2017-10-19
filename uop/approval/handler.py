# -*- coding: utf-8 -*-

import json
import uuid
import datetime
import logging

import requests
from flask_restful import reqparse, Api, Resource
from flask import current_app

from uop.approval import approval_blueprint
from uop import models
from uop.approval.errors import approval_errors
# from config import APP_ENV
from uop.util import get_CRP_url, check_network_use

approval_api = Api(approval_blueprint, errors=approval_errors)

#CPR_URL = current_app.config['CRP_URL']
#CPR_URL = configs[APP_ENV].CRP_URL


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
                            project_id=project_id,department_id=department_id,
                            creator_id=creator_id,create_date=create_date,
                            approval_status=approval_status).save()

            resource = models.ResourceModel.objects.get(res_id=resource_id)
            resource.approval_status = "processing"
            resource.save()
            code = 200
        except Exception as e:
            logging.exception("[UOP] ApprovalList failed, Exception: %s", e.args)
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
            args = parser.parse_args()

            approval = models.Approval.objects.get(resource_id=res_id)
            resource = models.ResourceModel.objects.get(res_id=res_id)
            if approval:
                approval.approve_uid = args.approve_uid
                approval.approve_date = datetime.datetime.now()
                approval.annotations = args.annotations
                if args.agree:
                    approval.approval_status = "success"
                    resource.approval_status = "success"
                else:
                    approval.approval_status = "failed"
                    resource.approval_status = "failed"
                approval.save()
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
            approval = models.Approval.objects.get(resource_id=res_id)

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

    def attach_domain_ip(self, compute_list, res):
        old_compute_list = res.compute_list
        for c in compute_list:
            if not c.get("domain_ip", ""):
                return False
        try:
            for i in xrange(0, len(old_compute_list)):
                match_one = filter(lambda x: x["ins_id"] == old_compute_list[i].ins_id, compute_list)[0]
                old_compute_list.remove(old_compute_list[i])
                compute = models.ComputeIns(ins_name=match_one["ins_name"], ins_id=match_one["ins_id"], cpu=match_one["cpu"], mem=match_one["mem"],
                                             url=match_one["url"], domain=match_one["domain"], quantity=match_one["quantity"], port=match_one["port"], domain_ip=match_one["domain_ip"])
                old_compute_list.insert(i, compute)
            res.save()
        except Exception as e:
            print "attach domain_ip to compute error:{}".format(e)
        return True

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
            #     flag = self.attach_domain_ip(new_computelist, resource)
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
            #resource = models.ResourceModel.objects.get(res_id=resource_id)
            item_info = models.ItemInformation.objects.get(item_name=resource.project)
        except Exception as e:
            print e
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
        data['unit_id'] = resource.project_id
        data['network_id'] = resource.network_id
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
                        "version": db_res.version
                    }
                )
            data['resource_list'] = res
        if compute_list:
            com = []
            for db_com in compute_list:
                # for i in range(0, db_com.quantity):
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
            # 调用network 表 匹配子网是否有余  插入 表中该子网
            network_id = check_network_use(env)
            if not network_id:
                code = 200
                res = {
                    "code": code,
                    "result": {
                       'res': 'fail',
                       'msg': 'Create resource application fail.  not network_id can use' 
                    }
                }
                return res, code

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
        
        # 调用network 表 匹配子网是否有余  插入 表中该子网
        network_id = check_network_use(resource.env)
        if not network_id:
            code = 200
            res = {
                "code": code,
                "result": {
                    'res': 'fail',
                    'msg': 'Create resource application fail.  not network_id can use' 
                 }
            }
            return res, code

        data = dict()
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
                        "version": db_res.version
                    }
                )
            data['resource_list'] = res
        if compute_list:
            com = []
            for db_com in compute_list:
                # for i in range(0, db_com.quantity):
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
        #MOCE
        code = 200
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
