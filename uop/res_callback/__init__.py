# -*- coding: utf-8 -*-
from flask import Blueprint

res_callback_blueprint = Blueprint('res_callback_blueprint', __name__)

from . import handler, forms, errors
