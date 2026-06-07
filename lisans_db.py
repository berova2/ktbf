"""
KKTC Bisiklet Federasyonu – Lisans Kayıt Sistemi
=================================================
Dayandığı talimatlar:
  • Sporcu Lisans, Tescil, Vize, Transfer ve Uluslararası Yarış Talimatı
  • Yabancı Uyruklu ve Misafir Sporcu Lisans, Tescil ve Yarışma Talimatı
  • Yabancı Federasyon Lisanslı KKTC Vatandaşı Sporcular Talimatı
  • Spor Kulüplerinin Yeniden Üyelik ve Aktif Kayıt Talimatı

Veritabanı: temp/lisans.db (SQLite)
"""

import sqlite3
import os
from contextlib import contextmanager
from datetime import date
from typing import Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "temp", "lisans.db")


# ---------------------------------------------------------------------------
# Bağlantı yönetimi
# ---------------------------------------------------------------------------

@contextmanager
def get_conn():
    """Bağlantı context manager – commit / rollback otomatik."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Veritabanı başlatma
# ---------------------------------------------------------------------------

DDL = """
-- -------------------------------------------------------
-- Kulüpler (Üyelik Talimatı Madde 5-6)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS kulupler (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    ad               TEXT    NOT NULL,
    yetkili_adi      TEXT,
    telefon          TEXT,
    adres            TEXT,
    email            TEXT,
    forma_renk       TEXT,
    aidat_odendi     INTEGER NOT NULL DEFAULT 0 CHECK(aidat_odendi IN (0,1)),
    sezon            TEXT,
    durum            TEXT    NOT NULL DEFAULT 'Aktif'
                             CHECK(durum IN ('Aktif','Pasif','Askıda')),
    kayit_tarihi     TEXT    NOT NULL DEFAULT (date('now'))
);

-- -------------------------------------------------------
-- Sporcular (Lisans Talimatı Madde 7, EK-1, EK-5)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS sporcular (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    ad                      TEXT    NOT NULL,
    soyad                   TEXT    NOT NULL,
    kimlik_no               TEXT    NOT NULL UNIQUE,
    dogum_tarihi            TEXT,
    uyruk                   TEXT    NOT NULL DEFAULT 'KKTC',
    pasaport_no             TEXT,
    telefon                 TEXT,
    email                   TEXT,
    adres                   TEXT,
    -- Madde 7A: Spor Dairesi Bilgi Yönetim Sistemi kaydı zorunludur
    spor_dairesi_kayitli    INTEGER NOT NULL DEFAULT 0 CHECK(spor_dairesi_kayitli IN (0,1)),
    kayit_tarihi            TEXT    NOT NULL DEFAULT (date('now'))
);

-- -------------------------------------------------------
-- Veli Bilgileri (EK-7: Veli Muvafakatname Formu)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS veli_bilgileri (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sporcu_id   INTEGER NOT NULL UNIQUE REFERENCES sporcular(id) ON DELETE CASCADE,
    ad_soyad    TEXT    NOT NULL,
    telefon     TEXT,
    adres       TEXT
);

-- -------------------------------------------------------
-- Lisanslar (Lisans Talimatı Madde 4-7, EK-5)
-- Kulüp lisansı veya ferdi lisans (kulup_id NULL olabilir)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS lisanslar (
    id                          INTEGER PRIMARY KEY AUTOINCREMENT,
    lisans_no                   TEXT    UNIQUE,
    sporcu_id                   INTEGER NOT NULL REFERENCES sporcular(id) ON DELETE RESTRICT,
    kulup_id                    INTEGER REFERENCES kulupler(id) ON DELETE RESTRICT,
    lisans_turu                 TEXT    NOT NULL
                                        CHECK(lisans_turu IN (
                                            'Ulusal','Uluslararası','Ferdi',
                                            'Geçici','MisafirSporcu','GeçiciYarışİzni'
                                        )),
    sezon                       TEXT    NOT NULL,
    basvuru_tarihi              TEXT    NOT NULL DEFAULT (date('now')),
    tescil_tarihi               TEXT,
    federasyon_onay_tarihi      TEXT,
    gecerlilik_bitis            TEXT,
    durum                       TEXT    NOT NULL DEFAULT 'Aktif'
                                        CHECK(durum IN ('Aktif','Pasif','İptal','Askıda')),
    -- Başvuru belgeleri kontrol listesi (Madde 7, EK-1)
    saglik_raporu               INTEGER NOT NULL DEFAULT 0 CHECK(saglik_raporu IN (0,1)),
    veli_muvafakati             INTEGER NOT NULL DEFAULT 0 CHECK(veli_muvafakati IN (0,1)),
    -- Madde 8: Başka federasyon beyanı
    baska_federasyon_beyani     INTEGER NOT NULL DEFAULT 0 CHECK(baska_federasyon_beyani IN (0,1)),
    lisans_ucreti_odendi        INTEGER NOT NULL DEFAULT 0 CHECK(lisans_ucreti_odendi IN (0,1)),
    notlar                      TEXT
);

