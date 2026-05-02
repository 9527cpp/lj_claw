import { createRouter, createWebHistory } from 'vue-router'
import SettingsView from '@/views/SettingsView.vue'
import ChatView from '@/views/ChatView.vue'
import WidgetChatView from '@/views/WidgetChatView.vue'
import WidgetSettingsView from '@/views/WidgetSettingsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/settings' },
    { path: '/settings', component: SettingsView },
    { path: '/chat', component: ChatView },
    { path: '/widget', component: WidgetChatView },
    { path: '/widget-settings', component: WidgetSettingsView }
  ]
})

export default router