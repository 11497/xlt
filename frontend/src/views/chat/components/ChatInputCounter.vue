<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  count: {
    type: Number,
    required: true
  },
  maxLength: {
    type: Number,
    required: true
  }
})

const status = computed(() => {
  const ratio = props.maxLength > 0 ? props.count / props.maxLength : 1
  if (ratio >= 1) return 'limit'
  if (ratio >= 0.8) return 'warning'
  return 'normal'
})

const liveMessage = ref('')

watch(status, (currentStatus, previousStatus) => {
  if (currentStatus === previousStatus) return

  if (currentStatus === 'limit') {
    liveMessage.value = `已达到 ${props.maxLength} 个字符的输入上限，发送按钮已禁用`
  } else if (currentStatus === 'warning') {
    liveMessage.value = `输入内容已达到上限的百分之八十，当前 ${props.count} 个字符，上限 ${props.maxLength} 个字符`
  } else if (previousStatus) {
    liveMessage.value = '输入字数已恢复到安全范围'
  }
})
</script>

<template>
  <div class="character-counter">
    <span
      v-if="status !== 'normal'"
      class="counter-value"
      :class="`is-${status}`"
      aria-hidden="true"
    >
      {{ count }}/{{ maxLength }}
    </span>
    <span id="chat-input-count-status" class="sr-only" role="status" aria-live="polite" aria-atomic="true">
      {{ liveMessage }}
    </span>
  </div>
</template>

<style scoped>
.character-counter {
  position: absolute;
  right: 12px;
  bottom: 5px;
  z-index: 1;
  pointer-events: none;
  font-size: 12px;
  line-height: 16px;
}
.counter-value { display: block; padding: 0 4px; color: #606266; background-color: #fff; }
.counter-value.is-warning { color: #946200; }
.counter-value.is-limit { color: #d93025; font-weight: 600; }
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
</style>