-- -------------------------------------------------------
-- Yabancı Federasyon Lisansları
-- (Yabancı Federasyon Lisanslı KKTC Vatandaşı Sporcular Talimatı
--  Madde 4, EK-1)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS yabanci_lisanslar (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    sporcu_id           INTEGER NOT NULL REFERENCES sporcular(id) ON DELETE CASCADE,
    yabanci_federasyon  TEXT    NOT NULL,
    kulup               TEXT,
    lisans_no           TEXT,
    gecerlilik_tarihi   TEXT,
    beyan_tarihi        TEXT    NOT NULL DEFAULT (date('now')),
    -- Madde 8: Kulüp muvafakati (kulüp lisanslı sporcular için)
    kulup_muvafakati    INTEGER NOT NULL DEFAULT 0 CHECK(kulup_muvafakati IN (0,1))
);

-- -------------------------------------------------------
-- Transferler (Lisans Talimatı Madde 9)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS transferler (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    sporcu_id               INTEGER NOT NULL REFERENCES sporcular(id) ON DELETE RESTRICT,
    eski_kulup_id           INTEGER NOT NULL REFERENCES kulupler(id) ON DELETE RESTRICT,
    yeni_kulup_id           INTEGER NOT NULL REFERENCES kulupler(id) ON DELETE RESTRICT,
    transfer_tarihi         TEXT    NOT NULL DEFAULT (date('now')),
    ilizsizlik_belgesi      INTEGER NOT NULL DEFAULT 0 CHECK(ilizsizlik_belgesi IN (0,1)),
    federasyon_onay_tarihi  TEXT,
    durum                   TEXT    NOT NULL DEFAULT 'Beklemede'
                                    CHECK(durum IN ('Beklemede','Onaylandı','Reddedildi'))
);

-- -------------------------------------------------------
-- Yurt Dışı Yarış İzinleri (Lisans Talimatı Madde 10-11, EK-3)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS yurtdisi_yaris_izinleri (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    sporcu_id               INTEGER NOT NULL REFERENCES sporcular(id) ON DELETE RESTRICT,
    lisans_id               INTEGER NOT NULL REFERENCES lisanslar(id) ON DELETE RESTRICT,
    yaris_adi               TEXT    NOT NULL,
    ulke                    TEXT    NOT NULL,
    kulup_organizasyon      TEXT,
    yaris_tarihi            TEXT,
    basvuru_tarihi          TEXT    NOT NULL DEFAULT (date('now')),
    kulup_yazisi            INTEGER NOT NULL DEFAULT 0 CHECK(kulup_yazisi IN (0,1)),
    federasyon_izin_tarihi  TEXT,
    durum                   TEXT    NOT NULL DEFAULT 'Beklemede'
                                    CHECK(durum IN ('Beklemede','Onaylandı','Reddedildi'))
);

