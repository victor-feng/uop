#/home/zhangyb/Desktop/uop_runtime/bin/python
# -*- coding: utf-8 -*-
from config import APP_ENV
from uop import create_app
from uop import models
from uop.models import db
from flask_script  import Manager, Shell

app = create_app(APP_ENV)

manager = Manager(app)

def _make_context():
    return dict(app=app, db=db, models=models)

manager.add_command("shell", Shell(make_context=_make_context, use_ipython=True))
if __name__ == "__main__":
    manager.run()