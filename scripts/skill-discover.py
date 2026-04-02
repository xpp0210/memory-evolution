#!/usr/bin/env python3
"""
skill-discover.py — 工具自动发现（Forage启发）

当Agent遇到能力缺口时，自动搜索ClawHub/GitHub/Skill注册表，
找到合适的Skill并推荐安装。

用法：
  skill-discover.py search "关键词"          搜索可用的Skills
  skill-discover.py gap "任务描述"            从任务描述推断能力缺口并搜索
  skill-discover.py install <skill_name>      安装找到的Skill
  skill-discover.py status                    查看已发现+已安装的Skill
"""

import sys
import json
import os
import subprocess

BASE = os.path.expanduser("~/.openclaw/workspace")
DISCOVERY_FILE = os.path.join(BASE, "memory/skill-discoveries.json")
INSTALLED_SKILLS_DIR = os.path.join(BASE, "skills")

# Initialize discovery file
def load_discoveries():
    if os.path.exists(DISCOVERY_FILE):
        with open(DISCOVERY_FILE) as f:
            return json.load(f)
    return {"searches": [], "installed": [], "passed": []}

def save_discoveries(data):
    with open(DISCOVERY_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def search_clawhub(query):
    """Search ClawHub for skills"""
    results = []
    try:
        # Use openclaw skills search if available
        r = subprocess.run(
            ["openclaw", "skills", "search", query],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and r.stdout.strip():
            results.append({"source": "openclaw", "output": r.stdout.strip()[:2000]})
    except Exception:
        pass
    
    return results

def search_github(query):
    """Search GitHub for relevant tools/skills"""
    results = []
    try:
        import urllib.request
        import urllib.parse
        
        # GitHub search API
        encoded = urllib.parse.quote(f"{query} skill openclaw")
        url = f"https://api.github.com/search/repositories?q={encoded}&sort=stars&per_page=5"
        req = urllib.request.Request(url, headers={"Accept": "application/vnd.github.v3+json"})
        
        # Unset proxy for direct connection
        env_backup = {}
        for key in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "all_proxy", "ALL_PROXY"]:
            if key in os.environ:
                env_backup[key] = os.environ.pop(key)
        
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                for repo in data.get("items", [])[:5]:
                    results.append({
                        "source": "github",
                        "name": repo["full_name"],
                        "stars": repo["stargazers_count"],
                        "description": repo.get("description", "")[:200],
                        "url": repo["html_url"],
                        "language": repo.get("language", "")
                    })
        finally:
            os.environ.update(env_backup)
    except Exception as e:
        results.append({"source": "github", "error": str(e)})
    
    return results

def get_installed_skills():
    """List currently installed skills"""
    skills = set()
    
    # Workspace skills
    if os.path.exists(INSTALLED_SKILLS_DIR):
        for d in os.listdir(INSTALLED_SKILLS_DIR):
            skill_md = os.path.join(INSTALLED_SKILLS_DIR, d, "SKILL.md")
            if os.path.exists(skill_md):
                skills.add(d)
    
    # Managed skills
    managed_dir = os.path.expanduser("~/.agents/skills")
    if os.path.exists(managed_dir):
        for d in os.listdir(managed_dir):
            skill_md = os.path.join(managed_dir, d, "SKILL.md")
            if os.path.exists(skill_md):
                skills.add(d)
    
    return sorted(skills)

def infer_gaps(task_description):
    """Infer capability gaps from task description"""
    gaps = []
    
    gap_keywords = {
        "docker": ["docker", "container", "镜像", "容器"],
        "k8s": ["kubernetes", "k8s", "部署编排"],
        "database": ["数据库", "database", "sql", "migration"],
        "api-test": ["api测试", "接口测试", "postman"],
        "monitoring": ["监控", "monitoring", "alert", "告警"],
        "ci-cd": ["ci/cd", "jenkins", "github actions", "流水线"],
        "video": ["视频", "video", "录制", "screencast"],
        "audio": ["音频", "audio", "语音", "tts", "stt"],
        "image-edit": ["图片编辑", "修图", "image edit"],
        "spreadsheet": ["表格", "excel", "spreadsheet", "csv"],
        "email": ["邮件", "email", "smtp"],
        "calendar": ["日历", "calendar", "日程"],
        "translation": ["翻译", "translate", "localize"],
        "pdf": ["pdf", "文档处理"],
        "data-viz": ["数据可视化", "chart", "图表", "visualization"],
    }
    
    task_lower = task_description.lower()
    for gap, keywords in gap_keywords.items():
        for kw in keywords:
            if kw in task_lower:
                gaps.append(gap)
                break
    
    return gaps


def cmd_search(query):
    print(f"🔍 搜索: {query}")
    print("=" * 50)
    
    installed = get_installed_skills()

    # Triple Fusion: 搜索本地记忆库先
    print("\n🧠 本地记忆搜索 (Triple Fusion):")
    try:
        triple_path = os.path.join(os.path.dirname(__file__), "triple-fusion.py")
        r = subprocess.run(
            ["python3", triple_path, "search", query, "--top-k", "3"],
            capture_output=True, text=True, timeout=30
        )
        if r.stdout.strip():
            for line in r.stdout.strip().split("\n")[:10]:
                print(f"  {line}")
    except Exception as e:
        print(f"  ⚠️ Triple Fusion 不可用: {e}")

    # Search GitHub
    print("\n📂 GitHub搜索结果:")
    gh_results = search_github(query)
    for r in gh_results:
        if "error" in r:
            print(f"  ❌ 搜索失败: {r['error']}")
        else:
            print(f"  ⭐{r['stars']} {r['name']}")
            print(f"     {r['description'][:100]}")
            print(f"     {r['url']}")
    
    # Search ClawHub
    print("\n🏪 ClawHub搜索结果:")
    claw_results = search_clawhub(query)
    for r in claw_results:
        print(f"  {r['output'][:500]}")
    
    if not gh_results and not claw_results:
        print("  无结果")
    
    # Record search
    discoveries = load_discoveries()
    discoveries["searches"].append({
        "query": query,
        "github_results": len([r for r in gh_results if "error" not in r]),
        "clawhub_results": len(claw_results),
        "timestamp": __import__("datetime").datetime.now().isoformat()
    })
    save_discoveries(discoveries)
    
    print(f"\n当前已安装 {len(installed)} 个Skills")


def cmd_gap(task_description):
    print(f"🧩 能力缺口分析: {task_description[:80]}")
    print("=" * 50)
    
    gaps = infer_gaps(task_description)
    installed = get_installed_skills()
    
    if not gaps:
        print("✅ 未检测到明显能力缺口")
        return
    
    print(f"检测到 {len(gaps)} 个潜在缺口:")
    for gap in gaps:
        print(f"  🔴 {gap}")
    
    print("\n正在搜索可用工具...")
    for gap in gaps:
        print(f"\n--- 搜索: {gap} ---")
        gh_results = search_github(f"{gap} tool CLI")
        for r in gh_results[:3]:
            if "error" not in r:
                print(f"  ⭐{r['stars']} {r['name']}: {r['description'][:80]}")


def cmd_status():
    installed = get_installed_skills()
    discoveries = load_discoveries()
    
    print("📊 工具发现统计")
    print("=" * 50)
    print(f"已安装Skills: {len(installed)} 个")
    print(f"搜索历史: {len(discoveries['searches'])} 次")
    print(f"已跳过: {len(discoveries['passed'])} 个")
    
    if discoveries["searches"]:
        print(f"\n最近搜索:")
        for s in discoveries["searches"][-5:]:
            print(f"  [{s.get('timestamp','')[:10]}] {s['query']} → {s.get('github_results',0)} GitHub + {s.get('clawhub_results',0)} ClawHub")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == "search" and len(sys.argv) >= 3:
        cmd_search(" ".join(sys.argv[2:]))
    elif cmd == "gap" and len(sys.argv) >= 3:
        cmd_gap(" ".join(sys.argv[2:]))
    elif cmd == "status":
        cmd_status()
    else:
        print(__doc__)
