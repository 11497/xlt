-- 非破坏性初始化脚本：不会删除已有数据库、表或数据。
create database if not exists xlt;

use xlt;

-- 外键删除策略：
-- 1. 完全隶属于父记录、且不关联外部资源的数据使用 CASCADE。
-- 2. 需要先解绑或清理 OSS、Chroma、Elasticsearch 的数据使用 RESTRICT。

create table user (
    id int auto_increment primary key comment '用户id',
    username varchar(255) not null unique comment '用户名',
    password varchar(255) not null default '$argon2id$v=19$m=65536,t=3,p=4$sFFvvH2qZYyhTBvJs0vx5A$nfy24ZwxcDs6A/VKWLKZlofCg3KENlL9dhExvnByGc0' comment 'Argon2id 密码哈希',
    is_admin tinyint default 0 comment '是否管理员，0为普通用户，1为管理员'
) comment '用户';

create table session (
    id int auto_increment primary key comment '会话id',
    user_id int not null comment '用户id',
    name varchar(255) not null default '新建会话' comment '会话名称',
    create_time datetime default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间',
    constraint fk_session_user
        foreign key (user_id) references user(id) on delete cascade
) comment '会话';

create table message (
    id int auto_increment primary key comment '消息id',
    session_id int not null comment '会话id',
    role varchar(255) not null comment '角色',
    content text comment '消息内容',
    rewritten_content text comment '重写后的内容',
    create_time datetime default current_timestamp comment '创建时间',
    constraint fk_message_session
        foreign key (session_id) references session(id) on delete cascade
) comment '消息';

create table knowledge_base (
    id int auto_increment primary key comment '知识库id',
    name varchar(255) not null unique comment '知识库名称'
) comment '知识库';

create table role (
    id int auto_increment primary key comment '角色id',
    name varchar(255) not null unique comment '角色名称'
) comment '角色';

create table role_user (
    role_id int comment '角色id',
    user_id int comment '用户id',
    primary key (role_id, user_id),
    constraint fk_role_user_role
        foreign key (role_id) references role(id) on delete restrict,
    constraint fk_role_user_user
        foreign key (user_id) references user(id) on delete restrict
) comment '角色用户关联';

create table role_knowledge_base (
    role_id int comment '角色id',
    knowledge_base_id int comment '知识库id',
    primary key (role_id, knowledge_base_id),
    constraint fk_role_knowledge_base_role
        foreign key (role_id) references role(id) on delete restrict,
    constraint fk_role_knowledge_base_knowledge_base
        foreign key (knowledge_base_id) references knowledge_base(id) on delete restrict
) comment '角色知识库关联';

create table document (
    id int auto_increment primary key comment '文档id',
    knowledge_base_id int not null comment '知识库id',
    filename varchar(255) not null comment '文档文件名',
    storage_path varchar(500) not null comment '文档存储路径',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间',
    constraint fk_document_knowledge_base
        foreign key (knowledge_base_id) references knowledge_base(id) on delete restrict
) comment '文档';

create table announcement (
    id int auto_increment primary key comment '公告id',
    title varchar(255) not null comment '公告标题',
    content longtext not null comment '公告内容',
    is_top tinyint not null default 0 comment '是否置顶，0=否，1=是',
    create_time datetime not null default current_timestamp comment '创建时间',
    update_time datetime not null default current_timestamp comment '更新时间'
) comment '公告';

create table announcement_attachment (
    id int auto_increment primary key comment '公告附件id',
    announcement_id int not null comment '公告id',
    filename varchar(255) not null comment '附件文件名',
    storage_path varchar(500) not null comment '附件存储路径',
    upload_time datetime not null default current_timestamp comment '上传时间',
    constraint fk_announcement_attachment_announcement
        foreign key (announcement_id) references announcement(id) on delete restrict
) comment '公告附件';

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

insert into role_knowledge_base (role_id, knowledge_base_id)
values (1, 1),
       (3, 3);

insert into announcement (title, content, is_top)
values ('测试公告', '这是一条测试公告', 0),
       ('测试置顶公告', '这是一条置顶公告', 1);
