from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
REPO_ROOT = SRC_DIR.parent
DATA_DIR = SRC_DIR / "Data"
CSV_PATH = DATA_DIR / "Strings.csv"
SOURCE_ROOT = REPO_ROOT / "Barony Ukrainian Localization"
OUTPUT_ENCODING = "utf-8"
SOURCE_ENCODING_CANDIDATES = (OUTPUT_ENCODING, "utf-8-sig", "cp1251")


@dataclass(frozen=True)
class TranslationRow:
    row_id: str
    relative_path: str
    file_format: str
    line_number: int
    locator: str
    source_text: str
    translated_text: str
    skip_apply_translation: bool


@dataclass(frozen=True)
class JsonStringSpan:
    value: str
    start: int
    end: int


@dataclass(frozen=True)
class JsonArraySpan:
    start: int
    end: int


@dataclass(frozen=True)
class SourceText:
    text: str
    encoding: str
    data: bytes
    bom_length: int = 0


LOCATOR_TOKEN_RE = re.compile(r"\.([^.@\[\]]+)|\[(\d+)\]")
JSON_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")

TECHNICAL_KEYS = {
    "action",
    "base_path",
    "colors",
    "conditional_attribute",
    "direction",
    "gui_module",
    "horizontal_justify",
    "icon_offset_x",
    "icon_offset_y",
    "icon_path",
    "id",
    "img_path",
    "img_from_spell_id",
    "internal_name",
    "notification_font",
    "path",
    "path_active",
    "path_active_hover",
    "path_hover",
    "path_locked",
    "path_locked_hover",
    "panels",
    "panel_center_x_offset",
    "panel_center_y_offset",
    "panel_radius",
    "panel_button_thickness",
    "panel_inner_circle_radius_offset",
    "spell_id",
    "tag",
    "tooltip_width",
    "vertical_justify",
    "version",
    "world_icon",
    "world_icon_small",
    "x",
    "y",
}

TECHNICAL_KEY_SUFFIXES = ("_path", "_icon", "_id")
TECHNICAL_CONTAINERS = {
    "colors",
    "world_icons",
    "variables",
    "damage_indicators",
}
TRANSLATABLE_TEXT_KEYS = {
    "abilities",
    "blurb",
    "default",
    "desc",
    "description",
    "details",
    "display_name",
    "format",
    "format0",
    "format1",
    "format2",
    "format3",
    "format4",
    "format_time",
    "inventory",
    "left_align",
    "legend_text",
    "localized_name",
    "localized_short_name",
    "message",
    "msg_emote",
    "msg_emote_to_you",
    "msg_emote_you",
    "msg_says",
    "name",
    "name_identified",
    "name_unidentified",
    "right_align",
    "sign",
    "text",
    "title",
    "title_short",
}
TRANSLATABLE_HELP_STRING_KEYS = {
    "empty_steam",
    "ghost",
    "healing",
    "healing_urgent",
    "hungry",
    "hungry_blood",
    "low_steam",
    "starving",
    "starving_blood",
    "very_hungry",
    "very_hungry_blood",
}
ASSET_REFERENCE_RE = re.compile(
    r"(?:^#?\*?images/|^fonts/|\.png\b|\.ttf\b|\.ogg\b|\.wav\b)",
    re.IGNORECASE,
)
LEADING_PLACEHOLDERS_RE = re.compile(r"^(?:(?:%%|%[sdif])\s*)+")
WORD_HIGHLIGHTS_KEY = b'"word_highlights"'
WORD_TOKEN_RE = re.compile(r"\S+")
WORD_HIGHLIGHT_TEXT_KEYS = ("text", "sign", "left_align", "right_align")


def read_source_text(file_path: Path) -> SourceText:
    data = file_path.read_bytes()
    if data.startswith(b"\xef\xbb\xbf"):
        return SourceText(
            text=data.decode("utf-8-sig"),
            encoding=OUTPUT_ENCODING,
            data=data,
            bom_length=3,
        )

    for encoding in SOURCE_ENCODING_CANDIDATES:
        try:
            return SourceText(text=data.decode(encoding), encoding=encoding, data=data)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError(
        OUTPUT_ENCODING,
        data,
        0,
        1,
        f"Unable to decode as {', '.join(SOURCE_ENCODING_CANDIDATES)}",
    )


def write_source_text(file_path: Path, text: str) -> None:
    file_path.write_bytes(text.encode(OUTPUT_ENCODING))


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


