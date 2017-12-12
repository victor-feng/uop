# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
from flask import request
from flask import redirect
from flask import jsonify
from flask_restful import reqparse, abort, Api, Resource, fields, marshal_with
from uop.user import user_blueprint
from uop.models import User
from uop.user.errors import user_errors


