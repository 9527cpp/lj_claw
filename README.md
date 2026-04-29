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
