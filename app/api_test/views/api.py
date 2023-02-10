# -*- coding: utf-8 -*-
from threading import Thread

from flask import current_app as app, request, send_from_directory, g

from app.baseModel import db
from app.api_test.blueprint import api_test
from app.baseView import LoginRequiredView, NotLoginView
from utils.util.fileUtil import STATIC_ADDRESS
from utils.parse.parseExcel import parse_file_content
from utils.client.runApiTest import RunApi
from app.api_test.models.module import ApiModule as Module
from app.api_test.models.project import ApiProject as Project
from app.api_test.models.report import ApiReport as Report
from app.api_test.models.api import ApiMsg as Api
from app.api_test.models.case import ApiCase as Case
from app.api_test.models.caseSet import ApiCaseSet as CaseSet
from app.api_test.models.step import ApiStep as Step
from app.config.models.config import Config
from app.api_test.forms.api import AddApiForm, EditApiForm, RunApiMsgForm, DeleteApiForm, ApiListForm, GetApiByIdForm, \
    ApiFromForm
from config import assert_mapping_list


class ApiAssertMappingView(LoginRequiredView):

    def get(self):
        """ 获取断言类型 """
        return app.restful.success("获取成功", data=assert_mapping_list)


class ApiMethodsMappingView(LoginRequiredView):

    def get(self):
        """ 获取配置的请求方法列表 """
        return app.restful.success(
            "获取成功",
            data=[{"value": method} for method in Config.get_http_methods().split(",")]
        )


class ApiGetApiListView(LoginRequiredView):

    def get(self):
        """ 根据模块查接口list """
        form = ApiListForm().do_validate()
        return app.restful.success(data=Api.make_pagination(form))


class ApiGetApiFromView(LoginRequiredView):

    def get(self):
        """ 根据接口地址获取接口的归属信息 """
        form = ApiFromForm().do_validate()
        res_msg = "此接口归属："
        for api in form.api_list:  # 多个服务存在同一个接口地址的情况
            project = Project.get_first(id=api.project_id)
            module = Module.get_first(id=api.module_id)
            res_msg += f'【{project.name}_{module.name}_{api.name}】、'
        return app.restful.success(msg=res_msg)


class ApiGetApiToStepView(LoginRequiredView):

    def get(self):
        """ 查询哪些用例下的步骤引用了当前接口 """
        form = ApiFromForm().do_validate()
        res_msg = "以下步骤由当前接口转化："
        case_dict, case_set_dict, project_dict = {}, {}, {}  # 可能存在重复获取数据的请，获取到就存下来，一条数据只查一次库
        for api in form.api_list:  # 多个服务存在同一个接口地址的情况
            steps = Step.get_all(api_id=api.id)  # 存在一个接口在多个步骤调用的情况
            for step in steps:
                # 获取用例
                if step.case_id not in case_dict:
                    case_dict[step.case_id] = Case.get_first(id=step.case_id)
                case = case_dict[step.case_id]

                # 获取用例集
                if case.set_id not in case_set_dict:
                    case_set_dict[case.set_id] = CaseSet.get_first(id=case.set_id)
                case_set = case_set_dict[case.set_id]

                # 获取步骤
                if case_set.project_id not in project_dict:
                    project_dict[case_set.project_id] = Project.get_first(id=case_set.project_id)
                project = project_dict[case_set.project_id]

                res_msg += f'【{project.name}_{case_set.name}_{case.name}】、'
        return app.restful.success(msg=res_msg)


class ApiGetApiUploadView(NotLoginView):

    def post(self):
        """ 从excel中导入接口 """
        file, module, user_id = request.files.get("file"), Module.get_first(id=request.form.get("id")), g.user_id
        if not module:
            return app.restful.fail("模块不存在")
        if file and file.filename.endswith("xls"):
            excel_data = parse_file_content(file.read())  # [{"请求类型": "get", "接口名称": "xx接口", "addr": "/api/v1/xxx"}]
            with db.auto_commit():
                for api_data in excel_data:
                    new_api = Api()
                    for key, value in api_data.items():
                        if hasattr(new_api, key):
                            setattr(new_api, key, value)
                    new_api.method = api_data.get("method", "post").upper()
                    new_api.num = new_api.get_insert_num(module_id=module.id)
                    new_api.project_id = module.project_id
                    new_api.module_id = module.id
                    new_api.create_user = user_id
                    db.session.add(new_api)
            return app.restful.success("接口导入成功")
        return app.restful.fail("请上传后缀为xls的Excel文件")


