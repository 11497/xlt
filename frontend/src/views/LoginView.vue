<script setup>
import {ref, onMounted} from 'vue';
import {userLogin} from "@/api/user.js";
import {ElMessage} from "element-plus";
import {useRouter} from "vue-router";

let userForm = ref({username: "", password: ""});
const loginFormRef = ref(null);
const router = useRouter();

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

    const result = await userLogin({
      username: userForm.value.username,
      password: userForm.value.password,
      is_admin: 0,
      id: 0
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
}

// 重置
const clear = () => {
    userForm.value = {username: '', password: ''};
    loginFormRef.value.resetFields();
}
</script>

<template>
    <div id="container">
        <div class="login-form">
            <el-form ref="loginFormRef" :model="userForm" :rules="rules" label-width="80px">
                <p class="title">校灵通</p>
                <el-form-item label="用户名" prop="username">
                    <el-input v-model="userForm.username" placeholder="请输入用户名"></el-input>
                </el-form-item>

                <el-form-item label="密码" prop="password">
                    <el-input type="password" v-model="userForm.password" placeholder="请输入密码"></el-input>
                </el-form-item>

                <el-form-item>
                    <el-button class="button" type="primary" @click="login">登 录</el-button>
                    <el-button class="button" type="info" @click="clear">重 置</el-button>
                </el-form-item>
            </el-form>
        </div>
    </div>
</template>

<style scoped>
#container {
    padding: 10%;
    height: 410px;
    background-repeat: no-repeat;
    background-size: cover;
}

.login-form {
    max-width: 400px;
    padding: 30px;
    margin: 0 auto;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    background-color: white;
}

.title {
    font-size: 30px;
    font-family: '楷体';
    text-align: center;
    margin-bottom: 30px;
    font-weight: bold;
}

.button {
    margin-top: 30px;
    width: 120px;
}
</style>