def detect_newline_style(text: str) -> str:
    if "\r\n" in text:
        return "\r\n"
    if "\n" in text:
        return "\n"
    return "\r\n"


def normalize_line_endings(value: str) -> str:
    return value.replace("\r\n", "\n").replace("\r", "\n")


def adapt_line_endings(value: str, reference: str) -> str:
    newline = "\r\n" if "\r\n" in reference else "\n"
    return normalize_line_endings(value).replace("\n", newline)


def parse_locator(locator: str) -> tuple[list[object], bool]:
    is_key_locator = locator.endswith(".@key")
    base_locator = locator[:-5] if is_key_locator else locator
    if not base_locator.startswith("root"):
        raise ValueError(f"Unsupported locator: {locator}")

    tokens: list[object] = []
    for match in LOCATOR_TOKEN_RE.finditer(base_locator[4:]):
        key_token, index_token = match.groups()
        if key_token is not None:
            tokens.append(key_token)
        else:
            tokens.append(int(index_token))
    return tokens, is_key_locator


def get_node(root: object, tokens: list[object]) -> object:
    current = root
    for token in tokens:
        if isinstance(token, int):
            current = current[token]
        else:
            current = current[token]
    return current


def key_from_locator(locator: str) -> str:
    tokens, _ = parse_locator(locator)
    if tokens and isinstance(tokens[-1], str):
        return tokens[-1]
    return ""


def is_technical_key(key: str) -> bool:
    lowered = key.lower()
    return lowered in TECHNICAL_KEYS or lowered.endswith(TECHNICAL_KEY_SUFFIXES)


def is_technical_locator(locator: str) -> bool:
    tokens, _ = parse_locator(locator)
    if not tokens:
        return False

    leaf = tokens[-1]
    if isinstance(leaf, str):
        return is_technical_key(leaf)

    for token in reversed(tokens[:-1]):
        if isinstance(token, str):
            return token.lower() in TECHNICAL_KEYS
    return False


def text_key_from_tokens(tokens: list[object]) -> str:
    if not tokens:
        return ""

    leaf = tokens[-1]
    if isinstance(leaf, str):
        return leaf

    for token in reversed(tokens[:-1]):
        if isinstance(token, str):
            return token
    return ""


def has_technical_container(tokens: list[object]) -> bool:
    return any(
        isinstance(token, str) and token.lower() in TECHNICAL_CONTAINERS
        for token in tokens[:-1]
    )


def is_translatable_json_text_locator(relative_path: str, locator: str) -> bool:
    tokens, is_key_locator = parse_locator(locator)
    if is_key_locator:
        return False

    if has_technical_container(tokens):
        return False

    if relative_path in {"data/callout_wheel.json", "data/callout_wheelen.json"}:
        key = text_key_from_tokens(tokens)
        key_lower = key.lower()
        if len(tokens) >= 2 and tokens[-2] == "help_strings":
            return key in TRANSLATABLE_HELP_STRING_KEYS
        return key_lower in {
            "text",
            "msg_says",
            "msg_emote",
            "msg_emote_you",
            "msg_emote_to_you",
        }

    if relative_path == "data/status_effects.json":
        key = text_key_from_tokens(tokens)
        key_lower = key.lower()
        return key_lower in {"name", "desc"}

    return not is_technical_locator(locator)


def is_asset_reference(value: str) -> bool:
    return bool(ASSET_REFERENCE_RE.search(value))


def should_apply_row(row: TranslationRow) -> bool:
    if not row.translated_text:
        return False

    if row.skip_apply_translation:
        return False

    # JSON keys are structure for Barony's layout-sensitive JSON configs.
    # Only replace string values; never rename keys or re-serialize the file.
    if row.locator.endswith(".@key"):
        return False

    if row.file_format == "json" and not is_translatable_json_text_locator(
        row.relative_path,
        row.locator,
    ):
        return False

    # Keep images, fonts, audio and other asset references untouched.
    if is_asset_reference(row.source_text) or is_asset_reference(row.translated_text):
        return False

    # Keep known technical fields untouched even if they contain string values.
    if row.file_format == "json" and is_technical_locator(row.locator):
        return False

    return True


def skip_json_whitespace(text: str, index: int) -> int:
    while index < len(text) and text[index] in " \t\r\n":
        index += 1
    return index


def parse_json_string_token(text: str, index: int) -> tuple[str, int, int]:
    if index >= len(text) or text[index] != '"':
        raise ValueError(f"Expected JSON string at offset {index}")
    value, end = json.decoder.scanstring(text, index + 1, True)
    return value, index, end


