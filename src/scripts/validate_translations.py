import csv
import json
import re
from collections import Counter
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
STRINGS_PATH = DATA_DIR / "Strings.csv"
OUTPUT_CSV = DATA_DIR / "Validation.Report.csv"
OUTPUT_JSON = DATA_DIR / "Validation.Summary.json"

PLACEHOLDER_RE = re.compile(r"%(?:\+\.\d+f|\+\.\d*f|\+\d*d|\+d|\.?\d*f|d|s|f|%)")
BRACKETED_CONTROL_RE = re.compile(r"\[[^\]]+\]")
ESCAPE_TOKENS = ["\\n", "\\r", "\\t", "\\u0020", "\\\\"]
CONTROL_MARKERS = ["^*"]


def extract_placeholders(text: str) -> list[str]:
    return PLACEHOLDER_RE.findall(text)


def extract_bracketed_controls(text: str) -> list[str]:
    return BRACKETED_CONTROL_RE.findall(text)


def compare_multiset(left: list[str], right: list[str]) -> bool:
    return Counter(left) == Counter(right)


def add_issue(issues: list[dict[str, str]], row: dict[str, str], issue_type: str, details: str) -> None:
    issues.append(
        {
            "id": row["id"],
            "relativeFilePath": row["relativeFilePath"],
            "locator": row["locator"],
            "sourceText": row["sourceText"],
            "translatedText": row["translatedText"],
            "issueType": issue_type,
            "details": details,
        }
    )


def main() -> None:
    with STRINGS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    issues: list[dict[str, str]] = []
    translated_count = 0

    for row in rows:
        translated = row["translatedText"]
        source = row["sourceText"]
        if not translated:
            continue

        translated_count += 1

        source_placeholders = extract_placeholders(source)
        translated_placeholders = extract_placeholders(translated)
        if not compare_multiset(source_placeholders, translated_placeholders):
            add_issue(
                issues,
                row,
                "placeholder_mismatch",
                f"source={source_placeholders} translated={translated_placeholders}",
            )

        source_controls = extract_bracketed_controls(source)
        translated_controls = extract_bracketed_controls(translated)
        if len(source_controls) != len(translated_controls):
            add_issue(
                issues,
                row,
                "bracketed_control_count_mismatch",
                f"source={source_controls} translated={translated_controls}",
            )

        for token in ESCAPE_TOKENS:
            if source.count(token) != translated.count(token):
                add_issue(
                    issues,
                    row,
                    "escape_count_mismatch",
                    f"token={token} source_count={source.count(token)} translated_count={translated.count(token)}",
                )

        for marker in CONTROL_MARKERS:
            if source.count(marker) != translated.count(marker):
                add_issue(
                    issues,
                    row,
                    "control_marker_mismatch",
                    f"marker={marker} source_count={source.count(marker)} translated_count={translated.count(marker)}",
                )

        if "?" in translated and all(ch == "?" or ch.isspace() for ch in translated):
            add_issue(issues, row, "question_mark_only_translation", "Translation appears to contain only question marks.")

        if row["relativeFilePath"].startswith("data/") and ("fonts/" in source.lower() or "images/" in source.lower()):
            if source != translated:
                add_issue(issues, row, "technical_asset_modified", "Technical asset reference differs from source.")

    fieldnames = [
        "id",
        "relativeFilePath",
        "locator",
        "sourceText",
        "translatedText",
        "issueType",
        "details",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(issues)

    summary = {
        "stringsRows": len(rows),
        "translatedRows": translated_count,
        "issueCount": len(issues),
        "issueBreakdown": dict(Counter(issue["issueType"] for issue in issues)),
        "reportCsv": OUTPUT_CSV.name,
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
