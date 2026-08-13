# 企业IT服务智能助手（IT Service Intelligent Assistant）

> 一个用于学习和探索AI应用开发的个人项目，展示如何从零构建一个具备对话、RAG知识库问答和Agent工具调用能力的企业级AI助手。

## 📋 项目简介

本项目是一个完整的AI应用开发教学骨架，涵盖了当前AI落地最核心的三大能力：

| 能力 | 说明 | 学习重点 |
|------|------|----------|
| 💬 普通对话 | 直接与LLM交互的基础对话能力 | Prompt工程、对话管理 |
| 📚 知识库问答 | RAG（检索增强生成），基于文档回答问题 | 向量数据库、文档处理、检索策略 |
| 🧠 智能Agent | AI自主调用工具解决复杂问题 | Agent设计模式、工具编排、推理链 |

**技术栈：** FastAPI + LangChain + Chroma + Tailwind CSS（零构建前端）

**设计理念：** 可读性 > 性能 > 功能完备性。代码有充分注释，架构清晰，适合从全局到局部逐步学习。

---

## 🚀 快速开始

### 方式一：Docker Compose（推荐，一键启动）

```bash
# 1. 克隆项目
git clone <repo-url>
cd it-service-assistant

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 API Key

# 3. 启动服务
docker-compose up -d

# 4. 访问
# 前端界面: http://localhost:3000
# API 文档: http://localhost:8000/docs
```

### 方式二：本地开发运行

```bash
# 1. 进入后端目录
cd backend

# 2. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp ../.env.example .env
# 编辑 .env 填入 API Key

# 5. 启动后端
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 6. 打开前端（直接用浏览器打开）
# 双击 frontend/index.html，或用任意静态服务器
cd ../frontend && python -m http.server 3000
```

### 首次启动后的设置

1. 打开管理后台：http://localhost:3000/admin.html
2. 上传示例文档（`sample_docs/` 目录下的3个MD文件）
3. 等待自动向量化完成
4. 返回对话页面，切换到「知识库问答」或「智能Agent」模式开始体验

---

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (静态页面)                   │
│  index.html (对话界面)  │  admin.html (管理后台)              │
│  chat.js  rag.js  admin.js  api.js                          │
└───────────────────────────┬─────────────────────────────────┘
                            │ HTTP / REST API
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Chat API│  │  RAG API │  │ Agent API│  │Document API│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └─────┬──────┘ │
│       │              │              │                │        │
│  ┌────▼──────────────▼──────────────▼────────────────▼─────┐│
│  │                   Service Layer (业务逻辑层)              ││
│  │   LLM Service │ RAG Service │ Agent Service │ Document  ││
│  └────┬──────────────┬──────────────┬──────────────┬───────┘│
│       │              │              │              │        │
│  ┌────▼────┐   ┌─────▼──────┐    ┌──▼──────┐    ┌──▼─────┐ │
│  │ LangChain│   │ Chroma     │    │ Tools   │    │ File   │ │
│  │          │   │ (向量数据库)│    │ (工具集) │    │ System │ │
│  └────┬────┘   └────────────┘    └─────────┘    └────────┘ │
│       │                                                      │
│  ┌────▼───────────────────────────────────────────────────┐ │
│  │              LLM Provider (大模型服务)                   │ │
│  │    火山方舟 / 通义千问 / DeepSeek / OpenAI ...          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块说明

| 模块 | 文件路径 | 职责 | 学习优先级 |
|------|----------|------|-----------|
| 配置管理 | `backend/app/config.py` | 统一管理环境变量和配置 | ⭐⭐⭐ 入门必读 |
| LLM服务 | `backend/app/services/llm_service.py` | 封装大模型调用，支持多提供商 | ⭐⭐⭐ 入门必读 |
| RAG服务 | `backend/app/services/rag_service.py` | 检索增强生成核心逻辑 | ⭐⭐⭐ 核心重点 |
| Agent服务 | `backend/app/services/agent_service.py` | Agent推理与工具调用 | ⭐⭐⭐ 进阶重点 |
| 文档服务 | `backend/app/services/document_service.py` | 文档加载、切分、管理 | ⭐⭐ 辅助理解 |
| API路由层 | `backend/app/api/*.py` | HTTP接口定义 | ⭐⭐ 按需阅读 |
| 数据模型 | `backend/app/models/__init__.py` | 请求/响应数据结构 | ⭐ 浏览即可 |

---

## 📚 推荐学习路径

> 从全局到局部，从会用到理解，逐步深入。

### 第一阶段：跑起来 + 建立体感（1-2天）

1. **按照快速开始指南把项目跑起来**
   - 目标：能在浏览器里看到界面，能对话
   - 重点：不求甚解，先建立整体认知

