<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'

defineProps({
  items: { type: Array, required: true },
  open: { type: Boolean, default: false }
})

defineEmits(['close'])

const route = useRoute()
const activePath = computed(() => route.path)
</script>

<template>
  <div class="app-navigation-mask" :class="{ 'is-visible': open }" @click="$emit('close')" />
  <aside class="app-sidebar" :class="{ 'is-mobile-open': open }">
    <div class="app-sidebar-label">工作区导航</div>
    <el-menu router :default-active="activePath" @select="$emit('close')">
      <el-menu-item v-for="item in items" :key="item.path" :index="item.path">
        <el-icon><component :is="item.icon" /></el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
    <div class="app-sidebar-footer">校园知识服务</div>
  </aside>
</template>
