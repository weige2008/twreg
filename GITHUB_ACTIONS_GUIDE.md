# GitHub Actions 配置指南

## 概述

本项目现已支持通过 GitHub Actions 自动化运行 Twitch CDK 注册机。所有配置以明文形式存储在 `reg_linux/config.txt` 中。

## 配置文件说明

### config.txt 参数详解

```
FRONT_IP=8.138.198.37              # 前端服务器IP地址
API_TOKEN=twitch-cdk-api-token-2024 # API认证令牌
MAIL_API_URL=https://mailapi.xxx.cn # 邮件API地址
MAIL_ADMIN_AUTH=Aalcsttkx1!        # 邮件API认证
MAIL_DOMAINS=htazmbb.shop          # 邮件域名
REGISTER_COUNT=10                  # 每个job注册的账户数 (单个并发线程的任务量)
REG_THREADS=2                      # GitHub Actions job数量 (并发job数)
PREFIX=blue_ctf                    # 注册账户名前缀
PASSWORD=BlueCtf2026!Secure        # 统一密码
DEBUG=false                        # 调试模式
```

### 关键参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| **REG_THREADS** | GitHub Actions **并发job数量** | 2 = 启动2个并发job |
| **REGISTER_COUNT** | 每个job要注册的**账户数量** | 10 = 每个job注册10个账户 |
| 总注册数 | REG_THREADS × REGISTER_COUNT | 2 × 10 = 20个账户 |

## 使用方式

### 方式1：手动触发（Manual Dispatch）

1. 推送 `config.txt` 到仓库
2. 进入 GitHub 仓库 → **Actions** 选项卡
3. 选择 **"Twitch CDK Registration"** workflow
4. 点击 **"Run workflow"** → **"Run workflow"**
5. GitHub Actions 会根据 `config.txt` 中的 `REG_THREADS` 启动相应数量的并发job

### 方式2：定时运行（Scheduled）

workflow 已配置每天 UTC 2:00 自动运行，无需手动操作。

修改定时规则：编辑 `.github/workflows/twitch-registration.yml`

```yaml
schedule:
  - cron: '0 2 * * *'  # UTC时间 2:00
```

## 工作流程说明

### 执行流程

```
┌─────────────────────────────────────┐
│  prepare (准备阶段)                  │
│  - 读取 config.txt                   │
│  - 解析 REG_THREADS 数量             │
│  - 生成 job 矩阵                     │
└──────────────┬──────────────────────┘
               │
               ├──────────────────────────────────────┐
               │                                      │
        ┌──────▼─────┐  ┌────────────┐  ┌────────────┐
        │  Job 0     │  │   Job 1    │  │   Job N    │
        │  (并发运行) │  │  (并发运行) │  │  (并发运行) │
        └──────┬─────┘  └────────────┘  └────────────┘
               │                                      │
               └──────────────────────────────────────┘
                       │
            ┌──────────▼──────────────┐
            │  summary (汇总阶段)      │
            │  - 收集所有job日志      │
            │  - 显示执行摘要         │
            └───────────────────────┘
```

### 各阶段详解

**1. prepare (准备阶段)**
   - 检出代码
   - 读取 `reg_linux/config.txt`
   - 提取 `REG_THREADS` 和 `REGISTER_COUNT` 值
   - 生成 job 矩阵用于并发执行

**2. register (注册阶段，并发执行)**
   - 为每个 job index 创建独立的运行实例
   - 并行安装系统依赖和 Python 依赖
   - 启动虚拟显示 (Xvfb)
   - 执行注册程序
   - 上传日志文件

**3. summary (汇总阶段)**
   - 下载所有 job 的日志
   - 显示执行统计信息

## GitHub Actions 设置要点

### 必需配置

1. **代码仓库权限**
   - 确保 `.github/workflows/twitch-registration.yml` 已提交
   - 确保 `reg_linux/config.txt` 已提交

