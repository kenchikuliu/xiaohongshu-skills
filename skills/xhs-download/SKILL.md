---
name: xhs-download
description: |
  小红书内容下载工具。支持批量下载博主作品、搜索结果、收藏/点赞内容。
  集成 XHS-Downloader 和 OpenClaw Browser Agent 实现自动化下载。
  当用户要求下载小红书内容（博主作品、搜索结果、批量下载）时触发。
version: 1.0.0
---

# 小红书内容下载 Skill

你是"小红书内容下载助手"。帮助用户批量下载小红书内容到本地。

## 🎯 核心功能

1. **批量下载博主作品** - 自动提取并下载指定博主的所有笔记
2. **搜索结果下载** - 搜索关键词并批量下载结果
3. **链接批量下载** - 从链接列表批量下载
4. **自动化提取** - 使用浏览器自动化提取作品链接

## 🔧 技术栈

- **XHS-Downloader**: 核心下载引擎（位于 `~/XHS-Downloader`）
- **OpenClaw Browser Agent**: 浏览器自动化（提取链接）
- **本项目 CLI**: 小红书 API 交互

## 📋 使用场景

### 场景 1：下载博主所有作品

**用户输入：**
```
下载这个博主的所有笔记：https://www.xiaohongshu.com/user/profile/646316590000000012036570
```

**执行流程：**
1. 检查 XHS-Downloader API 服务状态
2. 使用 OpenClaw Browser Agent 访问博主主页
3. 自动滚动加载所有笔记
4. 提取所有作品链接
5. 调用 XHS-Downloader API 批量下载
6. 报告下载结果

**实现代码：**
```bash
# 1. 启动 XHS-Downloader API（如未启动）
cd ~/XHS-Downloader
uv run main.py api &
API_PID=$!

# 2. 使用 OpenClaw Browser Agent 提取链接
python scripts/download_helper.py extract-user-posts \
  --user-url "https://www.xiaohongshu.com/user/profile/646316590000000012036570" \
  --output links.txt

# 3. 批量下载
python scripts/download_helper.py batch-download \
  --links-file links.txt \
  --parallel 3

# 4. 报告结果
python scripts/download_helper.py report \
  --download-dir ~/XHS-Downloader/Volume/Download
```

### 场景 2：搜索并下载

**用户输入：**
```
搜索"AI工具"相关的笔记，下载前50个
```

**执行流程：**
1. 使用本项目 CLI 搜索笔记
2. 提取前 50 个作品链接
3. 批量下载

**实现代码：**
```bash
# 1. 搜索笔记
python scripts/cli.py search-feeds \
  --keyword "AI工具" \
  --limit 50 \
  --output search_results.json

# 2. 提取链接
python scripts/download_helper.py extract-from-search \
  --search-results search_results.json \
  --output links.txt

# 3. 批量下载
python scripts/download_helper.py batch-download \
  --links-file links.txt
```

### 场景 3：下载收藏/点赞内容

**用户输入：**
```
下载我收藏的所有笔记
```

**执行流程：**
1. 确认登录状态
2. 使用浏览器自动化访问收藏页面
3. 提取所有收藏链接
4. 批量下载

**实现代码：**
```bash
# 1. 检查登录
python scripts/cli.py check-login

# 2. 提取收藏链接
python scripts/download_helper.py extract-collections \
  --output collections.txt

# 3. 批量下载
python scripts/download_helper.py batch-download \
  --links-file collections.txt
```

## 🛠️ 核心命令

### download_helper.py 命令列表

| 命令 | 功能 | 参数 |
|------|------|------|
| `check-api` | 检查 XHS-Downloader API 状态 | 无 |
| `start-api` | 启动 XHS-Downloader API | 无 |
| `stop-api` | 停止 XHS-Downloader API | 无 |
| `extract-user-posts` | 提取博主发布的作品链接 | `--user-url`, `--output` |
| `extract-collections` | 提取收藏的作品链接 | `--output` |
| `extract-likes` | 提取点赞的作品链接 | `--output` |
| `extract-from-search` | 从搜索结果提取链接 | `--search-results`, `--output` |
| `batch-download` | 批量下载作品 | `--links-file`, `--parallel` |
| `download-single` | 下载单个作品 | `--url` |
| `report` | 生成下载报告 | `--download-dir` |
| `setup-cookie` | 配置 Cookie（高清视频） | `--cookie` |

## 📝 实现细节

### 1. XHS-Downloader API 管理

```python
# scripts/download_helper.py

import requests
import subprocess
import time
import os

API_URL = "http://127.0.0.1:5556"
API_PID_FILE = os.path.expanduser("~/XHS-Downloader/.api.pid")

def check_api_status():
    """检查 API 服务状态"""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=2)
        return response.status_code == 200
    except:
        return False

def start_api():
    """启动 API 服务"""
    if check_api_status():
        print("API 服务已在运行")
        return True

    cmd = ["uv", "run", "main.py", "api"]
    process = subprocess.Popen(
        cmd,
        cwd=os.path.expanduser("~/XHS-Downloader"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 保存 PID
    with open(API_PID_FILE, "w") as f:
        f.write(str(process.pid))

    # 等待服务启动
    for _ in range(10):
        time.sleep(1)
        if check_api_status():
            print("API 服务启动成功")
            return True

    print("API 服务启动失败")
    return False

def stop_api():
    """停止 API 服务"""
    if not os.path.exists(API_PID_FILE):
        print("未找到 API 进程")
        return

    with open(API_PID_FILE, "r") as f:
        pid = int(f.read().strip())

    try:
        os.kill(pid, 15)  # SIGTERM
        os.remove(API_PID_FILE)
        print("API 服务已停止")
    except ProcessLookupError:
        print("API 进程不存在")
        os.remove(API_PID_FILE)
```

