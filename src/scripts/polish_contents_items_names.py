from __future__ import annotations

import csv
import json
import re
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = SCRIPT_DIR.parent
REPO_ROOT = SRC_DIR.parent
DATA_DIR = SRC_DIR / "Data"
SOURCE_ROOT = REPO_ROOT / "Barony Ukrainian Localization"

CSV_PATHS = [
    DATA_DIR / "Strings.All.csv",
    DATA_DIR / "Strings.csv",
]

CONTENTS_ITEMS_MAPPING = {
    "\\u0020\\u0020\\u0020\\u0020ARMOR": "\\u0020\\u0020\\u0020\\u0020БРОНЯ",
    "SHIELDS": "ЩИТИ",
    "LEATHER ARMOR": "ШКІРЯНА БРОНЯ",
    "QUILTED ARMOR": "СТЬОБАНА БРОНЯ",
    "CHAIN ARMOR": "КОЛЬЧУЖНА БРОНЯ",
    "IRON ARMOR": "ЗАЛІЗНА БРОНЯ",
    "STEEL ARMOR": "СТАЛЕВА БРОНЯ",
    "CRYSTAL ARMOR": "КРИШТАЛЕВА БРОНЯ",
    "SPHINX'S CASQUE": "ШОЛОМ СФІНКСА",
    "ORACLE'S TREADS": "ЧОБОТИ ОРАКУЛА",
    "DJINNI'S BRACE": "НАРУЧ ДЖИНА",
    "DRAGON'S MAIL": "ДРАКОНЯЧА КОЛЬЧУГА",
    "WRAITH'S GOWN": "ШАТИ ПРИМАРИ",
    "\\u0020\\u0020\\u0020\\u0020CLOTHING": "\\u0020\\u0020\\u0020\\u0020ОДЯГ",
    "HATS & HOODS": "КАПЕЛЮХИ ТА КАПТУРИ",
    "CROWNS & HEADDRESSES": "КОРОНИ ТА ГОЛОВНІ УБОРИ",
    "FACE ACCESSORIES": "АКСЕСУАРИ ДЛЯ ОБЛИЧЧЯ",
    "MASKS & VISORS": "МАСКИ ТА ЗАБРАЛА",
    "CLOAKS & CLOTHING": "ПЛАЩІ ТА ОДЯГ",
    "BACKPACKS": "НАПЛІЧНИКИ",
    "\\u0020\\u0020\\u0020\\u0020MELEE WEAPONS": "\\u0020\\u0020\\u0020\\u0020ХОЛОДНА ЗБРОЯ",
    "SWORDS": "МЕЧІ",
    "GREATSWORDS": "ДВОРУЧНІ МЕЧІ",
    "RAPIER": "РАПІРА",
    "AXES": "СОКИРИ",
    "MACES": "БУЛАВИ",
    "FLAILS": "ЦІПИ",
    "SHILLELAGH": "ШІЛЕЛАГ",
    "POLEARMS": "ДРЕВКОВА ЗБРОЯ",
    "DYRNWYN": "ДИРНВІН",
    "PARASHU": "ПАРАШУ",
    "SHARUR": "ШАРУР",
    "GUNGNIR": "ГУНГНІР",
    "FIST WEAPONS": "КУЛАЧНА ЗБРОЯ",
    "WHIP": "БАТІГ",
    "\\u0020\\u0020\\u0020\\u0020MISSILE WEAPONS": "\\u0020\\u0020\\u0020\\u0020ДИСТАНЦІЙНА ЗБРОЯ",
    "SLINGSHOT": "РОГАТКА",
    "BOWS": "ЛУКИ",
    "CROSSBOW": "АРБАЛЕТ",
    "ARBALEST": "АРБАЛЕСТ",
    "KHRYSELAKATOS": "ХРИСЕЛАКАТОС",
    "SWIFT & SPRINGSHOT AMMO": "ШВИДКІ ТА ПРУЖИННІ БОЄПРИПАСИ",
    "SILVER & PIERCING AMMO": "СРІБНІ ТА БРОНЕБІЙНІ БОЄПРИПАСИ",
    "FIRE & HUNTING AMMO": "ВОГНЯНІ ТА МИСЛИВСЬКІ БОЄПРИПАСИ",
    "CRYSTAL AMMO": "КРИШТАЛЕВІ БОЄПРИПАСИ",
    "\\u0020\\u0020\\u0020\\u0020THROWING WEAPONS": "\\u0020\\u0020\\u0020\\u0020МЕТАЛЬНА ЗБРОЯ",
    "TOMAHAWKS & DAGGERS": "ТОМАГАВКИ ТА КИНДЖАЛИ",
    "CHAKRAMS & SHURIKENS": "ЧАКРАМИ ТА СЮРІКЕНИ",
    "BOOMERANG": "БУМЕРАНГ",
    "BOLAS": "БОЛАС",
    "SLUDGE BALLS": "БАГНЯНІ КУЛІ",
    "\\u0020\\u0020\\u0020\\u0020CRYSTALS": "\\u0020\\u0020\\u0020\\u0020КРИСТАЛИ",
    "ROCKS & GEMS": "КАМІННЯ ТА САМОЦВІТИ",
    "CRYSTAL SHARD": "УЛАМОК КРИШТАЛЮ",
    "MYSTIC ORB": "МІСТИЧНА СФЕРА",
    "\\u0020\\u0020\\u0020\\u0020FOOD": "\\u0020\\u0020\\u0020\\u0020ЇЖА",
    "MORSELS": "СИР І ЯБЛУКА",
    "CREAM PIE": "КРЕМОВИЙ ПИРІГ",
    "TOMALLEY": "ТОМАЛЕЙ",
    "MEALS": "М'ЯСО, РИБА ТА ХЛІБ",
    "RATIONS": "ПАЙКИ",
    "TIN & TIN OPENER": "КОНСЕРВИ ТА КОНСЕРВНИЙ НІЖ",
    "BLOOD VIALS": "ФЛАКОНИ КРОВІ",
    "\\u0020\\u0020\\u0020\\u0020POTIONS & DRINKS": "\\u0020\\u0020\\u0020\\u0020ЗІЛЛЯ ТА НАПОЇ",
    "WATER": "ВОДА",
    "EMPTY BOTTLE": "ПОРОЖНЯ ПЛЯШКА",
    "DEFENSIVE POTIONS": "ЗАХИСНІ ЗІЛЛЯ",
    "OFFENSIVE POTIONS": "НАСТУПАЛЬНІ ЗІЛЛЯ",
    "ALEMBIC": "АЛЕМБІК",
    "\\u0020\\u0020\\u0020\\u0020TOOLS": "\\u0020\\u0020\\u0020\\u0020ІНСТРУМЕНТИ",
    "TORCHES & LANTERNS": "СМОЛОСКИПИ ТА ЛІХТАРІ",
    "MIRRORS": "ДЗЕРКАЛА",
    "TOWEL": "РУШНИК",
    "MINING PICK": "КАЙЛО",
    "TINKERING KIT": "НАБІР МАЙСТРУВАННЯ",
    "FRYPAN": "СКОВОРІДКА",
    "LOCKPICK": "ВІДМИЧКА",
    "KEYS": "КЛЮЧІ",
    "SKELETON KEY": "СКЕЛЕТНИЙ КЛЮЧ",
    "\\u0020\\u0020\\u0020\\u0020GADGETS": "\\u0020\\u0020\\u0020\\u0020ПРИСТРОЇ",
    "BEARTRAP": "ВЕДМЕЖИЙ КАПКАН",
    "NOISEMAKER": "ШУМОВИЙ ПРИСТРІЙ",
    "DUMMYBOT": "МАНЕКЕН-БОТ",
    "SENTRY BOT & SPELLBOT": "СТОРОЖОВИЙ БОТ І СПЕЛБОТ",
    "GYROBOT": "ГІРОБОТ",
    "TINKERED TRAPS": "МЕХАНІЧНІ ПАСТКИ",
    "TELEPORTATION TRAP": "ТЕЛЕПОРТАЦІЙНА ПАСТКА",
    "\\u0020\\u0020\\u0020\\u0020OTHER": "\\u0020\\u0020\\u0020\\u0020ІНШЕ",
    "MAIL & LORE BOOKS": "ЛИСТИ ТА КНИГИ ЗНАНЬ",
    "DEATH BOX": "СКРИНЯ СМЕРТІ",
    "DUCK": "КАЧКА",
    "DARTS & PLUMBATA": "ДРОТИКИ ТА ПЛЮМБАТИ",
}

