<script setup>
import { onMounted, ref, reactive, onUnmounted, computed } from 'vue';
import { useCurrentUser } from "@/hooks/useCurrentUser.js";
import { getAllAnnouncements } from "@/api/announcement.js";
import { getAnnouncementAttachments, downloadAnnouncementAttachment } from "@/api/announcement_attachment.js";
import { ElMessage } from 'element-plus';
import {updatePassword} from "@/api/user.js";
import { Download, Bell, ArrowRight, ArrowLeft, ChatLineSquare, Notebook, Message, Key, UserFilled } from "@element-plus/icons-vue";
import {useRouter} from 'vue-router';
import PageHeader from '@/components/PageHeader.vue';

const { user } = useCurrentUser();
const router = useRouter();
const quickLinks = [
  {label: '开始智能问答', description: '从校园知识库查找答案', icon: ChatLineSquare, path: '/chat'},
  {label: '浏览知识库', description: '查看当前可访问的资料', icon: Notebook, path: '/user/knowledgeBase'},
  {label: '查看校园公告', description: '关注最新通知与附件', icon: Message, path: '/user/announcement'}
];

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
  <div class="personal-dashboard">
    <PageHeader title="个人工作台" description="集中查看身份、校园通知与常用知识入口" />

    <section class="identity-panel">
      <div class="identity-avatar"><el-icon><UserFilled /></el-icon></div>
      <div class="identity-copy">
        <span>欢迎回来</span>
        <h2>{{ user?.username || '校园用户' }}</h2>
        <div class="identity-tags">
          <el-tag :class="user?.is_admin ? 'status-tag-admin' : ''" effect="plain">{{ user?.is_admin ? '管理员' : '普通用户' }}</el-tag>
          <el-tag type="info" effect="plain">校园知识服务成员</el-tag>
          <span class="identity-id">账号 ID {{ user?.id ?? '-' }}</span>
        </div>
      </div>
      <el-button plain @click="openPwdDialog"><el-icon><Key /></el-icon>修改密码</el-button>
    </section>

    <section class="notice-strip">
      <div class="notice-label"><el-icon><Bell /></el-icon><span>置顶公告</span></div>
      <button class="notice-title" type="button" @click="showTopAnnouncementDetail">{{ currentAnnouncement?.title || '暂无置顶公告' }}</button>
      <div v-if="topAnnouncements.length > 1" class="notice-controls">
        <button type="button" aria-label="上一条公告" title="上一条" @click="goToPrev"><el-icon><ArrowLeft /></el-icon></button>
        <span>{{ currentAnnouncementIndex + 1 }} / {{ topAnnouncements.length }}</span>
        <button type="button" aria-label="下一条公告" title="下一条" @click="goToNext"><el-icon><ArrowRight /></el-icon></button>
      </div>
    </section>

    <section class="quick-section">
      <h2>常用入口</h2>
      <div class="quick-grid">
        <button v-for="item in quickLinks" :key="item.path" type="button" @click="router.push(item.path)">
          <span class="quick-icon"><el-icon><component :is="item.icon" /></el-icon></span>
          <span class="quick-copy"><strong>{{ item.label }}</strong><small>{{ item.description }}</small></span>
          <el-icon class="quick-arrow"><ArrowRight /></el-icon>
        </button>
      </div>
    </section>

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
        <div class="content-body">{{ detailAnnouncement?.content || '暂无内容' }}</div>
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
.personal-dashboard { width: 100%; }
.identity-panel { min-height: 132px; padding: 24px; display: flex; align-items: center; gap: 18px; background: #fff; border: 1px solid var(--color-border); border-radius: 6px; }
.identity-avatar { width: 58px; height: 58px; flex: 0 0 58px; display: grid; place-items: center; border-radius: 6px; background: var(--color-primary-soft); color: var(--color-primary); font-size: 28px; }
.identity-copy { min-width: 0; flex: 1; }
.identity-copy > span { color: var(--color-text-secondary); font-size: 13px; }
.identity-copy h2 { margin: 4px 0 10px; overflow: hidden; font-size: 22px; text-overflow: ellipsis; white-space: nowrap; }
.identity-tags { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.identity-id { color: var(--color-text-muted); font-size: 12px; }
.notice-strip { min-height: 54px; margin-top: 16px; padding: 8px 12px; display: flex; align-items: center; gap: 12px; background: #fffdf8; border: 1px solid #eee1c3; border-radius: 6px; }
.notice-label { flex: 0 0 auto; display: flex; align-items: center; gap: 6px; color: #91630d; font-size: 13px; font-weight: 600; }
.notice-title { min-width: 0; flex: 1; padding: 8px; overflow: hidden; border: 0; background: transparent; color: #46525e; text-align: left; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }
.notice-title:hover { color: var(--color-primary); }
.notice-controls { flex: 0 0 auto; display: flex; align-items: center; gap: 5px; color: var(--color-text-muted); font-size: 11px; }
.notice-controls button { width: 34px; height: 34px; display: grid; place-items: center; border: 0; border-radius: 4px; background: transparent; color: var(--color-text-secondary); cursor: pointer; }
.notice-controls button:hover { background: #f4ecd9; }
.quick-section { margin-top: 26px; }
.quick-section > h2 { margin: 0 0 12px; font-size: 16px; }
.quick-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid var(--color-border); border-radius: 6px; overflow: hidden; }
.quick-grid > button { min-width: 0; min-height: 88px; padding: 16px; display: flex; align-items: center; gap: 12px; border: 0; border-right: 1px solid var(--color-border); background: #fff; color: inherit; text-align: left; cursor: pointer; }
.quick-grid > button:last-child { border-right: 0; }
.quick-grid > button:hover { background: #f5faf9; }
.quick-icon { width: 38px; height: 38px; flex: 0 0 38px; display: grid; place-items: center; border-radius: 6px; background: var(--color-primary-soft); color: var(--color-primary); font-size: 19px; }
.quick-copy { min-width: 0; display: flex; flex: 1; flex-direction: column; gap: 5px; }
.quick-copy strong { font-size: 14px; }
.quick-copy small { overflow: hidden; color: var(--color-text-secondary); font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.quick-arrow { flex: 0 0 auto; color: var(--color-text-muted); }

/* 公告详情弹窗样式 */
.dialog-content-scroll {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px 0;
  line-height: 1.6;
  color: #333;
}
.content-body {
  white-space: pre-wrap;
  word-break: break-word;
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
  .identity-panel { padding: 18px 14px; align-items: flex-start; flex-wrap: wrap; }
  .identity-avatar { width: 48px; height: 48px; flex-basis: 48px; font-size: 22px; }
  .identity-copy { width: calc(100% - 66px); }
  .identity-panel > .el-button { margin-left: 66px; }
  .notice-strip { gap: 6px; }
  .notice-label span { display: none; }
  .notice-controls span { display: none; }
  .quick-grid { grid-template-columns: 1fr; }
  .quick-grid > button { min-height: 76px; border-right: 0; border-bottom: 1px solid var(--color-border); }
  .quick-grid > button:last-child { border-bottom: 0; }
  .attachment-item { min-width: 0; }
}
</style>
