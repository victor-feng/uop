# -*- coding: utf-8 -*-

import json
import requests
import datetime
from uop.log import Log
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from flask import current_app, jsonify
from uop.item_info import iteminfo_blueprint
from uop.item_info.errors import user_errors
from uop.models import ItemInformation, ResourceModel
from uop.item_info.handler import *
from config import configs, APP_ENV
from uop.util import response_data

import sys
reload(sys)
sys.setdefaultencoding('utf-8')

iteminfo_api = Api(iteminfo_blueprint, errors=user_errors)

null = "null"

class ItemInfo(Resource):
    @classmethod
    def get(cls,item_id):
        res_list = []
        ret = {}
        code = 200
        item_id = "project_item"
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str, location='args')
            parser.add_argument('user_name', type=str, location='args')
            parser.add_argument('item_name', type=str, location='args')
            parser.add_argument('item_code', type=str, location='args')
            parser.add_argument('start_time', type=str, location='args')
            parser.add_argument('end_time', type=str, location='args')
            parser.add_argument('department', type=str, location='args')
            parser.add_argument('page_num', type=int, location='args')
            parser.add_argument('page_size', type=int, location='args')
            args = parser.parse_args()

            condition = {}
            if args.user_id:
                condition["user_id"] = args.user_id
            if args.user_name:
                condition["user"] = args.user_name
            if args.item_name:
                condition["item_name"] = args.item_name
            if args.item_code:
                condition["item_code"] = args.item_code
            if args.department:
                condition["item_depart"] = args.department
            if args.start_time and args.end_time:
                condition['create_date__gte'] = args.start_time
                condition['create_date__lt'] = args.end_time
            res={}
            try:
                total_count=ItemInformation.objects.filter(**condition).count()
                if args.page_num and args.page_size:
                    skip_count = (args.page_num - 1) * args.page_size
                    items = ItemInformation.objects.filter(**condition).order_by('-create_date').skip(skip_count).limit(args.page_size)
                else:
                    items = ItemInformation.objects.filter(**condition).order_by('-create_date')
                res["total_count"] = total_count
            except Exception as e:
                code = 400
                err_msg=str(e)
                ret = {
                    'code': code,
                    'result': {
                        'res': "failed",
                        'msg': "Resource not find .%s" % err_msg
                    }
                }
                return ret, code

            for item in items:
                result = {}
                result["user"] = item.user
                result["user_id"] = item.user_id
                result["item_id"] = item.item_id
                result["item_name"] = item.item_name
                result["item_code"] = item.item_code
                result["item_depart"] = item.item_depart
                result["item_description"] = item.item_description
                result["create_date"] = str(item.create_date)
                res_list.append(result)
            res["res_list"] = res_list
        except Exception as e:
            code = 500
            err_msg=str(e)
            ret = {
                'code': code,
                'result': {
                    'res': "failed",
                    'msg': "UOP item info get error,%s" % err_msg
                }
            }
            return ret, code
        ret = {
            'code': code,
            'result': {
                'res': res,
                'msg': "success"
            }
        }
        return ret, code

    @classmethod
    def put(cls,item_id):
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('user_id', type=str)
            parser.add_argument('user_name', type=str)
            parser.add_argument('item_name', type=str)
            parser.add_argument('item_code', type=str)
            parser.add_argument('item_department', type=str)
            parser.add_argument('item_description', type=str)
            args = parser.parse_args()
            data = {}
            property_list = []

            if args.item_code:
                property_list.append({"type": "string", "name": "部署单元编号", "value": args.item_code})
            if args.item_name:
                property_list.append({"type": "string", "name": "名称", "value": args.item_name})
            if args.item_department:
                property_list.append({"type": "string", "name": "归属部门", "value": args.item_department})
            if args.item_description:
                property_list.append({"type": "string", "name": "部署单元描述", "value": args.item_description})
            data["property_list"] = property_list
            data_str = json.dumps(data)
            CMDB_URL = current_app.config['CMDB_URL']
            CMDB_API = CMDB_URL+'cmdb/api/'
            res = requests.put(CMDB_API + "repo/" + item_id + "/", data=data_str)
            ret = eval(res.content.decode('unicode_escape'))
            if res.status_code == 200:
                item = ItemInformation.objects.get(item_id=item_id)
                if args.item_code:
                   item.item_code = args.item_code
                if args.item_name:
                    item.item_name = args.item_name
                if args.item_department:
                    item.item_depart = args.item_department
                if args.item_description:
                    item.item_description = args.item_description
                item.save()

        except Exception as e:
            code = 500

        return ret, code

    @classmethod
    def delete(cls, item_id):
        ret = {}
        code = 200
        status = 0
        try:
            items = ItemInformation.objects.filter(item_id=item_id)
            if items:
                item = items[0]
                res = ResourceModel.objects.filter(project_id=item_id,approval_status="success")
                if not res:
                    item.delete()
                    code = 200
                    status = 0
                    msg = '部署单元删除成功'
                    CMDB_URL = current_app.config['CMDB_URL']
                    CMDB_API = CMDB_URL+'cmdb/api/'
                    res = requests.delete(CMDB_API + "repo_delete/" + item_id + "/")
                else:
                    code = 200
                    status = 1
                    msg = '该部署单元拥有部署实例，需要清除后方可删除部署单元'
        except Exception as e:
            code = 500
            msg = '后端出现异常, 请联系管理员'

        ret = {
            'code': code,
            'status': status,
            'result': {
                'res': "",
                'msg': msg
            }
        }
        return ret, code


