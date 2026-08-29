-- 为已有数据库增加角色-知识库权限字段。
-- 执行前请确认目标数据库中尚不存在该字段；本文件不会重建或删除数据库。
-- 目标 MySQL 版本必须支持并实际执行 CHECK 约束（MySQL 8.0.16 及以上）。
ALTER TABLE role_knowledge_base
    ADD COLUMN permission TINYINT NOT NULL DEFAULT 0
        COMMENT '权限：0=只读，1=读写',
    ADD CONSTRAINT chk_role_knowledge_base_permission
        CHECK (permission IN (0, 1));
