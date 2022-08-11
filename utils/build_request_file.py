# -*- coding: utf-8 -*-
import os

from utils.globalVariable import CASE_FILE_ADDRESS, CONTENT_TYPE


def build_file_path(filename):
    """ 拼装要上传文件的路径 """
    return os.path.join(CASE_FILE_ADDRESS, filename)


def build_request_file(file_dict):
    """ 构建文件请求对象 """
    request_file = {}
    for key, value in file_dict.items():
        request_file[key] = (
            value,  # 文件名
            open(build_file_path(value), 'rb'),  # 文件流
            CONTENT_TYPE[f".{value.split('.')[-1]}"]  # content-type，根据文件后缀取
        )
    return request_file