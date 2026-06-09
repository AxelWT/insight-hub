<!-- 根组件 - 定义应用的整体布局结构 -->
<script setup lang="ts">
import Sidebar from './components/Sidebar.vue'
</script>

<template>
  <!-- VitePress 风格布局：左侧边栏 + 右侧主内容区 -->
  <div class="vp-layout">
    <aside class="vp-sidebar">
      <Sidebar />
    </aside>
    <main class="vp-main">
      <div class="vp-main-content">
        <!-- 路由视图：根据当前 URL 渲染对应的页面组件 -->
        <router-view />
      </div>
    </main>
  </div>
</template>
