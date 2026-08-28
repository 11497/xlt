<script setup>
import { computed, ref, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'
import { ChatDotRound, Delete, Position, UserFilled, VideoPause } from '@element-plus/icons-vue'
import { countCharacters, truncateCharacters } from '@/utils/characterCount.js'
import ChatInputCounter from './ChatInputCounter.vue'

const md = new MarkdownIt({ html: false, breaks: true, linkify: true, typographer: true })
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
      <div v-if="messages.length === 0" class="chat-welcome">
        <span class="welcome-mark"><el-icon><ChatDotRound /></el-icon></span>
        <h1>今天想了解什么？</h1>
        <p>我会基于你有权限访问的校园知识库查找信息并组织回答。</p>
      </div>
      <div v-for="(msg, index) in messages" :key="index" class="message-row"
           :class="msg.role === 'user' ? 'is-user' : 'is-assistant'">
        <div class="message-avatar" aria-hidden="true">
          <el-icon v-if="msg.role === 'user'"><UserFilled /></el-icon><span v-else>AI</span>
        </div>
        <div class="message-content">
          <span class="message-role">{{ msg.role === 'user' ? '你' : '校灵通助手' }}</span>
          <div class="message-bubble">
            <template v-if="msg.role === 'user'">{{ msg.content }}</template>
            <div v-else-if="msg.content" class="markdown-body" v-html="md.render(msg.content)"></div>
            <div v-else class="generating-status"><i /><i /><i /><span>{{ isStopping ? '正在停止' : '正在检索并组织回答' }}</span></div>
          </div>
          <el-tooltip v-if="msg.id && !isStreaming" content="删除此消息及后续内容" placement="bottom">
            <button class="message-delete-btn" type="button" aria-label="删除此消息及后续内容" @click="$emit('delete-message', msg)"><el-icon><Delete /></el-icon></button>
          </el-tooltip>
        </div>
      </div>
    </div>
    <div class="chat-input-area">
      <div class="chat-composer">
        <div class="chat-input-wrapper">
          <textarea
            v-model="inputContent"
            class="chat-textarea"
            placeholder="向校园知识库提问"
            rows="1"
            aria-label="输入问题"
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
          circle
          @click="isStreaming ? emit('stop') : handleSend()"
          :disabled="isStopping || (!isStreaming && (!inputContent.trim() || isOverLimit))"
          :aria-label="isStreaming ? '停止生成' : '发送消息'"
          :title="isStreaming ? '停止生成' : '发送消息'"
        >
          <el-icon><VideoPause v-if="isStreaming"/><Position v-else/></el-icon>
        </el-button>
      </div>
      <span class="composer-note">回答由知识库生成，请结合原始资料核验重要信息</span>
    </div>
  </section>
</template>

<style scoped>
.main-chat { min-width: 0; flex: 1; display: flex; flex-direction: column; min-height: 0; overflow: hidden; background: #fff; }
.chat-messages { flex: 1; overflow-y: auto; padding: 34px max(24px, calc((100% - 900px) / 2)); min-height: 0; scroll-behavior: smooth; }
.chat-welcome { max-width: 720px; margin: clamp(28px, 9vh, 96px) auto 0; text-align: center; }
.welcome-mark { width: 48px; height: 48px; display: inline-grid; place-items: center; border-radius: 8px; background: var(--color-primary-soft); color: var(--color-primary); font-size: 24px; }
.chat-welcome h1 { margin: 20px 0 8px; font-size: 28px; font-weight: 650; letter-spacing: 0; }
.chat-welcome > p { margin: 0; color: var(--color-text-secondary); font-size: 14px; line-height: 1.7; }
.message-row { max-width: 820px; margin: 0 auto 28px; display: flex; align-items: flex-start; gap: 12px; }
.message-row.is-user { flex-direction: row-reverse; }
.message-avatar { width: 32px; height: 32px; flex: 0 0 32px; display: grid; place-items: center; border-radius: 6px; background: var(--color-primary); color: #fff; font-size: 12px; font-weight: 700; }
.is-assistant .message-avatar { background: #edf1f3; color: #52606d; }
.message-content { max-width: min(720px, calc(100% - 44px)); display: flex; flex-direction: column; align-items: flex-start; }
.is-user .message-content { align-items: flex-end; }
.message-role { margin-bottom: 5px; color: var(--color-text-muted); font-size: 12px; }
.message-bubble { max-width: 100%; padding: 11px 15px; border-radius: 6px; color: var(--color-text); font-size: 14px; line-height: 1.75; overflow-wrap: anywhere; }
.is-assistant .message-bubble { padding: 2px 0; background: transparent; }
.is-user .message-bubble { background: var(--color-primary); color: #fff; }
.message-delete-btn { width: 30px; height: 30px; margin-top: 3px; padding: 0; display: grid; place-items: center; opacity: 0; border: 0; border-radius: 4px; background: transparent; color: var(--color-text-muted); cursor: pointer; transition: opacity .15s, background-color .15s, color .15s; }
.message-row:hover .message-delete-btn, .message-delete-btn:focus-visible { opacity: 1; }
.message-delete-btn:hover { background: #fff0f0; color: var(--color-danger); }
.generating-status { min-height: 30px; display: flex; align-items: center; gap: 5px; color: var(--color-text-secondary); font-size: 13px; }
.generating-status i { width: 5px; height: 5px; border-radius: 50%; background: var(--color-primary); animation: thinking 1.2s infinite ease-in-out; }
.generating-status i:nth-child(2) { animation-delay: .15s; }
.generating-status i:nth-child(3) { animation-delay: .3s; margin-right: 5px; }
.markdown-body { max-width: 100%; }
.markdown-body :deep(h1), .markdown-body :deep(h2), .markdown-body :deep(h3) { margin: 1.35em 0 .55em; color: var(--color-text); line-height: 1.35; font-weight: 650; letter-spacing: 0; }
.markdown-body :deep(h1) { font-size: 21px; }
.markdown-body :deep(h2) { font-size: 18px; }
.markdown-body :deep(h3) { font-size: 16px; }
.markdown-body :deep(p) { margin: 0 0 .85em; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin: .6em 0 .9em; padding-left: 1.5em; }
.markdown-body :deep(li) { margin: .32em 0; }
.markdown-body :deep(blockquote) { margin: 1em 0; padding: 8px 14px; border-left: 3px solid var(--color-accent); background: #faf8f2; color: #5d6670; }
.markdown-body :deep(a) { color: var(--color-primary); text-underline-offset: 3px; }
.markdown-body :deep(code) { padding: 2px 5px; border-radius: 4px; background: #edf1f2; color: #384650; font-family: Consolas, "SFMono-Regular", monospace; font-size: .9em; }
.markdown-body :deep(pre) { max-width: 100%; margin: 1em 0; padding: 14px 16px; overflow-x: auto; border-radius: 6px; background: #202a31; color: #e7edf0; line-height: 1.6; }
.markdown-body :deep(pre code) { padding: 0; background: transparent; color: inherit; }
.markdown-body :deep(table) { display: block; width: 100%; margin: 1em 0; overflow-x: auto; border-collapse: collapse; }
.markdown-body :deep(th), .markdown-body :deep(td) { min-width: 110px; padding: 8px 10px; border: 1px solid var(--color-border); text-align: left; }
.markdown-body :deep(th) { background: #f5f7f8; font-weight: 600; }
.markdown-body :deep(hr) { margin: 20px 0; border: 0; border-top: 1px solid var(--color-border); }
.chat-input-area { flex-shrink: 0; padding: 12px max(24px, calc((100% - 900px) / 2)) 10px; border-top: 1px solid var(--color-border); background: #fff; }
.chat-composer { display: flex; align-items: flex-end; gap: 8px; }
.chat-input-wrapper { position: relative; flex: 1; min-width: 0; }
.chat-textarea { display: block; width: 100%; min-height: 44px; resize: none; border: 1px solid #cfd8dd; border-radius: 6px; padding: 9px 68px 9px 13px; font-size: 14px; line-height: 24px; max-height: 120px; outline: none; transition: border-color .15s, box-shadow .15s; font-family: inherit; }
.chat-textarea:focus { border-color: var(--color-primary); box-shadow: 0 0 0 3px rgb(20 125 115 / 10%); }
.send-btn { width: 44px; height: 44px; flex: 0 0 44px; }
.composer-note { display: block; margin-top: 7px; color: var(--color-text-muted); font-size: 11px; text-align: center; }
@keyframes thinking { 0%, 70%, 100% { opacity: .28; transform: translateY(0); } 35% { opacity: 1; transform: translateY(-2px); } }

@media (max-width: 768px) {
  .chat-messages { padding: 22px 12px; }
  .chat-welcome { margin-top: 24px; }
  .chat-welcome h1 { font-size: 23px; }
  .message-row { gap: 8px; margin-bottom: 22px; }
  .message-avatar { width: 28px; height: 28px; flex-basis: 28px; }
  .message-content { max-width: calc(100% - 36px); }
  .message-bubble { max-width: 100%; padding: 9px 12px; }
  .message-delete-btn { opacity: 1; }
  .message-bubble :deep(pre), .message-bubble :deep(table) { max-width: 100%; overflow-x: auto; }
  .chat-input-area { padding: 8px 8px max(8px, env(safe-area-inset-bottom)); }
  .send-btn { width: 44px; padding: 0; }
  .composer-note { display: none; }
}
</style>
