# -*- coding: utf-8 -*-
import json
import uuid
import datetime
import requests
from flask_restful import reqparse, Api, Resource
from uop.approval import approval_blueprint
from uop import models
from uop.approval.errors import approval_errors
from config import APP_ENV, configs


approval_api = Api(approval_blueprint, errors=approval_errors)

CPR_URL = configs[APP_ENV].CRP_URL


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

        data = dict()
        data['resource_list'] = resource.resource_list
        data['project'] = resource.project
        data['project_id'] = resource.project_id
        data['department'] = resource.department
        data['res_id'] = resource.res_id
        data['user_name'] = resource.user_name
        data['user_id'] = resource.user_id
        data['domain'] = resource.domain
        data['env'] = resource.env
        data['application_status'] = resource.application_status
        resource_list = resource.resource_list
        compute_list = resource.compute_list
        if resource_list:
            res = []
            for db_res in resource_list:
                res.append(
                    {
                        "res_name": db_res.ins_name,
                        "res_id": db_res.ins_id,
                        "res_type": db_res.ins_type,
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
                com.append(
                    {
                        "ins_name": db_com.ins_name,
                        "ins_id": db_com.ins_id,
                        "cpu": db_com.cpu,
                        "mem": db_com.mem,
                        "url": db_com.url
                    }
                )
            data['compute_list'] = com

        data_str = json.dumps(data)
        headers = {'Content-Type': 'application/json'}
        try:
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
# approval_api.add_resource(ReservationMock, '/reservation')