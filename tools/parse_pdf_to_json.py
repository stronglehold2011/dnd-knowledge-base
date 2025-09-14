# tools/parse_pdf_to_json.py
# Конвертация PDF (раздел "Расы" редакции Theon Greyjoy) → data/races.json
# Логика: после первых base_offset страниц (обложка/оглавление) каждая следующая страница = 1 раса.
# Использование:
#   python tools/parse_pdf_to_json.py /path/to/Расы.pdf data/races.json --base-offset 2

from __future__ import annotations

import sys
import re
import json
import unicodedata
import argparse
import os

try:
    import fitz  # PyMuPDF
except Exception:
    print("Нужно установить зависимость: pip install pymupdf")
    raise


# Список рас в ТОМ ЖЕ порядке, как на страницах PDF после оглавления.
ANCHORS = [
    "Гномы", "Люди", "Дроу", "Зверолюды", "Демоны",
    "Эльфы", "Хоббиты", "Лотары", "Орки", "Циклопы",
    "Огры", "Нордиры", "Ринка", "Саури", "Тролли",
]


def slugify(value: str) -> str:
    """ASCII slug из названия (для ссылок/файлов)."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value or "item"


def parse_traits(text: str) -> list[dict]:
    """
    Пытаемся выделить секцию 'Расовые бонусы и недостатки' с простыми эвристиками:
    - Ищем заголовок 'Расовые бонусы и недостатки'
    - Каждая строка вида 'Название: описание' считается трейтом (название не слишком длинное, начинается с заглавной)
    """
    parts = text.split("Расовые бонусы и недостатки")
    if len(parts) < 2:
        return []

    tail = parts[1]
    lines = [l.strip() for l in tail.splitlines() if l.strip()]

    traits = []
    cur_t, cur_b = None, []
    for ln in lines:
        if ":" in ln and ln[0].isupper() and len(ln.split(":", 1)[0]) < 40:
            if cur_t:
                traits.append({"title": cur_t, "text": " ".join(cur_b).strip()})
                cur_b = []
            title, body = ln.split(":", 1)
            cur_t = title.strip()
            body = body.strip()
            if body:
                cur_b.append(body)
        else:
            cur_b.append(ln)
    if cur_t:
        traits.append({"title": cur_t, "text": " ".join(cur_b).strip()})
    return traits


def extract_quote(text: str) -> str | None:
    """Ищем цитату вида “…” или "..." внутри страницы."""
    m = re.search(r"“([^”]+)”|\"([^\"]+)\"", text)
    if not m:
        return None
    return m.group(1) if m.group(1) else m.group(2)


def parse(pdf_path: str, base_offset: int = 2) -> list[dict]:
    """
    Читает PDF и формирует races.json.
    - base_offset: сколько страниц с начала пропускаем (обложка + оглавление и т.п.).
    - Для i-й расы берём страницу (base_offset + i) — нумерация страниц в PDF с 1,
      а у PyMuPDF индексы с 0 → страница = doc[base_offset + i - 1], см. ниже.
    """
    doc = fitz.open(pdf_path)

    races: list[dict] = []

    for i, name in enumerate(ANCHORS):
        page_number = base_offset + i            # номер страницы как видит браузер (1..N)
        page_index = page_number - 1             # индекс для PyMuPDF (0..N-1)

        if page_index < 0 or page_index >= len(doc):
            # На случай, если PDF короче ожидаемого
            print(f"[warn] Страницы для '{name}' нет (index={page_index}). Пропускаю.")
            continue

        page = doc[page_index]
        page_text = page.get_text("text").strip()

        # Грубое описание — текст до секции с трейтов, либо весь текст страницы
        parts = page_text.split("Расовые бонусы и недостатки")
        description = parts[0].strip()
        summary = " ".join(description.split()[:40])
        quote = extract_quote(page_text)
        traits = parse_traits(page_text)

        races.append({
            "name": name,
            "slug": slugify(name),
            "quote": quote,
            "summary": summary,
            "description": description,
            "traits": traits,
            "page": page_number,   # ← ключ для фронта: открывать PDF на этой странице
        })

    return races


def main():
    p = argparse.ArgumentParser(description="Парсер PDF (Расы) → races.json c номерами страниц.")
    p.add_argument("pdf_path", help="Путь к PDF с расами")
    p.add_argument("out_path", help="Куда сохранить data/races.json")
    p.add_argument("--base-offset", type=int, default=2,
                   help="Сколько начальных страниц пропустить (обложка+оглавление). Пример: если первая раса на стр. 3 → 2")
    args = p.parse_args()

    races = parse(args.pdf_path, base_offset=args.base_offset)
    os.makedirs(os.path.dirname(args.out_path) or ".", exist_ok=True)
    with open(args.out_path, "w", encoding="utf-8") as f:
        json.dump(races, f, ensure_ascii=False, indent=2)

    print(f"OK: {len(races)} рас → {args.out_path} (offset={args.base_offset})")


if __name__ == "__main__":
    main()
