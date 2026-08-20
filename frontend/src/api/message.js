import request from "@/utils/request.js";
import router from '@/router/index.js'

// 通过会话ID查询所有消息
export const messageBySessionId = (sessionId) => request.get(`/message/session/${sessionId}`)

// 发送消息，并逐行解析后端返回的 NDJSON 流
export const chat = async (message, onEvent) => {
  const loginUserStr = localStorage.getItem('loginUser')
  let token = null

  try {
    token = loginUserStr ? JSON.parse(loginUserStr) : null
  } catch {
    localStorage.removeItem('loginUser')
  }

  const response = await fetch('/api/message/chat', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/x-ndjson',
      ...(token ? { Authorization: `Bearer ${token}` } : {})
    },
    body: JSON.stringify(message)
  })

  const contentType = response.headers.get('content-type') || ''
  if (!response.ok || !contentType.includes('application/x-ndjson')) {
    const body = await response.json().catch(() => null)
    if (response.status === 401) {
      localStorage.removeItem('loginUser')
      await router.push('/login')
    }
    throw new Error(body?.msg || body?.detail || `请求失败 (${response.status})`)
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式响应')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''
  let completedEvent = null

  const consumeLine = (line) => {
    if (!line.trim()) return
    const event = JSON.parse(line)
    if (event.type === 'error') {
      throw new Error(event.message || 'AI 回复生成失败')
    }
    onEvent?.(event)
    if (event.type === 'done') completedEvent = event
  }

  while (true) {
    const { value, done } = await reader.read()
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    lines.forEach(consumeLine)
    if (done) break
  }

  consumeLine(buffer)
  if (!completedEvent) throw new Error('AI 回复流意外中断')
  return completedEvent
}

// 删除指定消息ID及之后的所有消息
export const deleteMessagesAfter = (session_id, message_id) => request.delete(`/message/after?session_id=${session_id}&message_id=${message_id}`)

// 查询消息详情
export const getMessageById = (messageId) => request.get(`/message/${messageId}`);

// 删除指定会话ID下的所有消息
export const deleteMessagesBySessionId = (sessionId) => request.delete(`/message/session/${sessionId}`);
