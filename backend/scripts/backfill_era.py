"""Backfill `figures.era` and `figures.period` from Wikidata.

Figure names in this dataset are Wikipedia article titles, so each one resolves
to a Wikidata Q-id, and P569 gives the date of birth. That is authoritative and
free - no LLM involved, nothing to hallucinate.

Period buckets follow the project's historiography, not the old hardcoded 1800:

    ancient       < 476                      fall of the Western Roman Empire
    medieval      476 - 1499
    early_modern  1500 - 1916                Age of Discovery -> October Revolution
    modern        1917 - 1944                October Revolution -> end of WWII
    contemporary  1945 -                     Cold War to the present

Usage:
    python scripts/backfill_era.py              # dry run, prints a report
    python scripts/backfill_era.py --apply      # writes to the database
    python scripts/backfill_era.py --refresh    # ignore the cache, refetch
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "historical.db"
CACHE_PATH = Path(__file__).resolve().parent.parent / "data" / "era_cache.json"

PROXY = "http://127.0.0.1:7897"
UA = {"User-Agent": "HistoricalPersonaSystem/1.0 (era backfill; one-off script)"}

PERIODS = [
    ("ancient", None, 476),
    ("medieval", 476, 1500),
    ("early_modern", 1500, 1917),
    ("modern", 1917, 1945),
    ("contemporary", 1945, None),
]

# Wikipedia redirects "Kautilya" to the *Arthashastra* article (the treatise),
# so a plain title lookup lands on the wrong entity. The person is Chanakya.
TITLE_ALIASES = {
    "Kautilya": "Chanakya",
}

PERIOD_ZH = {
    "ancient": "古代",
    "medieval": "中世纪",
    "early_modern": "近代",
    "modern": "现代",
    "contemporary": "当代",
}


def period_for(year: int) -> str:
    for name, low, high in PERIODS:
        if (low is None or year >= low) and (high is None or year < high):
            return name
    raise ValueError(f"no period for year {year}")


def wikidata_year(time_value: str, precision: int | None) -> int | None:
    """'+0155-00-00T00:00:00Z' -> 155, '-0550-01-01T00:00:00Z' -> -550."""
    try:
        sign = -1 if time_value.startswith("-") else 1
        year = int(time_value[1:5])
    except (ValueError, IndexError):
        return None
    if year == 0:
        return None
    if precision is not None and precision < 9:
        # century (7) / decade (8) precision: keep it, but the caller may want to know
        pass
    return sign * year


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass
    return {"titles": {}, "births": {}}


def save_cache(cache: dict) -> None:
    CACHE_PATH.write_text(json.dumps(cache, indent=1, ensure_ascii=False), encoding="utf-8")


class Client:
    def __init__(self, proxies: dict | None, delay: float = 1.0):
        self.s = requests.Session()
        self.s.headers.update(UA)
        self.s.proxies = proxies or {}
        self.delay = delay

    def get(self, url: str, params: dict, tries: int = 6) -> dict | None:
        for attempt in range(tries):
            try:
                r = self.s.get(url, params=params, timeout=45)
            except Exception as exc:  # network hiccup
                wait = self.delay * (2 ** attempt)
                print(f"    network {type(exc).__name__}, retry in {wait:.0f}s")
                time.sleep(wait)
                continue
            if r.status_code == 200:
                time.sleep(self.delay)
                return r.json()
            if r.status_code in (429, 500, 502, 503, 504):
                retry_after = r.headers.get("Retry-After", "")
                wait = float(retry_after) if retry_after.isdigit() else self.delay * (2 ** attempt)
                print(f"    HTTP {r.status_code}, retry in {wait:.0f}s")
                time.sleep(wait)
                continue
            print(f"    HTTP {r.status_code} (giving up on this batch)")
            return None
        return None


def pick_client() -> Client:
    """Prefer the local proxy (Wikipedia is unreachable directly from CN)."""
    for label, proxies in (("proxy", {"http": PROXY, "https": PROXY}), ("direct", None)):
        c = Client(proxies, delay=0.0)
        try:
            r = c.s.get("https://en.wikipedia.org/w/api.php", timeout=15, params={
                "action": "query", "titles": "Cao Cao", "format": "json"})
            if r.status_code == 200:
                print(f"network: {label} ({PROXY if proxies else 'direct'})")
                return Client(proxies, delay=1.0)
        except Exception as exc:
            print(f"network: {label} failed ({type(exc).__name__})")
    raise SystemExit("no route to Wikipedia - start your proxy first")


def resolve_titles(client: Client, names: list[str], cache: dict) -> None:
    todo = [n for n in names if n not in cache["titles"]]
    print(f"title -> Q-id: {len(names) - len(todo)} cached, {len(todo)} to fetch")
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = client.get("https://en.wikipedia.org/w/api.php", {
            "action": "query", "titles": "|".join(batch), "prop": "pageprops",
            "format": "json", "redirects": 1, "formatversion": 2})
        if not data:
            continue
        j = data.get("query", {})
        by_title = {}
        for page in j.get("pages", []):
            if "missing" in page:
                continue
            by_title[page["title"]] = page.get("pageprops", {}).get("wikibase_item")
        alias = {}
        for n in j.get("normalized", []):
            alias[n["from"]] = n["to"]
        for rd in j.get("redirects", []):
            alias[rd["from"]] = rd["to"]
        for name in batch:
            t = name
            hops = 0
            while t in alias and hops < 5:
                t = alias[t]
                hops += 1
            cache["titles"][name] = by_title.get(t) or by_title.get(alias.get(name, name))
        print(f"  {i + len(batch)}/{len(todo)}")


def fetch_births(client: Client, cache: dict) -> None:
    qids = sorted({q for q in cache["titles"].values() if q})
    todo = [q for q in qids if q not in cache["births"]]
    print(f"Q-id -> P569: {len(qids) - len(todo)} cached, {len(todo)} to fetch")
    for i in range(0, len(todo), 50):
        batch = todo[i:i + 50]
        data = client.get("https://www.wikidata.org/w/api.php", {
            "action": "wbgetentities", "ids": "|".join(batch),
            "props": "claims", "format": "json"})
        if not data:
            continue
        for qid, ent in data.get("entities", {}).items():
            entry = None
            for claim in (ent.get("claims", {}).get("P569") or []):
                try:
                    value = claim["mainsnak"]["datavalue"]["value"]
                except KeyError:
                    continue
                year = wikidata_year(value["time"], value.get("precision"))
                if year is None:
                    continue
                entry = {
                    "year": year,
                    "time": value["time"],
                    "precision": value.get("precision"),
                }
                break
            cache["births"][qid] = entry
        print(f"  {i + len(batch)}/{len(todo)}")
        save_cache(cache)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    ap.add_argument("--refresh", action="store_true", help="ignore the cache")
    args = ap.parse_args()

    if not DB_PATH.exists():
        print(f"database not found: {DB_PATH}")
        return 1

    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row

    cache = {"titles": {}, "births": {}} if args.refresh else load_cache()

    targets = con.execute(
        "SELECT id, name, era, period FROM figures WHERE era IS NULL ORDER BY id"
    ).fetchall()
    curated = con.execute(
        "SELECT id, name, era, period FROM figures WHERE era IS NOT NULL ORDER BY id"
    ).fetchall()
    print(f"era IS NULL: {len(targets)}   era known: {len(curated)}\n")

    if not targets and not curated:
        print("nothing to do")
        return 0

    names = [r["name"] for r in targets]
    if names:
        client = pick_client()
        # resolve aliases as their own titles, then copy the Q-id back
        alias_titles = [TITLE_ALIASES[n] for n in names if n in TITLE_ALIASES]
        resolve_titles(client, names + alias_titles, cache)
        for source, target in TITLE_ALIASES.items():
            qid = cache["titles"].get(target)
            if qid:
                cache["titles"][source] = qid
        save_cache(cache)
        fetch_births(client, cache)
        save_cache(cache)

    # ---- build the plan -----------------------------------------------------
    plan, unresolved, low_precision = [], [], []
    for row in targets:
        qid = cache["titles"].get(row["name"])
        entry = cache["births"].get(qid) if qid else None
        if not entry:
            unresolved.append(row["name"])
            continue
        year = entry["year"]
        if not (-3000 <= year <= 2026):
            unresolved.append(f"{row['name']} (implausible year {year})")
            continue
        if entry["precision"] is not None and entry["precision"] < 9:
            low_precision.append(f"{row['name']} ({year}, precision={entry['precision']})")
        plan.append((row["id"], year, period_for(year), row["name"], entry["precision"], qid))

    # recompute period for rows that already have a hand-curated era
    relabel = []
    for row in curated:
        want = period_for(row["era"])
        if want != row["period"]:
            relabel.append((row["id"], row["name"], row["era"], row["period"], want))

    # ---- report -------------------------------------------------------------
    print("\n" + "=" * 62)
    print(f"可写入 (era + period): {len(plan)}")
    print(f"无法解析: {len(unresolved)}")
    print(f"仅改 period 的人工标注行: {len(relabel)}")
    print("=" * 62)

    from collections import Counter
    dist = Counter(p for _, _, p, *_ in plan)
    print("\n新 period 分布（仅新写入的行）:")
    for key, _, _ in PERIODS:
        print(f"  {key:<14} {PERIOD_ZH[key]:<4} {dist.get(key, 0):>4}")

    print("\n现有 era 已知行的 period 变动:")
    if not relabel:
        print("  (无)")
    for _id, name, era, old, new in relabel:
        print(f"  #{_id:<4} {name:<24} era={era:<6} {old} -> {new}")

    if unresolved:
        print(f"\n无法解析 ({len(unresolved)}):")
        for n in unresolved:
            print(f"  - {n}")

    if low_precision:
        print(f"\n低精度日期（世纪级，误差可能上百年）: {len(low_precision)}")
        for n in low_precision[:15]:
            print(f"  ~ {n}")
        if len(low_precision) > 15:
            print(f"  ... 另有 {len(low_precision) - 15} 条")

    if not args.apply:
        print("\n[dry run] 未写入。加 --apply 执行。")
        return 0

    # ---- apply --------------------------------------------------------------
    backup_dir = DB_PATH.parent / "backup"
    backup_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = backup_dir / f"historical-{stamp}-before-era-backfill.db"
    src = sqlite3.connect(DB_PATH)
    dst = sqlite3.connect(backup)
    with dst:
        src.backup(dst)
    src.close()
    dst.close()
    print(f"\n备份: {backup}")

    changed_era = 0
    for _id, year, period, _name, _prec, _qid in plan:
        cur = con.execute(
            "UPDATE figures SET era=?, period=? WHERE id=?", (year, period, _id))
        changed_era += cur.rowcount
    changed_period = 0
    for _id, _name, _era, _old, want in relabel:
        cur = con.execute("UPDATE figures SET period=? WHERE id=?", (want, _id))
        changed_period += cur.rowcount
    con.commit()

    total = con.execute("SELECT COUNT(*) FROM figures").fetchone()[0]
    print(f"\nera/period 更新: {changed_era}")
    print(f"period 重标:     {changed_period}")
    print(f"figures 总数:    {total}")
    print("剩余 era IS NULL:",
          con.execute("SELECT COUNT(*) FROM figures WHERE era IS NULL").fetchone()[0])
    for key, _, _ in PERIODS:
        n = con.execute("SELECT COUNT(*) FROM figures WHERE period=?", (key,)).fetchone()[0]
        print(f"  {key:<14} {n}")
    n = con.execute("SELECT COUNT(*) FROM figures WHERE period='unknown'").fetchone()[0]
    print(f"  {'unknown':<14} {n}")
    print("integrity_check:", con.execute("PRAGMA integrity_check").fetchone()[0])
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
