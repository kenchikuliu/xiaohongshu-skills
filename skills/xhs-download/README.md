# Xiaohongshu Download Skills

**小红书内容批量下载工具 - Claude Code Skills**

一套完整的小红书内容采集与下载工具，集成 XHS-Downloader 和 OpenClaw Browser Agent，支持批量下载博主作品、搜索结果采集等功能。

## ✨ 特性

- 🚀 **批量下载博主作品** - 自动提取并下载指定博主的所有笔记
- 🔍 **搜索结果采集** - 搜索关键词并批量下载结果
- 🤖 **浏览器自动化** - 使用 OpenClaw Browser Agent 自动提取链接
- 📦 **并行下载** - 支持多线程并行下载，提高效率
- 🎨 **高清视频** - 支持配置 Cookie 下载高清视频
- 📊 **JSON 输出** - 所有命令输出结构化 JSON，易于集成

## 📦 安装

### 前置要求

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (Python 包管理器)
- [Claude Code](https://claude.ai/code)
- [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader)

### 安装步骤

1. **克隆本仓库到 Claude Code skills 目录**

```bash
cd ~/.claude/skills
git clone https://github.com/YOUR_USERNAME/xiaohongshu-skills.git
cd xiaohongshu-skills
```

2. **安装依赖**

```bash
uv sync
uv add playwright
uv run playwright install chromium
```

3. **安装 XHS-Downloader**

```bash
cd ~
git clone https://github.com/JoeanAmier/XHS-Downloader.git
cd XHS-Downloader
uv sync --no-dev
```

4. **验证安装**

```bash
cd ~/.claude/skills/xiaohongshu-skills
python scripts/download_helper.py check-api
```

## 🚀 快速开始

### 场景 1：下载博主所有作品

```bash
# 1. 启动 API 服务
python scripts/download_helper.py start-api

# 2. 提取博主作品链接
python scripts/download_helper.py extract-user-posts \
  --user-url "https://www.xiaohongshu.com/user/profile/646316590000000012036570" \
  --output links.txt

# 3. 批量下载
python scripts/download_helper.py batch-download \
  --links-file links.txt \
  --parallel 3
```

### 场景 2：在 Claude Code 中使用

在 Claude Code 中直接说：

```
下载这个博主的所有笔记：https://www.xiaohongshu.com/user/profile/646316590000000012036570
```

Claude 会自动调用 `xhs-download` skill 完成任务。

## 📚 命令参考

### check-api
检查 XHS-Downloader API 服务状态

```bash
python scripts/download_helper.py check-api
```

### start-api
启动 XHS-Downloader API 服务

```bash
python scripts/download_helper.py start-api
```

### stop-api
停止 XHS-Downloader API 服务

```bash
python scripts/download_helper.py stop-api
```

### extract-user-posts
提取博主发布的作品链接

```bash
python scripts/download_helper.py extract-user-posts \
  --user-url "https://www.xiaohongshu.com/user/profile/USER_ID" \
  --output links.txt
```

**参数：**
- `--user-url`: 博主主页链接
- `--output`: 输出文件路径

### batch-download
批量下载作品

```bash
python scripts/download_helper.py batch-download \
  --links-file links.txt \
  --parallel 5
```

**参数：**
- `--links-file`: 链接文件路径（每行一个链接）
- `--parallel`: 并行下载数（默认 3，建议 ≤ 5）

### setup-cookie
配置 Cookie（用于下载高清视频）

```bash
python scripts/download_helper.py setup-cookie \
  --cookie "your_cookie_here"
```

## ⚙️ 配置

### Cookie 配置（推荐）

Cookie 可以获取更高画质的视频，无需登录账号。

**获取 Cookie：**
1. 访问 https://www.xiaohongshu.com
2. 按 F12 打开开发者工具
3. Application → Cookies → xiaohongshu.com
4. 复制所有 Cookie

**配置：**
```bash
python scripts/download_helper.py setup-cookie --cookie "your_cookie"
```

### 自定义下载目录

编辑 `~/XHS-Downloader/Volume/settings.json`：

```json
{
  "work_path": "/path/to/download",
  "folder_mode": true,
  "author_folder": true,
  "name_format": "{作者昵称}_{作品标题}_{作品ID}"
}
```

## 🏗️ 技术架构

```
用户请求
    ↓
Claude Code (xhs-download skill)
    ↓
download_helper.py
    ↓
┌─────────────────┬──────────────────────┐
│                 │                      │
OpenClaw Browser  XHS-Downloader API    │
Agent             (localhost:5556)      │
│                 │                      │
提取链接          下载文件               │
│                 │                      │
└─────────────────┴──────────────────────┘
                  ↓
            本地存储
    ~/XHS-Downloader/Volume/Download/
```

## 📖 使用场景

### 研究竞品内容
```bash
# 下载竞品博主的所有作品
python scripts/download_helper.py extract-user-posts \
  --user-url "https://www.xiaohongshu.com/user/profile/COMPETITOR_ID" \
  --output competitor_links.txt

python scripts/download_helper.py batch-download \
  --links-file competitor_links.txt
```

### 内容灵感收集
使用现有的 `xhs-explore` skill 搜索，然后下载：

```bash
# 1. 搜索笔记
python scripts/cli.py search-feeds --keyword "产品设计" --limit 50

# 2. 提取链接并下载
# (需要从搜索结果中提取链接)
```

### 备份个人内容
```bash
# 提取收藏的作品链接
python scripts/download_helper.py extract-collections \
  --output my_collections.txt

# 批量下载
python scripts/download_helper.py batch-download \
  --links-file my_collections.txt
```

## 🔒 隐私与安全

- ✅ 所有数据存储在本地
- ✅ Cookie 仅用于获取高清视频
- ✅ 不上传任何数据到第三方
- ✅ 遵守小红书服务条款
- ⚠️ 仅供个人学习研究使用
- ⚠️ 请勿用于商业用途

## 🐛 故障排除

### 问题 1：API 启动失败

```bash
# 检查端口占用
lsof -i :5556

# 手动启动
cd ~/XHS-Downloader
uv run main.py api
```

### 问题 2：浏览器连接失败

确保 Chrome CDP 运行在 localhost:9222：

```bash
# 使用 xiaohongshu-skills 的 Chrome launcher
cd ~/.claude/skills/xiaohongshu-skills
python scripts/chrome_launcher.py
```

### 问题 3：下载失败

```bash
# 查看日志
tail -f ~/XHS-Downloader/Volume/logs/error.log

# 配置 Cookie 后重试
python scripts/download_helper.py setup-cookie --cookie "..."
```

### 问题 4：视频画质低

配置 Cookie（见上方"Cookie 配置"）

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议！

### 开发环境

```bash
git clone https://github.com/YOUR_USERNAME/xiaohongshu-skills.git
cd xiaohongshu-skills
uv sync
uv run ruff check .
uv run ruff format .
uv run pytest
```

### 提交 PR

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 📄 开源协议

MIT License

## 🙏 致谢

- [XHS-Downloader](https://github.com/JoeanAmier/XHS-Downloader) - 核心下载引擎
- [OpenClaw](https://github.com/openclaw/openclaw) - 浏览器自动化框架
- [Claude Code](https://claude.ai/code) - AI 编程助手
- [Playwright](https://playwright.dev/) - 浏览器自动化库

## 📮 联系方式

- Issues: https://github.com/YOUR_USERNAME/xiaohongshu-skills/issues
- Discussions: https://github.com/YOUR_USERNAME/xiaohongshu-skills/discussions

## 🗺️ Roadmap

- [ ] 支持提取收藏/点赞内容
- [ ] 支持从搜索结果直接下载
- [ ] 支持视频转码
- [ ] 支持图片批量压缩
- [ ] 支持内容分析（AI）
- [ ] 支持导出 Markdown
- [ ] 支持定时任务
- [ ] 支持 Webhook 通知
