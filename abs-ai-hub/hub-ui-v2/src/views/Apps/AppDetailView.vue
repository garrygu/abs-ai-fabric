<template>
  <div class="app-detail">
    <router-link :to="`/workspace/${workspaceId}/apps`" class="back-link">
      ← Back to Apps
    </router-link>
    <h1>App Detail: {{ appId }}</h1>
    <p class="placeholder">Full app detail view coming soon...</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const workspaceId = computed(() => route.params.workspaceId as string)
const appId = computed(() => route.params.appId as string)
</script>

<style scoped>
.back-link {
  color: #818cf8;
  text-decoration: none;
}
.placeholder {
  color: #888;
  margin-top: 1rem;
}
</style>
