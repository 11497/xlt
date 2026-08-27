<script setup>
import { onMounted, ref, reactive, onUnmounted, computed } from 'vue';
import { useCurrentUser } from "@/hooks/useCurrentUser.js";
import { getAllAnnouncements } from "@/api/announcement.js";
import { getAnnouncementAttachments, downloadAnnouncementAttachment } from "@/api/announcement_attachment.js";
import { ElMessage } from 'element-plus';
import {updatePassword} from "@/api/user.js";
import { Download, Bell, ArrowRight, ArrowLeft } from "@element-plus/icons-vue";

const { user } = useCurrentUser();

const topAnnouncements = ref([]);
const currentAnnouncementIndex = ref(0);
const carouselTimer = ref(null);

// 获取所有置顶公告
const fetchTopAnnouncements = async () => {
  try {
    const res = await getAllAnnouncements(1, 100);
    if (res.code === 1 && res.data?.list) {
      topAnnouncements.value = res.data.list.filter(item => item.is_top);
    }
  } catch (e) {
    console.error('获取置顶公告失败', e);
  }
};

// 轮播控制
const startCarousel = () => {
  stopCarousel();
  if (topAnnouncements.value.length > 1) {
    carouselTimer.value = setInterval(() => {
      currentAnnouncementIndex.value = (currentAnnouncementIndex.value + 1) % topAnnouncements.value.length;
    }, 3000);
  }
};

const stopCarousel = () => {
  if (carouselTimer.value) {
    clearInterval(carouselTimer.value);
    carouselTimer.value = null;
  }
};

const goToPrev = () => {
  stopCarousel();
  if (topAnnouncements.value.length > 0) {
    currentAnnouncementIndex.value = (currentAnnouncementIndex.value - 1 + topAnnouncements.value.length) % topAnnouncements.value.length;
  }
  startCarousel();
};

const goToNext = () => {
  stopCarousel();
  if (topAnnouncements.value.length > 0) {
    currentAnnouncementIndex.value = (currentAnnouncementIndex.value + 1) % topAnnouncements.value.length;
  }
  startCarousel();
};

const goToIndex = (index) => {
  stopCarousel();
  currentAnnouncementIndex.value = index;
  startCarousel();
};

// 当前显示的公告
const currentAnnouncement = computed(() => {
  return topAnnouncements.value[currentAnnouncementIndex.value] || null;
});

// 详情弹窗相关状态
const detailDialogVisible = ref(false);
const detailAnnouncement = ref(null);
const attachmentList = ref([]);
const attachmentLoading = ref(false);

// 显示置顶公告详情
const showTopAnnouncementDetail = async () => {
  const announcement = topAnnouncements.value[currentAnnouncementIndex.value];
  if (!announcement) {
    ElMessage.info('暂无置顶公告');
    return;
  }
  
  detailAnnouncement.value = announcement;
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
  await fetchTopAnnouncements();
  startCarousel();
});

onUnmounted(() => {
  stopCarousel();
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
  oldPassword: [
    { required: true, message: '请输入旧密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
    { max: 20, message: '密码长度不能超过20位', trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '密码长度不能少于6位', trigger: 'blur' },
    { max: 20, message: '密码长度不能超过20位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && value === pwdForm.oldPassword) callback(new Error('新密码不能与旧密码相同'));
        else callback();
      },
      trigger: 'blur'
    }
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
      <el-header class="announcement-header">
        <div class="announcement-wrapper">
          <div class="announcement-container">
            <div class="announcement-carousel">
              <div class="carousel-left-group">
                <div class="announcement-badge">
                  <el-icon class="badge-icon"><Bell /></el-icon>
                  <span class="badge-text">置顶</span>
                </div>
                <el-icon class="carousel-btn" @click="goToPrev"><ArrowLeft /></el-icon>
              </div>
              
              <a href="javascript:0" class="announcement-link" @click="showTopAnnouncementDetail">
                <span class="announcement-title">
                  {{ currentAnnouncement?.title || '暂无置顶公告' }}
                </span>
              </a>
              
              <el-icon class="carousel-btn" @click="goToNext"><ArrowRight /></el-icon>
            </div>
          </div>

          <div class="carousel-indicators" v-if="topAnnouncements.length > 1">
            <span
              v-for="(_, index) in topAnnouncements"
              :key="index"
              class="indicator-dot"
              :class="{ active: index === currentAnnouncementIndex }"
              @click="goToIndex(index)"
            ></span>
          </div>
        </div>
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
            maxlength="20"
          />
        </el-form-item>
        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="pwdForm.newPassword"
            type="password"
            show-password
            placeholder="请输入新密码"
            maxlength="20"
            @input="pwdFormRef?.validateField('confirmPassword')"
          />
        </el-form-item>
        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="pwdForm.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入新密码"
            maxlength="20"
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
      :title="detailAnnouncement?.title"
      width="60%"
      top="5vh"
      destroy-on-close
      align-center
    >
      <template #header>
        <div style="text-align: center; font-size: 18px; font-weight: bold;">
          {{ detailAnnouncement?.title }}
        </div>
      </template>

      <div class="dialog-content-scroll">
        <div v-html="detailAnnouncement?.content || '暂无内容'" class="content-body"></div>
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

.announcement-header {
  background: linear-gradient(135deg, #40d2ff, #259feb);
  padding: 0;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
}

.announcement-wrapper {
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.announcement-container {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 20px 8px;
}

.announcement-carousel {
  width: 50%;
  display: flex;
  align-items: center;
  gap: 10px;
}

.carousel-left-group {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.announcement-badge {
  display: flex;
  align-items: center;
  gap: 4px;
  background-color: rgba(255, 255, 255, 0.95);
  padding: 4px 12px;
  border-radius: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.badge-icon {
  font-size: 18px;
  color: #409eff;
}

.badge-text {
  font-size: 13px;
  font-weight: bold;
  color: #409eff;
}

.carousel-btn {
  font-size: 20px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.3s ease;
  flex-shrink: 0;
  padding: 4px;
  border-radius: 50%;
}

.carousel-btn:hover {
  color: #e0f7fa;
  background-color: rgba(255, 255, 255, 0.2);
}

.announcement-link {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  text-decoration: none;
  transition: all 0.3s ease;
  cursor: pointer;
  min-width: 0;
}

.announcement-title {
  font-size: 16px;
  color: #ffffff;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.announcement-link:hover .announcement-title {
  color: #e0f7fa;
  text-decoration: underline;
}

.carousel-indicators {
  display: flex;
  gap: 6px;
  justify-content: center;
  padding-bottom: 8px;
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator-dot.active {
  background-color: #ffffff;
  transform: scale(1.2);
}

.indicator-dot:hover {
  background-color: rgba(255, 255, 255, 0.8);
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

@media (max-width: 768px) {
  .announcement-container { padding: 10px 8px 6px; }
  .announcement-carousel { width: 100%; gap: 6px; }
  .announcement-badge { padding: 4px 8px; }
  .badge-text { display: none; }
  .carousel-left-group { gap: 4px; }
  .account-card { max-width: 100%; }
  .attachment-item { min-width: 0; }
}
</style>
