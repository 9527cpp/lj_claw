<template>
  <div id="app">
    <aside class="sidebar">
      <nav class="sidebar-nav">
        <router-link to="/settings" class="sidebar-link">Settings</router-link>
        <router-link to="/chat" class="sidebar-link">Chat</router-link>
      </nav>
    </aside>
    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #333;
}

#app {
  min-height: 100vh;
  display: flex;
}

.sidebar {
  width: 200px;
  background: white;
  border-right: 1px solid #e0e0e0;
  position: fixed;
  left: 0;
  top: 0;
  bottom: 0;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  padding: 16px 0;
}

.sidebar-link {
  padding: 16px 24px;
  color: #666;
  text-decoration: none;
  border-left: 3px solid transparent;
}

.sidebar-link.active {
  color: #2196F3;
  border-left-color: #2196F3;
  background: #f5f5f5;
}

.main-content {
  flex: 1;
  margin-left: 200px;
}
</style>