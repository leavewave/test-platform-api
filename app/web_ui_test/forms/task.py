# -*- coding: utf-8 -*-
import validators
from wtforms import StringField, IntegerField
from wtforms.validators import ValidationError, DataRequired
from crontab import CronTab

from app.baseForm import BaseForm
from app.config.models.config import Config
from app.web_ui_test.models.task import WebUiTask as Task
from app.web_ui_test.models.project import WebUiProject as Project


def validate_email(email_server, email_from, email_pwd, email_to):
    """ 发件邮箱、发件人、收件人、密码 """
    if not email_server:
        raise ValidationError('选择了要邮件接收，则发件邮箱项目器必填')

    if not email_to or not email_from or not email_pwd:
        raise ValidationError('选择了要邮件接收，则发件人、收件人、密码3个必须有值')

    # 校验发件邮箱
    if email_from and not validators.email(email_from.strip()):
        raise ValidationError(f'发件人邮箱【{email_from}】格式错误')

    # 校验收件邮箱
    for mail in email_to.split(';'):
        mail = mail.strip()
        if mail and not validators.email(mail):
            raise ValidationError(f'收件人邮箱【{mail}】格式错误')


def validate_webhook(we_chat=None, ding_ding=None):
    """ 校验webhook地址是否合法 """
    if not we_chat and not ding_ding:
        raise ValidationError(f'选择了要通过机器人发送报告，则webhook地址必填')

    if (we_chat and not we_chat.startswith('https://')) or (ding_ding and not ding_ding.startswith('https://')):
        raise ValidationError(f'webhook地址错误:【{we_chat or ding_ding}】')


class AddTaskForm(BaseForm):
    """ 添加定时任务的校验 """
    project_id = IntegerField(validators=[DataRequired('请选择项目')])
    set_ids = StringField()
    case_ids = StringField()
    env = StringField(validators=[DataRequired('请选择要运行的环境')])
    name = StringField(validators=[DataRequired('任务名不能为空')])
    we_chat = StringField()
    ding_ding = StringField()
    is_send = StringField(validators=[DataRequired('请选择是否发送报告')])
    send_type = StringField()
    email_server = StringField()
    email_to = StringField()
    email_from = StringField()
    email_pwd = StringField()
    cron = StringField()
    num = StringField()
    call_back = StringField()
    is_async = IntegerField()

    def validate_is_send(self, field):
        """ 发送报告类型 1.不发送、2.始终发送、3.仅用例不通过时发送 """
        if field.data in ['2', '3']:
            if self.send_type.data == 'we_chat':
                validate_webhook(self.we_chat.data)
            elif self.send_type.data == 'ding_ding':
                validate_webhook(ding_ding=self.ding_ding.data)
            elif self.send_type.data == 'email':
                validate_email(self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data)
            elif self.send_type.data == 'all':
                validate_webhook(self.we_chat.data, self.ding_ding.data)
                validate_email(self.email_server.data, self.email_from.data, self.email_pwd.data, self.email_to.data)

    def validate_cron(self, field):
        """ 校验cron格式 """
        try:
            if len(field.data.strip().split(' ')) == 6:
                field.data += ' *'
            CronTab(field.data)
        except Exception as error:
            raise ValidationError(f'时间配置【{field.data}】错误，需为cron格式, 请检查')

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_exist(
            f'当前项目中，任务名【{field.data}】已存在',
            Task,
            project_id=self.project_id.data,
            name=field.data
        )


class HasTaskIdForm(BaseForm):
    """ 校验任务id已存在 """
    id = IntegerField(validators=[DataRequired('任务id必传')])

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f'任务id【{field.data}】不存在', Task, id=field.data)
        setattr(self, 'task', task)


class DisableTaskIdForm(HasTaskIdForm):
    """ 禁用任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f'任务id【{field.data}】不存在', Task, id=field.data)
        setattr(self, 'task', task)

        self.validate_data_is_true(f'任务【{task.name}】的状态不为启用中', task.is_enable())


class RunTaskForm(HasTaskIdForm):
    """ 运行任务 """
    env = StringField()
    is_async = IntegerField()

    def validate_env(self, field):
        """ 检验环境 """
        if field.data:
            self.validate_data_is_true(f'环境【{field.data}】不存在', field.data in Config.get_run_test_env())


class EditTaskForm(AddTaskForm, HasTaskIdForm):
    """ 编辑任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f'任务id【{field.data}】不存在', Task, id=field.data)
        self.validate_data_is_true(f'任务【{task.name}】的状态不为禁用中，请先禁用再修改', task.is_disable())
        setattr(self, 'task', task)

    def validate_name(self, field):
        """ 校验任务名不重复 """
        self.validate_data_is_not_repeat(
            f'当前项目中，任务名【{field.data}】已存在',
            Task,
            self.id.data,
            project_id=self.project_id.data,
            name=field.data
        )


class GetTaskListForm(BaseForm):
    """ 获取任务列表 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    pageNum = IntegerField()
    pageSize = IntegerField()


class FindTaskForm(BaseForm):
    """ 查找任务信息 """
    projectId = IntegerField(validators=[DataRequired('项目id必传')])
    taskName = StringField()
    page = IntegerField()
    sizePage = IntegerField()

    def validate_taskName(self, field):
        """ 校验任务名存在 """
        task_select = Task.query.filter_by(project_id=self.projectId.data)
        if field.data:
            task_select = task_select.filter(Task.name.like('%{}%'.format(field.data)))
            self.validate_data_is_true(f'名为【{field.data}】的任务不存在', task_select)
        setattr(self, 'task_filter', task_select)


class DeleteTaskIdForm(HasTaskIdForm):
    """ 删除任务 """

    def validate_id(self, field):
        """ 校验id存在 """
        task = self.validate_data_is_exist(f'任务id【{field.data}】不存在', Task, id=field.data)
        self.validate_data_is_true(f'请先禁用任务【{task.name}】', task.is_disable())
        self.validate_data_is_true(f'不能删除别人的数据【{task.name}】', Project.is_can_delete(task.project_id, task))
        setattr(self, 'task', task)