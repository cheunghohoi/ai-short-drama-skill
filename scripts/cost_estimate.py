#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""估算一集 AI 短剧的视频成本，并对比按秒计费的商用 API。

所有价格都是「参考值」，平台会调价；请用 --coin-price / --api-price 换成你实际看到的数字。

用法：
    python scripts/cost_estimate.py
    python scripts/cost_estimate.py --segments 50 --avg-seconds 6 --takes 3
    python scripts/cost_estimate.py --coins-per-clip 100 --coin-price 0.0018 --api-price 1.2
    python scripts/cost_estimate.py --json
"""

from __future__ import annotations

import argparse
import json
import sys

# ---- 默认参考价（2026-11 观察，仅供估算；以平台实际显示为准）----
# 单段代币以「6 秒一段」为基准，按段落时长近似线性折算（与 references/10-cost.md 的公式一致）。
DEFAULT_COIN_PRICE = 0.0018
BASE_SECONDS = 6.0
DEFAULT_TIER_COINS = {
    "economy": 100,   # 省钱档：单次采样，低分辨率
    "standard": 185,  # 精细档：单次采样 + 超分放大
    "max": 795,       # 极致档：整段二次采样
}
TIER_LABELS = {
    "economy": "省钱档（单次采样）",
    "standard": "精细档（采样 + 超分）",
    "max": "极致档（二次采样）",
}
DEFAULT_MONTHLY_FEE = 99
DEFAULT_MONTHLY_COINS = 54000
DEFAULT_API_PRICE = 1.0  # 按秒计费的商用 API，元/秒


def estimate(args) -> dict:
    total_clips = args.segments * args.takes
    total_seconds = total_clips * args.avg_seconds
    tiers = {}
    for tier, base in DEFAULT_TIER_COINS.items():
        per_clip = args.coins_per_clip or max(
            1, round(base * args.avg_seconds / BASE_SECONDS)
        )
        coins = per_clip * total_clips
        tiers[tier] = {
            "label": TIER_LABELS[tier],
            "coins_per_clip": per_clip,
            "cny_per_clip": round(per_clip * args.coin_price, 3),
            "coins_per_episode": coins,
            "cny_per_episode": round(coins * args.coin_price, 2),
        }
    api_cost = total_seconds * args.api_price
    economy = tiers["economy"]["cny_per_episode"]
    return {
        "input": {
            "segments": args.segments,
            "avg_seconds": args.avg_seconds,
            "takes": args.takes,
            "clips_total": total_clips,
            "seconds_total": total_seconds,
            "coin_price": args.coin_price,
            "api_price": args.api_price,
        },
        "tiers": tiers,
        "compare": {
            "api_cny": round(api_cost, 2),
            "ratio": round(api_cost / economy, 1) if economy else 0,
        },
        "membership": {
            "monthly_fee": DEFAULT_MONTHLY_FEE,
            "monthly_coins": DEFAULT_MONTHLY_COINS,
            "episodes_supported": int(DEFAULT_MONTHLY_COINS // tiers["economy"]["coins_per_episode"])
            if tiers["economy"]["coins_per_episode"]
            else 0,
        },
        "notices": [
            "所有价格为参考值（2026-11 观察），以平台实际显示为准。",
            f"单段代币以 {BASE_SECONDS:g} 秒为基准，按平均时长近似线性折算；"
            "实际消耗以平台扣费为准，可用 --coins-per-clip 覆盖。",
            "未计入失败重跑、超分失败、活动价与汇率变化。",
        ],
    }


def print_report(data: dict) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    inp = data["input"]
    line = "=" * 68
    print(line)
    print("一集 AI 短剧 · 视频成本估算（参考值，以平台实际显示为准）")
    print(line)
    print(
        f"输入：{inp['segments']} 段 × 平均 {inp['avg_seconds']:g} 秒 × 抽 {inp['takes']} 次"
        f" = {inp['clips_total']} 次生成 / {inp['seconds_total']:g} 秒成片素材"
    )
    print()
    print("档位 | 单段代币 | 单段元 | 整集代币 | 整集元")
    print("-" * 68)
    for tier in ("economy", "standard", "max"):
        t = data["tiers"][tier]
        print(
            f"{t['label']} | {t['coins_per_clip']} 代币 | {t['cny_per_clip']:.2f} 元"
            f" | {t['coins_per_episode']} 代币 | {t['cny_per_episode']:.2f} 元"
        )
    print()
    cmp = data["compare"]
    print(
        f"对照：按秒计费的商用 API（{inp['api_price']:g} 元/秒 × {inp['seconds_total']:g} 秒）"
        f"≈ {cmp['api_cny']:.2f} 元，约为省钱档的 {cmp['ratio']} 倍"
    )
    mem = data["membership"]
    print(
        f"会员套餐：{mem['monthly_fee']} 元/月（参考），赠 {mem['monthly_coins']} 代币"
        f" → 按省钱档可做约 {mem['episodes_supported']} 集"
    )
    print()
    for note in data["notices"]:
        print(f"- {note}")
    print(line)


def main() -> int:
    p = argparse.ArgumentParser(description="AI 短剧视频成本估算（参考值）")
    p.add_argument("--segments", type=int, default=50, help="一集素材段数，默认 50")
    p.add_argument("--avg-seconds", type=float, default=6.0, help="平均每段秒数，默认 6")
    p.add_argument("--takes", type=int, default=3, help="每段抽卡次数，默认 3")
    p.add_argument("--coins-per-clip", type=int, default=0, help="覆盖单段代币消耗（0 表示用档位默认值）")
    p.add_argument("--coin-price", type=float, default=DEFAULT_COIN_PRICE, help="1 代币折合人民币")
    p.add_argument("--api-price", type=float, default=DEFAULT_API_PRICE, help="对照 API 的元/秒")
    p.add_argument("--json", action="store_true", help="输出 JSON")
    args = p.parse_args()

    data = estimate(args)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print_report(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
