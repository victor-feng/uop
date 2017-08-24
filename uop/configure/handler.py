# -*- coding: utf-8 -*-

import logging

from flask_restful import reqparse, Api, Resource, fields

from uop.configure import configure_blueprint

configure_api = Api(configure_blueprint)


class ConfigureEnv(Resource):

    @classmethod
    def get(cls):
        envs = [dict(name=u'开发环境', id='dev'),
                dict(name=u'测试环境', id='test'),
                dict(name=u'生产环境', id='prod')]
        res = {
                'code': 200,
                'result': {
                    'res': envs,
                    'msg': u'请求成功'
                    }
                }
        return res


class Configure(Resource):

    @classmethod
    def get(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        args = parser.parse_args()
        category = parser.parse_args()
        env = args.env if args.env else 'dev'
        category = args.category if args.category else 'nginx'
        logging.info("[UOP] Get configs, env:%s, category: %s", env, category)
        if env == 'dev':
            if category == 'nginx':
                envs = [dict(name=u'开发环境Nginx', url='192.168.2.1', id=1),
                        ]
            else:
                envs = [dict(name=u'开发环境Disconf', url='172.28.18.48', id=1),
                        dict(name=u'开发环境Disconf2', url='172.28.11.111', id=2),
                        ]
        elif env == 'test':
            if category == 'nginx':
                envs = [dict(name=u'测试环境Nginx', url='192.168.2.1', id=2),
                        ]
            else:
                envs = [dict(name=u'测试环境Disconf', url='192.168.2.1', id=3),
                        ]

        res = {
                'code': 200,
                'result': {
                    'res': envs,
                    'msg': u'请求成功'
                    }
                }
        return res

    @classmethod
    def post(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        args = parser.parse_args()
        category = parser.parse_args()
        env = args.env if args.env else 'dev'
        category = args.category if args.category else 'nginx'
        logging.info("[UOP] Create configs, env:%s, category: %s", env, category)

        res = {
                'code': 200,
                'result': {
                        'res': {'id':11},
                        'msg': u'请求成功'
                    }
                }
        return res

    @classmethod
    def put(cls):
        parser = reqparse.RequestParser()
        parser.add_argument('env', type=str)
        parser.add_argument('category', type=str)
        args = parser.parse_args()
        category = parser.parse_args()
        env = args.env if args.env else 'dev'
        category = args.category if args.category else 'nginx'
        logging.info("[UOP] Modify configs, env:%s, category: %s", env, category)

        res = {
                'code': 200,
                'result': {
                    'msg': u'请求成功'
                    }
                }
        return res


configure_api.add_resource(ConfigureEnv, '/env')
configure_api.add_resource(Configure, '/')
