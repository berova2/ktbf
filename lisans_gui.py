"""
KKTC Bisiklet Federasyonu – Kulüp ve Sporcu Kayıt Arayüzü
==========================================================
Kullanım: python lisans_gui.py
"""

import os
import sys
import ctypes
from datetime import date
import tkinter as tk
from tkinter import ttk, messagebox
import lisans_db as db

# ---------------------------------------------------------------------------
# Renk / stil sabitleri
# ---------------------------------------------------------------------------
BG       = "#f4f6f9"
HEADER   = "#1a3c6e"
ACCENT   = "#2563eb"
ROW_ODD  = "#ffffff"
ROW_EVEN = "#eef2f8"
BTN_ADD  = "#16a34a"
BTN_UPD  = "#d97706"
BTN_DEL  = "#dc2626"

BASE_SCREEN_WIDTH = 1920
BASE_SCREEN_HEIGHT = 1080
UI_SCALE = 1.0
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 13, "bold")
FONT_S   = ("Segoe UI", 8)


def _scaled(value: int) -> int:
    return max(1, int(round(value * UI_SCALE)))


def _update_ui_metrics(scale: float) -> None:
    global UI_SCALE, FONT, FONT_B, FONT_H, FONT_S

    UI_SCALE = max(0.9, min(scale, 1.35))
    body_size = _scaled(10)
    header_size = _scaled(13)
    small_size = _scaled(8)
    FONT = ("Segoe UI", body_size)
    FONT_B = ("Segoe UI", body_size, "bold")
    FONT_H = ("Segoe UI", header_size, "bold")
    FONT_S = ("Segoe UI", small_size)


