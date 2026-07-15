from typing import Any


class Result:
    """接口返回模型"""
    code: int
    msg: str
    data: Any

    def __init__(self, code: int = 0, msg: str = "", data: Any = None):
        self.code = code
        self.msg = msg
        self.data = data

    def success(self, msg: str = "操作成功", data: Any = None):
        """
        成功返回
        :param msg: 成功消息
        :param data: 数据
        :return: JSON 字符串
        """
        self.code = 1
        self.msg = msg
        self.data = data
        return self.json()

    def error(self, msg: str = "操作失败", data: Any = None):
        """
        错误返回
        :param msg: 错误消息
        :param data: 数据
        :return: JSON 字符串
        """
        self.code = 0
        self.msg = msg
        self.data = data
        return self.json()

    def json(self):
        """
        转换为 JSON 字符串
        :return: JSON 字符串
        """
        return {"code": self.code, "msg": self.msg, "data": self.data}