# -*- coding: utf-8 -*-
from flask import Blueprint

resource_view_blueprint = Blueprint('resource_view_blueprint', __name__)

from . import handler, forms, errors, view
