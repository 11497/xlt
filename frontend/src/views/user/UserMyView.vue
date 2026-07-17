<script setup>
import { onMounted, ref, reactive } from 'vue';
import { useCurrentUser } from "@/hooks/useCurrentUser.js";
import { getAllAnnouncements } from "@/api/announcement.js";
import { ElMessage } from 'element-plus';
import {updatePassword} from "@/api/user.js";

const { user } = useCurrentUser();

const topAnnouncements = ref([]);

onMounted(async () => {
  try {
    const res = await getAllAnnouncements(1, 1);
    if (res.data?.list?.[0]?.is_top) {
      topAnnouncements.value = res.data.list;
    }
  } catch (e) {
    console.error('获取公告失败', e);
  }
});

const pwdDialogVisible = ref(false);
const pwdFormRef = ref(null);
const pwdLoading = ref(false);

const pwdForm = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
});

const pwdRules = {
  oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
    { max: 20, message: '密码长度不能超过20位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value !== pwdForm.newPassword) {
          callback(new Error('两次输入的密码不一致'));
        } else {
          callback();
        }
      },
      trigger: 'blur'  // ← 关键！没有这行自定义校验不会触发
    },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
    { max: 20, message: '密码长度不能超过20位', trigger: 'blur' }
  ]
};

const openPwdDialog = () => {
  // 重置表单
  pwdForm.oldPassword = '';
  pwdForm.newPassword = '';
  pwdForm.confirmPassword = '';
  pwdDialogVisible.value = true;
};

const submitPassword = async () => {
  if (!pwdFormRef.value) return;
  await pwdFormRef.value.validate(async (valid) => {
    if (!valid) return;

    pwdLoading.value = true;
    try {
      const res = await updatePassword({
        oldPassword: pwdForm.oldPassword,
        newPassword: pwdForm.newPassword
      })

      if (res.code === 1) {
        ElMessage.success('密码修改成功');
      } else {
        ElMessage.error(res.msg || '密码修改失败');
      }
      pwdDialogVisible.value = false;
    } catch (error) {
      ElMessage.error(error?.message || '密码修改失败');
    } finally {
      pwdLoading.value = false;
    }
  });
};
</script>

<template>
  <div class="common-layout">
    <el-container>
      <!-- 顶部公告 -->
      <el-header>
        <p class="announcement-text">
          <a href="javascript:0" class="announcement-link">
            置顶公告: {{ topAnnouncements?.length > 0 ? topAnnouncements[0].title : '暂无置顶公告' }}
          </a>
        </p>
      </el-header>

      <el-main>
        <el-card shadow="hover" class="account-card">
          <template #header>
            <div class="card-header">
              <span>账号信息</span>
            </div>
          </template>

          <!-- 使用 el-descriptions 替代 el-form 展示只读信息更语义化 -->
          <el-descriptions :column="1" border label-class-name="desc-label">
            <el-descriptions-item label="用户ID">
              {{ user?.id ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="用户名">
              {{ user?.username ?? '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="操作">
              <el-button type="primary" @click="openPwdDialog">
                更改密码
              </el-button>
            </el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-main>
    </el-container>

    <!-- 修改密码弹窗 -->
    <el-dialog
      v-model="pwdDialogVisible"
      title="更改密码"
      width="460px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form
        ref="pwdFormRef"
        :model="pwdForm"
        :rules="pwdRules"
        label-width="90px"
      >
        <el-form-item label="旧密码" prop="oldPassword">
          <el-input
            v-model="pwdForm.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前使用的密码"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="pwdForm.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码"
            @input="pwdFormRef?.validateField('confirmPassword')"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="pwdForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取 消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPassword">
          确 定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.announcement-text {
  text-align: center;
}

.announcement-link {
  margin: 10px;
  font-size: 18px;
  color: #000000;
}

.announcement-link:hover {
  color: #00aaa0;
}

a {
  text-decoration: none;
}

.account-card {
  max-width: 600px;
  margin: 0 auto; /* 中置效果 */
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
}

/* 让 descriptions 的 label 列宽度固定且居中 */
:deep(.desc-label) {
  width: 100px !important;
  text-align: center !important;
}
</style>