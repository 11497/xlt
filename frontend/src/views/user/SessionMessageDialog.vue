<script setup>
import { ref, watch, nextTick } from "vue";
import { messageBySessionId } from "@/api/message.js";
import { ElMessage } from "element-plus";

const props = defineProps({
  visible: {
    type: Boolean,
    default: false,
  },
  sessionId: {
    type: [Number, String],
    default: null,
  },
  sessionName: {
    type: String,
    default: "会话详情",
  },
});

const emit = defineEmits(["update:visible"]);

const dialogVisible = ref(false);
const messageList = ref([]);
const loading = ref(false);
const scrollContainer = ref(null);

// 同步外部 visible 状态
watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val;
    if (val && props.sessionId) {
      fetchMessages();
    }
  }
);

// 关闭弹窗时通知父组件
const handleClose = () => {
  emit("update:visible", false);
};

// 获取消息列表
const fetchMessages = async () => {
  loading.value = true;
  try {
    const res = await messageBySessionId(props.sessionId);
    if (res.code === 1) {
      messageList.value = res.data || [];
      // 等待DOM更新后滚动到底部
      await nextTick();
      scrollToBottom();
    } else {
      ElMessage.error(res.msg || "获取消息失败");
      messageList.value = [];
    }
  } catch (error) {
    console.error("获取消息异常:", error);
    ElMessage.error("网络异常，请稍后重试");
  } finally {
    loading.value = false;
  }
};

// 滚动到最新消息
const scrollToBottom = () => {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return "";
  return timeStr.replace("T", " ").substring(0, 19);
};
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    :title="sessionName"
    width="70%"
    top="5vh"
    :close-on-click-modal="false"
    @close="handleClose"
    destroy-on-close
  >
    <!-- 消息列表区域：复用 dialog-content-scroll 样式 -->
    <div
      ref="scrollContainer"
      class="dialog-content-scroll"
      v-loading="loading"
    >
      <div v-if="messageList.length === 0 && !loading" class="no-attachment">
        暂无对话记录
      </div>

      <div
        v-for="(msg, index) in messageList"
        :key="index"
        class="message-item"
        :class="msg.role"
      >
        <div class="message-header">
          <span class="role-tag">{{ msg.role === "user" ? "我" : "AI助手" }}</span>
          <span class="msg-time">{{ formatTime(msg.create_time) }}</span>
        </div>
        <div class="message-body">
          <pre>{{ msg.content }}</pre>
        </div>
      </div>
    </div>

    <!-- 底部占位：保持与原页面一致的间距风格 -->
    <template #footer>
      <div class="dialog-footer-attachments">
        <el-button @click="handleClose">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
/* 复用原页面的滚动容器样式 */
.dialog-content-scroll {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px 15px;
  line-height: 1.6;
  color: #333;
}

/* 消息条目基础样式 */
.message-item {
  margin-bottom: 20px;
  padding: 12px 16px;
  border-radius: 8px;
  max-width: 85%;
}

/* 用户消息靠右 */
.message-item.user {
  margin-left: auto;
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
}

/* AI消息靠左 */
.message-item.assistant {
  margin-right: auto;
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
}

.message-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
  font-size: 12px;
  color: #909399;
}

.role-tag {
  font-weight: bold;
  color: #606266;
}

.message-body pre {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  color: #303133;
}

/* 复用原页面底部样式 */
.dialog-footer-attachments {
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
  text-align: right;
}

.no-attachment {
  color: #909399;
  font-style: italic;
  text-align: center;
  padding: 40px 10px;
}
</style>