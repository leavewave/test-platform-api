# -*- coding: utf-8 -*-
import os

from flask import current_app as app

from app.baseView import LoginRequiredView
from app.home.blueprint import home
from app.api_test.models.step import ApiStep as Step
from app.baseModel import db
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.module import ApiModule as Module
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.task import ApiTask as Task
from app.api_test.models.report import ApiReport as Report
from utils.util.fileUtil import CASE_FILE_ADDRESS
from utils.util.timeUtil import get_now, time_calculate, get_week_start_and_end


class GetApiTestCountTitleView(LoginRequiredView):

    def get(self):
        """ 获取卡片统计 """
        return app.restful.success(
            '获取成功',
            data={
                'project': len(Project.get_all()),
                'module': len(Module.get_all()),
                'api': len(Api.get_all()),
                'file': len(os.listdir(CASE_FILE_ADDRESS)),
                'case': len(Case.get_all()),
                'step': len(Step.get_all()),
                'task': len(Task.get_all()),
                'report': len(Report.get_all())
            })


class GetApiTestCountProjectView(LoginRequiredView):

    def get(self):
        """ 统计服务数 """
        return app.restful.success(data={
            'title': '服务',
            'options': ['总数'],
            'data': [len(Project.get_all())],
        })


class GetApiTestCountModuleView(LoginRequiredView):

    def get(self):
        """ 统计模块数 """
        return app.restful.success(data={
            'title': '模块',
            'options': ['总数'],
            'data': [len(Module.get_all())],
        })


class GetApiTestCountApiView(LoginRequiredView):

    def get(self):
        """ 统计接口数 """
        data = db.execute_query_sql("""
            select methods, count(*) as totle
                from (select case
                         when method = 'GET' then 'GET'
                         when method = 'POST' then 'POST'
                         when method = 'PUT' then 'PUT'
                         when method = 'DELETE' then 'DELETE'
                         else 'Other' end as methods
                      from `api_test_api`
                     ) as t
                group by methods
            """)
        usage = db.execute_query_sql("""
            select item, count(*) as totle
                from (select IF(quote_count = 0, 'not_used', 'is_used') as item from `api_test_api`) as t
                group by item
        """)
        return app.restful.success(data={
            'title': '接口',
            'options': [
                '总数',
                'GET请求', 'POST请求', 'PUT请求', 'DELETE请求', '其他请求',
                '已使用数', '未使用数'
            ],
            'data': [
                sum(data.values()),
                data.get('GET', 0), data.get('POST', 0), data.get('PUT', 0), data.get('DELETE', 0),
                data.get('Other', 0),
                usage.get('is_used', 0), usage.get('not_used', 0)
            ]
        })


class GetApiTestCountCaseView(LoginRequiredView):

    def get(self):
        """ 统计用例数 """
        data = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = 0, 'not_run', 'is_run') as status from `api_test_case`) as t
                group by status;
            """)

        last_day_add = len(Case.query.filter(Case.created_time.between(time_calculate(-1), time_calculate(0))).all())
        to_day_add = len(Case.query.filter(Case.created_time.between(time_calculate(0), get_now())).all())

        last_start_time, last_end_time = get_week_start_and_end(1)
        last_week_add = len(Case.query.filter(Case.created_time.between(last_start_time, last_end_time)).all())

        current_start_time, current_end_time = get_week_start_and_end(0)
        current_week_add = len(Case.query.filter(Case.created_time.between(current_start_time, current_end_time)).all())

        last_month_add = len(Case.query.filter(Case.created_time.between(time_calculate(-30), get_now())).all())

        return app.restful.success('获取成功', data={
            'title': '用例',
            'options': [
                '总数', '要执行的用例', '不执行的用例',
                '昨日新增', '今日新增', '本周新增', '上周新增', '30日内新增'
            ],
            'data': [
                sum(data.values()), data.get('is_run', 0), data.get('not_run', 0),
                last_day_add, to_day_add, current_week_add, last_week_add, last_month_add
            ],
        })


class GetApiTestCountStepView(LoginRequiredView):

    def get(self):
        """ 统计步骤数 """
        data = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = 0, 'not_run', 'is_run') as status from `api_test_step`) as t
                group by status;
            """)

        last_day_add = len(Step.query.filter(Step.created_time.between(time_calculate(-1), time_calculate(0))).all())
        to_day_add = len(Step.query.filter(Step.created_time.between(time_calculate(0), get_now())).all())

        last_start_time, last_end_time = get_week_start_and_end(1)
        last_week_add = len(Step.query.filter(Step.created_time.between(last_start_time, last_end_time)).all())

        current_start_time, current_end_time = get_week_start_and_end(0)
        current_week_add = len(Step.query.filter(Step.created_time.between(current_start_time, current_end_time)).all())

        last_month_add = len(Step.query.filter(Step.created_time.between(time_calculate(-30), get_now())).all())

        return app.restful.success('获取成功', data={
            'title': '测试步骤',
            'options': [
                '总数', '要执行的步骤', '不执行的步骤',
                '昨日新增', '今日新增', '本周新增', '上周新增', '30日内新增'
            ],
            'data': [
                sum(data.values()), data.get('is_run', 0), data.get('not_run', 0),
                last_day_add, to_day_add, current_week_add, last_week_add, last_month_add
            ],
        })