def parse_json_literal(text: str, index: int, literal: str) -> int:
    if not text.startswith(literal, index):
        raise ValueError(f"Expected {literal!r} at offset {index}")
    return index + len(literal)


def parse_json_value(
    text: str,
    index: int,
    path: tuple[object, ...],
    spans: dict[tuple[object, ...], JsonStringSpan],
    key_spans: dict[tuple[object, ...], JsonStringSpan],
    array_spans: dict[tuple[object, ...], JsonArraySpan] | None = None,
) -> int:
    index = skip_json_whitespace(text, index)
    if index >= len(text):
        raise ValueError("Unexpected end of JSON")

    char = text[index]
    if char == "{":
        return parse_json_object(text, index, path, spans, key_spans, array_spans)
    if char == "[":
        start = index
        end = parse_json_array(text, index, path, spans, key_spans, array_spans)
        if array_spans is not None:
            array_spans[path] = JsonArraySpan(start=start, end=end)
        return end
    if char == '"':
        value, start, end = parse_json_string_token(text, index)
        spans[path] = JsonStringSpan(value=value, start=start, end=end)
        return end
    if char == "t":
        return parse_json_literal(text, index, "true")
    if char == "f":
        return parse_json_literal(text, index, "false")
    if char == "n":
        return parse_json_literal(text, index, "null")

    match = JSON_NUMBER_RE.match(text, index)
    if not match:
        raise ValueError(f"Expected JSON value at offset {index}")
    return match.end()


def parse_json_object(
    text: str,
    index: int,
    path: tuple[object, ...],
    spans: dict[tuple[object, ...], JsonStringSpan],
    key_spans: dict[tuple[object, ...], JsonStringSpan],
    array_spans: dict[tuple[object, ...], JsonArraySpan] | None = None,
) -> int:
    index += 1
    index = skip_json_whitespace(text, index)
    if index < len(text) and text[index] == "}":
        return index + 1

    while True:
        index = skip_json_whitespace(text, index)
        key, start, index = parse_json_string_token(text, index)
        key_spans[(*path, key)] = JsonStringSpan(value=key, start=start, end=index)
        index = skip_json_whitespace(text, index)
        if index >= len(text) or text[index] != ":":
            raise ValueError(f"Expected ':' at offset {index}")
        index = parse_json_value(
            text,
            index + 1,
            (*path, key),
            spans,
            key_spans,
            array_spans,
        )
        index = skip_json_whitespace(text, index)
        if index >= len(text):
            raise ValueError("Unexpected end of JSON object")
        if text[index] == "}":
            return index + 1
        if text[index] != ",":
            raise ValueError(f"Expected ',' at offset {index}")
        index += 1


def parse_json_array(
    text: str,
    index: int,
    path: tuple[object, ...],
    spans: dict[tuple[object, ...], JsonStringSpan],
    key_spans: dict[tuple[object, ...], JsonStringSpan],
    array_spans: dict[tuple[object, ...], JsonArraySpan] | None = None,
) -> int:
    index += 1
    index = skip_json_whitespace(text, index)
    if index < len(text) and text[index] == "]":
        return index + 1

    item_index = 0
    while True:
        index = parse_json_value(
            text,
            index,
            (*path, item_index),
            spans,
            key_spans,
            array_spans,
        )
        item_index += 1
        index = skip_json_whitespace(text, index)
        if index >= len(text):
            raise ValueError("Unexpected end of JSON array")
        if text[index] == "]":
            return index + 1
        if text[index] != ",":
            raise ValueError(f"Expected ',' at offset {index}")
        index += 1


def build_json_string_spans(
    text: str,
) -> tuple[
    dict[tuple[object, ...], JsonStringSpan],
    dict[tuple[object, ...], JsonStringSpan],
]:
    spans: dict[tuple[object, ...], JsonStringSpan] = {}
    key_spans: dict[tuple[object, ...], JsonStringSpan] = {}
    index = parse_json_value(text, 0, (), spans, key_spans)
    index = skip_json_whitespace(text, index)
    if index != len(text):
        raise ValueError(f"Unexpected trailing JSON content at offset {index}")
    return spans, key_spans


