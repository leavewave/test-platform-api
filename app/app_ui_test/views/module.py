# -*- coding: utf-8 -*-
from flask import request, current_app as app

from app.baseView import LoginRequiredView
from app.busines import ModuleBusiness
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.module import AppUiModule as Module
from app.app_ui_test.forms.module import AddModelForm, EditModelForm, FindModelForm, DeleteModelForm, GetModelForm


class AppUiGetModuleListView(LoginRequiredView):

    def get(self):
        """ 获取模块列表 """
        form = FindModelForm().do_validate()
        return app.restful.get_success(data=Module.make_pagination(form))


class AppUiGetModuleTreeView(LoginRequiredView):

    def get(self):
        """ 获取指定服务下的模块树 """
        project_id = int(request.args.get("project_id"))
        module_list = [
            module.to_dict() for module in Module.query.filter_by(
                project_id=project_id).order_by(Module.parent.asc()).all()
        ]
        return app.restful.success(data=module_list)


class AppUiModuleView(LoginRequiredView):

    def get(self):
        """ 获取模块 """
        form = GetModelForm().do_validate()
        return app.restful.get_success(data=form.module.to_dict())

    def post(self):
        """ 新增模块 """
        form = AddModelForm().do_validate()
        new_model = ModuleBusiness.post(form, Module)
        return app.restful.success(f"模块【{form.name.data}】创建成功", new_model.to_dict())

    def put(self):
        """ 修改模块 """
        form = EditModelForm().do_validate()
        form.old_module.update(form.data)
        return app.restful.success(f"模块【{form.name.data}】修改成功", form.old_module.to_dict())

    def delete(self):
        """ 删除模块 """
        form = DeleteModelForm().do_validate()
        form.module.delete()
        return app.restful.success(f"模块【{form.module.name}】删除成功")


app_ui_test.add_url_rule("/module", view_func=AppUiModuleView.as_view("AppUiModuleView"))
app_ui_test.add_url_rule("/module/list", view_func=AppUiGetModuleListView.as_view("AppUiGetModuleListView"))
app_ui_test.add_url_rule("/module/tree", view_func=AppUiGetModuleTreeView.as_view("AppUiGetModuleTreeView"))