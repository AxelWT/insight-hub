<script setup lang="ts">
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <el-container style="height: 100vh">
    <el-aside width="320px" style="border-right: 1px solid var(--el-border-color)">
      <Sidebar />
    </el-aside>
    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}
</style>