ITEM_NAME_LOCATOR_MAPPING = {
    "root.items.tool_pickaxe.name_identified": "кайло",
    "root.items.tool_pickaxe.name_unidentified": "кайло",
    "root.items.tool_tinopener.name_identified": "консервний ніж",
    "root.items.tool_tinopener.name_unidentified": "консервний ніж",
    "root.items.tool_dummybot.name_identified": "манекен-бот",
    "root.items.tool_dummybot.name_unidentified": "манекен-бот",
    "root.items.tool_sentrybot.name_identified": "сторожовий бот",
    "root.items.tool_sentrybot.name_unidentified": "сторожовий бот",
    "root.items.tool_spellbot.name_identified": "спелбот",
    "root.items.tool_spellbot.name_unidentified": "спелбот",
}

MONSTER_CONTENTS_OVERRIDES = {
    "DUMMYBOT": "МАНЕКЕН-БОТ",
}

CONTENTS_LOCATOR_RE = re.compile(
    r"^root\.(contents|contents_alphabetical)\[(\d+)\]\..+\.@key$"
)


def update_csv(path: Path) -> tuple[int, int]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=";"))
        fieldnames = list(rows[0].keys()) if rows else []

    contents_updated = 0
    item_names_updated = 0

    for row in rows:
        if (
            row["relativeFilePath"] == "lang/compendium_lang/contents_items.json"
            and row["locator"].endswith(".@key")
        ):
            translated = CONTENTS_ITEMS_MAPPING.get(row["sourceText"])
            if translated is not None and row.get("translatedText") != translated:
                row["translatedText"] = translated
                row["translationMethod"] = "manual_glossary_synced"
                row["isHumanTranslation"] = "true"
                row["status"] = "translated"
                contents_updated += 1
        elif row["relativeFilePath"] == "lang/item_names.json":
            translated = ITEM_NAME_LOCATOR_MAPPING.get(row["locator"])
            if translated is not None and row.get("translatedText") != translated:
                row["translatedText"] = translated
                row["translationMethod"] = "manual_glossary_synced"
                row["isHumanTranslation"] = "true"
                row["status"] = "translated"
                item_names_updated += 1
        elif row["relativeFilePath"] == "lang/compendium_lang/contents_monsters.json":
            translated = MONSTER_CONTENTS_OVERRIDES.get(row["sourceText"])
            if translated is not None and row.get("translatedText") != translated:
                row["translatedText"] = translated
                row["translationMethod"] = "manual_glossary_synced"
                row["isHumanTranslation"] = "true"
                row["status"] = "translated"

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=fieldnames,
            delimiter=";",
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)

    return contents_updated, item_names_updated


