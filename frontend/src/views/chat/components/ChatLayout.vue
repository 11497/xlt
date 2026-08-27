<script setup>
import { useCurrentUser } from '@/hooks/useCurrentUser.js'
import { reactive, ref, watch, nextTick, onBeforeUnmount } from 'vue'
import { createSession, deleteSession, renameSession, sessionByUserId } from '@/api/session.js'
import { chat, deleteMessagesAfter, deleteMessagesBySessionId, messageBySessionId, stopChat } from '@/api/message.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router/index.js'
import { House, Menu, SwitchButton } from '@element-plus/icons-vue'
import SessionSidebar from './SessionSidebar.vue'
import ChatPanel from './ChatPanel.vue'

const { user } = useCurrentUser()
const sessions = ref([])
const sessionsLoading = ref(false)
const currentSessionId = ref(0)
const messages = ref([])
const isStreaming = ref(false)
const isStopping = ref(false)
const sidebarOpen = ref(false)
let activeChatController = null
let activeServerRequestId = null
let activeChatRequestId = 0

watch(
  () => user.value?.id,
  async (newId) => {
    if (!newId) return
    sessionsLoading.value = true
    try {
      const res = await sessionByUserId(newId)
      sessions.value = res.data
    } finally {
      sessionsLoading.value = false
    }
  },
  { immediate: true }
)

const loadSessionMessages = async (sessionId) => {
  const res = await messageBySessionId(sessionId)
  if (res.code) {
    messages.value = res.data
    currentSessionId.value = sessionId
    scrollToBottom()
  } else {
    ElMessage.error(res.msg)
  }
}

const cancelForNavigation = () => {
  if (!activeChatController) return

  const controller = activeChatController
  activeChatRequestId += 1
  activeChatController = null
  activeServerRequestId = null
  isStreaming.value = false
  isStopping.value = false
  controller.abort()
}

const handleSessionClick = async (sessionId) => {
  sidebarOpen.value = false
  cancelForNavigation()
  await loadSessionMessages(sessionId)
}

const scrollToBottom = () => {
  nextTick(() => {
    const container = document.querySelector('.chat-messages')
    if (container) container.scrollTop = container.scrollHeight
  })
}

const logout = () => {
  ElMessageBox.confirm('确定要退出登录吗?', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    cancelForNavigation()
    ElMessage.success('退出成功')
    localStorage.removeItem('loginUser')
    await router.push({ path: '/login' })
  }).catch(() => {
    ElMessage.info('已取消退出')
  })
}

const handleRename = (session) => {
  ElMessageBox.prompt(`确定要重命名会话「${session.name}」吗？`, '重命名', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'info',
    inputValue: session.name,
    inputValidator: (value) => {
      const name = value?.trim() || ''
      if (!name) return '会话名称不能为空'
      if (Array.from(name).length > 20) return '会话名称不能超过 20 个字符'
      return true
    }
  }).then(async ({ value }) => {
    await renameSession(session.id, value.trim())
    const res = await sessionByUserId(user.value.id)
    sessions.value = res.data
  }).catch(() => {})
}

const handleDelete = (session) => {
  ElMessageBox.confirm(`确定要删除会话「${session.name}」吗？`, '删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    cancelForNavigation()
    await deleteMessagesBySessionId(session.id)
    await deleteSession(session.id)
    const res = await sessionByUserId(user.value.id)
    sessions.value = res.data
    if (currentSessionId.value === session.id) {
      currentSessionId.value = 0
      messages.value = []
    }
  }).catch(() => {})
}

const handleNewSession = () => {
  sidebarOpen.value = false
  cancelForNavigation()
  currentSessionId.value = 0
  messages.value = []
}

const createSessionForMessage = async () => {
  const res = await createSession({
    user_id: user.value.id,
    name: '新建会话'
  })
  if (res.code) {
    currentSessionId.value = res.data.id
    return res.data.id
  }

  throw new Error(res.msg || '创建会话失败')
}

