drop database if exists xlt;
create database if not exists xlt;

use xlt;

drop table if exists user;
create table user (
    id int auto_increment primary key comment '用户id',
    username varchar(255) not null unique comment '用户名',
    password varchar(255) not null default '123456' comment '密码',
    is_admin boolean default 0 comment '是否管理员，0为普通用户，1为管理员'
) comment '用户';

drop table if exists session;
create table session (
    id int auto_increment primary key comment '会话id',
    user_id int not null comment '用户id'
) comment '会话';

drop table if exists message;
create table message (
    id int auto_increment primary key comment '消息id',
    session_id int not null comment '会话id',
    content text not null comment '消息内容',
    create_time datetime default current_timestamp comment '创建时间',
    foreign key (session_id) references session(id)
);

drop table if exists knowledge_base;
create table knowledge_base (
    id int auto_increment primary key comment '知识库id',
    name varchar(255) not null unique comment '知识库名称'
) comment '知识库';

drop table if exists role;
create table role (
    id int auto_increment primary key comment '角色id',
    name varchar(255) not null unique comment '角色名称'
) comment '角色';

drop table if exists role_user;
create table role_user (
    role_id int comment '角色id',
    user_id int comment '用户id',
    primary key (role_id, user_id),
    foreign key (role_id) references role(id),
    foreign key (user_id) references user(id)
) comment '角色用户关联';

drop table if exists role_knowledge_base;
create table role_knowledge_base (
    role_id int comment '角色id',
    knowledge_base_id int comment '知识库id',
    primary key (role_id, knowledge_base_id),
    foreign key (role_id) references role(id),
    foreign key (knowledge_base_id) references knowledge_base(id)
) comment '角色知识库关联';

drop table if exists document;
create table document (
    id int auto_increment primary key comment '文档id',
    knowledge_base_id int not null comment '知识库id',
    name varchar(255) not null unique comment '文档名称',
    content longtext not null comment '文档内容',
    create_time datetime default current_timestamp comment '创建时间',
    update_time datetime default current_timestamp comment '更新时间',
    foreign key (knowledge_base_id) references knowledge_base(id)
) comment '文档';

drop table if exists announcement;
create table announcement (
    id int auto_increment primary key comment '公告id',
    content longtext not null comment '公告内容',
    create_time datetime default current_timestamp comment '创建时间',
    update_time datetime default current_timestamp comment '更新时间'
) comment '公告';
