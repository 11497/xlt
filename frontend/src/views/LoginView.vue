<script setup>
import {ref, onMounted} from 'vue';
import {userLogin} from "@/api/user.js";
import {ElMessage} from "element-plus";
import {useRouter} from "vue-router";
import {ArrowRight, Lock, User} from '@element-plus/icons-vue';
import campusLibrary from '@/assets/images/campus-library.png';
import xltIcon from '@/assets/xlt-icon.svg';

let userForm = ref({username: "", password: ""});
const loginFormRef = ref(null);
const router = useRouter();
const loginLoading = ref(false);

// 表单校验规则
const rules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 4, max: 15, message: '用户名长度必须在4-15位之间', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 6, max: 20, message: '密码长度必须在6-20位之间', trigger: 'blur' }
    ]
};

// 页面加载时检查是否已登录
onMounted(async () => {
    const loginUser = localStorage.getItem('loginUser');
    if (loginUser) {
        await router.push({path: '/chat'});
    }
});

// 登录
const login = async () => {
    // 表单校验
    const valid = await loginFormRef.value.validate().catch(() => false);
    if (!valid) return;

    loginLoading.value = true;
    try {
      const result = await userLogin({
        username: userForm.value.username,
        password: userForm.value.password
      });
      if (result.code) {
        // 1. 提示信息
        ElMessage.success('登录成功');

        // 2. 存储当前登录员工的信息
        localStorage.setItem('loginUser', JSON.stringify(result.data));

        // 3. 跳转页面 - 首页
        await router.push({path: '/chat'});
      } else {
        ElMessage.error(result.msg);
      }
    } finally {
      loginLoading.value = false;
    }
}
</script>

<template>
    <main class="login-page">
      <section class="login-visual" :style="{ backgroundImage: `url(${campusLibrary})` }" aria-label="校园图书馆">
        <div class="visual-copy">
          <h1>知识在校园里流动</h1>
          <p>连接可信资料、校园公告与智能问答，让每一次查找都更有依据。</p>
        </div>
      </section>
      <section class="login-panel">
        <div class="login-form">
          <div class="login-brand">
            <img class="login-brand-mark" :src="xltIcon" alt="" />
            <div><strong>校灵通</strong><span>校园知识工作台</span></div>
          </div>
          <div class="login-heading">
            <h2>欢迎回来</h2>
          </div>
          <el-form ref="loginFormRef" :model="userForm" :rules="rules" label-position="top" @submit.prevent="login">
            <el-form-item label="用户名" prop="username">
              <el-input v-model="userForm.username" size="large" placeholder="请输入用户名" autocomplete="username" :prefix-icon="User" />
            </el-form-item>
            <el-form-item label="密码" prop="password">
              <el-input v-model="userForm.password" size="large" type="password" placeholder="请输入密码" autocomplete="current-password" :prefix-icon="Lock" show-password @keyup.enter="login" />
            </el-form-item>
            <el-button class="login-button" type="primary" size="large" native-type="submit" :loading="loginLoading">
              <span>{{ loginLoading ? '正在登录' : '进入工作台' }}</span><el-icon v-if="!loginLoading"><ArrowRight /></el-icon>
            </el-button>
          </el-form>
          <p class="login-footnote">校园知识问答与管理服务</p>
        </div>
      </section>
    </main>
</template>

<style scoped>
.login-page { min-height: 100dvh; display: grid; grid-template-columns: minmax(0, 1.35fr) minmax(420px, .65fr); background: #fff; }
.login-visual { position: relative; min-height: 100dvh; background-position: center; background-size: cover; }
.login-visual::after { content: ""; position: absolute; inset: 0; background: linear-gradient(180deg, rgb(10 30 34 / 8%) 28%, rgb(8 28 29 / 76%) 100%); }
.visual-copy { position: absolute; z-index: 1; left: clamp(28px, 6vw, 88px); right: clamp(28px, 8vw, 120px); bottom: clamp(40px, 9vh, 100px); max-width: 680px; color: #fff; }
.visual-copy h1 { margin: 0 0 12px; font-size: clamp(34px, 4.2vw, 58px); line-height: 1.14; letter-spacing: 0; }
.visual-copy p { max-width: 560px; margin: 0; color: rgb(255 255 255 / 86%); font-size: 16px; line-height: 1.8; }
.login-panel { min-width: 0; padding: 48px clamp(32px, 5vw, 72px); display: flex; align-items: center; justify-content: center; }
.login-form { width: 100%; max-width: 420px; }
.login-brand { display: flex; align-items: center; gap: 12px; margin-bottom: clamp(48px, 10vh, 88px); }
.login-brand-mark { width: 42px; height: 42px; flex: 0 0 42px; }
.login-brand div { display: flex; flex-direction: column; gap: 3px; }
.login-brand strong { font-size: 20px; }
.login-brand span { color: var(--color-text-secondary); font-size: 12px; }
.login-heading { margin-bottom: 28px; }
.login-heading h2 { margin: 0; font-size: 28px; font-weight: 650; }
.login-form :deep(.el-form-item) { margin-bottom: 22px; }
.login-form :deep(.el-form-item__label) { padding-bottom: 7px; color: #46525e; font-weight: 600; }
.login-button { width: 100%; margin-top: 8px; }
.login-button .el-icon { margin-left: 8px; }
.login-footnote { margin: 28px 0 0; color: var(--color-text-muted); font-size: 12px; text-align: center; }

@media (max-width: 900px) {
  .login-page { display: block; }
  .login-visual { display: none; }
  .login-panel { min-height: 100dvh; padding: 40px 28px; }
}
@media (max-width: 640px) {
  .login-panel { padding: 28px 20px 36px; }
  .login-brand { margin-bottom: 30px; }
  .login-heading { margin-bottom: 22px; }
  .login-heading h2 { font-size: 24px; }
}
</style>
