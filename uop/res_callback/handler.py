# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.res_callback import res_callback_blueprint
from uop.models import User
from uop.res_callback.errors import res_callback_errors

user_api = Api(res_callback_blueprint, errors=res_callback_errors)


class UserRegister(Resource):
    """
    test
    """
    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('email', type=str)
        parser.add_argument('first_name', type=str)
        parser.add_argument('last_name', type=str)
        args = parser.parse_args()

        email = args.email
        first_name = args.first_name
        last_name = args.first_name

        User(email=email, first_name=first_name, last_name=last_name).save()

        res = {
            "code": 200,
            "result": {
                "res": "success",
                "msg": "test info"
            }
        }
        return res, 200

    @classmethod
    def get(cls):
        return "test info", 409


user_api.add_resource(UserRegister, '/users')
