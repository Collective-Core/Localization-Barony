from __future__ import annotations

import csv
import re
from pathlib import Path

from deep_translator import GoogleTranslator


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
DATA_DIR = SRC_DIR / "Data"
MASTER_CSV = DATA_DIR / "Strings.All.csv"

TOKEN_RE = re.compile(
    r"%(?:\d+\$)?[-+#0 ]*(?:\d+)?(?:\.\d+)?[A-Za-z%]|%[tmpeh]|"
    r"\b(?:LVL|HP|MP|DMG|XP|STR|DEX|CON|INT|PER|CHR|AC|RES|LAN|ONLINE|SOLO)\b|"
    r"\$+|\\\\n|\\\\r|\\\\t|#"
)


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
        "fonts/Р†РЅС„Р°.txt",
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
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}$")
UPPER_TOKEN_RE = re.compile(r"^[A-Z0-9_%+\-*. /\\:()]+$")

CATEGORY_VALUES = {"joker", "experience", "technique", "adventure", "teamwork"}

EXACT_TRANSLATIONS = {
    "$": "$",
    "%d Hits": "%d Влучань",
    "%d Times": "%d Разів",
    "%d Shards": "%d Уламків",
    "%d Shields": "%d Щитів",
    "%d Years Bad Luck": "%d Років Невдачі",
    "%d Brews": "%d Варок",
    "%d Bottles": "%d Пляшок",
    "%d Vials": "%d Флаконів",
    "%d Refreshments": "%d Напоїв",
    "%d Items": "%d Предметів",
    "%d Torches": "%d Смолоскипів",
    "%d DMG": "%d DMG",
    "%dG": "%dG",
    "%d Decantations": "%d Переливань",
    "%d *Plinks*": "%d *Дзиньків*",
    "%d Gems": "%d Самоцвітів",
    "%d Runs": "%d Рун",
    "%d Clowns": "%d Клоунів",
    "%d Zaps": "%d Зарядів",
    "%d Scrolls": "%d Сувоїв",
    "%d%": "%d%",
    "%d Spellbooks": "%d Книг Заклять",
    "%d Failures": "%d Провалів",
    "%d Spells": "%d Заклять",
    "%d Deaths": "%d Смертей",
    "%d XP": "%d XP",
    "%d Pts": "%d Очок",
    "%d Bonuses": "%d Бонусів",
    "%d HP": "%d HP",
    "%d MP": "%d MP",
    "%d Kills": "%d Убивств",
    "%d Strikes": "%d Ударів",
    "%d Identities": "%d Ідентичностей",
    "%d Crimes": "%d Злочинів",
    "%d Keys Total": "%d Ключів Загалом",
    "%d Iron Keys": "%d Залізних Ключів",
    "%d Bronze Keys": "%d Бронзових Ключів",
    "%d Silver Keys": "%d Срібних Ключів",
    "%d Gold Keys": "%d Золотих Ключів",
    "%d Fish": "%d Рибин",
    "%d LVLs": "%d Рівнів",
    "%d Games": "%d Ігор",
    "%d Wins": "%d Перемог",
    "%d Classic Wins": "%d Класичних Перемог",
    "%d Hell Wins": "%d Перемог у Пеклі",
    "%d Gold": "%d Золота",
    "%d Bats": "%d Кажанів",
    "%d Openings": "%d Відкривань",
    "%d Boxes": "%d Ящиків",
    "%d Doors": "%d Дверей",
    "%d Chests": "%d Скринь",
    "%d Successes": "%d Успіхів",
    "%d Mixes": "%d Змішувань",
    "%d Explosions": "%d Вибухів",
    "%d Metal Scrap": "%d Металобрухту",
    "%d Magic Scrap": "%d Магобрухту",
    "%d Times (HP Regen)": "%d Разів (Реген HP)",
    "%d Times (MP Regen)": "%d Разів (Реген MP)",
    "%d Times (Agility)": "%d Разів (Спритність)",
    "%d Times (Stamina)": "%d Разів (Витривалість)",
    "%d Times (Strength)": "%d Разів (Сила)",
    "%d Times (Mentality)": "%d Разів (Ментальність)",
    "%d Times (Restoration)": "%d Разів (Відновлення)",
    "%d Clappers Broken": "%d Розбитих Язиків Дзвона",
    "%d Bells Dropped": "%d Скинутих Дзвонів",
    "%d %s Novices": "%d %s Новачків",
    "%d Boulder Kills": "%d Убивств Валунами",
    "%d Gemstone Kills": "%d Убивств Самоцвітами",
    "%d Rock Kills": "%d Убивств Камінням",
    "%d Total Jewels": "%d Самоцвітів Усього",
    "%d Cracked Jewels": "%d Тріснутих Самоцвітів",
    "%d Rough Jewels": "%d Необроблених Самоцвітів",
    "%d Flawed Jewels": "%d Самоцвітів з Дефектом",
    "%d Flawless Jewels": "%d Бездоганних Самоцвітів",
    "+%d%%": "+%d%%",
    "+%d%% RES": "+%d%% RES",
    "+%d HP": "+%d HP",
    "+%d Bless": "+%d Благ.",
    "%d%%": "%d%%",
    "%d HP (%s)": "%d HP (%s)",
    "%d MP (%s)": "%d MP (%s)",
    "%d AC (%s)": "%d AC (%s)",
    "%d STR (%s)": "%d STR (%s)",
    "%d DEX (%s)": "%d DEX (%s)",
    "%d CON (%s)": "%d CON (%s)",
    "%d INT (%s)": "%d INT (%s)",
    "%d PER (%s)": "%d PER (%s)",
    "%d CHR (%s)": "%d CHR (%s)",
    "This is my first $ line of $ text": "Це мій перший $ рядок $ тексту",
    "This the $ second line in the text": "Це $ другий рядок у тексті",
    "Custom variable $ $ goes here!": "Спеціальна змінна $ $ тут!",
    "And it goes here: $ woo!": "І ось тут: $ ура!",
    "Also, here: $ thank you.": "Також ось тут: $ дякую.",
    "Use": "Використати",
    "Defend": "Захист",
    "variable text": "текст змінної",
    "This is my first line of text": "Це мій перший рядок тексту",
    "This the second line in the text": "Це другий рядок у тексті",
    "Custom variable $ goes here!": "Спеціальна змінна $ тут!",
    "Test dialogue line.\\nThis is a new line": "Тестовий рядок діалогу.\\nЦе новий рядок",
    "Test grave line.\\nThis is a new line": "Тестовий рядок епітафії.\\nЦе новий рядок",
    "Test signpost line.\\nThis is a new line": "Тестовий рядок таблички.\\nЦе новий рядок",
    "Test message line in green!\\nThis is a new line\\nColor variable data optional.": "Тестовий рядок повідомлення зеленим!\\nЦе новий рядок\\nДані змінної кольору необов'язкові.",
    "The JSON format for story scenes looks like this:\\r\\n": "JSON-формат для сюжетних сцен виглядає так:\\r\\n",
    "{\\r\\n": "{\\r\\n",
    "\\t\\\"version\\\": 1,\\r\\n": "\\t\\\"version\\\": 1,\\r\\n",
    "\\t\\\"press_a_to_advance\\\": true,\\r\\n": "\\t\\\"press_a_to_advance\\\": true,\\r\\n",
    "\\t\\\"text\\\": [\\r\\n": "\\t\\\"text\\\": [\\r\\n",
    "\\t\\t\\\"*3This is a text line. \\\",\\r\\n": "\\t\\t\\\"*3Це рядок тексту. \\\",\\r\\n",
    "\\t\\t\\\"Each line is simply concatenated by default.\\\\n\\\",\\r\\n": "\\t\\t\\\"Кожен рядок за замовчуванням просто приєднується.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Insert a new line sequence with \\\\n to add a new line anywhere.\\\\n\\\",\\r\\n": "\\t\\t\\\"Вставте послідовність нового рядка \\\\n, щоб додати новий рядок будь-де.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Use an asterisk *2 to change the size of the text box.\\\\n\\\",\\r\\n": "\\t\\t\\\"Використайте зірочку *2, щоб змінити розмір текстового вікна.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Insert an up carat aka ^ to advance to the next background image\\\\n\\\",\\r\\n": "\\t\\t\\\"Вставте каретку вгору, тобто ^, щоб перейти до наступного фонового зображення\\\\n\\\",\\r\\n",
    "\\t\\t\\\"in the list below at any time.\\\\n\\\",\\r\\n": "\\t\\t\\\"у списку нижче в будь-який момент.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Add a hashmark aka # to pause for dramatic effect any time.\\\\n\\\",\\r\\n": "\\t\\t\\\"Додайте символ решітки, тобто #, щоб у будь-який момент зробити драматичну паузу.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Add multiple hashmarks for a longer pause...##### Like that.\\\\n\\\",\\r\\n": "\\t\\t\\\"Додайте кілька решіток для довшої паузи...##### Отак.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"Each line of text should fit 80 characters. Blah blah blah blah blah blah blah.\\\\n\\\",\\r\\n": "\\t\\t\\\"Кожен рядок тексту має вміщатися у 80 символів. Бла-бла-бла-бла-бла-бла-бла.\\\\n\\\",\\r\\n",
    "\\t\\t\\\"The story ends when the last line is printed.\\\"\\r\\n": "\\t\\t\\\"Історія закінчується, коли виводиться останній рядок.\\\"\\r\\n",
    "\\t],\\r\\n": "\\t],\\r\\n",
    "\\t\\\"images\\\": [\\r\\n": "\\t\\\"images\\\": [\\r\\n",
    "\\t]\\r\\n": "\\t]\\r\\n",
    "}\\r\\n": "}\\r\\n",
    "If you miss a comma anywhere, or some other necessary punctuation mark, the story won't load.\\r\\n": "Якщо десь пропустити кому чи інший потрібний розділовий знак, історія не завантажиться.\\r\\n",
    "Have fun.\\r\\n": "Розважайтеся.\\r\\n",
}


