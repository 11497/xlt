-- 空环境初始化脚本：业务数据删除采用逻辑删除。
create database if not exists xlt
    default character set utf8mb4
    default collate utf8mb4_unicode_ci;

use xlt;

-- 外键删除策略：
-- 业务表统一使用 RESTRICT，避免数据库级联硬删除绕过应用层逻辑删除。
-- document_task 是异步任务状态表，不参与业务软删除。

create table user (
    id int auto_increment primary key comment '用户id',
    username varchar(255) not null unique comment '用户名',
    password varchar(255) not null comment 'Argon2id 密码哈希',
    is_admin tinyint(1) not null default 0 comment '是否管理员，0为普通用户，1为管理员',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_user_deleted (is_deleted)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '用户';

create table session (
    id int auto_increment primary key comment '会话id',
    user_id int not null comment '用户id',
    name varchar(30) not null default '新建会话' comment '会话名称',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_session_deleted (is_deleted),
    key idx_session_user_deleted (user_id, is_deleted, update_time),
    constraint fk_session_user
        foreign key (user_id) references user(id) on delete restrict
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '会话';

create table message (
    id int auto_increment primary key comment '消息id',
    session_id int not null comment '会话id',
    role varchar(16) not null comment '角色',
    content text not null comment '消息内容',
    rewritten_content text comment '重写后的内容',
    create_time datetime not null default current_timestamp comment '创建时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_message_deleted (is_deleted),
    key idx_message_session_deleted (session_id, is_deleted, create_time),
    constraint fk_message_session
        foreign key (session_id) references session(id) on delete restrict,
    constraint chk_message_role check (role in ('user', 'assistant'))
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '消息';

create table knowledge_base (
    id int auto_increment primary key comment '知识库id',
    name varchar(255) not null unique comment '知识库名称',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_knowledge_base_deleted (is_deleted)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '知识库';

create table role (
    id int auto_increment primary key comment '角色id',
    name varchar(255) not null unique comment '角色名称',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_role_deleted (is_deleted)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '角色';

create table role_user (
    role_id int not null comment '角色id',
    user_id int not null comment '用户id',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    primary key (role_id, user_id),
    key idx_role_user_deleted (is_deleted, role_id, user_id),
    constraint fk_role_user_role
        foreign key (role_id) references role(id) on delete restrict,
    constraint fk_role_user_user
        foreign key (user_id) references user(id) on delete restrict
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '角色用户关联';

create table role_knowledge_base (
    role_id int not null comment '角色id',
    knowledge_base_id int not null comment '知识库id',
    permission tinyint not null default 0 comment '权限：0=只读，1=读写',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    primary key (role_id, knowledge_base_id),
    key idx_role_knowledge_base_deleted (is_deleted, role_id, knowledge_base_id),
    constraint fk_role_knowledge_base_role
        foreign key (role_id) references role(id) on delete restrict,
    constraint fk_role_knowledge_base_knowledge_base
        foreign key (knowledge_base_id) references knowledge_base(id) on delete restrict,
    constraint chk_role_knowledge_base_permission check (permission in (0, 1))
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '角色知识库关联';

create table document (
    id int auto_increment primary key comment '文档id',
    knowledge_base_id int not null comment '知识库id',
    filename varchar(255) not null comment '文档文件名（原始文件名，仅用于展示和下载）',
    storage_path varchar(500) not null comment 'OSS对象key，使用UUID避免同名覆盖',
    status varchar(20) not null default 'pending' comment '状态：pending=待索引, indexing=索引中, ready=可用, failed=索引失败, deleting=删除中, deleted=已删除',
    error_message text null comment '最近一次失败原因',
    retry_count int not null default 0 comment '索引重试次数',
    chunk_count int null comment '实际写入的切片数',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_document_status (status),
    key idx_document_kb_status (knowledge_base_id, status),
    key idx_document_deleted (is_deleted),
    key idx_document_kb_deleted_created (knowledge_base_id, is_deleted, create_time),
    constraint fk_document_knowledge_base
        foreign key (knowledge_base_id) references knowledge_base(id) on delete restrict
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '文档';

create table document_task (
    id bigint unsigned auto_increment primary key comment '任务id',
    task_type varchar(20) not null comment '任务类型：index=索引, delete=删除, delete_kb=删除知识库',
    document_id int not null comment '文档id',
    knowledge_base_id int not null comment '知识库id',
    status varchar(20) not null default 'pending' comment '状态：pending=待处理, processing=处理中, done=完成, failed=失败',
    payload text null comment '任务参数（JSON），如 object_key、文件名',
    error_message text null comment '失败原因',
    retry_count int not null default 0 comment '已重试次数',
    max_retries int not null default 5 comment '最大重试次数',
    next_retry_at datetime null comment '下次重试时间（指数退避）',
    result_json text null comment 'Chroma/ES 删除或写入结果记录，OSS 保留不删除',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp on update current_timestamp comment '更新时间',
    claimed_by varchar(100) null comment '当前 Worker 租约标识',
    claimed_at datetime null comment '当前 Worker 租约时间',
    key idx_task_status_retry (status, next_retry_at),
    key idx_task_lease (status, claimed_at),
    key idx_task_document (document_id),
    key idx_task_kb (knowledge_base_id)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '文档索引/删除异步任务';

create table announcement (
    id int auto_increment primary key comment '公告id',
    title varchar(255) not null comment '公告标题',
    content longtext not null comment '公告内容',
    is_top tinyint not null default 0 comment '是否置顶，0=否，1=是',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_announcement_deleted_top_created (is_deleted, is_top, create_time)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '公告';

create table announcement_attachment (
    id int auto_increment primary key comment '公告附件id',
    announcement_id int not null comment '公告id',
    filename varchar(255) not null comment '附件文件名',
    storage_path varchar(500) not null comment 'OSS对象key，使用UUID避免同名覆盖',
    upload_time datetime not null default current_timestamp comment '上传时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    key idx_announcement_attachment_deleted (is_deleted),
    key idx_announcement_attachment_announcement_deleted (announcement_id, is_deleted),
    constraint fk_announcement_attachment_announcement
        foreign key (announcement_id) references announcement(id) on delete restrict
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '公告附件';

create table source_content (
    id int auto_increment primary key comment '正文id',
    content_hash char(64) not null comment 'UTF-8 SHA-256 十六进制',
    content text not null comment '切片正文，写入后不更新',
    create_time datetime not null default current_timestamp comment '首次写入时间',
    unique key uk_source_content_hash (content_hash)
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '来源正文（按内容去重）';

create table message_source (
    id int auto_increment primary key comment '来源引用id',
    message_id int not null comment 'assistant 消息id',
    session_id int not null comment '冗余会话id，便于按会话清理',
    source_content_id int not null comment '正文id',
    knowledge_base_id int not null comment '知识库id',
    document_id int not null comment '文档id',
    chunk_id varchar(64) not null comment '当时的 document_id_chunk_index',
    chunk_index int not null comment '当时的切片序号',
    filename varchar(255) not null comment '当时的文档名',
    rerank_score double null comment '精排分数',
    recall_source varchar(20) null comment 'vector 或 bm25',
    sort_order int not null default 0 comment '展示顺序',
    create_time datetime not null default current_timestamp comment '创建时间',
    is_deleted tinyint(1) not null default 0 comment '是否逻辑删除，0=否，1=是',
    deleted_at datetime null comment '逻辑删除时间',
    unique key uk_message_source_chunk (message_id, chunk_id),
    key idx_message_source_message_deleted (message_id, is_deleted),
    key idx_message_source_session_deleted (session_id, is_deleted),
    key idx_message_source_content (source_content_id),
    constraint fk_message_source_message
        foreign key (message_id) references message(id) on delete restrict,
    constraint fk_message_source_session
        foreign key (session_id) references session(id) on delete restrict,
    constraint fk_message_source_content
        foreign key (source_content_id) references source_content(id) on delete restrict,
    constraint fk_message_source_knowledge_base
        foreign key (knowledge_base_id) references knowledge_base(id) on delete restrict,
    constraint fk_message_source_document
        foreign key (document_id) references document(id) on delete restrict
) engine=InnoDB default charset=utf8mb4 collate=utf8mb4_unicode_ci comment '回答用来源引用';

insert into user (username, password, is_admin)
values ('admin', '$argon2id$v=19$m=65536,t=3,p=4$wSH04ON+NjdRsHmJ6F36fA$/g62R/uOp6WadTu1GldXdS5DxOHyALvvoDDJoTr+woU', 1),
       ('hajimi', '$argon2id$v=19$m=65536,t=3,p=4$RZwfTmZAQNO6O2ALHSJHMA$ak/qWRD7EbYH0omX//mvDtKywR7QW11hVFCceG8p9MQ', 0);

insert into role (name)
values ('新芒'),
       ('教职工'),
       ('学生');

insert into role_user (role_id, user_id)
values (1, 1),
       (3, 2);

insert into knowledge_base (name)
values ('图书馆'),
       ('教职工'),
       ('学生');

insert into role_knowledge_base (role_id, knowledge_base_id, permission)
values (1, 1, 0),
       (3, 3, 0);

insert into announcement (title, content, is_top)
values ('测试公告', '这是一条测试公告', 0),
       ('测试置顶公告', '这是一条置顶公告', 1);
