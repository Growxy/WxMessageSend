#!/usr/bin/env python3
"""
GitHub 每周热门仓库推送脚本（中文版）
功能：抓取 GitHub 本周 Trending Top 20，翻译描述，通过 Server酱 推送到微信
"""

import os
import json
import urllib.request
import urllib.parse
from datetime import datetime

SCKEY = os.environ.get("SCKEY", "")

# ── 语言映射（显示更友好） ──────────────────────────────────
LANG_FLAG = {
    "Python": "🐍 Python", "JavaScript": "🌐 JavaScript",
    "TypeScript": "🔷 TypeScript", "Go": "🐹 Go",
    "Rust": "🦀 Rust", "Java": "☕ Java",
    "C++": "⚙️ C++", "C": "⚙️ C",
    "Shell": "🐚 Shell", "Jupyter Notebook": "📓 Jupyter",
    "Swift": "🍎 Swift", "Kotlin": "🟣 Kotlin",
    "Ruby": "💎 Ruby", "PHP": "🐘 PHP",
    "Dockerfile": "🐳 Docker", "HTML": "🌍 HTML",
    "CSS": "🎨 CSS", "Unknown": "❓ 未知",
}

# ── 免费翻译（使用 Google Translate 非官方接口） ────────────
def translate_to_chinese(text):
    if not text or text == "暂无描述":
        return "暂无描述"
    try:
        params = urllib.parse.urlencode({
            "client": "gtx",
            "sl": "en",
            "tl": "zh-CN",
            "dt": "t",
            "q": text[:200],
        })
        url = f"https://translate.googleapis.com/translate_a/single?{params}"
        req = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0"
        })
        with urllib.request.urlopen(req, timeout=8) as resp:
            result = json.loads(resp.read().decode())
        translated = "".join(item[0] for item in result[0] if item[0])
        return translated
    except Exception:
        return text  # 翻译失败则保留原文

# ── 抓取 GitHub 热门仓库（本周新增 star 最多）──────────────
def fetch_trending():
    from datetime import timedelta
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; GitHub-Trending-Bot/1.0)",
        "Accept": "application/vnd.github+json",
    }
    api_url = (
        f"https://api.github.com/search/repositories"
        f"?q=created:>{week_ago}&sort=stars&order=desc&per_page=20"
    )
    req = urllib.request.Request(api_url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())

    repos = []
    for item in data.get("items", [])[:20]:
        lang = item.get("language") or "Unknown"
        desc_en = item.get("description") or ""
        print(f"  翻译中：{item['full_name']}...")
        desc_zh = translate_to_chinese(desc_en) if desc_en else "暂无描述"
        repos.append({
            "rank":     len(repos) + 1,
            "name":     item["full_name"],
            "url":      item["html_url"],
            "desc_zh":  desc_zh,
            "language": LANG_FLAG.get(lang, f"💻 {lang}"),
            "stars":    item["stargazers_count"],
            "forks":    item["forks_count"],
        })
    return repos

# ── 构建漂亮的中文消息 ──────────────────────────────────────
def build_message(repos):
    today = datetime.now().strftime("%Y年%m月%d日")
    lines = [
        f"## 🔥 GitHub 本周热门 Top 20",
        f"📅 **{today}** | 数据来源：GitHub Trending\n",
        "---",
    ]
    for r in repos:
        stars = f"{r['stars']:,}"
        forks = f"{r['forks']:,}"
        lines.append(
            f"### #{r['rank']} [{r['name']}]({r['url']})\n"
            f"{r['language']} ｜ ⭐ {stars} ｜ 🍴 {forks}\n"
            f"> {r['desc_zh']}\n"
        )
    lines.append("---\n📌 每周一早9点自动推送，祝开发愉快 🚀")
    return "\n".join(lines)

# ── 通过 Server酱 发送 ──────────────────────────────────────
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
    print(f"✅ 获取并翻译完成，共 {len(repos)} 个仓库")
    content = build_message(repos)
    print("📨 正在推送到微信...")
    send_serverchan("🔥 GitHub 本周热门 Top 20", content)

if __name__ == "__main__":
    main()
