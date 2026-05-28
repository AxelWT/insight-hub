<script setup lang="ts">
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <div class="vp-layout">
    <aside class="vp-sidebar">
      <Sidebar />
    </aside>
    <main class="vp-main">
      <div class="vp-main-content">
        <router-view />
      </div>
    </main>
  </div>
</template>
