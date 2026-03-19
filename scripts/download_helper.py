#!/usr/bin/env python3
"""
小红书内容下载助手
集成 XHS-Downloader API 和浏览器自动化
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import requests

# 配置
API_URL = "http://127.0.0.1:5556"
XHS_DOWNLOADER_DIR = Path.home() / "XHS-Downloader"
API_PID_FILE = XHS_DOWNLOADER_DIR / ".api.pid"


class DownloadError(Exception):
    """下载错误基类"""
    pass


def check_api_status() -> bool:
    """检查 XHS-Downloader API 服务状态"""
    try:
        response = requests.get(f"{API_URL}/docs", timeout=2)
        return response.status_code == 200
    except Exception:
        return False


def start_api() -> bool:
    """启动 XHS-Downloader API 服务"""
    if check_api_status():
        print(json.dumps({"status": "running", "message": "API 服务已在运行"}))
        return True

    if not XHS_DOWNLOADER_DIR.exists():
        print(json.dumps({
            "status": "error",
            "message": f"XHS-Downloader 未安装在 {XHS_DOWNLOADER_DIR}"
        }))
        return False

    cmd = ["uv", "run", "main.py", "api"]
    process = subprocess.Popen(
        cmd,
        cwd=XHS_DOWNLOADER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True
    )

    # 保存 PID
    API_PID_FILE.write_text(str(process.pid))

    # 等待服务启动
    for i in range(15):
        time.sleep(1)
        if check_api_status():
            print(json.dumps({
                "status": "success",
                "message": "API 服务启动成功",
                "pid": process.pid
            }))
            return True

    print(json.dumps({"status": "error", "message": "API 服务启动超时"}))
    return False


def stop_api() -> None:
    """停止 XHS-Downloader API 服务"""
    if not API_PID_FILE.exists():
        print(json.dumps({"status": "info", "message": "未找到 API 进程"}))
        return

    pid = int(API_PID_FILE.read_text().strip())

    try:
        os.kill(pid, 15)  # SIGTERM
        API_PID_FILE.unlink()
        print(json.dumps({"status": "success", "message": "API 服务已停止"}))
    except ProcessLookupError:
        print(json.dumps({"status": "info", "message": "API 进程不存在"}))
        if API_PID_FILE.exists():
            API_PID_FILE.unlink()


def extract_user_posts(user_url: str, output_file: str) -> None:
    """
    使用浏览器自动化提取博主作品链接
    需要 Chrome CDP 运行在 localhost:9222
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(json.dumps({
            "status": "error",
            "message": "请先安装 playwright: uv add playwright && uv run playwright install chromium"
        }))
        sys.exit(1)

    with sync_playwright() as p:
        try:
            # 连接到 Chrome CDP
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
            context = browser.contexts[0]
            page = context.new_page()

            # 访问博主主页
            page.goto(user_url, wait_until="networkidle")
            time.sleep(3)

            # 自动滚动加载所有笔记
            last_height = 0
            scroll_count = 0
            max_scrolls = 50  # 最多滚动 50 次

            while scroll_count < max_scrolls:
                # 滚动到底部
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(2)

                # 检查是否还有新内容
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                scroll_count += 1

            # 提取所有作品链接
            links = page.evaluate("""
                () => {
                    const items = document.querySelectorAll('a[href*="/explore/"]');
                    return Array.from(items).map(a => a.href);
                }
            """)

            # 去重并过滤
            links = list(set(link for link in links if "/explore/" in link))

            # 保存到文件
            output_path = Path(output_file)
            output_path.write_text("\n".join(links))

            print(json.dumps({
                "status": "success",
                "data": {
                    "total": len(links),
                    "output_file": str(output_path.absolute()),
                    "links": links[:10]  # 只显示前 10 个
                }
            }, ensure_ascii=False))

            page.close()

        except Exception as e:
            print(json.dumps({
                "status": "error",
                "message": f"提取链接失败: {str(e)}"
            }))
            sys.exit(1)


def download_single(url: str) -> dict[str, Any]:
    """下载单个作品"""
    api_url = f"{API_URL}/xhs/detail"
    payload = {"url": url, "download": True}

    try:
        response = requests.post(api_url, json=payload, timeout=120)
        response.raise_for_status()
        result = response.json()
        return {"url": url, "status": "success", "data": result}
    except Exception as e:
        return {"url": url, "status": "failed", "error": str(e)}


