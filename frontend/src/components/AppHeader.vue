<script setup>
import { Menu, Reading, SwitchButton } from '@element-plus/icons-vue'

defineProps({
  username: { type: String, default: '' },
  section: { type: String, default: '' }
})

defineEmits(['menu', 'logout'])
</script>

<template>
  <header class="app-shell-header">
    <button class="app-icon-button app-shell-menu" type="button" aria-label="打开导航菜单" title="导航菜单" @click="$emit('menu')">
      <el-icon><Menu /></el-icon>
    </button>
    <div class="app-brand" aria-label="校灵通校园知识工作台">
      <span class="app-brand-mark" aria-hidden="true"><el-icon><Reading /></el-icon></span>
      <span class="app-brand-copy">
        <strong>校灵通</strong>
        <small v-if="section">{{ section }}</small>
      </span>
    </div>
    <div class="app-shell-actions">
      <slot name="actions" />
      <span v-if="username" class="app-user-name" :title="username">{{ username }}</span>
      <el-tooltip content="退出登录" placement="bottom">
        <button class="app-icon-button" type="button" aria-label="退出登录" @click="$emit('logout')">
          <el-icon><SwitchButton /></el-icon>
        </button>
      </el-tooltip>
    </div>
  </header>
</template>
