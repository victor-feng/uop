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
from uop.util import response_data,deal_enbedded_data

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
        if args.username:
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
            Roles = RoleInfo.objects.all()
            for user in Users:
                for role in Roles:
                    if user.role == role.name:
                        res = {}
                        res["id"] = user.id
                        res["username"] = user.username
                        res["role"] = role.description
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
    管理角色权限
    """
    def get(self):
        pass

    def post(self):
        pass

    def put(self):
        pass

    def delete(self):
        pass


class AllPermManage(Resource):
    """
    管理所有权限
    """
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument('perm_id', type=str, location='args')
        parser.add_argument('name', type=str, location='args')
        parser.add_argument('perm_type', type=str, location='args')
        args = parser.parse_args()
        condition = {}
        data={}
        res_list=[]
        if args.name:
            condition["name"] = args.name
        if args.perm_type:
            condition["perm_type"] = args.perm_type
        if args.perm_id:
            condition["perm_id"] = args.perm_id
        try:
            Permissions = PermissionList.objects.filter(**condition)
            for permission in Permissions:
                res={}
                res["perm_id"] = permission.perm_id
                res["menu_id"] = permission.menu_id
                res["name"] = permission.name
                res["role"] = permission.role
                res["button"] = permission.button
                res["icon"] = permission.icon
                res["operation"] = permission.operation
                res["url"] = permission.url
                res["perm_type"] = permission.perm_type
                res["created_time"] = str(permission.created_time)
                res["updated_time"] = str(permission.updated_time)
                res["endpoint"] = permission.endpoint
                res["level"] = permission.level
                res["parent_id"] = permission.parent_id
                res["get"] = permission.api_get
                res["post"] = permission.api_post
                res["put"] = permission.api_put
                res["delete"] = permission.api_delete
                res_list.append(res)
            data["res_list"] = res_list
            code = 200
            msg = "Get permission info success"
        except Exception as e:
            msg = "Get permission info error,error msg is %s" % str(e)
            code = 500
            data = "Error"
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

    def post(self):
        parser = reqparse.RequestParser()
        parser.add_argument('menu_id', type=str,location="json")
        parser.add_argument('name', type=str,location="json")
        parser.add_argument('button', type=str,location="json")
        parser.add_argument('icon', type=str,location="json")
        parser.add_argument('operation', type=str,location="json")
        parser.add_argument('url', type=str,location="json")
        parser.add_argument('perm_type', type=str,location="json")
        parser.add_argument('endpoint', type=str, location="json")
        parser.add_argument('level', type=str, location="json")
        parser.add_argument('parent_id', type=str, location="json")
        parser.add_argument('get', type=bool, location="json")
        parser.add_argument('put', type=bool, location="json")
        parser.add_argument('post', type=bool, location="json")
        parser.add_argument('delete', type=bool, location="json")
        args = parser.parse_args()
        try:
            code = 200
            Permissions = PermissionList.objects.filter(name=args.name,role='super_admin')
            #如果同一角色，有重名的，给前端返回失败信息
            if Permissions:
                msg = "Create permission Failed,The name has already existed"
                data = "Failed"
                ret = response_data(code, msg, data)
                return ret, code
            perm_id = str(uuid.uuid1())
            Permission=PermissionList(
                perm_id = perm_id,
                name=args.name,
                menu_id = args.menu_id,
                role = "super_admin",
                perm_type = args.perm_type,
                button = args.button,
                icon = args.icon,
                operation = args.operation,
                url = args.url,
                endpoint = args.endpoint,
                level = args.level,
                parent_id = args.parent_id,
                api_get = args.get,
                api_post=args.post,
                api_put=args.put,
                api_delete=args.delete,
                created_time=datetime.datetime.now(),
                updated_time=datetime.datetime.now()
                )
            Permission.save()
            msg = "Create permission success"
            data = "Success"
        except Exception as e:
            code = 500
            msg = "Create permission error,error msg is %s" % str(e)
            data = "Error"
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('perm_id', type=str)
        args = parser.parse_args()
        try:
            Permission = PermissionList.objects.get(perm_id=args.perm_id)
            Permission.delete()
            code = 200
            msg = "Delete permission success"
            data = "Success"
        except Exception as e:
            msg = "Delete permission error,error msg is %s" % str(e)
            code = 500
            data = "Error"
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('perm_id', type=str,location="json")
        parser.add_argument('menu_id', type=str,location="json")
        parser.add_argument('name', type=str,location="json")
        parser.add_argument('button', type=str,location="json")
        parser.add_argument('icon', type=str,location="json")
        parser.add_argument('operation', type=str,location="json")
        parser.add_argument('url', type=str,location="json")
        parser.add_argument('perm_type', type=str,location="json")
        parser.add_argument('endpoint', type=str, location="json")
        parser.add_argument('level', type=str, location="json")
        parser.add_argument('parent_id', type=str, location="json")
        parser.add_argument('get', type=bool, defult=True, location="json")
        parser.add_argument('put', type=bool, defult=True, location="json")
        parser.add_argument('post', type=bool, defult=True, location="json")
        parser.add_argument('delete', type=bool, defult=True, location="json")
        args = parser.parse_args()
        try:
            Permission = PermissionList.objects.get(perm_id=args.perm_id)
            if args.menu_id:
                Permission.menu_id = args.menu_id
            if args.name:
                Permission.name = args.name
            if args.button:
                Permission.button = args.button
            if args.icon:
                Permission.icon = args.icon
            if args.operation:
                Permission.operation = args.operation
            if args.url:
                Permission.url = args.url
            if args.perm_type:
                Permission.perm_type = args.perm_type
            if args.endpoint:
                Permission.endpoint = args.endpoint
            if args.level:
                Permission.level = args.level
            if args.get:
                Permission.api_get = args.get
            if args.post:
                Permission.api_post = args.post
            if args.put:
                Permission.api_put = args.put
            if args.delete:
                Permission.api_delete = args.delete
            Permission.updated_time = datetime.datetime.now()
            Permission.save()

            code = 200
            msg = "Update permission success"
            data = "Success"
        except Exception as e:
            msg = "Update permission error,error msg is %s" % str(e)
            code = 500
            data = "Error"
            Log.logger.error(msg)
        ret = response_data(code, msg, data)
        return ret, code




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
                res["created_time"] = str(role.created_time)
                res["description"] = role.description
                res_list.append(res)
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
            code = 200
            Role_obj = RoleInfo.objects.filter(name=args.name)
            if  Role_obj:
                msg = "Create role Failed,The role has already existed"
                data = "Failed"
            else:
                id = str(uuid.uuid1())
                Role = RoleInfo(id=id,name=args.name,description=args.description,
                                created_time=datetime.datetime.now(),updated_time=datetime.datetime.now())
                Role.save()
                msg = "Create role success"
                data = "Success"
        except Exception as e:
            msg = "Create role error,error msg is %s" % str(e)
            code = 500
            data = "Error"
        ret = response_data(code, msg, data)
        return ret, code

    def put(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('new_name', type=str)
        parser.add_argument('description', type=str)
        args = parser.parse_args()
        try:
            Users = UserInfo.objects.filter(role=args.name)
            Role = RoleInfo.objects.get(name=args.name)
            Role_obj = RoleInfo.objects.filter(name=args.new_name)
            #新名字和旧名字不能相同
            if args.name == args.new_name:
                code=200
                msg = "Update role Failed.The new name is the same as the old name"
                data = "Failed"
                ret = response_data(code, msg, data)
                return ret, code
            # 新名字不能存在
            if Role_obj:
                code = 200
                msg = "Update role Failed,The role has already existed"
                data = "Failed"
                ret = response_data(code, msg, data)
                return ret, code
            if not Users:
                if args.new_name:
                    Role.name = args.new_name
                if args.description:
                    Role.description = args.description
            else:
                if args.description:
                    Role.description = args.description
                if args.new_name:
                    Role.name = args.new_name
                for user in Users:
                    user.role = args.new_name
                    user.save()
            Role.updated_time=datetime.datetime.now()
            Role.save()
            code = 200
            msg = "Update role success"
            data = "Success"
        except Exception as e:
            msg = "Update role error, error msg is %s" % str(e)
            data = "Error"
            code = 500
        ret = response_data(code, msg, data)
        return ret, code

    def delete(self):
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        args = parser.parse_args()
        try:
            Users=UserInfo.objects.filter(role=args.name)
            Role = RoleInfo.objects.get(name=args.name)
            code = 200
            if not Users:
                Role.delete()
                msg = "Delete role success"
                data = "Success"
            else:
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