class ItemPostInfo(Resource):
    def post(self):
        # req = request
        ret = {}
        code = 200
        try:
            parser = reqparse.RequestParser()
            #parser.add_argument('property_list', type=list, required=True, location='json')
            parser.add_argument('user_id', type=str)
            parser.add_argument('user_name', type=str)
            parser.add_argument('item_name', type=str)
            parser.add_argument('item_code', type=str)
            parser.add_argument('item_department', type=str)
            parser.add_argument('item_description', type=str)
            args = parser.parse_args()

            CMDB_URL = current_app.config['CMDB_URL']
            CMDB_API = CMDB_URL+'cmdb/api/'
            req = CMDB_API + "repo_detail?item_id=person_item&p_code=user_id&value=" + args.user_id
            res = requests.get(req)
            ret = eval(res.content.decode('unicode_escape'))
            user_p_code = None
            if res.status_code == 200:
                Log.logger.info("[UOP] Get resust: %s", ret.get("result"))
                result_res = ret.get("result").get("res")
                if len(result_res) > 0:
                    user_p_code = result_res[0].get("p_code")

            data = {}
            data["name"] = args.item_name
            data["layer_id"] = "business"
            data["group_id"] = "BusinessLine"
            data["item_id"] = "project_item"

            property_list = []
            property_list.append({"type": "string", "name": "部署单元编号", "value": args.item_code})
            property_list.append({"type": "string", "name": "名称", "value": args.item_name})
            property_list.append({"type": "string", "name": "归属部门", "value": args.item_department})
            property_list.append({"type": "string", "name": "部署单元描述", "value": args.item_description})
            property_list.append({"type": "string", "name": "创建人", "value": args.user_name})
            property_list.append({"type": "string", "name": "创建时间", "value": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
            if user_p_code is not None:
                property_list.append({
                                'type': 'reference',
                                'reference_ci': 'person_item',
                                'reference_id': user_p_code,
                                'name': '归属人',
                                })
            data["property_list"] = property_list
            data_str = json.dumps(data)

            CMDB_URL = current_app.config['CMDB_URL']
            CMDB_API = CMDB_URL+'cmdb/api/'
            res = requests.post(CMDB_API + "repo/", data=data_str)
            ret = eval(res.content.decode('unicode_escape'))
            if res.status_code == 200:
                if ItemInformation.objects.filter(item_name = args.item_name).count() ==0:
                    ItemInformation(
                        user = args.user_name,
                        user_id = args.user_id,
                        item_id = ret.get("result").get("id"),
                        item_name = args.item_name,
                        item_depart= args.item_department,
                        item_description = args.item_description,
                        item_code = args.item_code).save()
                else:
                    ret = {
                        'code': 2017,
                        'result': {
                            'msg': '部署单元名称重复',
                        }
                    }
        except Exception as e:
            code = 500

        return ret, code


class ItemInfoLoacl(Resource):
    def get(self,user_id):
        code = 200
        res_list = []
        try:
            items = ItemInformation.objects.filter(user_id = user_id)
            for i in items:
                res = {}
                res["user"] = i.user
                res["user_id"] = i.user_id
                res["item_id"] = i.item_id
                res["item_name"] = i.item_name
                res["item_code"] = i.item_code
                res["item_depart"] = i.item_depart
                res["item_description"] = i.item_description
                res_list.append(res)
        except Exception as e:
            code = 500

        ret = {
            'code': code,
            'result': {
                'res': res_list,
                'msg': ""
            }
        }
        return ret, code


class CheckImageUrl(Resource):
    def get(self):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('image_url', type=str)
            args = parser.parse_args()
            image_url=args.image_url
            num = image_url.count(':')
            if num ==1:
                image_info=image_url.strip().split(':')
                image_tag=image_info[1]
                if image_tag:
                    status='success'
                    msg='image url check success'
                else:
                    status = 'failed'
                    msg = 'image url check failed'
            else:
                status = 'failed'
                msg = 'image url check failed'
            code = 200
        except Exception as e:
            code = 500
            status = 'error'
            msg = 'image url check error'

        ret = {
            'code': code,
            'result': {
                'msg': msg,
                'status':status,
            }
        }
        return ret, code


class BusinessProject(Resource):
    '''
    -业务模块工程-    资源视图
    '''
    def get(self):
        '''
        根据？name=参数，返回相应的CMDB仓库数据
        A 类视图去查 部门--->业务--->模块--->工程
        :return:
        '''
        response = response_data(200, "success", "")
        parser = reqparse.RequestParser()
        parser.add_argument('name', type=str)
        parser.add_argument('code', type=str)
        parser.add_argument('uid', type=str)
        parser.add_argument('token', type=str)
        parser.add_argument('instance_id', type=str)
        parser.add_argument('model_id', type=str)
        args = parser.parse_args()
        name, code, uid, token, instance_id, model_id = \
            args.name, args.code, args.uid, args.token, args.instance_id, args.model_id
        if not uid or not token:
            uid, token = get_uid_token()
        A_data = {
            "uid": uid,
            "token": token,
            "sign":"",
            "data":{
                "instance":{
                    "model_id": model_id,
                    "instance_id": instance_id
                },
                "relation":[{
                    "model_id":""
                }]
            }
        }
        Log.logger.info("the request data:{}".format(A_data))
        try:
            a_query_result = Aquery(A_data)
            format_data = package_data(a_query_result, A_data)  # 重新组装数据
            # parameters = get_entity(format_data["entity_id"]) # 获取A视图下一层实体属性
            # format_data.update(property=parameters)
            Log.logger.info(u"A视图搜素结果format_data: {}".format(format_data))
            response["result"]["data"] = format_data
        except Exception as exc:
            response["code"] = 500
            response["result"]["msg"] = str(exc)
            Log.logger.error("get data from CMDB2.0 error:{}".format(str(exc)))
        return jsonify(response)

    def post(self):
        '''
        调用插入子图，插入 业务|模块|工程
        注：
            关系层采用默认的default，减少用户输入关系层的数据
        :return:
        '''
        response = response_data(200, "success", "")
        parser = reqparse.RequestParser()
        parser.add_argument('model_id', type=str) #新增的实例继承的实体id
        parser.add_argument('instance_id', type=str)  # 上一级别的实例id
        parser.add_argument('property', type=list, location='json')
        parser.add_argument('uid', type=str)
        parser.add_argument('token', type=str)
        args = parser.parse_args()
        try:
            graph_data = subgrath_data(args)
            response["result"]["data"] = graph_data
        except Exception as exc:
            response["code"] = 500
            response["result"]["msg"] = str(exc)
            Log.logger.error(u"A类视图添加业务模块工程出错:{}".format(str(exc)))
        return jsonify(response)


class CmdbModels(Resource):
    def get(self):
        '''
        filters 参数为空时会去cmdb2.0获取最新的实体属性信息
        非空时，会按照filters字典去匹配相应的实体
        :return:
        '''
        response = response_data(200, "success", "")
        parser = reqparse.RequestParser()
        parser.add_argument('filters', type=dict, location='json')
        args = parser.parse_args()
        filters = args.filters
        Log.logger.info("args.filters:{},type:{}".format(filters, type(filters)))
        try:
            data = get_entity_from_file(filters) if filters else get_entity()
            response["result"]["data"] = data
        except Exception as exc:
            Log.logger.error("get CmdbModels error:{}".format(str(exc)))
        return jsonify(response)

    def post(self):
        pass
    pass


iteminfo_api.add_resource(ItemInfo, '/iteminfoes/<string:item_id>')
iteminfo_api.add_resource(ItemInfoLoacl, '/iteminfoes/local/<string:user_id>')
iteminfo_api.add_resource(ItemPostInfo, '/iteminfoes')
iteminfo_api.add_resource(CheckImageUrl, '/check_image_url')
iteminfo_api.add_resource(BusinessProject, '/cmdbinfo')
iteminfo_api.add_resource(CmdbModels, '/cmdbmodels')