<script setup>
import { ChatLineSquare, EditPen, Delete, Plus, MoreFilled } from '@element-plus/icons-vue'

defineProps({
  sessions: Array,
  loading: Boolean,
  currentId: Number
})
defineEmits(['select', 'rename', 'delete', 'create'])
</script>

<template>
  <aside class="main-left">
    <div class="sessions-header"><span><el-icon><ChatLineSquare /></el-icon>最近对话</span><small>保留你的校园问答记录</small></div>
    <el-button type="primary" class="sessions-create-btn" @click="$emit('create')"><el-icon><Plus /></el-icon>新建对话</el-button>
    <div class="sessions-list">
      <div
        v-for="session in sessions"
        :key="session.id"
        class="session-item"
        :class="{ 'is-active': session.id === currentId }"
        @click="$emit('select', session.id)"
      >
        <div class="session-name">{{ session.name }}</div>
        <el-popover placement="bottom-end" :width="120" trigger="click" popper-class="session-popover">
          <template #reference>
            <button class="session-more-btn" type="button" aria-label="会话操作" title="会话操作" @click.stop><el-icon><MoreFilled /></el-icon></button>
          </template>
          <div class="session-popover-menu">
            <div class="menu-item" @click.stop="$emit('rename', session)">
              <el-icon><EditPen /></el-icon> 重命名
            </div>
            <div class="menu-item danger" @click.stop="$emit('delete', session)">
              <el-icon><Delete /></el-icon> 删除
            </div>
          </div>
        </el-popover>
      </div>
      <div v-if="loading" class="loading-text"><span class="loading-dot" />正在加载会话</div>
      <div v-else-if="sessions && sessions.length === 0" class="empty-text">暂无历史会话<br><small>提问后会自动保存在这里</small></div>
    </div>
  </aside>
</template>

<style scoped>
.main-left { width: 248px; flex-shrink: 0; background-color: #ffffff; border-right: 1px solid var(--color-border); display: flex; flex-direction: column; min-height: 0; }
.sessions-header { padding: 20px 16px 12px; flex-shrink: 0; }
.sessions-header span { display: flex; align-items: center; gap: 7px; color: var(--color-text); font-weight: 650; }
.sessions-header small { display: block; margin-top: 5px; color: var(--color-text-muted); font-size: 11px; font-weight: 400; }
.sessions-create-btn { margin: 4px 12px 12px; }
.sessions-list { flex: 1; overflow-y: auto; min-height: 0; overscroll-behavior: contain; scrollbar-gutter: stable; }
.sessions-list::-webkit-scrollbar { width: 4px; }
.sessions-list::-webkit-scrollbar-track { background: #f1f1f1; }
.sessions-list::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 2px; }
.sessions-list::-webkit-scrollbar-thumb:hover { background: #909399; }
.session-item { min-height: 44px; padding: 9px 10px 9px 12px; margin: 2px 8px; cursor: pointer; transition: background-color 0.15s; border-radius: 6px; display: flex; align-items: center; justify-content: space-between; border-left: 3px solid transparent; }
.session-item:hover { background-color: #f2f6f5; }
.session-item.is-active { border-left-color: var(--color-primary); background-color: var(--color-primary-soft); }
.session-item.is-active .session-name { color: var(--color-primary-dark); font-weight: 600; }
.session-item.is-active .session-more-btn { color: var(--color-primary-dark); }
.session-item.is-active:hover { background-color: var(--color-primary-soft); }
.session-item:last-child { border-bottom: none; }
.session-name { font-size: 14px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.loading-text, .empty-text { padding: 28px 16px; text-align: center; color: var(--color-text-muted); font-size: 13px; line-height: 1.7; }
.empty-text small { font-size: 11px; }
.loading-dot { display: inline-block; width: 6px; height: 6px; margin-right: 8px; border-radius: 50%; background: var(--color-primary); animation: loading-pulse 1.2s ease-in-out infinite; }
.session-more-btn { display: none; width: 30px; height: 30px; flex: 0 0 auto; padding: 0; place-items: center; border: 0; font-size: 17px; color: #909399; cursor: pointer; background: transparent; border-radius: 4px; }
.session-more-btn:hover { color: #303133; background-color: #e4e7ed; }
.session-item:hover .session-more-btn { display: inline-block; }
.session-popover-menu { display: flex; flex-direction: column; gap: 4px; }
.session-popover-menu .menu-item { padding: 8px 12px; font-size: 14px; cursor: pointer; border-radius: 4px; transition: background-color 0.2s; color: #303133; }
.session-popover-menu .menu-item:hover { background-color: #f5f7fa; }
.session-popover-menu .menu-item.danger { color: #f56c6c; }
.session-popover-menu .menu-item.danger:hover { background-color: #fef0f0; }
@keyframes loading-pulse { 50% { opacity: .35; } }

@media (max-width: 768px) {
  .session-more-btn { display: grid; min-width: 40px; min-height: 40px; }
}
</style>
