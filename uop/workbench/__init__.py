# -*- coding: utf-8 -*-
from flask import Blueprint

bench_blueprint = Blueprint('bench_blueprint', __name__)

from . import handler, forms, errors
