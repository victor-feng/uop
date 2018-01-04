# -*- coding: utf-8 -*-
from flask import Blueprint

perm_blueprint = Blueprint('perm_blueprint', __name__)

from . import handler, forms, errors, view
