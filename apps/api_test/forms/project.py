# -*- coding: utf-8 -*-
from typing import Optional, Union, List

import requests
import validators
from flask import g
from sqlalchemy import or_
from pydantic import field_validator, ValidationInfo

from ...base_form import BaseForm, Field, PaginationForm, ValidateModel, HeaderModel, required_str_field
from ..model_factory import ApiProject as Project, ApiProjectEnv as ProjectEnv, ApiModule as Module, \
    ApiCaseSuite as CaseSuite, ApiTask as Task
from ...system.models.user import User
from ...assist.models.script import Script


class GetProjectListForm(PaginationForm):
    """ 查找服务form """
    name: Optional[str] = Field(None, title="服务名")
    manager: Optional[Union[int, str]] = Field(None, title="负责人")
    business_id: Optional[int] = Field(None, title="所属业务线")
    create_user: Optional[Union[int, str]] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.business_id:  # 传了业务线id，就获取对应的业务线的服务
            filter_list.append(Project.business_id == self.business_id)
        else:
            if User.is_not_admin():  # 非管理员
                filter_list.append(Project.business_id.in_(g.business_list))
        if self.name:
            filter_list.append(Project.name.like(f'%{self.name}%'))
        if self.manager:
            filter_list.append(Project.manager == self.manager)
        if self.business_id:
            filter_list.append(Project.business_id == self.business_id)
        if self.create_user:
            filter_list.append(Project.create_user == self.create_user)
        return filter_list


class GetProjectForm(BaseForm):
    """ 获取具体服务信息 """
    id: int = Field(..., title='服务id')

    @field_validator("id")
    def validate_id(cls, value):
        project = cls.validate_data_is_exist("服务不存在", Project, id=value)
        setattr(cls, "project", project)
        return value


class DeleteProjectForm(GetProjectForm):
    """ 删除服务 """

    @field_validator("id")
    def validate_id(cls, value):
        cls.validate_is_true("不能删除别人负责的服务", Project.is_can_delete(value))
        cls.validate_is_false(
            Module.db.session.query(Module.id).filter(Module.project_id == value).first(), '服务下有模块,不允许删除')
        cls.validate_is_false(
            CaseSuite.db.session.query(CaseSuite.id).filter(CaseSuite.project_id == value).first(),
            '服务下有用例集,不允许删除')
        cls.validate_is_false(
            Task.db.session.query(Task.id).filter(Task.project_id == value).first(), '服务下有任务，不允许删除')
        return value


class AddProjectForm(BaseForm):
    """ 添加服务参数校验 """
    name: str = required_str_field(title="服务名称")
    manager: int = Field(..., title="负责人")
    business_id: int = Field(..., title="业务线")
    swagger: Optional[Union[str, None]] = Field(None, title="swagger地址")
    script_list: Optional[list[int]] = Field([], title="脚本文件")

    @field_validator("swagger")
    def validate_swagger(cls, value):
        """ 校验swagger地址是否正确 """
        if value:
            cls.validate_is_true("swagger地址不正确，请输入正确地址", validators.url(value) is True)
            cls.validate_is_true("请输入获取swagger数据的地址，不要输入swagger-ui地址", "swagger-ui.htm" not in value)
        return value


class EditProjectForm(GetProjectForm, AddProjectForm):
    """ 修改服务参数校验 """


class GetEnvForm(BaseForm):
    """ 获取服务环境form """
    project_id: int = Field(..., title="服务id")
    env_id: int = Field(..., title="环境id")

    @field_validator('project_id', 'env_id')
    def validate_env_id(cls, value, info: ValidationInfo):
        if info.field_name == 'env_id':
            project_id = info.data["project_id"]
            env_data = ProjectEnv.get_first(project_id=project_id, env_id=value)
            if not env_data:  # 如果没有就插入一条记录， 并且自动同步当前服务已有的环境数据
                project_other_env = ProjectEnv.get_first(project_id=project_id)
                if project_other_env:
                    insert_env_data = project_other_env.to_dict()
                    insert_env_data["env_id"] = value
                else:
                    insert_env_data = {"env_id": value, "project_id": project_id}
                ProjectEnv.model_create(insert_env_data)
            setattr(cls, "env_data", env_data)
        return value


class EditEnv(GetEnvForm):
    """ 修改环境 """
    id: int = Field(..., title='环境数据id')
    host: str = required_str_field(title='域名')
    variables: List[ValidateModel] = Field(title="变量")
    headers: List[HeaderModel] = Field(title="头部信息")

    @field_validator('id')
    def validate_id(cls, value):
        project_env = cls.validate_data_is_exist("环境不存在", ProjectEnv, id=value)
        setattr(cls, 'project_env', project_env)
        return value

    @field_validator('project_id')
    def validate_project_id(cls, value, values):
        project = cls.validate_data_is_exist("服务不存在", Project, id=value)
        all_func_name = Script.get_func_by_script_id(project.script_list)
        setattr(cls, 'all_func_name', all_func_name)
        return value

    @field_validator('host')
    def validate_host(cls, value):
        try:
            res = requests.get(value, timeout=5)
            if res.status_code >= 500:
                raise
        except:
            raise ValueError(f"环境地址【{value}】不可访问，请确认")
        return value

    @field_validator('env_id')
    def validate_env_id(cls, value):
        return value

    @field_validator('variables')
    def validate_variables(cls, value):
        """ 公共变量参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        all_variables = {variable.key: variable.value for variable in value if variable.key}
        variables = [variable.model_dump() for variable in value]
        cls.validate_variable_format(variables)  # 校验格式
        cls.validate_func(getattr(cls, 'all_func_name'), content=cls.dumps(variables))  # 校验引用的自定义函数
        cls.validate_variable(all_variables, cls.dumps(variables), "自定义变量")  # 校验变量
        setattr(cls, 'all_variables', all_variables)
        return value

    @field_validator('headers')
    def validate_headers(cls, value):
        """ 头部参数的校验
        1.校验是否存在引用了自定义函数但是没有引用脚本文件的情况
        2.校验是否存在引用了自定义变量，但是自定义变量未声明的情况
        """
        headers = [header.model_dump() for header in value]
        cls.validate_header_format(headers)  # 校验格式
        cls.validate_func(getattr(cls, 'all_func_name'), content=cls.dumps(headers))  # 校验引用的自定义函数
        cls.validate_variable(getattr(cls, 'all_variables'), cls.dumps(headers), "头部信息")  # 校验引用的变量
        return value


class SynchronizationEnvForm(BaseForm):
    """ 同步环境form """
    project_id: int = Field(..., title="服务id")
    env_from: int = Field(..., title="环境数据源")
    env_to: list = required_str_field(title="要同步到环境")

    @field_validator('project_id')
    def validate_project_id(cls, value):
        project = cls.validate_data_is_exist("服务不存在", Project, id=value)
        setattr(cls, "project", project)
        return value

    @field_validator('env_from')
    def validate_env_from(cls, value):
        env_from_data = cls.validate_data_is_exist(
            "环境不存在", ProjectEnv, project_id=getattr(cls, 'project').id, env_id=value)
        setattr(cls, "env_from_data", env_from_data)
        return value