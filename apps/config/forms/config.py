import json
from typing import Optional

from pydantic import Field, field_validator, ValidationInfo
from selenium.webdriver.common.keys import Keys

from ...base_form import BaseForm, PaginationForm, required_str_field
from ..model_factory import Config
import config


class GetConfigListForm(PaginationForm):
    """ 查找配置form """
    type: Optional[str] = Field(None, title="配置类型")
    name: Optional[str] = Field(None, title="配置名")
    value: Optional[str] = Field(None, title="配置值")
    create_user: Optional[str] = Field(None, title="创建者")

    def get_query_filter(self, *args, **kwargs):
        """ 查询条件 """
        filter_list = []
        if self.type:
            filter_list.append(Config.type == int(self.type))
        if self.name:
            filter_list.append(Config.name.like(f'%{self.name}%'))
        if self.value:
            filter_list.append(Config.value.like(f'%{self.value}%'))
        if self.create_user:
            filter_list.append(Config.create_user == self.create_user)
        return filter_list


class GetConfigValueForm(BaseForm):
    """ 获取配置 """

    id: Optional[int] = Field(None, title="配置id")
    code: Optional[str] = Field(None, title="配置名")

    @field_validator("id")
    def validate_id(cls, value):
        if value:
            conf = cls.validate_data_is_exist("配置不存在", Config, id=value)
            setattr(cls, 'conf', conf.value)
        return value

    @field_validator("code")
    def validate_code(cls, value, info: ValidationInfo):
        if not info.data["id"]:
            cls.validate_is_true(value, '配置id或配置code必传')
            if value.startswith('_') is False and hasattr(config, value):  # config.py中的配置
                conf = getattr(config, value)
            elif value == "ui_key_board_code":
                conf = {key: f'按键【{key}】' for key in dir(Keys) if key.startswith('_') is False}
            else:
                conf_data = cls.validate_data_is_exist("配置不存在", Config, name=value)
                try:
                    conf = json.loads(conf_data.value)
                except:
                    conf = conf_data.value
            setattr(cls, 'conf', conf)
        return value


class GetSkipIfConfigForm(BaseForm):
    """ 获取跳过类型配置 """

    test_type: str = required_str_field(title="测试类型")
    type: str = required_str_field(title="跳过类型")

    @field_validator("type")
    def validate_type(cls, value, info: ValidationInfo):
        data = [{"label": "运行环境", "value": "run_env"}]
        if info.data["test_type"] == "appUi":
            data += [{"label": "运行服务器", "value": "run_server"}, {"label": "运行设备", "value": "run_device"}]
        if value == "step":
            data += [{"label": "自定义变量", "value": "variable"}, {"label": "自定义函数", "value": "func"}]
        setattr(cls, 'data', data)
        return value


class GetFindElementByForm(BaseForm):
    """ 获取定位方式数据源 """

    test_type: str = required_str_field(title="测试类型")

    @field_validator("test_type")
    def validate_type(cls, value):
        if value == "appUi":
            data = config.find_element_option + [
                {"label": "根据元素范围坐标定位", "value": "bounds"},
                {"label": "accessibility_id", "value": "accessibility id"}
            ]
        else:
            data = config.find_element_option
        setattr(cls, 'data', data)
        return value


class GetConfigForm(BaseForm):
    """ 获取配置表单校验 """
    id: int = Field(..., title="配置id")

    @field_validator("id")
    def validate_id(cls, value):
        conf = cls.validate_data_is_exist("配置不存在", Config, id=value)
        setattr(cls, 'conf', conf)
        return value


class DeleteConfigForm(GetConfigForm):
    """ 删除配置表单校验 """


class PostConfigForm(BaseForm):
    """ 新增配置表单校验 """
    name: str = required_str_field(title="配置名")
    value: str = required_str_field(title="配置值")
    type: int = Field(..., title="配置类型 id")
    desc: Optional[str] = Field(title="备注")


class PutConfigForm(GetConfigForm, PostConfigForm):
    """ 修改配置表单校验 """
