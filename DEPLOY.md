# 内网穿透指南 (Cloudflare Tunnel)

本指南介绍如何使用 **Cloudflare Tunnel (TryCloudflare)** 将本地运行的豆瓣数据分析系统（端口 5001）免费发布到公网。

## 1. 安装 Cloudflare Tunnel (`cloudflared`)

### Windows 用户
1.  下载 `cloudflared-windows-amd64.exe`：[点击下载](https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe)
2.  将下载的文件重命名为 `cloudflared.exe`。
3.  打开 PowerShell，进入该文件所在的文件夹。

### WSL / Linux 用户 (推荐)
在终端执行以下命令直接安装：

```bash
# 下载
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# 安装
sudo dpkg -i cloudflared.deb
```

## 2. 启动隧道

确保您的 Flask 应用已经在运行中（监听 5001 端口）：
```bash
python app.py
```

新开一个终端窗口，执行以下命令来创建临时隧道：

```bash
cloudflared tunnel --url http://localhost:5001
```

## 3. 获取公网地址

启动后，注意观察终端输出，找到以 `.trycloudflare.com` 结尾的链接：

```text
...
2023-12-19T14:00:00Z INF +--------------------------------------------------------------------------------------------+
2023-12-19T14:00:00Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2023-12-19T14:00:00Z INF |  https://meaningless-random-words.trycloudflare.com                                       |
2023-12-19T14:00:00Z INF +--------------------------------------------------------------------------------------------+
...
```

复制那个 **`https://xxxx-xxxx.trycloudflare.com`** 的链接。
任何人都可以通过这个链接访问您的网站！无需注册账号。

## ⚠️ 优势与限制
*   **优势**: 无需注册，完全免费，无需配置 Authtoken，速度很快。
*   **限制**: 每次重启隧道，生成的域名都会随机变化（临时使用非常方便）。
