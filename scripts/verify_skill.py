#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""校验这个技能包的结构是否完整、是否符合写作规范。

用法（在仓库根目录）：
    python scripts/verify_skill.py

检查项：
  1. SKILL.md 存在，YAML frontmatter 含 name / description，name 与目录名一致，
     description 长度不超过 1024 字符，SKILL.md 正文不超过 500 行；
  2. references/ 与 assets/prompts/ 下每个文件都以 `# 标题` 开头、前 5 行内有 `> 说明`；
  3. 提示词文件都含代码块；
  4. 技能目录内不出现禁止词（转述痕迹、他人署名、来源作品里的示例人名）；
  5. 不残留 TODO / 待补 / TBD；
  6. 所有以 references/、assets/、scripts/ 开头的行内代码路径都真实存在。

任一项失败退出码为 1。
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "ai-short-drama"
SKILL_DIR = ROOT / "skills" / SKILL_NAME
SKILL_MD = SKILL_DIR / "SKILL.md"

# 这些是「转述痕迹」检查：确保正文是自己的话，示例是自造的例子。
FORBIDDEN = [
    "原文",
    "原作者",
    "本文作者",
    "羊羊",
    "诗仙",
    "书院",
]
# 注意：不把「待补」算作残留——剪辑单里「待补生成」是正式表名。
TODO_PATTERN = re.compile(r"\bTODO\b|\bTBD\b|\bFIXME\b|【补")

XREF_PATTERN = re.compile(r"`((?:references|assets|scripts)/[^`\s]+)`")

MAX_DESCRIPTION = 1024
MAX_SKILL_LINES = 500


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def display_width(text: str) -> int:
    """按字符数计（技能规范以字符为单位，不按字节）。"""
    return len(text)


def parse_frontmatter(text: str) -> dict:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    data: dict = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line.startswith((" ", "\t")):
            continue
        if ":" in line:
            key, _, value = line.partition(":")
            data[key.strip()] = value.strip().strip("'\"")
    return data


def check(results: list, name: str, ok: bool, detail: str = "") -> None:
    results.append((bool(ok), name, detail))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    results: list = []

    # --- 1. SKILL.md ---
    if not SKILL_MD.exists():
        check(results, "SKILL.md 存在", False, str(SKILL_MD))
        report(results)
        return 1

    text = read_text(SKILL_MD)
    front = parse_frontmatter(text)
    check(results, "SKILL.md 有 YAML frontmatter", bool(front), f"keys={sorted(front)}")
    check(results, "frontmatter 含 name", bool(front.get("name")), front.get("name", ""))
    check(
        results,
        f"name 与目录名一致（{SKILL_NAME}）",
        front.get("name") == SKILL_NAME,
        front.get("name", ""),
    )
    desc = front.get("description", "")
    check(results, "frontmatter 含 description", bool(desc))
    check(
        results,
        f"description ≤ {MAX_DESCRIPTION} 字符",
        display_width(desc) <= MAX_DESCRIPTION,
        f"{display_width(desc)} 字符",
    )
    body_lines = len(text.splitlines())
    check(
        results,
        f"SKILL.md ≤ {MAX_SKILL_LINES} 行",
        body_lines <= MAX_SKILL_LINES,
        f"{body_lines} 行",
    )

    # --- 2/3. 文档与提示词结构 ---
    def check_markdown_group(folder: Path, need_codeblock: bool, label: str) -> None:
        files = sorted(folder.glob("*.md")) if folder.exists() else []
        check(results, f"{label} 目录非空", bool(files), f"{len(files)} 个文件")
        for path in files:
            lines = [ln for ln in read_text(path).splitlines()]
            non_empty = [(i, ln) for i, ln in enumerate(lines) if ln.strip()]
            head_ok = bool(non_empty) and non_empty[0][1].startswith("# ")
            intro_ok = any(
                ln.lstrip().startswith(">") for _, ln in non_empty[:5]
            )
            rel = path.relative_to(SKILL_DIR).as_posix()
            check(results, f"{rel} 以 # 标题 开头", head_ok)
            check(results, f"{rel} 前 5 行内有 > 说明", intro_ok)
            if need_codeblock:
                check(results, f"{rel} 含代码块", "```" in "\n".join(lines))

    check_markdown_group(SKILL_DIR / "references", False, "references")
    check_markdown_group(SKILL_DIR / "assets" / "prompts", True, "assets/prompts")

    # --- 4/5. 禁止词与 TODO ---
    md_files = sorted(SKILL_DIR.rglob("*.md"))
    for path in md_files:
        rel = path.relative_to(SKILL_DIR).as_posix()
        text = read_text(path)
        hits = [w for w in FORBIDDEN if w in text]
        check(results, f"{rel} 无禁止词", not hits, ",".join(hits))
        todo = TODO_PATTERN.findall(text)
        check(results, f"{rel} 无 TODO 残留", not todo, ",".join(sorted(set(todo))))

    # --- 6. 交叉引用 ---
    missing = []
    total_refs = 0
    for path in md_files:
        for ref in XREF_PATTERN.findall(read_text(path)):
            total_refs += 1
            candidates = [SKILL_DIR / ref, ROOT / ref]
            if not any(c.exists() for c in candidates):
                missing.append(f"{path.relative_to(SKILL_DIR).as_posix()} -> {ref}")
    check(
        results,
        f"交叉引用均存在（共 {total_refs} 处）",
        not missing,
        "; ".join(missing[:8]),
    )

    # --- 摘要 ---
    ref_count = len(sorted((SKILL_DIR / "references").glob("*.md")))
    prompt_count = len(sorted((SKILL_DIR / "assets" / "prompts").glob("*.md")))
    tmpl_count = len(sorted((SKILL_DIR / "assets" / "templates").glob("*")))
    total_lines = sum(len(read_text(p).splitlines()) for p in md_files)
    summary = [
        f"技能目录：{SKILL_DIR}",
        f"references {ref_count} 篇 / prompts {prompt_count} 个 / templates {tmpl_count} 个",
        f"Markdown 合计 {total_lines} 行",
        f"SKILL.md 正文 {body_lines} 行，description {display_width(desc)} 字符",
    ]

    failed = [r for r in results if not r[0]]
    for line in summary:
        print(line)
    print("-" * 60)
    for ok, name, detail in results:
        mark = "OK  " if ok else "FAIL"
        suffix = f"  ({detail})" if detail else ""
        if not ok or verbose():
            print(f"[{mark}] {name}{suffix}")
    print("-" * 60)
    print(f"通过 {len(results) - len(failed)} / {len(results)} 项")
    if failed:
        print("失败项：")
        for _, name, detail in failed:
            print(f"  - {name} {detail}")
        return 1
    print("全部通过")
    return 0


def verbose() -> bool:
    return "--verbose" in sys.argv or "-v" in sys.argv


def report(results: list) -> None:
    for ok, name, detail in results:
        print(f"[{'OK  ' if ok else 'FAIL'}] {name} {detail}")


if __name__ == "__main__":
    raise SystemExit(main())
