<script setup>
import { ref, watch, nextTick } from "vue";
import { deleteMessagesAfter, messageBySessionId } from "@/api/message.js";
import { ElMessage, ElMessageBox } from "element-plus";
import { CopyDocument, Delete, Document } from "@element-plus/icons-vue";
import MarkdownIt from "markdown-it";
import MessageSourcesDialog from "@/components/MessageSourcesDialog.vue";

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
const sourceDialogVisible = ref(false);
const selectedSources = ref([]);

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

const showSources = (sources) => {
  selectedSources.value = sources;
  sourceDialogVisible.value = true;
};

const copyMessage = async (content) => {
  if (!content) return;

  try {
    let copied = false;
    if (navigator.clipboard?.writeText) {
      try {
        await navigator.clipboard.writeText(content);
        copied = true;
      } catch {
        copied = false;
      }
    }

    if (!copied) {
      const textarea = document.createElement("textarea");
      textarea.value = content;
      textarea.style.position = "fixed";
      textarea.style.opacity = "0";
      document.body.appendChild(textarea);
      try {
        textarea.select();
        copied = document.execCommand("copy");
      } finally {
        textarea.remove();
      }
    }

    if (!copied) throw new Error("浏览器拒绝复制操作");
    ElMessage.success("消息已复制");
  } catch (error) {
    console.error("复制消息失败:", error);
    ElMessage.error("复制失败，请稍后重试");
  }
};

const deleteMessage = async (msg) => {
  try {
    await ElMessageBox.confirm("确定要删除该消息及后续内容吗？", "删除", {
      confirmButtonText: "确定",
      cancelButtonText: "取消",
      type: "warning",
    });
    const res = await deleteMessagesAfter(msg.session_id, msg.id);
    if (res.code) {
      ElMessage.success("删除成功");
      await fetchMessages();
    } else {
      ElMessage.error(res.msg || "删除失败");
    }
  } catch (error) {
    if (error !== "cancel" && error?.action !== "cancel") {
      ElMessage.error("删除请求异常");
    }
  }
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
        <span v-if="msg.role === 'assistant' && msg.is_stopped === 1" class="message-stopped-tag">已停止生成</span>
        <div v-if="msg.id" class="message-controls">
          <div class="message-actions">
            <el-tooltip content="复制消息" placement="bottom" :hide-after="30">
              <button class="message-action-btn" type="button" aria-label="复制消息" @click="copyMessage(msg.content)">
                <el-icon><CopyDocument /></el-icon>
              </button>
            </el-tooltip>
            <el-tooltip content="删除此消息及后续内容" placement="bottom" :hide-after="30">
              <button class="message-action-btn message-delete-btn" type="button" aria-label="删除此消息及后续内容" @click="deleteMessage(msg)">
                <el-icon><Delete /></el-icon>
              </button>
            </el-tooltip>
          </div>
          <el-tooltip v-if="msg.role === 'assistant' && msg.sources?.length" :content="`${msg.sources.length}个来源`" placement="bottom" :hide-after="30">
            <button
              class="message-action-btn message-source-btn"
              type="button"
              @click="showSources(msg.sources)"
            >
              <el-icon><Document /></el-icon><span>{{ msg.sources.length }}个来源</span>
            </button>
          </el-tooltip>
        </div>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer-attachments">
        <el-button @click="handleClose">关 闭</el-button>
      </div>
    </template>
  </el-dialog>
  <MessageSourcesDialog v-model:visible="sourceDialogVisible" :sources="selectedSources" />
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

.message-controls {
  width: 100%;
  min-height: 30px;
  margin-top: 4px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.message-actions {
  height: 30px;
  display: flex;
  align-items: center;
  gap: 2px;
}

.message-action-btn {
  width: 30px;
  height: 30px;
  padding: 0;
  display: grid;
  place-items: center;
  border: 0;
  border-radius: 4px;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;
  transition: background-color .15s, color .15s;
}

.message-action-btn .el-icon {
  font-size: 16px;
}

.message-action-btn:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
}

.message-delete-btn:hover {
  background: #fff0f0;
  color: var(--color-danger);
}

.message-stopped-tag {
  margin-left: 4px;
  color: #909399;
  font-size: 12px;
}

.message-source-btn {
  height: 30px;
  width: auto;
  margin-left: 0;
  padding: 0 7px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 14px;
  white-space: nowrap;
}

.message-source-btn .el-icon {
  font-size: 16px;
}

.message-source-btn:hover {
  background: var(--color-primary-soft);
  color: var(--color-primary);
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
