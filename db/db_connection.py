import pymysql
from contextlib import contextmanager
from .db_config import DB_CONFIG


@contextmanager
def get_connection():
    """获取数据库连接的上下文管理器，自动处理提交/回滚/关闭"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


@contextmanager
def get_cursor():
    """获取游标的上下文管理器，返回字典格式结果"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            yield cursor
        finally:
            cursor.close()