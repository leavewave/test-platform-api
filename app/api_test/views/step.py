# -*- coding: utf-8 -*-
from flask import current_app as app, request, views

from app.api_test import api_test
from app.api_test.models.api import ApiMsg
from app.baseModel import db
from app.api_test.models.step import ApiStep
from app.api_test.forms.step import GetStepListForm, GetStepForm, AddStepForm, EditStepForm


@api_test.route('/step/list', methods=['GET'])
def api_get_step_list():
    """ 根据用例id获取步骤列表 """
    form = GetStepListForm()
    if form.validate():
        step_obj_list = ApiStep.query.filter_by(case_id=form.caseId.data).order_by(ApiStep.num.asc()).all()
        return app.restful.success('获取成功', data=[step.to_dict() for step in step_obj_list])
    return app.restful.error(form.get_error())


@api_test.route('/step/changeIsRun', methods=['PUT'])
def api_change_step_status():
    """ 修改步骤状态（是否执行） """
    with db.auto_commit():
        ApiStep.get_first(id=request.json.get('id')).is_run = request.json.get('is_run')
    return app.restful.success(f'步骤已修改为 {"执行" if request.json.get("is_run") else "不执行"}')


@api_test.route('/step/changeHost', methods=['PUT'])
def api_change_step_host():
    """ 修改步骤引用的host """
    step = ApiStep.get_first(id=request.json.get('id'))
    with db.auto_commit():
        step.replace_host = request.json.get('replace_host')
    return app.restful.success(
        f'步骤已修改为 {"使用【用例】所在服务的host" if request.json.get("replace_host") else "使用【接口】所在服务的host"}',
        data=step.to_dict()
    )


@api_test.route('/step/sort', methods=['PUT'])
def api_change_step_sort():
    """ 更新步骤的排序 """
    ApiStep.change_sort(request.json.get('List'), request.json.get('pageNum', 0), request.json.get('pageSize', 0))
    return app.restful.success(msg='修改排序成功')


@api_test.route('/step/copy', methods=['POST'])
def api_copy_step():
    """ 复制步骤 """
    old = ApiStep.get_first(id=request.json.get('id')).to_dict()
    old['name'] = f"{old['name']}_copy"
    old['num'] = ApiStep.get_insert_num(case_id=old['case_id'])
    step = ApiStep().create(old)
    step.add_api_quote_count()
    return app.restful.success(msg='步骤复制成功', data=step.to_dict())


class ApiStepMethodView(views.MethodView):

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
            form.num.data = ApiStep.get_insert_num(case_id=form.case_id.data)
            step = ApiStep().create(form.data)
            step.add_api_quote_count()
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
            form.step.subtract_api_quote_count()
            return app.restful.success(f'步骤【{form.step.name}】删除成功')
        return app.restful.error(form.get_error())


api_test.add_url_rule('/step', view_func=ApiStepMethodView.as_view('api_step'))
