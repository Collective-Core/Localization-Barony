import csv
from collections import defaultdict
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
STRINGS_PATH = DATA_DIR / "Strings.csv"
OUTPUT_PATH = DATA_DIR / "Glossary.Technical.csv"


def detect_asset_type(source_text: str) -> str | None:
    lower = source_text.lower()
    if (
        "images/" in lower
        or lower.startswith("#*images/")
        or lower.endswith(".png")
        or lower.endswith(".jpg")
        or lower.endswith(".jpeg")
    ):
        return "image"
    if "fonts/" in lower or ".ttf" in lower or ".otf" in lower:
        return "font"
    return None


def main() -> None:
    entries: dict[str, dict[str, object]] = defaultdict(
        lambda: {
            "assetType": "",
            "occurrences": 0,
            "contexts": set(),
            "sourceFiles": set(),
            "sampleLocators": [],
            "keepOriginal": "true",
            "notes": "",
        }
    )

    with STRINGS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    for row in rows:
        source_text = row["sourceText"]
        asset_type = detect_asset_type(source_text)
        if not asset_type:
            continue

        entry = entries[source_text]
        entry["assetType"] = asset_type
        entry["occurrences"] += 1
        entry["contexts"].add(row["context"])
        entry["sourceFiles"].add(row["relativeFilePath"])

        locator_ref = f'{row["relativeFilePath"]}::{row["locator"]}'
        if len(entry["sampleLocators"]) < 5 and locator_ref not in entry["sampleLocators"]:
            entry["sampleLocators"].append(locator_ref)

    fieldnames = [
        "term",
        "assetType",
        "occurrences",
        "contexts",
        "sourceFiles",
        "sampleLocators",
        "keepOriginal",
        "notes",
    ]

    output_rows = []
    for term, meta in sorted(entries.items(), key=lambda item: (item[1]["assetType"], item[0])):
        output_rows.append(
            {
                "term": term,
                "assetType": meta["assetType"],
                "occurrences": str(meta["occurrences"]),
                "contexts": " | ".join(sorted(meta["contexts"])),
                "sourceFiles": " | ".join(sorted(meta["sourceFiles"])),
                "sampleLocators": " | ".join(meta["sampleLocators"]),
                "keepOriginal": meta["keepOriginal"],
                "notes": meta["notes"],
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Generated {len(output_rows)} technical glossary entries at {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
