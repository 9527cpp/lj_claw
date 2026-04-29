# lj_claw Agent 设计文档

**日期**: 2026-04-29
**状态**: 已批准

---

## 1. 概述

### 项目目标
构建一个独立的 lj_claw Agent，具有管理页面和对话功能，支持模型配置管理和 Skills 精细控制。

### 技术栈
- **前端**: Vue 3 + Vite
- **后端**: FastAPI (Python)
- **存储**: JSON 文件
- **部署**: Nginx 反向代理，生产级

---

## 2. 架构

```
用户浏览器 → Nginx → FastAPI (API)
                    ↓
              JSON 配置文件
```

**组件职责：**
- **Vue3 前端**：管理页面（模型配置、skills 开关）+ 对话界面
- **FastAPI 后端**：API 服务，处理配置读写、聊天请求、skill 列表
- **JSON 存储**：模型配置、skills 启用状态、对话历史
- **Nginx**：生产环境反向代理 + 静态文件服务

---

## 3. API 设计

```
/api
├── GET    /models              # 获取所有模型配置
├── POST   /models              # 添加模型
├── PUT    /models/{id}         # 更新模型
├── DELETE /models/{id}        # 删除模型
├── PUT    /models/{id}/active  # 激活指定模型
│
├── GET    /skills              # 获取所有 skills（含启用状态）
├── PUT    /skills/{id}         # 更新单个 skill 配置
├── PUT    /skills/{id}/enabled # 启用/禁用单个 skill
│
├── POST   /chat                # 发送消息，返回流式响应
├── GET    /chat/history        # 获取对话历史
└── DELETE /chat/history        # 清空对话历史
```

### 请求/响应示例

**POST /api/chat**
```json
// Request
{ "message": "帮我写一个快速排序", "model_id": "gpt-4" }

// Response (SSE stream)
data: {"type":"thinking","content":"正在思考..."}
data: {"type":"text","content":"好的，我来帮你写..."}
data: {"type":"done"}
```

**GET /api/skills**
```json
{
  "skills": [
    { "id": "code-review", "name": "Code Review", "enabled": true, "config": {} },
    { "id": "tdd-guide",   "name": "TDD Guide",   "enabled": false, "config": {} }
  ]
}
```

### 错误响应格式
```json
{
  "error": {
    "code": "MODEL_NOT_FOUND",
    "message": "指定的模型不存在"
  }
}
```

---

## 4. 数据模型

### models.json
```json
{
  "models": [
    {
      "id": "gpt-4",
      "name": "GPT-4",
      "provider": "openai",
      "api_key": "sk-xxx",
      "api_base": "https://api.openai.com/v1",
      "enabled": true
    }
  ],
  "active_model": "gpt-4"
}
```

### skills.json
```json
{
  "skills": [
    { "id": "code-review",  "name": "Code Review",  "enabled": true,  "config": {} },
    { "id": "tdd-guide",    "name": "TDD Guide",    "enabled": false, "config": {} }
  ]
}
```

### chat_history.json
```json
{
  "history": [
    { "role": "user",    "content": "帮我写一个快排" },
    { "role": "assistant","content": "好的..." }
  ]
}
```

---

## 5. 前端页面结构

### 路由
- `/` → 重定向到 `/settings`
- `/settings` → 模型配置 + Skills 管理
- `/chat` → 对话界面

### /settings 布局
- 顶部导航 (Settings / Chat)
- 模型配置区域（卡片列表 + 添加按钮）
- Skills 管理区域（开关列表）

### /chat 布局
- 顶部导航
- 对话消息区域（流式输出）
- 底部输入框 + 发送按钮

---

## 6. 错误处理

| 场景 | 处理方式 |
|------|---------|
| 未配置 API Key | 弹窗提示，引导去 settings 配置 |
| API 调用失败 | 流式返回错误信息，保留对话上下文 |
| 模型配置不完整 | 前端表单验证，阻止提交 |
| Skills 全部禁用 | 对话仍可用，只是没有 skill 加持 |
| 网络断开 | 显示重连按钮，自动保存输入 |

### 空状态
- 无模型配置 → 显示引导添加模型的提示
- 对话历史为空 → 显示欢迎语和示例问题

---

## 7. 项目结构

```
lj_claw/
├── backend/
│   ├── main.py              # FastAPI 入口
│   ├── routers/
│   │   ├── models.py        # 模型配置 API
│   │   ├── skills.py        # Skills API
│   │   └── chat.py          # 对话 API
│   ├── services/
│   │   └── agent.py         # Agent 执行逻辑
│   └── data/
│       ├── models.json
│       ├── skills.json
│       └── chat_history.json
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── Settings.vue
│   │   │   └── Chat.vue
│   │   ├── components/
│   │   │   ├── ModelCard.vue
│   │   │   ├── SkillToggle.vue
│   │   │   └── ChatMessage.vue
│   │   └── router/
│   ├── vite.config.ts
│   └── index.html
│
├── nginx/
│   └── lj_claw.conf
│
├── docker-compose.yml
└── README.md
```

---

## 8. 下一步

进入 implementation planning 阶段 → writing-plans skill
