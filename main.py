# -*- coding: utf-8 -*-
"""
AMINA FDS - Logiciel de Gestion de Stock
Production et vente de poudre de marbre et dérivés
Auteur: Généré pour AMINA FDS
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import hashlib
import os
import sys
import calendar
from datetime import datetime, timedelta

try:
    from PIL import Image, ImageTk, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# ------------------------------------------------------------------
# CONFIGURATION GENERALE
# ------------------------------------------------------------------
APP_TITLE = "AMINA FDS - Gestion de Stock"

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, "anima_fds.db")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "logo.jpg")
MUR_PATH = os.path.join(ASSETS_DIR, "mur.jpg")
TVA_TAUX = 0.18

# ------------------------------------------------------------------
# PERIODE D'ESSAI
# ------------------------------------------------------------------
ESSAI_NB_JOURS = 7
# Hash SHA-256 du code de déverrouillage (le code en clair n'apparaît jamais dans le code source)
CODE_DEVERROUILLAGE_HASH = "cab96e5dc35bafa25db541e7f7707323abcecbb98d592e3b8f243d06bb83ee53"

COLOR_PRIMARY = "#7a4a2b"      # marron marbre/terre
COLOR_PRIMARY_DARK = "#5c3720"
COLOR_ACCENT = "#c9a15a"       # doré/beige marbre
COLOR_BG = "#f4f1ec"
COLOR_SIDEBAR = "#2e2a26"
COLOR_SIDEBAR_TEXT = "#f4f1ec"
COLOR_DANGER = "#a83232"
COLOR_SUCCESS = "#2f7a3e"
FONT_TITLE = ("Segoe UI", 18, "bold")
FONT_SUBTITLE = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_BOLD = ("Segoe UI", 10, "bold")

TYPES_PRODUITS = {
    "MP": "matieres_premieres",
    "PSF": "produits_semi_finis",
    "PF": "produits_finis",
}
TYPE_LABELS = {
    "MP": "Matière première",
    "PSF": "Produit semi-fini",
    "PF": "Produit fini",
}

# ------------------------------------------------------------------
# IMAGES / IDENTITE VISUELLE
# ------------------------------------------------------------------
_image_cache = {}


def load_logo(size=140):
    """Retourne le logo AMINA FDS (rogné en cercle) en PhotoImage, ou None si indisponible."""
    if not PIL_AVAILABLE or not os.path.exists(LOGO_PATH):
        return None
    key = ("logo", size)
    if key in _image_cache:
        return _image_cache[key]
    try:
        im = Image.open(LOGO_PATH).convert("RGBA")
        side = min(im.size)
        im = im.crop((0, 0, side, side)).resize((size, size), Image.LANCZOS)
        mask = Image.new("L", (size, size), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, size, size), fill=255)
        im.putalpha(mask)
        photo = ImageTk.PhotoImage(im)
        _image_cache[key] = photo
        return photo
    except Exception:
        return None


def load_banner(width=900, height=90):
    """Retourne une bannière décorative découpée dans l'image murale, ou None."""
    if not PIL_AVAILABLE or not os.path.exists(MUR_PATH):
        return None
    key = ("banner", width, height)
    if key in _image_cache:
        return _image_cache[key]
    try:
        im = Image.open(MUR_PATH).convert("RGB")
        # Redimensionner en conservant le ratio puis rogner en bande centrale
        ratio = width / im.width
        new_h = int(im.height * ratio)
        im = im.resize((width, new_h), Image.LANCZOS)
        top = max(0, (new_h - height) // 2)
        im = im.crop((0, top, width, top + height))
        photo = ImageTk.PhotoImage(im)
        _image_cache[key] = photo
        return photo
    except Exception:
        return None


def load_side_texture(width=210, height=140):
    """Petite vignette décorative (bas de la barre latérale)."""
    if not PIL_AVAILABLE or not os.path.exists(MUR_PATH):
        return None
    key = ("side", width, height)
    if key in _image_cache:
        return _image_cache[key]
    try:
        im = Image.open(MUR_PATH).convert("RGB")
        ratio = max(width / im.width, height / im.height)
        new_w, new_h = int(im.width * ratio), int(im.height * ratio)
        im = im.resize((new_w, new_h), Image.LANCZOS)
        left = (new_w - width) // 2
        top = (new_h - height) // 2
        im = im.crop((left, top, left + width, top + height))
        photo = ImageTk.PhotoImage(im)
        _image_cache[key] = photo
        return photo
    except Exception:
        return None


# ------------------------------------------------------------------
# BASE DE DONNEES
# ------------------------------------------------------------------

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS config (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        entreprise TEXT DEFAULT 'AMINA FDS',
        pseudo TEXT,
        pwd1_hash TEXT,
        pwd2_hash TEXT,
        configured INTEGER DEFAULT 0
    )""")
    for table in TYPES_PRODUITS.values():
        extra = ", prix_vente REAL DEFAULT 0" if table == "produits_finis" else ""
        c.execute(f"""CREATE TABLE IF NOT EXISTS {table} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT UNIQUE NOT NULL,
            quantite REAL DEFAULT 0,
            cout REAL DEFAULT 0
            {extra}
        )""")
    c.execute("""CREATE TABLE IF NOT EXISTS stock_journal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_heure TEXT,
        type_produit TEXT,
        produit_nom TEXT,
        quantite REAL,
        action TEXT,
        utilisateur TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS factures (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero TEXT UNIQUE,
        date_heure TEXT,
        date_jour TEXT,
        client_nom TEXT,
        client_tel TEXT,
        client_adresse TEXT,
        total REAL,
        utilisateur TEXT,
        modifiee INTEGER DEFAULT 0,
        tva_active INTEGER DEFAULT 0,
        montant_ht REAL DEFAULT 0,
        montant_tva REAL DEFAULT 0
    )""")
    # Migration douce pour les bases déjà existantes (avant l'ajout de la TVA)
    existing_cols = [r["name"] for r in c.execute("PRAGMA table_info(factures)").fetchall()]
    for col, ddl in [("tva_active", "INTEGER DEFAULT 0"), ("montant_ht", "REAL DEFAULT 0"), ("montant_tva", "REAL DEFAULT 0")]:
        if col not in existing_cols:
            c.execute(f"ALTER TABLE factures ADD COLUMN {col} {ddl}")
    c.execute("""CREATE TABLE IF NOT EXISTS prestations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_jour TEXT,
        date_heure TEXT,
        libelle TEXT,
        montant REAL,
        utilisateur TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS facture_lignes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        facture_id INTEGER,
        type_produit TEXT,
        produit_nom TEXT,
        quantite REAL,
        prix_unitaire REAL,
        sous_total REAL,
        FOREIGN KEY (facture_id) REFERENCES factures(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS depenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_jour TEXT,
        date_heure TEXT,
        description TEXT,
        montant REAL,
        utilisateur TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS journees (
        date_jour TEXT PRIMARY KEY,
        cloturee INTEGER DEFAULT 0,
        cloturee_par TEXT,
        date_cloture TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS licence (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        date_installation TEXT,
        debloquee INTEGER DEFAULT 0
    )""")
    conn.commit()
    conn.close()


def hash_pwd(pwd):
    return hashlib.sha256(pwd.encode("utf-8")).hexdigest()


def now_str():
    return datetime.now().strftime("%d/%m/%Y %H:%M:%S")


def today_str():
    return datetime.now().strftime("%Y-%m-%d")


def yesterday_str():
    return (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")


def fmt_date_fr(d):
    return datetime.strptime(d, "%Y-%m-%d").strftime("%d/%m/%Y")


def is_configured():
    conn = get_conn()
    row = conn.execute("SELECT configured FROM config WHERE id=1").fetchone()
    conn.close()
    return bool(row and row["configured"] == 1)


# ------------------------------------------------------------------
# GESTION DE LA PERIODE D'ESSAI
# ------------------------------------------------------------------
def get_licence_row():
    """Crée (si besoin) et retourne la ligne licence, en fixant la date d'installation
    lors du tout premier lancement de l'application."""
    conn = get_conn()
    row = conn.execute("SELECT * FROM licence WHERE id=1").fetchone()
    if row is None:
        conn.execute(
            "INSERT INTO licence (id, date_installation, debloquee) VALUES (1, ?, 0)",
            (today_str(),))
        conn.commit()
        row = conn.execute("SELECT * FROM licence WHERE id=1").fetchone()
    conn.close()
    return row


def jours_ecoules_depuis_installation():
    row = get_licence_row()
    try:
        d_install = datetime.strptime(row["date_installation"], "%Y-%m-%d")
    except Exception:
        d_install = datetime.now()
    return (datetime.now() - d_install).days


def licence_est_valide():
    """Retourne True si l'application peut être utilisée : période d'essai encore
    en cours, ou code de déverrouillage déjà saisi avec succès."""
    row = get_licence_row()
    if row["debloquee"] == 1:
        return True
    return jours_ecoules_depuis_installation() < ESSAI_NB_JOURS


def tenter_deverrouillage(code):
    """Vérifie le code saisi ; si correct, débloque définitivement l'application."""
    if hash_pwd(code.strip()) != CODE_DEVERROUILLAGE_HASH:
        return False
    conn = get_conn()
    conn.execute("UPDATE licence SET debloquee=1 WHERE id=1")
    conn.commit()
    conn.close()
    return True


def is_journee_cloturee(date_jour=None):
    date_jour = date_jour or today_str()
    conn = get_conn()
    row = conn.execute("SELECT cloturee FROM journees WHERE date_jour=?", (date_jour,)).fetchone()
    conn.close()
    return bool(row and row["cloturee"] == 1)


def log_mouvement(type_produit, produit_nom, quantite, action, utilisateur):
    conn = get_conn()
    conn.execute(
        "INSERT INTO stock_journal (date_heure, type_produit, produit_nom, quantite, action, utilisateur) VALUES (?,?,?,?,?,?)",
        (now_str(), type_produit, produit_nom, quantite, action, utilisateur))
    conn.commit()
    conn.close()


def get_stock(type_code):
    table = TYPES_PRODUITS[type_code]
    conn = get_conn()
    rows = conn.execute(f"SELECT * FROM {table} ORDER BY nom").fetchall()
    conn.close()
    return rows


def get_prestations_total(date_debut, date_fin):
    conn = get_conn()
    row = conn.execute("SELECT COALESCE(SUM(montant),0) as t, COUNT(*) as n FROM prestations WHERE date_jour BETWEEN ? AND ?",
                       (date_debut, date_fin)).fetchone()
    conn.close()
    return row["t"], row["n"]


def generate_numero_facture():
    prefix = f"F-{datetime.now().strftime('%Y%m%d')}"
    conn = get_conn()
    count = conn.execute(
        "SELECT COUNT(*) as c FROM factures WHERE numero LIKE ?", (prefix + "%",)).fetchone()["c"]
    conn.close()
    return f"{prefix}-{count + 1:03d}"


# ------------------------------------------------------------------
# WIDGET CALENDRIER (sélecteur de date simple, sans dépendance externe)
# ------------------------------------------------------------------
class DatePickerEntry(ttk.Frame):
    def __init__(self, parent, initial_date=None, **kwargs):
        super().__init__(parent, **kwargs)
        self.date_var = tk.StringVar(value=initial_date or today_str())
        self.entry = ttk.Entry(self, textvariable=self.date_var, width=12, state="readonly")
        self.entry.pack(side="left", padx=(0, 4))
        btn = ttk.Button(self, text="📅", width=3, command=self.open_calendar)
        btn.pack(side="left")

    def get(self):
        return self.date_var.get()

    def open_calendar(self):
        top = tk.Toplevel(self)
        top.title("Sélectionner une date")
        top.grab_set()
        top.configure(bg="white")

        try:
            cur = datetime.strptime(self.date_var.get(), "%Y-%m-%d")
        except Exception:
            cur = datetime.now()
        state = {"year": cur.year, "month": cur.month}

        header = tk.Frame(top, bg=COLOR_PRIMARY)
        header.pack(fill="x")
        lbl_month = tk.Label(header, font=FONT_BOLD, bg=COLOR_PRIMARY, fg="white", width=20)
        lbl_month.pack(side="left", padx=10, pady=8)

        nav = tk.Frame(header, bg=COLOR_PRIMARY)
        nav.pack(side="right", padx=6)

        grid_frame = tk.Frame(top, bg="white")
        grid_frame.pack(padx=10, pady=10)

        def draw():
            for w in grid_frame.winfo_children():
                w.destroy()
            lbl_month.config(text=calendar.month_name[state["month"]] + " " + str(state["year"]))
            jours = ["Lu", "Ma", "Me", "Je", "Ve", "Sa", "Di"]
            for i, j in enumerate(jours):
                tk.Label(grid_frame, text=j, font=FONT_BOLD, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=0, column=i, padx=2, pady=2)
            cal = calendar.Calendar(firstweekday=0)
            row = 1
            for week in cal.monthdayscalendar(state["year"], state["month"]):
                for col, day in enumerate(week):
                    if day == 0:
                        tk.Label(grid_frame, text="", bg="white", width=3).grid(row=row, column=col)
                    else:
                        b = tk.Button(grid_frame, text=str(day), width=3, relief="flat",
                                      bg="white", activebackground=COLOR_ACCENT,
                                      command=lambda d=day: choose(d))
                        b.grid(row=row, column=col, padx=1, pady=1)
                row += 1

        def choose(day):
            d = datetime(state["year"], state["month"], day)
            self.date_var.set(d.strftime("%Y-%m-%d"))
            top.destroy()

        def prev_month():
            m, y = state["month"] - 1, state["year"]
            if m == 0:
                m, y = 12, y - 1
            state["month"], state["year"] = m, y
            draw()

        def next_month():
            m, y = state["month"] + 1, state["year"]
            if m == 13:
                m, y = 1, y + 1
            state["month"], state["year"] = m, y
            draw()

        tk.Button(nav, text="◀", command=prev_month, relief="flat",
                  bg=COLOR_PRIMARY, fg="white", activebackground=COLOR_PRIMARY_DARK).pack(side="left", padx=2)
        tk.Button(nav, text="▶", command=next_month, relief="flat",
                  bg=COLOR_PRIMARY, fg="white", activebackground=COLOR_PRIMARY_DARK).pack(side="left", padx=2)

        draw()


# ------------------------------------------------------------------
# APPLICATION PRINCIPALE
# ------------------------------------------------------------------
class AnimaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1200x760")
        self.minsize(1024, 680)
        self.configure(bg=COLOR_BG)

        self.style = ttk.Style(self)
        try:
            self.style.theme_use("clam")
        except Exception:
            pass
        self.style.configure("TButton", font=FONT_NORMAL, padding=6)
        self.style.configure("Primary.TButton", font=FONT_BOLD)
        self.style.configure("Treeview", font=FONT_NORMAL, rowheight=26)
        self.style.configure("Treeview.Heading", font=FONT_BOLD)

        self.session = {"pseudo": None, "level": None}  # level 1 = secrétaire, 2 = chef

        self.container = tk.Frame(self, bg=COLOR_BG)
        self.container.pack(fill="both", expand=True)

        init_db()

        self.demarrer()

    def demarrer(self):
        """Point d'entrée après le contrôle de licence : lance la configuration
        initiale ou l'écran de connexion selon l'état de l'application."""
        if not licence_est_valide():
            self.show_frame(TrialLockFrame)
            return
        if not is_configured():
            self.show_frame(WelcomeConfigFrame)
        else:
            self.show_frame(LoginFrame)

    def clear_container(self):
        for w in self.container.winfo_children():
            w.destroy()

    def show_frame(self, frame_class, **kwargs):
        self.clear_container()
        frame = frame_class(self.container, self, **kwargs)
        frame.pack(fill="both", expand=True)

    def logout(self):
        self.session = {"pseudo": None, "level": None}
        self.show_frame(LoginFrame)


# ------------------------------------------------------------------
# ECRAN DE VERROUILLAGE (PERIODE D'ESSAI EXPIREE)
# ------------------------------------------------------------------
class TrialLockFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app

        card = tk.Frame(self, bg="white", padx=50, pady=40, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center")

        logo = load_logo(110)
        if logo:
            lbl_logo = tk.Label(card, image=logo, bg="white")
            lbl_logo.image = logo
            lbl_logo.pack(pady=(0, 15))
        else:
            tk.Label(card, text="AMINA FDS", font=("Segoe UI", 24, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(0, 5))

        tk.Label(card, text="Période d'essai terminée", font=FONT_TITLE, bg="white", fg=COLOR_DANGER).pack(pady=(5, 10))
        tk.Label(card, text=f"La période d'essai gratuite de {ESSAI_NB_JOURS} jours de ce logiciel est arrivée à\n"
                             "son terme. Veuillez saisir le code de déverrouillage fourni par\n"
                             "Ecom-Academy pour continuer à utiliser l'application.",
                 font=FONT_NORMAL, bg="white", justify="center").pack(pady=(0, 20))

        tk.Label(card, text="Code de déverrouillage", font=FONT_BOLD, bg="white", fg=COLOR_PRIMARY_DARK).pack()
        self.code_var = tk.StringVar()
        entry = ttk.Entry(card, textvariable=self.code_var, show="*", width=28, justify="center")
        entry.pack(pady=(8, 20))
        entry.bind("<Return>", lambda e: self.valider())
        entry.focus_set()

        ttk.Button(card, text="Déverrouiller", style="Primary.TButton", command=self.valider).pack(ipadx=20, ipady=4)

        tk.Label(card, text="Application créée par Ecom Academy. Contactez-nous sur WhatsApp +22899373635",
                 font=("Segoe UI", 8), bg="white", fg="#777").pack(pady=(25, 0))

    def valider(self):
        code = self.code_var.get()
        if not code:
            messagebox.showerror("Erreur", "Veuillez saisir un code de déverrouillage.")
            return
        if tenter_deverrouillage(code):
            messagebox.showinfo("Succès", "Application déverrouillée. Merci pour votre confiance !")
            self.app.demarrer()
        else:
            messagebox.showerror("Code incorrect", "Le code de déverrouillage saisi est incorrect.")
            self.code_var.set("")


# ------------------------------------------------------------------
# ETAPE 0 : MESSAGE DE BIENVENUE
# ------------------------------------------------------------------
class WelcomeConfigFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app

        card = tk.Frame(self, bg="white", padx=50, pady=40, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center")

        logo = load_logo(130)
        if logo:
            lbl_logo = tk.Label(card, image=logo, bg="white")
            lbl_logo.image = logo
            lbl_logo.pack(pady=(0, 15))
        else:
            tk.Label(card, text="AMINA FDS", font=("Segoe UI", 26, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(0, 5))
        tk.Label(card, text="Production & vente de poudre de marbre", font=FONT_NORMAL, fg="#555", bg="white").pack(pady=(0, 25))

        tk.Label(card, text="Bienvenue DG FDS.", font=FONT_TITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack()
        tk.Label(card, text="Veuillez paramétrer votre application de gestion\navant de commencer à l'utiliser.",
                 font=FONT_NORMAL, bg="white", justify="center").pack(pady=(10, 30))

        ttk.Button(card, text="OK", style="Primary.TButton",
                   command=lambda: app.show_frame(ConfigFormFrame)).pack(ipadx=20, ipady=4)


# ------------------------------------------------------------------
# ETAPE 1 : FORMULAIRE PSEUDO + MOTS DE PASSE
# ------------------------------------------------------------------
class ConfigFormFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app

        card = tk.Frame(self, bg="white", padx=40, pady=30, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center", width=460)

        logo = load_logo(70)
        if logo:
            lbl_logo = tk.Label(card, image=logo, bg="white")
            lbl_logo.image = logo
            lbl_logo.grid(row=0, column=0, columnspan=2, pady=(0, 10))
            title_row = 1
        else:
            title_row = 0
        tk.Label(card, text="Configuration du compte administrateur", font=FONT_SUBTITLE,
                 bg="white", fg=COLOR_PRIMARY_DARK).grid(row=title_row, column=0, columnspan=2, pady=(0, 20))

        labels = ["Pseudo", "Mot de passe niveau 1", "Confirmer mot de passe niveau 1",
                  "Mot de passe niveau 2", "Confirmer mot de passe niveau 2"]
        self.vars = {}
        for i, lbl in enumerate(labels, start=title_row + 1):
            tk.Label(card, text=lbl, font=FONT_NORMAL, bg="white").grid(row=i, column=0, sticky="w", pady=6)
            show = "" if lbl == "Pseudo" else "*"
            var = tk.StringVar()
            ent = ttk.Entry(card, textvariable=var, show=show, width=26)
            ent.grid(row=i, column=1, pady=6, padx=(10, 0))
            self.vars[lbl] = var

        ttk.Button(card, text="Suivant ➜", style="Primary.TButton", command=self.validate).grid(
            row=title_row + len(labels) + 1, column=0, columnspan=2, pady=(20, 0), ipadx=10, ipady=4)

    def validate(self):
        v = {k: val.get().strip() for k, val in self.vars.items()}
        if not v["Pseudo"]:
            messagebox.showerror("Erreur", "Le pseudo est obligatoire.")
            return
        if not v["Mot de passe niveau 1"] or not v["Mot de passe niveau 2"]:
            messagebox.showerror("Erreur", "Les mots de passe niveau 1 et niveau 2 sont obligatoires.")
            return
        if v["Mot de passe niveau 1"] != v["Confirmer mot de passe niveau 1"]:
            messagebox.showerror("Erreur", "La confirmation du mot de passe niveau 1 ne correspond pas.")
            return
        if v["Mot de passe niveau 2"] != v["Confirmer mot de passe niveau 2"]:
            messagebox.showerror("Erreur", "La confirmation du mot de passe niveau 2 ne correspond pas.")
            return
        if v["Mot de passe niveau 1"] == v["Mot de passe niveau 2"]:
            messagebox.showerror("Erreur", "Les mots de passe niveau 1 et niveau 2 doivent être différents.")
            return

        conn = get_conn()
        conn.execute("""INSERT INTO config (id, entreprise, pseudo, pwd1_hash, pwd2_hash, configured)
                        VALUES (1, 'AMINA FDS', ?, ?, ?, 0)
                        ON CONFLICT(id) DO UPDATE SET pseudo=excluded.pseudo,
                        pwd1_hash=excluded.pwd1_hash, pwd2_hash=excluded.pwd2_hash""",
                     (v["Pseudo"], hash_pwd(v["Mot de passe niveau 1"]), hash_pwd(v["Mot de passe niveau 2"])))
        conn.commit()
        conn.close()
        self.app.show_frame(StockInitFrame, type_code="MP")


# ------------------------------------------------------------------
# ETAPES 2-3-4 : SAISIE DES STOCKS INITIAUX
# ------------------------------------------------------------------
class StockInitFrame(tk.Frame):
    STEP_ORDER = ["MP", "PSF", "PF"]
    STEP_TITLES = {
        "MP": "Matières premières en stock",
        "PSF": "Produits semi-finis en stock",
        "PF": "Produits finis en stock",
    }

    def __init__(self, parent, app, type_code="MP"):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        self.type_code = type_code

        wrap = tk.Frame(self, bg=COLOR_BG)
        wrap.place(relx=0.5, rely=0.5, anchor="center", width=650)

        header = tk.Frame(wrap, bg=COLOR_BG)
        header.pack(pady=(0, 15))
        logo = load_logo(50)
        if logo:
            lbl_logo = tk.Label(header, image=logo, bg=COLOR_BG)
            lbl_logo.image = logo
            lbl_logo.pack(side="left", padx=(0, 12))
        step_idx = self.STEP_ORDER.index(type_code) + 1
        tk.Label(header, text=f"Étape {step_idx + 1}/4 — {self.STEP_TITLES[type_code]}",
                 font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(side="left")

        form = tk.Frame(wrap, bg="white", padx=25, pady=20, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        form.pack(fill="x")

        tk.Label(form, text="Nom du produit", font=FONT_NORMAL, bg="white").grid(row=0, column=0, sticky="w", pady=6)
        self.nom_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.nom_var, width=25).grid(row=0, column=1, padx=10)

        tk.Label(form, text="Quantité (Kg)", font=FONT_NORMAL, bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.qte_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.qte_var, width=25).grid(row=1, column=1, padx=10)

        tk.Label(form, text="Coût (unité/Kg)", font=FONT_NORMAL, bg="white").grid(row=2, column=0, sticky="w", pady=6)
        self.cout_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.cout_var, width=25).grid(row=2, column=1, padx=10)

        next_row = 3
        self.prix_var = None
        if type_code == "PF":
            tk.Label(form, text="Prix de vente (unité/Kg)", font=FONT_NORMAL, bg="white").grid(row=3, column=0, sticky="w", pady=6)
            self.prix_var = tk.StringVar(value="0")
            ttk.Entry(form, textvariable=self.prix_var, width=25).grid(row=3, column=1, padx=10)
            next_row = 4

        ttk.Button(form, text="Enregistrer", command=self.enregistrer).grid(row=next_row, column=0, columnspan=2, pady=(15, 0), ipadx=10)

        # Liste des éléments déjà enregistrés
        tk.Label(wrap, text="Éléments enregistrés :", font=FONT_BOLD, bg=COLOR_BG).pack(anchor="w", pady=(15, 5))
        cols = ("nom", "qte", "cout") if type_code != "PF" else ("nom", "qte", "cout", "prix")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=6)
        headers = {"nom": "Nom", "qte": "Quantité (Kg)", "cout": "Coût", "prix": "Prix de vente"}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=140, anchor="center")
        self.tree.pack(fill="x")

        btn_frame = tk.Frame(wrap, bg=COLOR_BG)
        btn_frame.pack(pady=20)
        label_next = "Terminer ✔" if type_code == "PF" else "Suivant ➜"
        ttk.Button(btn_frame, text=label_next, style="Primary.TButton", command=self.next_step).pack(ipadx=15, ipady=4)

        self.refresh_list()

    def enregistrer(self):
        nom = self.nom_var.get().strip()
        if not nom:
            messagebox.showerror("Erreur", "Le nom du produit est obligatoire.")
            return
        try:
            qte = float(self.qte_var.get().replace(",", ".")) if self.qte_var.get() else 0.0
            cout = float(self.cout_var.get().replace(",", ".")) if self.cout_var.get() else 0.0
            prix = float(self.prix_var.get().replace(",", ".")) if self.prix_var else 0.0
        except ValueError:
            messagebox.showerror("Erreur", "Quantité / Coût / Prix doivent être numériques.")
            return

        table = TYPES_PRODUITS[self.type_code]
        conn = get_conn()
        try:
            if self.type_code == "PF":
                conn.execute(f"INSERT INTO {table} (nom, quantite, cout, prix_vente) VALUES (?,?,?,?)",
                             (nom, qte, cout, prix))
            else:
                conn.execute(f"INSERT INTO {table} (nom, quantite, cout) VALUES (?,?,?)", (nom, qte, cout))
            conn.commit()
        except sqlite3.IntegrityError:
            messagebox.showerror("Erreur", f"« {nom} » existe déjà.")
            conn.close()
            return
        conn.close()

        self.nom_var.set("")
        self.qte_var.set("0")
        self.cout_var.set("0")
        if self.prix_var:
            self.prix_var.set("0")
        self.refresh_list()

    def refresh_list(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for row in get_stock(self.type_code):
            if self.type_code == "PF":
                self.tree.insert("", "end", values=(row["nom"], row["quantite"], row["cout"], row["prix_vente"]))
            else:
                self.tree.insert("", "end", values=(row["nom"], row["quantite"], row["cout"]))

    def next_step(self):
        idx = self.STEP_ORDER.index(self.type_code)
        if idx + 1 < len(self.STEP_ORDER):
            self.app.show_frame(StockInitFrame, type_code=self.STEP_ORDER[idx + 1])
        else:
            conn = get_conn()
            conn.execute("UPDATE config SET configured=1 WHERE id=1")
            conn.commit()
            conn.close()
            messagebox.showinfo("Configuration terminée",
                                 "La configuration initiale est terminée. Vous pouvez maintenant vous connecter.")
            self.app.show_frame(LoginFrame)


# ------------------------------------------------------------------
# ECRAN DE CONNEXION
# ------------------------------------------------------------------
class LoginFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app

        card = tk.Frame(self, bg="white", padx=45, pady=35, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        card.place(relx=0.5, rely=0.5, anchor="center")

        logo = load_logo(110)
        if logo:
            lbl_logo = tk.Label(card, image=logo, bg="white")
            lbl_logo.image = logo
            lbl_logo.pack(pady=(0, 10))
        else:
            tk.Label(card, text="AMINA FDS", font=("Segoe UI", 24, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(0, 5))
        tk.Label(card, text="Connexion à votre espace de gestion", font=FONT_NORMAL, fg="#666", bg="white").pack(pady=(0, 25))

        tk.Label(card, text="Pseudo", font=FONT_NORMAL, bg="white").pack(anchor="w")
        self.pseudo_var = tk.StringVar()
        ttk.Entry(card, textvariable=self.pseudo_var, width=30).pack(pady=(2, 15))

        tk.Label(card, text="Mot de passe", font=FONT_NORMAL, bg="white").pack(anchor="w")
        self.pwd_var = tk.StringVar()
        pwd_entry = ttk.Entry(card, textvariable=self.pwd_var, width=30, show="*")
        pwd_entry.pack(pady=(2, 20))
        pwd_entry.bind("<Return>", lambda e: self.connect())

        ttk.Button(card, text="Connexion", style="Primary.TButton", command=self.connect).pack(ipadx=20, ipady=4)

    def connect(self):
        pseudo = self.pseudo_var.get().strip()
        pwd = self.pwd_var.get()
        conn = get_conn()
        row = conn.execute("SELECT * FROM config WHERE id=1").fetchone()
        conn.close()
        if not row or pseudo != row["pseudo"]:
            messagebox.showerror("Erreur", "Pseudo ou mot de passe incorrect.")
            return
        h = hash_pwd(pwd)
        if h == row["pwd2_hash"]:
            level = 2
        elif h == row["pwd1_hash"]:
            level = 1
        else:
            messagebox.showerror("Erreur", "Pseudo ou mot de passe incorrect.")
            return
        self.app.session = {"pseudo": pseudo, "level": level}
        self.app.show_frame(DashboardFrame)


# ------------------------------------------------------------------
# TABLEAU DE BORD PRINCIPAL
# ------------------------------------------------------------------
class DashboardFrame(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        level = app.session["level"]

        # --- SIDEBAR ---
        sidebar = tk.Frame(self, bg=COLOR_SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="AMINA FDS", font=("Segoe UI", 16, "bold"), bg=COLOR_SIDEBAR, fg=COLOR_ACCENT).pack(pady=(25, 5))
        role_txt = "Chef (Niveau 2)" if level == 2 else "Secrétaire (Niveau 1)"
        tk.Label(sidebar, text=f"{app.session['pseudo']}\n{role_txt}", font=FONT_NORMAL,
                 bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT, justify="center").pack(pady=(0, 25))

        def side_btn(text, cmd):
            b = tk.Button(sidebar, text=text, command=cmd, anchor="w", padx=20, pady=10,
                          bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT, bd=0, font=FONT_NORMAL,
                          activebackground=COLOR_PRIMARY, activeforeground="white", cursor="hand2")
            b.pack(fill="x")
            return b

        side_btn("🏠  Tableau de bord", lambda: self.app.show_frame(DashboardFrame))
        side_btn("📦  Stock", lambda: self.app.show_frame(StockFrame))
        side_btn("🧾  Vendre", lambda: self.app.show_frame(VenteFrame))
        side_btn("🛠️  Prestations de services", lambda: self.app.show_frame(PrestationFrame))
        side_btn("📊  Rapports", lambda: self.app.show_frame(RapportFrame))
        if level == 2:
            side_btn("⚙️  Options avancées", lambda: self.app.show_frame(OptionsAvanceesFrame))
        side_btn("🔒  Clôturer la journée", self.cloturer_journee)
        tk.Frame(sidebar, bg=COLOR_SIDEBAR).pack(expand=True, fill="y")
        side_tex = load_side_texture(210, 90)
        if side_tex:
            tex_lbl = tk.Label(sidebar, image=side_tex, bg=COLOR_SIDEBAR)
            tex_lbl.image = side_tex
            tex_lbl.pack(fill="x", pady=(0, 5))
        side_btn("↩️  Déconnexion", self.app.logout)

        # --- CONTENU ---
        content = tk.Frame(self, bg=COLOR_BG)
        content.pack(side="left", fill="both", expand=True, padx=30, pady=25)

        # Bannière décorative (murs peints) tout en haut du contenu
        banner = load_banner(960, 70)
        if banner:
            banner_lbl = tk.Label(content, image=banner, bg=COLOR_BG)
            banner_lbl.image = banner
            banner_lbl.pack(fill="x", pady=(0, 15))

        header = tk.Frame(content, bg=COLOR_BG)
        header.pack(fill="x")
        tk.Label(header, text="Tableau de bord", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(side="left")
        etat = "🔴 Journée clôturée" if is_journee_cloturee() else "🟢 Journée en cours"
        tk.Label(header, text=etat, font=FONT_BOLD, bg=COLOR_BG,
                 fg=COLOR_DANGER if is_journee_cloturee() else COLOR_SUCCESS).pack(side="right", padx=(0, 15))
        logo_corner = load_logo(48)
        if logo_corner:
            lbl_logo_corner = tk.Label(header, image=logo_corner, bg=COLOR_BG)
            lbl_logo_corner.image = logo_corner
            lbl_logo_corner.pack(side="right")

        # cartes de stock
        cards_frame = tk.Frame(content, bg=COLOR_BG)
        cards_frame.pack(fill="x", pady=20)

        for i, tc in enumerate(["MP", "PSF", "PF"]):
            rows = get_stock(tc)
            total_qte = sum(r["quantite"] for r in rows)
            card = tk.Frame(cards_frame, bg="white", highlightbackground=COLOR_ACCENT, highlightthickness=1, padx=20, pady=15)
            card.grid(row=0, column=i, padx=10, sticky="nsew")
            cards_frame.grid_columnconfigure(i, weight=1)
            tk.Label(card, text=TYPE_LABELS[tc], font=FONT_BOLD, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w")
            tk.Label(card, text=f"{total_qte:.2f} Kg", font=("Segoe UI", 20, "bold"), bg="white", fg=COLOR_PRIMARY).pack(anchor="w", pady=(5, 0))
            if level == 2:
                if tc == "PF":
                    valeur = sum(r["quantite"] * r["prix_vente"] for r in rows)
                else:
                    valeur = sum(r["quantite"] * r["cout"] for r in rows)
                tk.Label(card, text=f"Valeur : {valeur:,.0f} F CFA".replace(",", " "), font=FONT_NORMAL, bg="white", fg="#666").pack(anchor="w")

        # détail par produit
        tk.Label(content, text="Détail du stock en temps réel", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(10, 5))
        nb = ttk.Notebook(content)
        nb.pack(fill="both", expand=True)
        for tc in ["MP", "PSF", "PF"]:
            tab = tk.Frame(nb, bg="white")
            nb.add(tab, text=TYPE_LABELS[tc])
            cols = ("nom", "qte", "cout") if tc != "PF" or level != 2 else ("nom", "qte", "cout", "prix")
            if tc == "PF":
                cols = ("nom", "qte", "prix") if level != 2 else ("nom", "qte", "cout", "prix")
            tree = ttk.Treeview(tab, columns=cols, show="headings", height=8)
            headers = {"nom": "Nom", "qte": "Quantité (Kg)", "cout": "Coût", "prix": "Prix de vente"}
            for c in cols:
                tree.heading(c, text=headers[c])
                tree.column(c, anchor="center")
            tree.pack(fill="both", expand=True, padx=10, pady=10)
            for r in get_stock(tc):
                vals = []
                for c in cols:
                    if c == "nom":
                        vals.append(r["nom"])
                    elif c == "qte":
                        vals.append(f"{r['quantite']:.2f}")
                    elif c == "cout":
                        vals.append(f"{r['cout']:.0f}")
                    elif c == "prix":
                        vals.append(f"{r['prix_vente']:.0f}")
                tree.insert("", "end", values=vals)

    def cloturer_journee(self):
        date_j = today_str()
        if is_journee_cloturee(date_j):
            messagebox.showinfo("Info", "La journée est déjà clôturée.")
            return
        if not messagebox.askyesno("Confirmation", "Voulez-vous clôturer la journée en cours ?\nPlus aucune saisie ne sera possible après clôture."):
            return
        conn = get_conn()
        conn.execute("""INSERT INTO journees (date_jour, cloturee, cloturee_par, date_cloture)
                        VALUES (?,1,?,?) ON CONFLICT(date_jour) DO UPDATE SET cloturee=1, cloturee_par=excluded.cloturee_par, date_cloture=excluded.date_cloture""",
                     (date_j, self.app.session["pseudo"], now_str()))
        conn.commit()
        conn.close()
        messagebox.showinfo("Journée clôturée", "La journée a été clôturée avec succès.")
        self.app.show_frame(DashboardFrame)


# ------------------------------------------------------------------
# FRAME AVEC SIDEBAR REUTILISABLE (base pour Stock / Vente / Rapport / Options)
# ------------------------------------------------------------------
class BaseSidebarFrame(tk.Frame):
    def __init__(self, parent, app, active_title="Stock"):
        super().__init__(parent, bg=COLOR_BG)
        self.app = app
        level = app.session["level"]

        sidebar = tk.Frame(self, bg=COLOR_SIDEBAR, width=210)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="AMINA FDS", font=("Segoe UI", 16, "bold"), bg=COLOR_SIDEBAR, fg=COLOR_ACCENT).pack(pady=(25, 5))
        role_txt = "Chef (Niveau 2)" if level == 2 else "Secrétaire (Niveau 1)"
        tk.Label(sidebar, text=f"{app.session['pseudo']}\n{role_txt}", font=FONT_NORMAL,
                 bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT, justify="center").pack(pady=(0, 25))

        def side_btn(text, cmd):
            b = tk.Button(sidebar, text=text, command=cmd, anchor="w", padx=20, pady=10,
                          bg=COLOR_SIDEBAR, fg=COLOR_SIDEBAR_TEXT, bd=0, font=FONT_NORMAL,
                          activebackground=COLOR_PRIMARY, activeforeground="white", cursor="hand2")
            b.pack(fill="x")
            return b

        side_btn("🏠  Tableau de bord", lambda: self.app.show_frame(DashboardFrame))
        side_btn("📦  Stock", lambda: self.app.show_frame(StockFrame))
        side_btn("🧾  Vendre", lambda: self.app.show_frame(VenteFrame))
        side_btn("🛠️  Prestations de services", lambda: self.app.show_frame(PrestationFrame))
        side_btn("📊  Rapports", lambda: self.app.show_frame(RapportFrame))
        if level == 2:
            side_btn("⚙️  Options avancées", lambda: self.app.show_frame(OptionsAvanceesFrame))
        tk.Frame(sidebar, bg=COLOR_SIDEBAR).pack(expand=True, fill="y")
        side_tex = load_side_texture(210, 90)
        if side_tex:
            tex_lbl = tk.Label(sidebar, image=side_tex, bg=COLOR_SIDEBAR)
            tex_lbl.image = side_tex
            tex_lbl.pack(fill="x", pady=(0, 5))
        side_btn("↩️  Déconnexion", self.app.logout)

        self.content = tk.Frame(self, bg=COLOR_BG)
        self.content.pack(side="left", fill="both", expand=True, padx=30, pady=25)


# ------------------------------------------------------------------
# STOCK : ENTREE EN STOCK
# ------------------------------------------------------------------
class StockFrame(BaseSidebarFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Stock")
        c = self.content

        tk.Label(c, text="Gestion du Stock — Entrée", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w")

        if is_journee_cloturee():
            tk.Label(c, text="⚠ La journée est clôturée : aucune saisie n'est possible.", font=FONT_BOLD,
                     bg=COLOR_BG, fg=COLOR_DANGER).pack(anchor="w", pady=10)

        form = tk.Frame(c, bg="white", padx=25, pady=20, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        form.pack(fill="x", pady=15)

        tk.Label(form, text="Type de produit", font=FONT_NORMAL, bg="white").grid(row=0, column=0, sticky="w", pady=6)
        self.type_var = tk.StringVar(value="MP")
        type_combo = ttk.Combobox(form, textvariable=self.type_var, state="readonly", width=25,
                                   values=[TYPE_LABELS[t] for t in TYPES_PRODUITS])
        type_combo.current(0)
        type_combo.grid(row=0, column=1, padx=10)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_produits())

        tk.Label(form, text="Produit", font=FONT_NORMAL, bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.produit_var = tk.StringVar()
        self.produit_combo = ttk.Combobox(form, textvariable=self.produit_var, state="readonly", width=25)
        self.produit_combo.grid(row=1, column=1, padx=10)

        tk.Label(form, text="Quantité à ajouter (Kg)", font=FONT_NORMAL, bg="white").grid(row=2, column=0, sticky="w", pady=6)
        self.qte_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.qte_var, width=25).grid(row=2, column=1, padx=10)

        tk.Label(form, text="Nouveau produit ? (optionnel)", font=FONT_NORMAL, bg="white").grid(row=3, column=0, sticky="w", pady=6)
        self.nouveau_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.nouveau_var, width=25).grid(row=3, column=1, padx=10)

        tk.Label(form, text="Coût (unité/Kg)", font=FONT_NORMAL, bg="white").grid(row=4, column=0, sticky="w", pady=6)
        self.cout_var = tk.StringVar(value="0")
        ttk.Entry(form, textvariable=self.cout_var, width=25).grid(row=4, column=1, padx=10)

        self.prix_label = tk.Label(form, text="Prix de vente (unité/Kg)", font=FONT_NORMAL, bg="white")
        self.prix_var = tk.StringVar(value="0")
        self.prix_entry = ttk.Entry(form, textvariable=self.prix_var, width=25)

        state = "disabled" if is_journee_cloturee() else "normal"
        ttk.Button(form, text="Enregistrer l'entrée", command=self.enregistrer, state=state).grid(
            row=6, column=0, columnspan=2, pady=(15, 0), ipadx=10)

        tk.Label(c, text="Journal des entrées récentes", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(15, 5))
        cols = ("date", "type", "produit", "qte", "action", "user")
        self.tree = ttk.Treeview(c, columns=cols, show="headings", height=10)
        headers = {"date": "Date/Heure", "type": "Type", "produit": "Produit", "qte": "Quantité (Kg)", "action": "Action", "user": "Saisi par"}
        for cc in cols:
            self.tree.heading(cc, text=headers[cc])
            self.tree.column(cc, anchor="center")
        self.tree.pack(fill="both", expand=True)

        self.refresh_produits()
        self.refresh_journal()

    def type_code(self):
        label = self.type_var.get()
        for k, v in TYPE_LABELS.items():
            if v == label:
                return k
        return "MP"

    def refresh_produits(self):
        tc = self.type_code()
        rows = get_stock(tc)
        self.produit_combo["values"] = [r["nom"] for r in rows]
        if tc == "PF":
            self.prix_label.grid(row=5, column=0, sticky="w", pady=6)
            self.prix_entry.grid(row=5, column=1, padx=10)
        else:
            self.prix_label.grid_forget()
            self.prix_entry.grid_forget()

    def enregistrer(self):
        if is_journee_cloturee():
            messagebox.showerror("Erreur", "La journée est clôturée.")
            return
        tc = self.type_code()
        nouveau_nom = self.nouveau_var.get().strip()
        table = TYPES_PRODUITS[tc]
        try:
            qte = float(self.qte_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide.")
            return

        conn = get_conn()
        if nouveau_nom:
            nom = nouveau_nom
            try:
                cout = float(self.cout_var.get().replace(",", ".") or 0)
                prix = float(self.prix_var.get().replace(",", ".") or 0)
            except ValueError:
                cout, prix = 0, 0
            try:
                if tc == "PF":
                    conn.execute(f"INSERT INTO {table} (nom, quantite, cout, prix_vente) VALUES (?,?,?,?)", (nom, qte, cout, prix))
                else:
                    conn.execute(f"INSERT INTO {table} (nom, quantite, cout) VALUES (?,?,?)", (nom, qte, cout))
            except sqlite3.IntegrityError:
                conn.execute(f"UPDATE {table} SET quantite = quantite + ? WHERE nom=?", (qte, nom))
        else:
            nom = self.produit_var.get()
            if not nom:
                messagebox.showerror("Erreur", "Sélectionnez un produit ou saisissez-en un nouveau.")
                conn.close()
                return
            conn.execute(f"UPDATE {table} SET quantite = quantite + ? WHERE nom=?", (qte, nom))
        conn.commit()
        conn.close()

        log_mouvement(TYPE_LABELS[tc], nom, qte, "Entrée en stock", self.app.session["pseudo"])
        messagebox.showinfo("Succès", f"Entrée de {qte} Kg enregistrée pour « {nom} ».")
        self.qte_var.set("")
        self.nouveau_var.set("")
        self.refresh_produits()
        self.refresh_journal()

    def refresh_journal(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = get_conn()
        rows = conn.execute("SELECT * FROM stock_journal ORDER BY id DESC LIMIT 50").fetchall()
        conn.close()
        for r in rows:
            self.tree.insert("", "end", values=(r["date_heure"], r["type_produit"], r["produit_nom"], r["quantite"], r["action"], r["utilisateur"]))


# ------------------------------------------------------------------
# PRESTATIONS DE SERVICES
# ------------------------------------------------------------------
class PrestationFrame(BaseSidebarFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Prestations de services")
        c = self.content

        tk.Label(c, text="Prestations de services", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w")
        tk.Label(c, text="Ex: transport, installation, main d'œuvre, etc. Ce montant vient augmenter le chiffre d'affaires de la journée.",
                 font=FONT_NORMAL, bg=COLOR_BG, fg="#666").pack(anchor="w", pady=(2, 10))

        if is_journee_cloturee():
            tk.Label(c, text="⚠ La journée est clôturée : aucune saisie n'est possible.", font=FONT_BOLD,
                     bg=COLOR_BG, fg=COLOR_DANGER).pack(anchor="w", pady=5)

        form = tk.Frame(c, bg="white", padx=25, pady=20, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        form.pack(fill="x", pady=10)

        tk.Label(form, text="Libellé du service", font=FONT_NORMAL, bg="white").grid(row=0, column=0, sticky="w", pady=6)
        self.libelle_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.libelle_var, width=35).grid(row=0, column=1, padx=10)

        tk.Label(form, text="Montant (F CFA)", font=FONT_NORMAL, bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.montant_var = tk.StringVar()
        ttk.Entry(form, textvariable=self.montant_var, width=35).grid(row=1, column=1, padx=10)

        state = "disabled" if is_journee_cloturee() else "normal"
        ttk.Button(form, text="Enregistrer", state=state, command=self.enregistrer).grid(row=2, column=0, columnspan=2, pady=(15, 0), ipadx=10)

        tk.Label(c, text="Prestations enregistrées aujourd'hui", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(15, 5))
        self.tree = ttk.Treeview(c, columns=("heure", "libelle", "montant", "user"), show="headings", height=10)
        headers = {"heure": "Heure", "libelle": "Libellé", "montant": "Montant (F CFA)", "user": "Saisi par"}
        for cc in ("heure", "libelle", "montant", "user"):
            self.tree.heading(cc, text=headers[cc])
            self.tree.column(cc, anchor="center")
        self.tree.pack(fill="both", expand=True)

        total_frame = tk.Frame(c, bg=COLOR_BG)
        total_frame.pack(fill="x", pady=(10, 0))
        self.total_lbl = tk.Label(total_frame, text="", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_PRIMARY)
        self.total_lbl.pack(anchor="e")

        self.refresh()

    def enregistrer(self):
        if is_journee_cloturee():
            messagebox.showerror("Erreur", "La journée est clôturée.")
            return
        libelle = self.libelle_var.get().strip()
        if not libelle:
            messagebox.showerror("Erreur", "Le libellé du service est obligatoire.")
            return
        try:
            montant = float(self.montant_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return
        if montant <= 0:
            messagebox.showerror("Erreur", "Le montant doit être positif.")
            return

        conn = get_conn()
        conn.execute("INSERT INTO prestations (date_jour, date_heure, libelle, montant, utilisateur) VALUES (?,?,?,?,?)",
                     (today_str(), now_str(), libelle, montant, self.app.session["pseudo"]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", f"Prestation « {libelle} » enregistrée pour {montant:,.0f} F CFA.".replace(",", " "))
        self.libelle_var.set("")
        self.montant_var.set("")
        self.refresh()

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        conn = get_conn()
        rows = conn.execute("SELECT * FROM prestations WHERE date_jour=? ORDER BY id DESC", (today_str(),)).fetchall()
        conn.close()
        total = 0
        for r in rows:
            heure = r["date_heure"].split(" ")[1] if " " in r["date_heure"] else r["date_heure"]
            self.tree.insert("", "end", values=(heure, r["libelle"], f"{r['montant']:.0f}", r["utilisateur"]))
            total += r["montant"]
        self.total_lbl.config(text=f"Total du jour : {total:,.0f} F CFA".replace(",", " "))


# ------------------------------------------------------------------
# VENTE
# ------------------------------------------------------------------
class VenteFrame(BaseSidebarFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Vendre")
        self.panier = []  # liste de dict: type_code, nom, qte, prix_unitaire

        c = self.content
        tk.Label(c, text="Ventes", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w")

        if is_journee_cloturee():
            tk.Label(c, text="⚠ La journée est clôturée : aucune vente n'est possible.", font=FONT_BOLD,
                     bg=COLOR_BG, fg=COLOR_DANGER).pack(anchor="w", pady=10)

        top = tk.Frame(c, bg=COLOR_BG)
        top.pack(fill="both", expand=True)

        # --- colonne gauche : ajout produit + panier ---
        left = tk.Frame(top, bg="white", padx=20, pady=15, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        tk.Label(left, text="Ajouter un produit", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        tk.Label(left, text="Type", bg="white", font=FONT_NORMAL).grid(row=1, column=0, sticky="w", pady=4)
        self.type_var = tk.StringVar(value=TYPE_LABELS["PSF"])
        type_combo = ttk.Combobox(left, textvariable=self.type_var, state="readonly", width=22,
                                   values=[TYPE_LABELS["PSF"], TYPE_LABELS["PF"]])
        type_combo.grid(row=1, column=1, pady=4)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_produits())

        tk.Label(left, text="Produit", bg="white", font=FONT_NORMAL).grid(row=2, column=0, sticky="w", pady=4)
        self.produit_var = tk.StringVar()
        self.produit_combo = ttk.Combobox(left, textvariable=self.produit_var, state="readonly", width=22)
        self.produit_combo.grid(row=2, column=1, pady=4)
        self.produit_combo.bind("<<ComboboxSelected>>", lambda e: self.update_prix())

        tk.Label(left, text="Quantité (Kg)", bg="white", font=FONT_NORMAL).grid(row=3, column=0, sticky="w", pady=4)
        self.qte_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.qte_var, width=24).grid(row=3, column=1, pady=4)

        tk.Label(left, text="Prix unitaire", bg="white", font=FONT_NORMAL).grid(row=4, column=0, sticky="w", pady=4)
        self.prix_var = tk.StringVar()
        ttk.Entry(left, textvariable=self.prix_var, width=24).grid(row=4, column=1, pady=4)

        ttk.Button(left, text="➕ Ajouter au panier", command=self.ajouter_panier).grid(row=5, column=0, columnspan=2, pady=12, ipadx=8)

        tk.Label(left, text="Panier", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=6, column=0, columnspan=2, sticky="w", pady=(10, 5))
        self.panier_tree = ttk.Treeview(left, columns=("type", "produit", "qte", "pu", "total"), show="headings", height=6)
        for c2, t in zip(("type", "produit", "qte", "pu", "total"), ("Type", "Produit", "Qté(Kg)", "P.U.", "Total")):
            self.panier_tree.heading(c2, text=t)
            self.panier_tree.column(c2, width=90, anchor="center")
        self.panier_tree.grid(row=7, column=0, columnspan=2, sticky="nsew")

        ttk.Button(left, text="🗑 Retirer la ligne sélectionnée", command=self.retirer_ligne).grid(row=8, column=0, columnspan=2, pady=8)

        # --- colonne droite : infos client + génération facture ---
        right = tk.Frame(top, bg="white", padx=20, pady=15, highlightbackground=COLOR_ACCENT, highlightthickness=2, width=320)
        right.pack(side="left", fill="y")

        tk.Label(right, text="Informations Client", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(0, 10))
        tk.Label(right, text="Nom du client *", bg="white", font=FONT_NORMAL).pack(anchor="w")
        self.client_nom = tk.StringVar()
        ttk.Entry(right, textvariable=self.client_nom, width=30).pack(pady=(2, 8))

        tk.Label(right, text="Téléphone *", bg="white", font=FONT_NORMAL).pack(anchor="w")
        self.client_tel = tk.StringVar()
        ttk.Entry(right, textvariable=self.client_tel, width=30).pack(pady=(2, 8))

        tk.Label(right, text="Quartier / Adresse *", bg="white", font=FONT_NORMAL).pack(anchor="w")
        self.client_adr = tk.StringVar()
        ttk.Entry(right, textvariable=self.client_adr, width=30).pack(pady=(2, 15))

        self.tva_var = tk.BooleanVar(value=False)
        tva_check = tk.Checkbutton(right, text=f"Appliquer la TVA ({int(TVA_TAUX*100)}%)", variable=self.tva_var,
                                    bg="white", font=FONT_BOLD, fg=COLOR_PRIMARY_DARK, activebackground="white",
                                    selectcolor=COLOR_ACCENT, cursor="hand2")
        tva_check.pack(anchor="w", pady=(0, 10))

        state = "disabled" if is_journee_cloturee() else "normal"
        ttk.Button(right, text="🧾 Aperçu Facture", style="Primary.TButton", state=state,
                   command=self.apercu_facture).pack(fill="x", ipady=6, pady=(10, 0))

        # Liste des factures du jour
        tk.Label(c, text="Factures enregistrées aujourd'hui", font=FONT_SUBTITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(20, 5))
        self.fact_tree = ttk.Treeview(c, columns=("numero", "heure", "client", "total"), show="headings", height=6)
        for c3, t in zip(("numero", "heure", "client", "total"), ("N° Facture", "Heure", "Client", "Total")):
            self.fact_tree.heading(c3, text=t)
            self.fact_tree.column(c3, anchor="center")
        self.fact_tree.pack(fill="x")
        self.fact_tree.bind("<Double-1>", self.voir_facture)

        self.refresh_produits()
        self.refresh_factures_jour()

    def type_code(self):
        for k in ["PSF", "PF"]:
            if TYPE_LABELS[k] == self.type_var.get():
                return k
        return "PSF"

    def refresh_produits(self):
        tc = self.type_code()
        rows = get_stock(tc)
        self.produit_combo["values"] = [r["nom"] for r in rows if r["quantite"] > 0]

    def update_prix(self):
        tc = self.type_code()
        nom = self.produit_var.get()
        conn = get_conn()
        table = TYPES_PRODUITS[tc]
        row = conn.execute(f"SELECT * FROM {table} WHERE nom=?", (nom,)).fetchone()
        conn.close()
        if row and tc == "PF":
            self.prix_var.set(str(row["prix_vente"]))
        else:
            self.prix_var.set("")

    def ajouter_panier(self):
        if is_journee_cloturee():
            messagebox.showerror("Erreur", "La journée est clôturée.")
            return
        tc = self.type_code()
        nom = self.produit_var.get()
        if not nom:
            messagebox.showerror("Erreur", "Sélectionnez un produit.")
            return
        try:
            qte = float(self.qte_var.get().replace(",", "."))
            pu = float(self.prix_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Quantité et prix doivent être numériques.")
            return
        if qte <= 0:
            messagebox.showerror("Erreur", "La quantité doit être positive.")
            return

        conn = get_conn()
        table = TYPES_PRODUITS[tc]
        stock_row = conn.execute(f"SELECT quantite FROM {table} WHERE nom=?", (nom,)).fetchone()
        conn.close()
        dispo = stock_row["quantite"] if stock_row else 0
        deja_panier = sum(l["qte"] for l in self.panier if l["nom"] == nom and l["type_code"] == tc)
        if qte + deja_panier > dispo:
            messagebox.showerror("Stock insuffisant", f"Stock disponible pour « {nom} » : {dispo} Kg.")
            return

        self.panier.append({"type_code": tc, "nom": nom, "qte": qte, "pu": pu})
        self.panier_tree.insert("", "end", values=(TYPE_LABELS[tc], nom, qte, pu, qte * pu))
        self.qte_var.set("")
        self.prix_var.set("")

    def retirer_ligne(self):
        sel = self.panier_tree.selection()
        if not sel:
            return
        idx = self.panier_tree.index(sel[0])
        del self.panier[idx]
        self.panier_tree.delete(sel[0])

    def apercu_facture(self):
        if not self.panier:
            messagebox.showerror("Erreur", "Le panier est vide.")
            return
        if not self.client_nom.get().strip() or not self.client_tel.get().strip() or not self.client_adr.get().strip():
            messagebox.showerror("Erreur", "Veuillez renseigner le nom, le téléphone et le quartier/adresse du client.")
            return
        FacturePreview(self, self.app, self.panier, self.client_nom.get(), self.client_tel.get(),
                       self.client_adr.get(), self.tva_var.get())

    def valider_facture(self):
        """Appelé par la fenêtre de preview après enregistrement définitif."""
        self.panier = []
        for i in self.panier_tree.get_children():
            self.panier_tree.delete(i)
        self.client_nom.set("")
        self.client_tel.set("")
        self.client_adr.set("")
        self.tva_var.set(False)
        self.refresh_produits()
        self.refresh_factures_jour()

    def refresh_factures_jour(self):
        for i in self.fact_tree.get_children():
            self.fact_tree.delete(i)
        conn = get_conn()
        rows = conn.execute("SELECT * FROM factures WHERE date_jour=? ORDER BY id DESC", (today_str(),)).fetchall()
        conn.close()
        for r in rows:
            heure = r["date_heure"].split(" ")[1] if " " in r["date_heure"] else r["date_heure"]
            self.fact_tree.insert("", "end", iid=str(r["id"]), values=(r["numero"], heure, r["client_nom"], f"{r['total']:.0f}"))

    def voir_facture(self, event):
        sel = self.fact_tree.selection()
        if not sel:
            return
        facture_id = int(sel[0])
        show_facture_detail(self.app, facture_id)


class FacturePreview(tk.Toplevel):
    def __init__(self, vente_frame, app, panier, nom, tel, adr, tva_active=False):
        super().__init__(vente_frame)
        self.vente_frame = vente_frame
        self.app = app
        self.panier = panier
        self.nom, self.tel, self.adr = nom, tel, adr
        self.tva_active = tva_active
        self.title("Aperçu de la facture")
        self.geometry("620x640")
        self.minsize(620, 640)
        self.configure(bg="white")
        self.grab_set()
        self.build()

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        logo = load_logo(60)
        if logo:
            lbl = tk.Label(self, image=logo, bg="white")
            lbl.image = logo
            lbl.pack(pady=(12, 0))
        else:
            tk.Label(self, text="AMINA FDS", font=("Segoe UI", 18, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(15, 0))
        tk.Label(self, text="Aperçu de facture (non enregistrée)", font=FONT_NORMAL, bg="white", fg="#666").pack(pady=(0, 10))

        info = tk.Frame(self, bg="white")
        info.pack(fill="x", padx=20)
        tk.Label(info, text=f"Client : {self.nom}", font=FONT_BOLD, bg="white").pack(anchor="w")
        tk.Label(info, text=f"Téléphone : {self.tel}", bg="white").pack(anchor="w")
        tk.Label(info, text=f"Adresse/Quartier : {self.adr}", bg="white").pack(anchor="w")
        tk.Label(info, text=f"Date : {now_str()}", bg="white").pack(anchor="w", pady=(0, 10))

        tree = ttk.Treeview(self, columns=("produit", "qte", "pu", "total"), show="headings", height=7)
        widths = {"produit": 200, "qte": 100, "pu": 110, "total": 130}
        for c, t in zip(("produit", "qte", "pu", "total"), ("Produit", "Qté(Kg)", "P.U.", "Sous-total")):
            tree.heading(c, text=t)
            tree.column(c, anchor="center", width=widths[c])
        tree.pack(fill="both", expand=True, padx=20)
        montant_ht = 0
        for l in self.panier:
            st = l["qte"] * l["pu"]
            montant_ht += st
            tree.insert("", "end", values=(l["nom"], l["qte"], l["pu"], f"{st:.0f}"))

        montant_tva = montant_ht * TVA_TAUX if self.tva_active else 0
        montant_total = montant_ht + montant_tva

        totaux = tk.Frame(self, bg="white")
        totaux.pack(fill="x", padx=20, pady=(10, 0))
        row1 = tk.Frame(totaux, bg="white")
        row1.pack(fill="x")
        tk.Label(row1, text="Sous-total HT :", font=FONT_NORMAL, bg="white").pack(side="left")
        tk.Label(row1, text=f"{montant_ht:,.0f} F CFA".replace(",", " "), font=FONT_NORMAL, bg="white").pack(side="right")
        if self.tva_active:
            row2 = tk.Frame(totaux, bg="white")
            row2.pack(fill="x")
            tk.Label(row2, text=f"TVA ({int(TVA_TAUX*100)}%) :", font=FONT_NORMAL, bg="white").pack(side="left")
            tk.Label(row2, text=f"{montant_tva:,.0f} F CFA".replace(",", " "), font=FONT_NORMAL, bg="white").pack(side="right")

        tk.Label(self, text=f"MONTANT TOTAL : {montant_total:,.0f} F CFA".replace(",", " "), font=("Segoe UI", 14, "bold"),
                 bg="white", fg=COLOR_PRIMARY_DARK).pack(pady=15)

        self.montant_ht, self.montant_tva, self.montant_total = montant_ht, montant_tva, montant_total

        btns = tk.Frame(self, bg="white")
        btns.pack(pady=10)
        ttk.Button(btns, text="✏ Modifier", command=self.destroy).pack(side="left", padx=10, ipadx=10)
        ttk.Button(btns, text="✅ Enregistrer définitivement", style="Primary.TButton",
                   command=self.enregistrer).pack(side="left", padx=10, ipadx=10)

    def enregistrer(self):
        if is_journee_cloturee():
            messagebox.showerror("Erreur", "La journée est clôturée.")
            self.destroy()
            return
        numero = generate_numero_facture()
        conn = get_conn()
        cur = conn.execute("""INSERT INTO factures (numero, date_heure, date_jour, client_nom, client_tel, client_adresse,
                              total, utilisateur, modifiee, tva_active, montant_ht, montant_tva)
                              VALUES (?,?,?,?,?,?,?,?,0,?,?,?)""",
                           (numero, now_str(), today_str(), self.nom, self.tel, self.adr, self.montant_total,
                            self.app.session["pseudo"], 1 if self.tva_active else 0, self.montant_ht, self.montant_tva))
        facture_id = cur.lastrowid
        for l in self.panier:
            conn.execute("""INSERT INTO facture_lignes (facture_id, type_produit, produit_nom, quantite, prix_unitaire, sous_total)
                            VALUES (?,?,?,?,?,?)""",
                        (facture_id, TYPE_LABELS[l["type_code"]], l["nom"], l["qte"], l["pu"], l["qte"] * l["pu"]))
            table = TYPES_PRODUITS[l["type_code"]]
            conn.execute(f"UPDATE {table} SET quantite = quantite - ? WHERE nom=?", (l["qte"], l["nom"]))
        conn.commit()
        conn.close()
        for l in self.panier:
            log_mouvement(TYPE_LABELS[l["type_code"]], l["nom"], -l["qte"], f"Vente (facture {numero})", self.app.session["pseudo"])

        messagebox.showinfo("Succès", f"Facture {numero} enregistrée avec succès.\nMontant total : {self.montant_total:,.0f} F CFA".replace(",", " "))
        self.vente_frame.valider_facture()
        self.destroy()


def show_facture_detail(app, facture_id, allow_edit=False):
    conn = get_conn()
    facture = conn.execute("SELECT * FROM factures WHERE id=?", (facture_id,)).fetchone()
    lignes = conn.execute("SELECT * FROM facture_lignes WHERE facture_id=?", (facture_id,)).fetchall()
    conn.close()
    if not facture:
        return

    top = tk.Toplevel(app)
    top.title(f"Facture {facture['numero']}")
    top.geometry("620x660")
    top.minsize(620, 660)
    top.configure(bg="white")
    top.grab_set()

    logo = load_logo(55)
    if logo:
        lbl = tk.Label(top, image=logo, bg="white")
        lbl.image = logo
        lbl.pack(pady=(12, 0))
    else:
        tk.Label(top, text="AMINA FDS", font=("Segoe UI", 18, "bold"), fg=COLOR_PRIMARY, bg="white").pack(pady=(15, 0))
    tk.Label(top, text=f"Facture N° {facture['numero']}" + ("  (MODIFIÉE)" if facture["modifiee"] else ""),
             font=FONT_BOLD, bg="white", fg=COLOR_DANGER if facture["modifiee"] else COLOR_PRIMARY_DARK).pack(pady=(0, 10))

    info = tk.Frame(top, bg="white")
    info.pack(fill="x", padx=20)
    tk.Label(info, text=f"Client : {facture['client_nom']}", font=FONT_BOLD, bg="white").pack(anchor="w")
    tk.Label(info, text=f"Téléphone : {facture['client_tel']}", bg="white").pack(anchor="w")
    tk.Label(info, text=f"Adresse/Quartier : {facture['client_adresse']}", bg="white").pack(anchor="w")
    tk.Label(info, text=f"Date : {facture['date_heure']}", bg="white").pack(anchor="w")
    tk.Label(info, text=f"Enregistrée par : {facture['utilisateur']}", bg="white").pack(anchor="w", pady=(0, 10))

    tree = ttk.Treeview(top, columns=("produit", "qte", "pu", "total"), show="headings", height=7)
    widths = {"produit": 200, "qte": 100, "pu": 110, "total": 130}
    for c, t in zip(("produit", "qte", "pu", "total"), ("Produit", "Qté(Kg)", "P.U.", "Sous-total")):
        tree.heading(c, text=t)
        tree.column(c, anchor="center", width=widths[c])
    tree.pack(fill="both", expand=True, padx=20)
    for l in lignes:
        tree.insert("", "end", values=(l["produit_nom"], l["quantite"], l["prix_unitaire"], f"{l['sous_total']:.0f}"))

    totaux = tk.Frame(top, bg="white")
    totaux.pack(fill="x", padx=20, pady=(10, 0))
    try:
        tva_active = bool(facture["tva_active"])
        montant_ht = facture["montant_ht"] or 0
        montant_tva = facture["montant_tva"] or 0
    except (IndexError, KeyError):
        tva_active, montant_ht, montant_tva = False, 0, 0
    if montant_ht:
        row1 = tk.Frame(totaux, bg="white")
        row1.pack(fill="x")
        tk.Label(row1, text="Sous-total HT :", bg="white").pack(side="left")
        tk.Label(row1, text=f"{montant_ht:,.0f} F CFA".replace(",", " "), bg="white").pack(side="right")
    if tva_active:
        row2 = tk.Frame(totaux, bg="white")
        row2.pack(fill="x")
        tk.Label(row2, text=f"TVA ({int(TVA_TAUX*100)}%) :", bg="white").pack(side="left")
        tk.Label(row2, text=f"{montant_tva:,.0f} F CFA".replace(",", " "), bg="white").pack(side="right")

    tk.Label(top, text=f"MONTANT TOTAL : {facture['total']:,.0f} F CFA".replace(",", " "), font=("Segoe UI", 14, "bold"),
             bg="white", fg=COLOR_PRIMARY_DARK).pack(pady=15)

    if allow_edit and app.session["level"] == 2:
        ttk.Button(top, text="✏ Modifier cette facture (Niveau 2)",
                   command=lambda: [top.destroy(), EditFactureWindow(app, facture_id)]).pack(pady=5)


class EditFactureWindow(tk.Toplevel):
    """Modification d'une facture déjà enregistrée — réservé au chef (niveau 2)."""
    def __init__(self, app, facture_id):
        super().__init__(app)
        self.app = app
        self.facture_id = facture_id
        self.title("Modifier la facture")
        self.geometry("640x580")
        self.minsize(640, 580)
        self.configure(bg="white")
        self.grab_set()
        self.load_data()
        self.build()

    def load_data(self):
        conn = get_conn()
        self.facture = conn.execute("SELECT * FROM factures WHERE id=?", (self.facture_id,)).fetchone()
        self.lignes = [dict(r) for r in conn.execute("SELECT * FROM facture_lignes WHERE facture_id=?", (self.facture_id,)).fetchall()]
        conn.close()

    def build(self):
        for w in self.winfo_children():
            w.destroy()
        tk.Label(self, text=f"Modification — Facture {self.facture['numero']}", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(pady=10)

        self.tree = ttk.Treeview(self, columns=("produit", "qte", "pu", "total"), show="headings", height=8)
        widths = {"produit": 200, "qte": 100, "pu": 110, "total": 130}
        for c, t in zip(("produit", "qte", "pu", "total"), ("Produit", "Qté(Kg)", "P.U.", "Sous-total")):
            self.tree.heading(c, text=t)
            self.tree.column(c, anchor="center", width=widths[c])
        self.tree.pack(fill="both", expand=True, padx=20)
        for i, l in enumerate(self.lignes):
            self.tree.insert("", "end", iid=str(i), values=(l["produit_nom"], l["quantite"], l["prix_unitaire"], f"{l['sous_total']:.0f}"))

        edit_frame = tk.Frame(self, bg="white")
        edit_frame.pack(pady=10)
        tk.Label(edit_frame, text="Nouvelle quantité (Kg) :", bg="white").grid(row=0, column=0, padx=5)
        self.qte_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.qte_var, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(edit_frame, text="Appliquer à la ligne sélectionnée", command=self.modifier_ligne).grid(row=0, column=2, padx=10)

        ttk.Button(self, text="💾 Enregistrer les modifications", style="Primary.TButton",
                   command=self.enregistrer).pack(pady=15, ipadx=10)

    def modifier_ligne(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showerror("Erreur", "Sélectionnez une ligne.")
            return
        try:
            new_qte = float(self.qte_var.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Quantité invalide.")
            return
        idx = int(sel[0])
        self.lignes[idx]["quantite"] = new_qte
        self.lignes[idx]["sous_total"] = new_qte * self.lignes[idx]["prix_unitaire"]
        self.tree.item(sel[0], values=(self.lignes[idx]["produit_nom"], new_qte, self.lignes[idx]["prix_unitaire"], f"{self.lignes[idx]['sous_total']:.0f}"))

    def enregistrer(self):
        conn = get_conn()
        # Remettre en stock les anciennes quantités puis retirer les nouvelles
        old_lignes = conn.execute("SELECT * FROM facture_lignes WHERE facture_id=?", (self.facture_id,)).fetchall()
        for ol in old_lignes:
            for tc, table in TYPES_PRODUITS.items():
                conn.execute(f"UPDATE {table} SET quantite = quantite + ? WHERE nom=?", (ol["quantite"], ol["produit_nom"]))
        conn.execute("DELETE FROM facture_lignes WHERE facture_id=?", (self.facture_id,))

        montant_ht = 0
        for l in self.lignes:
            montant_ht += l["quantite"] * l["prix_unitaire"]
            conn.execute("""INSERT INTO facture_lignes (facture_id, type_produit, produit_nom, quantite, prix_unitaire, sous_total)
                            VALUES (?,?,?,?,?,?)""",
                        (self.facture_id, l["type_produit"], l["produit_nom"], l["quantite"], l["prix_unitaire"], l["quantite"] * l["prix_unitaire"]))
            for tc, table in TYPES_PRODUITS.items():
                conn.execute(f"UPDATE {table} SET quantite = quantite - ? WHERE nom=?", (l["quantite"], l["produit_nom"]))

        tva_active = bool(self.facture["tva_active"]) if "tva_active" in self.facture.keys() else False
        montant_tva = montant_ht * TVA_TAUX if tva_active else 0
        total = montant_ht + montant_tva

        conn.execute("UPDATE factures SET total=?, montant_ht=?, montant_tva=?, modifiee=1 WHERE id=?",
                     (total, montant_ht, montant_tva, self.facture_id))
        conn.commit()
        conn.close()
        log_mouvement("Facture", self.facture["numero"], 0, "Modification de facture", self.app.session["pseudo"])
        messagebox.showinfo("Succès", "Facture modifiée avec succès.")
        self.destroy()


# ------------------------------------------------------------------
# RAPPORTS
# ------------------------------------------------------------------
class RapportFrame(BaseSidebarFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Rapports")
        c = self.content
        tk.Label(c, text="Rapports", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w")

        selector = tk.Frame(c, bg=COLOR_BG)
        selector.pack(fill="x", pady=15)
        self.periode_var = tk.StringVar(value="Aujourd'hui")
        ttk.Combobox(selector, textvariable=self.periode_var, state="readonly", width=20,
                     values=["Aujourd'hui", "Hier"]).pack(side="left")
        ttk.Button(selector, text="Afficher", command=self.afficher_rapport).pack(side="left", padx=10)
        ttk.Button(selector, text="📄 Exporter PDF", command=self.export_pdf).pack(side="left", padx=5)
        ttk.Button(selector, text="📊 Exporter Excel", command=self.export_excel).pack(side="left", padx=5)

        self.result_frame = tk.Frame(c, bg="white", padx=20, pady=15, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        self.result_frame.pack(fill="both", expand=True, pady=10)

        # --- Dépenses du jour ---
        dep_frame = tk.Frame(c, bg="white", padx=20, pady=15, highlightbackground=COLOR_ACCENT, highlightthickness=2)
        dep_frame.pack(fill="x", pady=10)
        tk.Label(dep_frame, text="Enregistrer une dépense du jour", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=0, column=0, columnspan=3, sticky="w")
        tk.Label(dep_frame, text="Description", bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.dep_desc = tk.StringVar()
        ttk.Entry(dep_frame, textvariable=self.dep_desc, width=30).grid(row=1, column=1, padx=8)
        tk.Label(dep_frame, text="Montant", bg="white").grid(row=1, column=2, sticky="w")
        self.dep_montant = tk.StringVar()
        ttk.Entry(dep_frame, textvariable=self.dep_montant, width=15).grid(row=1, column=3, padx=8)
        state = "disabled" if is_journee_cloturee() else "normal"
        ttk.Button(dep_frame, text="Enregistrer", state=state, command=self.enregistrer_depense).grid(row=1, column=4, padx=8)

        self.afficher_rapport()

    def get_period_dates(self):
        return today_str() if self.periode_var.get() == "Aujourd'hui" else yesterday_str()

    def compute_rapport(self, date_debut, date_fin):
        conn = get_conn()
        ventes = conn.execute("SELECT COALESCE(SUM(total),0) as t, COUNT(*) as n FROM factures WHERE date_jour BETWEEN ? AND ?", (date_debut, date_fin)).fetchone()
        depenses = conn.execute("SELECT COALESCE(SUM(montant),0) as t FROM depenses WHERE date_jour BETWEEN ? AND ?", (date_debut, date_fin)).fetchone()
        factures = conn.execute("SELECT * FROM factures WHERE date_jour BETWEEN ? AND ? ORDER BY date_heure", (date_debut, date_fin)).fetchall()
        liste_dep = conn.execute("SELECT * FROM depenses WHERE date_jour BETWEEN ? AND ? ORDER BY date_heure", (date_debut, date_fin)).fetchall()
        conn.close()
        total_prestations, nb_prestations = get_prestations_total(date_debut, date_fin)
        chiffre_affaires = ventes["t"] + total_prestations
        return {
            "total_ventes": ventes["t"], "nb_factures": ventes["n"],
            "total_prestations": total_prestations, "nb_prestations": nb_prestations,
            "chiffre_affaires": chiffre_affaires,
            "total_depenses": depenses["t"], "benefice": chiffre_affaires - depenses["t"],
            "factures": factures, "depenses": liste_dep
        }

    def afficher_rapport(self):
        for w in self.result_frame.winfo_children():
            w.destroy()
        date_j = self.get_period_dates()
        data = self.compute_rapport(date_j, date_j)
        self.last_rapport = data
        self.last_period_label = f"{self.periode_var.get()} ({fmt_date_fr(date_j)})"

        tk.Label(self.result_frame, text=f"Rapport — {self.last_period_label}", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w")
        stats = tk.Frame(self.result_frame, bg="white")
        stats.pack(fill="x", pady=10)
        for label, val in [("Nombre de factures", data["nb_factures"]),
                            ("Total des ventes", f"{data['total_ventes']:,.0f} F CFA".replace(",", " ")),
                            ("Total des prestations de services", f"{data['total_prestations']:,.0f} F CFA".replace(",", " ")),
                            ("Chiffre d'affaires (ventes + prestations)", f"{data['chiffre_affaires']:,.0f} F CFA".replace(",", " ")),
                            ("Total des dépenses", f"{data['total_depenses']:,.0f} F CFA".replace(",", " ")),
                            ("Bénéfice net", f"{data['benefice']:,.0f} F CFA".replace(",", " "))]:
            row = tk.Frame(stats, bg="white")
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label + " :", font=FONT_NORMAL, bg="white", width=32, anchor="w").pack(side="left")
            tk.Label(row, text=str(val), font=FONT_BOLD, bg="white", fg=COLOR_PRIMARY).pack(side="left")

        tree = ttk.Treeview(self.result_frame, columns=("numero", "client", "total"), show="headings", height=6)
        for c, t in zip(("numero", "client", "total"), ("N° Facture", "Client", "Total")):
            tree.heading(c, text=t)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True, pady=10)
        for f in data["factures"]:
            tree.insert("", "end", values=(f["numero"], f["client_nom"], f"{f['total']:.0f}"))

    def enregistrer_depense(self):
        if is_journee_cloturee():
            messagebox.showerror("Erreur", "La journée est clôturée.")
            return
        desc = self.dep_desc.get().strip()
        try:
            montant = float(self.dep_montant.get().replace(",", "."))
        except ValueError:
            messagebox.showerror("Erreur", "Montant invalide.")
            return
        if not desc:
            messagebox.showerror("Erreur", "Description obligatoire.")
            return
        conn = get_conn()
        conn.execute("INSERT INTO depenses (date_jour, date_heure, description, montant, utilisateur) VALUES (?,?,?,?,?)",
                     (today_str(), now_str(), desc, montant, self.app.session["pseudo"]))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", "Dépense enregistrée.")
        self.dep_desc.set("")
        self.dep_montant.set("")
        self.afficher_rapport()

    def export_pdf(self):
        data = getattr(self, "last_rapport", None)
        if not data:
            return
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfgen import canvas
        except ImportError:
            messagebox.showerror("Erreur", "Le module reportlab n'est pas installé.")
            return
        path = os.path.join(BASE_DIR, f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
        cvs = canvas.Canvas(path, pagesize=A4)
        w, h = A4
        y = h - 60
        cvs.setFont("Helvetica-Bold", 16)
        cvs.drawString(50, y, "AMINA FDS - Rapport")
        y -= 25
        cvs.setFont("Helvetica", 11)
        cvs.drawString(50, y, f"Période : {self.last_period_label}")
        y -= 25
        for label, val in [("Nombre de factures", data["nb_factures"]),
                            ("Total des ventes", f"{data['total_ventes']:.0f} F CFA"),
                            ("Total des prestations de services", f"{data['total_prestations']:.0f} F CFA"),
                            ("Chiffre d'affaires", f"{data['chiffre_affaires']:.0f} F CFA"),
                            ("Total des dépenses", f"{data['total_depenses']:.0f} F CFA"),
                            ("Bénéfice net", f"{data['benefice']:.0f} F CFA")]:
            cvs.drawString(50, y, f"{label} : {val}")
            y -= 18
        y -= 15
        cvs.setFont("Helvetica-Bold", 12)
        cvs.drawString(50, y, "Détail des factures")
        y -= 18
        cvs.setFont("Helvetica", 10)
        for f in data["factures"]:
            if y < 60:
                cvs.showPage()
                y = h - 60
            cvs.drawString(50, y, f"{f['numero']}  |  {f['client_nom']}  |  {f['total']:.0f} F CFA")
            y -= 15
        cvs.save()
        messagebox.showinfo("Export réussi", f"Rapport PDF exporté :\n{path}")

    def export_excel(self):
        data = getattr(self, "last_rapport", None)
        if not data:
            return
        try:
            from openpyxl import Workbook
        except ImportError:
            messagebox.showerror("Erreur", "Le module openpyxl n'est pas installé.")
            return
        wb = Workbook()
        ws = wb.active
        ws.title = "Rapport"
        ws.append(["AMINA FDS - Rapport", self.last_period_label])
        ws.append([])
        ws.append(["Nombre de factures", data["nb_factures"]])
        ws.append(["Total des ventes", data["total_ventes"]])
        ws.append(["Total des prestations de services", data["total_prestations"]])
        ws.append(["Chiffre d'affaires", data["chiffre_affaires"]])
        ws.append(["Total des dépenses", data["total_depenses"]])
        ws.append(["Bénéfice net", data["benefice"]])
        ws.append([])
        ws.append(["N° Facture", "Client", "Téléphone", "Total"])
        for f in data["factures"]:
            ws.append([f["numero"], f["client_nom"], f["client_tel"], f["total"]])
        path = os.path.join(BASE_DIR, f"rapport_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        wb.save(path)
        messagebox.showinfo("Export réussi", f"Rapport Excel exporté :\n{path}")


# ------------------------------------------------------------------
# OPTIONS AVANCEES (NIVEAU 2 UNIQUEMENT)
# ------------------------------------------------------------------
class OptionsAvanceesFrame(BaseSidebarFrame):
    def __init__(self, parent, app):
        super().__init__(parent, app, "Options avancées")
        if app.session["level"] != 2:
            tk.Label(self.content, text="Accès réservé au Chef (Niveau 2).", font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_DANGER).pack()
            return

        c = self.content
        tk.Label(c, text="Options avancées — Niveau 2", font=FONT_TITLE, bg=COLOR_BG, fg=COLOR_PRIMARY_DARK).pack(anchor="w")

        nb = ttk.Notebook(c)
        nb.pack(fill="both", expand=True, pady=15)

        self.build_tab_passwords(nb)
        self.build_tab_facture(nb)
        self.build_tab_supprimer(nb)
        self.build_tab_rapport_periode(nb)
        self.build_tab_reouverture(nb)

    # ---- Modifier les mots de passe ----
    def build_tab_passwords(self, nb):
        tab = tk.Frame(nb, bg="white", padx=20, pady=20)
        nb.add(tab, text="Mots de passe")

        tk.Label(tab, text="Modifier les mots de passe", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=0, column=0, columnspan=2, pady=(0, 15), sticky="w")
        labels = ["Nouveau mot de passe niveau 1", "Confirmer niveau 1", "Nouveau mot de passe niveau 2", "Confirmer niveau 2"]
        self.pwd_vars = {}
        for i, lbl in enumerate(labels, start=1):
            tk.Label(tab, text=lbl, bg="white").grid(row=i, column=0, sticky="w", pady=6)
            v = tk.StringVar()
            ttk.Entry(tab, textvariable=v, show="*", width=28).grid(row=i, column=1, padx=10)
            self.pwd_vars[lbl] = v
        ttk.Button(tab, text="Mettre à jour", command=self.update_passwords).grid(row=len(labels) + 1, column=0, columnspan=2, pady=15)

    def update_passwords(self):
        v = {k: val.get() for k, val in self.pwd_vars.items()}
        conn = get_conn()
        row = conn.execute("SELECT * FROM config WHERE id=1").fetchone()
        pwd1_hash, pwd2_hash = row["pwd1_hash"], row["pwd2_hash"]

        if v["Nouveau mot de passe niveau 1"]:
            if v["Nouveau mot de passe niveau 1"] != v["Confirmer niveau 1"]:
                messagebox.showerror("Erreur", "La confirmation du mot de passe niveau 1 ne correspond pas.")
                conn.close()
                return
            pwd1_hash = hash_pwd(v["Nouveau mot de passe niveau 1"])
        if v["Nouveau mot de passe niveau 2"]:
            if v["Nouveau mot de passe niveau 2"] != v["Confirmer niveau 2"]:
                messagebox.showerror("Erreur", "La confirmation du mot de passe niveau 2 ne correspond pas.")
                conn.close()
                return
            pwd2_hash = hash_pwd(v["Nouveau mot de passe niveau 2"])

        conn.execute("UPDATE config SET pwd1_hash=?, pwd2_hash=? WHERE id=1", (pwd1_hash, pwd2_hash))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", "Mots de passe mis à jour.")
        for v in self.pwd_vars.values():
            v.set("")

    # ---- Modifier une facture ----
    def build_tab_facture(self, nb):
        tab = tk.Frame(nb, bg="white", padx=20, pady=20)
        nb.add(tab, text="Modifier une facture")

        tk.Label(tab, text="Rechercher une facture par numéro", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w")
        row = tk.Frame(tab, bg="white")
        row.pack(fill="x", pady=10)
        self.search_num = tk.StringVar()
        ttk.Entry(row, textvariable=self.search_num, width=30).pack(side="left")
        ttk.Button(row, text="Rechercher", command=self.search_facture).pack(side="left", padx=10)

        self.search_result = tk.Frame(tab, bg="white")
        self.search_result.pack(fill="both", expand=True, pady=10)

    def search_facture(self):
        for w in self.search_result.winfo_children():
            w.destroy()
        num = self.search_num.get().strip()
        conn = get_conn()
        row = conn.execute("SELECT * FROM factures WHERE numero LIKE ?", (f"%{num}%",)).fetchone()
        conn.close()
        if not row:
            tk.Label(self.search_result, text="Aucune facture trouvée.", bg="white", fg=COLOR_DANGER).pack()
            return
        tk.Label(self.search_result, text=f"Facture {row['numero']} — {row['client_nom']} — {row['total']:.0f} F CFA",
                 font=FONT_BOLD, bg="white").pack(anchor="w", pady=5)
        ttk.Button(self.search_result, text="Voir / Modifier", command=lambda: show_facture_detail(self.app, row["id"], allow_edit=True)).pack(anchor="w")

    # ---- Supprimer un produit ----
    def build_tab_supprimer(self, nb):
        tab = tk.Frame(nb, bg="white", padx=20, pady=20)
        nb.add(tab, text="Supprimer un produit")

        tk.Label(tab, text="Supprimer un produit existant en stock", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))

        tk.Label(tab, text="Type", bg="white").grid(row=1, column=0, sticky="w", pady=6)
        self.del_type_var = tk.StringVar(value=TYPE_LABELS["MP"])
        combo = ttk.Combobox(tab, textvariable=self.del_type_var, state="readonly", width=25, values=list(TYPE_LABELS.values()))
        combo.grid(row=1, column=1, padx=10)
        combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_del_produits())

        tk.Label(tab, text="Produit", bg="white").grid(row=2, column=0, sticky="w", pady=6)
        self.del_produit_var = tk.StringVar()
        self.del_produit_combo = ttk.Combobox(tab, textvariable=self.del_produit_var, state="readonly", width=25)
        self.del_produit_combo.grid(row=2, column=1, padx=10)

        ttk.Button(tab, text="🗑 Supprimer", command=self.supprimer_produit).grid(row=3, column=0, columnspan=2, pady=15)
        self.refresh_del_produits()

    def refresh_del_produits(self):
        tc = [k for k, v in TYPE_LABELS.items() if v == self.del_type_var.get()][0]
        rows = get_stock(tc)
        self.del_produit_combo["values"] = [r["nom"] for r in rows]

    def supprimer_produit(self):
        tc = [k for k, v in TYPE_LABELS.items() if v == self.del_type_var.get()][0]
        nom = self.del_produit_var.get()
        if not nom:
            messagebox.showerror("Erreur", "Sélectionnez un produit.")
            return
        if not messagebox.askyesno("Confirmation", f"Supprimer définitivement « {nom} » du stock ?"):
            return
        table = TYPES_PRODUITS[tc]
        conn = get_conn()
        conn.execute(f"DELETE FROM {table} WHERE nom=?", (nom,))
        conn.commit()
        conn.close()
        log_mouvement(TYPE_LABELS[tc], nom, 0, "Suppression produit", self.app.session["pseudo"])
        messagebox.showinfo("Succès", f"« {nom} » a été supprimé du stock.")
        self.refresh_del_produits()

    # ---- Rapport sur période ----
    def build_tab_rapport_periode(self, nb):
        tab = tk.Frame(nb, bg="white", padx=20, pady=20)
        nb.add(tab, text="Rapport par période")

        tk.Label(tab, text="Rapport sur une période donnée", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(0, 15))

        row = tk.Frame(tab, bg="white")
        row.pack(fill="x", pady=5)
        tk.Label(row, text="Du :", bg="white").pack(side="left")
        self.date_debut = DatePickerEntry(row, initial_date=yesterday_str())
        self.date_debut.pack(side="left", padx=10)
        tk.Label(row, text="Au :", bg="white").pack(side="left")
        self.date_fin = DatePickerEntry(row, initial_date=today_str())
        self.date_fin.pack(side="left", padx=10)
        ttk.Button(row, text="Générer", command=self.generer_rapport_periode).pack(side="left", padx=10)

        self.periode_result = tk.Frame(tab, bg="white")
        self.periode_result.pack(fill="both", expand=True, pady=15)

    def generer_rapport_periode(self):
        for w in self.periode_result.winfo_children():
            w.destroy()
        d1, d2 = self.date_debut.get(), self.date_fin.get()
        conn = get_conn()
        ventes = conn.execute("SELECT COALESCE(SUM(total),0) as t, COUNT(*) as n FROM factures WHERE date_jour BETWEEN ? AND ?", (d1, d2)).fetchone()
        depenses = conn.execute("SELECT COALESCE(SUM(montant),0) as t FROM depenses WHERE date_jour BETWEEN ? AND ?", (d1, d2)).fetchone()
        factures = conn.execute("SELECT * FROM factures WHERE date_jour BETWEEN ? AND ? ORDER BY date_heure", (d1, d2)).fetchall()
        conn.close()
        total_prestations, nb_prestations = get_prestations_total(d1, d2)
        chiffre_affaires = ventes["t"] + total_prestations

        tk.Label(self.periode_result, text=f"Période : {fmt_date_fr(d1)} → {fmt_date_fr(d2)}", font=FONT_BOLD, bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Nombre de factures : {ventes['n']}", bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Total des ventes : {ventes['t']:,.0f} F CFA".replace(",", " "), bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Total des prestations de services ({nb_prestations}) : {total_prestations:,.0f} F CFA".replace(",", " "), bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Chiffre d'affaires : {chiffre_affaires:,.0f} F CFA".replace(",", " "), font=FONT_BOLD, bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Total des dépenses : {depenses['t']:,.0f} F CFA".replace(",", " "), bg="white").pack(anchor="w")
        tk.Label(self.periode_result, text=f"Bénéfice net : {chiffre_affaires - depenses['t']:,.0f} F CFA".replace(",", " "),
                 font=FONT_BOLD, fg=COLOR_PRIMARY, bg="white").pack(anchor="w", pady=(0, 10))

        tree = ttk.Treeview(self.periode_result, columns=("numero", "date", "client", "total"), show="headings", height=8)
        for c, t in zip(("numero", "date", "client", "total"), ("N° Facture", "Date", "Client", "Total")):
            tree.heading(c, text=t)
            tree.column(c, anchor="center")
        tree.pack(fill="both", expand=True)
        for f in factures:
            tree.insert("", "end", values=(f["numero"], f["date_heure"], f["client_nom"], f"{f['total']:.0f}"))

    # ---- Réouverture de journée ----
    def build_tab_reouverture(self, nb):
        tab = tk.Frame(nb, bg="white", padx=20, pady=20)
        nb.add(tab, text="Réouverture de journée")

        tk.Label(tab, text="Rouvrir une journée clôturée", font=FONT_SUBTITLE, bg="white", fg=COLOR_PRIMARY_DARK).pack(anchor="w", pady=(0, 15))
        row = tk.Frame(tab, bg="white")
        row.pack(fill="x")
        tk.Label(row, text="Date :", bg="white").pack(side="left")
        self.reopen_date = DatePickerEntry(row, initial_date=today_str())
        self.reopen_date.pack(side="left", padx=10)
        ttk.Button(row, text="Rouvrir la journée", command=self.reopen_journee).pack(side="left", padx=10)

    def reopen_journee(self):
        d = self.reopen_date.get()
        if not is_journee_cloturee(d):
            messagebox.showinfo("Info", "Cette journée n'est pas clôturée.")
            return
        if not messagebox.askyesno("Confirmation", f"Rouvrir la journée du {fmt_date_fr(d)} ?"):
            return
        conn = get_conn()
        conn.execute("UPDATE journees SET cloturee=0 WHERE date_jour=?", (d,))
        conn.commit()
        conn.close()
        messagebox.showinfo("Succès", "Journée rouverte avec succès.")


# ------------------------------------------------------------------
# LANCEMENT
# ------------------------------------------------------------------
if __name__ == "__main__":
    app = AnimaApp()
    app.mainloop()
