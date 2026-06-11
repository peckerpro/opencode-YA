# Secure Access to YA Web UI over SSH

## Status

FastAPI/Web UI 计划在 v0.2 实现。本文定义目标运行方式和安全默认值；在 `ya serve` 实现前，命令仅作为接口约定。

## Security Default

YA Web 服务默认：

```text
host = 127.0.0.1
port = 8000
```

启动目标命令：

```bash
ya serve --host 127.0.0.1 --port 8000
```

不要为了方便远程访问改为 `0.0.0.0`。通过 SSH 转发时，FastAPI 仍只需要监听 Linux loopback。

配置优先级应为 CLI 参数 > 环境变量/配置文件 > 安全默认值。任何 `0.0.0.0` 或非 loopback 监听都应显示明确警告。

## Option A: Windows Initiates Local Port Forwarding

这是从 Windows 访问 Linux YA 的推荐方式，也是大多数场景真正需要的方式。

### 1. 在 Linux 启动 YA

```bash
ya serve --host 127.0.0.1 --port 8000
```

验证仅本机可访问：

```bash
curl http://127.0.0.1:8000/health
ss -ltnp | grep 8000
```

`ss` 输出应显示 `127.0.0.1:8000`，而不是 `0.0.0.0:8000`。

### 2. 在 Windows PowerShell 建立隧道

```powershell
ssh -N -L 8000:127.0.0.1:8000 linux_user@linux_host
```

参数含义：

- 第一个 `8000`：Windows 本地监听端口。
- `127.0.0.1:8000`：从 Linux SSH server 视角访问 YA。
- `-N`：不启动远程 shell，只做转发。

然后在 Windows 浏览器打开：

```text
http://127.0.0.1:8000
```

若 Windows 的 8000 已占用，可改成本地 18000：

```powershell
ssh -N -L 18000:127.0.0.1:8000 linux_user@linux_host
```

浏览器打开 `http://127.0.0.1:18000`。

### 3. 可选 SSH 参数

```powershell
ssh -N `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -o ServerAliveCountMax=3 `
  -L 18000:127.0.0.1:8000 `
  linux_user@linux_host
```

建议使用 SSH key，并在 Linux 的 `sshd_config` 中保持合适的 `AllowTcpForwarding` 策略。

## Option B: Linux Initiates a Reverse Tunnel to Windows

只有在 Linux 无法被 Windows 主动 SSH 连接，但 Linux 可以主动连接 Windows SSH Server 时使用。

前提：

- Windows 已安装并启动 OpenSSH Server。
- Windows firewall 允许 SSH 入站。
- Windows SSH server 允许 TCP forwarding。
- Windows 账号使用 key 或安全认证。

在 Linux 启动 YA：

```bash
ya serve --host 127.0.0.1 --port 8000
```

再从 Linux 建立 reverse tunnel：

```bash
ssh -N \
  -o ExitOnForwardFailure=yes \
  -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 \
  -R 127.0.0.1:18000:127.0.0.1:8000 \
  windows_user@windows_host
```

然后在 Windows 浏览器打开：

```text
http://127.0.0.1:18000
```

`-R 127.0.0.1:...` 明确要求 Windows 端只绑定 loopback。不要把 reverse port 绑定到 `0.0.0.0`。

## SSH Config Examples

Windows 用户的 `%USERPROFILE%\.ssh\config`：

```sshconfig
Host ya-linux
    HostName linux_host
    User linux_user
    LocalForward 18000 127.0.0.1:8000
    ExitOnForwardFailure yes
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

使用：

```powershell
ssh -N ya-linux
```

## Binding and Authentication Notes

- SSH 隧道只解决传输和主机访问，不自动替代 Web UI 自身的会话保护。
- v0.2 最小 Web UI 即使只绑定 loopback，也应防止跨站请求、任意文件读取和未经确认的危险工具调用。
- 不把 MiniMax/MinerU/GitHub key 发给浏览器；由 Linux 后端安全读取。
- API 响应和日志不得返回 secret。
- 如未来使用反向代理或公网 gateway，必须单独设计 TLS、认证、CSRF/CORS、速率限制和审计，不能沿用“本地可信”假设。

## Troubleshooting

### Windows 端口已占用

```powershell
netstat -ano | findstr :18000
```

改用其他 Windows 本地端口，不需要修改 Linux YA 端口。

### SSH 报转发失败

使用：

```powershell
ssh -vvv -N -L 18000:127.0.0.1:8000 linux_user@linux_host
```

检查：

- SSH 是否能正常登录。
- Linux `sshd` 是否允许 forwarding。
- YA 是否真的监听 `127.0.0.1:8000`。
- 转发端口是否被占用。

### 隧道建立但页面打不开

先在 Linux 执行：

```bash
curl -v http://127.0.0.1:8000/health
```

若 Linux 本机也失败，问题在 YA 服务而不是 SSH。若 Linux 成功，再检查 SSH verbose 输出和 Windows 本地端口。

### 检查是否误暴露公网

Linux：

```bash
ss -ltnp | grep 8000
```

安全默认应显示 loopback 地址。发现 `0.0.0.0:8000` 或 `[::]:8000` 时，停止服务并修正 host 配置。

