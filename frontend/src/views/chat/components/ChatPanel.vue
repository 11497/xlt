<script setup>
import { computed, ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'
import { Delete, Position, VideoPause } from '@element-plus/icons-vue'
import { countCharacters, truncateCharacters } from '@/utils/characterCount.js'
import ChatInputCounter from './ChatInputCounter.vue'

const md = new MarkdownIt({ html: true, linkify: true, typographer: true })
const MAX_INPUT_LENGTH = 2000

const props = defineProps({
  messages: Array,
  currentSessionId: Number,
  isStreaming: Boolean,
  isStopping: Boolean
})
const emit = defineEmits(['send', 'stop', 'delete-message'])

const inputContent = ref('')
const textareaRef = ref(null)
const isComposing = ref(false)
const inputLength = computed(() => countCharacters(inputContent.value))
const isOverLimit = computed(() => inputLength.value > MAX_INPUT_LENGTH)

const autoResizeTextarea = () => {
  const el = textareaRef.value
  if (!el) return
  const minHeight = 40
  const maxHeight = 120
  el.style.height = `${minHeight}px`
  const contentHeight = el.scrollHeight + 2
  el.style.height = `${Math.min(Math.max(contentHeight, minHeight), maxHeight)}px`
  el.style.overflowY = contentHeight > maxHeight ? 'auto' : 'hidden'
}

const enforceInputLimit = (event) => {
  if (isComposing.value) return

  const value = event.target.value
  if (countCharacters(value) <= MAX_INPUT_LENGTH) return

  inputContent.value = truncateCharacters(value, MAX_INPUT_LENGTH)
  event.target.value = inputContent.value
}

const handleInput = (event) => {
  enforceInputLimit(event)
  nextTick(() => autoResizeTextarea())
}

const handleCompositionEnd = (event) => {
  isComposing.value = false
  enforceInputLimit(event)
  nextTick(() => autoResizeTextarea())
}

const handlePaste = (event) => {
  const textarea = textareaRef.value
  if (!textarea) return

  event.preventDefault()
  const pastedText = event.clipboardData?.getData('text') || ''
  const selectionStart = textarea.selectionStart
  const selectionEnd = textarea.selectionEnd
  const beforeSelection = inputContent.value.slice(0, selectionStart)
  const afterSelection = inputContent.value.slice(selectionEnd)
  const availableLength = Math.max(
    0,
    MAX_INPUT_LENGTH - countCharacters(beforeSelection) - countCharacters(afterSelection)
  )
  const acceptedText = truncateCharacters(pastedText, availableLength)

  inputContent.value = beforeSelection + acceptedText + afterSelection

  if (countCharacters(pastedText) > availableLength) {
    ElMessage.warning(`粘贴内容超过 ${MAX_INPUT_LENGTH} 个字符，已自动截断`)
  }

  nextTick(() => {
    const cursorPosition = beforeSelection.length + acceptedText.length
    textarea.setSelectionRange(cursorPosition, cursorPosition)
    autoResizeTextarea()
  })
}

const handleEnter = (event) => {
  if (event.isComposing || isComposing.value) return
  event.preventDefault()
  handleSend()
}

const handleSend = () => {
  const content = inputContent.value.trim()
  if (!content || props.isStreaming) return
  if (countCharacters(content) > MAX_INPUT_LENGTH) return
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
        <el-button v-if="msg.id && !isStreaming" class="message-delete-btn" size="small" type="danger" text @click="$emit('delete-message', msg)">
          <el-icon><Delete /></el-icon> 删除
        </el-button>
      </div>
    </div>
    <div class="chat-input-area">
      <div class="chat-input-wrapper">
        <textarea
          v-model="inputContent"
          class="chat-textarea"
          placeholder="输入消息..."
          rows="1"
          aria-describedby="chat-input-count-status"
          @keydown.enter.exact="handleEnter"
          @input="handleInput"
          @paste="handlePaste"
          @compositionstart="isComposing = true"
          @compositionend="handleCompositionEnd"
          ref="textareaRef"
        ></textarea>
        <ChatInputCounter :count="inputLength" :max-length="MAX_INPUT_LENGTH" />
      </div>
      <el-button
        :type="isStreaming ? 'danger' : 'primary'"
        class="send-btn"
        @click="isStreaming ? emit('stop') : handleSend()"
        :disabled="isStopping || (!isStreaming && isOverLimit)"
      >
        <el-icon><VideoPause v-if="isStreaming"/><Position v-else/></el-icon>
        {{ isStopping ? '停止中' : (isStreaming ? '停止' : '发送') }}
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
.chat-input-wrapper { position: relative; flex: 1; min-width: 0; }
.chat-textarea { display: block; width: 100%; min-height: 40px; resize: none; border: 1px solid #dcdfe6; border-radius: 4px; padding: 7px 12px; font-size: 14px; line-height: 24px; max-height: 120px; outline: none; transition: border-color 0.2s; font-family: inherit; box-sizing: border-box; }
.chat-textarea:focus { border-color: #409eff; }
.send-btn { flex-shrink: 0; height: 40px; }
</style>
