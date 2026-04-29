# lj_claw Agent Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个独立的 lj_claw Agent，具有管理页面（模型配置、Skills 管理）和对话功能

**Architecture:** FastAPI 后端 + Vue3 前端分离架构，JSON 文件存储配置和对话历史，Nginx 反向代理

**Tech Stack:** FastAPI, Vue 3, Vite, Vue Router, Pinia, Nginx, Docker

---

## 文件结构

```
lj_claw/
├── backend/
│   ├── main.py                    # FastAPI 入口，路由汇总
│   ├── config.py                  # JSON 数据读写封装
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── models.py              # /api/models 路由
│   │   ├── skills.py              # /api/skills 路由
│   │   └── chat.py                # /api/chat 路由
│   ├── services/
│   │   ├── __init__.py
│   │   └── agent.py               # Agent 执行逻辑，调用模型 API
│   └── data/
│       ├── models.json            # 模型配置
│       ├── skills.json            # Skills 配置
│       └── chat_history.json      # 对话历史
│
├── frontend/
│   ├── index.html
│   ├── vite.config.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── main.ts
│   │   ├── App.vue
│   │   ├── router/
│   │   │   └── index.ts
│   │   ├── stores/
│   │   │   ├── models.ts          # Pinia store for models
│   │   │   ├── skills.ts          # Pinia store for skills
│   │   │   └── chat.ts            # Pinia store for chat
│   │   ├── views/
│   │   │   ├── SettingsView.vue   # /settings 页面
│   │   │   └── ChatView.vue       # /chat 页面
│   │   ├── components/
│   │   │   ├── ModelCard.vue      # 模型卡片
│   │   │   ├── ModelForm.vue      # 添加/编辑模型表单
│   │   │   ├── SkillToggle.vue    # Skill 开关
│   │   │   └── ChatMessage.vue    # 消息气泡
│   │   └── api/
│   │       └── index.ts           # API 客户端
│   └── public/
│
├── nginx/
│   └── lj_claw.conf
│
├── docker-compose.yml
└── README.md
```

---

## Task 1: 初始化项目结构

**Files:**
- Create: `backend/data/models.json`
- Create: `backend/data/skills.json`
- Create: `backend/data/chat_history.json`

- [ ] **Step 1: 创建目录结构**

```bash
mkdir -p backend/routers backend/services backend/data
mkdir -p frontend/src/router frontend/src/stores frontend/src/views
mkdir -p frontend/src/components frontend/src/api frontend/public
mkdir -p nginx
```

- [ ] **Step 2: 创建初始数据文件**

`backend/data/models.json`:
```json
{
  "models": [],
  "active_model": null
}
```

`backend/data/skills.json`:
```json
{
  "skills": []
}
```

`backend/data/chat_history.json`:
```json
{
  "history": []
}
```

- [ ] **Step 3: Commit**

```bash
git init
git add .
git commit -m "chore: initialize project structure"
```

---

## Task 2: FastAPI 后端基础

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/main.py`
- Create: `backend/config.py`
- Create: `backend/routers/__init__.py`
- Create: `backend/routers/models.py`
- Create: `backend/routers/skills.py`
- Create: `backend/routers/chat.py`
- Create: `backend/services/__init__.py`
- Create: `backend/services/agent.py`

- [ ] **Step 1: 创建 requirements.txt**

```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
httpx==0.26.0
sse-starlette==2.0.0
```

- [ ] **Step 2: 创建 config.py**

```python
import json
from pathlib import Path
from typing import Any

DATA_DIR = Path(__file__).parent / "data"

