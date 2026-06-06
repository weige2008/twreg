# GitHub Actions 集成改造总结

## 改造内容

本项目已完全改造为 **GitHub Actions 运行版本**。所有配置参数以**明文形式**存储在 `config.txt`，通过 GitHub Actions 自动执行。

## 文件变更

### 1. 修改的文件

#### `/workspaces/tw_reg/reg_linux/config.py`
- **改变**: 支持从 `config.txt` 直接读取配置
- **特点**:
  - 优先级: 环境变量 > .env > config.txt > 默认值
  - 自动解析 INI 格式的 config.txt
  - 向后兼容环境变量方式
  - 支持 `FRONT_IP` 参数自动构建 `API_URL`

#### `/workspaces/tw_reg/reg_linux/README.md`
- **改变**: 更新了项目说明文档
- **新增内容**:
  - GitHub Actions 快速开始指南
  - config.txt 参数详解
  - 参数优先级说明
  - 配置方式对比

### 2. 创建的文件

#### `.github/workflows/twitch-registration.yml` (GitHub Actions Workflow)
**核心工作流文件**，包含3个阶段：

**a) prepare 阶段**
  - 读取 `reg_linux/config.txt`
  - 解析 `REG_THREADS` 数量
  - 解析 `REGISTER_COUNT` 数量
  - 生成 job 执行矩阵

**b) register 阶段 (并发执行)**
  - 为每个 job index 创建独立的运行实例
  - 并发数量由 `config.txt` 中的 `REG_THREADS` 决定
  - 安装系统依赖和 Python 依赖
  - 启动虚拟显示环境 (Xvfb)
  - 执行注册程序
  - 自动上传日志文件

**c) summary 阶段**
  - 汇总所有 job 的执行结果
  - 显示总结信息
  - 收集日志文件

#### `/workspaces/tw_reg/reg_linux/run_github_actions.sh`
**GitHub Actions 专用启动脚本**，用于:
  - 设置虚拟显示环境
  - 加载 config.txt 配置
  - 启动 Xvfb 虚拟显示
  - 执行注册程序

#### `/workspaces/tw_reg/GITHUB_ACTIONS_GUIDE.md`
**完整的 GitHub Actions 使用指南**，包括:
  - 配置参数详解
  - 三种使用方式说明
  - 工作流程图解
  - 常见问题解答
  - 故障排除指南
  - 安全建议

## 核心特性

### ✅ 配置管理
- **明文存储**: 所有配置在 `config.txt` 明文显示
- **INI 格式**: 标准格式，易于编辑和维护
- **支持注释**: 行首 `#` 为注释行
- **灵活覆盖**: 环境变量可覆盖配置文件

### ✅ 并发执行
- **动态 Job 数量**: 根据 `REG_THREADS` 参数自动生成
- **独立 Job 实例**: 每个 job 完全独立运行
- **并行执行**: GitHub Actions 会自动并发运行多个 job
- **日志隔离**: 每个 job 独立上传日志

### ✅ 灵活触发
1. **手动触发** (Manual Dispatch)
   - 进入 GitHub Actions 页面手动运行
   
2. **定时触发** (Scheduled)
   - 默认每天 UTC 2:00 自动运行
   - 可自定义 cron 表达式

3. **推送触发** (可选)
   - 修改 config.txt 时自动触发

### ✅ 系统支持
- **虚拟显示**: 自动配置 Xvfb 虚拟显示 (无需实体显示器)
- **依赖管理**: 自动安装所有系统和 Python 依赖
- **日志收集**: 自动收集并保存所有 job 的日志

## 使用流程

### 快速开始 (3 步)

```bash
# 1. 编辑配置文件
vim reg_linux/config.txt
# 修改参数，特别是:
#   - REG_THREADS=N     (启动N个并发job)
#   - REGISTER_COUNT=M  (每个job注册M个账户)

# 2. 提交到仓库
git add reg_linux/config.txt
git commit -m "Update registration config"
git push

# 3. 手动触发 GitHub Actions
# 进入 GitHub 仓库 → Actions → Twitch CDK Registration → Run workflow
```

### 工作流程

```
config.txt (包含 REG_THREADS=2)
        ↓
    prepare 阶段
    ├─ 读取 REG_THREADS=2
    ├─ 生成 job 矩阵: [0, 1]
        ↓
    register 阶段 (并发执行)
    ├─ Job 0 (WORKER_ID=reg_job_0_xxx)
    │  └─ 注册 REGISTER_COUNT 个账户
    │
    └─ Job 1 (WORKER_ID=reg_job_1_xxx)
       └─ 注册 REGISTER_COUNT 个账户
        ↓
    summary 阶段
    └─ 汇总结果，生成日志
```