-- -------------------------------------------------------
-- Vizeler / Lisans Yenileme (Lisans Talimatı EK-4)
-- -------------------------------------------------------
CREATE TABLE IF NOT EXISTS vizeler (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    lisans_id               INTEGER NOT NULL REFERENCES lisanslar(id) ON DELETE RESTRICT,
    sporcu_id               INTEGER NOT NULL REFERENCES sporcular(id) ON DELETE RESTRICT,
    sezon                   TEXT    NOT NULL,
    basvuru_tarihi          TEXT    NOT NULL DEFAULT (date('now')),
    saglik_raporu           INTEGER NOT NULL DEFAULT 0 CHECK(saglik_raporu IN (0,1)),
    eski_lisans_teslim      INTEGER NOT NULL DEFAULT 0 CHECK(eski_lisans_teslim IN (0,1)),
    kulup_yetkilisi         TEXT,
    federasyon_onay_tarihi  TEXT,
    durum                   TEXT    NOT NULL DEFAULT 'Beklemede'
                                    CHECK(durum IN ('Beklemede','Onaylandı','Reddedildi'))
);
"""


def init_db():
    """Veritabanını ve tüm tabloları oluşturur."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_conn() as conn:
        conn.executescript(DDL)
    print(f"Veritabanı hazır: {DB_PATH}")


# ---------------------------------------------------------------------------
# Kulüp işlemleri
# ---------------------------------------------------------------------------

def kulup_ekle(ad: str, yetkili_adi: str = None, telefon: str = None,
               adres: str = None, email: str = None, forma_renk: str = None,
               sezon: str = None) -> int:
    """Yeni kulüp kaydı ekler; döndürülen değer yeni satırın id'sidir."""
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO kulupler (ad, yetkili_adi, telefon, adres, email,
               forma_renk, sezon)
               VALUES (?,?,?,?,?,?,?)""",
            (ad, yetkili_adi, telefon, adres, email, forma_renk, sezon)
        )
        return cur.lastrowid


def kulup_guncelle(kulup_id: int, **kwargs) -> None:
    """Verilen alanları günceller. Geçerli alanlar: ad, yetkili_adi, telefon,
    adres, email, forma_renk, aidat_odendi, sezon, durum."""
    izin = {"ad","yetkili_adi","telefon","adres","email",
            "forma_renk","aidat_odendi","sezon","durum"}
    sutunlar = {k: v for k, v in kwargs.items() if k in izin}
    if not sutunlar:
        return
    set_ifade = ", ".join(f"{k}=?" for k in sutunlar)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE kulupler SET {set_ifade} WHERE id=?",
            (*sutunlar.values(), kulup_id)
        )


def kulup_getir(kulup_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM kulupler WHERE id=?", (kulup_id,)).fetchone()


def kulupler_listele(durum: str = None) -> list:
    with get_conn() as conn:
        if durum:
            return conn.execute(
                "SELECT * FROM kulupler WHERE durum=? ORDER BY ad", (durum,)
            ).fetchall()
        return conn.execute("SELECT * FROM kulupler ORDER BY ad").fetchall()


def kulupler_dropdown() -> list:
    """GUI combobox için aktif kulüplerin (id, ad) listesini döner."""
    with get_conn() as conn:
        return conn.execute(
            "SELECT id, ad FROM kulupler WHERE durum='Aktif' ORDER BY ad"
        ).fetchall()


# ---------------------------------------------------------------------------
# Sporcu işlemleri
# ---------------------------------------------------------------------------

def sporcu_ekle(ad: str, soyad: str, kimlik_no: str,
                dogum_tarihi: str = None, uyruk: str = "KKTC",
                pasaport_no: str = None, telefon: str = None,
                email: str = None, adres: str = None,
                spor_dairesi_kayitli: int = 0) -> int:
    """
    Yeni sporcu kaydı ekler.
    UYARI (Lisans Talimatı Madde 7A): spor_dairesi_kayitli=0 olan sporcular
    adına lisans işlemi yapılamaz.
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO sporcular
               (ad, soyad, kimlik_no, dogum_tarihi, uyruk, pasaport_no,
                telefon, email, adres, spor_dairesi_kayitli)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (ad, soyad, kimlik_no, dogum_tarihi, uyruk, pasaport_no,
             telefon, email, adres, spor_dairesi_kayitli)
        )
        return cur.lastrowid


