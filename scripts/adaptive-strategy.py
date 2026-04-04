#!/usr/bin/env python3
"""
adaptive-strategy.py — 自适应学习策略引擎 (v5.0 Phase 5)

用法:
  python3 adaptive-strategy.py status           # 查看当前策略状态
  python3 adaptive-strategy.py run-experiment   # 运行A/B实验
  python3 adaptive-strategy.py evaluate         # 评估实验结果
  python3 adaptive-strategy.py adapt            # 自适应调整参数
  python3 adaptive-strategy.py history          # 实验历史
"""

import json
import os
import sys
import math
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = Path(os.environ.get("OPENCLAW_WORKSPACE_DIR",
    Path.home() / ".openclaw" / "workspace"))
MEMORY_DIR = WORKSPACE / "memory"
ADAPTIVE_PATH = MEMORY_DIR / "adaptive-strategy.json"

# Default configurable parameters with ranges
DEFAULT_PARAMS = {
    "decay_half_life_days": {"value": 14, "min": 7, "max": 28, "step": 1},
    "attribution_threshold": {"value": 3, "min": 2, "max": 5, "step": 1},
    "skill_quality_threshold": {"value": 6, "min": 5, "max": 8, "step": 0.5},
    "distill_batch_size": {"value": 10, "min": 5, "max": 30, "step": 5},
    "capture_sensitivity": {"value": 0.7, "min": 0.3, "max": 1.0, "step": 0.1},
}


def load_state():
    if ADAPTIVE_PATH.exists():
        with open(ADAPTIVE_PATH) as f:
            return json.load(f)
    return {
        "current_params": DEFAULT_PARAMS,
        "experiments": [],
        "results": [],
        "last_adaptation": None,
        "version": "5.0",
    }


def save_state(state):
    ADAPTIVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(ADAPTIVE_PATH, "w") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def cmd_status():
    state = load_state()
    params = state["current_params"]
    exp_count = len(state["experiments"])
    result_count = len(state["results"])

    print("=== Adaptive Strategy Status ===")
    print(f"Experiments run: {exp_count}")
    print(f"Results collected: {result_count}")
    print(f"Last adaptation: {state.get('last_adaptation', 'never')}")
    print(f"\nCurrent parameters:")
    for name, p in params.items():
        print(f"  {name}: {p['value']} (range: {p['min']}-{p['max']}, step: {p['step']})")


def cmd_run_experiment():
    """Run an A/B experiment: try a variant parameter and compare."""
    state = load_state()
    params = state["current_params"]

    # Pick parameter to experiment with (round-robin or random)
    # Simple: pick the one with least experiments
    param_names = list(params.keys())
    exp_counts = {n: 0 for n in param_names}
    for exp in state["experiments"]:
        if exp.get("param") in exp_counts:
            exp_counts[exp["param"]] += 1

    target_param = min(exp_counts, key=exp_counts.get)
    p = params[target_param]

    # Generate variant: move one step in a direction
    import random
    if random.random() > 0.5:
        variant = min(p["value"] + p["step"], p["max"])
    else:
        variant = max(p["value"] - p["step"], p["min"])

    if variant == p["value"]:
        # Already at boundary, try other direction
        variant = p["max"] if p["value"] == p["min"] else p["min"]

    experiment = {
        "id": f"exp_{len(state['experiments'])+1}",
        "param": target_param,
        "control": p["value"],
        "variant": variant,
        "started": datetime.now().isoformat(),
        "status": "running",
    }

    state["experiments"].append(experiment)
    save_state(state)

    print(f"=== Experiment {experiment['id']} Started ===")
    print(f"Parameter: {target_param}")
    print(f"Control (current): {p['value']}")
    print(f"Variant (testing): {variant}")
    print(f"\nThis experiment will be evaluated after real task data is collected.")


def cmd_evaluate():
    """Evaluate running experiments based on recent task outcomes."""
    state = load_state()
    running = [e for e in state["experiments"] if e["status"] == "running"]

    if not running:
        print("No running experiments to evaluate.")
        return

    # Check recent task data from reflect logs
    reflect_log = MEMORY_DIR / "evolution-log.json"
    if not reflect_log.exists():
        print("No evolution log found. Cannot evaluate.")
        return

    with open(reflect_log) as f:
        evo_log = json.load(f)

    # Get recent entries (last 7 days)
    cutoff = (datetime.now() - timedelta(days=7)).isoformat()
    recent = [e for e in evo_log if e.get("timestamp", "") > cutoff]

    if not recent:
        print("No recent task data.")
        return

    success_rate = len([e for e in recent if e.get("status") == "success"]) / len(recent)

    for exp in running:
        # Simple heuristic: if success rate > 60%, variant might be better
        result = {
            "experiment_id": exp["id"],
            "param": exp["param"],
            "control": exp["control"],
            "variant": exp["variant"],
            "success_rate": round(success_rate, 3),
            "recommendation": "adopt_variant" if success_rate > 0.6 else "keep_control",
            "evaluated": datetime.now().isoformat(),
        }
        state["results"].append(result)
        exp["status"] = "completed"
        print(f"Experiment {exp['id']}: success_rate={success_rate:.1%} → {result['recommendation']}")

    save_state(state)


def cmd_adapt():
    """Apply adaptive adjustments based on experiment results."""
    state = load_state()

    # Check unapplied results
    applied_ids = set()
    for exp in state["experiments"]:
        if exp.get("status") == "applied":
            applied_ids.add(exp["id"])

    new_results = [r for r in state["results"] if r["experiment_id"] not in applied_ids]

    if not new_results:
        print("No new results to adapt. Run experiments and evaluate first.")
        return

    changes = []
    for result in new_results:
        param = result["param"]
        if result["recommendation"] == "adopt_variant" and param in state["current_params"]:
            old_val = state["current_params"][param]["value"]
            new_val = result["variant"]
            state["current_params"][param]["value"] = new_val
            changes.append(f"  {param}: {old_val} → {new_val}")

            # Mark experiment as applied
            for exp in state["experiments"]:
                if exp["id"] == result["experiment_id"]:
                    exp["status"] = "applied"

    state["last_adaptation"] = datetime.now().isoformat()
    save_state(state)

    if changes:
        print(f"=== Adapted {len(changes)} parameters ===")
        for c in changes:
            print(c)
    else:
        print("No changes applied (all recommendations: keep_control)")


def cmd_history():
    """Show experiment history."""
    state = load_state()
    experiments = state["experiments"]

    if not experiments:
        print("No experiments yet.")
        return

    print("=== Experiment History ===")
    for exp in experiments:
        status_icon = {"running": "🔄", "completed": "✅", "applied": "🎯"}.get(exp["status"], "❓")
        result = next((r for r in state["results"] if r["experiment_id"] == exp["id"]), None)
        rec = f" → {result['recommendation']}" if result else ""
        print(f"{status_icon} {exp['id']}: {exp['param']} {exp['control']} vs {exp['variant']}{rec}")


COMMANDS = {
    "status": cmd_status,
    "run-experiment": cmd_run_experiment,
    "evaluate": cmd_evaluate,
    "adapt": cmd_adapt,
    "history": cmd_history,
}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print(f"Usage: {sys.argv[0]} <{'|'.join(COMMANDS.keys())}>")
        sys.exit(1)
    COMMANDS[sys.argv[1]]()