2. **体验三种模式的差异**
   - 普通对话 vs 知识库问答 vs 智能Agent
   - 思考：同样的问题，三种模式回答有什么不同？为什么？

3. **上传自己的文档试试RAG效果**
   - 找一份你熟悉的文档（PDF/MD/TXT）
   - 上传后提问，观察回答质量和引用来源

### 第二阶段：理解后端核心逻辑（3-7天）

1. **从 main.py 开始，顺着调用链往下读**
   - `main.py` → `api/chat.py` → `services/llm_service.py`
   - 理解一个最简单的请求是如何流转的

2. **深入理解RAG（重点！）**
   - 读 `rag_service.py`，理解检索→增强→生成的三步流程
   - 读 `document_service.py`，理解文档切分原理
   - 动手：修改 `chunk_size` 和 `chunk_overlap`，看检索效果变化

3. **理解Agent的工作原理**
   - 读 `agent_service.py`，重点看 ReAct 模式的提示词
   - 观察Agent模式下的「思考过程」展示
   - 思考：Agent是怎么决定用哪个工具的？

### 第三阶段：动手修改和扩展（1-2周）

1. **简单修改（热身）**
   - 修改系统提示词，让助手用不同的语气回答
   - 添加一个新的FAQ条目
   - 改变RAG返回的文档数量（top_k）

2. **中等难度（核心练习）**
   - 添加一个新的Agent工具（比如：计算器、天气查询）
   - 换一个LLM提供商（比如从火山方舟换到通义千问）
   - 实现对话历史持久化（目前是纯前端内存）

3. **进阶挑战**
   - 添加用户认证和权限管理
   - 实现流式输出（SSE）
   - 添加对话评价和反馈功能
   - 部署到云服务器

### 第四阶段：深入原理（持续学习）

1. **向量数据库原理**
   - 什么是Embedding？为什么能做语义检索？
   - 不同的相似度计算方法（余弦、欧氏距离...）
   - 了解 Milvus / Pinecone / Weaviate 等生产级向量库

2. **Agent设计模式**
   - ReAct、Plan-and-Execute、Reflection等模式
   - 多Agent协作（AutoGPT、MetaGPT）
   - Agent框架对比：LangChain vs LlamaIndex vs AutoGen

3. **工程化能力**
   - 评测体系：如何量化评估RAG和Agent的效果？
   - 缓存和成本优化
   - 监控和可观测性

---

## 🔧 配置说明

### LLM 提供商配置

本项目支持所有 OpenAI 兼容接口的大模型平台。在 `.env` 中配置：

| 平台 | LLM_BASE_URL | 模型示例 |
|------|-------------|----------|
| 火山方舟（豆包） | `https://ark.cn-beijing.volces.com/api/v3` | `doubao-pro-32k-241028` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| 智谱AI | `https://open.bigmodel.cn/api/paas/v4` | `glm-4` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |

> **火山方舟提示：** 需要先在火山方舟控制台创建「推理接入点」，获取接入点ID作为模型名称。

### 主要配置项

| 配置项 | 默认值 | 说明 |
|--------|--------|------|
| `LLM_API_KEY` | - | **必填**，你的API密钥 |
| `LLM_BASE_URL` | 火山方舟地址 | OpenAI兼容API地址 |
| `LLM_MODEL` | doubao-pro-32k | 对话模型名称 |
| `EMBEDDING_MODEL` | doubao-embedding | 向量嵌入模型 |
| `CHUNK_SIZE` | 500 | 文档切分大小（字符） |
| `CHUNK_OVERLAP` | 50 | 切分重叠大小（字符） |
| `RAG_TOP_K` | 4 | RAG检索返回数量 |

---

## 📁 项目结构

```
it-service-assistant/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── main.py             # FastAPI入口
│   │   ├── config.py           # 配置管理
│   │   ├── models/             # 数据模型（Pydantic）
│   │   ├── api/                # API路由层
│   │   │   ├── chat.py         # 对话接口
│   │   │   ├── rag.py          # RAG接口
│   │   │   ├── agent.py        # Agent接口
│   │   │   ├── documents.py    # 文档管理接口
│   │   │   └── admin.py        # 管理接口
│   │   ├── services/           # 业务逻辑层
│   │   │   ├── llm_service.py  # LLM调用封装
│   │   │   ├── rag_service.py  # RAG检索增强
│   │   │   ├── agent_service.py # Agent推理引擎
│   │   │   └── document_service.py # 文档处理
│   │   └── utils/              # 工具函数
│   ├── data/                   # 数据存储（向量库等）
│   ├── uploads/                # 上传的文档
│   ├── requirements.txt        # Python依赖
│   └── Dockerfile
├── frontend/                   # 前端（纯静态，零构建）
│   ├── index.html              # 对话主页面
│   ├── admin.html              # 管理后台
│   ├── css/style.css           # 自定义样式
│   └── js/
│       ├── api.js              # API调用封装
│       ├── chat.js             # 对话界面逻辑
│       └── admin.js            # 管理后台逻辑
├── sample_docs/                # 示例文档
│   ├── VPN故障排查指南.md
│   ├── 企业邮箱配置与使用指南.md
│   └── 密码重置与账号安全管理.md
├── docker-compose.yml          # Docker编排
├── nginx.conf                  # Nginx配置
├── .env.example                # 环境变量示例
├── PROJECT_STRUCTURE.md        # 详细技术架构文档
└── README.md                   # 本文件
```

