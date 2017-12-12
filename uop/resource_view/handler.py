# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
from flask import current_app
from uop.resource_view import resource_view_blueprint
from uop.resource_view.errors import resource_view_errors
from uop.log import Log
from uop.models import ResourceModel

