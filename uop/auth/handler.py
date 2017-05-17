# -*- coding: utf-8 -*-
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.auth import auth_blueprint
from uop.models import UserInfo, User
from uop.auth.errors import user_errors


auth_api = Api(auth_blueprint, errors=user_errors)


class UserRegister(Resource):
    def post(self):
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

    def get(self):
        return "test info", 200


class UserList(Resource):
    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str)
        parser.add_argument('password', type=str)
        args = parser.parse_args()

        username = args.username
        password = args.password
        user = UserInfo.objects.get(username=username)
        if user:
            if user.password == password:
                res = '登录成功'
                code = 200
            else:
                res = '密码错误'
                code = 304
        else:
            code = 305
            res = '用户不存在'
        res = {
                "code": code,
                "result": {
                    "res": res,
                    "msg": ""
                    }
                }
        return res, code


class AdminUserList(Resource):
    def post(self):
        data = json.loads(request.body)
        username = data.get('username')
        password = data.get('password')
        user = UserInfo.objects.get(username=username)
        if user:
            if user.password == password:
                if user.is_admin:
                    res = '管理员登录成功'
                    code = 200
                else:
                    res = '您没有管理员权限'
                    code = 405
        else:
            res = '用户不存在'
            code = 404
        res = {
                'code': code,
                'result': {
                    'res': res,
                    'msg': ''
                    }
                }
        return json.dumps(res)


class AdminUserDetail(Resource):
    def put(self, name):
        user = UserInfo.objects.get(username=name)
        is_admin = json.loads(request.body())
        if user:
            user.is_admin = is_admin
            user.save()

    def delete(self, name):
        user = UserInfo.objects.get(username=name)
        user.delete()
        pass


auth_api.add_resource(UserRegister, '/users')
auth_api.add_resource(UserList, '/userlist')
auth_api.add_resource(AdminUserList, '/adminlist')
auth_api.add_resource(AdminUserDetail, '/admindetail/<name>')
