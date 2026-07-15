<script setup>
import {useCurrentUser} from "@/hooks/useCurrentUser.js";

const { user, loading } = useCurrentUser();
</script>

<template>
    <div class="common-layout">
        <el-container>
            <el-header class="app-header">
                <div class="header-left">校灵通</div>
                <div class="header-center">中间</div>
                <div class="header-right">欢迎，{{ user?.username }}</div>
            </el-header>

            <el-main>
                <el-container class="app-main">
                    <div class="main-left">左边</div>
                    <div class="main-chat">聊天</div>
                </el-container>
            </el-main>

            <el-footer class="app-footer">Copyright © 2026-2026 · 校灵通</el-footer>
        </el-container>
    </div>
</template>

<style>
/* 1. 最外层容器：占满整个视口高度，使用 flex 纵向排列 */
.common-layout {
    height: 100vh;
    display: flex;
    flex-direction: column;
}

/* 2. Header：固定高度，横向排列 */
.app-header {
    height: 60px;       /* 根据实际需求调整 */
    flex-shrink: 0;     /* 防止被压缩 */
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 0 20px;
    background-color: #f5f7fa; /* 可选：添加背景色区分 */
}

.header-left {
    font-size: 20px;
    font-weight: bold;
    white-space: nowrap;
}

.header-center {
    flex: 1;
    text-align: center;
}

.header-right {
    white-space: nowrap;
}

/* 3. Main：占据除 header 和 footer 之外的所有剩余空间 */
.el-main {
    flex: 1;            /* 👈 核心：自动撑满剩余高度 */
    padding: 0;         /* 去除 el-main 默认的 20px padding，避免产生滚动条 */
    overflow: hidden;   /* 防止内容溢出导致外层出现滚动条 */
}

/* 4. Main 内部容器：横向排列，占满父级高度 */
.app-main {
    display: flex;
    height: 100%;
}

/* 5. 左侧边栏：固定 200px 宽度 */
.main-left {
    width: 200px;
    flex-shrink: 0;     /* 防止被压缩 */
    background-color: #e9ecef; /* 可选：侧边栏背景色 */
    border-right: 1px solid #dcdfe6; /* 可选：分割线 */
}

/* 6. 聊天区域：占据剩余宽度，允许内部滚动 */
.main-chat {
    flex: 1;            /* 👈 占据剩余宽度 */
    overflow-y: auto;   /* 聊天记录过多时，仅聊天区域内部滚动 */
    padding: 16px;      /* 聊天内容的内边距 */
}

/* 7. Footer：固定在底部，固定高度 */
.app-footer {
    height: 40px;       /* 根据实际需求调整 */
    flex-shrink: 0;     /* 防止被压缩 */
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f5f7fa;
    border-top: 1px solid #dcdfe6;
}
</style>