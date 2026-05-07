from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


COLUMN_NAMES = [
    "id",
    "key",
    "relativeFilePath",
    "fileFormat",
    "lineNumber",
    "locator",
    "sourceText",
    "translatedText",
    "techHash",
    "placeholders",
    "placeholderCheck",
    "translationMethod",
    "isHumanTranslation",
    "status",
    "context",
    "stringType",
]

PRINTF_PLACEHOLDER_RE = re.compile(
    r"%(?:\d+\$)?[-+#0 ]*(?:\d+)?(?:\.\d+)?[a-zA-Z]"
)
BRACKET_PLACEHOLDER_RE = re.compile(r"\[[^\[\]\r\n]+\]")
SNAKE_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9]+(?:_[A-Za-z0-9]+)+$")
NUMERIC_STRING_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")
CYRILLIC_RE = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")
NON_TRANSLATABLE_JSON_KEYS = {
    "action",
    "base_path",
    "comment",
    "conditional_attribute",
    "direction",
    "horizontal_justify",
    "id",
    "internal_name",
    "spell_id",
    "tag",
    "vertical_justify",
    "world_icon",
    "world_icon_small",
}

IGNORED_RELATIVE_PATHS = {
    "books/compiled_books.json",
}

SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
REPO_ROOT = SRC_DIR.parent
DATA_DIR = SRC_DIR / "Data"
MASTER_CSV = DATA_DIR / "Strings.All.csv"
TRANS_CSV = DATA_DIR / "Strings.csv"
TECH_CSV = DATA_DIR / "Strings.Technical.csv"
SOURCE_ROOT = REPO_ROOT / "Barony Ukrainian Localization"


def escape_text(value: str) -> str:
    if not value:
        return value

    first_non_ws = 0
    while first_non_ws < len(value) and value[first_non_ws].isspace():
        first_non_ws += 1

    last_non_ws = len(value) - 1
    while last_non_ws >= 0 and value[last_non_ws].isspace():
        last_non_ws -= 1

    def escape_char(ch: str, force_unicode_space: bool) -> str:
        if ch == "\\":
            return "\\\\"
        if ch == '"':
            return '\\"'
        if ch == "\r":
            return "\\r"
        if ch == "\n":
            return "\\n"
        if ch == "\t":
            return "\\t"
        if force_unicode_space and ch == " ":
            return "\\u0020"
        if ord(ch) < 32 or ord(ch) == 127:
            return f"\\u{ord(ch):04x}"
        return ch

    escaped: list[str] = []
    for index, ch in enumerate(value):
        at_edge = index < first_non_ws or index > last_non_ws
        escaped.append(escape_char(ch, force_unicode_space=at_edge))
    return "".join(escaped)


def compute_hash(value: str) -> str:
    return hashlib.md5(value.encode("utf-8")).hexdigest()


def extract_placeholders(value: str) -> list[str]:
    seen: set[str] = set()
    placeholders: list[str] = []
    for match in PRINTF_PLACEHOLDER_RE.finditer(value):
        token = match.group(0)
        if token not in seen:
            seen.add(token)
            placeholders.append(token)
    for match in BRACKET_PLACEHOLDER_RE.finditer(value):
        token = match.group(0)
        if token not in seen:
            seen.add(token)
            placeholders.append(token)
    return placeholders


def infer_context(relative_path: str, raw_text: str, key: str) -> str:
    first_part = Path(relative_path).parts[0].lower()
    if first_part == "books":
        base = "book/lore text"
    elif first_part == "items":
        base = "item related text"
    elif first_part == "lang":
        base = "UI/system text"
    else:
        base = "game data text"

    stripped = raw_text.lstrip()
    if stripped.startswith("#") or key.lower() == "icon_path":
        return f"{base}, technical comment"
    return base


def make_row(
    row_id: int,
    key: str,
    relative_path: str,
    file_format: str,
    line_number: int,
    locator: str,
    raw_text: str,
) -> dict[str, str]:
    return {
        "id": str(row_id),
        "key": key,
        "relativeFilePath": relative_path,
        "fileFormat": file_format,
        "lineNumber": str(line_number),
        "locator": locator,
        "sourceText": escape_text(raw_text),
        "translatedText": "",
        "techHash": compute_hash(raw_text),
        "placeholders": json.dumps(
            extract_placeholders(raw_text), ensure_ascii=False
        ),
        "placeholderCheck": "true",
        "translationMethod": "auto_extracted",
        "isHumanTranslation": "false",
        "status": "new",
        "context": infer_context(relative_path, raw_text, key),
        "stringType": "sentence",
    }