def load_json(filename: str) -> dict:
    path = DATA_DIR / filename
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(filename: str, data: dict) -> None:
    path = DATA_DIR / filename
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
```

- [ ] **Step 3: 创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import models, skills, chat

app = FastAPI(title="lj_claw Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(models.router, prefix="/api/models", tags=["models"])
app.include_router(skills.router, prefix="/api/skills", tags=["skills"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

@app.get("/api/health")
def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 创建 models 路由 (routers/models.py)**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import load_json, save_json

router = APIRouter()

class ModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    api_key: str
    api_base: str
    enabled: bool = True

class SetActiveRequest(BaseModel):
    model_id: str

@router.get("/")
def list_models():
    data = load_json("models.json")
    return data

@router.post("/")
def add_model(model: ModelConfig):
    data = load_json("models.json")
    if any(m["id"] == model.id for m in data.get("models", [])):
        raise HTTPException(status_code=400, detail="Model already exists")
    data.setdefault("models", []).append(model.model_dump())
    if data.get("active_model") is None:
        data["active_model"] = model.id
    save_json("models.json", data)
    return {"success": True}

@router.put("/{model_id}")
def update_model(model_id: str, model: ModelConfig):
    data = load_json("models.json")
    for i, m in enumerate(data.get("models", [])):
        if m["id"] == model_id:
            data["models"][i] = model.model_dump()
            save_json("models.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Model not found")

@router.delete("/{model_id}")
def delete_model(model_id: str):
    data = load_json("models.json")
    data["models"] = [m for m in data.get("models", []) if m["id"] != model_id]
    if data.get("active_model") == model_id:
        data["active_model"] = data["models"][0]["id"] if data["models"] else None
    save_json("models.json", data)
    return {"success": True}

@router.put("/{model_id}/active")
def set_active_model(model_id: str):
    data = load_json("models.json")
    if not any(m["id"] == model_id for m in data.get("models", [])):
        raise HTTPException(status_code=404, detail="Model not found")
    data["active_model"] = model_id
    save_json("models.json", data)
    return {"success": True}
```

- [ ] **Step 5: 创建 skills 路由 (routers/skills.py)**

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from config import load_json, save_json

router = APIRouter()

class SkillConfig(BaseModel):
    id: str
    name: str
    enabled: bool = True
    config: dict = {}

@router.get("/")
def list_skills():
    data = load_json("skills.json")
    return data

@router.put("/{skill_id}")
def update_skill(skill_id: str, skill: SkillConfig):
    data = load_json("skills.json")
    for i, s in enumerate(data.get("skills", [])):
        if s["id"] == skill_id:
            data["skills"][i] = skill.model_dump()
            save_json("skills.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Skill not found")

@router.put("/{skill_id}/enabled")
def toggle_skill(skill_id: str, enabled: bool):
    data = load_json("skills.json")
    for i, s in enumerate(data.get("skills", [])):
        if s["id"] == skill_id:
            data["skills"][i]["enabled"] = enabled
            save_json("skills.json", data)
            return {"success": True}
    raise HTTPException(status_code=404, detail="Skill not found")
```

- [ ] **Step 6: 创建 chat 路由 (routers/chat.py)**

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from config import load_json, save_json
from services.agent import AgentService
import json

router = APIRouter()
agent_service = AgentService()

class ChatRequest(BaseModel):
    message: str
    model_id: str | None = None

@router.get("/history")
def get_history():
    data = load_json("chat_history.json")
    return data

@router.delete("/history")
def clear_history():
    save_json("chat_history.json", {"history": []})
    return {"success": True}

@router.post("/")
async def chat(request: ChatRequest):
    data = load_json("models.json")
    model_id = request.model_id or data.get("active_model")
    if not model_id:
        raise HTTPException(status_code=400, detail="No active model configured")

    model_config = next((m for m in data.get("models", []) if m["id"] == model_id), None)
    if not model_config:
        raise HTTPException(status_code=404, detail="Model not found")

    skills_data = load_json("skills.json")
    enabled_skills = [s for s in skills_data.get("skills", []) if s.get("enabled")]

    chat_data = load_json("chat_history.json")
    history = chat_data.get("history", [])
    history.append({"role": "user", "content": request.message})
    save_json("chat_history.json", {"history": history})

    async def generate():
        full_response = ""
        async for chunk in agent_service.stream_chat(
            message=request.message,
            model_config=model_config,
            skills=enabled_skills,
            history=history[:-1]
        ):
            if chunk.get("type") == "text":
                full_response += chunk.get("content", "")
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        history.append({"role": "assistant", "content": full_response})
        save_json("chat_history.json", {"history": history})

    return StreamingResponse(generate(), media_type="text/event-stream")
```

