# -*- coding: utf-8 -*-

import json
import requests
from flask_restful import reqparse, Api, Resource
from flask import current_app, jsonify
from uop.resource_view import resource_view_blueprint
from uop.resource_view.errors import resource_view_errors
from uop.log import Log
from uop.models import ResourceModel
from uop.resource_view.handler import *
from uop.util import response_data


resource_view_api = Api(resource_view_blueprint, errors=resource_view_errors)


class ResourceView(Resource):
    @classmethod
    def get(cls, res_id):
        try:
            parser = reqparse.RequestParser()
            parser.add_argument('reference_sequence', type=str, location='args')
            parser.add_argument('reference_type', type=str, action='append', location='args')
            parser.add_argument('item_filter', type=str, action='append', location='args')
            parser.add_argument('columns_filter', type=str, location='args')
            parser.add_argument('layer_count', type=str, location='args')
            parser.add_argument('total_count', type=str, location='args')
            parser.add_argument('cmdb', type=int)
            args = parser.parse_args()
            Log.logger.info("get graph from cmdb: {}".format(args.cmdb))
            if args.cmdb == 1:
                result = cmdb_graph_search(args, res_id)
            elif args.cmdb == 2:
                result = cmdb2_graph_search(args, res_id)
            else:
                result = cmdb_graph_search(args, res_id)
                #result = response_data(500, "args.cmdb:{}".format(args.cmdb), "")
        except Exception as exc:
            Log.logger.error("get graph from cmdb error: {}".format(str(exc)))
            result = response_data(500, str(exc), "")
        return jsonify(result)


resource_view_api.add_resource(ResourceView, '/res_view/<res_id>')
