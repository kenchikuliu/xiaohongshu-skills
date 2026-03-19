#!/bin/bash
# 小红书下载功能测试脚本

set -e

echo "========================================="
echo "小红书下载功能测试"
echo "========================================="
echo

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试用例
TEST_USER_URL="https://www.xiaohongshu.com/user/profile/646316590000000012036570"
SCRIPT_DIR="$HOME/.claude/skills/xiaohongshu-skills/scripts"
DOWNLOAD_HELPER="$SCRIPT_DIR/download_helper.py"

# 检查脚本是否存在
if [ ! -f "$DOWNLOAD_HELPER" ]; then
    echo -e "${RED}✗ 错误: download_helper.py 不存在${NC}"
    exit 1
fi

echo -e "${GREEN}✓ 找到 download_helper.py${NC}"
echo

# 测试 1: 检查 API 状态
echo "测试 1: 检查 API 状态"
echo "-----------------------------------"
python3 "$DOWNLOAD_HELPER" check-api
echo

# 测试 2: 启动 API 服务
echo "测试 2: 启动 API 服务"
echo "-----------------------------------"
python3 "$DOWNLOAD_HELPER" start-api
echo

# 等待 API 启动
sleep 3

# 测试 3: 再次检查 API 状态
echo "测试 3: 再次检查 API 状态"
echo "-----------------------------------"
python3 "$DOWNLOAD_HELPER" check-api
echo

# 测试 4: 提取链接（需要浏览器）
echo "测试 4: 提取博主作品链接"
echo "-----------------------------------"
echo -e "${YELLOW}注意: 此测试需要 Chrome CDP 运行在 localhost:9222${NC}"
echo -e "${YELLOW}如果失败，请先运行: python scripts/chrome_launcher.py${NC}"
echo

read -p "是否继续测试提取链接功能？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 "$DOWNLOAD_HELPER" extract-user-posts \
        --user-url "$TEST_USER_URL" \
        --output "/tmp/xhs_test_links.txt" || echo -e "${RED}✗ 提取链接失败（可能需要启动浏览器）${NC}"

    if [ -f "/tmp/xhs_test_links.txt" ]; then
        echo -e "${GREEN}✓ 链接提取成功${NC}"
        echo "前 5 个链接："
        head -5 "/tmp/xhs_test_links.txt"
    fi
fi
echo

# 测试 5: 批量下载（仅测试 1 个链接）
echo "测试 5: 批量下载测试"
echo "-----------------------------------"
if [ -f "/tmp/xhs_test_links.txt" ]; then
    # 只取第一个链接测试
    head -1 "/tmp/xhs_test_links.txt" > "/tmp/xhs_test_single.txt"

    read -p "是否测试下载单个作品？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        python3 "$DOWNLOAD_HELPER" batch-download \
            --links-file "/tmp/xhs_test_single.txt" \
            --parallel 1
        echo -e "${GREEN}✓ 下载测试完成${NC}"
    fi
else
    echo -e "${YELLOW}跳过下载测试（未提取链接）${NC}"
fi
echo

# 测试 6: 停止 API 服务
echo "测试 6: 停止 API 服务"
echo "-----------------------------------"
read -p "是否停止 API 服务？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 "$DOWNLOAD_HELPER" stop-api
fi
echo

echo "========================================="
echo "测试完成！"
echo "========================================="
echo
echo "下载的文件位于: ~/XHS-Downloader/Volume/Download/"
echo
echo "清理测试文件："
echo "  rm /tmp/xhs_test_*.txt"