def mask_tokens(text: str) -> tuple[str, list[str]]:
    tokens: list[str] = []

    def replace(match: re.Match[str]) -> str:
        tokens.append(match.group(0))
        return f"__TOK{len(tokens) - 1}__"

    return TOKEN_RE.sub(replace, text), tokens


def unmask_tokens(text: str, tokens: list[str]) -> str:
    for index, token in enumerate(tokens):
        text = text.replace(f"__TOK{index}__", token)
    return text


def should_uppercase(source: str) -> bool:
    letters = [ch for ch in source if ch.isalpha()]
    return bool(letters) and all(ch.upper() == ch for ch in letters)


def postprocess_translation(source: str, translated: str) -> str:
    replacements = {
        "звернень": "влучань",
        "Розпилені пляшки": "Пляшок Випито",
        "пекло перемагає": "Перемог у Пеклі",
        "класичних перемог": "Класичних Перемог",
        "сольні пробіги": "Сольні Забіги",
        "онлайн-пробіги": "Онлайн-Забіги",
        "локальні пробіги": "LAN-Забіги",
        "пробіжку": "забіг",
        "пробіг": "забіг",
        "ПЛОЩА:": "ЗОНА:",
    }
    for old, new in replacements.items():
        translated = translated.replace(old, new).replace(old.capitalize(), new)

    if should_uppercase(source):
        translated = translated.upper()

    return translated


