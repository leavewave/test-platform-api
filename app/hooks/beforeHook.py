# -*- coding: utf-8 -*-

from flask import request, abort

from utils.required import before_request_required


def register_before_hook(app):
    """ 注册前置钩子函数，有请求时，会按函数所在位置，以从近到远的序顺序执行以下钩子函数 """

    @app.before_request
    def save_log():
        """ 打日志 """
        if request.method != 'HEAD':
            request_data = request.json or request.form.to_dict() or request.args.to_dict()
            app.logger.info(f'【{request.remote_addr}】【{request.method}】【{request.url}】: \n请求参数：{request_data}')

    @app.before_request
    def request_endpoint_is_exist():
        """ 若终结点不存在，则抛出404 """
        if not request.endpoint:
            abort(404)

    @app.before_request
    def login_and_permission_required():
        """ 登录校验和权限校验 """
        before_request_required()  # 校验登录状态和权限