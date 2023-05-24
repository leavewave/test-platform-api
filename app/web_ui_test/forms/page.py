# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import Length, DataRequired, ValidationError

from app.baseForm import BaseForm
from app.web_ui_test.models.element import WebUiElement as Element
from app.web_ui_test.models.page import WebUiPage as Page
from app.web_ui_test.models.module import WebUiModule as Module
from app.web_ui_test.models.project import WebUiProject as Project


class AddPageForm(BaseForm):
    """ 添加页面信息的校验 """
    project_id = StringField(validators=[DataRequired("项目id必传")])
    module_id = StringField(validators=[DataRequired("模块id必传")])

    page_list = StringField(validators=[DataRequired("页面必传")])

    def validate_project_id(self, field):
        """ 校验项目id """
        project = self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)
        setattr(self, "project", project)

    def validate_module_id(self, field):
        """ 校验模块id """
        self.validate_data_is_exist(f"id为【{field.data}】的模块不存在", Module, id=field.data)

    def validate_page_list(self, field):
        """ 校验同一模块下页面名不重复 """
        name_list = []
        for index, page in enumerate(field.data):
            page_name = page.get("name")
            self.validate_data_is_true(f'第【{index + 1}】行，页面名必传', page_name)
            if page_name in name_list:
                raise ValidationError(f'第【{index + 1}】行，与第【{name_list.index(page_name) + 1}】行，页面名重复')
            self.validate_data_is_not_exist(
                f"当前模块下，名为【{page_name}】的页面已存在",
                Page,
                name=page_name,
                module_id=self.module_id.data
            )


class EditPageForm(AddPageForm):
    """ 修改页面信息 """
    page_list = None
    id = IntegerField(validators=[DataRequired("页面id必传")])
    name = StringField(validators=[DataRequired("页面名必传"), Length(1, 255, "页面名长度为1~255位")])
    desc = StringField()
    addr = StringField()
    num = StringField()

    def validate_id(self, field):
        """ 校验页面id已存在 """
        old = self.validate_data_is_exist(f"id为【{field.data}】的页面不存在", Page, id=field.data)
        setattr(self, "old", old)

    def validate_name(self, field):
        """ 校验页面名不重复 """
        self.validate_data_is_not_repeat(
            f"当前模块下，名为【{field.data}】的页面已存在",
            Page,
            self.id.data,
            name=field.data,
            module_id=self.module_id.data
        )


class ValidateProjectId(BaseForm):
    """ 校验项目id """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])

    def validate_projectId(self, field):
        """ 校验项目id """
        self.validate_data_is_exist(f"id为【{field.data}】的项目不存在", Project, id=field.data)


class PageListForm(BaseForm):
    """ 查询页面信息 """
    moduleId = IntegerField(validators=[DataRequired("请选择模块")])
    name = StringField()
    pageNum = IntegerField()
    pageSize = IntegerField()


class GetPageById(BaseForm):
    """ 待编辑信息 """
    id = IntegerField(validators=[DataRequired("页面id必传")])

    def validate_id(self, field):
        page = self.validate_data_is_exist(f"id为【{field.data}】的页面不存在", Page, id=field.data)
        setattr(self, "page", page)


class DeletePageForm(GetPageById):
    """ 删除页面 """

    def validate_id(self, field):
        # 页面存在
        page = self.validate_data_is_exist(f"id为【{field.data}】的页面不存在", Page, id=field.data)

        # 页面下没有元素
        self.validate_data_is_not_exist("当前页面下有元素，请先删除元素，再删除页面", Element, page_id=field.data)

        # 校验页面是否被测试用例引用
        # case_data = Step.get_first(api_id=field.data)
        # if case_data:
        #     case = Case.get_first(id=case_data.case_id)
        #     raise ValidationError(f"用例【{case.name}】已引用此页面，请先解除引用")

        self.validate_data_is_true(
            "不能删除别人项目下的页面",
            Project.is_can_delete(Module.get_first(id=page.module_id).project_id, page)
        )

        setattr(self, "page", page)