def should_copy_source_as_translation(row: dict[str, str]) -> bool:
    source = row["sourceText"].strip()
    locator = row["locator"]
    relative_path = row["relativeFilePath"]

    if not source:
        return True

    if source in CATEGORY_VALUES or locator.endswith(".category"):
        return True

    if DATE_RE.fullmatch(source):
        return True

    if locator.endswith((".format", ".value", ".default", ".format_time")):
        return True

    if relative_path == "items/item_tooltips.json" and (
        ".stat_short_name." in locator
        or ".template_alchemy_type[" in locator
        or ".template_attributes_text_armor_conditional_tags[" in locator
    ):
        return True

    if UPPER_TOKEN_RE.fullmatch(source):
        return True

    return False


def translate_text_batch(translator: GoogleTranslator, texts: list[str]) -> list[str]:
    if not texts:
        return []
    masked = []
    token_sets = []
    for text in texts:
        value, tokens = mask_tokens(text)
        masked.append(value)
        token_sets.append(tokens)
    translated = translator.translate_batch(masked)
    results = []
    for source, value, tokens in zip(texts, translated, token_sets):
        if value is None:
            value = source
        restored = unmask_tokens(value, tokens)
        results.append(postprocess_translation(source, restored))
    return results


def main() -> None:
    with MASTER_CSV.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
        fieldnames = list(rows[0].keys())

    source_texts_to_translate: list[str] = []
    seen: set[str] = set()

    for row in rows:
        if row.get("translatedText", "").strip():
            continue
        if is_project_technical_row(row):
            continue
        if should_copy_source_as_translation(row):
            continue
        source = row["sourceText"]
        if source in EXACT_TRANSLATIONS or source in seen:
            continue
        seen.add(source)
        source_texts_to_translate.append(source)

    translator = GoogleTranslator(source="en", target="uk")
    generated: dict[str, str] = {}
    batch_size = 50
    for start in range(0, len(source_texts_to_translate), batch_size):
        chunk = source_texts_to_translate[start : start + batch_size]
        for source, translated in zip(chunk, translate_text_batch(translator, chunk)):
            generated[source] = translated

    updated = 0
    for row in rows:
        if row.get("translatedText", "").strip():
            continue
        if is_project_technical_row(row):
            continue
        source = row["sourceText"]
        if should_copy_source_as_translation(row):
            row["translatedText"] = source
        elif source in EXACT_TRANSLATIONS:
            row["translatedText"] = EXACT_TRANSLATIONS[source]
        else:
            row["translatedText"] = generated[source]
        row["translationMethod"] = "auto_machine_translated"
        row["isHumanTranslation"] = "false"
        row["status"] = "translated"
        updated += 1

    with MASTER_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, delimiter=";", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"updated_rows={updated}")


if __name__ == "__main__":
    main()