def sporcu_guncelle(sporcu_id: int, **kwargs) -> None:
    izin = {"ad","soyad","kimlik_no","dogum_tarihi","uyruk","pasaport_no",
            "telefon","email","adres","spor_dairesi_kayitli"}
    sutunlar = {k: v for k, v in kwargs.items() if k in izin}
    if not sutunlar:
        return
    set_ifade = ", ".join(f"{k}=?" for k in sutunlar)
    with get_conn() as conn:
        conn.execute(
            f"UPDATE sporcular SET {set_ifade} WHERE id=?",
            (*sutunlar.values(), sporcu_id)
        )


def sporcu_getir(sporcu_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM sporcular WHERE id=?", (sporcu_id,)).fetchone()


def sporcu_ara(kimlik_no: str = None, ad_soyad: str = None) -> list:
    """Kimlik no veya ad/soyad ile arama yapar."""
    with get_conn() as conn:
        if kimlik_no:
            return conn.execute(
                "SELECT * FROM sporcular WHERE kimlik_no=?", (kimlik_no,)
            ).fetchall()
        if ad_soyad:
            pattern = f"%{ad_soyad}%"
            return conn.execute(
                "SELECT * FROM sporcular WHERE (ad || ' ' || soyad) LIKE ?",
                (pattern,)
            ).fetchall()
        return []


def veli_ekle(sporcu_id: int, ad_soyad: str,
              telefon: str = None, adres: str = None) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO veli_bilgileri (sporcu_id, ad_soyad, telefon, adres) VALUES (?,?,?,?)",
            (sporcu_id, ad_soyad, telefon, adres)
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Lisans işlemleri
# ---------------------------------------------------------------------------

def _spor_dairesi_kontrol(sporcu_id: int, conn: sqlite3.Connection) -> None:
    """Madde 7A uyarınca Spor Dairesi kaydı yoksa hata fırlatır."""
    row = conn.execute(
        "SELECT spor_dairesi_kayitli FROM sporcular WHERE id=?", (sporcu_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"Sporcu bulunamadı: id={sporcu_id}")
    if not row["spor_dairesi_kayitli"]:
        raise ValueError(
            f"Sporcu (id={sporcu_id}) Spor Dairesi Bilgi Yönetim Sistemine kayıtlı değil. "
            "Lisans işlemi yapılamaz. (Lisans Talimatı Madde 7A)"
        )


def lisans_ekle(sporcu_id: int, lisans_turu: str, sezon: str,
                kulup_id: int = None, lisans_no: str = None,
                tescil_tarihi: str = None, federasyon_onay_tarihi: str = None,
                gecerlilik_bitis: str = None,
                saglik_raporu: int = 0, veli_muvafakati: int = 0,
                baska_federasyon_beyani: int = 0,
                lisans_ucreti_odendi: int = 0,
                notlar: str = None) -> int:
    """
    Yeni lisans kaydı ekler.
    Spor Dairesi kaydı zorunluluğunu (Madde 7A) otomatik denetler.
    """
    with get_conn() as conn:
        _spor_dairesi_kontrol(sporcu_id, conn)
        cur = conn.execute(
            """INSERT INTO lisanslar
               (lisans_no, sporcu_id, kulup_id, lisans_turu, sezon,
                tescil_tarihi, federasyon_onay_tarihi, gecerlilik_bitis,
                saglik_raporu, veli_muvafakati, baska_federasyon_beyani,
                lisans_ucreti_odendi, notlar)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (lisans_no, sporcu_id, kulup_id, lisans_turu, sezon,
             tescil_tarihi, federasyon_onay_tarihi, gecerlilik_bitis,
             saglik_raporu, veli_muvafakati, baska_federasyon_beyani,
             lisans_ucreti_odendi, notlar)
        )
        lid = cur.lastrowid
        if lisans_no is None:
            auto_no = f"{sezon}-{lid:03d}"
            conn.execute("UPDATE lisanslar SET lisans_no=? WHERE id=?",
                         (auto_no, lid))
        return lid


def lisans_durum_guncelle(lisans_id: int, durum: str,
                          federasyon_onay_tarihi: str = None) -> None:
    with get_conn() as conn:
        conn.execute(
            """UPDATE lisanslar SET durum=?,
               federasyon_onay_tarihi=COALESCE(?,federasyon_onay_tarihi)
               WHERE id=?""",
            (durum, federasyon_onay_tarihi, lisans_id)
        )


def lisans_getir(lisans_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM lisanslar WHERE id=?", (lisans_id,)).fetchone()


def sporcu_lisanslari(sporcu_id: int) -> list:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM lisanslar WHERE sporcu_id=? ORDER BY basvuru_tarihi DESC",
            (sporcu_id,)
        ).fetchall()


def aktif_lisanslar(sezon: str) -> list:
    """Belirtilen sezonda aktif tüm lisansları getirir."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT l.*, s.ad, s.soyad, s.kimlik_no, k.ad AS kulup_adi
               FROM lisanslar l
               JOIN sporcular s ON s.id = l.sporcu_id
               LEFT JOIN kulupler k ON k.id = l.kulup_id
               WHERE l.sezon=? AND l.durum='Aktif'
               ORDER BY s.soyad, s.ad""",
            (sezon,)
        ).fetchall()


# ---------------------------------------------------------------------------
# Yabancı Federasyon Lisansı
# ---------------------------------------------------------------------------

def yabanci_lisans_ekle(sporcu_id: int, yabanci_federasyon: str,
                        kulup: str = None, lisans_no: str = None,
                        gecerlilik_tarihi: str = None,
                        kulup_muvafakati: int = 0) -> int:
    """
    KKTC vatandaşı sporcunun yabancı federasyon lisansını kaydeder.
    (Yabancı Federasyon Lisanslı KKTC Vatandaşı Sporcular Talimatı Madde 4)
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO yabanci_lisanslar
               (sporcu_id, yabanci_federasyon, kulup, lisans_no,
                gecerlilik_tarihi, kulup_muvafakati)
               VALUES (?,?,?,?,?,?)""",
            (sporcu_id, yabanci_federasyon, kulup, lisans_no,
             gecerlilik_tarihi, kulup_muvafakati)
        )
        return cur.lastrowid


# ---------------------------------------------------------------------------
# Transfer işlemleri
# ---------------------------------------------------------------------------

def transfer_ekle(sporcu_id: int, eski_kulup_id: int, yeni_kulup_id: int,
                  ilizsizlik_belgesi: int = 0) -> int:
    """
    Transfer başvurusu oluşturur. (Lisans Talimatı Madde 9)
    İlişiksizlik belgesi zorunludur.
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO transferler
               (sporcu_id, eski_kulup_id, yeni_kulup_id, ilizsizlik_belgesi)
               VALUES (?,?,?,?)""",
            (sporcu_id, eski_kulup_id, yeni_kulup_id, ilizsizlik_belgesi)
        )
        return cur.lastrowid


def transfer_onayla(transfer_id: int) -> None:
    """Transferi onaylar ve sporcunun aktif lisansını günceller."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM transferler WHERE id=?", (transfer_id,)
        ).fetchone()
        if row is None:
            raise ValueError(f"Transfer bulunamadı: id={transfer_id}")
        today = date.today().isoformat()
        conn.execute(
            """UPDATE transferler
               SET durum='Onaylandı', federasyon_onay_tarihi=?
               WHERE id=?""",
            (today, transfer_id)
        )
        # Aktif lisansın kulübünü güncelle
        conn.execute(
            """UPDATE lisanslar SET kulup_id=?
               WHERE sporcu_id=? AND durum='Aktif'""",
            (row["yeni_kulup_id"], row["sporcu_id"])
        )


# ---------------------------------------------------------------------------
# Yurt Dışı Yarış İzni
# ---------------------------------------------------------------------------

def yurtdisi_izin_ekle(sporcu_id: int, lisans_id: int, yaris_adi: str,
                       ulke: str, kulup_organizasyon: str = None,
                       yaris_tarihi: str = None,
                       kulup_yazisi: int = 0) -> int:
    """
    Yurt dışı yarış izin başvurusu oluşturur. (Lisans Talimatı Madde 10, EK-3)
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO yurtdisi_yaris_izinleri
               (sporcu_id, lisans_id, yaris_adi, ulke,
                kulup_organizasyon, yaris_tarihi, kulup_yazisi)
               VALUES (?,?,?,?,?,?,?)""",
            (sporcu_id, lisans_id, yaris_adi, ulke,
             kulup_organizasyon, yaris_tarihi, kulup_yazisi)
        )
        return cur.lastrowid


def yurtdisi_izin_onayla(izin_id: int) -> None:
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """UPDATE yurtdisi_yaris_izinleri
               SET durum='Onaylandı', federasyon_izin_tarihi=?
               WHERE id=?""",
            (today, izin_id)
        )