- [ ] **Step 7: 创建 agent service (services/agent.py)**

```python
import httpx
from typing import AsyncGenerator, List, Dict, Any

class AgentService:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=60.0)

    async def stream_chat(
        self,
        message: str,
        model_config: Dict[str, Any],
        skills: List[Dict[str, Any]],
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        provider = model_config.get("provider", "openai")
        api_base = model_config.get("api_base")
        api_key = model_config.get("api_key")

        if provider == "openai":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._openai_chat(message, api_base, api_key, history):
                yield chunk
        elif provider == "anthropic":
            yield {"type": "thinking", "content": "正在思考..."}
            async for chunk in self._anthropic_chat(message, api_base, api_key, history):
                yield chunk
        else:
            yield {"type": "error", "content": f"Unsupported provider: {provider}"}

        yield {"type": "done"}

    async def _openai_chat(
        self,
        message: str,
        api_base: str,
        api_key: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{api_base.rstrip('/')}/chat/completions/accept"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "gpt-4",
            "messages": history + [{"role": "user", "content": message}],
            "stream": True
        }

        async with self.client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield {"type": "text", "content": content}
                    except json.JSONDecodeError:
                        pass

    async def _anthropic_chat(
        self,
        message: str,
        api_base: str,
        api_key: str,
        history: List[Dict[str, str]]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        url = f"{api_base.rstrip('/')}/v1/messages"
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": history + [{"role": "user", "content": message}],
            "max_tokens": 1024,
            "stream": True
        }

        async with self.client.stream("POST", url, headers=headers, json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json
                    try:
                        chunk = json.loads(data)
                        content = chunk.get("delta", {}).get("text", "")
                        if content:
                            yield {"type": "text", "content": content}
                    except json.JSONDecodeError:
                        pass

    async def close(self):
        await self.client.aclose()
```

- [ ] **Step 8: 测试后端**

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# 在另一个终端测试
curl http://localhost:8000/api/health
curl http://localhost:8000/api/models
```

- [ ] **Step 9: Commit**

```bash
git add backend/
git commit -m "feat: FastAPI backend with models, skills, chat APIs"
```

---

## Task 3: Vue3 前端基础

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tsconfig.json`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "lj-claw-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vue-tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "vue": "^3.4.0",
    "vue-router": "^4.2.5",
    "pinia": "^2.1.7",
    "axios": "^1.6.5"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^5.0.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "vue-tsc": "^1.8.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { resolve } from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  }
})
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "module": "ESNext",
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "preserve",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src/**/*.ts", "src/**/*.tsx", "src/**/*.vue"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>lj_claw Agent</title>
  </head>
  <body>
    <div id="app"></div>
    <script type="module" src="/src/main.ts"></script>
  </body>
</html>
```

- [ ] **Step 5: 创建 main.ts**

```typescript
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
```

- [ ] **Step 6: 创建 App.vue**

```vue
<template>
  <div id="app">
    <router-view />
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
}
</style>
```

- [ ] **Step 7: 创建 router/index.ts**

```typescript
import { createRouter, createWebHistory } from 'vue-router'
import SettingsView from '@/views/SettingsView.vue'
import ChatView from '@/views/ChatView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/settings' },
    { path: '/settings', component: SettingsView },
    { path: '/chat', component: ChatView }
  ]
})

export default router
```

- [ ] **Step 8: 创建基础 view 文件**

`frontend/src/views/SettingsView.vue`:
```vue
<template>
  <div class="settings">
    <h1>Settings (开发中)</h1>
  </div>
</template>

<script setup lang="ts">
</script>
```

`frontend/src/views/ChatView.vue`:
```vue
<template>
  <div class="chat">
    <h1>Chat (开发中)</h1>
  </div>
</template>

