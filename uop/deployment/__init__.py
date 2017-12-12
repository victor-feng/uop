# -*- coding: utf-8 -*-
from flask import Blueprint

deployment_blueprint = Blueprint('deployment_blueprint', __name__)

from . import handler, forms, errors, view
