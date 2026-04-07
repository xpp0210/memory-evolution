#!/usr/bin/env python3
"""
skill-verify.py — Surrogate Verifier简化版
在skill安装前，用独立LLM生成测试用例验证skill质量

EvoSkills方案的核心：独立验证器避免Ground-Truth依赖和信息泄露
"""
import json
import sys
from pathlib import Path
import argparse

MEMORY_SKILLS = Path.home() / ".openclaw/workspace/memory/memory-skills.json"
SKILLS_DIR = Path.home() / ".openclaw/workspace/skills"


def load_skill(skill_path):
    """加载skill内容"""
    skill_md = Path(skill_path) / "SKILL.md"
    if not skill_md.exists():
        return None
    return skill_md.read_text(encoding="utf-8")


def generate_test_cases(skill_content, n=3):
    """
    用独立LLM为skill生成n个测试场景
    返回: [{"scenario": str, "expected": str, "difficulty": str}]
    """
    prompt = f"""你是一个AI Agent技能验证专家。为以下SKILL.md生成{n}个测试场景：

---SKILL.md---
{skill_content[:2000]}
---

要求：
- 每个场景包含：场景描述、预期行为、难度（easy/medium/hard）
- 难度分布：1个easy、1个medium、1个hard
- 输出JSON数组格式

输出JSON："""

    try:
        import subprocess
        result = subprocess.run(
            [
                "python3", "-c",
                f"""
import requests
import os
resp = requests.post(
    "https://open.bigmodel.cn/api/coding/paas/v4/chat/completions",
    headers={{
        "Authorization": f"Bearer {{os.environ.get('ZAI_API_KEY', '')}}",
        "Content-Type": "application/json"
    }},
    json={{
        "model": "glm-4.7",
        "messages": [{{"role": "user", "content": {repr(prompt)[:3000]}}}],
        "max_tokens": 800,
        "temperature": 0.3
    }},
    timeout=30
)
print(resp.json().get("choices", [{{}}])[0].get("message", {{}}).get("content", ""))
"""
            ],
            capture_output=True, text=True, timeout=40,
            env={**__import__('os').environ, "ZHIT": ""}
        )
        output = result.stdout.strip()
        # Extract JSON from output
        if "```json" in output:
            start = output.find("```json") + 7
            end = output.rfind("```")
            output = output[start:end].strip()
        elif "[" in output:
            start = output.find("[")
            end = output.rfind("]") + 1
            output = output[start:end]
        return json.loads(output)
    except Exception as e:
        return [{"scenario": f"验证失败: {e}", "expected": "N/A", "difficulty": "unknown"}]


def score_skill_quality(skill_content):
    """
    基于SKILL.md结构评估质量
    返回: (score 0-100, issues[])
    """
    score = 50  # base
    issues = []

    required_sections = ["## 触发条件", "## 执行", "## 步骤"]
    for section in required_sections:
        if section in skill_content:
            score += 10
        else:
            issues.append(f"缺少: {section}")

    # Bonus for good patterns
    if "## 反思" in skill_content or "## 自检" in skill_content:
        score += 10
    if "```" in skill_content:  # has code examples
        score += 5
    if len(skill_content) > 500:
        score += 5
    if "---" in skill_content:  # has frontmatter
        score += 5

    return min(100, score), issues


def main():
    parser = argparse.ArgumentParser(description="Surrogate Skill Verifier")
    parser.add_argument("skill", nargs="?", help="Skill目录路径（不指定则分析所有skills）")
    parser.add_argument("--n", "-n", type=int, default=3, help="生成的测试用例数")
    parser.add_argument("--json", action="store_true", help="JSON输出")
    args = parser.parse_args()

    if args.skill:
        skills = [args.skill]
    else:
        skills = [str(d) for d in SKILLS_DIR.iterdir() if d.is_dir() and (d / "SKILL.md").exists()]

    results = []
    for skill_path in skills:
        skill_name = Path(skill_path).name
        content = load_skill(skill_path)
        if not content:
            continue

        struct_score, issues = score_skill_quality(content)

        # 生成测试用例（可选，n>0时启用）
        test_cases = generate_test_cases(content, args.n) if args.n > 0 else []

        results.append({
            "skill": skill_name,
            "structural_score": struct_score,
            "issues": issues,
            "test_cases": test_cases,
            "quality": "high" if struct_score >= 80 else ("medium" if struct_score >= 60 else "low"),
        })

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    print(f"📋 Skill质量验证（{len(results)}个skills）\n")
    for r in sorted(results, key=lambda x: x["structural_score"], reverse=True):
        quality_icon = "🟢" if r["quality"] == "high" else ("🟡" if r["quality"] == "medium" else "🔴")
        print(f"{quality_icon} {r['skill']:<40} 结构分:{r['structural_score']}")
        for issue in r.get("issues", []):
            print(f"   ⚠️  {issue}")
        if r.get("test_cases"):
            print(f"   📝 {len(r['test_cases'])}个测试用例")


if __name__ == "__main__":
    main()
