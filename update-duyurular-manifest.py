"""Yari-otomatik WhatsApp metni -> Duyurular manifest guncelleyici.

Kullanim ornekleri:
  python update-duyurular-manifest.py
  python update-duyurular-manifest.py --text-file temp\whatsapp.txt
  python update-duyurular-manifest.py --date 2026-06-12 --title "Baslik" --content "Icerik" --link "https://..."
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
DATE_DMY_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{4})\b")
DATE_YMD_RE = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="WhatsApp metninden duyuru cikarip Duyurular/manifest.json dosyasina ekler."
    )
    parser.add_argument(
        "--manifest",
        default="Duyurular/manifest.json",
        help="Manifest dosya yolu (varsayilan: Duyurular/manifest.json)",
    )
    parser.add_argument(
        "--text-file",
        help="WhatsApp metninin okunacagi txt dosyasi",
    )
    parser.add_argument("--date", help="ISO tarih (YYYY-MM-DD)")
    parser.add_argument("--title", help="Duyuru basligi")
    parser.add_argument("--content", help="Duyuru metni")
    parser.add_argument("--link", help="Duyuru linki")
    parser.add_argument(
        "--yes",
        action="store_true",
        help="Onay sormadan kaydet",
    )
    return parser.parse_args()


def read_text_interactive() -> str:
    print("WhatsApp metnini yapistirin. Bitirmek icin tek satira EOF yazip Enter'a basin.")
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "EOF":
            break
        lines.append(line)
    return "\n".join(lines).strip()


def normalize_text(value: str) -> str:
    # Fazla bosluklari sadeleştirir ama satirlari korur.
    lines = [ln.rstrip() for ln in value.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(lines).strip()


def detect_link(text: str) -> str:
    match = URL_RE.search(text)
    return match.group(0) if match else ""


def detect_date(text: str) -> str:
    ymd = DATE_YMD_RE.search(text)
    if ymd:
        y, m, d = ymd.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    dmy = DATE_DMY_RE.search(text)
    if dmy:
        d, m, y = dmy.groups()
        return f"{int(y):04d}-{int(m):02d}-{int(d):02d}"

    return date.today().isoformat()


def remove_links(text: str) -> str:
    return URL_RE.sub("", text)


def detect_title_and_content(text: str) -> tuple[str, str]:
    cleaned = remove_links(text)
    lines = [ln.strip() for ln in cleaned.split("\n") if ln.strip()]

    if not lines:
        return "Duyuru", ""

    # Ilk anlamli satiri baslik yap.
    title = lines[0]
    if len(title) > 90:
        title = title[:87].rstrip() + "..."

    # Icerik olarak tum satirlari birlestir.
    content = " ".join(lines)
    content = re.sub(r"\s+", " ", content).strip()

    return title, content


def load_manifest(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    raw = path.read_text(encoding="utf-8")
    if not raw.strip():
        return []

    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Manifest bir JSON liste olmalidir.")

    valid_items: list[dict[str, Any]] = []
    for item in data:
        if isinstance(item, dict):
            valid_items.append(item)
    return valid_items


def save_manifest(path: Path, items: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(items, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def build_record(args: argparse.Namespace, text: str) -> dict[str, str]:
    detected_link = detect_link(text)
    detected_date = detect_date(text)
    detected_title, detected_content = detect_title_and_content(text)

    return {
        "date": (args.date or detected_date or date.today().isoformat()).strip(),
        "title": (args.title or detected_title or "Duyuru").strip(),
        "content": (args.content or detected_content or "").strip(),
        "link": (args.link or detected_link or "").strip(),
    }


def prompt_edit_defaults(record: dict[str, str]) -> dict[str, str]:
    print("\nAlgilanan alanlar (Enter = mevcut degeri koru):")

    new_date = input(f"Tarih [{record['date']}]: ").strip()
    if new_date:
        record["date"] = new_date

    new_title = input(f"Baslik [{record['title']}]: ").strip()
    if new_title:
        record["title"] = new_title

    new_content = input(f"Icerik [{record['content'][:70]}{'...' if len(record['content']) > 70 else ''}]: ").strip()
    if new_content:
        record["content"] = new_content

    new_link = input(f"Link [{record['link']}]: ").strip()
    if new_link:
        record["link"] = new_link

    return record


def main() -> None:
    args = parse_args()
    manifest_path = Path(args.manifest)

    if args.text_file:
        source_text = Path(args.text_file).read_text(encoding="utf-8")
    else:
        source_text = read_text_interactive()

    source_text = normalize_text(source_text)

    # Komut satirinda tum alanlar verilmediyse metinden tahmin edip duzeltme imkani sun.
    record = build_record(args, source_text)

    if not (args.date and args.title and args.content and args.link):
        record = prompt_edit_defaults(record)

    if not record["title"]:
        raise SystemExit("Baslik bos olamaz.")

    items = load_manifest(manifest_path)
    items.insert(0, record)

    print("\nEklenecek duyuru:")
    print(json.dumps(record, ensure_ascii=False, indent=2))

    if not args.yes:
        onay = input("\nKaydetmek istiyor musunuz? (e/h): ").strip().lower()
        if onay not in {"e", "evet", "y", "yes"}:
            print("Iptal edildi.")
            return

    save_manifest(manifest_path, items)
    print(f"Kaydedildi: {manifest_path}")


if __name__ == "__main__":
    main()