### 2. 浏览器自动化提取链接

```python
# scripts/download_helper.py

from playwright.sync_api import sync_playwright
import time
import json

def extract_user_posts(user_url: str, output_file: str):
    """使用浏览器自动化提取博主作品链接"""

    with sync_playwright() as p:
        # 使用 OpenClaw Browser Agent 的 Chrome Profile
        browser = p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.new_page()

        # 访问博主主页
        page.goto(user_url)
        time.sleep(2)

        # 自动滚动加载所有笔记
        last_height = 0
        while True:
            # 滚动到底部
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(2)

            # 检查是否还有新内容
            new_height = page.evaluate("document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # 提取所有作品链接
        links = page.evaluate("""
            () => {
                const items = document.querySelectorAll('a[href*="/explore/"]');
                return Array.from(items).map(a => a.href);
            }
        """)

        # 去重
        links = list(set(links))

        # 保存到文件
        with open(output_file, "w") as f:
            for link in links:
                f.write(link + "\n")

        print(f"提取了 {len(links)} 个作品链接")
        print(f"保存到: {output_file}")

        page.close()
```

### 3. 批量下载

```python
# scripts/download_helper.py

import requests
import concurrent.futures
from typing import List

def download_single(url: str) -> dict:
    """下载单个作品"""
    api_url = f"{API_URL}/xhs/detail"
    payload = {
        "url": url,
        "download": True
    }

    try:
        response = requests.post(api_url, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return {"url": url, "status": "success", "data": result}
    except Exception as e:
        return {"url": url, "status": "failed", "error": str(e)}

def batch_download(links_file: str, parallel: int = 3):
    """批量下载作品"""

    # 读取链接
    with open(links_file, "r") as f:
        urls = [line.strip() for line in f if line.strip()]

    print(f"共 {len(urls)} 个作品待下载")

    # 并行下载
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(download_single, url) for url in urls]

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)

            status = "✓" if result["status"] == "success" else "✗"
            print(f"[{i}/{len(urls)}] {status} {result['url']}")

    # 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    print(f"\n下载完成！")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")

    # 保存失败列表
    if failed_count > 0:
        failed_file = links_file.replace(".txt", "_failed.txt")
        with open(failed_file, "w") as f:
            for r in results:
                if r["status"] == "failed":
                    f.write(f"{r['url']}\n")
        print(f"失败列表: {failed_file}")

    return results
```

## 🚀 快速开始

### 安装依赖

```bash
cd ~/.claude/skills/xiaohongshu-skills
uv add playwright
uv run playwright install chromium
```

### 创建 download_helper.py

```bash
# 将上述代码整合到 scripts/download_helper.py
touch scripts/download_helper.py
chmod +x scripts/download_helper.py
```

### 测试

```bash
# 1. 检查 API
python scripts/download_helper.py check-api

# 2. 启动 API
python scripts/download_helper.py start-api

# 3. 下载博主作品
python scripts/download_helper.py extract-user-posts \
  --user-url "https://www.xiaohongshu.com/user/profile/USER_ID" \
  --output links.txt

python scripts/download_helper.py batch-download \
  --links-file links.txt
```

## ⚙️ 配置

### Cookie 配置（推荐）

Cookie 可以获取更高画质的视频，无需登录。

```bash
python scripts/download_helper.py setup-cookie \
  --cookie "your_cookie_here"
```

### 自定义下载目录

编辑 `~/XHS-Downloader/Volume/settings.json`：

```json
{
  "work_path": "/path/to/download",
  "folder_mode": true,
  "author_folder": true
}
```

## 🔒 约束与限制

1. **频率限制**: 下载速度不宜过快，建议并行数 ≤ 5
2. **Cookie 有效期**: Cookie 会过期，需定期更新
3. **网络稳定性**: 大批量下载建议在网络稳定时进行
4. **存储空间**: 确保有足够的磁盘空间

## 📊 输出格式

所有命令输出 JSON 格式：

```json
{
  "status": "success",
  "data": {
    "total": 100,
    "success": 95,
    "failed": 5,
    "download_dir": "~/XHS-Downloader/Volume/Download",
    "failed_urls": ["url1", "url2"]
  }
}
```

## 🐛 故障排除

### 问题 1: API 启动失败

```bash
# 检查端口占用
lsof -i :5556

# 手动启动
cd ~/XHS-Downloader
uv run main.py api
```

### 问题 2: 浏览器连接失败

```bash
# 启动 Chrome with CDP
python scripts/chrome_launcher.py
```

### 问题 3: 下载失败

```bash
# 查看日志
tail -f ~/XHS-Downloader/Volume/logs/error.log

# 配置 Cookie
python scripts/download_helper.py setup-cookie
```

## 📚 参考资料

- [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)
- [OpenClaw Browser Agent](https://github.com/openclaw/openclaw)
- [Playwright](https://playwright.dev/)
