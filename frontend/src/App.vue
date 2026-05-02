<template>
  <div id="app">
    <!-- Mobile menu button -->
    <button class="mobile-menu-btn" @click="toggleSidebar" :class="{ active: sidebarOpen }">
      <span></span>
      <span></span>
      <span></span>
    </button>

    <!-- Overlay for mobile -->
    <div class="sidebar-overlay" v-if="sidebarOpen" @click="sidebarOpen = false"></div>

    <aside class="sidebar" :class="{ open: sidebarOpen }">
      <nav class="sidebar-nav">
        <router-link to="/settings" class="sidebar-link" @click="sidebarOpen = false">Settings</router-link>
        <router-link to="/chat" class="sidebar-link" @click="sidebarOpen = false">Chat</router-link>
      </nav>
    </aside>

    <div class="main-content">
      <router-view />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const sidebarOpen = ref(false)

function toggleSidebar() {
  sidebarOpen.value = !sidebarOpen.value
}
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

.main-content {
  flex: 1;
  min-width: 0;
}

/* Desktop sidebar */
@media (min-width: 769px) {
  .sidebar {
    width: 200px;
    background: white;
    border-right: 1px solid #e0e0e0;
    position: fixed;
    left: 0;
    top: 0;
    bottom: 0;
    z-index: 300;
  }

  .main-content {
    margin-left: 200px;
  }

  .mobile-menu-btn {
    display: none;
  }

  .sidebar-overlay {
    display: none;
  }
}

/* Mobile sidebar */
@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    width: 24px;
    height: 18px;
    background: none;
    border: none;
    cursor: pointer;
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 200;
    padding: 0;
  }

  .mobile-menu-btn span {
    display: block;
    width: 100%;
    height: 2px;
    background: #333;
    transition: all 0.3s;
  }

  .mobile-menu-btn.active span:nth-child(1) {
    transform: rotate(45deg) translate(5px, 5px);
  }

  .mobile-menu-btn.active span:nth-child(2) {
    opacity: 0;
  }

  .mobile-menu-btn.active span:nth-child(3) {
    transform: rotate(-45deg) translate(5px, -5px);
  }

  .sidebar-overlay {
    display: block;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.5);
    z-index: 195;
  }

  .sidebar {
    position: fixed;
    left: -200px;
    top: 0;
    bottom: 0;
    width: 200px;
    background: white;
    z-index: 300;
    transition: left 0.3s;
  }

  .sidebar.open {
    left: 0;
  }

  .main-content {
    margin-left: 0;
    padding-top: 50px;
  }
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
  display: block;
}

.sidebar-link.active {
  color: #2196F3;
  border-left-color: #2196F3;
  background: #f5f5f5;
}
</style>