<script setup lang="ts">
</script>
```

- [ ] **Step 9: 安装依赖并测试**

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

- [ ] **Step 10: Commit**

```bash
git add frontend/
git commit -m "feat: Vue3 frontend scaffold with router"
```

---

## Task 4: Settings 页面 - 模型管理

**Files:**
- Create: `frontend/src/api/index.ts`
- Modify: `frontend/src/views/SettingsView.vue`
- Create: `frontend/src/components/ModelCard.vue`
- Create: `frontend/src/components/ModelForm.vue`
- Create: `frontend/src/stores/models.ts`

- [ ] **Step 1: 创建 API 客户端 (api/index.ts)**

```typescript
import axios from 'axios'

const api = axios.create({
  baseURL: '/api'
})

export const modelsApi = {
  list: () => api.get('/models'),
  create: (data: any) => api.post('/models', data),
  update: (id: string, data: any) => api.put(`/models/${id}`, data),
  delete: (id: string) => api.delete(`/models/${id}`),
  setActive: (id: string) => api.put(`/models/${id}/active`)
}

export const skillsApi = {
  list: () => api.get('/skills'),
  update: (id: string, data: any) => api.put(`/skills/${id}`, data),
  toggle: (id: string, enabled: boolean) => api.put(`/skills/${id}/enabled?enabled=${enabled}`)
}

export const chatApi = {
  send: (message: string, modelId?: string) => {
    return api.post('/chat', { message, model_id: modelId }, {
      responseType: 'stream'
    })
  },
  history: () => api.get('/chat/history'),
  clearHistory: () => api.delete('/chat/history')
}

export default api
```

- [ ] **Step 2: 创建 models store (stores/models.ts)**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { modelsApi } from '@/api'

export interface ModelConfig {
  id: string
  name: string
  provider: string
  api_key: string
  api_base: string
  enabled: boolean
}

export const useModelsStore = defineStore('models', () => {
  const models = ref<ModelConfig[]>([])
  const activeModel = ref<string | null>(null)
  const loading = ref(false)

  async function fetchModels() {
    loading.value = true
    try {
      const res = await modelsApi.list()
      models.value = res.data.models || []
      activeModel.value = res.data.active_model
    } finally {
      loading.value = false
    }
  }

  async function addModel(model: Omit<ModelConfig, 'enabled'>) {
    const res = await modelsApi.create({ ...model, enabled: true })
    await fetchModels()
    return res
  }

  async function updateModel(id: string, model: ModelConfig) {
    await modelsApi.update(id, model)
    await fetchModels()
  }

  async function deleteModel(id: string) {
    await modelsApi.delete(id)
    await fetchModels()
  }

  async function setActive(id: string) {
    await modelsApi.setActive(id)
    activeModel.value = id
  }

  return { models, activeModel, loading, fetchModels, addModel, updateModel, deleteModel, setActive }
})
```

- [ ] **Step 3: 创建 ModelCard 组件 (components/ModelCard.vue)**

```vue
<template>
  <div class="model-card" :class="{ active: isActive }">
    <div class="model-header">
      <h3>{{ model.name }}</h3>
      <span class="provider">{{ model.provider }}</span>
    </div>
    <div class="model-body">
      <p><strong>API Base:</strong> {{ model.api_base }}</p>
      <p><strong>API Key:</strong> {{ maskedKey }}</p>
    </div>
    <div class="model-actions">
      <button @click="$emit('edit', model)">编辑</button>
      <button @click="$emit('delete', model.id)">删除</button>
      <button v-if="!isActive" @click="$emit('activate', model.id)">激活</button>
      <span v-else class="active-badge">使用中</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { ModelConfig } from '@/stores/models'

const props = defineProps<{
  model: ModelConfig
  isActive: boolean
}>()

defineEmits<{
  edit: [model: ModelConfig]
  delete: [id: string]
  activate: [id: string]
}>()

const maskedKey = computed(() => {
  const key = props.model.api_key
  if (key.length <= 8) return '***'
  return key.slice(0, 4) + '...' + key.slice(-4)
})
</script>

<style scoped>
.model-card {
  background: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
.model-card.active {
  border: 2px solid #4CAF50;
}
.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.provider {
  background: #e0e0e0;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.model-body p {
  margin: 4px 0;
  font-size: 14px;
  color: #666;
}
.model-actions {
  margin-top: 12px;
  display: flex;
  gap: 8px;
}
button {
  padding: 6px 12px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
button:first-child {
  background: #2196F3;
  color: white;
}
button:nth-child(2) {
  background: #f44336;
  color: white;
}
.active-badge {
  background: #4CAF50;
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
}
</style>
```

