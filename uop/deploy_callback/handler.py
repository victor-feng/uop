# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
import uuid
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.deploy_callback import deploy_cb_blueprint
from uop.deploy_callback.errors import deploy_cb_errors
from uop.models import Deployment

deploy_cb_api = Api(deploy_cb_blueprint, errors=deploy_cb_errors)


class DeployCallback(Resource):
    @classmethod
    def put(cls, deploy_id):
        try:
            dep = Deployment.objects.get(deploy_id=deploy_id)
        except Exception as e:
            print e
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'fail',
                    'msg': "Deployment find error."
                }
            }
            return ret
        if not len(dep):
            code = 200
            ret = {
                'code': code,
                'result': {
                    'res': 'success',
                    'msg': "Deployment not find."
                }
            }
            return ret
        parser = reqparse.RequestParser()
        parser.add_argument('result', type=str)
        args = parser.parse_args()

        dep.deploy_result = args.result
        try:
            dep.save()
        except Exception as e:
            code = 500
            ret = {
                'code': code,
                'result': {
                    'res': 'failed',
                    'msg': "Deployment update failed."
                }
            }
            return ret

        code = 200
        ret = {
            'code': code,
            'result': {
                'res': 'success',
                'msg': "Deployment update success."
            }
        }
        return ret



deploy_cb_api.add_resource(DeployCallback, '/<string:deploy_id>/')