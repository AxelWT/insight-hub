<script setup lang="ts">
import { useThemeProvider } from './composables/theme'
import Sidebar from './components/Sidebar.vue'

const { theme, toggleTheme } = useThemeProvider()
</script>

<template>
  <div class="bg-grid" />
  <div class="bg-glow" />
  <div class="bg-glow" />
  <div class="bg-glow" />
  <button
    class="theme-toggle-float"
    :title="theme === 'dark' ? '切换到亮色' : '切换到暗色'"
    @click="toggleTheme()"
  >
    {{ theme === 'dark' ? '☀' : '☾' }}
  </button>
  <div class="vp-layout">
    <aside class="vp-sidebar">
      <Sidebar />
    </aside>
    <main class="vp-main">
      <div class="vp-main-content">
        <router-view />
      </div>
    </main>
    <footer class="vp-footer">
      insightHub©2026 · AI 调研平台
    </footer>
  </div>
</template>

<style scoped>
.theme-toggle-float {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 100;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border: 1px solid var(--vp-c-divider);
  border-radius: var(--vp-radius-sm);
  background: var(--vp-c-bg-soft);
  color: var(--vp-c-text-2);
  cursor: pointer;
  font-size: 16px;
  transition: all var(--vp-transition);
  padding: 0;
  line-height: 1;
}

.theme-toggle-float:hover {
  color: var(--vp-c-brand);
  border-color: var(--vp-c-brand);
  background: var(--vp-c-brand-bg);
}
</style>