class ApiTemplateDownloadView(LoginRequiredView):

    def get(self):
        """ 下载接口导入模板 """
        return send_from_directory(STATIC_ADDRESS, "接口导入模板.xls", as_attachment=True)


class ApiRunApiMsgView(LoginRequiredView):

    def post(self):
        """ 运行接口 """
        form = RunApiMsgForm().do_validate()
        api, api_list = form.api_list[0], form.api_list
        report = Report.get_new_report(
            name=api.name,
            run_type="api",
            env=form.env_code.data,
            create_user=g.user_id,
            project_id=form.projectId.data
        )

        # 新起线程运行接口
        Thread(
            target=RunApi(
                project_id=form.projectId.data,
                run_name=report.name,
                api_ids=api_list,
                report_id=report.id,
                env_code=form.env_code.data
            ).run_case
        ).start()
        return app.restful.success(msg="触发执行成功，请等待执行完毕", data={"report_id": report.id})


class ApiChangeApiSortView(LoginRequiredView):

    def put(self):
        """ 修改接口的排序 """
        Api.change_sort(request.json.get("List"), request.json.get("pageNum"), request.json.get("pageSize"))
        return app.restful.success(msg="修改排序成功")


class ApiMsgView(LoginRequiredView):
    """ 接口信息 """

    def get(self):
        """ 获取接口 """
        form = GetApiByIdForm().do_validate()
        return app.restful.success(data=form.api.to_dict())

    def post(self):
        """ 新增接口 """
        form = AddApiForm().do_validate()
        form.num.data = Api.get_insert_num(module_id=form.module_id.data)
        new_api = Api().create(form.data)
        return app.restful.success(f'接口【{form.name.data}】新建成功', data=new_api.to_dict())


    def put(self):
        """ 修改接口 """
        form = EditApiForm().do_validate()
        form.api.update(form.data)
        return app.restful.success(f'接口【{form.name.data}】修改成功', form.api.to_dict())

    def delete(self):
        """ 删除接口 """
        form = DeleteApiForm().do_validate()
        form.api.delete()
        return app.restful.success(f'接口【{form.api.name}】删除成功')


api_test.add_url_rule("/apiMsg", view_func=ApiMsgView.as_view("ApiMsgView"))
api_test.add_url_rule("/apiMsg/run", view_func=ApiRunApiMsgView.as_view("ApiRunApiMsgView"))
api_test.add_url_rule("/apiMsg/list", view_func=ApiGetApiListView.as_view("ApiGetApiListView"))
api_test.add_url_rule("/apiMsg/sort", view_func=ApiChangeApiSortView.as_view("ApiChangeApiSortView"))
api_test.add_url_rule("/apiMsg/upload", view_func=ApiGetApiUploadView.as_view("ApiGetApiUploadView"))
api_test.add_url_rule("/apiMsg/methods", view_func=ApiMethodsMappingView.as_view("ApiMethodsMappingView"))
api_test.add_url_rule("/apiMsg/from", view_func=ApiGetApiFromView.as_view("ApiGetApiFromView"))
api_test.add_url_rule("/apiMsg/assertMapping", view_func=ApiAssertMappingView.as_view("ApiAssertMappingView"))
api_test.add_url_rule("/apiMsg/toStep", view_func=ApiGetApiToStepView.as_view("ApiGetApiToStepView"))
api_test.add_url_rule("/apiMsg/template/download", view_func=ApiTemplateDownloadView.as_view("ApiTemplateDownloadView"))