2. **Actions 权限**
   - 仓库 Settings → Actions → General
   - 确保 "Read and write permissions" 已启用

3. **config.txt 提交**
   - 所有配置参数必须在 `reg_linux/config.txt` 中
   - 建议添加到 `.gitignore` 前缀位置后再手动提交关键版本

### 可选配置

**自定义定时规则**

编辑 `.github/workflows/twitch-registration.yml` 中的 schedule:

```yaml
on:
  workflow_dispatch:      # 手动触发
  schedule:
    - cron: '0 2 * * *'   # 每天 UTC 2:00
    # - cron: '0 */6 * * *' # 每6小时运行一次
    # - cron: '0 10 * * 1' # 每周一 UTC 10:00
```

**修改并发限制**

```yaml
strategy:
  max-parallel: 10  # 最多并发10个job
```

## 日志和输出

### 查看日志

1. 进入 GitHub 仓库 → **Actions**
2. 选择最近的 workflow 运行
3. 查看各个 job 的输出

### 下载完整日志

1. 进入已完成的 workflow run
2. 页面底部 "Artifacts" 部分
3. 下载 `logs-job-*` 压缩包

## 常见问题

### Q1: 如何修改并发job数量？

编辑 `reg_linux/config.txt`，改变 `REG_THREADS` 值：

```bash
REG_THREADS=5  # 将启动5个并发job
```

重新提交并手动触发 workflow。

### Q2: 如何修改每个job的注册数量？

编辑 `reg_linux/config.txt`，改变 `REGISTER_COUNT` 值：

```bash
REGISTER_COUNT=20  # 每个job注册20个账户
```

### Q3: 日志在哪里？

- **实时日志**: GitHub Actions 页面中每个 job 的日志
- **完整日志**: Artifacts 中 `logs-job-*` 压缩包

### Q4: 如何停止正在运行的job？

GitHub Actions 页面 → 选择正在运行的 workflow → 点击 "Cancel workflow"

### Q5: config.txt 支持哪些格式？

支持标准 ini 风格的 `KEY=VALUE` 格式：

```
# 注释行（以#开头）
KEY=VALUE    # 支持行尾注释
EMPTY_KEY=   # 支持空值
```

## 故障排除

### 问题: Job 失败但没有日志

1. 确认 `reg_linux/config.txt` 存在且格式正确
2. 检查 Python 依赖是否安装成功
3. 查看 workflow 的"准备"步骤输出

### 问题: REG_THREADS 没有被识别

确保 `reg_linux/config.txt` 中有：
```
REG_THREADS=N
```

不要使用空格或其他格式。

### 问题: 浏览器启动失败

- 系统依赖可能未完整安装
- 检查 workflow 日志中的 "Install system dependencies" 步骤
- Xvfb 虚拟显示可能未启动

## 自定义扩展

### 修改 workflow 触发条件

编辑 `.github/workflows/twitch-registration.yml`:

```yaml
on:
  workflow_dispatch:
  push:
    branches: [main]
    paths: ['reg_linux/config.txt']  # config.txt 变更时触发
  pull_request:
```

### 添加通知

在 `summary` job 中添加：

```yaml
      - name: Send notification
        run: |
          curl -X POST https://your-webhook.url \
            -d "status=${{ needs.register.result }}"
```

## 安全建议

1. **不要提交敏感信息到公开仓库**
   - 如使用私密 token，考虑使用 GitHub Secrets
   - 编辑 workflow 使用 `secrets.API_TOKEN` 替代明文

2. **使用私有仓库**
   - 避免 config.txt 中的配置被公开

3. **定期更新依赖**
   - 定期检查 `requirements.txt` 的更新

## 下一步

- 推送 `.github/workflows/twitch-registration.yml` 到仓库
- 推送修改后的 `reg_linux/config.txt`
- 进入 GitHub Actions 手动触发 workflow 测试
- 监控第一次运行，调整参数如需要