# ---------------------------------------------------------------------------
# Vize / Lisans Yenileme
# ---------------------------------------------------------------------------

def vize_ekle(lisans_id: int, sporcu_id: int, sezon: str,
              saglik_raporu: int = 0, eski_lisans_teslim: int = 0,
              kulup_yetkilisi: str = None) -> int:
    """
    Lisans yenileme (vize) başvurusu oluşturur. (Lisans Talimatı EK-4)
    """
    with get_conn() as conn:
        cur = conn.execute(
            """INSERT INTO vizeler
               (lisans_id, sporcu_id, sezon, saglik_raporu,
                eski_lisans_teslim, kulup_yetkilisi)
               VALUES (?,?,?,?,?,?)""",
            (lisans_id, sporcu_id, sezon, saglik_raporu,
             eski_lisans_teslim, kulup_yetkilisi)
        )
        return cur.lastrowid


def vize_onayla(vize_id: int) -> None:
    today = date.today().isoformat()
    with get_conn() as conn:
        conn.execute(
            """UPDATE vizeler
               SET durum='Onaylandı', federasyon_onay_tarihi=?
               WHERE id=?""",
            (today, vize_id)
        )


# ---------------------------------------------------------------------------
# Raporlama sorguları
# ---------------------------------------------------------------------------

