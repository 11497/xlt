<script setup>

</script>

<template>
  <div class="container">
    <img src="@/assets/index.png" alt="index" class="index-image">
  </div>
</template>

<style scoped>
.container {
  margin: 15px 0;
  display: flex;
  justify-content: center;
  height: 80vh;
}

.index-image {
  max-width: 100%;
  max-height: 80vh;
  width: auto;
  height: auto;
  object-fit: contain;
}
</style>