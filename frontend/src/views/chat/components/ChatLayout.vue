<script setup>
import { useCurrentUser } from '@/hooks/useCurrentUser.js'
import { ref, watch, nextTick } from 'vue'
import { createSession, deleteSession, renameSession, sessionByUserId } from '@/api/session.js'
import { chat, deleteMessagesAfter, deleteMessagesBySessionId, messageBySessionId } from '@/api/message.js'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router/index.js'
import { House, SwitchButton } from '@element-plus/icons-vue'
import SessionSidebar from './SessionSidebar.vue'
import ChatPanel from './ChatPanel.vue'

const { user } = useCurrentUser()
const sessions = ref([])
const sessionsLoading = ref(false)
const currentSessionId = ref(0)
const messages = ref([])

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

const handleSessionClick = async (sessionId) => {
  const res = await messageBySessionId(sessionId)
  if (res.code) {
    messages.value = res.data
    currentSessionId.value = sessionId
    scrollToBottom()
  } else {
    ElMessage.error(res.msg)
  }
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
    type: 'info'
  }).then(async ({ value }) => {
    await renameSession(session.id, value)
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

const createSessionBtn = async () => {
  const res = await createSession({
    user_id: user.value.id,
    name: '新建会话',
    create_time: null,
    update_time: null,
    id: null
  })
  if (res.code) {
    ElMessage.success('创建成功')
    const result = await sessionByUserId(user.value.id)
    sessions.value = result.data
    currentSessionId.value = res.data.id
    messages.value = []
  } else {
    ElMessage.error(res.msg)
  }
}

const switchToMyPage = async () => {
  await router.push({ path: '/user' })
}

const handleSend = async (content) => {
  // 1. 确保会话存在
  if (currentSessionId.value === 0) {
    await createSessionBtn()
  }

  // 2. 先追加用户消息到界面
  const userMsg = {
    id: null,
    role: 'user',
    content,
    rewritten_content: null,
    session_id: currentSessionId.value,
    create_time: new Date().toISOString()
  }
  messages.value.push(userMsg)
  await nextTick(() => scrollToBottom())

  // 3. 发送消息并获取AI回复
  // 注意：chat API 现在应返回 AI 的回复内容，而非仅确认收到
  const res = await chat(userMsg)

  // 4. 刷新消息列表
  if (res.code) {
    await handleSessionClick(currentSessionId.value)
  }

  // 5. 仅在必要时刷新会话列表（如标题可能已更新）
  const sessionRes = await sessionByUserId(user.value.id)
  sessions.value = sessionRes.data
}

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
      <div class="header-left">校灵通</div>
      <div class="header-center"></div>
      <div class="header-right">
        <a href="javascript:0" @click="switchToMyPage" class="my-btn">
          <el-icon><House /></el-icon> 我的
        </a>
        <a href="javascript:0" @click="logout" class="logout-btn">
          <el-icon><SwitchButton/></el-icon> 退出登录 【{{ user?.username }}】
        </a>
      </div>
    </header>
    <main class="app-main">
      <SessionSidebar
        :sessions="sessions"
        :loading="sessionsLoading"
        :current-id="currentSessionId"
        @select="handleSessionClick"
        @rename="handleRename"
        @delete="handleDelete"
        @create="createSessionBtn"
      />
      <ChatPanel
        :messages="messages"
        :current-session-id="currentSessionId"
        @send="handleSend"
        @delete-message="handleDeleteMessage"
      />
    </main>
    <footer class="app-footer">Copyright © 2026-2026 · 校灵通</footer>
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
</style>