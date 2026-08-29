-- 会话名称约束增量迁移。
-- 执行前请备份数据库；本迁移会修改超长或空白历史会话名称。
-- LEFT 和 CHAR_LENGTH 按字符处理，而非按 UTF-8 字节处理。

UPDATE session
SET name = LEFT(TRIM(name), 30)
WHERE CHAR_LENGTH(TRIM(name)) > 30;

UPDATE session
SET name = '新建会话'
WHERE name IS NULL OR CHAR_LENGTH(TRIM(name)) = 0;

ALTER TABLE session
    MODIFY COLUMN name VARCHAR(30) NOT NULL DEFAULT '新建会话'
    COMMENT '会话名称';
