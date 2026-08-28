<script setup>
import { ref, watch, nextTick } from "vue";
import { messageBySessionId } from "@/api/message.js";
import { ElMessage } from "element-plus";
import MarkdownIt from "markdown-it";

// 初始化 markdown-it，启用常用GFM特性
const md = new MarkdownIt({
  html: false,        // 禁用原始HTML标签，防止XSS
  breaks: true,       // 单个换行符转为 <br>（对标原 marked.breaks）
  linkify: true,      // 自动识别URL并转为链接
  typographer: true,  // 启用排版优化（如引号替换）
});

// 如需表格/任务列表等GFM扩展，可在此处按需加载插件：
// import markdownItTable from 'markdown-it-multimd-table';
// md.use(markdownItTable);

const props = defineProps({
  visible: { type: Boolean, default: false },
  sessionId: { type: [Number, String], default: null },
  sessionName: { type: String, default: "会话详情" },
});

const emit = defineEmits(["update:visible"]);

const dialogVisible = ref(false);
const messageList = ref([]);
const loading = ref(false);
const scrollContainer = ref(null);

watch(
  () => props.visible,
  (val) => {
    dialogVisible.value = val;
    if (val && props.sessionId) fetchMessages();
  }
);

const handleClose = () => emit("update:visible", false);

const fetchMessages = async () => {
  loading.value = true;
  try {
    const res = await messageBySessionId(props.sessionId);
    if (res.code === 1) {
      messageList.value = res.data || [];
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

const scrollToBottom = () => {
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

const formatTime = (timeStr) => {
  if (!timeStr) return "";
  return timeStr.replace("T", " ").substring(0, 19);
};

/**
 * 使用 markdown-it 渲染AI消息
 * html:false 已禁止原始HTML注入，用户消息仍走纯文本<pre>
 */
const renderMarkdown = (content) => {
  if (!content) return "";
  return md.render(content);
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
    <div
      ref="scrollContainer"
      class="dialog-content-scroll"
      v-loading="loading"
    >
      <div v-if="messageList.length === 0 && !loading" class="no-attachment">
        暂无对话记录
      </div>

      <!-- 名称和时间移到气泡外部上方 -->
      <!-- 使用明确类名 msg--user / msg--assistant 替代动态class，消除IDE未使用警告 -->
      <div
        v-for="(msg, index) in messageList"
        :key="index"
        class="message-row"
        :class="msg.role === 'user' ? 'message-row--user' : 'message-row--assistant'"
      >
        <!-- 元信息行：在气泡外部 -->
        <div class="message-meta">
          <span class="role-tag">{{ msg.role === "user" ? "我" : "AI助手" }}</span>
          <span class="msg-time">{{ formatTime(msg.create_time) }}</span>
        </div>

        <!-- 消息气泡 -->
        <div class="message-bubble">
          <!-- AI消息用 v-html 渲染Markdown；用户消息用 pre 保持纯文本 -->
          <div
            v-if="msg.role === 'assistant'"
            class="markdown-body"
            v-html="renderMarkdown(msg.content)"
          />
          <pre v-else class="user-text">{{ msg.content }}</pre>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer-attachments">
        <el-button @click="handleClose">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<style scoped>
.dialog-content-scroll {
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px 15px;
  line-height: 1.6;
  color: #333;
}

/* 消息行布局 */
.message-row {
  margin-bottom: 24px;
  width: fit-content;
  max-width: 75%;
}

.message-row--user {
  margin-left: auto;
}

.message-row--assistant {
  margin-right: auto;
}

/* 元信息：名称 + 时间 */
.message-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
  font-size: 12px;
  color: #909399;
  padding: 0 4px;
}

.role-tag {
  font-weight: bold;
  color: #606266;
}

/* 消息气泡布局 */
.message-bubble {
  padding: 12px 16px;
  border-radius: 8px;
}

/* 用户气泡样式 */
.message-row--user .message-bubble {
  background-color: #ecf5ff;
  border: 1px solid #d9ecff;
}

/* AI气泡样式 */
.message-row--assistant .message-bubble {
  background-color: #f4f4f5;
  border: 1px solid #e9e9eb;
}

/* 用户纯文本 */
.user-text {
  margin: 0;
  white-space: pre-wrap;
  word-wrap: break-word;
  font-family: inherit;
  font-size: 14px;
  color: #303133;
}

/* AI Markdown 渲染样式（scoped下需用 :deep 穿透） */
.markdown-body :deep(p) {
  margin: 0 0 8px;
  font-size: 14px;
  color: #303133;
}

.markdown-body :deep(p:last-child) {
  margin-bottom: 0;
}

.markdown-body :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
  font-size: 13px;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 13px;
}

.markdown-body :deep(pre code) {
  background: none;
  padding: 0;
}

.markdown-body :deep(a) {
  color: var(--color-primary);
  text-decoration: none;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid #dcdfe6;
  margin: 8px 0;
  padding: 4px 12px;
  color: #606266;
  background: rgba(0, 0, 0, 0.02);
}

.markdown-body :deep(table) {
  border-collapse: collapse;
  width: 100%;
  margin: 8px 0;
  font-size: 13px;
}

.markdown-body :deep(th),
.markdown-body :deep(td) {
  border: 1px solid #ebeef5;
  padding: 6px 12px;
  text-align: left;
}

.markdown-body :deep(th) {
  background: #f5f7fa;
  font-weight: bold;
}

/* 底部 & 空状态布局 */
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
