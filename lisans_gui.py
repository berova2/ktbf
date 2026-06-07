"""
KKTC Bisiklet Federasyonu – Kulüp ve Sporcu Kayıt Arayüzü
==========================================================
Kullanım: python lisans_gui.py
"""

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
        self.v_uyruk    = _lbl_combo(form_frame, "Uyruk",
                                     ["KKTC", "TC", "Diğer"], 4, width=10)
        self.v_uyruk.set("KKTC")
        self.v_pasaport = _lbl_entry(form_frame, "Pasaport No",    5)
        self.v_tel      = _lbl_entry(form_frame, "Telefon",        6)
        self.v_email    = _lbl_entry(form_frame, "E-posta",        7)
        self.v_adres    = _lbl_entry(form_frame, "Adres",          8)
        self.v_sd_kayit = _lbl_check(form_frame,
                                     "Spor Dairesi BYS Kayıtlı (Madde 7A)", 9)

        # Kulüp seçimi — kayıtlı kulüpler veya Ferdi
        ttk.Label(form_frame, text="Kulüp").grid(
            row=10, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_kulup = tk.StringVar(value="— Ferdi —")
        self.cb_kulup = ttk.Combobox(form_frame, textvariable=self.v_kulup,
                                     width=24, state="readonly")
        self.cb_kulup.grid(row=10, column=1, columnspan=2,
                           sticky="ew", padx=(0, 8), pady=4)

        # Lisans türü
        self.v_lisans_turu = _lbl_combo(
            form_frame, "Lisans Türü",
            ["Ulusal", "Uluslararası", "Ferdi", "Geçici", "MisafirSporcu"],
            11, width=16)
        self.v_lisans_turu.set("Ulusal")

        # Sezon
        self.v_sezon = _lbl_entry(form_frame, "Sezon", 12, width=10)
        self.v_sezon.set("2026")

        # Üretilen lisans no (salt okunur, kayıt sonrası dolar)
        ttk.Label(form_frame, text="Lisans No").grid(
            row=13, column=0, sticky="e", padx=(8, 4), pady=4)
        self.v_lisans_no = tk.StringVar(value="—")
        ttk.Label(form_frame, textvariable=self.v_lisans_no,
                  foreground=ACCENT, font=FONT_B).grid(
            row=13, column=1, sticky="w", padx=(0, 8), pady=4)

        form_frame.columnconfigure(1, weight=1)

        btn = ttk.Frame(form_frame)
        btn.grid(row=14, column=0, columnspan=3, pady=(12, 4))
        ttk.Button(btn, text="➕ Kaydet",           style="Add.TButton",
                   command=self._kaydet).pack(side="left", padx=4)
        ttk.Button(btn, text="✏️ Güncelle",         style="Upd.TButton",
                   command=self._guncelle).pack(side="left", padx=4)
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
        SELECT s.id, s.ad, s.soyad, s.kimlik_no, s.dogum_tarihi,
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
                uyruk=self.v_uyruk.get() or "KKTC",
                pasaport_no=self.v_pasaport.get() or None,
                telefon=self.v_tel.get() or None,
                email=self.v_email.get() or None,
                adres=self.v_adres.get() or None,
                spor_dairesi_kayitli=self.v_sd_kayit.get(),
            )
            if self.v_sd_kayit.get():
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
            else:
                self.v_lisans_no.set("—")
                messagebox.showinfo("Başarılı",
                                    "Sporcu kaydedildi.\n"
                                    "⚠ BYS kaydı olmadığından lisans oluşturulmadı.")
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

    # ------------------------------------------------------------------
    def _temizle(self):
        for v in (self.v_ad, self.v_soyad, self.v_kimlik, self.v_dogum,
                  self.v_pasaport, self.v_tel, self.v_email, self.v_adres):
            v.set("")
        self.v_uyruk.set("KKTC")
        self.v_sd_kayit.set(0)
        self.v_kulup.set("— Ferdi —")
        self.v_lisans_turu.set("Ulusal")
        self.v_sezon.set("2026")
        self.v_lisans_no.set("—")
        self._secili_id = None
        self.tree.selection_remove(*self.tree.selection())


# ---------------------------------------------------------------------------
# Ana uygulama
# ---------------------------------------------------------------------------

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KTBF – Lisans Kayıt Sistemi")
        self.geometry("1100x640")
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
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=6, pady=6)

        self.kulup_sekme  = KulupSekme(nb)
        self.sporcu_sekme = SporcuSekme(nb)

        nb.add(self.kulup_sekme,  text="  🏢 Kulüpler  ")
        nb.add(self.sporcu_sekme, text="  🚴 Sporcular  ")

        # DB'yi başlat
        db.init_db()


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