const switchToMyPage = async () => {
  cancelForNavigation()
  await router.push({ path: '/user' })
}

const handleStopGeneration = async () => {
  if (!activeChatController || isStopping.value) return

  // 建流前还没有服务端请求 ID，此时只能直接取消请求。
  if (!activeServerRequestId) {
    activeChatController.abort()
    return
  }

  isStopping.value = true
  try {
    const res = await stopChat(activeServerRequestId)
    if (!res.code) {
      isStopping.value = false
      ElMessage.error(res.msg || '停止生成失败')
    }
  } catch {
    isStopping.value = false
  }
}

const handleSend = async (content) => {
  if (isStreaming.value) return
  isStreaming.value = true

  const controller = new AbortController()
  const requestId = ++activeChatRequestId
  activeChatController = controller
  activeServerRequestId = null
  isStopping.value = false

  let assistantMsg = null
  let targetSessionId = 0

  try {
    // 1. 首次发送消息时再创建会话
    targetSessionId = currentSessionId.value || await createSessionForMessage()
    if (controller.signal.aborted || requestId !== activeChatRequestId) {
      throw new DOMException('请求已取消', 'AbortError')
    }

    // 2. 先追加用户消息到界面
    const userMsg = reactive({
      role: 'user',
      content,
      session_id: targetSessionId,
      create_time: new Date().toISOString()
    })
    messages.value.push(userMsg)
    assistantMsg = reactive({
      role: 'assistant',
      content: '',
      session_id: targetSessionId,
      create_time: new Date().toISOString()
    })
    messages.value.push(assistantMsg)
    await nextTick(() => scrollToBottom())

    // 3. 逐段接收 AI 回复并更新当前消息气泡
    await chat(userMsg, (event) => {
      if (event.type === 'start') {
        userMsg.id = event.user_message_id
        activeServerRequestId = event.request_id || null
      } else if (event.type === 'delta') {
        assistantMsg.content += event.content
        scrollToBottom()
      } else if (event.type === 'done' || event.type === 'stopped') {
        assistantMsg.id = event.assistant_message_id
      }
    }, { signal: controller.signal })

    if (requestId === activeChatRequestId) {
      activeChatController = null
      activeServerRequestId = null
      isStreaming.value = false
      isStopping.value = false

      if (!assistantMsg.content) {
        const index = messages.value.indexOf(assistantMsg)
        if (index !== -1) messages.value.splice(index, 1)
      }
    }

    // 4. 刷新会话列表（第一轮对话可能已生成标题）
    const sessionRes = await sessionByUserId(user.value.id)
    sessions.value = sessionRes.data
  } catch (error) {
    const isCurrentRequest = requestId === activeChatRequestId
    const isCancelled = controller.signal.aborted

    // 断网、离页或失败不保存部分回复，此时以持久化历史为准。
    if (isCurrentRequest && targetSessionId && currentSessionId.value === targetSessionId) {
      try {
        await loadSessionMessages(targetSessionId)
        const sessionRes = await sessionByUserId(user.value.id)
        sessions.value = sessionRes.data
      } catch {
        const index = messages.value.indexOf(assistantMsg)
        if (index !== -1) messages.value.splice(index, 1)
      }
    }

    if (isCurrentRequest) {
      if (isCancelled) {
        ElMessage.info('已停止生成')
      } else {
        ElMessage.error(error.message || '发送消息失败')
      }
    }
  } finally {
    if (requestId === activeChatRequestId) {
      activeChatController = null
      activeServerRequestId = null
      isStreaming.value = false
      isStopping.value = false
    }
  }
}

onBeforeUnmount(cancelForNavigation)

const handleDeleteMessage = async (msg) => {
  ElMessageBox.confirm('确定要删除该消息吗？', '删除', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    const res = await deleteMessagesAfter(currentSessionId.value, msg.id)
    if (res.code) {
      ElMessage.success('删除成功')
      await handleSessionClick(currentSessionId.value)
    } else {
      ElMessage.error(res.msg)
    }
  }).catch(() => {})
}
</script> 