## 配置参数速查

| 参数 | 含义 | 示例 |
|------|------|------|
| **REG_THREADS** | **GitHub Actions 并发 job 数** | `2` = 2个job并发 |
| **REGISTER_COUNT** | **每个job注册的账户数** | `10` = 每个job注10个 |
| **FRONT_IP** | 前端服务器IP | `8.138.198.37` |
| **API_TOKEN** | API认证令牌 | `twitch-cdk-...` |
| **PREFIX** | 注册账户名前缀 | `blue_ctf` |
| **PASSWORD** | 统一密码 | `BlueCtf2026!...` |
| **DEBUG** | 调试模式 | `false` / `true` |

**计算总注册数**: REG_THREADS × REGISTER_COUNT

例如: `REG_THREADS=2, REGISTER_COUNT=10` → 总共注册 2×10=**20个账户**

## 文件清单

```
/workspaces/tw_reg/
├── .github/
│   └── workflows/
│       └── twitch-registration.yml          # ✨ GitHub Actions workflow
├── reg_linux/
│   ├── config.txt                           # ✏️ 配置文件 (明文)
│   ├── config.py                            # ✏️ 改进: 支持config.txt
│   ├── README.md                            # ✏️ 改进: 添加GA说明
│   ├── run_github_actions.sh                # ✨ 新增: GA启动脚本
│   ├── main.py                              # (保持不变)
│   ├── twitch_registration.py               # (保持不变)
│   ├── api_client.py                        # (保持不变)
│   ├── requirements.txt                     # (保持不变)
│   ├── start.sh                             # (保持不变)
│   └── install.sh                           # (保持不变)
└── GITHUB_ACTIONS_GUIDE.md                  # ✨ 新增: 详细指南
```

## 向后兼容性

✅ **完全向后兼容**: 现有的本地运行方式保持不变

- `bash start.sh` 仍然可以本地运行
- 环境变量方式仍然支持
- .env 文件方式仍然支持
- 只是新增了 `config.txt` 配置方式

## 安全考虑

⚠️ **建议**:

1. **私有仓库**: 建议使用私有仓库存储敏感配置
2. **Secrets**: 对于非常敏感的令牌，考虑使用 GitHub Secrets
3. **访问控制**: 限制谁可以手动触发 workflow

## 常见问题

**Q: 如何修改并发job数量?**
A: 编辑 `config.txt` 中的 `REG_THREADS` 值

**Q: 如何修改每个job的注册数量?**
A: 编辑 `config.txt` 中的 `REGISTER_COUNT` 值

**Q: 在哪里查看日志?**
A: GitHub Actions 页面，每个 job 的日志输出，或在 Artifacts 中下载完整日志

**Q: 如何停止正在运行的job?**
A: GitHub Actions 页面的 "Cancel workflow" 按钮

## 技术细节

### Job 矩阵生成
```bash
# config.txt 中 REG_THREADS=3 会生成
{
  "job-index": [0, 1, 2]
}
```

### 环境变量设置
每个 job 会自动接收:
- `WORKER_ID=reg_job_{index}_{run_id}`
- `TWITCH_CTF=1`
- `LOGURU_LEVEL=INFO`
- `DISPLAY=:99` (虚拟显示)

### 日志位置
- **实时日志**: GitHub Actions 页面
- **完整日志**: `Artifacts/logs-job-*`
- **保留期**: 7天

## 升级指南

如果从旧版本升级:

1. 保持 `config.txt` 不变 (参数完全兼容)
2. 推送 `.github/workflows/twitch-registration.yml`
3. 推送 `GITHUB_ACTIONS_GUIDE.md`
4. 推送更新后的 `config.py`
5. 可选: 推送更新后的 `README.md`

## 支持的 Python 版本

- ✅ Python 3.8+
- ✅ GitHub Actions 默认的 Python 3.11
- 推荐: Python 3.10+

## 依赖

- Python: 3.8+
- Playwright: 1.50.0+
- Cloakbrowser: 0.3.0+
- 系统: Ubuntu 20.04 LTS+

---

**改造完成日期**: 2026-06-06
**当前版本**: GitHub Actions 集成版 v1.0