def spor_dairesi_kayitsiz_sporcular() -> list:
    """
    Spor Dairesi Bilgi Yönetim Sistemine kayıtlı olmayan sporcuları listeler.
    (Lisans Talimatı Madde 7A)
    """
    with get_conn() as conn:
        return conn.execute(
            """SELECT * FROM sporcular
               WHERE spor_dairesi_kayitli=0
               ORDER BY soyad, ad"""
        ).fetchall()


def bekleyen_transferler() -> list:
    with get_conn() as conn:
        return conn.execute(
            """SELECT t.*, s.ad, s.soyad,
                      ek.ad AS eski_kulup, yk.ad AS yeni_kulup
               FROM transferler t
               JOIN sporcular s ON s.id = t.sporcu_id
               JOIN kulupler ek ON ek.id = t.eski_kulup_id
               JOIN kulupler yk ON yk.id = t.yeni_kulup_id
               WHERE t.durum='Beklemede'
               ORDER BY t.transfer_tarihi"""
        ).fetchall()


def bekleyen_yurtdisi_izinler() -> list:
    with get_conn() as conn:
        return conn.execute(
            """SELECT y.*, s.ad, s.soyad
               FROM yurtdisi_yaris_izinleri y
               JOIN sporcular s ON s.id = y.sporcu_id
               WHERE y.durum='Beklemede'
               ORDER BY y.yaris_tarihi"""
        ).fetchall()


def kulup_sporcu_sayilari(sezon: str) -> list:
    """Sezon bazında kulüp başına aktif lisanslı sporcu sayısı."""
    with get_conn() as conn:
        return conn.execute(
            """SELECT k.ad AS kulup, COUNT(l.id) AS sporcu_sayisi
               FROM kulupler k
               LEFT JOIN lisanslar l
                 ON l.kulup_id = k.id AND l.sezon=? AND l.durum='Aktif'
               GROUP BY k.id, k.ad
               ORDER BY sporcu_sayisi DESC""",
            (sezon,)
        ).fetchall()


if __name__ == "__main__":
    init_db()
    print(f"Veri tabanı hazır: {DB_PATH}")