def should_extract_json_key(
    relative_path: str,
    locator: str,
    key_name: str,
    value: object,
) -> bool:
    if not isinstance(value, str):
        return False

    if relative_path.startswith("lang/compendium_lang/contents_"):
        return locator.startswith("root.contents[") or locator.startswith(
            "root.contents_alphabetical["
        )

    return False


def should_extract_json_value(
    relative_path: str,
    locator: str,
    key_name: str,
    value: str,
) -> bool:
    if value == "":
        return False

    if key_name in NON_TRANSLATABLE_JSON_KEYS or key_name.endswith("_path"):
        return False

    if key_name == "comment" or locator.endswith(".comment"):
        return False

    if relative_path.startswith("lang/compendium_lang/contents_") and (
        locator.startswith("root.contents[")
        or locator.startswith("root.contents_alphabetical[")
    ):
        return False

    if NUMERIC_STRING_RE.fullmatch(value):
        return False

    lowered = value.lower()
    if any(ext in lowered for ext in (".png", ".ttf", ".ogg", ".wav")):
        return False

    if SNAKE_IDENTIFIER_RE.fullmatch(value):
        return False

    return True


def append_json_rows(
    value: object,
    relative_path: str,
    rows: list[dict[str, str]],
    next_id: list[int],
    locator: str = "root",
    key_name: str = "value",
) -> None:
    if isinstance(value, dict):
        for child_key, child_value in value.items():
            child_locator = f"{locator}.{child_key}"
            if should_extract_json_key(
                relative_path=relative_path,
                locator=child_locator,
                key_name=child_key,
                value=child_value,
            ):
                rows.append(
                    make_row(
                        row_id=next_id[0],
                        key=child_key,
                        relative_path=relative_path,
                        file_format="json",
                        line_number=-1,
                        locator=f"{child_locator}.@key",
                        raw_text=child_key,
                    )
                )
                next_id[0] += 1
            append_json_rows(
                child_value,
                relative_path,
                rows,
                next_id,
                locator=child_locator,
                key_name=child_key,
            )
        return

    if isinstance(value, list):
        for index, child_value in enumerate(value):
            append_json_rows(
                child_value,
                relative_path,
                rows,
                next_id,
                locator=f"{locator}[{index}]",
                key_name=key_name,
            )
        return

    if isinstance(value, str):
        if should_extract_json_value(
            relative_path=relative_path,
            locator=locator,
            key_name=key_name,
            value=value,
        ):
            rows.append(
                make_row(
                    row_id=next_id[0],
                    key=key_name,
                    relative_path=relative_path,
                    file_format="json",
                    line_number=-1,
                    locator=locator,
                    raw_text=value,
                )
            )
            next_id[0] += 1


def append_txt_rows(
    file_path: Path,
    relative_path: str,
    rows: list[dict[str, str]],
    next_id: list[int],
) -> None:
    with file_path.open("r", encoding="utf-8", newline="") as handle:
        contents = handle.read()
    for line_number, line in enumerate(contents.splitlines(keepends=True), start=1):
        stripped = line.strip()
        if stripped == "" or stripped.startswith("#"):
            continue
        rows.append(
            make_row(
                row_id=next_id[0],
                key="line",
                relative_path=relative_path,
                file_format="txt",
                line_number=line_number,
                locator=f"line:{line_number}",
                raw_text=line,
            )
        )
        next_id[0] += 1


