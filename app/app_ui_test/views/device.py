# -*- coding: utf-8 -*-
from flask import request, current_app as app
import requests

from app.baseView import LoginRequiredView
from app.app_ui_test.blueprint import app_ui_test
from app.app_ui_test.models.device import AppUiRunServer as Server, AppUiRunPhone as Phone
from app.app_ui_test.forms.device import (
    AddServerForm, HasServerIdForm, EditServerForm, GetServerListForm,
    AddPhoneForm, HasPhoneIdForm, EditPhoneForm, GetPhoneListForm
)


class AppUiGetRunServerListView(LoginRequiredView):

    def get(self):
        """ 服务器列表 """
        form = GetServerListForm().do_validate()
        return app.restful.success(data=Server.make_pagination(form))


class AppUiChangeRunServerSortView(LoginRequiredView):

    def put(self):
        """ 更新服务器的排序 """
        Server.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppUiRunServerCopyView(LoginRequiredView):

    def post(self):
        """ 复制服务器 """
        form = HasServerIdForm().do_validate()
        new_server = form.server.copy()
        return app.restful.success(msg="复制成功", data=new_server.to_dict())


class AppUiRunServer(LoginRequiredView):

    def get(self):
        """ 调appium服务器 """
        form = HasServerIdForm().do_validate()
        try:
            status_code = requests.get(f'http://{form.server.ip}:{form.server.port}', timeout=5).status_code
        except Exception as error:
            form.server.request_fail()
            return app.restful.fail(msg="设置的appium服务器地址不能访问，请检查")
        if status_code > 499:  # 5开头的
            form.server.request_fail()
            return app.restful.fail(msg=f'设置的appium服务器地址响应状态码为 {status_code}，请检查')
        form.server.request_success()
        return app.restful.success(msg=f'服务器访问成功，响应为：状态码为 {status_code}')


class AppUiRunServerView(LoginRequiredView):

    def get(self):
        """ 获取服务 """
        form = HasServerIdForm().do_validate()
        return app.restful.success(data=form.server.to_dict())

    def post(self):
        """ 新增服务 """
        form = AddServerForm().do_validate()
        form.num.data = Server.get_insert_num()
        new_server = Server().create(form.data)
        return app.restful.success(f"服务器【{form.name.data}】新建成功", new_server.to_dict())

    def put(self):
        """ 修改服务 """
        form = EditServerForm().do_validate()
        form.server.update(form.data)
        return app.restful.success(f"服务器【{form.name.data}】修改成功", form.server.to_dict())

    def delete(self):
        """ 删除服务 """
        form = HasServerIdForm().do_validate()
        form.server.delete()
        return app.restful.success(f"服务器【{form.server.name}】删除成功")


class AppUiGetRunPhoneListView(LoginRequiredView):

    def get(self):
        """ 手机列表 """
        form = GetPhoneListForm().do_validate()
        return app.restful.success(data=Phone.make_pagination(form))


class AppUiChangeRunPhoneSortView(LoginRequiredView):

    def put(self):
        """ 更新手机列表的排序 """
        Phone.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class AppUiRunPhoneCopyView(LoginRequiredView):

    def post(self):
        """ 复制手机 """
        form = HasPhoneIdForm().do_validate()
        new_phone = form.phone.copy()
        return app.restful.success(msg="复制成功", data=new_phone.to_dict())


class AppUiRunPhoneView(LoginRequiredView):

    def get(self):
        """ 获取手机 """
        form = HasPhoneIdForm().do_validate()
        return app.restful.success(data=form.phone.to_dict())

    def post(self):
        """ 新增手机 """
        form = AddPhoneForm().do_validate()
        form.num.data = Phone.get_insert_num()
        new_phone = Phone().create(form.data)
        return app.restful.success(f"手机【{form.name.data}】新建成功", new_phone.to_dict())

    def put(self):
        """ 修改手机 """
        form = EditPhoneForm().do_validate()
        form.phone.update(form.data)
        return app.restful.success(f"手机【{form.name.data}】修改成功", form.phone.to_dict())

    def delete(self):
        """ 删除手机 """
        form = HasPhoneIdForm().do_validate()
        form.phone.delete()
        return app.restful.success(f"手机【{form.phone.name}】删除成功")


app_ui_test.add_url_rule("/device/server/run", view_func=AppUiRunServer.as_view("AppUiRunServer"))
app_ui_test.add_url_rule("/device/server", view_func=AppUiRunServerView.as_view("AppUiRunServerView"))
app_ui_test.add_url_rule("/device/server/copy", view_func=AppUiRunServerCopyView.as_view("AppUiRunServerCopyView"))
app_ui_test.add_url_rule("/device/server/list",
                         view_func=AppUiGetRunServerListView.as_view("AppUiGetRunServerListView"))
app_ui_test.add_url_rule("/device/server/sort",
                         view_func=AppUiChangeRunServerSortView.as_view("AppUiChangeRunServerSortView"))

app_ui_test.add_url_rule("/device/phone", view_func=AppUiRunPhoneView.as_view("AppUiRunPhoneView"))
app_ui_test.add_url_rule("/device/phone/copy", view_func=AppUiRunPhoneCopyView.as_view("AppUiRunPhoneCopyView"))
app_ui_test.add_url_rule("/device/phone/list", view_func=AppUiGetRunPhoneListView.as_view("AppUiGetRunPhoneListView"))
app_ui_test.add_url_rule("/device/phone/sort",
                         view_func=AppUiChangeRunPhoneSortView.as_view("AppUiChangeRunPhoneSortView"))