- [ ] **Step 4: 创建 ModelForm 组件 (components/ModelForm.vue)**

```vue
<template>
  <div class="model-form-overlay" @click.self="$emit('close')">
    <div class="model-form">
      <h2>{{ editingModel ? '编辑模型' : '添加模型' }}</h2>
      <form @submit.prevent="handleSubmit">
        <div class="form-group">
          <label>模型 ID</label>
          <input v-model="form.id" placeholder="如: gpt-4" required :disabled="!!editingModel" />
        </div>
        <div class="form-group">
          <label>名称</label>
          <input v-model="form.name" placeholder="如: GPT-4" required />
        </div>
        <div class="form-group">
          <label>Provider</label>
          <select v-model="form.provider" required>
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic</option>
          </select>
        </div>
        <div class="form-group">
          <label>API Base URL</label>
          <input v-model="form.api_base" placeholder="https://api.openai.com/v1" required />
        </div>
        <div class="form-group">
          <label>API Key</label>
          <input v-model="form.api_key" type="password" placeholder="sk-..." required />
        </div>
        <div class="form-actions">
          <button type="button" @click="$emit('close')">取消</button>
          <button type="submit">{{ editingModel ? '保存' : '添加' }}</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import type { ModelConfig } from '@/stores/models'

const props = defineProps<{
  editingModel?: ModelConfig
}>()

const emit = defineEmits<{
  close: []
  submit: [data: Partial<ModelConfig>]
}>()

const form = reactive({
  id: props.editingModel?.id || '',
  name: props.editingModel?.name || '',
  provider: props.editingModel?.provider || 'openai',
  api_base: props.editingModel?.api_base || '',
  api_key: props.editingModel?.api_key || ''
})

function handleSubmit() {
  emit('submit', { ...form })
}
</script>

<style scoped>
.model-form-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
}
.model-form {
  background: white;
  padding: 24px;
  border-radius: 8px;
  width: 400px;
}
h2 { margin-bottom: 16px; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; margin-bottom: 4px; font-weight: 500; }
.form-group input, .form-group select {
  width: 100%;
  padding: 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
}
.form-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
  margin-top: 16px;
}
.form-actions button {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
.form-actions button[type="submit"] {
  background: #4CAF50;
  color: white;
}
</style>
```

- [ ] **Step 5: 更新 SettingsView (views/SettingsView.vue)**

