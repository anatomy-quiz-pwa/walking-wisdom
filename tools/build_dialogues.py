#!/usr/bin/env python3
"""Build data/dialogues.json from the Walking Wisdom Q&A Google Sheet.

Default behavior: fetch the sheet directly as CSV and write
data/dialogues.json next to the project root.

Usage:
    python3 tools/build_dialogues.py                # fetch from Sheet
    python3 tools/build_dialogues.py path/to.csv    # use a local CSV instead

The sheet is owned by paopao (publicly viewable). If the share setting
changes and the fetch fails, download the sheet as CSV manually and pass
the path as an argument.
"""

import csv
import io
import json
import sys
import urllib.request
from pathlib import Path

SHEET_ID = "1W4PsBkx_aNPfHbcv1Xv2C-vcGT8ZWMDQbnZ7oJQayuo"
SHEET_CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

REPO_ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = REPO_ROOT / "data" / "dialogues.json"

# Sheet's "character" column value -> master id used by the game
NAME_TO_ID = {
    "Cavagna": "cavagna",
    "Lieberman": "lieberman",
    "Roberts": "roberts",
    "Studenski": "studenski",
    "Bernstein": "bernstein",
    "Perry": "perry",
}


def split_pipe(s: str) -> list[str]:
    """Split by full-width pipe (｜) used in the sheet."""
    if not s:
        return []
    return [part.strip() for part in s.split("｜") if part.strip()]


def parse_next(raw: str):
    raw = raw.strip()
    if not raw or raw.lower() == "end":
        return None
    return int(raw)


def parse_row(row: list[str]) -> dict | None:
    """Return a normalized question dict, or None for empty/header rows.

    Bernstein's block is shifted right by 1 column in the source sheet,
    so we try offset 0 first then offset 1.
    """
    for offset in (0, 1):
        try:
            qid_raw = row[offset + 0]
            if not qid_raw or not qid_raw.strip().isdigit():
                continue
            qid = int(qid_raw.strip())
            question = row[offset + 1].strip()
            options_raw = row[offset + 2].strip()
            answer = row[offset + 3].strip()
            feedback_raw = row[offset + 4].strip()
            next_correct = parse_next(row[offset + 5])
            next_wrong = parse_next(row[offset + 6])
            character = row[offset + 7].strip()
            image_url = row[offset + 8].strip()
            bio_title = row[offset + 9].strip() if len(row) > offset + 9 else ""
            bio_1 = row[offset + 10].strip() if len(row) > offset + 10 else ""
            bio_2 = row[offset + 11].strip() if len(row) > offset + 11 else ""

            if character not in NAME_TO_ID:
                continue

            options = split_pipe(options_raw)
            feedback_parts = split_pipe(feedback_raw)
            feedback_correct = feedback_parts[0] if feedback_parts else ""
            feedback_wrong = feedback_parts[1] if len(feedback_parts) > 1 else ""

            return {
                "id": qid,
                "character": character,
                "text": question,
                "options": options,
                "answer": answer,
                "feedback_correct": feedback_correct,
                "feedback_wrong": feedback_wrong,
                "next_correct": next_correct,
                "next_wrong": next_wrong,
                "image": image_url,
                "bio_title": bio_title,
                "bio_1": bio_1,
                "bio_2": bio_2,
            }
        except (IndexError, ValueError):
            continue
    return None


def load_csv_text(arg: str | None) -> str:
    if arg:
        return Path(arg).read_text(encoding="utf-8")
    print(f"Fetching {SHEET_CSV_URL}", file=sys.stderr)
    with urllib.request.urlopen(SHEET_CSV_URL) as resp:
        return resp.read().decode("utf-8")


def build(rows: list[list[str]]) -> dict[str, dict]:
    masters: dict[str, dict] = {}
    for row in rows:
        parsed = parse_row(row)
        if not parsed:
            continue
        master_id = NAME_TO_ID[parsed["character"]]
        if master_id not in masters:
            masters[master_id] = {
                "id": master_id,
                "character_name": parsed["character"],
                "bio": {
                    "title": parsed["bio_title"],
                    "lines": [
                        line for line in (parsed["bio_1"], parsed["bio_2"]) if line
                    ],
                },
                "questions": [],
            }
        else:
            bio = masters[master_id]["bio"]
            if not bio["title"] and parsed["bio_title"]:
                bio["title"] = parsed["bio_title"]
            for line in (parsed["bio_1"], parsed["bio_2"]):
                if line and line not in bio["lines"]:
                    bio["lines"].append(line)

        masters[master_id]["questions"].append(
            {
                "id": parsed["id"],
                "text": parsed["text"],
                "options": parsed["options"],
                "answer": parsed["answer"],
                "feedback_correct": parsed["feedback_correct"],
                "feedback_wrong": parsed["feedback_wrong"],
                "next_correct": parsed["next_correct"],
                "next_wrong": parsed["next_wrong"],
                "image": parsed["image"],
            }
        )

    for m in masters.values():
        m["questions"].sort(key=lambda q: q["id"])
    return masters


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    csv_text = load_csv_text(arg)
    rows = list(csv.reader(io.StringIO(csv_text)))
    masters = build(rows)

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8") as f:
        json.dump(masters, f, ensure_ascii=False, indent=2)
        f.write("\n")

    for mid, m in masters.items():
        bio_status = "OK" if m["bio"]["title"] else "MISSING"
        print(f"{mid}: {len(m['questions'])} questions, bio={bio_status}")
    print(f"Wrote {OUT_PATH.relative_to(REPO_ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
