import { defineStore } from 'pinia'
import { ref } from 'vue'
import { widgetApi } from '@/api/widget'

export interface WidgetSite {
  id: string
  site_name: string
  site_url: string
  api_key: string
  primary_color: string
  secondary_color: string
  bot_name: string
  welcome_message: string
  input_placeholder: string
  enabled: boolean
  created_at: string
  updated_at: string
}

export const useWidgetStore = defineStore('widget', () => {
  const sites = ref<WidgetSite[]>([])
  const loading = ref(false)

  async function fetchSites() {
    loading.value = true
    try {
      const res = await widgetApi.listSites()
      sites.value = res.data.sites || []
    } finally {
      loading.value = false
    }
  }

  async function createSite(data: Partial<WidgetSite>) {
    const res = await widgetApi.createSite(data)
    await fetchSites()
    return res.data
  }

  async function updateSite(siteId: string, data: Partial<WidgetSite>) {
    const res = await widgetApi.updateSite(siteId, data)
    await fetchSites()
    return res.data
  }

  async function deleteSite(siteId: string) {
    await widgetApi.deleteSite(siteId)
    await fetchSites()
  }

  async function regenerateKey(siteId: string) {
    const res = await widgetApi.regenerateKey(siteId)
    await fetchSites()
    return res.data
  }

  function getEmbedCode(site: WidgetSite) {
    const domain = site.site_url.replace(/^https?:\/\//, '').replace(/\/$/, '')
    return `<!-- lj_claw 客服浮窗 -->
<script src="https://${domain}/lj-claw-widget.js"></script>
<script>
  LjClawWidget.init({
    apiUrl: 'https://${domain}/api/chat/',
    botName: '${site.bot_name}',
    primaryColor: '${site.primary_color}',
    welcomeMessage: '${site.welcome_message}'
  })
</script>`
  }

  return {
    sites,
    loading,
    fetchSites,
    createSite,
    updateSite,
    deleteSite,
    regenerateKey,
    getEmbedCode
  }
})