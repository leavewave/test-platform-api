# -*- coding: utf-8 -*-

from flask import request, views, current_app as app

from app.ui_test import ui_test
from app.baseModel import db
from config.config import (ui_action_mapping_list, ui_assert_mapping_list, ui_extract_mapping_list)
from app.ui_test.models.step import UiStep
from app.ui_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm


@ui_test.route('/step/list', methods=['GET'])
def ui_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    if form.validate():
        step_obj_list = UiStep.query.filter_by(case_id=form.caseId.data).order_by(UiStep.num.asc()).all()
        return app.restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
    return app.restful.error(form.get_error())


@ui_test.route('/step/execute/list', methods=['GET'])
def ui_get_execute_list():
    """ 获取步骤执行列表 """
    return app.restful.success('获取成功', data=ui_action_mapping_list)


@ui_test.route('/step/extractMapping/list', methods=['GET'])
def ui_get_extract_mapping_list():
    """ 数据提取方法列表 """
    return app.restful.success('获取成功', data=ui_extract_mapping_list)


@ui_test.route('/step/assertMapping/list', methods=['GET'])
def ui_get_assert_mapping_list():
    """ 断言方法列表 """
    return app.restful.success('获取成功', data=ui_assert_mapping_list)


@ui_test.route('/step/changeIsRun', methods=['PUT'])
def ui_change_step_status():
    """ 修改步骤状态（是否执行） """
    with db.auto_commit():
        UiStep.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return app.restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@ui_test.route('/step/sort', methods=['PUT'])
def ui_change_step_sort():
    """ 更新步骤的排序 """
    UiStep.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
    return app.restful.success(msg='修改排序成功')


@ui_test.route('/step/copy', methods=['POST'])
def ui_copy_step():
    """ 复制步骤 """
    old = UiStep.get_first(id=request.json.get('id')).to_dict()
    old['name'] = f"{old['name']}_copy"
    old['num'] = UiStep.get_insert_num(case_id=old['case_id'])
    step = UiStep().create(old)
    return app.restful.success(msg='步骤复制成功', data=step.to_dict())


class UiStepMethodView(views.MethodView):

    def get(self):
        """ 获取步骤 """
        form = GetStepForm()
        if form.validate():
            return app.restful.success('获取成功', data=form.step.to_dict())
        return app.restful.error(form.get_error())

    def post(self):
        """ 新增步骤 """
        form = AddStepForm()
        if form.validate():
            form.num.data = UiStep.get_insert_num(case_id=form.case_id.data)
            step = UiStep().create(form.data)
            return app.restful.success(f'步骤【{step.name}】新建成功', data=step.to_dict())
        return app.restful.error(form.get_error())

    def put(self):
        """ 修改步骤 """
        form = EditStepForm()
        if form.validate():
            form.step.update(form.data)
            return app.restful.success(msg=f'步骤【{form.step.name}】修改成功', data=form.step.to_dict())
        return app.restful.fail(form.get_error())

    def delete(self):
        """ 删除步骤 """
        form = GetStepForm()
        if form.validate():
            form.step.delete()
            return app.restful.success(f'步骤【{form.step.name}】删除成功')
        return app.restful.error(form.get_error())


ui_test.add_url_rule('/step', view_func=UiStepMethodView.as_view('ui_step'))