def collect_rows(source_root: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    next_id = [1]

    for file_path in sorted(source_root.rglob("*")):
        if not file_path.is_file():
            continue

        suffix = file_path.suffix.lower()
        if suffix not in {".json", ".txt"}:
            continue

        relative_path = file_path.relative_to(source_root).as_posix()
        if relative_path in IGNORED_RELATIVE_PATHS:
            continue

        if suffix == ".json":
            payload = json.loads(file_path.read_text(encoding="utf-8"))
            append_json_rows(payload, relative_path, rows, next_id)
        else:
            append_txt_rows(file_path, relative_path, rows, next_id)

    return rows


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def row_identity(row: dict[str, str]) -> tuple[str, str]:
    return row["relativeFilePath"], row["locator"]


def unescape_text(value: str) -> str:
    if not value:
        return value

    result: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char != "\\":
            result.append(char)
            index += 1
            continue

        index += 1
        if index >= len(value):
            result.append("\\")
            break

        escaped = value[index]
        if escaped == "r":
            result.append("\r")
        elif escaped == "n":
            result.append("\n")
        elif escaped == "t":
            result.append("\t")
        elif escaped == "\\":
            result.append("\\")
        elif escaped == '"':
            result.append('"')
        elif escaped == "u" and index + 4 < len(value):
            hex_value = value[index + 1 : index + 5]
            result.append(chr(int(hex_value, 16)))
            index += 4
        else:
            result.append(escaped)
        index += 1

    return "".join(result)


def contains_cyrillic(value: str) -> bool:
    return bool(CYRILLIC_RE.search(unescape_text(value)))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=COLUMN_NAMES,
            delimiter=";",
            lineterminator="\n",
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)


def merge_rows(
    extracted_rows: list[dict[str, str]],
    existing_rows: list[dict[str, str]],
) -> tuple[list[dict[str, str]], int, int, int]:
    existing_by_identity = {row_identity(row): row for row in existing_rows}
    next_id = max((int(row["id"]) for row in existing_rows), default=0) + 1
    merged_rows: list[dict[str, str]] = []
    preserved = 0
    added = 0
    skipped_cyrillic_source = 0

    for extracted in extracted_rows:
        identity = row_identity(extracted)
        existing = existing_by_identity.get(identity)

        if existing is None:
            if contains_cyrillic(extracted["sourceText"]):
                skipped_cyrillic_source += 1
                continue
            extracted["id"] = str(next_id)
            next_id += 1
            merged_rows.append(extracted)
            added += 1
            continue

        merged = dict(existing)
        merged["key"] = extracted["key"]
        merged["fileFormat"] = extracted["fileFormat"]
        merged["lineNumber"] = extracted["lineNumber"]
        merged["context"] = extracted["context"]
        merged["stringType"] = extracted["stringType"]

        old_source = existing.get("sourceText", "")
        old_translation = existing.get("translatedText", "")
        new_source = extracted["sourceText"]

        if contains_cyrillic(old_source) and contains_cyrillic(new_source):
            skipped_cyrillic_source += 1
            continue

        if new_source == old_source:
            pass
        elif (
            old_translation
            and old_source == old_translation
            and contains_cyrillic(old_source)
            and not contains_cyrillic(new_source)
        ):
            merged["sourceText"] = new_source
            merged["techHash"] = extracted["techHash"]
            merged["placeholders"] = extracted["placeholders"]
        elif old_translation and new_source == old_translation:
            merged["sourceText"] = old_source
            merged["techHash"] = existing.get("techHash", merged["techHash"])
            merged["placeholders"] = existing.get("placeholders", merged["placeholders"])
        else:
            merged["sourceText"] = new_source
            merged["techHash"] = extracted["techHash"]
            merged["placeholders"] = extracted["placeholders"]
            if contains_cyrillic(new_source):
                skipped_cyrillic_source += 1
                continue
            elif old_source != new_source:
                merged["translatedText"] = ""
                merged["translationMethod"] = "auto_extracted"
                merged["isHumanTranslation"] = "false"
                merged["status"] = "new"

        merged_rows.append(merged)
        preserved += 1

    merged_rows.sort(key=lambda row: int(row["id"]))
    return merged_rows, preserved, added, skipped_cyrillic_source


def main() -> None:
    extracted_rows = collect_rows(SOURCE_ROOT)
    existing_rows = read_csv_rows(MASTER_CSV)
    merged_rows, preserved, added, skipped_cyrillic_source = merge_rows(
        extracted_rows,
        existing_rows,
    )

    write_csv(MASTER_CSV, merged_rows)
    print(f"extracted_rows={len(extracted_rows)}")
    print(f"merged_rows={len(merged_rows)}")
    print(f"preserved_rows={preserved}")
    print(f"added_rows={added}")
    print(f"skipped_cyrillic_source_rows={skipped_cyrillic_source}")
    print(f"master_csv={MASTER_CSV}")


if __name__ == "__main__":
    main()
