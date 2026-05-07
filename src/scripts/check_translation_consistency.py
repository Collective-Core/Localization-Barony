import csv
import json
from collections import Counter, defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
STRINGS_PATH = DATA_DIR / "Strings.csv"
EXCEPTIONS_PATH = DATA_DIR / "Consistency.Exceptions.csv"
OUTPUT_CSV = DATA_DIR / "Consistency.Report.csv"
OUTPUT_JSON = DATA_DIR / "Consistency.Summary.json"


def load_exceptions() -> dict[str, set[str]]:
    if not EXCEPTIONS_PATH.exists():
        return {}

    with EXCEPTIONS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    result: dict[str, set[str]] = {}
    for row in rows:
        allowed = {item.strip() for item in row["allowedTranslations"].split("|") if item.strip()}
        result[row["sourceText"]] = allowed
    return result


def main() -> None:
    with STRINGS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))
    exceptions = load_exceptions()

    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        if row["translatedText"]:
            grouped[row["sourceText"]].append(row)

    issues: list[dict[str, str]] = []
    for source_text, group in grouped.items():
        translations = {row["translatedText"] for row in group}
        if len(translations) <= 1:
            continue
        if source_text in exceptions and translations.issubset(exceptions[source_text]):
            continue

        counts = Counter(row["translatedText"] for row in group)
        details = " | ".join(f"{translation} => {count}" for translation, count in counts.items())
        for row in group:
            issues.append(
                {
                    "sourceText": source_text,
                    "translatedText": row["translatedText"],
                    "occurrencesForSource": str(len(group)),
                    "distinctTranslations": str(len(translations)),
                    "relativeFilePath": row["relativeFilePath"],
                    "locator": row["locator"],
                    "details": details,
                }
            )

    fieldnames = [
        "sourceText",
        "translatedText",
        "occurrencesForSource",
        "distinctTranslations",
        "relativeFilePath",
        "locator",
        "details",
    ]
    with OUTPUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(issues)

    summary = {
        "translatedSourceGroups": sum(1 for group in grouped.values() if group),
        "inconsistentSourceGroups": len({issue["sourceText"] for issue in issues}),
        "issueRows": len(issues),
        "exceptionsFile": EXCEPTIONS_PATH.name,
        "reportCsv": OUTPUT_CSV.name,
    }
    OUTPUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
