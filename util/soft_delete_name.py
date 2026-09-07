import uuid


def tombstone_unique_name(original: str) -> str:
    """
    为软删除记录生成墓碑名，释放原唯一名称。
    格式为「原名__」后接 32 位小写十六进制 UUID，不含连字符。
    :param original: 删除前的业务名称
    :return: 不会与合法新建名称冲突的占位名
    """
    return f"{original}__{uuid.uuid4().hex}"
