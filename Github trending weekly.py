#!/usr/bin/env python3
"""
GitHub 每周热门仓库推送脚本
功能：抓取 GitHub 本周 Trending Top 20，通过 WxPusher 推送到微信
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ── 配置区（通过环境变量读取） ──────────────────────────────
APP_TOKEN = os.environ.get("WXPUSHER_APP_TOKEN", "")
UID       = os.environ.get("WXPUSHER_UID", "")

TRENDSHIFT_URL = "https://trendshift.io/"
GITHUB_TRENDING_URL = "https://github.com/trending?since=weekly"

# ── 抓取 Trendshift 数据 ────────────────────────────────────
def fetch_trending():
    """通过 GitHub Trending 页面获取本周热门仓库"""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHub-Trending-Bot/1.0)"
    }

    # 使用 GitHub Search API 获取本周 star 增长最多的仓库
    api_url = (
        "https://api.github.com/search/repositories"
        "?q=stars:>1000&sort=stars&order=desc&per_page=20"
    )
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    repos = []
    for item in data.get("items", [])[:20]:
        repos.append({
            "rank":        len(repos) + 1,
            "name":        item["full_name"],
            "url":         item["html_url"],
            "description": item.get("description") or "暂无描述",
            "language":    item.get("language") or "Unknown",
            "stars":       item["stargazers_count"],
            "forks":       item["forks_count"],
        })
    return repos

# ── 构建消息内容（HTML 格式） ───────────────────────────────
def build_message(repos):
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [
        f"<h2>🔥 GitHub 本周热门仓库 Top 20</h2>",
        f"<p>📅 更新时间：{today}</p>",
        "<hr/>",
    ]
    for r in repos:
        lang_tag  = f"[{r['language']}]" if r['language'] else ""
        stars_fmt = f"{r['stars']:,}"
        forks_fmt = f"{r['forks']:,}"
        lines.append(
            f"<p><b>#{r['rank']} <a href=\"{r['url']}\">{r['name']}</a></b> {lang_tag}<br/>"
            f"⭐ {stars_fmt} &nbsp; 🍴 {forks_fmt}<br/>"
            f"{r['description']}</p>"
        )
    lines.append("<hr/><p>📌 每周一自动推送，祝开发愉快！</p>")
    return "\n".join(lines)

# ── 通过 WxPusher 发送消息 ──────────────────────────────────
def send_wxpusher(content):
    if not APP_TOKEN or not UID:
        raise ValueError("❌ 缺少 WXPUSHER_APP_TOKEN 或 WXPUSHER_UID 环境变量！")

    payload = json.dumps({
        "appToken":    APP_TOKEN,
        "content":     content,
        "summary":     "🔥 GitHub 本周热门 Top 20 来啦！",
        "contentType": 2,          # 2 = HTML
        "uids":        [UID],
        "url":         "https://github.com/trending?since=weekly",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://wxpusher.zjiecode.com/api/send/message",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())

    if result.get("success"):
        print("✅ 消息推送成功！")
    else:
        print(f"⚠️ 推送失败：{result}")

# ── 主流程 ──────────────────────────────────────────────────
def main():
    print("📡 正在抓取 GitHub Trending 数据...")
    repos   = fetch_trending()
    print(f"✅ 获取到 {len(repos)} 个仓库")

    content = build_message(repos)
    print("📨 正在推送到微信...")
    send_wxpusher(content)

if __name__ == "__main__":
    main()