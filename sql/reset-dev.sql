-- 仅限本地开发环境使用。
-- 此脚本会永久删除 xlt 数据库中的全部数据，且必须从项目根目录通过 MySQL 客户端执行。
drop database if exists xlt;
source sql/db.sql;
