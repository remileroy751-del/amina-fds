# AMINA FDS — Logiciel de Gestion de Stock

Application de bureau (Windows) pour la gestion du stock, des ventes et des
rapports de **AMINA FDS**, spécialisée dans la production et la vente de
poudre de marbre et de ses dérivés.

---

## 1. Contenu du dossier

| Fichier                          | Rôle                                                             |
|-----------------------------------|-------------------------------------------------------------------|
| `main.py`                        | Le programme complet de l'application                             |
| `requirements.txt`                | Liste des librairies Python nécessaires                           |
| `1_installer.bat`                 | Installe automatiquement tout ce qu'il faut (à faire une fois)    |
| `2_lancer_AMINA_FDS.bat`          | Lance l'application au quotidien                                  |
| `3_creer_executable_exe.bat`      | (Optionnel) Transforme le logiciel en un vrai fichier `.exe`      |
| `assets/logo.jpg`                 | Logo AMINA FDS (affiché pendant la configuration et sur le tableau de bord) |
| `assets/mur.jpg`                  | Image des murs peints, utilisée comme décoration de l'application |
| `assets/icon.ico`                 | Icône du logiciel (utilisée par l'exécutable et l'installateur)   |
| `installer.iss`                   | Script Inno Setup qui génère l'installateur Windows (icône Bureau) |
| `.github/workflows/build.yml`     | Workflow GitHub Actions : compile automatiquement l'exécutable et l'installateur |
| `anima_fds.db`                   | Base de données (créée automatiquement au premier lancement)      |

> ⚠️ Le dossier **`assets`** doit toujours rester à côté de `main.py` (ou de
> `AMINA_FDS.exe` une fois compilé). S'il est absent, le logiciel fonctionne
> quand même normalement, mais sans logo ni décorations.

---

## 2. Installation (à faire une seule fois)

1. Installez **Python 3.10 ou plus récent** depuis https://www.python.org/downloads/
   - ⚠️ Lors de l'installation, cochez bien la case **"Add Python to PATH"**.
2. Copiez tout le dossier `anima_fds` sur l'ordinateur du bureau (ex: `C:\AMINA_FDS`).
3. Double-cliquez sur **`1_installer.bat`** et attendez la fin de l'installation.

## 3. Utilisation quotidienne

Double-cliquez simplement sur **`2_lancer_AMINA_FDS.bat`** pour ouvrir le logiciel.

## 4. (Optionnel) Créer un exécutable .exe autonome

Si vous voulez un fichier `.exe` unique (sans avoir besoin d'ouvrir de fichier `.bat`
ni de voir de fenêtre noire), double-cliquez sur **`3_creer_executable_exe.bat`**.
Une fois terminé, vous trouverez `AMINA_FDS.exe` dans le dossier `dist`.
Vous pouvez le copier sur le Bureau et créer un raccourci — c'est ce fichier
que vos utilisateurs lanceront ensuite au quotidien.

> Important : la base de données `anima_fds.db` doit toujours rester dans le
> même dossier que le programme (`main.py` ou `AMINA_FDS.exe`), car c'est là
> que sont enregistrées toutes vos données (stocks, factures, rapports...).
> Pensez à faire une copie régulière de ce fichier pour une sauvegarde.

---

## 5. Premier lancement — Configuration initiale

Au tout premier démarrage, l'application vous guide automatiquement :

1. **Message de bienvenue** : "Bienvenue DG FDS. Veuillez paramétrer votre
   application de gestion avant de commencer à l'utiliser." → cliquez sur **OK**.
2. **Compte administrateur** : définissez un **Pseudo**, un **mot de passe
   niveau 1** (secrétaire) et un **mot de passe niveau 2** (chef), avec
   confirmation pour chacun.
3. **Stock initial** : saisissez, dans l'ordre, vos matières premières, vos
   produits semi-finis, puis vos produits finis déjà en stock (nom, quantité
   en Kg, coût, et prix de vente pour les produits finis). Vous pouvez en
   enregistrer autant que nécessaire avant de passer à l'étape suivante.
4. Cliquez sur **Terminer** → vous arrivez sur l'écran de connexion.

## 6. Connexion et niveaux d'accès

