# AMINA FDS — Logiciel de Gestion de Stock

> **Mise à jour** : correction de l'erreur `sqlite3.OperationalError: unable
> to open database file` qui pouvait survenir après installation de
> l'exécutable (la base de données est maintenant stockée dans le dossier
> personnel de l'utilisateur, voir §4bis) + saisie du nom des produits
> désormais automatiquement capitalisée (première lettre en majuscule).

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
| `anima_fds.db`                   | Base de données (créée automatiquement, voir §4bis ci-dessous)    |

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

## 4bis. Emplacement des données (important)

Pour que le logiciel fonctionne **quel que soit l'endroit où il est installé**
(y compris dans `Program Files`, qui est protégé en écriture pour les
utilisateurs normaux), la base de données **n'est pas stockée à côté de
l'exécutable**. Elle est automatiquement créée dans le dossier personnel de
l'utilisateur Windows :

```
%APPDATA%\AMINA_FDS\anima_fds.db
```

soit généralement :

```
C:\Users\<votre_nom>\AppData\Roaming\AMINA_FDS\anima_fds.db
```

Les rapports exportés (PDF / Excel) sont quant à eux enregistrés dans :

```
C:\Users\<votre_nom>\AppData\Roaming\AMINA_FDS\rapports\
```

> Pensez à faire une copie régulière du dossier `AMINA_FDS` (dans
> `AppData\Roaming`) pour sauvegarder vos données. Vous pouvez accéder
> rapidement à ce dossier en collant `%APPDATA%\AMINA_FDS` dans la barre
> d'adresse de l'explorateur Windows.

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

## 11. Support technique

Toutes les données sont stockées localement dans le fichier `anima_fds.db`
(base SQLite) situé dans `%APPDATA%\AMINA_FDS\` (voir §4bis). Pensez à en faire une
copie de sauvegarde régulièrement (clé USB, cloud, etc.).
