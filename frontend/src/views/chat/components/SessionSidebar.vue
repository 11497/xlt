<script setup>
import { ChatLineSquare, EditPen, Delete } from '@element-plus/icons-vue'

defineProps({
  sessions: Array,
  loading: Boolean,
  currentId: Number
})
defineEmits(['select', 'rename', 'delete', 'create'])
</script>

<template>
  <aside class="main-left">
    <div class="sessions-header"><el-icon><ChatLineSquare /></el-icon> 对话列表</div>
    <el-button type="primary" class="sessions-create-btn" @click="$emit('create')">创建对话</el-button>
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
            <span class="session-more-btn" @click.stop>⋯</span>
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
      <div v-if="loading" class="loading-text">加载中...</div>
      <div v-else-if="sessions && sessions.length === 0" class="empty-text">暂无会话</div>
    </div>
  </aside>
</template>

<style scoped>
.main-left { width: 200px; flex-shrink: 0; background-color: #ffffff; border-right: 1px solid #dcdfe6; display: flex; flex-direction: column; min-height: 0; }
.sessions-header { padding: 16px; font-weight: bold; border-bottom: 1px solid #dcdfe6; background-color: #f5f7fa; flex-shrink: 0; }
.sessions-create-btn { margin: 15px 15px 10px 10px; }
.sessions-list { flex: 1; overflow-y: auto; min-height: 0; overscroll-behavior: contain; scrollbar-gutter: stable; }
.sessions-list::-webkit-scrollbar { width: 4px; }
.sessions-list::-webkit-scrollbar-track { background: #f1f1f1; }
.sessions-list::-webkit-scrollbar-thumb { background: #c0c4cc; border-radius: 2px; }
.sessions-list::-webkit-scrollbar-thumb:hover { background: #909399; }
.session-item { padding: 12px 16px; margin: 4px 8px; cursor: pointer; transition: background-color 0.2s; border-radius: 8px; display: flex; align-items: center; justify-content: space-between; background-color: rgb(243 243 243); }
.session-item:hover { background-color: #e8f1ff; }
.session-item.is-active { background-color: #409eff; }
.session-item.is-active .session-name { color: #fff; }
.session-item.is-active .session-more-btn { color: #fff; }
.session-item.is-active:hover { background-color: #409eff; }
.session-item:last-child { border-bottom: none; }
.session-name { font-size: 14px; color: #303133; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.loading-text, .empty-text { padding: 16px; text-align: center; color: #909399; font-size: 14px; }
.session-more-btn { display: none; font-size: 18px; color: #909399; cursor: pointer; padding: 0 4px; line-height: 1; flex-shrink: 0; user-select: none; border-radius: 4px; transition: background-color 0.2s, color 0.2s; }
.session-more-btn:hover { color: #303133; background-color: #e4e7ed; }
.session-item:hover .session-more-btn { display: inline-block; }
.session-popover-menu { display: flex; flex-direction: column; gap: 4px; }
.session-popover-menu .menu-item { padding: 8px 12px; font-size: 14px; cursor: pointer; border-radius: 4px; transition: background-color 0.2s; color: #303133; }
.session-popover-menu .menu-item:hover { background-color: #f5f7fa; }
.session-popover-menu .menu-item.danger { color: #f56c6c; }
.session-popover-menu .menu-item.danger:hover { background-color: #fef0f0; }
</style>