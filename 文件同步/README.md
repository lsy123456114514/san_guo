# 文件同步：Windows → Linux 开机自动拉取 + 旧版回传

把 Windows 上指定的文件，在 **Linux 开机联网后自动传过来**；如果 Linux 上的旧版本
不一样，就把它**打上日期压成 zip**，再**回传给 Windows**，然后写入新文件。

点对点直连（P2P），不经过任何云盘。用 **HTTP over Tailscale** 实现：
- 传输是两台机器直连（Tailscale 打洞，连不上时自动走中继兜底）
- 纯 Python 标准库，无需安装任何 pip 包
- Windows 只当"服务端"，Linux 当"客户端"，不用担心 Windows 没有 SSH Server

```
┌─────────────┐   HEAD /file (问 hash)      ┌──────────────┐
│  Windows    │ ◀────────────────────────── │   Linux      │
│  sync_server│   GET  /file (下载新版)      │  sync_client │  ← 开机/定时触发
│  :8765      │ ◀────────────────────────── │              │
│             │   PUT  /backup/旧版.zip     │  旧版打包     │
│             │ ◀────────────────────────── │              │
└─────────────┘                             └──────────────┘
```

---

## 一、准备：Tailscale（跨网络也能直连的关键）

两台机器都装、都用**同一个账号**登录：

- Windows：https://tailscale.com/download/windows
- Linux：`curl -fsSL https://tailscale.com/install.sh | sh && sudo tailscale up`

装好后 Windows 的 Tailscale 名称/IP 就是 Linux 端要填的地址。
（若两台机器本来就在同一局域网，也可以直接用 Windows 的内网 IP，跳过 Tailscale。）

---

## 二、Windows 端（文件源 + 服务端）

1. 确认装了 Python（`py --version` 能出结果）。
2. 把本目录的 `config.server.example.json` 复制成 **`config.server.json`**，改成：
   ```json
   {
     "server": {
       "bind": "0.0.0.0",
       "port": 8765,
       "token": "自己编一个随机口令",
       "share_file": "C:/你要共享的文件/notes.md",
       "backup_dir": "C:/来自Linux的旧版备份"
     }
   }
   ```
3. **以管理员身份**打开 PowerShell，运行：
   ```powershell
   .\setup_windows.ps1 -Config .\config.server.json
   ```
   它会：创建备份目录、放行防火墙、把服务端注册成**开机自启**并立刻启动，
   最后打印出 Linux 要填的地址（Tailscale IP:8765）。

> 手动测试：`py sync_server.py --config config.server.json`

---

## 三、Linux 端（客户端，开机自动拉取）

1. 确认有 `python3`。
2. 把 `config.client.example.json` 复制成 `config.client.json`，改成：
   ```json
   {
     "client": {
       "server_url": "http://Windows的Tailscale名或IP:8765",
       "token": "和 Windows 端一模一样",
       "local_file": "/home/你/文件保存到哪/notes.md",
       "local_backup_dir": "/home/你/旧版备份放哪",
       "log_file": "/home/你/sync.log",
       "timeout": 120,
       "retries": 5
     }
   }
   ```
3. 安装为开机自启：
   ```bash
   sudo chmod +x install_linux.sh
   sudo ./install_linux.sh ./config.client.json
   ```
   装好后：开机 2 分钟自动跑一次，之后每 15 分钟一次。

**手动测试**：
```bash
python3 sync_client.py --config config.client.json --dry-run   # 只看差异，不写
python3 sync_client.py --config config.client.json             # 真正同步
```

---

## 四、它会怎么工作（对应你的需求）

| 情况 | 行为 |
|---|---|
| 远端和本地一致 | 什么都不做 |
| 远端变了，本地也有旧版 | ① 旧版压成 `文件名_20261003_221501.zip` 存到本地备份目录；② 把该 zip **回传** Windows 的 `backup_dir`；③ 下载新版覆盖本地 |
| 本地没有文件 | 直接下载，不备份 |

回传的 zip 会出现在 Windows 的 `backup_dir` 里，按时间戳命名，永不覆盖。

---

## 五、常见问题

- **连不上**：先在 Linux 上 `ping Windows的TailscaleIP`，再 `curl http://IP:8765/file` 看是否 401（401 说明通了，只是 token 不对）或超时（说明服务端没起/防火墙）。
- **改了 token**：两端 `config*.json` 的 token 必须一致。
- **共享多个文件**：目前一份配置对一个文件。要多个，就把客户端脚本复制多份配置，或在此脚本上扩展 `files` 列表（欢迎提需求）。
- **想改成双向同步**：把客户端逻辑对称地做一遍即可；当前实现是"Windows 为源，Linux 保留并回传旧版本"。
