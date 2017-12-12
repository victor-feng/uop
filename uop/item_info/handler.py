# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import json
import requests
import datetime
from uop.log import Log
from flask import current_app
from uop.item_info import iteminfo_blueprint
from uop.item_info.errors import user_errors
from uop.models import ItemInformation, ResourceModel

import sys