def batch_download(links_file: str, parallel: int = 3) -> None:
    """批量下载作品"""
    import concurrent.futures

    # 读取链接
    links_path = Path(links_file)
    if not links_path.exists():
        print(json.dumps({"status": "error", "message": f"文件不存在: {links_file}"}))
        sys.exit(1)

    urls = [line.strip() for line in links_path.read_text().splitlines() if line.strip()]

    if not urls:
        print(json.dumps({"status": "error", "message": "链接文件为空"}))
        sys.exit(1)

    # 确保 API 运行
    if not check_api_status():
        print(json.dumps({"status": "error", "message": "API 服务未运行，请先启动"}))
        sys.exit(1)

    # 并行下载
    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = {executor.submit(download_single, url): url for url in urls}

        for i, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)

            # 实时输出进度
            status_icon = "✓" if result["status"] == "success" else "✗"
            progress = {"progress": f"{i}/{len(urls)}", "status": status_icon, "url": result["url"]}
            print(json.dumps(progress, ensure_ascii=False), file=sys.stderr)

            time.sleep(0.5)  # 避免请求过快

    # 统计结果
    success_count = sum(1 for r in results if r["status"] == "success")
    failed_count = len(results) - success_count

    # 保存失败列表
    failed_urls = [r["url"] for r in results if r["status"] == "failed"]
    failed_file = None
    if failed_urls:
        failed_file = str(links_path.with_stem(f"{links_path.stem}_failed"))
        Path(failed_file).write_text("\n".join(failed_urls))

    print(json.dumps({
        "status": "success",
        "data": {
            "total": len(urls),
            "success": success_count,
            "failed": failed_count,
            "download_dir": str(XHS_DOWNLOADER_DIR / "Volume" / "Download"),
            "failed_file": failed_file
        }
    }, ensure_ascii=False))


def setup_cookie(cookie: str) -> None:
    """配置 Cookie"""
    settings_file = XHS_DOWNLOADER_DIR / "Volume" / "settings.json"

    if not settings_file.exists():
        print(json.dumps({"status": "error", "message": "配置文件不存在"}))
        sys.exit(1)

    settings = json.loads(settings_file.read_text())
    settings["cookie"] = cookie

    settings_file.write_text(json.dumps(settings, ensure_ascii=False, indent=2))

    print(json.dumps({"status": "success", "message": "Cookie 配置成功"}))


def main() -> None:
    parser = argparse.ArgumentParser(description="小红书内容下载助手")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # check-api
    subparsers.add_parser("check-api", help="检查 API 状态")

    # start-api
    subparsers.add_parser("start-api", help="启动 API 服务")

    # stop-api
    subparsers.add_parser("stop-api", help="停止 API 服务")

    # extract-user-posts
    extract_parser = subparsers.add_parser("extract-user-posts", help="提取博主作品链接")
    extract_parser.add_argument("--user-url", required=True, help="博主主页链接")
    extract_parser.add_argument("--output", required=True, help="输出文件路径")

    # batch-download
    batch_parser = subparsers.add_parser("batch-download", help="批量下载")
    batch_parser.add_argument("--links-file", required=True, help="链接文件路径")
    batch_parser.add_argument("--parallel", type=int, default=3, help="并行数")

    # setup-cookie
    cookie_parser = subparsers.add_parser("setup-cookie", help="配置 Cookie")
    cookie_parser.add_argument("--cookie", required=True, help="Cookie 字符串")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "check-api":
            status = check_api_status()
            print(json.dumps({"status": "running" if status else "stopped"}))

        elif args.command == "start-api":
            start_api()

        elif args.command == "stop-api":
            stop_api()

        elif args.command == "extract-user-posts":
            extract_user_posts(args.user_url, args.output)

        elif args.command == "batch-download":
            batch_download(args.links_file, args.parallel)

        elif args.command == "setup-cookie":
            setup_cookie(args.cookie)

    except KeyboardInterrupt:
        print(json.dumps({"status": "interrupted", "message": "用户中断"}))
        sys.exit(130)
    except Exception as e:
        print(json.dumps({"status": "error", "message": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