```vue
<template>
  <div class="settings-view">
    <nav class="nav">
      <router-link to="/settings" class="nav-link active">Settings</router-link>
      <router-link to="/chat" class="nav-link">Chat</router-link>
    </nav>

    <main class="content">
      <section class="models-section">
        <h2>模型配置</h2>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="modelsStore.models.length === 0" class="empty">
          <p>暂无模型配置</p>
        </div>
        <div v-else class="models-grid">
          <ModelCard
            v-for="model in modelsStore.models"
            :key="model.id"
            :model="model"
            :is-active="model.id === modelsStore.activeModel"
            @edit="openEditForm"
            @delete="handleDelete"
            @activate="handleActivate"
          />
        </div>
        <button class="add-btn" @click="showAddForm = true">+ 添加模型</button>
      </section>

      <section class="skills-section">
        <h2>Skills 管理</h2>
        <div v-if="skillsLoading" class="loading">加载中...</div>
        <div v-else class="skills-list">
          <SkillToggle
            v-for="skill in skillsStore.skills"
            :key="skill.id"
            :skill="skill"
            @toggle="handleSkillToggle"
          />
        </div>
      </section>
    </main>

    <ModelForm
      v-if="showAddForm || editingModel"
      :editing-model="editingModel"
      @close="closeForm"
      @submit="handleFormSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useSkillsStore } from '@/stores/skills'
import ModelCard from '@/components/ModelCard.vue'
import ModelForm from '@/components/ModelForm.vue'
import SkillToggle from '@/components/SkillToggle.vue'
import type { ModelConfig } from '@/stores/models'

const modelsStore = useModelsStore()
const skillsStore = useSkillsStore()
const loading = ref(false)
const skillsLoading = ref(false)
const showAddForm = ref(false)
const editingModel = ref<ModelConfig | undefined>()

onMounted(async () => {
  loading.value = true
  skillsLoading.value = true
  try {
    await Promise.all([modelsStore.fetchModels(), skillsStore.fetchSkills()])
  } finally {
    loading.value = false
    skillsLoading.value = false
  }
})

function openEditForm(model: ModelConfig) {
  editingModel.value = model
}

function closeForm() {
  showAddForm.value = false
  editingModel.value = undefined
}

async function handleFormSubmit(data: Partial<ModelConfig>) {
  if (editingModel.value) {
    await modelsStore.updateModel(editingModel.value.id, data as ModelConfig)
  } else {
    await modelsStore.addModel(data as any)
  }
  closeForm()
}

async function handleDelete(id: string) {
  if (confirm('确定删除?')) {
    await modelsStore.deleteModel(id)
  }
}

async function handleActivate(id: string) {
  await modelsStore.setActive(id)
}

async function handleSkillToggle(id: string, enabled: boolean) {
  await skillsStore.toggleSkill(id, enabled)
}
</script>

<style scoped>
.settings-view { min-height: 100vh; }
.nav {
  background: white;
  padding: 0 24px;
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #e0e0e0;
}
.nav-link {
  padding: 16px 0;
  color: #666;
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
.nav-link.active { color: #2196F3; border-bottom-color: #2196F3; }
.content { padding: 24px; max-width: 800px; margin: 0 auto; }
section { margin-bottom: 32px; }
h2 { margin-bottom: 16px; }
.models-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 16px; }
.empty, .loading { color: #999; text-align: center; padding: 32px; }
.add-btn {
  margin-top: 16px;
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}
</style>
```

- [ ] **Step 6: 创建 skills store (stores/skills.ts)**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { skillsApi } from '@/api'

export interface Skill {
  id: string
  name: string
  enabled: boolean
  config: Record<string, any>
}

export const useSkillsStore = defineStore('skills', () => {
  const skills = ref<Skill[]>([])
  const loading = ref(false)

  async function fetchSkills() {
    loading.value = true
    try {
      const res = await skillsApi.list()
      skills.value = res.data.skills || []
    } finally {
      loading.value = false
    }
  }

  async function toggleSkill(id: string, enabled: boolean) {
    await skillsApi.toggle(id, enabled)
    const skill = skills.value.find(s => s.id === id)
    if (skill) skill.enabled = enabled
  }

  return { skills, loading, fetchSkills, toggleSkill }
})
```

- [ ] **Step 7: 创建 SkillToggle 组件 (components/SkillToggle.vue)**

```vue
<template>
  <div class="skill-toggle">
    <span class="skill-name">{{ skill.name }}</span>
    <label class="switch">
      <input type="checkbox" :checked="skill.enabled" @change="handleToggle" />
      <span class="slider"></span>
    </label>
  </div>
</template>

<script setup lang="ts">
import type { Skill } from '@/stores/skills'

const props = defineProps<{ skill: Skill }>()
const emit = defineEmits<{ toggle: [id: string, enabled: boolean] }>()

function handleToggle(e: Event) {
  const target = e.target as HTMLInputElement
  emit('toggle', props.skill.id, target.checked)
}
</script>

