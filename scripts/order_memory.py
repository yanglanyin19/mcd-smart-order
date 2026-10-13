#!/usr/bin/env python3
"""
mcd-smart-order · 点餐记忆读写工具（纯标准库实现）

负责维护技能自带 memory/order-history.csv，支持：
  - init    创建 CSV（含表头）
  - add     追加一条点餐记录
  - history 读取历史（可按时段过滤）
  - suggest 基于时段从历史给出推荐种子（口味/人数/预算/菜品/饮品）

所有子命令向 stdout 输出 JSON，便于 agent 解析。不依赖任何第三方库，
不读取、不写入任何 MCP Token。

CSV 字段（逗号分隔，UTF-8）：
  date, time_slot, store, people, flavor, budget, dishes, drinks, amount_dinein, amount_takeout
  其中 time_slot 取值：上午 / 中午 / 下午
"""

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

# 记忆目录默认在技能根目录下的 memory/（脚本位于 <skill>/scripts/order_memory.py）
DEFAULT_MEMORY_DIR = Path(__file__).resolve().parent.parent / "memory"
CSV_NAME = "order-history.csv"
HEADER = [
    "date", "time_slot", "store", "people", "flavor", "budget",
    "dishes", "drinks", "amount_dinein", "amount_takeout",
]
VALID_SLOTS = {"上午", "中午", "下午"}


def _csv_path(memory_dir: Path) -> Path:
    return memory_dir / CSV_NAME


def _ensure_csv(memory_dir: Path) -> Path:
    memory_dir.mkdir(parents=True, exist_ok=True)
    path = _csv_path(memory_dir)
    if not path.exists():
        with path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(HEADER)
    return path


def _slot_from_hour(hour: int) -> str:
    if hour < 11:
        return "上午"
    if hour < 14:
        return "中午"
    return "下午"


def cmd_init(args) -> dict:
    path = _ensure_csv(Path(args.memory))
    return {"ok": True, "csv": str(path)}


def cmd_add(args) -> dict:
    if args.slot and args.slot not in VALID_SLOTS:
        return {"ok": False, "error": f"非法时段：{args.slot}，应为 上午/中午/下午"}
    try:
        people = int(args.people)
        budget = float(args.budget)
        dinein = float(args.dinein)
        takeout = float(args.takeout)
    except (TypeError, ValueError):
        return {"ok": False, "error": "people/budget/dinein/takeout 必须为数值"}
    row = {
        "date": args.date or "",
        "time_slot": args.slot or "",
        "store": args.store or "",
        "people": people,
        "flavor": args.flavor or "",
        "budget": budget,
        "dishes": args.dishes or "",
        "drinks": args.drinks or "",
        "amount_dinein": dinein,
        "amount_takeout": takeout,
    }
    path = _ensure_csv(Path(args.memory))
    with path.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([row[k] for k in HEADER])
    return {"ok": True, "row": row}


def _read_rows(memory_dir: Path) -> list:
    path = _csv_path(memory_dir)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def cmd_history(args) -> dict:
    rows = _read_rows(Path(args.memory))
    if args.slot:
        rows = [r for r in rows if r.get("time_slot") == args.slot]
    if args.limit and args.limit > 0:
        rows = rows[-args.limit:]
    return {"ok": True, "count": len(rows), "rows": rows}


def cmd_suggest(args) -> dict:
    rows = [r for r in _read_rows(Path(args.memory)) if r.get("time_slot") == args.slot]
    if not rows:
        return {
            "ok": True, "slot": args.slot, "has_history": False,
            "top_flavor": "", "common_people": "", "typical_budget": "",
            "sample_dishes": "", "sample_drinks": "",
            "note": "该时段无历史，改用门店单人套餐通用轮询",
        }
    # 口味：拆分常见分隔符后取众数
    flavor_tokens = []
    for r in rows:
        for tok in str(r.get("flavor", "")).replace("、", "/").replace("，", "/").split("/"):
            tok = tok.strip()
            if tok:
                flavor_tokens.append(tok)
    top_flavor = Counter(flavor_tokens).most_common(1)[0][0] if flavor_tokens else ""

    # 人数：众数
    people_vals = [int(r["people"]) for r in rows if str(r.get("people", "")).isdigit()]
    common_people = Counter(people_vals).most_common(1)[0][0] if people_vals else ""

    # 预算：中位数
    budget_vals = [float(r["budget"]) for r in rows if str(r.get("budget", "")).replace(".", "", 1).isdigit()]
    typical_budget = sorted(budget_vals)[len(budget_vals) // 2] if budget_vals else ""

    # 近期菜品/饮品（取最近 3 条非空）
    recent = [r for r in rows if str(r.get("dishes", "")).strip()][-3:]
    sample_dishes = " / ".join(r.get("dishes", "") for r in recent)
    sample_drinks = " / ".join(r.get("drinks", "") for r in recent if str(r.get("drinks", "")).strip())

    return {
        "ok": True, "slot": args.slot, "has_history": True,
        "top_flavor": top_flavor, "common_people": common_people,
        "typical_budget": typical_budget, "sample_dishes": sample_dishes,
        "sample_drinks": sample_drinks,
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="mcd-smart-order 点餐记忆工具")
    p.add_argument("--memory", default=str(DEFAULT_MEMORY_DIR), help="记忆目录（默认 <skill>/memory）")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="创建 CSV（含表头）")

    a = sub.add_parser("add", help="追加一条记录")
    a.add_argument("--date", default="")
    a.add_argument("--slot", default="")
    a.add_argument("--store", default="")
    a.add_argument("--people", required=True)
    a.add_argument("--flavor", default="")
    a.add_argument("--budget", required=True)
    a.add_argument("--dishes", default="")
    a.add_argument("--drinks", default="")
    a.add_argument("--dinein", required=True)
    a.add_argument("--takeout", required=True)

    h = sub.add_parser("history", help="读取历史")
    h.add_argument("--slot", default="")
    h.add_argument("--limit", type=int, default=0)

    s = sub.add_parser("suggest", help="基于时段给推荐种子")
    s.add_argument("--slot", required=True, choices=sorted(VALID_SLOTS))

    return p


def main() -> int:
    args = build_parser().parse_args()
    handlers = {
        "init": cmd_init, "add": cmd_add, "history": cmd_history, "suggest": cmd_suggest,
    }
    result = handlers[args.cmd](args)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
