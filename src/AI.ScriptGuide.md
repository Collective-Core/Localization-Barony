# AI Script Guide

Цей файл описує, як AI-агентам працювати зі скриптами локалізації Barony в цьому репозиторії.

## Layout

- Робоча директорія репозиторію: корінь цього репозиторію.
- Робоча папка моду, куди мають записуватися застосовані переклади: `Barony Ukrainian Localization`
- Дані перекладу: `src/Data`
- Скрипти високого рівня: `src/scripts`
- Низькорівневі скрипти заміни тексту лежать у `src/scripts`. Не вигадуй власну заміну JSON-значень і не форматуй JSON автоматично.

## Головне Правило

JSON-файли Barony потрібно вважати layout-sensitive. Не проганяй їх через formatter, Prettier, IDE formatter або `json.dump` для перезапису всього файла. Якщо треба змінювати мод-файли, міняй тільки текстові значення й зберігай:

- порядок ключів;
- таби та пробіли;
- переноси рядків;
- inline-масиви;
- компактні записи;
- розташування `{`, `}`, `[`, `]`.

## Дані CSV

Основні файли:

- `src/Data/Strings.csv` — реальні перекладні рядки.
- `src/Data/Strings.Technical.csv` — технічні рядки, які не мають потрапляти в звичайний переклад.
- `src/Data/Strings.All.csv` — повний об'єднаний набір рядків.
- `src/Data/Glossary.Core.csv`, `Glossary.Names.csv`, `Glossary.Technical.csv` — глосарії.

Для звичайної роботи з перекладом редагуй переважно `translatedText` у `Strings.csv`. Не змінюй `id`, `key`, `relativeFilePath`, `fileFormat`, `lineNumber`, `locator`, `sourceText`, `techHash` без окремої причини.

## Типовий Workflow

1. Перевірити якість CSV:

```powershell
python src\scripts\validate_translations.py
```

2. Перевірити консистентність повторюваних термінів:

```powershell
python src\scripts\check_translation_consistency.py
```

3. За потреби оновити кандидатів у глосарій:

```powershell
python src\scripts\extract_glossary_candidates.py
python src\scripts\extract_name_glossary.py
python src\scripts\extract_technical_glossary.py
```

4. Якщо змінився набір файлів моду або треба перечитати рядки з моду:

```powershell
python src\scripts\extract_strings.py
```

Після extraction уважно перевір зміни в `src/Data/*.csv`. Скрипт може оновити набір рядків, тому не приймай зміни наосліп.

## Скрипти

- `extract_strings.py` — витягує текстові рядки з `Barony Ukrainian Localization` у CSV.
- `validate_translations.py` — перевіряє placeholders, escape-послідовності, контрольні маркери й порожні переклади.
- `check_translation_consistency.py` — шукає несинхронні переклади однакових або пов'язаних рядків.
- `extract_glossary_candidates.py` — збирає кандидатів для глосарію з CSV та compendium.
- `extract_name_glossary.py` — витягує назви й імена для окремого глосарію.
- `extract_technical_glossary.py` — витягує технічні терміни, які важливо не ламати.
- `polish_contents_items_names.py` — допоміжний скрипт для синхронізації назв предметів у compendium/item name даних.
- `apply_translations_to_sources.py` — застосовує `src/Data/Strings.csv` напряму до робочого моду `Barony Ukrainian Localization`, зберігаючи layout-sensitive JSON.
- `split_strings_csv.py` — розділяє `Strings.All.csv` на перекладні й технічні рядки.

## Що Не Робити

- Не перекладай технічні поля, asset paths, font/image/model/music references.
- Не змінюй `word_highlights` без перевірки, що індекси не виходять за кількість слів у тексті.
- Не видаляй рядки з `Strings.Technical.csv`, якщо вони виглядають "неперекладними": це очікувано.
- Не запускай автоматичне форматування JSON.
- Не змішуй стару `Barony Ukraine Localization` з актуальною `Barony Ukrainian Localization`.

## Мінімальна Перевірка Перед Завершенням

Перед фінальною відповіддю після зміни CSV або скриптів запусти:

```powershell
python src\scripts\validate_translations.py
python src\scripts\check_translation_consistency.py
```

Якщо змінювалися самі скрипти, додатково:

```powershell
Get-ChildItem src\scripts\*.py | ForEach-Object { python -m py_compile $_.FullName }
```