---

## ❓ 常见问题

### Q: 启动后对话报错怎么办？

**检查清单：**
1. API Key 是否正确配置（注意不要有空格）
2. Base URL 是否正确（不要漏掉 `/v3` 或 `/v1`）
3. 模型名称是否正确（火山方舟要用推理接入点ID）
4. 网络是否能访问API端点（国内访问国外API可能需要代理）

**快速验证：**
访问 http://localhost:8000/docs ，用交互式文档测试 `/api/chat/send` 接口，看具体错误信息。

### Q: RAG回答质量不好怎么办？

常见优化方向（按优先级）：
1. **文档质量**：确保文档内容结构化、信息完整
2. **切分策略**：调整 chunk_size 和 chunk_overlap
3. **检索数量**：增加 top_k 获取更多上下文
4. **提示词优化**：改进 system prompt 的指令
5. **嵌入模型**：使用质量更好的嵌入模型
6. **重排序**：添加 Rerank 阶段（进阶）

### Q: 前端和后端不在同一个域名怎么办？

本项目前端调用的是 `http://localhost:8000/api`，如果后端部署在其他地址：

1. 修改 `frontend/js/api.js` 中的 `API_BASE` 变量
2. 或者使用 Nginx 反向代理（Docker Compose 方式已配置好）

---

## 📝 学习记录 - 新增内容

> 以下是在学习过程中逐步添加的功能，用 `🆕` 标记。

### 🆕 新增 1：Operations Agent（运维 Agent）

**背景：** 学习如何添加一个新的独立 Agent

**新增文件：**
- `backend/app/services/operations_agent_service.py` - 运维 Agent 服务
- `backend/app/api/operations_agent.py` - 运维 Agent API 端点

**新增功能：**
- 4 个运维工具：系统状态检查、服务管理、日志查询、资源监控
- 独立的对话历史持久化（localStorage）
- 前端侧边栏新增 Operations Agent 按钮

**学习要点：**
- 如何创建一个新的 Agent Service
- 如何注册新的 API 路由
- 前端如何支持新的 Agent 模式

---

### 🆕 新增 2：Router Agent + LangGraph 多 Agent 编排

**背景：** 学习多 Agent 协同，用 Router 自动分类问题并路由到对应 Agent

**新增文件：**
- `backend/app/services/router_agent_service.py` - 路由分类 Agent
- `backend/app/services/multi_agent_graph.py` - LangGraph 工作流编排
- `backend/app/api/multi_agent.py` - 多 Agent API 端点

**修改文件：**
- `backend/app/main.py` - 注册多 Agent 路由
- `backend/requirements.txt` - 添加 `langgraph` 依赖
- `frontend/js/api.js` - 添加 MultiAgentAPI 客户端
- `frontend/js/chat.js` - 添加多 Agent 模式支持
- `frontend/index.html` - 添加 Multi-Agent 按钮

**新增功能：**
- Router Agent：自动判断问题类型（service vs operations）
- LangGraph StateGraph：定义工作流状态和节点流转
- 条件边：根据 Router 决策动态选择执行路径
- 前端展示路由决策、置信度和原因

**学习要点：**
- LangGraph 的 State 管理机制
- 条件边（Conditional Edges）的使用
- 多 Agent 间的状态传递和更新
- LLM 输出格式校验与容错

---

### 🆕 新增 3：对话历史持久化

**背景：** 实现 Agent 模式下的对话历史保存和恢复

**修改文件：**
- `frontend/js/chat.js` - 添加 localStorage 持久化逻辑
- `backend/app/services/agent_service.py` - 支持 history 参数
- `backend/app/api/agent.py` - 接收 history 参数

**新增功能：**
- Agent 和 Operations Agent 模式的对话历史自动保存到 localStorage
- 刷新页面后自动恢复历史
- 切换模式时保留各自的历史记录
- 最多保留最近 10 条对话

**学习要点：**
- localStorage 的工作原理
- 前端状态持久化的最佳实践
- 如何将历史注入到 LLM Prompt 中