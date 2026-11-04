#!/usr/bin/env python3
"""Read-only storage report for macOS: apps (bundle + data + hidden files) and ~/Documents.

Nothing here writes or deletes. Prints a Markdown report to stdout.
"""
import plistlib
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HOME = Path.home()
LIB = HOME / "Library"

# Folders where apps keep data, named after the app or its bundle id.
LIB_DIRS = [
    "Application Support",
    "Caches",
    "Containers",
    "Group Containers",
    "Preferences",
    "Logs",
    "HTTPStorages",
    "WebKit",
    "Saved Application State",
    "Application Scripts",
]

# Data that can't be matched by app name or bundle id. Paths are relative to home.
KNOWN_PATHS = {
    "Claude": [".claude", ".claude.json", ".local/share/claude"],
    "Visual Studio Code": [
        ".vscode",
        ".vscode-shared",
        "Library/Application Support/Code",
        "Library/Caches/vscode-cpptools",
    ],
    "Google Chrome": [
        "Library/Application Support/Google/Chrome",
        "Library/Application Support/Google/GoogleUpdater",
        "Library/Caches/Google/Chrome",
    ],
}

MIN_OTHER_KB = 100 * 1024
TOP_DOCS_SUB = 3


def measure(path):
    """Return (size_kb, blocked). blocked means macOS denied part of the folder."""
    run = subprocess.run(
        ["du", "-sk", str(path)], capture_output=True, text=True, errors="replace"
    )
    size = int(run.stdout.split()[0]) if run.stdout.strip() else 0
    return size, "Operation not permitted" in run.stderr


def human(kb):
    if kb >= 1024 * 1024:
        return f"{kb / 1024 / 1024:.1f} GB"
    if kb >= 1024:
        return f"{kb / 1024:.0f} MB"
    return f"{kb} KB"


def app_bundle_id(app):
    try:
        with open(app / "Contents" / "Info.plist", "rb") as f:
            return plistlib.load(f).get("CFBundleIdentifier", "")
    except (OSError, plistlib.InvalidFileException, ValueError):
        return ""


def list_dir(path):
    try:
        return list(path.iterdir())
    except OSError:
        return []


def matches(entry, name, bundle_id):
    entry = entry.lower()
    if entry == name.lower():
        return True
    if not bundle_id:
        return False
    bundle_id = bundle_id.lower()
    # Group Containers prefix the id with a team id: VUTU7AKEUR.jp.naver.line.mac
    return (
        entry == bundle_id
        or entry.startswith(bundle_id + ".")
        or entry.endswith("." + bundle_id)
        or ("." + bundle_id + ".") in entry
    )


def outside_owned(path, owned):
    """Yield path, or its children when part of it already belongs to an app."""
    if not any(path in p.parents for p in owned):
        yield path
        return
    for child in list_dir(path):
        if child not in owned:
            yield from outside_owned(child, owned)


def collect_apps():
    apps = []
    for root in (Path("/Applications"), HOME / "Applications"):
        apps += [p for p in list_dir(root) if p.suffix == ".app"]
    return sorted(apps)


def build_report():
    apps = collect_apps()
    info = [(app, app.stem, app_bundle_id(app)) for app in apps]

    # Every path belongs to one owner, so nothing is counted twice.
    owners = {}
    for app, name, _ in info:
        owners[app] = name
        for rel in KNOWN_PATHS.get(name, []):
            path = HOME / rel
            if path.exists():
                owners[path] = name

    candidates = []
    for folder in LIB_DIRS:
        for entry in list_dir(LIB / folder):
            if entry in owners:
                continue
            owner = next(
                (n for _, n, b in info if matches(entry.name, n, b)), None
            )
            if owner:
                owners[entry] = owner
            else:
                candidates.append(entry)

    candidates += [
        p
        for p in list_dir(HOME)
        if p.name.startswith(".")
        and p not in owners
        and p.is_dir()
        and p.name != ".Trash"
    ]
    unmatched = [p for c in candidates for p in outside_owned(c, owners)]

    with ThreadPoolExecutor(max_workers=8) as pool:
        owned_paths = list(owners)
        sizes = dict(zip(owned_paths, pool.map(measure, owned_paths)))
        other = list(zip(unmatched, pool.map(measure, unmatched)))

    totals = {name: {"total": 0, "bundle": 0, "blocked": [], "parts": []} for _, name, _ in info}
    for path, (kb, blocked) in sizes.items():
        row = totals[owners[path]]
        row["total"] += kb
        if path.suffix == ".app" and path.stem == owners[path]:
            row["bundle"] += kb
        else:
            row["parts"].append((kb, path))
        if blocked:
            row["blocked"].append(path)

    return totals, other


