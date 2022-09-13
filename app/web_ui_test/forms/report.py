# -*- coding: utf-8 -*-

import json
import os

from wtforms import IntegerField
from wtforms.validators import DataRequired

from utils.filePath import WEB_UI_REPORT_ADDRESS
from app.baseForm import BaseForm
from app.web_ui_test.models.report import UiReport as Report


class DownloadReportForm(BaseForm):
    """ 报告下载 """
    id = IntegerField(validators=[DataRequired('请选择报告')])

    def validate_id(self, field):
        """ 校验报告是否存在 """
        report = self.validate_data_is_exist('报告不存在', Report, id=field.data)
        report_path = os.path.join(WEB_UI_REPORT_ADDRESS, f'{report.id}.txt')
        self.validate_data_is_true('报告文件不存在', os.path.exists(report_path))
        with open(report_path, 'r') as file:
            report_content = json.load(file)
        setattr(self, 'report', report)
        setattr(self, 'report_path', report_path)
        setattr(self, 'report_content', report_content)


class GetReportForm(DownloadReportForm):
    """ 查看报告 """


class DeleteReportForm(BaseForm):
    """ 删除报告 """
    id = IntegerField(validators=[DataRequired('请选择报告')])

    def validate_id(self, field):
        report = self.validate_data_is_exist('报告不存在', Report, id=field.data)
        report_path = os.path.join(WEB_UI_REPORT_ADDRESS, f'{report.id}.txt')
        self.validate_data_is_true('报告文件不存在', os.path.exists(report_path))
        setattr(self, 'report', report)
        setattr(self, 'report_path', report_path)


class FindReportForm(BaseForm):
    """ 查找报告 """
    projectId = IntegerField(validators=[DataRequired('请选择服务')])
    pageNum = IntegerField()
    pageSize = IntegerField()