- **Niveau 1 (mot de passe niveau 1)** — *Secrétaire* :
  - Consulter le stock en temps réel
  - Faire des entrées en stock
  - Réaliser des ventes et générer des factures (avec option TVA 18%)
  - Enregistrer des prestations de services (augmentent le chiffre d'affaires)
  - Consulter les rapports du jour et de la veille
  - Enregistrer les dépenses du jour
  - Exporter les rapports en PDF ou Excel
  - Clôturer la journée

- **Niveau 2 (mot de passe niveau 2)** — *Chef* :
  - Toutes les fonctions du niveau 1
  - Voit en plus la **valeur monétaire** du stock (prix de vente x quantité)
  - **Options avancées** :
    - Modifier les mots de passe niveau 1 et niveau 2
    - Modifier une facture déjà enregistrée
    - Supprimer un produit du stock
    - Générer un rapport sur une période donnée (avec calendrier)
    - Rouvrir une journée clôturée

## 7. Fonctionnement des ventes

1. Cliquez sur **Vendre**.
2. Ajoutez un ou plusieurs produits (semi-finis et/ou finis) au panier.
3. Renseignez obligatoirement le **nom**, le **téléphone** et **le quartier /
   adresse** du client.
4. Cliquez sur **Aperçu Facture** : la facture s'affiche en mode prévisualisation
   avec un bouton **Modifier** (pour revenir en arrière) et un bouton
   **Enregistrer définitivement**.
5. Une fois enregistrée, la facture reçoit un numéro unique, le stock est
   automatiquement décrémenté, et elle apparaît dans la liste des factures
   du jour (double-cliquez dessus pour en voir le détail).
6. Seul le **niveau 2 (chef)** peut modifier une facture déjà enregistrée
   (menu Options avancées → Modifier une facture).

## 8. Prestation de services

Le menu **Prestations de services** permet d'enregistrer une prestation
hors-produit (transport, main d'œuvre, installation, etc.) : il suffit de
saisir le **libellé** du service et son **montant**, puis de cliquer sur
**Enregistrer**. Ce montant vient automatiquement augmenter le **chiffre
d'affaires** de la journée dans les rapports (en plus des ventes de produits).

## 9. TVA (18%) sur les factures

Lors d'une vente, une case à cocher **« Appliquer la TVA (18%) »** est
disponible juste avant de générer l'aperçu de la facture :
- Si elle est **décochée**, la facture affiche uniquement le **MONTANT TOTAL**
  (= somme des lignes du panier).
- Si elle est **cochée**, la facture affiche le **Sous-total HT**, la
  **TVA (18%)**, puis le **MONTANT TOTAL** (HT + TVA). C'est ce montant TTC
  qui est enregistré et décompté du stock.

## 10. Clôture de journée

Le bouton **Clôturer la journée** (accessible aux niveaux 1 et 2) empêche
toute nouvelle saisie (stock, vente, dépense) pour la journée en cours.
Seul le **chef (niveau 2)** peut rouvrir une journée clôturée, via
**Options avancées → Réouverture de journée**.

---

## 11. Période d'essai gratuite (7 jours)

Ce logiciel intègre une **période d'essai gratuite de 7 jours**, décomptée à
partir de la toute première ouverture de l'application (date enregistrée
automatiquement dans la base de données locale).

- Pendant les 7 premiers jours : l'application fonctionne normalement, sans
  aucune restriction.
- Passé ce délai : au lancement, un écran **« Période d'essai terminée »**
  s'affiche à la place de l'écran de connexion habituel, et demande un
  **code de déverrouillage**.
- Une fois le bon code saisi, l'application est **déverrouillée
  définitivement** sur cet ordinateur (le blocage ne réapparaît plus, même
  après la date du 7ᵉ jour).
- Le code correct n'est jamais stocké ni affiché en clair dans le code
  source : seule son empreinte (hash SHA-256) y figure.

## 12. Compiler l'exécutable et l'installateur (GitHub Actions)

Ce dépôt est prêt à être poussé tel quel sur GitHub : un workflow automatique
(`.github/workflows/build.yml`) se charge de tout compiler dès que vous
poussez sur la branche `main` (ou manuellement via l'onglet **Actions →
Run workflow**).

Le workflow effectue, sur une machine Windows :
1. La compilation de `main.py` en un exécutable autonome `AMINA_FDS.exe`
   (PyInstaller, avec l'icône `assets/icon.ico`).
2. La génération d'un **véritable installateur** `AMINA_FDS_Setup.exe`
   (via Inno Setup et `installer.iss`), qui installe le logiciel dans
   `Program Files`, crée un raccourci dans le Menu Démarrer **et une icône
   de lancement sur le Bureau** — exactement comme un logiciel commercial
   classique.

Une fois le workflow terminé, les deux fichiers (`AMINA_FDS.exe` et
`AMINA_FDS_Setup.exe`) sont disponibles en téléchargement dans l'onglet
**Actions** du dépôt (section *Artifacts*). Si vous poussez un tag de
version (ex. `v1.0`), ils sont en plus automatiquement joints à une
**Release GitHub**.

C'est le fichier **`AMINA_FDS_Setup.exe`** qu'il faut envoyer au client :
en le lançant, il installe le logiciel et dépose directement l'icône de
lancement sur son Bureau.

---

## 13. Support technique

Toutes les données sont stockées localement dans le fichier `anima_fds.db`
(base SQLite) situé dans le dossier de l'application. Pensez à en faire une
copie de sauvegarde régulièrement (clé USB, cloud, etc.).