def build_json_spans(
    text: str,
) -> tuple[
    dict[tuple[object, ...], JsonStringSpan],
    dict[tuple[object, ...], JsonStringSpan],
    dict[tuple[object, ...], JsonArraySpan],
]:
    spans: dict[tuple[object, ...], JsonStringSpan] = {}
    key_spans: dict[tuple[object, ...], JsonStringSpan] = {}
    array_spans: dict[tuple[object, ...], JsonArraySpan] = {}
    index = parse_json_value(text, 0, (), spans, key_spans, array_spans)
    index = skip_json_whitespace(text, index)
    if index != len(text):
        raise ValueError(f"Unexpected trailing JSON content at offset {index}")
    return spans, key_spans, array_spans


def encode_json_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def text_offset_to_byte_offset(
    text: str,
    offset: int,
    encoding: str,
    bom_length: int = 0,
) -> int:
    return bom_length + len(text[:offset].encode(encoding))


def find_matching_json_array_end(data: bytes, start: int) -> int:
    depth = 0
    in_string = False
    escaped = False

    for index in range(start, len(data)):
        char = data[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == 0x5C:
                escaped = True
            elif char == 0x22:
                in_string = False
            continue

        if char == 0x22:
            in_string = True
        elif char == 0x5B:
            depth += 1
        elif char == 0x5D:
            depth -= 1
            if depth == 0:
                return index + 1

    raise ValueError("Unterminated word_highlights array")


def clear_word_highlights(data: bytes) -> tuple[bytes, int]:
    replacements: list[tuple[int, int, bytes]] = []
    search_from = 0

    while True:
        key_index = data.find(WORD_HIGHLIGHTS_KEY, search_from)
        if key_index == -1:
            break

        index = key_index + len(WORD_HIGHLIGHTS_KEY)
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index >= len(data) or data[index] != 0x3A:
            search_from = key_index + len(WORD_HIGHLIGHTS_KEY)
            continue

        index += 1
        while index < len(data) and data[index] in b" \t\r\n":
            index += 1
        if index >= len(data) or data[index] != 0x5B:
            search_from = key_index + len(WORD_HIGHLIGHTS_KEY)
            continue

        end = find_matching_json_array_end(data, index)
        if data[index:end] != b"[]":
            replacements.append((index, end, b"[]"))
        search_from = end

    for start, end, replacement in reversed(replacements):
        data = data[:start] + replacement + data[end:]

    return data, len(replacements)


def word_count(value: str) -> int:
    return len(WORD_TOKEN_RE.findall(value))


def filtered_word_highlights(text_value: object, current_highlights: object) -> object:
    if isinstance(text_value, str):
        if not isinstance(current_highlights, list):
            return []
        return [
            item
            for item in current_highlights
            if isinstance(item, int)
        ]

    if isinstance(text_value, list) and all(
        isinstance(item, str) for item in text_value
    ):
        if not isinstance(current_highlights, list) or not current_highlights:
            return []
        result: list[list[int]] = []
        for raw_line_highlights in current_highlights:
            if not isinstance(raw_line_highlights, list):
                raw_line_highlights = []
            result.append(
                [
                    item
                    for item in raw_line_highlights
                    if isinstance(item, int)
                ]
            )
        if not result:
            return []
        return result

    return []


def desired_word_highlights(root: object, path: tuple[object, ...]) -> object:
    if not path or path[-1] != "word_highlights":
        return []

    parent_path = path[:-1]
    parent = get_node(root, list(parent_path))
    if not isinstance(parent, dict):
        return []

    if "text" in parent:
        return filtered_word_highlights(
            parent.get("text"),
            parent.get("word_highlights"),
        )

    if parent_path and parent_path[-1] == "attributes":
        grandparent = get_node(root, list(parent_path[:-1]))
        if isinstance(grandparent, dict):
            for text_key in WORD_HIGHLIGHT_TEXT_KEYS:
                if text_key in grandparent:
                    return filtered_word_highlights(
                        grandparent.get(text_key),
                        parent.get("word_highlights"),
                    )

    return []


def format_word_highlights(value: object, current_text: str) -> str:
    if "\n" not in current_text and "\r" not in current_text:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))

    if isinstance(value, list) and all(isinstance(item, list) for item in value):
        newline = "\r\n" if "\r\n" in current_text else "\n"
        closing_indent = ""
        closing_match = re.search(r"(?:\r?\n)([ \t]*)\]\s*$", current_text)
        if closing_match:
            closing_indent = closing_match.group(1)

        item_indent = f"{closing_indent}\t"
        item_match = re.search(r"(?:\r?\n)([ \t]*)\[", current_text)
        if item_match:
            item_indent = item_match.group(1)

        multiline_items = bool(re.search(r"[ \t]*\[\s*\r?\n[ \t]*\d", current_text))

        def format_item(item: list[object]) -> str:
            if not item:
                return f"{item_indent}[]"
            if not multiline_items:
                return f"{item_indent}{json.dumps(item, ensure_ascii=False, separators=(',', ':'))}"

            number_indent = f"{item_indent}    "
            number_match = re.search(r"\[\s*\r?\n([ \t]*)\d", current_text)
            if number_match:
                number_indent = number_match.group(1)
            numbers = [
                f"{number_indent}{json.dumps(number, ensure_ascii=False)}"
                for number in item
            ]
            return f"{item_indent}[{newline}{(f',{newline}').join(numbers)}{newline}{item_indent}]"

        items = [format_item(item) for item in value]
        return f"[{newline}{(f',{newline}').join(items)}{newline}{closing_indent}]"

    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def sync_word_highlights(data: bytes, encoding: str, bom_length: int = 0) -> tuple[bytes, int]:
    text = data.decode("utf-8-sig" if bom_length else encoding)
    root = json.loads(text)
    _, _, array_spans = build_json_spans(text)
    replacements: list[tuple[int, int, bytes]] = []

    for path, span in array_spans.items():
        if not path or path[-1] != "word_highlights":
            continue

        current_text = text[span.start : span.end]
        current_value = get_node(root, list(path))
        desired_value = desired_word_highlights(root, path)
        if current_value == desired_value:
            continue

        replacement_text = format_word_highlights(
            desired_value,
            current_text,
        )
        if current_text == replacement_text:
            continue

        replacements.append(
            (
                text_offset_to_byte_offset(text, span.start, encoding, bom_length),
                text_offset_to_byte_offset(text, span.end, encoding, bom_length),
                replacement_text.encode(encoding),
            )
        )

    for start, end, replacement in reversed(replacements):
        data = data[:start] + replacement + data[end:]

    return data, len(replacements)


