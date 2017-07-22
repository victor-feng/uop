# -*- coding: utf-8 -*-
from flask import Flask
from uop import create_app

application = create_app('testing')
#application = create_app('default')

if __name__ == '__main__':
    application.run()