<style scoped>
.skill-toggle {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
}
.skill-name { font-weight: 500; }
.switch {
  position: relative;
  width: 48px;
  height: 24px;
}
.switch input { opacity: 0; width: 0; height: 0; }
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: #ccc;
  border-radius: 24px;
  transition: 0.3s;
}
.slider::before {
  content: "";
  position: absolute;
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: 0.3s;
}
input:checked + .slider { background: #4CAF50; }
input:checked + .slider::before { transform: translateX(24px); }
</style>
```

- [ ] **Step 8: 测试 Settings 页面**

```bash
npm run dev
# 访问 http://localhost:3000/settings
# 测试添加/编辑/删除模型
```

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: Settings page with model management"
```

---

## Task 5: Chat 页面

**Files:**
- Modify: `frontend/src/views/ChatView.vue`
- Create: `frontend/src/components/ChatMessage.vue`
- Modify: `frontend/src/stores/chat.ts`

- [ ] **Step 1: 创建 chat store (stores/chat.ts)**

```typescript
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { chatApi } from '@/api'

export interface Message {
  role: 'user' | 'assistant'
  content: string
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchHistory() {
    const res = await chatApi.history()
    messages.value = res.data.history || []
  }

  async function sendMessage(content: string, modelId?: string) {
    loading.value = true
    error.value = null

    messages.value.push({ role: 'user', content })

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: content, model_id: modelId })
      })

      const reader = response.body?.getReader()
      if (!reader) throw new Error('No response body')

      const decoder = new TextDecoder()
      let assistantMessage = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value)
        const lines = chunk.split('\n')

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              if (data.type === 'text') {
                assistantMessage += data.content
                messages.value = [...messages.value.filter(m => m.role !== 'assistant' || m.content !== ''), { role: 'assistant', content: assistantMessage }]
              } else if (data.type === 'error') {
                error.value = data.content
              }
            } catch {}
          }
        }
      }

      if (assistantMessage && !messages.value.find(m => m.role === 'assistant' && m.content === assistantMessage)) {
        messages.value.push({ role: 'assistant', content: assistantMessage })
      }
    } catch (e: any) {
      error.value = e.message || '发送失败'
    } finally {
      loading.value = false
    }
  }

  async function clearHistory() {
    await chatApi.clearHistory()
    messages.value = []
  }

  return { messages, loading, error, fetchHistory, sendMessage, clearHistory }
})
```

- [ ] **Step 2: 创建 ChatMessage 组件 (components/ChatMessage.vue)**

```vue
<template>
  <div class="chat-message" :class="message.role">
    <div class="message-content">{{ message.content }}</div>
  </div>
</template>

<script setup lang="ts">
import type { Message } from '@/stores/chat'

defineProps<{ message: Message }>()
</script>

<style scoped>
.chat-message {
  display: flex;
  margin-bottom: 16px;
}
.chat-message.user { justify-content: flex-end; }
.chat-message.assistant { justify-content: flex-start; }
.message-content {
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
}
.user .message-content {
  background: #2196F3;
  color: white;
  border-bottom-right-radius: 4px;
}
.assistant .message-content {
  background: white;
  color: #333;
  border-bottom-left-radius: 4px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}
</style>
```

- [ ] **Step 3: 更新 ChatView (views/ChatView.vue)**

```vue
<template>
  <div class="chat-view">
    <nav class="nav">
      <router-link to="/settings" class="nav-link">Settings</router-link>
      <router-link to="/chat" class="nav-link active">Chat</router-link>
    </nav>

    <main class="chat-main">
      <div class="messages" ref="messagesEl">
        <div v-if="chatStore.messages.length === 0" class="welcome">
          <h2>欢迎使用 lj_claw Agent</h2>
          <p>开始对话吧</p>
        </div>
        <ChatMessage
          v-for="(msg, i) in chatStore.messages"
          :key="i"
          :message="msg"
        />
        <div v-if="chatStore.loading" class="loading-indicator">
          <span>思考中...</span>
        </div>
        <div v-if="chatStore.error" class="error-msg">
          {{ chatStore.error }}
        </div>
      </div>

      <div class="input-area">
        <input
          v-model="inputMessage"
          placeholder="输入消息..."
          :disabled="chatStore.loading"
          @keydown.enter="handleSend"
        />
        <button @click="handleSend" :disabled="chatStore.loading || !inputMessage.trim()">
          发送
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useChatStore } from '@/stores/chat'
import ChatMessage from '@/components/ChatMessage.vue'

const chatStore = useChatStore()
const inputMessage = ref('')
const messagesEl = ref<HTMLElement>()

onMounted(() => {
  chatStore.fetchHistory()
})

async function handleSend() {
  const msg = inputMessage.value.trim()
  if (!msg || chatStore.loading) return

  inputMessage.value = ''
  await chatStore.sendMessage(msg)

  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}
</script>

<style scoped>
.chat-view { display: flex; flex-direction: column; height: 100vh; }
.nav {
  background: white;
  padding: 0 24px;
  display: flex;
  gap: 24px;
  border-bottom: 1px solid #e0e0e0;
}
.nav-link {
  padding: 16px 0;
  color: #666;
  text-decoration: none;
  border-bottom: 2px solid transparent;
}
.nav-link.active { color: #2196F3; border-bottom-color: #2196F3; }
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  max-width: 800px;
  width: 100%;
  margin: 0 auto;
  padding: 24px;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding-bottom: 16px;
}
.welcome {
  text-align: center;
  color: #999;
  margin-top: 100px;
}
.welcome h2 { margin-bottom: 8px; }
.loading-indicator {
  text-align: center;
  color: #999;
  padding: 8px;
}
.error-msg {
  background: #ffebee;
  color: #c62828;
  padding: 8px 16px;
  border-radius: 4px;
  margin: 8px 0;
}
.input-area {
  display: flex;
  gap: 8px;
  padding-top: 16px;
  border-top: 1px solid #e0e0e0;
}
.input-area input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #ddd;
  border-radius: 24px;
  outline: none;
}
.input-area input:focus { border-color: #2196F3; }
.input-area button {
  padding: 12px 24px;
  background: #2196F3;
  color: white;
  border: none;
  border-radius: 24px;
  cursor: pointer;
}
.input-area button:disabled { background: #ccc; cursor: not-allowed; }
</style>
```

- [ ] **Step 4: 测试 Chat 页面**

```bash
# 确保后端运行中: uvicorn main:app --reload --port 8000
# 前端: npm run dev
# 访问 http://localhost:3000/chat
# 测试发送消息
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/
git commit -m "feat: Chat page with streaming support"
```

---

## Task 6: 部署配置

**Files:**
- Create: `docker-compose.yml`
- Create: `nginx/lj_claw.conf`
- Create: `README.md`

- [ ] **Step 1: 创建 docker-compose.yml**

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
    environment:
      - PYTHONPATH=/app

  frontend:
    build: ./frontend
    ports:
      - "3000:80"

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx/lj_claw.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - backend
      - frontend
```

- [ ] **Step 2: 创建 backend Dockerfile**

`backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: 创建 frontend Dockerfile**

`frontend/Dockerfile`:
```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

`frontend/nginx.conf`:
```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
    }
}
```

- [ ] **Step 4: 创建 nginx 配置 (nginx/lj_claw.conf)**

```nginx
upstream backend {
    server backend:8000;
}

upstream frontend {
    server frontend:80;
}

server {
    listen 80;
    server_name localhost;

    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

- [ ] **Step 5: 创建 README.md**

```markdown
# lj_claw Agent

独立的 Agent 服务，支持模型配置、Skills 管理和对话功能。

## 快速开始

### 开发模式

后端:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

前端:
```bash
cd frontend
npm install
npm run dev
```

访问 http://localhost:3000

### 生产部署

```bash
docker-compose up -d
```

访问 http://localhost

## 功能

- 模型配置管理 (OpenAI/Anthropic)
- Skills 启用/禁用
- 流式对话
```

- [ ] **Step 6: 测试 Docker 构建**

```bash
docker-compose build
docker-compose up -d
# 测试访问
```

- [ ] **Step 7: Commit**

```bash
git add docker-compose.yml nginx/ backend/Dockerfile frontend/Dockerfile frontend/nginx.conf README.md
git commit -m "feat: Add Docker deployment configuration"
```

---

## 自检清单

- [ ] Spec 所有部分都有对应 task
- [ ] 无占位符 (TBD/TODO)
- [ ] 类型/方法名一致性检查
- [ ] 每个 task 都有测试步骤
