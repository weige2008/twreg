# Twitch CDK 注册机 (Linux)

## 快速开始

### GitHub Actions (推荐)

所有配置以**明文形式**存储在 `config.txt`，通过 GitHub Actions 自动运行：

1. **编辑配置**：修改 `reg_linux/config.txt`
2. **提交推送**：`git push` 到仓库
3. **手动触发**：进入 GitHub → Actions → 选择 "Twitch CDK Registration" → Run workflow
4. **自动运行**：默认每天 UTC 2:00 自动运行

详见 [GitHub Actions 使用指南](../GITHUB_ACTIONS_GUIDE.md)

### 本地运行

```bash
cd reg_linux
bash start.sh
```

## 系统依赖

首次部署需安装 Python 和 Chromium 系统库：

```bash
# 1. Python 及 pip
apt install -y python3 python3-pip python3-full

# 2. Chromium 浏览器依赖（完整清单）
apt install -y \
    libatk1.0-0t64 libatk-bridge2.0-0t64 libcups2t64 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 \
    libgbm1 libpango-1.0-0 libcairo2 libnspr4 libnss3 \
    libasound2t64 libxshmfence1 libx11-xcb1 libxcb-dri3-0 \
    libxfixes3 libxext6 libxinerama1
```

> 旧版 Ubuntu/Debian 把 `t64` 后缀去掉，如 `libatk1.0-0` 替代 `libatk1.0-0t64`

## 配置说明

### config.txt - 明文配置文件

所有参数存储在 `reg_linux/config.txt`（INI 格式）：

```ini
FRONT_IP=8.138.198.37              # 前端服务器IP
API_TOKEN=twitch-cdk-api-token-2024 # API认证令牌
MAIL_API_URL=https://mailapi.izlvxhe.cn
MAIL_ADMIN_AUTH=Aalcsttkx1!
MAIL_DOMAINS=htazmbb.shop
REGISTER_COUNT=10                  # 每个job的注册数量
REG_THREADS=2                      # GitHub Actions并发job数 (并发数量)
PREFIX=blue_ctf                    # 账户名前缀
PASSWORD=BlueCtf2026!Secure        # 统一密码
DEBUG=false                        # 调试模式
```

### 环境变量方式 (可选覆盖)

修改 `../.env` 或直接设置环境变量（优先级高于 config.txt）：

| 变量 | 说明 | 优先级 |
|------|------|--------|
| `API_URL` | 前端 API 地址 | 覆盖 FRONT_IP |
| `REGISTER_COUNT` | 注册数量 | 覆盖 config.txt |
| `REG_THREADS` | 并发线程数 | 覆盖 config.txt |
| `PREFIX` | 用户名前缀 | 覆盖 config.txt |
| `PASSWORD` | 统一密码 | 覆盖 config.txt |
| `TIMEOUT` | 验证码超时(秒) | 默认 90 |
| `MAX_RETRIES` | 失败重试次数 | 默认 2 |

### 参数优先级

1. **环境变量** (最高)
2. **.env 文件**
3. **config.txt** 
4. **代码默认值** (最低)
