<script setup>
import { onMounted, ref, reactive } from 'vue';
import { useCurrentUser } from "@/hooks/useCurrentUser.js";
import { getAllAnnouncements } from "@/api/announcement.js";
import { getAnnouncementAttachments, downloadAnnouncementAttachment } from "@/api/anouncement_attachment.js";
import { ElMessage } from 'element-plus';
import {updatePassword} from "@/api/user.js";
import { InfoFilled, Download } from "@element-plus/icons-vue";

const { user } = useCurrentUser();

const topAnnouncements = ref([]);

// 详情弹窗相关状态
const detailDialogVisible = ref(false);
const currentAnnouncement = ref(null);
const attachmentList = ref([]);
const attachmentLoading = ref(false);

// 显示置顶公告详情
const showTopAnnouncementDetail = async () => {
  if (topAnnouncements.value.length === 0) {
    ElMessage.info('暂无置顶公告');
    return;
  }
  
  const announcement = topAnnouncements.value[0];
  currentAnnouncement.value = announcement;
  detailDialogVisible.value = true;
  attachmentList.value = [];
  
  attachmentLoading.value = true;
  try {
    const res = await getAnnouncementAttachments(announcement.id);
    if (res.code === 1) {
      attachmentList.value = res.data || [];
    } else {
      ElMessage.error(res.msg || '获取附件失败');
    }
  } catch (e) {
    console.error(e);
  } finally {
    attachmentLoading.value = false;
  }
};

// 下载附件
const handleDownload = async (attachmentId) => {
  await downloadAnnouncementAttachment(attachmentId);
};

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
      trigger: 'blur'
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
  <div class="container">
    <el-container>
      <!-- 顶部公告 -->
      <el-header>
        <p class="announcement-text">
          <a href="javascript:0" class="announcement-link" @click="showTopAnnouncementDetail">
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

    <!-- 公告详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentAnnouncement?.title"
      width="60%"
      top="5vh"
      destroy-on-close
      align-center
    >
      <template #header>
        <div style="text-align: center; font-size: 18px; font-weight: bold;">
          {{ currentAnnouncement?.title }}
        </div>
      </template>

      <div class="dialog-content-scroll">
        <div v-html="currentAnnouncement?.content || '暂无内容'" class="content-body"></div>
      </div>

      <div class="dialog-footer-attachments">
        <div class="attachment-label">附件列表：</div>
        <div v-loading="attachmentLoading" class="attachment-list">
          <div v-if="attachmentList.length === 0 && !attachmentLoading" class="no-attachment">
            暂无附件
          </div>
          <div
            v-for="item in attachmentList"
            :key="item.id"
            class="attachment-item"
          >
            <el-tooltip :content="item.filename" placement="top">
              <span class="filename-text">{{ item.filename }}</span>
            </el-tooltip>
            <el-button
              type="primary"
              link
              @click="handleDownload(item.id)"
            >
              <el-icon><Download /></el-icon> 下载
            </el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<style scoped>
.container {
  margin: 15px 0;
}

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

/* 公告详情弹窗样式 */
.dialog-content-scroll {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px 0;
  line-height: 1.6;
  color: #333;
}

.dialog-footer-attachments {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.attachment-label {
  font-weight: bold;
  margin-bottom: 10px;
  color: #606266;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.attachment-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.filename-text {
  flex: 1;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  margin-right: 15px;
  color: #303133;
}

.no-attachment {
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 10px;
}
</style>