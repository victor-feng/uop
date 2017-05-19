# -*- coding: utf-8 -*-
import uuid
import datetime
from flask_restful import reqparse, Api, Resource
from uop.approval import approval_blueprint
from uop import models
from uop.approval.errors import approval_errors

approval_api = Api(approval_blueprint, errors=approval_errors)


class ApprovalList(Resource):
    def post(self):
        code = 200
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('resource_id', type=str)
            parser.add_argument('department_id', type=str)
            parser.add_argument('creator_id', type=str)
            args = parser.parse_args()

            approval_id = str(uuid.uuid1())
            resource_id = args.resource_id
            department_id = args.department_id
            creator_id = args.creator_id
            create_date = str(datetime.datetime.now)
            # approve_uid
            # approve_date
            # annotation
            approval_status = 'porcessing'

            models.Approval(approval_id=approval_id, resource_id=resource_id,
                            department_id=department_id, creator_id=creator_id,
                            create_date=create_date, approval_status=approval_status).save()

        except Exception as e:
            code = 500

        res = {
            "code": code,
            "result": {
                "res": "",
                "msg": ""
            }
        }
        return res, code

    def get(self):
        res = models.Approval.objects.all()
        return "test info"


class ApprovalInfo(Resource):
    def put(self, res_id):
        code = 200
        tmp_res = ""
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('approve_uid', type=str)
            parser.add_argument('agree', type=bool)
            parser.add_argument('annotation', type=str)
            args = parser.parse_args()

            approval = models.Approval.objects.get(resource_id=res_id)
            if approval:
                approval.approve_uid = args.approve_uid
                approval.approve_date = str(datetime.datetime.now)
                approval.annotation = args.annotation
                if args.agree:
                    approval.approval_status = "success"
                else:
                    approval.approval_status = "failed"
                approval.save()
            else:
                code = 410
                tmp_res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 410
            tmp_res = "A resource with that ID no longer exists"

        res = {
            "code": code,
            "result": {
                "res": tmp_res,
                "msg": ""
            }
        }
        return res, code

    def get(self, res_id):
        code = 200
        msg = {}
        tmp_res=""
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
                    msg["annotation"] = approval.annotation
            else:
                code = 410
                tmp_res = "A resource with that ID no longer exists"
        except Exception as e:
            code = 500

        res = {
            "code": code,
            "result": {
                "res": tmp_res,
                "msg": msg
            }
        }
        return res, code


approval_api.add_resource(ApprovalList, '/')
approval_api.add_resource(ApprovalInfo, '/<string:res_id>')
