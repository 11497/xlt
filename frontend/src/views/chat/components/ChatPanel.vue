<script setup>
import { ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { Delete, Position } from '@element-plus/icons-vue'

const md = new MarkdownIt({ html: true, linkify: true, typographer: true })

const props = defineProps({
  messages: Array,
  currentSessionId: Number,
  isStreaming: Boolean
})
const emit = defineEmits(['send', 'delete-message'])

const inputContent = ref('')
const textareaRef = ref(null)
const autoResizeTextarea = () => {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  const lineHeight = 24
  const maxHeight = lineHeight * 5
  if (el.scrollHeight <= maxHeight) {
    el.style.height = el.scrollHeight + 'px'
    el.style.overflowY = 'hidden'
  } else {
    el.style.height = maxHeight + 'px'
    el.style.overflowY = 'auto'
  }
}

const handleSend = () => {
  const content = inputContent.value.trim()
  if (!content || props.isStreaming) return
  emit('send', content)
  inputContent.value = ''
  nextTick(() => autoResizeTextarea())
}
</script>

<template>
  <section class="main-chat">
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, index) in messages" :key="index" class="message-row"
           :class="msg.role === 'user' ? 'is-user' : 'is-assistant'">
        <span class="message-role">{{ msg.role === 'user' ? '我' : 'AI 助手' }}</span>
        <div class="message-bubble">
          <template v-if="msg.role === 'user'">{{ msg.content }}</template>
          <div v-else class="markdown-body" v-html="md.render(msg.content)"></div>
        </div>
        <el-button v-if="msg.id" class="message-delete-btn" size="small" type="danger" text @click="$emit('delete-message', msg)">
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>
    </div>
    <div class="chat-input-area">
      <textarea
        v-model="inputContent"
        class="chat-textarea"
        placeholder="输入消息..."
        rows="1"
        @keydown.enter.exact.prevent="handleSend"
        @input="autoResizeTextarea"
        ref="textareaRef"
      ></textarea>
      <el-button type="primary" class="send-btn" @click="handleSend" :loading="isStreaming" :disabled="isStreaming">
        <el-icon v-if="!isStreaming"><Position /></el-icon> {{ isStreaming ? '发送中' : '发送' }}
      </el-button>
    </div>
  </section>
</template>

<style scoped>
.main-chat { flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px; min-height: 0; }
.message-row { display: flex; flex-direction: column; margin-bottom: 16px; }
.message-row.is-assistant { align-self: flex-start; align-items: flex-start; }
.message-row.is-user { align-self: flex-end; align-items: flex-end; }
.message-role { font-size: 12px; color: #909399; margin-bottom: 4px; padding: 0 4px; }
.message-bubble { padding: 10px 14px; font-size: 14px; line-height: 1.6; word-break: break-word; border-radius: 8px; position: relative; }
.message-delete-btn { opacity: 0; transition: opacity 0.2s; align-self: flex-end; }
.message-row.is-user .message-delete-btn { align-self: flex-end; }
.message-row.is-assistant .message-delete-btn { align-self: flex-start; }
.message-row:hover .message-delete-btn { opacity: 1; }
.is-assistant .message-bubble { background-color: #f0f2f5; color: #303133; border-top-left-radius: 2px; }
.is-user .message-bubble { background-color: #409eff; color: #fff; border-top-right-radius: 2px; }
.chat-input-area { flex-shrink: 0; display: flex; align-items: flex-end; gap: 8px; padding: 12px 16px; border-top: 1px solid #dcdfe6; background-color: #fff; }
.chat-textarea { flex: 1; resize: none; border: 1px solid #dcdfe6; border-radius: 4px; padding: 8px 12px; font-size: 14px; line-height: 24px; max-height: 120px; outline: none; transition: border-color 0.2s; font-family: inherit; box-sizing: border-box; }
.chat-textarea:focus { border-color: #409eff; }
.send-btn { flex-shrink: 0; height: 40px; }
</style>
