<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: { type: Boolean, default: false },
  sources: { type: Array, default: () => [] }
})

const emit = defineEmits(['update:visible'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})
</script>

<template>
  <el-dialog
    v-model="dialogVisible"
    title="回答来源"
    width="680px"
    top="8vh"
    destroy-on-close
  >
    <div class="source-list">
      <section
        v-for="(source, index) in sources"
        :key="source.chunk_id || index"
        class="source-item"
      >
        <strong class="source-filename">{{ source.filename }}</strong>
        <pre class="source-content">{{ source.content }}</pre>
      </section>
    </div>

    <template #footer>
      <el-button @click="dialogVisible = false">关闭</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.source-list {
  max-height: 65vh;
  overflow-y: auto;
  padding-right: 4px;
}

.source-item {
  padding: 0 2px 20px;
}

.source-item + .source-item {
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
}

.source-item:last-child {
  padding-bottom: 0;
}

.source-filename {
  display: block;
  margin-bottom: 10px;
  color: var(--color-text);
  font-size: 14px;
  overflow-wrap: anywhere;
}

.source-content {
  margin: 0;
  color: var(--color-text-secondary);
  font-family: inherit;
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}
</style>
