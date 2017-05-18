# -*- coding: utf-8 -*-
from uop import create_app

if __name__ == '__main__':
    # app = create_app('default')
    app = create_app('testing')
    app.run(host='0.0.0.0')
