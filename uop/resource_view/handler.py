# -*- coding: utf-8 -*-
import json
import requests
from flask_restful import reqparse, Api, Resource
from uop.resource_view import resource_view_blueprint
from uop.resource_view.errors import resource_view_errors
from uop.log import Log
from config import APP_ENV, configs


resource_view_api = Api(resource_view_blueprint, errors=resource_view_errors)
CMDB_URL = configs[APP_ENV].CMDB_URL
CMDB_RELATION = CMDB_URL+'cmdb/api/repo_relation/'


class ResourceView(Resource):
    @classmethod
    def get(self, id):
        parser = reqparse.RequestParser()
        parser.add_argument('reference_type', type=str, action='append', location='args')
        parser.add_argument('item_filter', type=str, action='append', location='args')
        parser.add_argument('columns_filter', type=str, location='args')
        parser.add_argument('layer_count', type=str, location='args')
        parser.add_argument('total_count', type=str, location='args')

        args = parser.parse_args()
        param_str = "?"
        if args.reference_type:
            for reference_type in args.reference_type:
                if param_str == "?":
                    param_str += "reference_type="+reference_type
                else:
                    param_str += "&reference_type="+reference_type
        if args.item_filter:
            for item_filter in args.item_filter:
                if param_str == "?":
                    param_str += "item_filter="+item_filter
                else:
                    param_str += "&item_filter="+item_filter
        if args.columns_filter:
            if param_str == "?":
                param_str += "columns_filter="+args.columns_filter
            else:
                param_str += "&columns_filter="+args.columns_filter
        if args.layer_count:
            if param_str == "?":
                param_str += "layer_count="+args.layer_count
            else:
                param_str += "&layer_count="+args.layer_count
        if args.total_count:
            if param_str == "?":
                param_str += "total_count="+args.total_count
            else:
                param_str += "&total_count="+args.total_count

        if param_str == "?":
            req_str = CMDB_RELATION + id + '/'
        else:
            req_str = CMDB_RELATION + id + param_str

        Log.logger.debug("The Request Body is: " + req_str)

        ci_relation_query = requests.get(req_str)
        Log.logger.debug(ci_relation_query)
        Log.logger.debug(ci_relation_query.content)
        ci_relation_query_decode = ci_relation_query.content.decode('unicode_escape')
        result = json.loads(ci_relation_query_decode)

        return result, 200


resource_view_api.add_resource(ResourceView, '/res_view/<id>')
