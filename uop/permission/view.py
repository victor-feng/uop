# -*- coding: utf-8 -*-

import sys
import datetime
import uuid
from flask import request
from flask_restful import reqparse, Api, Resource
from uop.permission import perm_blueprint
from uop.models import UserInfo,PermissionList,RoleInfo
from uop.permission.errors import perm_errors
from uop.log import Log
from uop.util import response_data

reload(sys)
sys.setdefaultencoding('utf-8')

perm_api = Api(perm_blueprint, errors=perm_errors)

class UserManage(Resource):
    """
    管理用户
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('username', type=str, location='args')
        parser.add_argument('role', type=str, location='args')
        parser.add_argument('id', type=str, location='args')
        parser.add_argument('department', type=str, location='args')
        parser.add_argument('page_num', type=int, location='args')
        parser.add_argument('page_size', type=int, location='args')
        args = parser.parse_args()
        condition = {}
        data={}
        res_list=[]
        if args.name:
            condition["username"] = args.username
        if args.id:
            condition["id"] = args.id
        if args.role:
            condition["role"] = args.role
        if args.department:
            condition["department"] = args.department
        try:
            total_count = UserInfo.objects.filter(**condition).count()
            if args.page_num and args.page_size:
                skip_count = (args.page_num - 1) * args.page_size
                Users = UserInfo.objects.filter(**condition).order_by('-last_login_time').skip(skip_count).limit(args.page_size)
            else:
                Users=UserInfo.objects.filter(**condition).order_by('-last_login_time')
            for user in Users:
                res = {}
                res["id"] = user.id
                res["username"] = user.username
                res["role"] = user.role
                res["department"] = user.department
                res["updated_time"] = str(user.updated_time)
                res["last_login_time"] = str(user.last_login_time)
                res["created_time"] = str(user.created_time)
                res_list.append(res)
            data["total_count"] = total_count
            data["res_list"] = res_list
            code=200
            msg="Get user info success"
        except Exception as e:
            msg = "Get user info error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code


    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('role', type=str)
        parser.add_argument('id', type=str)
        parser.add_argument('department', type=str)
        args = parser.parse_args()
        try:
            user=UserInfo.objects.get(id=args.id)
            user.role = args.role
            user.department = args.department
            user.updated_time = datetime.datetime.now()
            user.save()
            code=200
            data = "Success"
            msg = "Update user info success"
        except Exception as e:
            msg = "Update user info error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data= "Error"
        ret=response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('id', type=str)
        args = parser.parse_args()
        try:
            user=UserInfo.objects.get(id=args.id)
            user.delete()
            code=200

            data="Success"
            msg="Delete user success"
        except Exception as e:
            msg = "Delete user error,error msg is %s"  % str(e)
            Log.logger.error(msg)
            code=500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

class PermManage(Resource):
    """
    管理权限
    """
    def get(self):
        pass

    def post(self):
        pass


class AllPermManage(Resource):
    """
    管理权限
    """
    def get(self):
        pass

    def post(self):
        pass



class RoleManage(Resource):
    """
    管理角色
    """
    def get(self):
        data={}
        res_list=[]
        try:
            Roles=RoleInfo.objects.all()
            for role in Roles:
                res={}
                res["id"] = role.id
                res["name"] = role.name
                res["created_time"] = role.created_time
                res["description"] = role.description
                res_list.appned(res)
            data["res_list"] = res_list
            code = 200
            msg="Get role info success"
        except Exception as e:
            msg = "Get role info error,error msg is %s" % str(e)
            Log.logger.error(msg)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('description', type=str)
        args = parser.parse_args()
        try:
            id=str(uuid.uuid1())
            Role = RoleInfo(id=id,name=args.name,description=args.description,
                            created_time=datetime.datetime.now(),updated_time=datetime.datetime.now())
            Role.save()
            code = 200
            msg = "Create role success"
            data = "Success"
        except Exception as e:
            msg = "Create role error,error msg is %s" % str(e)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()
        try:
            Users=UserInfo.objects.filter(role=args.name)
            Role = RoleInfo.objects.get(name=args.name)
            if not Users:
                Role.delete()
                code = 200
                msg = "Delete role success"
                data = "Success"
            else:
                code = 400
                msg = "Delete role failed.Some users are also part of this role"
                data="Failed"
        except Exception as e:
            msg = "Delete role error, error msg is %s" % str(e)
            data = "Error"
            code = 500
        ret = response_data(code, msg, data)
        return ret, code



perm_api.add_resource(UserManage, '/user')
perm_api.add_resource(PermManage, '/perm')
perm_api.add_resource(RoleManage, '/role')
perm_api.add_resource(AllPermManage, '/allperm')



