# -*- coding: utf-8 -*-
from flask import Blueprint

deploy_cb_blueprint = Blueprint('deploy_cb_blueprint', __name__)

from . import handler, forms, errors