def short(path):
    try:
        return "~/" + str(path.relative_to(HOME))
    except ValueError:
        return str(path)


def print_apps(totals):
    print("## Application (ตัวแอป + data + ไฟล์ซ่อน)\n")
    print("| # | แอป | รวม | ตัวแอป | data ก้อนใหญ่สุด | ครบไหม |")
    print("|---|---|---|---|---|---|")
    rows = sorted(totals.items(), key=lambda r: -r[1]["total"])
    rows = [r for r in rows if r[1]["total"] >= 1024 or r[1]["blocked"]]
    for i, (name, row) in enumerate(rows, 1):
        parts = sorted(row["parts"], key=lambda p: -p[0])
        biggest = (
            f"`{short(parts[0][1])}` {human(parts[0][0])}"
            if parts and parts[0][0] >= 1024
            else "-"
        )
        complete = "วัดได้ไม่ครบ" if row["blocked"] else "ครบ"
        prefix = "≥" if row["blocked"] else ""
        print(
            f"| {i} | {name} | {prefix}{human(row['total'])} | {human(row['bundle'])} | {biggest} | {complete} |"
        )
    print()

    blocked = [(name, row["blocked"]) for name, row in rows if row["blocked"]]
    if blocked:
        print("**macOS ไม่ให้อ่านบางโฟลเดอร์ ตัวเลขของแอปเหล่านี้จึงอาจต่ำกว่าจริง:**")
        for name, paths in blocked:
            print(f"- {name}: {len(paths)} โฟลเดอร์ เช่น `{short(paths[0])}`")
        print()


def print_other(other):
    rows = sorted(
        ((p, kb) for p, (kb, _) in other if kb >= MIN_OTHER_KB), key=lambda r: -r[1]
    )
    if not rows:
        return
    print("## ไม่ได้จับคู่กับแอปใน Applications (เกิน 100 MB)\n")
    print("| โฟลเดอร์ | ขนาด |")
    print("|---|---|")
    for path, kb in rows[:10]:
        print(f"| `{short(path)}` | {human(kb)} |")
    print()


def print_documents():
    docs = HOME / "Documents"
    total, blocked = measure(docs)
    print(f"## Documents (รวม {human(total)})\n")
    if blocked and total == 0:
        print("macOS ไม่ให้อ่าน `~/Documents` จึงวัดไม่ได้\n")
        return
    entries = list_dir(docs)
    with ThreadPoolExecutor(max_workers=8) as pool:
        rows = list(zip(entries, pool.map(measure, entries)))
    rows.sort(key=lambda r: -r[1][0])

    print("| รายการ | ประเภท | ขนาด |")
    print("|---|---|---|")
    for path, (kb, _) in rows:
        if path.name in (".DS_Store", ".localized"):
            continue
        kind = "โฟลเดอร์" if path.is_dir() else "ไฟล์"
        print(f"| {path.name} | {kind} | {human(kb)} |")
    print()

    folders = [p for p, _ in rows if p.is_dir()]
    if folders:
        top = folders[0]
        subs = list_dir(top)
        with ThreadPoolExecutor(max_workers=8) as pool:
            sub_rows = list(zip(subs, pool.map(measure, subs)))
        sub_rows = [r for r in sub_rows if r[0].is_dir()]
        sub_rows.sort(key=lambda r: -r[1][0])
        if sub_rows:
            print(f"**ข้างใน {top.name} ที่ใหญ่สุด:**")
            for path, (kb, _) in sub_rows[:TOP_DOCS_SUB]:
                print(f"- {path.name}: {human(kb)}")
            print()


def main():
    if sys.platform != "darwin":
        sys.exit("check_storage ใช้ได้เฉพาะบน macOS")
    totals, other = build_report()
    print_apps(totals)
    print_other(other)
    print_documents()


if __name__ == "__main__":
    main()
