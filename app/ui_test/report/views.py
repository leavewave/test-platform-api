#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2020/9/25 17:13
# @Author : ZhongYeHai
# @Site :
# @File : views.py
# @Software: PyCharm
import os

from flask import request

from app.utils.report.report import render_html_report
from app.utils import restful
from app.utils.required import login_required
from app.ui_test import ui_test
from app.baseModel import db
from .models import UiReport as Report
from .forms import GetReportForm, DownloadReportForm, DeleteReportForm, FindReportForm


@ui_test.route('/report/download', methods=['GET'])
@login_required
def api_download_report():
    """ 报告下载 """
    form = DownloadReportForm()
    if form.validate():
        return restful.success(data=render_html_report(form.report_content))
    return restful.fail(form.get_error())


@ui_test.route('/report/list', methods=['GET'])
@login_required
def api_report_list():
    """ 报告列表 """
    form = FindReportForm()
    if form.validate():
        return restful.success(data=Report.make_pagination(form))
    return restful.fail(form.get_error())


@ui_test.route('/report/done', methods=['GET'])
@login_required
def api_report_is_done():
    """ 报告是否生成 """
    return restful.success(data=Report.get_first(id=request.args.to_dict().get('id')).is_done)


@ui_test.route('/report', methods=['GET'])
def api_get_report():
    """ 获取测试报告 """
    form = GetReportForm()
    if form.validate():
        with db.auto_commit():
            form.report.status = '已读'
        return restful.success('获取成功', data=form.report_content)
    return restful.fail(form.get_error())


@ui_test.route('/report', methods=['DELETE'])
@login_required
def api_delete_report():
    """ 删除测试报告 """
    form = DeleteReportForm()
    if form.validate():
        form.report.delete()
        if os.path.exists(form.report_path):
            os.remove(form.report_path)
        return restful.success('删除成功')
    return restful.fail(form.get_error())