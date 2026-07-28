# Minecraft AI Agent

基于 LangGraph 的游戏智能体系统，三层异构架构：Python（决策）+ Java（业务中台）+ Node.js（执行层）。

## 项目结构

```
minecraft-agent/
├── java-service/       # Java 业务中台（Spring Boot）
├── python-agent/       # Python 决策层（FastAPI + LangGraph）
├── node-bot/           # Node.js 执行层（Mineflayer）
├── .env                # 环境变量
└── README.md
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env .env.local
# 编辑 .env.local，填入真实的 API Key
```

### 2. 启动 Java 服务

```bash
cd java-service
./mvnw spring-boot:run
```

### 3. 启动 Python Agent

```bash
cd python-agent
pip install -r requirements.txt
python main.py
```

### 4. 启动 Node.js Bot

```bash
cd node-bot
npm install
npm start
```
