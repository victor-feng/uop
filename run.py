# -*- coding: utf-8 -*-
from uop import create_app
from config import APP_ENV

if __name__ == '__main__':
    app = create_app(APP_ENV)
    app.run(host='0.0.0.0', debug=True)