class GetApiTestCountTaskView(LoginRequiredView):

    def get(self):
        """ 统计定时任务数 """
        status = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = '启用中', 'enable', 'disable') as status from `api_test_task` ) as t
                group by status
            """)

        is_send = db.execute_query_sql("""
            select is_send, count(*) as totle
                from (select case
                         when is_send = 1 then 'is_send1'
                         when is_send = 2 then 'is_send2'
                         else 'is_send3' end as is_send
                      from `api_test_task`
                     ) as t
                group by is_send
            """)

        send_type = db.execute_query_sql("""
            select send_type, count(*) as totle
                from (select case
                         when send_type = 'all' then 'all'
                         when send_type = 'we_chat' then 'we_chat'
                         when send_type = 'ding_ding' then 'ding_ding'
                         else 'email' end as send_type
                      from `api_test_task`
                     ) as t
                group by send_type
            """)
        return app.restful.success('获取成功', data={
            'title': '定时任务',
            'options': [
                '总数', '启用中', '禁用中',
                '始终发送报告的任务', '不发送报告的任务', '失败时发送报告的任务',
                '都接收报告', '仅企业微信群接收报告', '仅钉钉群接收报告', '仅邮件接收报告',
            ],
            'data': [
                sum(status.values()),
                status.get('enable', 0), status.get('disable', 0),
                is_send.get('is_send2', 0), is_send.get('is_send1', 0), is_send.get('is_send3', 0),
                send_type.get('all', 0), send_type.get('we_chat', 0), send_type.get('ding_ding', 0),
                send_type.get('email', 0)
            ]
        })


class GetApiTestCountReportView(LoginRequiredView):

    def get(self):
        """ 统计测试报告数 """
        status = db.execute_query_sql("""
            select status, count(*) as totle
                from (select IF(status = '已读', 'is_read', 'not_read') as status from `api_test_report` ) as t
                group by status
            """)

        is_passed = db.execute_query_sql("""
            select is_passed, count(*) as totle
                from (select IF(is_passed = 1, 'is_passed', 'not_passed') as is_passed from `api_test_report`) as t
                group by is_passed
            """)

        run_type = db.execute_query_sql("""
            select run_type, count(*) as totle
                from (select case 
                         when run_type = 'api' then 'api'
                         when run_type = 'set' then 'set'
                         when run_type = 'case' then 'case'
                         when run_type = 'task' then 'task' end as run_type from `api_test_report`) as t
                group by run_type
            """)

        last_day_add = len(
            Report.query.filter(Report.created_time.between(time_calculate(-1), time_calculate(0))).all())
        to_day_add = len(Report.query.filter(Report.created_time.between(time_calculate(0), get_now())).all())
        last_start_time, last_end_time = get_week_start_and_end(1)
        last_week_add = len(Report.query.filter(Report.created_time.between(last_start_time, last_end_time)).all())

        current_start_time, current_end_time = get_week_start_and_end(0)
        current_week_add = len(
            Report.query.filter(Report.created_time.between(current_start_time, current_end_time)).all())

        last_month_add = len(Report.query.filter(Report.created_time.between(time_calculate(-30), get_now())).all())

        return app.restful.success('获取成功', data={
            'title': '测试报告',
            'options': [
                '总数', '已读', '未读', '通过数', '失败数',
                '接口生成', '用例生成', '用例集生成', '定时任务生成',
                '昨日新增', '今日新增', '本周新增', '上周新增', '30日内新增'
            ],
            'data': [
                sum(status.values()),
                status.get('is_read', 0), status.get('not_read', 0),
                is_passed.get('is_passed', 0), is_passed.get('not_passed', 0),
                run_type.get('api', 0), run_type.get('case', 0), run_type.get('set', 0), run_type.get('task', 0),
                last_day_add, to_day_add, current_week_add, last_week_add, last_month_add
            ]
        })


class GetApiTestCountFileView(LoginRequiredView):

    def get(self):
        """ 统计文件数 """
        return app.restful.success(data={
            'title': '测试文件',
            'options': ['总数'],
            'data': [len(os.listdir(CASE_FILE_ADDRESS))],
        })


home.add_url_rule('/apiTest/api', view_func=GetApiTestCountApiView.as_view('GetApiTestCountApiView'))
home.add_url_rule('/apiTest/file', view_func=GetApiTestCountFileView.as_view('GetApiTestCountFileView'))
home.add_url_rule('/apiTest/task', view_func=GetApiTestCountTaskView.as_view('GetApiTestCountTaskView'))
home.add_url_rule('/apiTest/step', view_func=GetApiTestCountStepView.as_view('GetApiTestCountStepView'))
home.add_url_rule('/apiTest/case', view_func=GetApiTestCountCaseView.as_view('GetApiTestCountCaseView'))
home.add_url_rule('/apiTest/title', view_func=GetApiTestCountTitleView.as_view('GetApiTestCountTitleView'))
home.add_url_rule('/apiTest/module', view_func=GetApiTestCountModuleView.as_view('GetApiTestCountModuleView'))
home.add_url_rule('/apiTest/report', view_func=GetApiTestCountReportView.as_view('GetApiTestCountReportView'))
home.add_url_rule('/apiTest/project', view_func=GetApiTestCountProjectView.as_view('GetApiTestCountProjectView'))
