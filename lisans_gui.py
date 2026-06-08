"""
KKTC Bisiklet Federasyonu – Kulüp ve Sporcu Kayıt Arayüzü
==========================================================
Kullanım: python lisans_gui.py
"""

import os
import sys
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
FONT     = ("Segoe UI", 10)
FONT_B   = ("Segoe UI", 10, "bold")
FONT_H   = ("Segoe UI", 13, "bold")


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


def _style_widget(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    style.theme_use("clam")
    style.configure("TFrame",       background=BG)
    style.configure("TLabel",       background=BG, font=FONT)
    style.configure("TEntry",       font=FONT, padding=3)
    style.configure("TCombobox",    font=FONT)
    style.configure("Header.TLabel", background=HEADER, foreground="white",
                    font=FONT_H, padding=8)
    style.configure("Treeview",      font=FONT, rowheight=26)
    style.configure("Treeview.Heading", font=FONT_B,
                    background=HEADER, foreground="white")
    style.map("Treeview.Heading",
              background=[("active", ACCENT)])
    style.configure("Add.TButton",   font=FONT_B, background=BTN_ADD,
                    foreground="white", padding=5)
    style.configure("Upd.TButton",   font=FONT_B, background=BTN_UPD,
                    foreground="white", padding=5)
    style.configure("Del.TButton",   font=FONT_B, background=BTN_DEL,
                    foreground="white", padding=5)
    style.configure("Neu.TButton",   font=FONT_B, background=ACCENT,
                    foreground="white", padding=5)
    return style


# ---------------------------------------------------------------------------
# Yardımcı widgetlar
# ---------------------------------------------------------------------------

def _lbl_entry(parent, text, row, col=0, width=22, colspan=1):
    ttk.Label(parent, text=text).grid(row=row, column=col,
                                       sticky="e", padx=(8, 4), pady=4)
    var = tk.StringVar()
    e = ttk.Entry(parent, textvariable=var, width=width)
    e.grid(row=row, column=col + 1, columnspan=colspan,
           sticky="ew", padx=(0, 8), pady=4)
    return var


def _lbl_combo(parent, text, values, row, col=0, width=22):
    ttk.Label(parent, text=text).grid(row=row, column=col,
                                       sticky="e", padx=(8, 4), pady=4)
    var = tk.StringVar()
    cb = ttk.Combobox(parent, textvariable=var, values=values,
                      width=width - 2, state="readonly")
    cb.grid(row=row, column=col + 1, sticky="ew", padx=(0, 8), pady=4)
    return var


def _lbl_check(parent, text, row, col=0):
    var = tk.IntVar()
    chk = ttk.Checkbutton(parent, text=text, variable=var)
    chk.grid(row=row, column=col, columnspan=2,
             sticky="w", padx=(60, 8), pady=2)
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
        tree.column(cid, width=cw, minwidth=40)
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
                  font=("Segoe UI", 8), foreground="gray"
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
                                     width=24, state="readonly")
        self.cb_kulup.grid(row=11, column=1, columnspan=2,
                           sticky="ew", padx=(0, 8), pady=4)

        # Lisans türü
        self.v_lisans_turu = _lbl_combo(
            form_frame, "Lisans Türü",
            ["Ulusal", "Uluslararası", "Ferdi", "Geçici", "MisafirSporcu"],
            12, width=16)
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

        form_frame.columnconfigure(1, weight=1)

        btn = ttk.Frame(form_frame)
        btn.grid(row=15, column=0, columnspan=3, pady=(12, 4))
        ttk.Button(btn, text="➕ Kaydet",           style="Add.TButton",
                   command=self._kaydet).pack(side="left", padx=4)
        ttk.Button(btn, text="✏️ Güncelle",         style="Upd.TButton",
                   command=self._guncelle).pack(side="left", padx=4)
        ttk.Button(btn, text="🗑 Sil",               style="Del.TButton",
               command=self._sil).pack(side="left", padx=4)
        ttk.Button(btn, text="🔄 Kulüpleri Yenile", style="Neu.TButton",
                   command=self._yukle_kulupler).pack(side="left", padx=4)
        ttk.Button(btn, text="✖ Temizle",           style="Neu.TButton",
                   command=self._temizle).pack(side="left", padx=4)

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
            ("uyruk","Uyruk",48), ("telefon","Telefon",100),
            ("lisans_no","Lisans No",88), ("kulup_adi","Kulüp",130),
            ("spor_dairesi_kayitli","BYS",38)]
        tf, self.tree = _make_tree(list_frame, cols)
        tf.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_sec)

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
                """SELECT l.lisans_no, l.lisans_turu, l.sezon, k.ad AS kulup_adi
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
        else:
            self.v_lisans_no.set("—")

    # ------------------------------------------------------------------
    def _kaydet(self):
        if not all([self.v_ad.get().strip(),
                    self.v_soyad.get().strip(),
                    self.v_kimlik.get().strip()]):
            messagebox.showwarning("Uyarı", "Ad, Soyad ve Kimlik No zorunludur.")
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
            )
            with db.get_conn() as conn:
                lis = conn.execute(
                    "SELECT lisans_no FROM lisanslar WHERE id=?", (lid,)
                ).fetchone()
            no = lis["lisans_no"] if lis else "—"
            self.v_lisans_no.set(no)
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
        try:
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
        ttk.Label(ust, text="(YYYY-AA-GG)", font=("Segoe UI", 8),
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

    def _kayit_penceresi_ac(self):
        win = tk.Toplevel(self)
        win.title("Yarışa Sporcu Kayıt")
        win.geometry("1500x900+0+0")
        win.configure(bg=BG)

        top = ttk.Frame(win)
        top.pack(fill="x", padx=8, pady=8)
        ttk.Label(top, text="Yarış:").pack(side="left", padx=(0, 6))

        v_yaris = tk.StringVar(value=self.v_kayit_yaris.get())
        cb = ttk.Combobox(
            top,
            textvariable=v_yaris,
            values=list(self._yaris_map.keys()),
            state="readonly",
            width=34,
        )
        cb.pack(side="left", padx=(0, 8))

        ttk.Label(top, text="Sporcu:").pack(side="left", padx=(6, 6))
        v_sporcu = tk.StringVar()
        cb_sporcu = ttk.Combobox(top, textvariable=v_sporcu,
                                 state="readonly", width=42)
        cb_sporcu.pack(side="left", padx=(0, 8))

        ttk.Label(top, text="Kategori:").pack(side="left", padx=(6, 6))
        v_kategori = tk.StringVar(value="Elite")
        cb_kat = ttk.Combobox(
            top,
            textvariable=v_kategori,
            values=["Elite", "Junior", "U17", "U15", "Master 1", "Master 2", "Master 3", "Diğer"],
            state="readonly",
            width=10,
        )
        cb_kat.pack(side="left", padx=(0, 8))

        ttk.Label(top, text="Kayıt Durumu:").pack(side="left", padx=(6, 6))
        v_durum = tk.StringVar(value="Onaylandı")
        cb_durum = ttk.Combobox(
            top,
            textvariable=v_durum,
            values=["Onaylandı", "Beklemede", "İptal"],
            state="readonly",
            width=10,
        )
        cb_durum.pack(side="left", padx=(0, 8))

        cols = [
            ("id", "ID", 42),
            ("yaris_adi", "Yarış", 190),
            ("yaris_tarihi", "Yarış Tarihi", 95),
            ("sporcu", "Sporcu", 180),
            ("lisans_no", "Lisans No", 90),
            ("kategori", "Kategori", 90),
            ("durum", "Durum", 85),
            ("kayit_tarihi", "Kayıt Tarihi", 95),
        ]
        tf, tree = _make_tree(win, cols)
        tf.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        sporcu_map: dict = {}

        def refresh_sporcular(yaris_id):
            nonlocal sporcu_map
            kayitli = db.yarisa_kayitli_sporcu_idleri(yaris_id) if yaris_id else set()
            rows = db.aktif_lisansli_sporcular()
            sporcu_map = {
                f"{r['ad_soyad']} | {r['lisans_no']} | {r['kulup_adi']}": (r["sporcu_id"], r["lisans_id"])
                for r in rows
                if r["sporcu_id"] not in kayitli
            }
            cb_sporcu["values"] = list(sporcu_map.keys())
            if v_sporcu.get() not in sporcu_map:
                v_sporcu.set("")
            if sporcu_map and not v_sporcu.get():
                v_sporcu.set(list(sporcu_map.keys())[0])

        def refresh(_=None):
            sec = v_yaris.get().strip()
            yaris_id = self._yaris_map.get(sec) if sec else None
            rows = db.yaris_kayitlari_listele(yaris_id)
            _fill_tree(tree, rows)
            refresh_sporcular(yaris_id)

        def kayit_ekle_popup():
            sec = v_yaris.get().strip()
            yaris_id = self._yaris_map.get(sec) if sec else None
            sporcu_info = sporcu_map.get(v_sporcu.get().strip())
            if not yaris_id or not sporcu_info:
                messagebox.showwarning(
                    "Uyarı",
                    "Kayıt için açık yarış ve sporcu seçimi zorunludur.",
                    parent=win,
                )
                return
            sporcu_id, lisans_id = sporcu_info
            try:
                db.yaris_kayit_ekle(
                    yaris_id=yaris_id,
                    sporcu_id=sporcu_id,
                    lisans_id=lisans_id,
                    kategori=v_kategori.get() or None,
                )
                refresh()
                messagebox.showinfo("Başarılı", "Sporcu yarışa kaydedildi.", parent=win)
            except Exception as exc:
                messagebox.showerror("Hata", str(exc), parent=win)

        def kayit_sil_popup():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Uyarı", "Silmek için bir kayıt seçin.", parent=win)
                return
            kayit_id = int(sel[0])
            if not messagebox.askyesno("Onay", "Seçili yarış kaydı silinsin mi?", parent=win):
                return
            db.yaris_kayit_sil(kayit_id)
            refresh()
            messagebox.showinfo("Başarılı", "Yarış kaydı silindi.", parent=win)

        def kayit_guncelle_popup():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Uyarı", "Güncellemek için bir kayıt seçin.", parent=win)
                return
            kayit_id = int(sel[0])
            try:
                db.yaris_kayit_guncelle(
                    kayit_id,
                    kategori=v_kategori.get() or None,
                    durum=v_durum.get() or None,
                )
                refresh()
                messagebox.showinfo("Başarılı", "Yarış kaydı güncellendi.", parent=win)
            except Exception as exc:
                messagebox.showerror("Hata", str(exc), parent=win)

        ttk.Button(top, text="➕ Kaydı Oluştur", style="Add.TButton",
                   command=kayit_ekle_popup).pack(side="left", padx=(4, 4))
        ttk.Button(top, text="✏️ Seçili Kaydı Güncelle", style="Upd.TButton",
               command=kayit_guncelle_popup).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="✖ Seçili Kaydı Sil", style="Del.TButton",
                   command=kayit_sil_popup).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="Yenile", style="Neu.TButton",
                   command=refresh).pack(side="left")

        def on_tree_sec(_=None):
            sel = tree.selection()
            if not sel:
                return
            vals = tree.item(sel[0], "values")
            if len(vals) >= 7:
                v_kategori.set(vals[5] if vals[5] != "—" else "Elite")
                v_durum.set(vals[6] or "Onaylandı")

        tree.bind("<<TreeviewSelect>>", on_tree_sec)
        cb.bind("<<ComboboxSelected>>", refresh)
        refresh()


# ---------------------------------------------------------------------------
# Ana uygulama
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        # Sekmeler ilk açılışta sorgu yaptığı için DB önce hazır olmalı.
        db.init_db()
        self.title("KTBF – Lisans Kayıt Sistemi")
        self.geometry("1500x900+0+0")
        self.configure(bg=BG)
        self.resizable(True, True)
        _style_widget(self)

        # Başlık
        hdr = tk.Frame(self, bg=HEADER, height=48)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text="  🚴 Kıbrıs Türk Bisiklet Federasyonu – Lisans Kayıt Sistemi",
                 bg=HEADER, fg="white",
                 font=("Segoe UI", 13, "bold")).pack(side="left", pady=8)

        # Sekmeler
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.kulup_sekme  = KulupSekme(self.nb)
        self.sporcu_sekme = SporcuSekme(self.nb)
        self.yaris_kayit_sekme = YarisKayitSekme(self.nb)

        self.nb.add(self.kulup_sekme,  text="  🏢 Kulüpler  ")
        self.nb.add(self.sporcu_sekme, text="  🚴 Sporcular  ")
        self.nb.add(self.yaris_kayit_sekme, text="  🏁 Yarış Kayıt  ")

        self._build_menu()

    def _build_menu(self):
        menubar = tk.Menu(self)

        modul = tk.Menu(menubar, tearoff=0)
        modul.add_command(label="Kulüpler", command=lambda: self._sekme_ac(0))
        modul.add_command(label="Sporcular", command=lambda: self._sekme_ac(1))
        modul.add_command(label="Yarış Kayıt", command=lambda: self._sekme_ac(2))
        modul.add_separator()
        modul.add_command(
            label="Yarışa Kayıtlı Sporcular Penceresi",
            command=self.yaris_kayit_sekme._kayit_penceresi_ac,
        )

        menubar.add_cascade(label="Modüller", menu=modul)
        self.config(menu=menubar)

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
