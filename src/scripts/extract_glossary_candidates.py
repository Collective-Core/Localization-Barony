from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path


def category_from_row(row: dict[str, str]) -> str | None:
    rel = row["relativeFilePath"]
    loc = row["locator"]

    if rel == "lang/item_names.json":
        if ".spell_names." in loc:
            return "spell_name"
        return "item_name"

    if rel == "lang/book_names.json":
        return "book_title"

    if rel.startswith("lang/compendium_lang/contents_") and loc.endswith(".@key"):
        return "compendium_heading"

    if rel == "data/status_effects.json" and ".name" in loc:
        return "status_effect_name"

    if rel == "data/monster_data.json" and loc.endswith(".localized_name"):
        return "monster_name"

    if rel == "data/charsheet.json" and loc.endswith(".display_name"):
        return "location_name"

    if rel == "data/race_descriptions.json" and loc.endswith(".title"):
        return "race_name"

    if rel == "data/class_descriptions.json" and (
        loc.endswith(".title") or loc.endswith(".name")
    ):
        return "class_name"

    if rel in {
        "data/skillsheet_entries.json",
        "data/skillsheet_leadership_entries.json",
    } and loc.endswith(".name"):
        return "skill_name"

    return None


def add_entry(
    glossary: dict[tuple[str, str], dict[str, object]],
    *,
    term: str,
    category: str,
    context: str,
    source_file: str,
    locator: str,
) -> None:
    key = (term, category)
    if key not in glossary:
        glossary[key] = {
            "term": term,
            "category": category,
            "occurrences": 0,
            "contexts": set(),
            "source_files": set(),
            "sample_locators": [],
        }

    entry = glossary[key]
    entry["occurrences"] = int(entry["occurrences"]) + 1
    entry["contexts"].add(context)
    entry["source_files"].add(source_file)
    locators = entry["sample_locators"]
    if locator not in locators and len(locators) < 5:
        locators.append(locator)


def load_rows(strings_csv: Path) -> list[dict[str, str]]:
    with strings_csv.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def extract_compendium_entry_keys(compendium_dir: Path) -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []
    for path in sorted(compendium_dir.glob("lang_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for key, value in data.items():
            if key == "version" or not isinstance(value, dict):
                continue
            rel = f"lang/compendium_lang/{path.name}"
            locator = f"root.{key}.@key"
            entries.append((key, rel, locator))
    return entries


def write_glossary(output_path: Path, glossary: dict[tuple[str, str], dict[str, object]]) -> None:
    fieldnames = [
        "term",
        "category",
        "occurrences",
        "contexts",
        "sourceFiles",
        "sampleLocators",
        "preferredTranslation",
        "notes",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter=";",
            quoting=csv.QUOTE_MINIMAL,
        )
        writer.writeheader()
        for entry in sorted(
            glossary.values(),
            key=lambda item: (str(item["category"]), str(item["term"]).lower()),
        ):
            writer.writerow(
                {
                    "term": entry["term"],
                    "category": entry["category"],
                    "occurrences": entry["occurrences"],
                    "contexts": " | ".join(sorted(entry["contexts"])),
                    "sourceFiles": " | ".join(sorted(entry["source_files"])),
                    "sampleLocators": " | ".join(entry["sample_locators"]),
                    "preferredTranslation": "",
                    "notes": "",
                }
            )


def main() -> None:
    src_dir = Path(__file__).resolve().parent.parent
    repo_root = src_dir.parent
    strings_csv = src_dir / "Data" / "Strings.csv"
    compendium_dir = repo_root / "Barony Ukrainian Localization" / "lang" / "compendium_lang"
    output_path = src_dir / "Data" / "Glossary.Candidates.csv"

    glossary: dict[tuple[str, str], dict[str, object]] = {}
    rows = load_rows(strings_csv)

    for row in rows:
        category = category_from_row(row)
        if not category:
            continue
        add_entry(
            glossary,
            term=row["sourceText"],
            category=category,
            context=row["context"],
            source_file=row["relativeFilePath"],
            locator=row["locator"],
        )

    for term, source_file, locator in extract_compendium_entry_keys(compendium_dir):
        add_entry(
            glossary,
            term=term,
            category="compendium_entry",
            context="UI/system text",
            source_file=source_file,
            locator=locator,
        )

    write_glossary(output_path, glossary)
    print(
        json.dumps(
            {
                "rows_in_strings": len(rows),
                "glossary_terms": len(glossary),
                "output": str(output_path),
            }
        )
    )


if __name__ == "__main__":
    main()
