# -*- coding: utf-8 -*-
from flask import request, g, current_app as app

from app.baseView import LoginRequiredView
from app.busines import RunCaseBusiness
from app.web_ui_test.models.case import WebUiCase as Case
from app.web_ui_test.models.report import WebUiReport as Report
from app.web_ui_test.blueprint import web_ui_test
from app.web_ui_test.models.caseSuite import WebUiCaseSuite as CaseSuite
from app.web_ui_test.forms.caseSuite import AddCaseSuiteForm, EditCaseSuiteForm, FindCaseSuite, GetCaseSuiteEditForm, \
    DeleteCaseSuiteForm, RunCaseSuiteForm
from utils.client.runUiTest import RunCase


class WebUiGetCaseSuiteListView(LoginRequiredView):

    def get(self):
        """ 用例集list """
        form = FindCaseSuite().do_validate()
        return app.restful.success(data=CaseSuite.make_pagination(form))


class WebUiRunCaseSuiteView(LoginRequiredView):

    def post(self):
        """ 运行用例集下的用例 """
        form = RunCaseSuiteForm().do_validate()
        run_id = Report.get_run_id()
        for env_code in form.env_list.data:
            RunCaseBusiness.run(
                run_id=run_id,
                env_code=env_code,
                browser=form.browser.data,
                is_async=form.is_async.data,
                project_id=form.suite.project_id,
                report_name=form.suite.name,
                task_type="suite",
                report_model=Report,
                case_id=form.suite.get_run_case_id(Case),
                run_type="webUi",
                run_func=RunCase
            )
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"run_id": run_id})


class WebUiGetCaseSuiteTreeView(LoginRequiredView):

    def get(self):
        """ 获取当前服务下的用例集树 """
        suite_list = [
            suite.to_dict() for suite in CaseSuite.query.filter_by(
                project_id=int(request.args.get("project_id"))).order_by(CaseSuite.parent.asc()).all()
        ]
        return app.restful.success(data=suite_list)


class WebUiCaseSuiteView(LoginRequiredView):

    def get(self):
        """ 获取用例集 """
        form = GetCaseSuiteEditForm().do_validate()
        return app.restful.success(data={"name": form.suite.name, "num": form.suite.num})

    def post(self):
        """ 新增用例集 """
        form = AddCaseSuiteForm().do_validate()
        form.num.data = CaseSuite.get_insert_num(project_id=form.project_id.data)
        new_suite = CaseSuite().create(form.data)
        return app.restful.success(f"用例集【{form.name.data}】创建成功", new_suite.to_dict())

    def put(self):
        """ 修改用例集 """
        form = EditCaseSuiteForm().do_validate()
        form.suite.update(form.data)
        return app.restful.success(f"用例集【{form.name.data}】修改成功", form.suite.to_dict())

    def delete(self):
        """ 删除用例集 """
        form = DeleteCaseSuiteForm().do_validate()
        form.suite.delete()
        return app.restful.success("删除成功")


web_ui_test.add_url_rule("/caseSuite", view_func=WebUiCaseSuiteView.as_view("WebUiCaseSuiteView"))
web_ui_test.add_url_rule("/caseSuite/run", view_func=WebUiRunCaseSuiteView.as_view("WebUiRunCaseSuiteView"))
web_ui_test.add_url_rule("/caseSuite/tree", view_func=WebUiGetCaseSuiteTreeView.as_view("WebUiGetCaseSuiteTreeView"))
web_ui_test.add_url_rule("/caseSuite/list", view_func=WebUiGetCaseSuiteListView.as_view("WebUiGetCaseSuiteListView"))