def adapt_translation_to_source_template(source_text: str, translated_text: str) -> str:
    result = translated_text
    placeholder_prefix = LEADING_PLACEHOLDERS_RE.match(source_text)
    prefix = placeholder_prefix.group(0) if placeholder_prefix else ""

    if prefix:
        source_has_opening_quote = source_text.startswith(f'{prefix}"')
        translation_has_prefix = result.startswith(prefix)
        translation_has_opening_quote = result.startswith(f'{prefix}"')
        if source_has_opening_quote and translation_has_prefix and not translation_has_opening_quote:
            result = f'{prefix}"{result[len(prefix):]}'
    elif source_text.startswith('"') and not result.startswith('"'):
        result = f'"{result}'

    if source_text.endswith('"') and not result.endswith('"'):
        result = f'{result}"'

    return result


def apply_txt_rows(file_path: Path, rows: list[TranslationRow]) -> tuple[int, list[str], bool]:
    source = read_source_text(file_path)
    contents = source.text
    lines = contents.splitlines(keepends=True)
    changed = 0
    warnings: list[str] = []

    for row in sorted(rows, key=lambda item: item.line_number):
        if not should_apply_row(row):
            continue

        index = row.line_number - 1
        if index < 0 or index >= len(lines):
            warnings.append(
                f"{row.relative_path}:{row.line_number} line is missing"
            )
            continue

        current = lines[index]
        translated_text = adapt_line_endings(row.translated_text, current)
        if current == translated_text:
            continue

        current_unescaped = normalize_line_endings(unescape_text(current))
        current_normalized = normalize_line_endings(current)
        source_text = normalize_line_endings(row.source_text)
        source_text_without_bom = source_text.removeprefix("\ufeff")
        translated_text_normalized = normalize_line_endings(translated_text)
        if current_unescaped not in {
            source_text,
            source_text_without_bom,
            translated_text_normalized,
        } and current_normalized not in {
            source_text,
            source_text_without_bom,
            translated_text_normalized,
        }:
            warnings.append(
                f"{row.relative_path}:{row.line_number} source mismatch"
            )
            continue

        lines[index] = translated_text
        changed += 1

    wrote_file = changed > 0
    if wrote_file:
        write_source_text(file_path, "".join(lines))

    return changed, warnings, wrote_file


