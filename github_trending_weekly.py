#!/usr/bin/env python3
"""
GitHub 每周热门仓库推送脚本
功能：抓取 GitHub 本周 Trending Top 20，通过 Server酱 推送到微信
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

# ── 配置区（通过环境变量读取） ──────────────────────────────
SCKEY = os.environ.get("SCKEY", "")

# ── 抓取 GitHub 热门仓库 ────────────────────────────────────
def fetch_trending():
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHub-Trending-Bot/1.0)"
    }
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

# ── 构建消息内容 ────────────────────────────────────────────
def build_message(repos):
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [f"📅 更新时间：{today}\n"]
    for r in repos:
        stars_fmt = f"{r['stars']:,}"
        lines.append(
            f"**#{r['rank']} [{r['name']}]({r['url']})**\n"
            f"⭐ {stars_fmt} ｜ 💻 {r['language']}\n"
            f"{r['description']}\n"
        )
    lines.append("---\n📌 每周一自动推送，祝开发愉快！")
    return "\n".join(lines)

# ── 通过 Server酱 发送消息 ──────────────────────────────────
def send_serverchan(title, content):
    if not SCKEY:
        raise ValueError("❌ 缺少 SCKEY 环境变量！")

    payload = urllib.parse.urlencode({
        "title": title,
        "desp":  content,
    }).encode("utf-8")

    url = f"https://sctapi.ftqq.com/{SCKEY}.send"
    req = urllib.request.Request(url, data=payload, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read().decode())

    if result.get("data", {}).get("errno") == 0 or result.get("code") == 0:
        print("✅ 消息推送成功！")
    else:
        print(f"⚠️ 推送结果：{result}")

# ── 主流程 ──────────────────────────────────────────────────
def main():
    print("📡 正在抓取 GitHub Trending 数据...")
    repos = fetch_trending()
    print(f"✅ 获取到 {len(repos)} 个仓库")

    content = build_message(repos)
    print("📨 正在推送到微信...")
    send_serverchan("🔥 GitHub 本周热门 Top 20", content)

if __name__ == "__main__":
    main()
