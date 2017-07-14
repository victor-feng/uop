# -*- coding: utf-8 -*-
from flask import Blueprint

dns_blueprint = Blueprint('dns_blueprint', __name__)

from . import handler, forms, errors