def apply_json_rows(file_path: Path, rows: list[TranslationRow]) -> tuple[int, list[str], bool]:
    source = read_source_text(file_path)
    original_text = source.text
    original_bytes = source.data
    value_spans, key_spans = build_json_string_spans(original_text)

    changed = 0
    warnings: list[str] = []
    replacements: list[tuple[int, int, bytes]] = []

    for row in rows:
        if not should_apply_row(row):
            continue

        tokens, is_key_locator = parse_locator(row.locator)
        span_map = key_spans if is_key_locator else value_spans
        span = span_map.get(tuple(tokens))
        if span is None:
            warnings.append(f"{row.relative_path}:{row.locator} locator is missing")
            continue

        translated_text = adapt_translation_to_source_template(
            row.source_text,
            row.translated_text,
        )

        if span.value == translated_text:
            encoded_translated_text = encode_json_string(translated_text)
            if original_text[span.start : span.end] == encoded_translated_text:
                continue
            replacements.append(
                (
                    text_offset_to_byte_offset(
                        original_text,
                        span.start,
                        source.encoding,
                        source.bom_length,
                    ),
                    text_offset_to_byte_offset(
                        original_text,
                        span.end,
                        source.encoding,
                        source.bom_length,
                    ),
                    encoded_translated_text.encode(source.encoding),
                )
            )
            changed += 1
            continue
        # JSON text fields may already contain an older translation. Once a
        # locator has passed the whitelist above, replacing only this string
        # span is layout-safe and keeps technical fields untouched.
        replacements.append(
            (
                text_offset_to_byte_offset(
                    original_text,
                    span.start,
                    source.encoding,
                    source.bom_length,
                ),
                text_offset_to_byte_offset(
                    original_text,
                    span.end,
                    source.encoding,
                    source.bom_length,
                ),
                encode_json_string(translated_text).encode(source.encoding),
            )
        )
        changed += 1

    wrote_file = changed > 0
    if wrote_file:
        for start, end, replacement in sorted(replacements, reverse=True):
            original_bytes = original_bytes[:start] + replacement + original_bytes[end:]

    # Highlight indices are coupled to word positions. Ukrainian translations
    # can shorten or reorder text, so stale indices may point past the
    # translated word list. Rewrite only the array values, preserving the
    # surrounding layout and keeping per-line arrays for script text blocks.
    original_bytes, word_highlight_changes = sync_word_highlights(
        original_bytes,
        source.encoding,
        source.bom_length,
    )
    changed += word_highlight_changes
    wrote_file = wrote_file or word_highlight_changes > 0

    if wrote_file:
        file_path.write_bytes(original_bytes)

    return changed, warnings, wrote_file


def load_rows() -> dict[str, list[TranslationRow]]:
    grouped_rows: dict[str, list[TranslationRow]] = defaultdict(list)
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter=";")
        for raw_row in reader:
            translated_text = raw_row["translatedText"]
            if not translated_text:
                continue

            row = TranslationRow(
                row_id=raw_row["id"],
                relative_path=raw_row["relativeFilePath"],
                file_format=raw_row["fileFormat"],
                line_number=int(raw_row["lineNumber"]),
                locator=raw_row["locator"],
                source_text=unescape_text(raw_row["sourceText"]),
                translated_text=unescape_text(translated_text),
                skip_apply_translation=raw_row.get("skipApplyTranslation", "").lower()
                == "true",
            )
            if not should_apply_row(row):
                continue
            grouped_rows[row.relative_path].append(row)

    return grouped_rows


def main() -> None:
    grouped_rows = load_rows()
    updated_files = 0
    updated_rows = 0
    warnings: list[str] = []

    for relative_path in sorted(grouped_rows):
        file_path = SOURCE_ROOT / relative_path
        if not file_path.exists():
            warnings.append(f"{relative_path} file is missing")
            continue

        rows = grouped_rows[relative_path]
        file_format = rows[0].file_format

        if file_format == "txt":
            changed, file_warnings, wrote_file = apply_txt_rows(file_path, rows)
        elif file_format == "json":
            changed, file_warnings, wrote_file = apply_json_rows(file_path, rows)
        else:
            warnings.append(f"{relative_path} unsupported format: {file_format}")
            continue

        if wrote_file:
            updated_files += 1
            updated_rows += changed
        warnings.extend(file_warnings)

    print(f"updated_files={updated_files}")
    print(f"updated_rows={updated_rows}")
    print(f"warning_count={len(warnings)}")
    for warning in warnings[:200]:
        print(f"warning={warning}")
    if len(warnings) > 200:
        print("warning=... truncated ...")


if __name__ == "__main__":
    main()