<template>
  <div class="app-layout">
    <header class="app-header">
      <button class="mobile-menu-button" type="button" aria-label="打开会话列表" title="会话列表" @click="sidebarOpen = true">
        <el-icon><Menu /></el-icon>
      </button>
      <div class="header-left">校灵通</div>
      <div class="header-center"></div>
      <div class="header-right">
        <a href="javascript:0" @click="switchToMyPage" class="my-btn" aria-label="我的" title="我的">
          <el-icon><House /></el-icon> 我的
        </a>
        <a href="javascript:0" @click="logout" class="logout-btn" aria-label="退出登录" title="退出登录">
          <el-icon><SwitchButton/></el-icon> 退出登录 【{{ user?.username }}】
        </a>
      </div>
    </header>
    <main class="app-main">
      <div class="mobile-sidebar-mask" :class="{ 'is-visible': sidebarOpen }" @click="sidebarOpen = false"></div>
      <SessionSidebar
        :class="{ 'is-mobile-open': sidebarOpen }"
        :sessions="sessions"
        :loading="sessionsLoading"
        :current-id="currentSessionId"
        @select="handleSessionClick"
        @rename="handleRename"
        @delete="handleDelete"
        @create="handleNewSession"
      />
      <ChatPanel
        :messages="messages"
        :current-session-id="currentSessionId"
        :is-streaming="isStreaming"
        :is-stopping="isStopping"
        @send="handleSend"
        @stop="handleStopGeneration"
        @delete-message="handleDeleteMessage"
      />
    </main>
  </div>
</template>

<style>
/* 此处放入原文档中 .app-layout, .app-header, .app-main, .app-footer 相关的所有样式 */
body { margin: 0; }
.app-layout { height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
.app-header { height: 60px; flex-shrink: 0; display: flex; align-items: center; gap: 16px; padding: 0 20px; background-image: linear-gradient(to right, #00547d, #007fa4, #00aaa0); }
.header-left { color: white; font-size: 40px; font-family: 楷体, serif; line-height: 60px; font-weight: bolder; }
.header-center { flex: 1; text-align: center; }
.header-right { white-space: nowrap; }
.app-main { flex: 1; display: flex; overflow: hidden; }
.app-footer { height: 40px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background-color: #f5f7fa; border-top: 1px solid #dcdfe6; }
a { text-decoration: none; }
.logout-btn { color: red; margin: 0 15px; font-size: 18px; }
.my-btn { color: white; margin: 0 15px; font-size: 18px; }

@media (max-width: 768px) {
  .app-layout { height: 100dvh; }
  .app-header { height: 52px; gap: 10px; padding: 0 12px; }
  .mobile-menu-button { display: inline-flex; width: 36px; height: 36px; padding: 0; align-items: center; justify-content: center; border: 0; background: transparent; color: #fff; font-size: 22px; cursor: pointer; }
  .header-left { font-size: 28px; line-height: 52px; }
  .header-center { display: none; }
  .header-right { margin-left: auto; display: flex; align-items: center; }
  .my-btn, .logout-btn { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; margin: 0 2px; font-size: 0; }
  .my-btn .el-icon, .logout-btn .el-icon { font-size: 20px; }
  .app-main { position: relative; }
  .main-left { position: fixed; z-index: 2002; top: 0; bottom: 0; left: 0; width: min(82vw, 300px) !important; transform: translateX(-100%); transition: transform 0.2s ease; box-shadow: 4px 0 16px rgb(0 0 0 / 18%); }
  .main-left.is-mobile-open { transform: translateX(0); }
  .mobile-sidebar-mask { position: fixed; z-index: 2001; inset: 0; display: block; background: rgb(0 0 0 / 40%); opacity: 0; visibility: hidden; transition: opacity 0.2s ease, visibility 0.2s ease; }
  .mobile-sidebar-mask.is-visible { opacity: 1; visibility: visible; }
}
</style>