def load_rows_by_relative_path(relative_path: str) -> list[dict[str, str]]:
    path = DATA_DIR / "Strings.csv"
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            row
            for row in csv.DictReader(handle, delimiter=";")
            if row["relativeFilePath"] == relative_path and row["locator"].endswith(".@key")
        ]


def update_contents_items_json() -> int:
    path = SOURCE_ROOT / "lang/compendium_lang/contents_items.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = load_rows_by_relative_path("lang/compendium_lang/contents_items.json")
    updated = 0

    for row in rows:
        match = CONTENTS_LOCATOR_RE.match(row["locator"])
        if not match:
            continue
        section_name, index_text = match.groups()
        index = int(index_text)
        translated_key = row["translatedText"]
        section = payload.get(section_name, [])
        if index >= len(section):
            continue
        entry = section[index]
        if not isinstance(entry, dict) or len(entry) != 1:
            continue
        current_key, value = next(iter(entry.items()))
        if current_key == translated_key:
            continue
        section[index] = {translated_key: value}
        updated += 1

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent="\t") + "\n",
        encoding="utf-8",
    )
    return updated


def update_item_names_json() -> int:
    path = SOURCE_ROOT / "lang/item_names.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", {})
    locator_to_item_field = {
        "root.items.tool_pickaxe.name_identified": ("tool_pickaxe", "name_identified"),
        "root.items.tool_pickaxe.name_unidentified": ("tool_pickaxe", "name_unidentified"),
        "root.items.tool_tinopener.name_identified": ("tool_tinopener", "name_identified"),
        "root.items.tool_tinopener.name_unidentified": ("tool_tinopener", "name_unidentified"),
        "root.items.tool_dummybot.name_identified": ("tool_dummybot", "name_identified"),
        "root.items.tool_dummybot.name_unidentified": ("tool_dummybot", "name_unidentified"),
        "root.items.tool_sentrybot.name_identified": ("tool_sentrybot", "name_identified"),
        "root.items.tool_sentrybot.name_unidentified": ("tool_sentrybot", "name_unidentified"),
        "root.items.tool_spellbot.name_identified": ("tool_spellbot", "name_identified"),
        "root.items.tool_spellbot.name_unidentified": ("tool_spellbot", "name_unidentified"),
    }

    updated = 0
    for locator, translated in ITEM_NAME_LOCATOR_MAPPING.items():
        item_key, field_name = locator_to_item_field[locator]
        if items[item_key][field_name] != translated:
            items[item_key][field_name] = translated
            updated += 1

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=4) + "\n",
        encoding="utf-8",
    )
    return updated


def update_contents_monsters_json() -> int:
    path = SOURCE_ROOT / "lang/compendium_lang/contents_monsters.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = load_rows_by_relative_path("lang/compendium_lang/contents_monsters.json")
    updated = 0

    for row in rows:
        if row["sourceText"] not in MONSTER_CONTENTS_OVERRIDES:
            continue
        match = CONTENTS_LOCATOR_RE.match(row["locator"])
        if not match:
            continue
        section_name, index_text = match.groups()
        index = int(index_text)
        translated_key = MONSTER_CONTENTS_OVERRIDES[row["sourceText"]]
        section = payload.get(section_name, [])
        if index >= len(section):
            continue
        entry = section[index]
        if not isinstance(entry, dict) or len(entry) != 1:
            continue
        current_key, value = next(iter(entry.items()))
        if current_key == translated_key:
            continue
        section[index] = {translated_key: value}
        updated += 1

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent="\t") + "\n",
        encoding="utf-8",
    )
    return updated


def main() -> None:
    for path in CSV_PATHS:
        contents_updated, item_names_updated = update_csv(path)
        print(
            f"{path.name}: contents_items_updated={contents_updated}, "
            f"item_names_updated={item_names_updated}"
        )
    print(f"contents_items.json updated={update_contents_items_json()}")
    print(f"item_names.json updated={update_item_names_json()}")
    print(f"contents_monsters.json updated={update_contents_monsters_json()}")


if __name__ == "__main__":
    main()
