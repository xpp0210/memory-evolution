#!/usr/bin/env python3
"""
LLM 工具模块 - memory-evolution v5.0

统一的 LLM 调用接口，支持 OpenAI 兼容 API（zai/glm-5.1）。

Usage:
    from llm_utils import call_llm, call_llm_json
    result = call_llm("分析这个任务...", system="你是反思引擎")
    parsed = call_llm_json("返回JSON格式...", system="你是技能进化引擎")
"""

import os
import json
import requests
from pathlib import Path
from typing import Optional, Dict, Any

# 从 openclaw.json 读取配置
def _load_config():
    config_path = Path.home() / ".openclaw/openclaw.json"
    try:
        with open(config_path) as f:
            cfg = json.load(f)

        # 从 providers 获取 baseUrl
        providers = cfg.get("models", {}).get("providers", {})
        zai = providers.get("zai", {})
        base_url = zai.get("baseUrl", "https://open.bigmodel.cn/api/coding/paas/v4")

        # API key: 优先从 MemOS summarizer 配置获取（智谱 key）
        api_key = ""
        try:
            memos_cfg = cfg["plugins"]["entries"]["memos-local-openclaw-plugin"]["config"]
            api_key = memos_cfg.get("summarizer", {}).get("apiKey", "")
        except (KeyError, TypeError):
            pass

        # fallback: 环境变量
        if not api_key:
            api_key = os.environ.get("ZAI_API_KEY", "")

        return {
            "baseUrl": base_url,
            "apiKey": api_key,
            "model": "glm-4.7-flash"  # 用 flash 模型，快速且便宜
        }
    except Exception:
        return {
            "baseUrl": "https://open.bigmodel.cn/api/coding/paas/v4",
            "apiKey": os.environ.get("ZAI_API_KEY", ""),
            "model": "glm-4.7-flash"
        }

CONFIG = _load_config()


def call_llm(
    prompt: str,
    system: str = "你是安宝的记忆进化引擎，专注于AI Agent的自我反思和技能进化。",
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 3000,
    timeout: int = 60
) -> Optional[str]:
    """
    调用 LLM，返回文本响应

    Args:
        prompt: 用户提示
        system: 系统提示
        model: 模型名（默认 glm-5.1）
        temperature: 温度（0-1）
        max_tokens: 最大输出 token
        timeout: 超时秒数

    Returns:
        LLM 响应文本，失败返回 None
    """
    if not CONFIG["apiKey"]:
        print("❌ ZAI_API_KEY 未设置", flush=True)
        return None

    try:
        resp = requests.post(
            f"{CONFIG['baseUrl']}/chat/completions",
            headers={
                "Authorization": f"Bearer {CONFIG['apiKey']}",
                "Content-Type": "application/json"
            },
            json={
                "model": model or CONFIG["model"],
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens
            },
            timeout=timeout
        )
        resp.raise_for_status()
        data = resp.json()
        message = data["choices"][0]["message"]
        # reasoning 模型：content 可能为空，实际输出在 reasoning_content
        content = message.get("content", "") or ""
        if not content.strip():
            reasoning = message.get("reasoning_content", "") or ""
            # 从 reasoning 中提取 JSON 或最终答案
            if reasoning.strip():
                content = reasoning
        return content
    except Exception as e:
        print(f"❌ LLM 调用失败: {e}", flush=True)
        return None


def call_llm_json(
    prompt: str,
    system: str = "你是安宝的记忆进化引擎。始终返回合法JSON。",
    model: Optional[str] = None,
    temperature: float = 0.2,
    max_tokens: int = 3000,
    timeout: int = 60
) -> Optional[Dict[str, Any]]:
    """
    调用 LLM 并解析 JSON 响应

    Args:
        同 call_llm

    Returns:
        解析后的 dict，失败返回 None
    """
    text = call_llm(prompt, system, model, temperature, max_tokens, timeout)
    if not text:
        return None

    # 尝试提取 JSON（可能被 markdown 包裹）
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1])

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 尝试提取 JSON 块
        import re
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        print(f"❌ JSON 解析失败: {text[:200]}", flush=True)
        return None


def extract_json_or_text(text: str) -> Any:
    """从 LLM 输出中提取 JSON 或返回原始文本"""
    if not text:
        return None
    import re
    match = re.search(r'\{[\s\S]*\}', text.strip())
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return text
