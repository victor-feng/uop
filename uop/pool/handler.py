# -*- coding: utf-8 -*-
'''
 Logic Layer
'''
import requests
import json
from uop.pool import pool_blueprint
from uop.pool.errors import pool_errors
from uop.models import ConfigureEnvModel,NetWorkConfig
from uop.util import get_CRP_url, get_network_used
from uop.log import Log
