# -*- coding: utf-8 -*-
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from crontab import CronTab

from app.baseForm import BaseForm
from app.config.models.runEnv import RunEnv
from app.web_ui_test.models.task import WebUiTask as Task
from app.web_ui_test.models.project import WebUiProject as Project


class AddTaskForm(BaseForm):
    """ 添加定时任务的校验 """
    project_id = IntegerField(validators=[DataRequired("请选择项目")])
    suite_ids = StringField()
    case_ids = StringField()
    env_list = StringField(validators=[DataRequired("请选择要运行的环境")])
    name = StringField(validators=[DataRequired("任务名不能为空")])
    is_send = StringField(validators=[DataRequired("请选择是否发送报告")])
    receive_type = StringField()
    webhook_list = StringField()
    email_server = StringField()
    email_to = StringField()
    email_from = StringField()
    email_pwd = StringField()
    cron = StringField()
    num = StringField()
    conf = StringField()
    call_back = StringField()
    is_async = IntegerField()

    def validate_is_send(self, field):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if field.data in ["2", "3"]:
            if self.receive_type.data in ("ding_ding", "we_chat"):
                self.validate_data_is_true('选择了要通过机器人发送报告，则webhook地址必填', self.webhook_list.data)
            elif self.receive_type.data == "email":
                self.validate_email(
                    self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data
                )

    def validate_cron(self, field):
        """ 校验cron格式 """
        try:
            if len(field.data.strip().split(" ")) == 6:
                field.data += " *"
            CronTab(field.data)
        except Exception as error:
            raise ValidationError(f"时间配置【{field.data}】错误，需为cron格式, 请检查")
        if field.data.startswith("*"):  # 每秒钟
            raise ValidationError(f"设置的执行频率过高，请重新设置")

    def validate_conf(self, field):
        """ 校验任务运行配置 """
        self.validate_data_is_true('请选择运行浏览器', field.data.get("browser"))

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_exist(
            f"当前项目中，任务名【{field.data}】已存在",
            Task,
            project_id=self.project_id.data,
            name=field.data
        )


class HasTaskIdForm(BaseForm):
    """ 校验任务id已存在 """
    id = IntegerField(validators=[DataRequired("任务id必传")])

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        setattr(self, "task", task)


class DisableTaskIdForm(HasTaskIdForm):
    """ 禁用任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        setattr(self, "task", task)

        self.validate_data_is_true(f"任务【{task.name}】的状态不为启用中", task.is_enable())


class RunTaskForm(HasTaskIdForm):
    """ 运行任务 """
    env_list = StringField()
    is_async = IntegerField()
    browser = StringField()
    trigger_type = StringField()  # pipeline 代表是流水线触发，跑完过后会发送测试报告
    extend = StringField()  # 运维传过来的扩展字段，接收的什么就返回什么

    def validate_env(self, field):
        """ 检验环境 """
        if field.data:
            self.validate_data_is_true(f"环境【{field.data}】不存在", RunEnv.get_first(code=field.data))

    def validate_browser(self, field):
        """ 浏览器类型 """
        field.data = field.data or self.loads(self.task.conf).get("browser", "chrome")
        self.validate_data_is_true('请设置运行浏览器', field.data)


class EditTaskForm(AddTaskForm, HasTaskIdForm):
    """ 编辑任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        self.validate_data_is_true(f"任务【{task.name}】的状态不为禁用中，请先禁用再修改", task.is_disable())
        setattr(self, "task", task)

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_repeat(
            f"当前项目中，任务名【{field.data}】已存在",
            Task,
            self.id.data,
            project_id=self.project_id.data,
            name=field.data
        )


class GetTaskListForm(BaseForm):
    """ 获取任务列表 """
    projectId = IntegerField(validators=[DataRequired("项目id必传")])
    pageNum = IntegerField()
    pageSize = IntegerField()


class DeleteTaskIdForm(HasTaskIdForm):
    """ 删除任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f"任务id【{field.data}】不存在", Task, id=field.data)
        self.validate_data_is_true(f"请先禁用任务【{task.name}】", task.is_disable())
        self.validate_data_is_true(f"不能删除别人的数据【{task.name}】", Project.is_can_delete(task.project_id, task))
        setattr(self, "task", task)
