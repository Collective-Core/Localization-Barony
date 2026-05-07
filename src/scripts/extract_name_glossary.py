import csv
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
CORE_GLOSSARY_PATH = DATA_DIR / "Glossary.Core.csv"
STRINGS_PATH = DATA_DIR / "Strings.csv"
OUTPUT_PATH = DATA_DIR / "Glossary.Names.csv"


CORE_CATEGORY_TO_NAME_TYPE = {
    "monster_name": "entity_name",
    "location_name": "place_name",
}


MANUAL_ENTRIES = {
    "Herx": {
        "nameType": "person_name",
        "preferredTranslation": "Херкс",
        "notes": "Основна форма імені для згадок поза відмінками.",
    },
    "Baron Herx": {
        "nameType": "title_name",
        "preferredTranslation": "Барон Херкс",
        "notes": "Форма з титулом для згадок у текстах і книгах.",
    },
    "Baphomet": {
        "nameType": "deity_name",
        "preferredTranslation": "Бафомет",
        "notes": "Окрема сутність, не плутати з локацією Baphomet's Domain.",
    },
    "Horace P. Fetch": {
        "nameType": "person_name",
        "preferredTranslation": "Горас П. Фетч",
        "notes": "Автор книги A Brief Survey of Goblins.",
    },
    "Harold": {
        "nameType": "person_name",
        "preferredTranslation": "Гарольд",
        "notes": "Згадується в книгах та рядках en.txt.",
    },
    "Emily": {
        "nameType": "person_name",
        "preferredTranslation": "Емілі",
        "notes": "Основна форма імені для To Emily.",
    },
    "Winny": {
        "nameType": "person_name",
        "preferredTranslation": "Вінні",
        "notes": "Основна форма імені для Winny's Report.",
    },
    "ZAP Brigade": {
        "nameType": "faction_name",
        "preferredTranslation": "Бригада ЗАП",
        "notes": "Назва групи; тримати абревіатуру ZAP узгоджено.",
    },
    "Citadel": {
        "nameType": "organization_or_place_name",
        "preferredTranslation": "Цитадель",
        "notes": "Окрема базова форма без артикля The.",
    },
    "Lich": {
        "nameType": "entity_name",
        "preferredTranslation": "Ліч",
        "notes": "Базова форма для похідних на кшталт Sightings of the Lich.",
    },
}


def normalize_visible_text(value: str) -> str:
    return (
        value.replace("\\r", " ")
        .replace("\\n", " ")
        .replace("\\t", " ")
        .replace("\\u0020", " ")
        .replace('\\"', '"')
        .replace("\\\\", "\\")
    )


def add_or_merge(entries: dict[str, dict[str, object]], row: dict[str, str]) -> None:
    term = row["term"]
    entry = entries.setdefault(
        term,
        {
            "term": term,
            "nameType": row["nameType"],
            "occurrences": 0,
            "contexts": set(),
            "sourceFiles": set(),
            "sampleLocators": [],
            "preferredTranslation": row.get("preferredTranslation", ""),
            "notes": row.get("notes", ""),
        },
    )
    entry["nameType"] = entry["nameType"] or row["nameType"]
    entry["preferredTranslation"] = entry["preferredTranslation"] or row.get("preferredTranslation", "")
    entry["notes"] = entry["notes"] or row.get("notes", "")
    entry["occurrences"] += int(row.get("occurrences", 0))
    if row.get("contexts"):
        for item in row["contexts"].split(" | "):
            if item:
                entry["contexts"].add(item)
    if row.get("sourceFiles"):
        for item in row["sourceFiles"].split(" | "):
            if item:
                entry["sourceFiles"].add(item)
    if row.get("sampleLocators"):
        for item in row["sampleLocators"].split(" | "):
            if item and item not in entry["sampleLocators"] and len(entry["sampleLocators"]) < 5:
                entry["sampleLocators"].append(item)


def build_from_core(entries: dict[str, dict[str, object]]) -> None:
    with CORE_GLOSSARY_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f, delimiter=";"):
            category = row["category"]
            if category not in CORE_CATEGORY_TO_NAME_TYPE:
                continue
            add_or_merge(
                entries,
                {
                    "term": row["term"],
                    "nameType": CORE_CATEGORY_TO_NAME_TYPE[category],
                    "occurrences": row["occurrences"],
                    "contexts": row["contexts"],
                    "sourceFiles": row["sourceFiles"],
                    "sampleLocators": row["sampleLocators"],
                    "preferredTranslation": row["preferredTranslation"],
                    "notes": f"Imported from {category}.",
                },
            )


def build_manual_entries(entries: dict[str, dict[str, object]]) -> None:
    with STRINGS_PATH.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    for term, meta in MANUAL_ENTRIES.items():
        occurrences = 0
        contexts: set[str] = set()
        source_files: set[str] = set()
        sample_locators: list[str] = []
        for row in rows:
            text = normalize_visible_text(row["sourceText"])
            if term not in text:
                continue
            occurrences += 1
            contexts.add(row["context"])
            source_files.add(row["relativeFilePath"])
            locator = f'{row["relativeFilePath"]}::{row["locator"]}'
            if locator not in sample_locators and len(sample_locators) < 5:
                sample_locators.append(locator)

        add_or_merge(
            entries,
            {
                "term": term,
                "nameType": meta["nameType"],
                "occurrences": str(occurrences),
                "contexts": " | ".join(sorted(contexts)),
                "sourceFiles": " | ".join(sorted(source_files)),
                "sampleLocators": " | ".join(sample_locators),
                "preferredTranslation": meta["preferredTranslation"],
                "notes": meta["notes"],
            },
        )


def write_output(entries: dict[str, dict[str, object]]) -> None:
    fieldnames = [
        "term",
        "nameType",
        "occurrences",
        "contexts",
        "sourceFiles",
        "sampleLocators",
        "preferredTranslation",
        "notes",
    ]
    output_rows = []
    for term, meta in sorted(entries.items(), key=lambda item: (item[1]["nameType"], item[0])):
        output_rows.append(
            {
                "term": term,
                "nameType": meta["nameType"],
                "occurrences": str(meta["occurrences"]),
                "contexts": " | ".join(sorted(meta["contexts"])),
                "sourceFiles": " | ".join(sorted(meta["sourceFiles"])),
                "sampleLocators": " | ".join(meta["sampleLocators"]),
                "preferredTranslation": meta["preferredTranslation"],
                "notes": meta["notes"],
            }
        )

    with OUTPUT_PATH.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Generated {len(output_rows)} name glossary entries at {OUTPUT_PATH}")


def main() -> None:
    entries: dict[str, dict[str, object]] = {}
    build_from_core(entries)
    build_manual_entries(entries)
    write_output(entries)


if __name__ == "__main__":
    main()
