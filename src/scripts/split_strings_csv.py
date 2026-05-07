from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
MASTER_CSV = DATA_DIR / "Strings.All.csv"
SOURCE_CSV = DATA_DIR / "Strings.csv"
TECHNICAL_CSV = DATA_DIR / "Strings.Technical.csv"
APPLY_SCRIPT = SCRIPT_DIR / "apply_translations_to_sources.py"


def load_apply_module():
    spec = importlib.util.spec_from_file_location(
        "apply_translations_to_sources",
        APPLY_SCRIPT,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module from {APPLY_SCRIPT}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def is_technical_row(module, raw_row: dict[str, str]) -> bool:
    row = module.TranslationRow(
        row_id=raw_row["id"],
        relative_path=raw_row["relativeFilePath"],
        file_format=raw_row["fileFormat"],
        line_number=int(raw_row["lineNumber"]),
        locator=raw_row["locator"],
        source_text=module.unescape_text(raw_row["sourceText"]),
        translated_text=module.unescape_text(raw_row["translatedText"]),
        skip_apply_translation=raw_row.get("skipApplyTranslation", "").lower()
        == "true",
    )

    if is_translatable_json_key_row(row.relative_path, row.locator):
        return False

    return (
        row.locator.endswith(".@key")
        or module.is_asset_reference(row.source_text)
        or module.is_asset_reference(row.translated_text)
        or (row.file_format == "json" and module.is_technical_locator(row.locator))
    )


def is_translatable_json_key_row(relative_path: str, locator: str) -> bool:
    return relative_path.startswith("lang/compendium_lang/contents_") and (
        locator.startswith("root.contents[")
        or locator.startswith("root.contents_alphabetical[")
    ) and locator.endswith(".@key")


def is_project_technical_row(raw_row: dict[str, str]) -> bool:
    relative_path = raw_row["relativeFilePath"]
    locator = raw_row["locator"]
    suffix = locator.split(".")[-1]

    if relative_path in {
        "data/class_hotbars.json",
        "data/compendium/events.json",
        "data/keyboard_glyph_config.json",
        "data/entity_data.json",
        "data/compendium/world.json",
        "data/monstercurve_sample.json",
        "data/gameplaymodifiers_sample.json",
        "fonts/Інфа.txt",
    }:
        return True

    if relative_path.startswith("data/custom-monsters/"):
        return True

    if relative_path.endswith("/models/creatures/crystalgolem/limbs.txt"):
        return True

    if relative_path.endswith("/models/creatures/ghoul/limbs.txt"):
        return True

    if relative_path.endswith("/models/creatures/mimic/limbs.txt"):
        return True

    if relative_path.endswith("/music/credits.txt"):
        return True

    if relative_path == "data/compendium/codex.json" and suffix.startswith("models["):
        return True

    if relative_path == "data/compendium/monsters.json" and (
        suffix in {"species", "type", "unique_npc"} or suffix.startswith("models[")
    ):
        return True

    if relative_path in {
        "data/compendium/comp_items.json",
        "data/compendium/comp_magic.json",
    } and (
        suffix.startswith("events[")
        or suffix.startswith("events_display[")
        or suffix.startswith("custom_events_display[")
    ):
        return True

    if relative_path == "data/shop_consumables.json" and suffix in {
        "status[0]",
        "appearance",
    }:
        return True

    if relative_path == "items/items.json" and suffix in {
        "item_category",
        "equip_slot",
        "effect_tags[0]",
        "effect_tags[1]",
        "school",
        "spell_type",
        "spell_name",
        "comment2",
        "comment3",
        "comment4",
        "format_tags[0]",
        "format_tags[1]",
    }:
        return True

    if relative_path == "data/scripts/sample_script.json" and (
        suffix == "type" or locator.endswith(".script")
    ):
        return True

    return False


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        rows = list(reader)
    return fieldnames, rows


def read_rows() -> tuple[list[str], list[dict[str, str]]]:
    if MASTER_CSV.exists():
        return read_csv(MASTER_CSV)

    source_fieldnames, source_rows = read_csv(SOURCE_CSV)
    technical_fieldnames, technical_rows = read_csv(TECHNICAL_CSV)

    if source_fieldnames != technical_fieldnames:
        raise RuntimeError("Strings.csv and Strings.Technical.csv have different columns")

    merged_rows = source_rows + technical_rows
    merged_rows.sort(key=lambda row: int(row["id"]))
    return source_fieldnames, merged_rows


def write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    module = load_apply_module()
    fieldnames, rows = read_rows()

    translatable_rows: list[dict[str, str]] = []
    technical_rows: list[dict[str, str]] = []

    for raw_row in rows:
        if is_technical_row(module, raw_row) or is_project_technical_row(raw_row):
            technical_rows.append(raw_row)
        else:
            translatable_rows.append(raw_row)

    write_rows(SOURCE_CSV, fieldnames, translatable_rows)
    write_rows(TECHNICAL_CSV, fieldnames, technical_rows)

    print(f"translatable_rows={len(translatable_rows)}")
    print(f"technical_rows={len(technical_rows)}")


if __name__ == "__main__":
    main()
