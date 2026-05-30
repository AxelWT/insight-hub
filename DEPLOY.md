# 部署指南

## 部署方式

### 方式一：GitHub Actions 自动部署（推荐）

代码推送到 `main` 分支时自动部署到服务器。

#### 1. 服务器初始化

```bash
# SSH 登录服务器
ssh root@your-server-ip

# 运行初始化脚本
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/insight-hub/main/scripts/server-init.sh | bash

# 或者手动执行
mkdir -p /opt/insight-hub
cd /opt/insight-hub
git clone https://github.com/YOUR_USERNAME/insight-hub.git .
cp .env.example .env
vim .env  # 填写 API Key
```

#### 2. 生成 SSH 密钥

在本地电脑生成 SSH 密钥对：

```bash
# 生成密钥（如果还没有）
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/github_actions -N ""

# 查看公钥（添加到服务器）
cat ~/.ssh/github_actions.pub

# 查看私钥（添加到 GitHub Secrets）
cat ~/.ssh/github_actions
```

#### 3. 配置服务器 SSH

```bash
# 在服务器上添加公钥
echo "你的公钥内容" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

#### 4. 配置 GitHub Secrets

在 GitHub 仓库页面：**Settings → Secrets and variables → Actions → New repository secret**

添加以下 Secrets：

| 名称 | 值 |
|------|-----|
| `SERVER_HOST` | 服务器 IP 地址 |
| `SERVER_USER` | SSH 用户名（如 `root`） |
| `SERVER_SSH_KEY` | SSH 私钥完整内容（包括 BEGIN 和 END） |

#### 5. 测试部署

```bash
# 推送代码触发部署
git add .
git commit -m "feat: new feature"
git push origin main

# 在 GitHub 仓库 Actions 页面查看部署进度
```

---

### 方式二：手动部署

#### 1. 登录服务器

```bash
ssh root@your-server-ip
```

#### 2. 进入项目目录

```bash
cd /opt/insight-hub
```

#### 3. 执行部署

```bash
# 使用部署脚本
./scripts/deploy.sh

# 或手动执行
git pull origin main
docker compose down
docker compose up -d --build
```

---

## 服务器要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 操作系统 | Ubuntu 20.04 / CentOS 7 | Ubuntu 22.04 |
| CPU | 1 核 | 2 核 |
| 内存 | 1 GB | 2 GB |
| 磁盘 | 20 GB | 40 GB |
| 网络 | 公网 IP | 带宽 5Mbps+ |

## 端口配置

需要开放以下端口：

```bash
# 防火墙配置（Ubuntu/Debian）
ufw allow 80/tcp    # 前端
ufw allow 8000/tcp  # 后端 API
ufw allow 22/tcp    # SSH

# 防火墙配置（CentOS）
firewall-cmd --permanent --add-port=80/tcp
firewall-cmd --permanent --add-port=8000/tcp
firewall-cmd --reload
```

## 域名配置（可选）

如果需要使用域名访问，可以配置 Nginx 反向代理：

```nginx
# /etc/nginx/sites-available/insight-hub
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://localhost:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## SSL 证书（推荐）

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
apt install certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your-domain.com

# 自动续期
certbot renew --dry-run
```

## 常见问题

### Q: 部署失败怎么办？

```bash
# 查看 GitHub Actions 日志
# 在仓库 Actions 页面点击失败的 workflow

# 查看服务器日志
cd /opt/insight-hub
docker compose logs -f
```

### Q: 如何回滚版本？

```bash
cd /opt/insight-hub
git log --oneline  # 查看历史版本
git checkout <commit-hash>  # 切换到指定版本
docker compose up -d --build
```

### Q: 如何查看服务状态？

```bash
cd /opt/insight-hub
docker compose ps        # 查看容器状态
docker compose logs -f   # 查看实时日志
```

### Q: 如何重启服务？

```bash
cd /opt/insight-hub
docker compose restart
```

### Q: 如何更新环境变量？

```bash
cd /opt/insight-hub
vim .env                # 编辑配置
docker compose restart  # 重启服务
```