def _apply_window_geometry(window: tk.Misc,
                           width_ratio: float = 0.88,
                           height_ratio: float = 0.85,
                           min_width: int = 1100,
                           min_height: int = 760) -> None:
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    width = min(max(int(screen_width * width_ratio), min_width), screen_width - 40)
    height = min(max(int(screen_height * height_ratio), min_height), screen_height - 60)
    x_pos = max((screen_width - width) // 2, 0)
    y_pos = max((screen_height - height) // 2, 0)
    window.geometry(f"{width}x{height}+{x_pos}+{y_pos}")


def _configure_display(root: tk.Tk) -> None:
    scale = min(
        root.winfo_screenwidth() / BASE_SCREEN_WIDTH,
        root.winfo_screenheight() / BASE_SCREEN_HEIGHT,
    )
    _update_ui_metrics(scale)
    _apply_window_geometry(root)
    if os.name == "nt":
        try:
            root.state("zoomed")
        except tk.TclError:
            pass


def _ensure_tcl_tk_env() -> None:
    """Windows kurulumunda eksikse Tcl/Tk kütüphane yollarını ayarlar."""
    if os.name != "nt":
        return
    if os.environ.get("TCL_LIBRARY") and os.environ.get("TK_LIBRARY"):
        return

    tcl_root = os.path.join(sys.base_prefix, "tcl")
    tcl_dir = os.path.join(tcl_root, "tcl8.6")
    tk_dir = os.path.join(tcl_root, "tk8.6")
    if os.path.isdir(tcl_dir) and os.path.isdir(tk_dir):
        os.environ.setdefault("TCL_LIBRARY", tcl_dir)
        os.environ.setdefault("TK_LIBRARY", tk_dir)


def _enable_windows_dpi_awareness() -> None:
    if os.name != "nt":
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def _style_widget(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame",       background=BG)
    style.configure("TLabel",       background=BG, font=FONT)
    style.configure("TEntry",       font=FONT, padding=_scaled(3))
    style.configure("TCombobox",    font=FONT)
    style.configure("Header.TLabel", background=HEADER, foreground="white",
                    font=FONT_H, padding=_scaled(5))
    style.configure("Treeview",      font=FONT, rowheight=_scaled(26))
    style.configure("Treeview.Heading", font=FONT_B,
                    background=HEADER, foreground="white")
    style.map("Treeview.Heading",
              background=[("active", ACCENT)])
    style.configure("Add.TButton",   font=FONT_B, background=BTN_ADD,
                    foreground="white", padding=_scaled(5))
    style.configure("Upd.TButton",   font=FONT_B, background=BTN_UPD,
                    foreground="white", padding=_scaled(5))
    style.configure("Del.TButton",   font=FONT_B, background=BTN_DEL,
                    foreground="white", padding=_scaled(5))
    style.configure("Neu.TButton",   font=FONT_B, background=ACCENT,
                    foreground="white", padding=_scaled(5))
    return style


# ---------------------------------------------------------------------------
# Yardımcı widgetlar
# ---------------------------------------------------------------------------

def _lbl_entry(parent, text, row, col=0, width=22, colspan=1):
    ttk.Label(parent, text=text).grid(row=row, column=col,
                        sticky="e", padx=(_scaled(8), _scaled(4)), pady=_scaled(4))
    var = tk.StringVar()
    e = ttk.Entry(parent, textvariable=var, width=width)
    e.grid(row=row, column=col + 1, columnspan=colspan,
        sticky="ew", padx=(0, _scaled(8)), pady=_scaled(4))
    return var


def _lbl_combo(parent, text, values, row, col=0, width=22):
    ttk.Label(parent, text=text).grid(row=row, column=col,
                                       sticky="e", padx=(_scaled(8), _scaled(4)), pady=_scaled(4))
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      width=width - 2, state="readonly")
    cb.grid(row=row, column=col + 1, sticky="ew", padx=(0, _scaled(8)), pady=_scaled(4))
    return var


def _lbl_check(parent, text, row, col=0):
    var = tk.IntVar()
    chk = ttk.Checkbutton(parent, text=text, variable=var)
    chk.grid(row=row, column=col, columnspan=2,
             sticky="w", padx=(_scaled(60), _scaled(8)), pady=_scaled(2))
    return var


def _make_tree(parent, columns: list[tuple[str, str, int]]):
    """columns: [(id, başlık, genişlik)]"""
    frame = ttk.Frame(parent)
    vsb = ttk.Scrollbar(frame, orient="vertical")
    hsb = ttk.Scrollbar(frame, orient="horizontal")
    tree = ttk.Treeview(frame,
                        columns=[c[0] for c in columns],
                        show="headings",
                        yscrollcommand=vsb.set,
                        xscrollcommand=hsb.set,
                        selectmode="browse")
    vsb.config(command=tree.yview)
    hsb.config(command=tree.xview)
    for cid, ctitle, cw in columns:
        tree.heading(cid, text=ctitle)
        tree.column(cid, width=_scaled(cw), minwidth=_scaled(40))
    vsb.pack(side="right", fill="y")
    hsb.pack(side="bottom", fill="x")
    tree.pack(fill="both", expand=True)
    tree.tag_configure("odd",  background=ROW_ODD)
    tree.tag_configure("even", background=ROW_EVEN)
    return frame, tree


def _fill_tree(tree, rows):
    tree.delete(*tree.get_children())
    for i, row in enumerate(rows):
        tag = "even" if i % 2 == 0 else "odd"
        tree.insert("", "end", iid=str(row[0]),
                    values=list(row), tags=(tag,))


# ---------------------------------------------------------------------------
# KULÜP sekmesi
# ---------------------------------------------------------------------------

class KulupSekme(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self._secili_id = None
        self._build()
        self._listele()

    def _build(self):
        ttk.Label(self, text="KULÜP KAYIT VE YÖNETİMİ",
                  style="Header.TLabel").pack(fill="x")

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=8, pady=8)

        # Sol: form
        form_frame = ttk.LabelFrame(pane, text="Kulüp Bilgileri", padding=8)
        pane.add(form_frame, weight=1)

        self.v_ad      = _lbl_entry(form_frame, "Kulüp Adı *",    0)
        self.v_yetkili = _lbl_entry(form_frame, "Yetkili Adı",    1)
        self.v_tel     = _lbl_entry(form_frame, "Telefon",        2)
        self.v_email   = _lbl_entry(form_frame, "E-posta",        3)
        self.v_adres   = _lbl_entry(form_frame, "Adres",          4)
        self.v_renk    = _lbl_entry(form_frame, "Forma Rengi",    5)
        self.v_sezon   = _lbl_entry(form_frame, "Sezon",          6, width=10)
        self.v_sezon.set("2026")
        self.v_durum   = _lbl_combo(form_frame, "Durum",
                                    ["Aktif", "Pasif", "Askıda"],  7, width=14)
        self.v_durum.set("Aktif")
        self.v_aidat   = _lbl_check(form_frame, "Aidat Ödendi",   8)

        form_frame.columnconfigure(1, weight=1)

        btn = ttk.Frame(form_frame)
        btn.grid(row=9, column=0, columnspan=2, pady=(12, 4))
        ttk.Button(btn, text="➕ Kaydet",  style="Add.TButton",
                   command=self._kaydet).pack(side="left", padx=4)
        ttk.Button(btn, text="✏️ Güncelle", style="Upd.TButton",
                   command=self._guncelle).pack(side="left", padx=4)
        ttk.Button(btn, text="🗑 Sil", style="Del.TButton",
               command=self._sil).pack(side="left", padx=4)
        ttk.Button(btn, text="🔄 Temizle", style="Neu.TButton",
                   command=self._temizle).pack(side="left", padx=4)

        # Sağ: liste
        list_frame = ttk.LabelFrame(pane, text="Kulüp Listesi", padding=4)
        pane.add(list_frame, weight=2)

        srch_frame = ttk.Frame(list_frame)
        srch_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(srch_frame, text="Durum filtresi:").pack(side="left", padx=4)
        self.v_filtre = tk.StringVar(value="Tümü")
        cb = ttk.Combobox(srch_frame, textvariable=self.v_filtre,
                          values=["Tümü", "Aktif", "Pasif", "Askıda"],
                          width=10, state="readonly")
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda _: self._listele())

        cols = [("id","ID",40), ("ad","Kulüp Adı",180),
                ("yetkili_adi","Yetkili",130), ("telefon","Tel",110),
                ("sezon","Sezon",55), ("durum","Durum",65),
                ("aidat_odendi","Aidat",50)]
        tf, self.tree = _make_tree(list_frame, cols)
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_sec)

    def _listele(self):
        f = self.v_filtre.get()
        rows = db.kulupler_listele(None if f == "Tümü" else f)
        _fill_tree(self.tree, rows)

    def _on_sec(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._secili_id = int(sel[0])
        row = db.kulup_getir(self._secili_id)
        if row:
            self.v_ad.set(row["ad"] or "")
            self.v_yetkili.set(row["yetkili_adi"] or "")
            self.v_tel.set(row["telefon"] or "")
            self.v_email.set(row["email"] or "")
            self.v_adres.set(row["adres"] or "")
            self.v_renk.set(row["forma_renk"] or "")
            self.v_sezon.set(row["sezon"] or "")
            self.v_durum.set(row["durum"] or "Aktif")
            self.v_aidat.set(row["aidat_odendi"] or 0)

    def _kaydet(self):
        if not self.v_ad.get().strip():
            messagebox.showwarning("Uyarı", "Kulüp Adı zorunludur.")
            return
        db.kulup_ekle(
            self.v_ad.get().strip(),
            yetkili_adi=self.v_yetkili.get() or None,
            telefon=self.v_tel.get() or None,
            adres=self.v_adres.get() or None,
            email=self.v_email.get() or None,
            forma_renk=self.v_renk.get() or None,
            sezon=self.v_sezon.get() or None,
            durum=self.v_durum.get(),
            aidat_odendi=self.v_aidat.get(),
        )
        self._temizle()
        self._listele()
        messagebox.showinfo("Başarılı", "Kulüp kaydedildi.")

    def _guncelle(self):
        if not self._secili_id:
            messagebox.showwarning("Uyarı", "Listeden bir kulüp seçin.")
            return
        db.kulup_guncelle(
            self._secili_id,
            ad=self.v_ad.get().strip(),
            yetkili_adi=self.v_yetkili.get() or None,
            telefon=self.v_tel.get() or None,
            adres=self.v_adres.get() or None,
            email=self.v_email.get() or None,
            forma_renk=self.v_renk.get() or None,
            sezon=self.v_sezon.get() or None,
            durum=self.v_durum.get(),
            aidat_odendi=self.v_aidat.get(),
        )
        self._listele()
        messagebox.showinfo("Başarılı", "Kulüp güncellendi.")

    def _sil(self):
        if not self._secili_id:
            messagebox.showwarning("Uyarı", "Listeden bir kulüp seçin.")
            return
        if not messagebox.askyesno("Onay", "Seçili kulüp silinsin mi?"):
            return
        try:
            db.kulup_sil(self._secili_id)
            self._temizle()
            self._listele()
            messagebox.showinfo("Başarılı", "Kulüp silindi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    def _temizle(self):
        for v in (self.v_ad, self.v_yetkili, self.v_tel,
                  self.v_email, self.v_adres, self.v_renk):
            v.set("")
        self.v_sezon.set("2026")
        self.v_durum.set("Aktif")
        self.v_aidat.set(0)
        self._secili_id = None
        self.tree.selection_remove(*self.tree.selection())


# ---------------------------------------------------------------------------
# SPORCU sekmesi
# ---------------------------------------------------------------------------

class SporcuSekme(ttk.Frame):
    _ALT_KATEGORI = {
        "Master 1": "Elite",
        "Master 2": "Master 1",
        "Master 3": "Master 2",
    }

    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self._secili_id = None
        self._kulup_map: dict = {}   # kulüp adı → id  (None = Ferdi)
        self._build()
        self._yukle_kulupler()
        self._listele()

    # ------------------------------------------------------------------
    def _yukle_kulupler(self):
        """Aktif kulüpleri combobox'a yükler."""
        rows = db.kulupler_dropdown()
        self._kulup_map = {"— Ferdi —": None}
        self._kulup_map.update({r["ad"]: r["id"] for r in rows})
        self.cb_kulup["values"] = list(self._kulup_map.keys())

    # ------------------------------------------------------------------
    def _build(self):
        ttk.Label(self, text="SPORCU KAYIT VE YÖNETİMİ",
                  style="Header.TLabel").pack(fill="x")

        ust_buton_seridi = ttk.Frame(self)
        ust_buton_seridi.pack(fill="x", padx=_scaled(8), pady=(_scaled(6), 0))
        ttk.Button(ust_buton_seridi, text="➕ Kaydet", style="Add.TButton",
                   command=self._kaydet).pack(side="left", padx=4)
        ttk.Button(ust_buton_seridi, text="✏️ Güncelle", style="Upd.TButton",
                   command=self._guncelle).pack(side="left", padx=4)
        ttk.Button(ust_buton_seridi, text="🗑 Sil", style="Del.TButton",
                   command=self._sil).pack(side="left", padx=4)
        ttk.Button(ust_buton_seridi, text="🔄 Kulüpleri Yenile", style="Neu.TButton",
                   command=self._yukle_kulupler).pack(side="left", padx=4)
        ttk.Button(ust_buton_seridi, text="🔄 Kategori Değiştir", style="Neu.TButton",
               command=self._kategori_degistir).pack(side="left", padx=4)
        ttk.Button(ust_buton_seridi, text="✖ Temizle", style="Neu.TButton",
                   command=self._temizle).pack(side="left", padx=4)

        ttk.Label(ust_buton_seridi, text="| Evrak:").pack(side="left", padx=(10, 2))
        self.v_evrak_saglik = tk.IntVar(value=0)
        self.v_evrak_veli = tk.IntVar(value=0)
        self.v_evrak_baska_fed = tk.IntVar(value=0)
        ttk.Checkbutton(ust_buton_seridi, text="Sağlık Raporu",
                variable=self.v_evrak_saglik).pack(side="left", padx=2)
        ttk.Checkbutton(ust_buton_seridi, text="Veli Muvafakati (<18)",
                variable=self.v_evrak_veli).pack(side="left", padx=2)
        ttk.Checkbutton(ust_buton_seridi, text="Başka Federasyon Beyanı",
                variable=self.v_evrak_baska_fed).pack(side="left", padx=2)

        pane = ttk.PanedWindow(self, orient="horizontal")
        pane.pack(fill="both", expand=True, padx=8, pady=8)

        # Sol: form
        form_frame = ttk.LabelFrame(pane, text="Sporcu Bilgileri", padding=8)
        pane.add(form_frame, weight=1)

        self.v_ad       = _lbl_entry(form_frame, "Ad *",           0)
        self.v_soyad    = _lbl_entry(form_frame, "Soyad *",        1)
        self.v_kimlik   = _lbl_entry(form_frame, "Kimlik No *",    2)
        self.v_dogum    = _lbl_entry(form_frame, "Doğum Tarihi",   3, width=14)
        ttk.Label(form_frame, text="(YYYY-AA-GG)",
                  font=FONT_S, foreground="gray"
                  ).grid(row=3, column=2, sticky="w")
        self.v_cinsiyet = _lbl_combo(form_frame, "Cinsiyet",
                         ["Belirtilmedi", "Erkek", "Kadın"], 4, width=14)
        self.v_cinsiyet.set("Belirtilmedi")
        self.v_uyruk    = _lbl_combo(form_frame, "Uyruk",
                         ["KKTC", "TC", "Diğer"], 5, width=10)
        self.v_uyruk.set("KKTC")
        self.v_pasaport = _lbl_entry(form_frame, "Pasaport No",    6)
        self.v_tel      = _lbl_entry(form_frame, "Telefon",        7)
        self.v_email    = _lbl_entry(form_frame, "E-posta",        8)
        self.v_adres    = _lbl_entry(form_frame, "Adres",          9)
        self.v_sd_kayit = _lbl_check(form_frame,
                         "Spor Dairesi BYS Kayıtlı", 10)

        # Kulüp seçimi — kayıtlı kulüpler veya Ferdi
        ttk.Label(form_frame, text="Kulüp").grid(
            row=11, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_kulup = tk.StringVar(value="— Ferdi —")
        self.cb_kulup = ttk.Combobox(form_frame, textvariable=self.v_kulup,
                                     width=14, state="readonly")
        self.cb_kulup.grid(row=11, column=1,
                           sticky="w", padx=(0, 8), pady=4)

        # Lisans türü
        self.v_lisans_turu = _lbl_combo(
            form_frame, "Lisans Türü",
            ["Ulusal", "Uluslararası", "Ferdi", "Geçici", "MisafirSporcu"],
            12, width=14)
        self.v_lisans_turu.set("Ulusal")

        # Sezon
        self.v_sezon = _lbl_entry(form_frame, "Sezon", 13, width=10)
        self.v_sezon.set("2026")

        # Üretilen lisans no (salt okunur, kayıt sonrası dolar)
        ttk.Label(form_frame, text="Lisans No").grid(
            row=14, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_lisans_no = tk.StringVar(value="—")
        ttk.Label(form_frame, textvariable=self.v_lisans_no,
                  foreground=ACCENT, font=FONT_B).grid(
            row=14, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(form_frame, text="Yaş Kategorisi").grid(
            row=15, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_yas_kategorisi = tk.StringVar(value="—")
        ttk.Label(form_frame, textvariable=self.v_yas_kategorisi,
                  font=FONT_B).grid(
            row=15, column=1, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(form_frame, text="Yarış Kategorisi").grid(
            row=16, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_yaris_kategorisi = tk.StringVar(value="—")
        self.lbl_yaris_kategorisi = tk.Label(
            form_frame,
            textvariable=self.v_yaris_kategorisi,
            bg=BG,
            fg="black",
            font=FONT_B,
        )
        self.lbl_yaris_kategorisi.grid(
            row=16, column=1, sticky="w", padx=(0, 8), pady=4)

        form_frame.columnconfigure(1, weight=1)

        # Sağ: liste + arama
        list_frame = ttk.LabelFrame(pane, text="Sporcu Listesi", padding=4)
        pane.add(list_frame, weight=2)

        srch_frame = ttk.Frame(list_frame)
        srch_frame.pack(fill="x", pady=(0, 4))
        ttk.Label(srch_frame, text="Ad / Kimlik No:").pack(side="left", padx=4)
        self.v_arama = tk.StringVar()
        ttk.Entry(srch_frame, textvariable=self.v_arama, width=20
                  ).pack(side="left", padx=2)
        ttk.Button(srch_frame, text="Ara", style="Neu.TButton",
                   command=self._ara).pack(side="left", padx=4)
        ttk.Button(srch_frame, text="Tümü", command=self._listele
                   ).pack(side="left")

        cols = [("id","ID",38), ("ad","Ad",85), ("soyad","Soyad",95),
            ("cinsiyet","Cinsiyet",80),
            ("kimlik_no","Kimlik No",105), ("dogum_tarihi","Doğum",82),
            ("yas_kategorisi","Yaş Kategorisi",120),
            ("yaris_kategorisi","Yarış Kategorisi",120),
            ("uyruk","Uyruk",48), ("telefon","Telefon",100),
            ("lisans_no","Lisans No",88), ("kulup_adi","Kulüp",130),
            ("spor_dairesi_kayitli","BYS",38)]
        tf, self.tree = _make_tree(list_frame, cols)
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_sec)

    @staticmethod
    def _hesapla_yas(dogum_tarihi: str):
        if not dogum_tarihi:
            return None
        try:
            return date.today().year - int(dogum_tarihi[:4])
        except Exception:
            return None

    @staticmethod
    def _hesapla_yas_kategorisi(dogum_tarihi: str) -> str:
        if not dogum_tarihi:
            return "—"
        try:
            yas = date.today().year - int(dogum_tarihi[:4])
        except Exception:
            return "—"
        if 11 <= yas <= 12:
            return "U13"
        if 13 <= yas <= 14:
            return "U15"
        if 15 <= yas <= 16:
            return "U17"
        if 17 <= yas <= 18:
            return "Junior"
        if 19 <= yas <= 34:
            return "Elite"
        if 35 <= yas <= 44:
            return "Master 1"
        if 45 <= yas <= 54:
            return "Master 2"
        if yas >= 55:
            return "Master 3"
        return "Kategori Dışı"

    def _kategori_gorunumu_guncelle(self):
        yas_kat = self._hesapla_yas_kategorisi(self.v_dogum.get().strip())
        self.v_yas_kategorisi.set(yas_kat)

        sezon = self.v_sezon.get().strip() or "2026"
        yaris_kat = yas_kat
        if self._secili_id and sezon:
            secim = db.sporcu_sezon_kayitli_kategori(self._secili_id, sezon)
            if secim:
                yaris_kat = secim

        self.v_yaris_kategorisi.set(yaris_kat)
        self.lbl_yaris_kategorisi.config(
            fg=ACCENT if yaris_kat != yas_kat else "black"
        )

    def _kategori_degistir(self):
        if not self._secili_id:
            messagebox.showwarning("Uyarı", "Önce listeden bir sporcu seçin.")
            return
        sezon = self.v_sezon.get().strip()
        if not sezon:
            messagebox.showwarning("Uyarı", "Önce sezon bilgisini girin.")
            return
        yas_kat = self._hesapla_yas_kategorisi(self.v_dogum.get().strip())
        alt_kat = self._ALT_KATEGORI.get(yas_kat)
        if not alt_kat:
            messagebox.showwarning(
                "Uyarı",
                "Bu sporcu için bir alt kategori uygulanamıyor.",
            )
            return

        onay = messagebox.askyesno(
            "Kategori Değiştir",
            f"Sporcunun yaş kategorisi: {yas_kat}\n"
            f"Bir alt kategori: {alt_kat}\n\n"
            "Bu değişiklik seçilen sezonun kalan tüm yarışlarında geçerli olur.\n"
            "Devam edilsin mi?",
        )
        if not onay:
            return

        db.sporcu_sezon_kategori_ata(
            self._secili_id,
            sezon,
            yas_kategorisi=yas_kat,
            yaris_kategorisi=alt_kat,
        )
        self._kategori_gorunumu_guncelle()
        messagebox.showinfo("Başarılı", "Sezonluk yarış kategorisi güncellendi.")

    def _evrak_kontrolu_gecerli(self) -> bool:
        yas = self._hesapla_yas(self.v_dogum.get().strip())
        if yas is not None and yas < 18 and not self.v_evrak_veli.get():
            messagebox.showwarning(
                "Uyarı",
                "18 yaş altı sporcu için Veli Muvafakati zorunludur.",
            )
            return False
        return True

    # ------------------------------------------------------------------
    _SPORCU_QUERY = """
        SELECT s.id, s.ad, s.soyad, s.cinsiyet, s.kimlik_no, s.dogum_tarihi,
               CASE
                   WHEN s.dogum_tarihi IS NULL OR TRIM(s.dogum_tarihi) = '' THEN '—'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 11 AND 12
                       THEN 'Yıldız C / U13'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 13 AND 14
                       THEN 'Yıldız B / U15'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 15 AND 16
                       THEN 'Yıldız A / U17'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 17 AND 18
                       THEN 'Junior / U19'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 19 AND 34
                       THEN 'Elite'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 35 AND 44
                       THEN 'Master 1'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 45 AND 54
                       THEN 'Master 2'
                   WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) >= 55
                       THEN 'Master 3'
                   ELSE 'Kategori Dışı'
               END AS yas_kategorisi,
               COALESCE(
                   ssk.yaris_kategorisi,
                   CASE
                       WHEN s.dogum_tarihi IS NULL OR TRIM(s.dogum_tarihi) = '' THEN '—'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 11 AND 12
                           THEN 'U13'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 13 AND 14
                           THEN 'U15'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 15 AND 16
                           THEN 'U17'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 17 AND 18
                           THEN 'Junior'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 19 AND 34
                           THEN 'Elite'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 35 AND 44
                           THEN 'Master 1'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) BETWEEN 45 AND 54
                           THEN 'Master 2'
                       WHEN (CAST(strftime('%Y','now') AS INTEGER) - CAST(substr(s.dogum_tarihi,1,4) AS INTEGER)) >= 55
                           THEN 'Master 3'
                       ELSE 'Kategori Dışı'
                   END
               ) AS yaris_kategorisi,
               s.uyruk, s.telefon,
               COALESCE(l.lisans_no, '—')  AS lisans_no,
               COALESCE(k.ad, 'Ferdi')     AS kulup_adi,
               s.spor_dairesi_kayitli
        FROM sporcular s
        LEFT JOIN lisanslar l ON l.id = (
            SELECT id FROM lisanslar
            WHERE sporcu_id = s.id AND durum = 'Aktif'
            ORDER BY id DESC LIMIT 1
        )
        LEFT JOIN kulupler k ON k.id = l.kulup_id
        LEFT JOIN sporcu_sezon_kategorileri ssk
               ON ssk.sporcu_id = s.id AND ssk.sezon = l.sezon
    """

    def _listele(self):
        with db.get_conn() as conn:
            rows = conn.execute(
                self._SPORCU_QUERY + " ORDER BY s.soyad, s.ad"
            ).fetchall()
        _fill_tree(self.tree, rows)

    def _ara(self):
        q = self.v_arama.get().strip()
        if not q:
            self._listele()
            return
        with db.get_conn() as conn:
            rows = conn.execute(
                self._SPORCU_QUERY +
                " WHERE s.kimlik_no=? OR (s.ad||' '||s.soyad) LIKE ?"
                " ORDER BY s.soyad, s.ad",
                (q, f"%{q}%")
            ).fetchall()
        _fill_tree(self.tree, rows)

    # ------------------------------------------------------------------
    def _on_sec(self, _=None):
        sel = self.tree.selection()
        if not sel:
            return
        self._secili_id = int(sel[0])
        row = db.sporcu_getir(self._secili_id)
        if row:
            self.v_ad.set(row["ad"] or "")
            self.v_soyad.set(row["soyad"] or "")
            self.v_kimlik.set(row["kimlik_no"] or "")
            self.v_dogum.set(row["dogum_tarihi"] or "")
            self.v_cinsiyet.set(row["cinsiyet"] or "Belirtilmedi")
            self.v_uyruk.set(row["uyruk"] or "KKTC")
            self.v_pasaport.set(row["pasaport_no"] or "")
            self.v_tel.set(row["telefon"] or "")
            self.v_email.set(row["email"] or "")
            self.v_adres.set(row["adres"] or "")
            self.v_sd_kayit.set(row["spor_dairesi_kayitli"] or 0)
        # Aktif lisans bilgilerini doldur
        with db.get_conn() as conn:
            lis = conn.execute(
                """SELECT l.lisans_no, l.lisans_turu, l.sezon,
                          l.saglik_raporu, l.veli_muvafakati, l.baska_federasyon_beyani,
                          k.ad AS kulup_adi
                   FROM lisanslar l
                   LEFT JOIN kulupler k ON k.id = l.kulup_id
                   WHERE l.sporcu_id=? AND l.durum='Aktif'
                   ORDER BY l.id DESC LIMIT 1""",
                (self._secili_id,)
            ).fetchone()
        if lis:
            self.v_lisans_no.set(lis["lisans_no"] or "—")
            self.v_lisans_turu.set(lis["lisans_turu"] or "Ulusal")
            self.v_sezon.set(lis["sezon"] or "2026")
            kulup_ad = lis["kulup_adi"] or "— Ferdi —"
            self.v_kulup.set(kulup_ad if kulup_ad in self._kulup_map
                             else "— Ferdi —")
            self.v_evrak_saglik.set(lis["saglik_raporu"] or 0)
            self.v_evrak_veli.set(lis["veli_muvafakati"] or 0)
            self.v_evrak_baska_fed.set(lis["baska_federasyon_beyani"] or 0)
        else:
            self.v_lisans_no.set("—")
            self.v_evrak_saglik.set(0)
            self.v_evrak_veli.set(0)
            self.v_evrak_baska_fed.set(0)
        self._kategori_gorunumu_guncelle()

    # ------------------------------------------------------------------
    def _kaydet(self):
        if not all([self.v_ad.get().strip(),
                    self.v_soyad.get().strip(),
                    self.v_kimlik.get().strip()]):
            messagebox.showwarning("Uyarı", "Ad, Soyad ve Kimlik No zorunludur.")
            return
        if not self._evrak_kontrolu_gecerli():
            return
        try:
            sid = db.sporcu_ekle(
                self.v_ad.get().strip(),
                self.v_soyad.get().strip(),
                self.v_kimlik.get().strip(),
                dogum_tarihi=self.v_dogum.get() or None,
                cinsiyet=self.v_cinsiyet.get() or "Belirtilmedi",
                uyruk=self.v_uyruk.get() or "KKTC",
                pasaport_no=self.v_pasaport.get() or None,
                telefon=self.v_tel.get() or None,
                email=self.v_email.get() or None,
                adres=self.v_adres.get() or None,
                spor_dairesi_kayitli=self.v_sd_kayit.get(),
            )
            kulup_id = self._kulup_map.get(self.v_kulup.get())  # None = Ferdi
            lid = db.lisans_ekle(
                sid,
                self.v_lisans_turu.get() or "Ulusal",
                self.v_sezon.get() or "2026",
                kulup_id=kulup_id,
                saglik_raporu=self.v_evrak_saglik.get(),
                veli_muvafakati=self.v_evrak_veli.get(),
                baska_federasyon_beyani=self.v_evrak_baska_fed.get(),
            )
            with db.get_conn() as conn:
                lis = conn.execute(
                    "SELECT lisans_no FROM lisanslar WHERE id=?", (lid,)
                ).fetchone()
            no = lis["lisans_no"] if lis else "—"
            self.v_lisans_no.set(no)
            self._secili_id = sid
            self._kategori_gorunumu_guncelle()
            messagebox.showinfo("Başarılı",
                                f"Sporcu kaydedildi.\nLisans No: {no}")
            self._listele()
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    # ------------------------------------------------------------------
    def _guncelle(self):
        if not self._secili_id:
            messagebox.showwarning("Uyarı", "Listeden bir sporcu seçin.")
            return
        if not self._evrak_kontrolu_gecerli():
            return
        try:
            kulup_id = self._kulup_map.get(self.v_kulup.get())
            db.sporcu_guncelle(
                self._secili_id,
                ad=self.v_ad.get().strip(),
                soyad=self.v_soyad.get().strip(),
                kimlik_no=self.v_kimlik.get().strip(),
                dogum_tarihi=self.v_dogum.get() or None,
                cinsiyet=self.v_cinsiyet.get() or "Belirtilmedi",
                uyruk=self.v_uyruk.get() or "KKTC",
                pasaport_no=self.v_pasaport.get() or None,
                telefon=self.v_tel.get() or None,
                email=self.v_email.get() or None,
                adres=self.v_adres.get() or None,
                spor_dairesi_kayitli=self.v_sd_kayit.get(),
            )
            db.aktif_lisans_guncelle(
                self._secili_id,
                lisans_turu=self.v_lisans_turu.get() or "Ulusal",
                sezon=self.v_sezon.get() or "2026",
                kulup_id=kulup_id,
                saglik_raporu=self.v_evrak_saglik.get(),
                veli_muvafakati=self.v_evrak_veli.get(),
                baska_federasyon_beyani=self.v_evrak_baska_fed.get(),
            )
            self._kategori_gorunumu_guncelle()
            self._listele()
            messagebox.showinfo("Başarılı", "Sporcu güncellendi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    def _sil(self):
        if not self._secili_id:
            messagebox.showwarning("Uyarı", "Listeden bir sporcu seçin.")
            return
        if not messagebox.askyesno("Onay", "Seçili sporcu silinsin mi?"):
            return
        try:
            db.sporcu_sil(self._secili_id)
            self._temizle()
            self._listele()
            messagebox.showinfo("Başarılı", "Sporcu silindi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    # ------------------------------------------------------------------
    def _temizle(self):
        for v in (self.v_ad, self.v_soyad, self.v_kimlik, self.v_dogum,
                  self.v_pasaport, self.v_tel, self.v_email, self.v_adres):
            v.set("")
        self.v_cinsiyet.set("Belirtilmedi")
        self.v_uyruk.set("KKTC")
        self.v_sd_kayit.set(0)
        self.v_kulup.set("— Ferdi —")
        self.v_lisans_turu.set("Ulusal")
        self.v_sezon.set("2026")
        self.v_lisans_no.set("—")
        self.v_evrak_saglik.set(0)
        self.v_evrak_veli.set(0)
        self.v_evrak_baska_fed.set(0)
        self.v_yas_kategorisi.set("—")
        self.v_yaris_kategorisi.set("—")
        self.lbl_yaris_kategorisi.config(fg="black")
        self._secili_id = None
        self.tree.selection_remove(*self.tree.selection())


# ---------------------------------------------------------------------------
# YARIŞ KAYIT sekmesi
# ---------------------------------------------------------------------------

class YarisKayitSekme(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self._secili_yaris_id = None
        self._yaris_map: dict = {}
        self._sporcu_map: dict = {}
        self._build()
        self._yarislari_yukle()
        self._sporculari_yukle()
        self._kayitlari_listele()

    def _build(self):
        ttk.Label(self, text="YARIŞ KAYIT MODÜLÜ",
                  style="Header.TLabel").pack(fill="x")

        ust = ttk.LabelFrame(self, text="Yarış Tanımı", padding=8)
        ust.pack(fill="x", padx=8, pady=(8, 4))

        self.v_yaris_ad = _lbl_entry(ust, "Yarış Adı *", 0, width=26)
        self.v_yaris_tarih = _lbl_entry(ust, "Tarih", 1, width=14)
        ttk.Label(ust, text="(YYYY-AA-GG)", font=FONT_S,
                  foreground="gray").grid(row=1, column=2, sticky="w")
        self.v_yaris_yer = _lbl_entry(ust, "Yer", 2, width=20)
        self.v_yaris_disiplin = _lbl_combo(
            ust, "Disiplin",
            ["Yol", "MTB", "Pist", "BMX", "Cyclocross", "Diğer"],
            3, width=14)
        self.v_yaris_disiplin.set("Yol")
        self.v_yaris_sezon = _lbl_entry(ust, "Sezon *", 4, width=10)
        self.v_yaris_sezon.set("2026")
        self.v_yaris_durum = _lbl_combo(
            ust, "Durum",
            ["Planlandı", "Kayıt Açık", "Tamamlandı", "İptal"],
            5, width=14)
        self.v_yaris_durum.set("Kayıt Açık")

        ust.columnconfigure(1, weight=1)

        b1 = ttk.Frame(ust)
        b1.grid(row=6, column=0, columnspan=3, pady=(8, 2))
        ttk.Button(b1, text="➕ Yarış Ekle", style="Add.TButton",
                   command=self._yaris_ekle).pack(side="left", padx=4)
        ttk.Button(b1, text="✏️ Yarış Güncelle", style="Upd.TButton",
               command=self._yaris_guncelle).pack(side="left", padx=4)
        ttk.Button(b1, text="🗑 Yarış Sil", style="Del.TButton",
               command=self._yaris_sil).pack(side="left", padx=4)
        ttk.Button(b1, text="🔄 Yarışları Yenile", style="Neu.TButton",
                   command=self._yarislari_yukle).pack(side="left", padx=4)

        orta = ttk.LabelFrame(self, text="Yarış Listesi", padding=4)
        orta.pack(fill="x", padx=8, pady=4)
        cols_yaris = [
            ("id", "ID", 42),
            ("ad", "Yarış", 220),
            ("tarih", "Tarih", 90),
            ("yer", "Yer", 140),
            ("disiplin", "Disiplin", 90),
            ("sezon", "Sezon", 65),
            ("durum", "Durum", 100),
        ]
        tf1, self.tree_yaris = _make_tree(orta, cols_yaris)
        tf1.pack(fill="x", expand=True)
        self.tree_yaris.bind("<<TreeviewSelect>>", self._on_yaris_sec)
        self.tree_yaris.bind("<Double-1>", self._on_yaris_cift_tikla)

        aksiyon = ttk.Frame(self)
        aksiyon.pack(fill="x", padx=8, pady=(0, 6))
        ttk.Button(aksiyon, text="📝 Sporcu Kayıt Penceresini Aç",
               style="Neu.TButton",
               command=self._kayit_penceresi_ac).pack(side="left")

        alt = ttk.LabelFrame(self, text="Sporcu Yarış Kaydı", padding=8)
        # Bu panel artık ana ekranda gösterilmiyor; kayıt işlemi ayrı pencerede.

        ttk.Label(alt, text="Yarış").grid(row=0, column=0, sticky="e",
                                            padx=(8, 4), pady=4)
        self.v_kayit_yaris = tk.StringVar()
        self.cb_kayit_yaris = ttk.Combobox(
            alt, textvariable=self.v_kayit_yaris, width=32, state="readonly")
        self.cb_kayit_yaris.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.cb_kayit_yaris.bind("<<ComboboxSelected>>", self._on_kayit_yaris_sec)

        ttk.Label(alt, text="Sporcu").grid(row=1, column=0, sticky="e",
                                             padx=(8, 4), pady=4)
        self.v_kayit_sporcu = tk.StringVar()
        self.cb_kayit_sporcu = ttk.Combobox(
            alt, textvariable=self.v_kayit_sporcu, width=32, state="readonly")
        self.cb_kayit_sporcu.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)

        self.v_kategori = _lbl_combo(
            alt, "Kategori",
            ["Elite", "Junior", "U17", "U15", "Master 1", "Master 2", "Master 3", "Diğer"],
            2, width=16)
        self.v_kategori.set("Elite")

        alt.columnconfigure(1, weight=1)

        b2 = ttk.Frame(alt)
        b2.grid(row=3, column=0, columnspan=2, pady=(8, 4))
        ttk.Button(b2, text="➕ Kaydı Oluştur", style="Add.TButton",
                   command=self._kayit_ekle).pack(side="left", padx=4)
        ttk.Button(b2, text="✖ Seçili Kaydı Sil", style="Del.TButton",
                   command=self._kayit_sil).pack(side="left", padx=4)
        ttk.Button(b2, text="🗂 Kayıt Penceresi", style="Neu.TButton",
               command=self._kayit_penceresi_ac).pack(side="left", padx=4)
        ttk.Button(b2, text="🔄 Sporcuları Yenile", style="Neu.TButton",
                   command=self._sporculari_yukle).pack(side="left", padx=4)

        cols_kayit = [
            ("id", "ID", 42),
            ("yaris_adi", "Yarış", 200),
            ("yaris_tarihi", "Yarış Tarihi", 95),
            ("sporcu", "Sporcu", 180),
            ("lisans_no", "Lisans No", 90),
            ("kategori", "Kategori", 90),
            ("durum", "Durum", 85),
            ("kayit_tarihi", "Kayıt Tarihi", 95),
        ]
        tf2, self.tree_kayit = _make_tree(alt, cols_kayit)
        tf2.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=(4, 0))
        alt.rowconfigure(4, weight=1)

    def _yaris_label(self, row):
        tarih = row["tarih"] or "Tarihsiz"
        return f"{row['ad']} ({tarih})"

    def _yarislari_yukle(self):
        rows = db.yarislar_listele()
        _fill_tree(self.tree_yaris, rows)
        acik_rows = db.kayit_acik_yarislar()
        self._yaris_map = {self._yaris_label(r): r["id"] for r in acik_rows}
        self.cb_kayit_yaris["values"] = list(self._yaris_map.keys())
        if self.v_kayit_yaris.get() not in self._yaris_map:
            self.v_kayit_yaris.set("")
        if acik_rows and not self.v_kayit_yaris.get():
            self.v_kayit_yaris.set(self._yaris_label(acik_rows[0]))
        self._kayitlari_listele()

    def _sporculari_yukle(self):
        sec = self.v_kayit_yaris.get().strip()
        yaris_id = self._yaris_map.get(sec) if sec else None
        kayitli = db.yarisa_kayitli_sporcu_idleri(yaris_id) if yaris_id else set()
        rows = db.aktif_lisansli_sporcular()
        self._sporcu_map = {
            f"{r['ad_soyad']} | {r['lisans_no']} | {r['kulup_adi']}": (r["sporcu_id"], r["lisans_id"])
            for r in rows
            if r["sporcu_id"] not in kayitli
        }
        self.cb_kayit_sporcu["values"] = list(self._sporcu_map.keys())
        if self.v_kayit_sporcu.get() not in self._sporcu_map:
            self.v_kayit_sporcu.set("")
        if self._sporcu_map and not self.v_kayit_sporcu.get():
            self.v_kayit_sporcu.set(list(self._sporcu_map.keys())[0])

    def _kayitlari_listele(self):
        sec = self.v_kayit_yaris.get().strip()
        yaris_id = self._yaris_map.get(sec) if sec else None
        rows = db.yaris_kayitlari_listele(yaris_id)
        _fill_tree(self.tree_kayit, rows)

    def _on_kayit_yaris_sec(self, _=None):
        self._kayitlari_listele()
        self._sporculari_yukle()

    def _on_yaris_sec(self, _=None):
        sel = self.tree_yaris.selection()
        if not sel:
            return
        self._secili_yaris_id = int(sel[0])
        row = db.yaris_getir(self._secili_yaris_id)
        if not row:
            return
        self.v_yaris_ad.set(row["ad"] or "")
        self.v_yaris_tarih.set(row["tarih"] or "")
        self.v_yaris_yer.set(row["yer"] or "")
        self.v_yaris_disiplin.set(row["disiplin"] or "Diğer")
        self.v_yaris_sezon.set(row["sezon"] or "2026")
        self.v_yaris_durum.set(row["durum"] or "Planlandı")
        label = self._yaris_label(row)
        if row["durum"] == "Kayıt Açık" and label in self._yaris_map:
            self.v_kayit_yaris.set(label)
            self._kayitlari_listele()
            self._sporculari_yukle()

    def _yaris_ekle(self):
        ad = self.v_yaris_ad.get().strip()
        sezon = self.v_yaris_sezon.get().strip()
        if not ad or not sezon:
            messagebox.showwarning("Uyarı", "Yarış adı ve sezon zorunludur.")
            return
        try:
            db.yaris_ekle(
                ad,
                sezon=sezon,
                tarih=self.v_yaris_tarih.get() or None,
                yer=self.v_yaris_yer.get() or None,
                disiplin=self.v_yaris_disiplin.get() or "Diğer",
                durum=self.v_yaris_durum.get() or "Planlandı",
            )
            self.v_yaris_ad.set("")
            self.v_yaris_tarih.set("")
            self.v_yaris_yer.set("")
            self.v_yaris_disiplin.set("Yol")
            self.v_yaris_durum.set("Kayıt Açık")
            self._yarislari_yukle()
            messagebox.showinfo("Başarılı", "Yarış kaydı eklendi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    def _yaris_guncelle(self):
        if not self._secili_yaris_id:
            messagebox.showwarning("Uyarı", "Listeden bir yarış seçin.")
            return
        ad = self.v_yaris_ad.get().strip()
        sezon = self.v_yaris_sezon.get().strip()
        if not ad or not sezon:
            messagebox.showwarning("Uyarı", "Yarış adı ve sezon zorunludur.")
            return
        try:
            db.yaris_guncelle(
                self._secili_yaris_id,
                ad=ad,
                tarih=self.v_yaris_tarih.get() or None,
                yer=self.v_yaris_yer.get() or None,
                disiplin=self.v_yaris_disiplin.get() or "Diğer",
                sezon=sezon,
                durum=self.v_yaris_durum.get() or "Planlandı",
            )
            self._yarislari_yukle()
            messagebox.showinfo("Başarılı", "Yarış güncellendi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    def _yaris_sil(self):
        if not self._secili_yaris_id:
            messagebox.showwarning("Uyarı", "Listeden bir yarış seçin.")
            return
        if not messagebox.askyesno("Onay", "Seçili yarış silinsin mi?"):
            return
        try:
            db.yaris_sil(self._secili_yaris_id)
            self._secili_yaris_id = None
            self.v_yaris_ad.set("")
            self.v_yaris_tarih.set("")
            self.v_yaris_yer.set("")
            self.v_yaris_disiplin.set("Yol")
            self.v_yaris_sezon.set("2026")
            self.v_yaris_durum.set("Kayıt Açık")
            self._yarislari_yukle()
            messagebox.showinfo("Başarılı", "Yarış silindi.")
        except Exception as exc:
            messagebox.showerror("Hata", str(exc))

    def _kayit_ekle(self):
        yaris = self.v_kayit_yaris.get().strip()
        sporcu = self.v_kayit_sporcu.get().strip()
        yaris_id = self._yaris_map.get(yaris)
        sporcu_info = self._sporcu_map.get(sporcu)
        if not yaris_id or not sporcu_info:
            messagebox.showwarning(
                "Uyarı",
                "Kayıt için sadece 'Kayıt Açık' yarış seçilebilir ve sporcu seçimi zorunludur.",
            )
            return
        sporcu_id, lisans_id = sporcu_info
        try:
            db.yaris_kayit_ekle(
                yaris_id=yaris_id,
                sporcu_id=sporcu_id,
                lisans_id=lisans_id,
                kategori=self.v_kategori.get() or None,
            )
            self._kayitlari_listele()
            self._sporculari_yukle()
            messagebox.showinfo("Başarılı", "Sporcu yarışa kaydedildi.")
        except Exception as exc:
            if "UNIQUE constraint failed" in str(exc):
                messagebox.showwarning(
                    "Uyarı",
                    "Bu sporcu seçili yarışa zaten kayıtlı.",
                )
                return
            messagebox.showerror("Hata", str(exc))

    def _kayit_sil(self):
        sel = self.tree_kayit.selection()
        if not sel:
            messagebox.showwarning("Uyarı", "Silmek için bir kayıt seçin.")
            return
        kayit_id = int(sel[0])
        if not messagebox.askyesno("Onay", "Seçili yarış kaydı silinsin mi?"):
            return
        db.yaris_kayit_sil(kayit_id)
        self._kayitlari_listele()
        self._sporculari_yukle()
        messagebox.showinfo("Başarılı", "Yarış kaydı silindi.")

    def _on_yaris_cift_tikla(self, event=None):
        sel = self.tree_yaris.selection()
        if not sel:
            return
        self._kayit_penceresi_ac(yaris_id=int(sel[0]))

    def _kayit_penceresi_ac(self, yaris_id: int | None = None):  # noqa: C901
        import datetime

        # ── Kategori sırası ve bir-alt haritası ──────────────────────────
        KATEGORI_SIRA = [
            "U13", "U15", "U17", "Junior",
            "Elite", "Master 1", "Master 2", "Master 3",
        ]
        ALT_KATEGORI = {
            "U15": "U13", "U17": "U15", "Junior": "U17",
            "Elite": "Junior", "Master 1": "Elite",
            "Master 2": "Master 1", "Master 3": "Master 2",
        }

        def hesapla_yas_kat(dogum_tarihi):
            if not dogum_tarihi:
                return "—"
            try:
                yas = datetime.date.today().year - int(dogum_tarihi[:4])
                if 11 <= yas <= 12:  return "U13"
                if 13 <= yas <= 14:  return "U15"
                if 15 <= yas <= 16:  return "U17"
                if 17 <= yas <= 18:  return "Junior"
                if 19 <= yas <= 34:  return "Elite"
                if 35 <= yas <= 44:  return "Master 1"
                if 45 <= yas <= 54:  return "Master 2"
                if yas >= 55:        return "Master 3"
                return "Kategori Dışı"
            except Exception:
                return "—"

        # ── Pencere ───────────────────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title("Yarışa Sporcu Kayıt")
        win.configure(bg=BG)
        _apply_window_geometry(
            win,
            width_ratio=0.9,
            height_ratio=0.88,
            min_width=1200,
            min_height=780,
        )

        tum_yarislar = db.yarislar_listele()
        popup_yaris_map  = {self._yaris_label(r): r["id"]     for r in tum_yarislar}
        yaris_sezon_map  = {r["id"]: (r["sezon"] or "")       for r in tum_yarislar}

        if yaris_id is not None:
            row0 = db.yaris_getir(yaris_id)
            baslangic_label = self._yaris_label(row0) if row0 else self.v_kayit_yaris.get()
        else:
            baslangic_label = self.v_kayit_yaris.get()

        # ── Form (grid) ───────────────────────────────────────────────────
        top = ttk.LabelFrame(win, text="Kayıt Bilgileri", padding=8)
        top.pack(fill="x", padx=8, pady=8)

        # Satır 0: Yarış | Kayıt Durumu
        ttk.Label(top, text="Yarış:").grid(
            row=0, column=0, sticky="e", padx=(4, 4), pady=4)
        v_yaris = tk.StringVar(value=baslangic_label)
        cb = ttk.Combobox(top, textvariable=v_yaris,
                          values=list(popup_yaris_map.keys()),
                          state="readonly", width=40)
        cb.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(0, 8), pady=4)
        ttk.Label(top, text="Kayıt Durumu:").grid(
            row=0, column=4, sticky="e", padx=(4, 4), pady=4)
        v_durum = tk.StringVar(value="Onaylandı")
        cb_durum = ttk.Combobox(top, textvariable=v_durum,
                                values=["Onaylandı", "Beklemede", "İptal"],
                                state="readonly", width=12)
        cb_durum.grid(row=0, column=5, sticky="ew", padx=(0, 8), pady=4)

        # Satır 1: Sporcu
        ttk.Label(top, text="Sporcu:").grid(
            row=1, column=0, sticky="e", padx=(4, 4), pady=4)
        v_sporcu = tk.StringVar()
        cb_sporcu = ttk.Combobox(top, textvariable=v_sporcu,
                                 state="readonly", width=50)
        cb_sporcu.grid(row=1, column=1, columnspan=5,
                       sticky="ew", padx=(0, 8), pady=4)

        # Satır 2: Yaş Kategorisi | Yarış Kategorisi | Kategori Değiştir
        ttk.Label(top, text="Yaş Kategorisi:").grid(
            row=2, column=0, sticky="e", padx=(4, 4), pady=4)
        lbl_yas_kat = ttk.Label(top, text="—", font=FONT_B)
        lbl_yas_kat.grid(row=2, column=1, sticky="w", padx=(0, 16), pady=4)
        ttk.Label(top, text="Yarış Kategorisi:").grid(
            row=2, column=2, sticky="e", padx=(4, 4), pady=4)
        v_yaris_kat = tk.StringVar(value="—")
        lbl_yaris_kat = tk.Label(top, textvariable=v_yaris_kat,
                                 font=FONT_B,
                                 bg=BG, foreground="black")
        lbl_yaris_kat.grid(row=2, column=3, sticky="w", padx=(0, 8), pady=4)
        btn_kat_degistir = ttk.Button(top, text="🔄 Kategori Değiştir",
                                      style="Neu.TButton", state="disabled")
        btn_kat_degistir.grid(row=2, column=4, columnspan=2,
                               sticky="w", padx=(0, 8), pady=4)

        # Satır 3: İşlem butonları
        btn_frame = ttk.Frame(top)
        btn_frame.grid(row=3, column=0, columnspan=6, pady=(8, 2))
        top.columnconfigure(1, weight=1)

        # ── Kayıt listesi ─────────────────────────────────────────────────
        cols = [
            ("id",           "ID",           42),
            ("sporcu",       "Sporcu",       230),
            ("lisans_no",    "Lisans No",     95),
            ("kategori",     "Kategori",      95),
            ("durum",        "Durum",         90),
            ("kayit_tarihi", "Kayıt Tarihi", 100),
        ]
        tf, tree = _make_tree(win, cols)
        tf.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        # ── İç durum ──────────────────────────────────────────────────────
        sporcu_map: dict = {}   # label → (sporcu_id, lisans_id, dogum_tarihi)
        _st = {"yas_kat": "—", "override_kat": None}

        # ── Yardımcı fonksiyonlar ─────────────────────────────────────────
        def get_secili_sezon():
            yid = popup_yaris_map.get(v_yaris.get().strip())
            return yaris_sezon_map.get(yid, "") if yid else ""

        def update_kat_display():
            yas = _st["yas_kat"]
            ov  = _st["override_kat"]
            if ov and ov != yas:
                v_yaris_kat.set(ov)
                lbl_yaris_kat.config(foreground=ACCENT)   # mavi
                btn_kat_degistir.config(state="disabled")  # kilitli
            else:
                v_yaris_kat.set(yas)
                lbl_yaris_kat.config(foreground="black")
                alt = ALT_KATEGORI.get(yas)
                btn_kat_degistir.config(
                    state="normal" if (alt and yas not in ("—", "Kategori Dışı"))
                    else "disabled")

        def on_sporcu_sec(_=None):
            info = sporcu_map.get(v_sporcu.get().strip())
            if not info:
                _st["yas_kat"] = "—"
                _st["override_kat"] = None
                lbl_yas_kat.config(text="—")
                update_kat_display()
                return
            sporcu_id, _lid, dogum_tarihi = info
            yas_kat = hesapla_yas_kat(dogum_tarihi)
            _st["yas_kat"] = yas_kat
            lbl_yas_kat.config(text=yas_kat)
            # Bu sezonda zaten kayıtlı kategorisi var mı?
            sezon = get_secili_sezon()
            ov = db.sporcu_sezon_kayitli_kategori(sporcu_id, sezon) if sezon else None
            _st["override_kat"] = ov if (ov and ov != yas_kat) else None
            update_kat_display()

        cb_sporcu.bind("<<ComboboxSelected>>", on_sporcu_sec)

        def on_kat_degistir():
            yas = _st["yas_kat"]
            alt = ALT_KATEGORI.get(yas)
            if not alt:
                return
            info = sporcu_map.get(v_sporcu.get().strip())
            if not info:
                messagebox.showwarning("Uyarı", "Önce bir sporcu seçin.", parent=win)
                return
            sporcu_id, _lisans_id, _dogum_tarihi = info
            sezon = get_secili_sezon()
            if not sezon:
                messagebox.showwarning("Uyarı", "Sezon bilgisi bulunamadı.", parent=win)
                return
            if not messagebox.askyesno(
                "Kategori Değiştir",
                f"Sporcunun yaş kategorisi: {yas}\n"
                f"Bir alt kategoride ({alt}) yarışmak isteniyor.\n\n"
                f"UYARI: Bu sezondaki TÜM yarışlarda '{alt}' kategorisinde\n"
                "yarışmak zorunda kalır.\n\nDevam etmek istiyor musunuz?",
                parent=win,
            ):
                return
            db.sporcu_sezon_kategori_ata(
                sporcu_id,
                sezon,
                yas_kategorisi=yas,
                yaris_kategorisi=alt,
            )
            _st["override_kat"] = alt
            update_kat_display()

        btn_kat_degistir.config(command=on_kat_degistir)

        def fill_tree_kayit(rows):
            tree.delete(*tree.get_children())
            for i, row in enumerate(rows):
                tag = "even" if i % 2 == 0 else "odd"
                vals = (
                    row["id"], row["sporcu"], row["lisans_no"],
                    row["kategori"], row["durum"], row["kayit_tarihi"],
                )
                tree.insert("", "end", iid=str(row["id"]),
                            values=vals, tags=(tag,))

        def refresh_sporcular(secili_yaris_id):
            nonlocal sporcu_map
            kayitli = (db.yarisa_kayitli_sporcu_idleri(secili_yaris_id)
                       if secili_yaris_id else set())
            rows = db.aktif_lisansli_sporcular()
            sporcu_map = {
                f"{r['ad_soyad']} | {r['lisans_no']} | {r['kulup_adi']}":
                    (r["sporcu_id"], r["lisans_id"], r["dogum_tarihi"])
                for r in rows
                if r["sporcu_id"] not in kayitli
            }
            cb_sporcu["values"] = list(sporcu_map.keys())
            if v_sporcu.get() not in sporcu_map:
                v_sporcu.set("")
            if sporcu_map and not v_sporcu.get():
                v_sporcu.set(list(sporcu_map.keys())[0])
            on_sporcu_sec()

        def refresh(_=None):
            sec = v_yaris.get().strip()
            secili_yaris_id = popup_yaris_map.get(sec) if sec else None
            rows = db.yaris_kayitlari_listele(secili_yaris_id)
            fill_tree_kayit(rows)
            refresh_sporcular(secili_yaris_id)

        def kayit_ekle_popup():
            sec = v_yaris.get().strip()
            ekle_yaris_id = popup_yaris_map.get(sec) if sec else None
            sporcu_info = sporcu_map.get(v_sporcu.get().strip())
            if not ekle_yaris_id or not sporcu_info:
                messagebox.showwarning(
                    "Uyarı",
                    "Kayıt için yarış ve sporcu seçimi zorunludur.",
                    parent=win,
                )
                return
            sporcu_id, lisans_id, _ = sporcu_info
            kat = v_yaris_kat.get()
            kategori = None if kat in ("—", "Kategori Dışı") else kat
            try:
                db.yaris_kayit_ekle(
                    yaris_id=ekle_yaris_id,
                    sporcu_id=sporcu_id,
                    lisans_id=lisans_id,
                    kategori=kategori,
                )
                refresh()
                messagebox.showinfo("Başarılı", "Sporcu yarışa kaydedildi.", parent=win)
            except Exception as exc:
                if "UNIQUE constraint failed" in str(exc):
                    messagebox.showwarning(
                        "Uyarı", "Bu sporcu bu yarışa zaten kayıtlı.", parent=win)
                    return
                messagebox.showerror("Hata", str(exc), parent=win)

        def kayit_sil_popup():
            sel_items = tree.selection()
            if not sel_items:
                messagebox.showwarning("Uyarı", "Silmek için bir kayıt seçin.", parent=win)
                return
            kayit_id = int(sel_items[0])
            if not messagebox.askyesno("Onay", "Seçili yarış kaydı silinsin mi?", parent=win):
                return
            db.yaris_kayit_sil(kayit_id)
            refresh()
            messagebox.showinfo("Başarılı", "Yarış kaydı silindi.", parent=win)

        def kayit_guncelle_popup():
            sel_items = tree.selection()
            if not sel_items:
                messagebox.showwarning("Uyarı", "Güncellemek için bir kayıt seçin.", parent=win)
                return
            kayit_id = int(sel_items[0])
            kat = v_yaris_kat.get()
            kategori = None if kat in ("—", "Kategori Dışı") else kat
            try:
                db.yaris_kayit_guncelle(
                    kayit_id,
                    kategori=kategori,
                    durum=v_durum.get() or None,
                )
                refresh()
                messagebox.showinfo("Başarılı", "Yarış kaydı güncellendi.", parent=win)
            except Exception as exc:
                messagebox.showerror("Hata", str(exc), parent=win)

        def on_tree_sec(_=None):
            sel_items = tree.selection()
            if not sel_items:
                return
            vals = tree.item(sel_items[0], "values")
            # vals: (id, sporcu, lisans_no, kategori, durum, kayit_tarihi)
            if len(vals) >= 5:
                v_durum.set(vals[4] or "Onaylandı")

        tree.bind("<<TreeviewSelect>>", on_tree_sec)

        ttk.Button(btn_frame, text="➕ Kaydı Oluştur", style="Add.TButton",
                   command=kayit_ekle_popup).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="✏️ Seçili Kaydı Güncelle", style="Upd.TButton",
                   command=kayit_guncelle_popup).pack(side="left", padx=(0, 4))
        ttk.Button(btn_frame, text="✖ Seçili Kaydı Sil", style="Del.TButton",
                   command=kayit_sil_popup).pack(side="left", padx=(0, 4))
        ttk.Button(btn_frame, text="🔄 Yenile", style="Neu.TButton",
                   command=refresh).pack(side="left")

        cb.bind("<<ComboboxSelected>>", refresh)
        refresh()


# ---------------------------------------------------------------------------
# EVRAK KONTROL sekmesi
# ---------------------------------------------------------------------------

class EvrakKontrolSekme(ttk.Frame):
    BASVURU_TURLERI = {
        "Kulüp Üyelik / Aktif Üyelik": {
            "referans_turu": "kulup",
            "kaynak": "KT_Bisiklet_Federasyonu_Üyelik_Talimatı ve kulüp başvuru formu",
            "belgeler": [
                ("uyelik_formu", "Kulüp yeniden kayıt / aktif üyelik başvuru formu", 1),
                ("yetkili_bilgileri", "Kulüp yetkili ve iletişim bilgileri", 1),
                ("aidat_teyidi", "Aidat ödeme / üyelik durumu teyidi", 1),
            ],
        },
        "Sporcu Lisans Başvurusu": {
            "referans_turu": "sporcu",
            "kaynak": "Sporcu_Lisans_Talimatı Madde 7, 7A, 8 ve EK-1",
            "belgeler": [
                ("spor_dairesi_kaydi", "Spor Dairesi BYS kaydı", 1),
                ("saglik_raporu", "Sağlık raporu", 1),
                ("veli_muvafakati", "Veli muvafakatnamesi", 0),
                ("baska_federasyon_beyani", "Başka federasyon lisans beyanı", 0),
            ],
        },
        "Vize / Lisans Yenileme": {
            "referans_turu": "sporcu",
            "kaynak": "Sporcu_Lisans_Talimatı EK-4",
            "belgeler": [
                ("saglik_raporu", "Sağlık raporu", 1),
                ("eski_lisans_teslim", "Eski lisans teslimi", 1),
                ("kulup_yetkilisi", "Kulüp yetkilisi onayı / bilgisi", 0),
            ],
        },
        "Transfer Başvurusu": {
            "referans_turu": "sporcu",
            "kaynak": "Sporcu_Lisans_Talimatı Madde 9",
            "belgeler": [
                ("ilizsizlik_belgesi", "İlişiksizlik belgesi", 1),
            ],
        },
        "Yurt Dışı Yarış İzni": {
            "referans_turu": "sporcu",
            "kaynak": "Sporcu_Lisans_Talimatı Madde 10-11 ve EK-3",
            "belgeler": [
                ("kulup_yazisi", "Kulüp yazısı / organizasyon onayı", 1),
            ],
        },
        "Yabancı Uyruklu / Misafir Sporcu": {
            "referans_turu": "sporcu",
            "kaynak": "Yabanci_Uyruklu_Misafir_Sporcu_Talimati",
            "belgeler": [
                ("pasaport_kimlik", "Pasaport / kimlik belgesi", 1),
                ("yabanci_lisans", "Yabancı federasyon lisans bilgisi", 1),
                ("gecerlilik_teyidi", "Lisans geçerlilik teyidi", 1),
            ],
        },
        "Yabancı Federasyon Lisanslı KKTC Vatandaşı": {
            "referans_turu": "sporcu",
            "kaynak": "KTBF_Yabanci_Federasyon_Lisansli_KKTC_Vatandasi_Sporcular_Talimati",
            "belgeler": [
                ("yabanci_lisans", "Yabancı federasyon lisans bilgisi", 1),
                ("gecerlilik_tarihi", "Lisans geçerlilik tarihi teyidi", 1),
                ("kulup_muvafakati", "Kulüp muvafakati", 0),
            ],
        },
    }

    def __init__(self, parent):
        super().__init__(parent, style="TFrame")
        self._sporcu_map: dict[str, int] = {}
        self._kulup_map: dict[str, int] = {}
        self._evrak_satirlari: dict[str, dict] = {}
        self._ozet_map: dict[str, dict] = {}
        self._build()
        self._referanslari_yukle()
        self._basvuru_turlerini_yukle()
        self._ozet_listele()

    def _build(self):
        ttk.Label(self, text="EVRAK KONTROL MODÜLÜ",
                  style="Header.TLabel").pack(fill="x")

        ust = ttk.LabelFrame(self, text="Başvuru Seçimi", padding=8)
        ust.pack(fill="x", padx=8, pady=(8, 4))
        ust.columnconfigure(1, weight=1)
        ust.columnconfigure(3, weight=1)

        ttk.Label(ust, text="Başvuru Türü").grid(
            row=0, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_basvuru = tk.StringVar()
        self.cb_basvuru = ttk.Combobox(
            ust,
            textvariable=self.v_basvuru,
            state="readonly",
            width=34,
        )
        self.cb_basvuru.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.cb_basvuru.bind("<<ComboboxSelected>>", lambda _=None: self._basvuru_degisti())

        ttk.Label(ust, text="Sezon").grid(
            row=0, column=2, sticky="e", padx=(8, 4), pady=4)
        self.v_sezon = tk.StringVar(value="2026")
        ttk.Entry(ust, textvariable=self.v_sezon, width=12).grid(
            row=0, column=3, sticky="w", padx=(0, 8), pady=4)

        ttk.Label(ust, text="Sporcu").grid(
            row=1, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_sporcu = tk.StringVar()
        self.cb_sporcu = ttk.Combobox(ust, textvariable=self.v_sporcu,
                                      state="readonly", width=34)
        self.cb_sporcu.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)

        ttk.Label(ust, text="Kulüp").grid(
            row=1, column=2, sticky="e", padx=(8, 4), pady=4)
        self.v_kulup = tk.StringVar()
        self.cb_kulup = ttk.Combobox(ust, textvariable=self.v_kulup,
                                     state="readonly", width=28)
        self.cb_kulup.grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=4)

        ttk.Label(ust, text="Talimat Kaynağı").grid(
            row=2, column=0, sticky="ne", padx=(8, 4), pady=4)
        self.lbl_kaynak = ttk.Label(ust, text="—", justify="left")
        self.lbl_kaynak.grid(row=2, column=1, columnspan=3,
                             sticky="w", padx=(0, 8), pady=4)

        aksiyon = ttk.Frame(ust)
        aksiyon.grid(row=3, column=0, columnspan=4, sticky="w", pady=(8, 0))
        ttk.Button(aksiyon, text="💾 Kontrolü Kaydet", style="Add.TButton",
                   command=self._kaydet).pack(side="left", padx=4)
        ttk.Button(aksiyon, text="🔄 Kayıtları Yükle", style="Neu.TButton",
                   command=self._mevcut_kaydi_yukle).pack(side="left", padx=4)
        ttk.Button(aksiyon, text="🗂 Listeleri Yenile", style="Neu.TButton",
                   command=self._referanslari_yukle).pack(side="left", padx=4)
        ttk.Button(aksiyon, text="✖ Temizle", style="Neu.TButton",
                   command=self._temizle).pack(side="left", padx=4)

        self.frm_evrak = ttk.LabelFrame(self, text="İstenen Evraklar", padding=8)
        self.frm_evrak.pack(fill="x", padx=8, pady=4)
        self.frm_evrak.columnconfigure(2, weight=1)

        alt = ttk.LabelFrame(self, text="Kayıtlı Evrak Kontrolleri", padding=4)
        alt.pack(fill="both", expand=True, padx=8, pady=(4, 8))
        cols = [
            ("basvuru", "Başvuru", 240),
            ("referans", "Referans", 200),
            ("sezon", "Sezon", 70),
            ("tamam", "Tamam", 80),
            ("guncelleme", "Güncelleme", 95),
        ]
        tf, self.tree_ozet = _make_tree(alt, cols)
        tf.pack(fill="both", expand=True)
        self.tree_ozet.bind("<<TreeviewSelect>>", self._on_ozet_sec)

    def _basvuru_turlerini_yukle(self):
        basvurular = list(self.BASVURU_TURLERI.keys())
        self.cb_basvuru["values"] = basvurular
        if not self.v_basvuru.get() and basvurular:
            self.v_basvuru.set(basvurular[0])
        self._basvuru_degisti()

    def _referanslari_yukle(self):
        sporcular = db.sporcular_dropdown()
        self._sporcu_map = {row["ad_soyad"]: row["id"] for row in sporcular}
        self.cb_sporcu["values"] = list(self._sporcu_map.keys())
        if self.v_sporcu.get() not in self._sporcu_map:
            self.v_sporcu.set("")
        if self._sporcu_map and not self.v_sporcu.get():
            self.v_sporcu.set(next(iter(self._sporcu_map)))

        kulupler = db.kulupler_listele()
        self._kulup_map = {row["ad"]: row["id"] for row in kulupler}
        self.cb_kulup["values"] = list(self._kulup_map.keys())
        if self.v_kulup.get() not in self._kulup_map:
            self.v_kulup.set("")
        if self._kulup_map and not self.v_kulup.get():
            self.v_kulup.set(next(iter(self._kulup_map)))

    def _aktif_kural(self):
        return self.BASVURU_TURLERI[self.v_basvuru.get()]

    def _secili_referans(self):
        referans_turu = self._aktif_kural()["referans_turu"]
        if referans_turu == "sporcu":
            return referans_turu, self._sporcu_map.get(self.v_sporcu.get(), 0)
        if referans_turu == "kulup":
            return referans_turu, self._kulup_map.get(self.v_kulup.get(), 0)
        return referans_turu, 0

    def _basvuru_degisti(self):
        kural = self._aktif_kural()
        referans_turu = kural["referans_turu"]
        self.lbl_kaynak.config(text=kural["kaynak"])
        self.cb_sporcu.configure(state="readonly" if referans_turu == "sporcu" else "disabled")
        self.cb_kulup.configure(state="readonly" if referans_turu == "kulup" else "disabled")
        self._evrak_satirlarini_olustur()
        self._mevcut_kaydi_yukle()

    def _evrak_satirlarini_olustur(self):
        for child in self.frm_evrak.winfo_children():
            child.destroy()
        self._evrak_satirlari.clear()

        ttk.Label(self.frm_evrak, text="Belge", font=FONT_B).grid(
            row=0, column=0, sticky="w", padx=(4, 8), pady=(0, 6))
        ttk.Label(self.frm_evrak, text="Durum", font=FONT_B).grid(
            row=0, column=1, sticky="w", padx=(4, 8), pady=(0, 6))
        ttk.Label(self.frm_evrak, text="Not", font=FONT_B).grid(
            row=0, column=2, sticky="w", padx=(4, 8), pady=(0, 6))

        for index, (kod, ad, zorunlu) in enumerate(self._aktif_kural()["belgeler"], start=1):
            ttk.Label(self.frm_evrak, text=ad).grid(
                row=index, column=0, sticky="w", padx=(4, 8), pady=4)
            teslim = tk.IntVar(value=0)
            chk = ttk.Checkbutton(
                self.frm_evrak,
                text="Zorunlu" if zorunlu else "Opsiyonel",
                variable=teslim,
            )
            chk.grid(row=index, column=1, sticky="w", padx=(4, 8), pady=4)
            not_var = tk.StringVar()
            ttk.Entry(self.frm_evrak, textvariable=not_var, width=48).grid(
                row=index, column=2, sticky="ew", padx=(0, 8), pady=4)
            self._evrak_satirlari[kod] = {
                "ad": ad,
                "zorunlu": zorunlu,
                "teslim": teslim,
                "notlar": not_var,
            }
        self.frm_evrak.columnconfigure(2, weight=1)

    def _mevcut_kaydi_yukle(self):
        referans_turu, referans_id = self._secili_referans()
        if referans_turu != "serbest" and not referans_id:
            self._satirlari_sifirla()
            return
        kayitlar = db.evrak_kontrol_getir(
            self.v_basvuru.get(),
            referans_turu,
            referans_id=referans_id,
            sezon=self.v_sezon.get().strip(),
        )
        self._satirlari_sifirla()
        for kayit in kayitlar:
            satir = self._evrak_satirlari.get(kayit["belge_kodu"])
            if not satir:
                continue
            satir["teslim"].set(kayit["teslim"])
            satir["notlar"].set(kayit["notlar"] or "")

    def _satirlari_sifirla(self):
        for satir in self._evrak_satirlari.values():
            satir["teslim"].set(0)
            satir["notlar"].set("")

    def _kaydet(self):
        referans_turu, referans_id = self._secili_referans()
        if referans_turu != "serbest" and not referans_id:
            messagebox.showwarning("Uyarı", "Önce ilgili sporcu veya kulüp seçin.")
            return
        kalemler = []
        for kod, satir in self._evrak_satirlari.items():
            kalemler.append({
                "belge_kodu": kod,
                "belge_adi": satir["ad"],
                "zorunlu": satir["zorunlu"],
                "teslim": satir["teslim"].get(),
                "notlar": satir["notlar"].get().strip(),
            })
        db.evrak_kontrol_kaydet(
            self.v_basvuru.get(),
            referans_turu,
            kalemler,
            referans_id=referans_id,
            sezon=self.v_sezon.get().strip(),
        )
        self._ozet_listele()
        messagebox.showinfo("Başarılı", "Evrak kontrol kaydı kaydedildi.")

    def _referans_etiketi(self, referans_turu: str, referans_id: int) -> str:
        if referans_turu == "sporcu":
            for ad, sid in self._sporcu_map.items():
                if sid == referans_id:
                    return ad
            return f"Sporcu #{referans_id}"
        if referans_turu == "kulup":
            for ad, kid in self._kulup_map.items():
                if kid == referans_id:
                    return ad
            return f"Kulüp #{referans_id}"
        return "Genel"

    def _ozet_listele(self):
        self.tree_ozet.delete(*self.tree_ozet.get_children())
        self._ozet_map.clear()
        for index, row in enumerate(db.evrak_kontrol_ozet_listele()):
            iid = "|".join([
                row["basvuru_turu"],
                row["referans_turu"],
                str(row["referans_id"]),
                row["sezon"] or "",
            ])
            self._ozet_map[iid] = {
                "basvuru_turu": row["basvuru_turu"],
                "referans_turu": row["referans_turu"],
                "referans_id": row["referans_id"],
                "sezon": row["sezon"],
            }
            tag = "even" if index % 2 == 0 else "odd"
            self.tree_ozet.insert(
                "",
                "end",
                iid=iid,
                values=(
                    row["basvuru_turu"],
                    self._referans_etiketi(row["referans_turu"], row["referans_id"]),
                    row["sezon"] or "—",
                    f"{row['tamamlanan']}/{row['toplam']}",
                    row["guncelleme_tarihi"],
                ),
                tags=(tag,),
            )

    def _on_ozet_sec(self, _=None):
        sel = self.tree_ozet.selection()
        if not sel:
            return
        kayit = self._ozet_map.get(sel[0])
        if not kayit:
            return
        self.v_basvuru.set(kayit["basvuru_turu"])
        self.v_sezon.set(kayit["sezon"] or "")
        self._basvuru_degisti()
        if kayit["referans_turu"] == "sporcu":
            for ad, sid in self._sporcu_map.items():
                if sid == kayit["referans_id"]:
                    self.v_sporcu.set(ad)
                    break
        elif kayit["referans_turu"] == "kulup":
            for ad, kid in self._kulup_map.items():
                if kid == kayit["referans_id"]:
                    self.v_kulup.set(ad)
                    break
        self._mevcut_kaydi_yukle()

    def _temizle(self):
        self.v_sezon.set("2026")
        self._satirlari_sifirla()


# ---------------------------------------------------------------------------
# Ana uygulama
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Sekmeler ilk açılışta sorgu yaptığı için DB önce hazır olmalı.
        db.init_db()
        self.title("KTBF – Lisans Kayıt Sistemi")
        _configure_display(self)
        self.configure(bg=BG)
        self.resizable(True, True)
        _style_widget(self)

        # Başlık
        hdr = tk.Frame(self, bg=HEADER, height=38)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="  🚴 Kıbrıs Türk Bisiklet Federasyonu – Lisans Kayıt Sistemi",
                 bg=HEADER, fg="white",
             font=FONT_H).pack(side="left", pady=_scaled(4))

        # Sekmeler
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.kulup_sekme  = KulupSekme(self.nb)
        self.sporcu_sekme = SporcuSekme(self.nb)
        self.yaris_kayit_sekme = YarisKayitSekme(self.nb)
        self.evrak_kontrol_sekme = EvrakKontrolSekme(self.nb)

        self.nb.add(self.kulup_sekme,  text="  🏢 Kulüpler  ")
        self.nb.add(self.sporcu_sekme, text="  🚴 Sporcular  ")
        self.nb.add(self.yaris_kayit_sekme, text="  🏁 Yarış Kayıt  ")
        self.nb.add(self.evrak_kontrol_sekme, text="  📋 Evrak Kontrol  ")

    def _sekme_ac(self, index: int):
        self.nb.select(index)


def main():
    _ensure_tcl_tk_env()
    app = App()
    try:
        app.mainloop()
    except KeyboardInterrupt:
        # Terminalden Ctrl+C ile kapatıldığında gereksiz traceback göstermeyelim.
        pass


if __name__ == "__main__":
    main()
