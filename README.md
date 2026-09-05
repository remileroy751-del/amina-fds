# AMINA FDS — Logiciel de Gestion de Stock

> **Mise à jour v1.2.1** : nouveau menu **Prestation de Services** avec établissement de factures multi-lignes pour les prestations d'infographie et autres services, panier, total en temps réel, TVA à 18 %, informations client et montant total en lettres. Les factures de services sont enregistrées séparément et intégrées au chiffre d'affaires.


> **Mise à jour v1.1.0** : ajout du prix unitaire de vente pour les produits
> semi-finis (désormais vendables) ; nouvel onglet **Dépenses** dédié
> (Secrétaire + Chef) avec date modifiable, libellé et montant ; possibilité
> pour le Chef de modifier les prix de vente des produits semi-finis/finis
> depuis Options avancées ; tableau de bord du Chef enrichi avec le chiffre
> d'affaires, le bénéfice brut et le bénéfice net du jour ; mise en
> surbrillance (jaune foncé / texte noir) du bouton de menu actif.
>
> **Mise à jour précédente** : correction de l'erreur `sqlite3.OperationalError:
> unable to open database file` qui pouvait survenir après installation de
> l'exécutable (la base de données est maintenant stockée dans le dossier
> personnel de l'utilisateur, voir §4bis) + saisie du nom des produits
> désormais automatiquement capitalisée (première lettre en majuscule) +
> **vrai installateur Windows** (`AMINA_FDS_Setup.exe`) avec raccourci
> créé automatiquement sur le Bureau et désinstalleur (voir §4).

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
| `3_creer_executable_exe.bat`      | Étape 1/2 : transforme le logiciel en fichier `.exe` brut          |
| `4_creer_installateur.bat`        | Étape 2/2 : fabrique le vrai installateur Windows (`Setup.exe`)   |
| `installer/setup.iss`             | Script Inno Setup qui décrit l'installateur                       |
| `installer/app_icon.ico`          | Icône du logiciel (utilisée par l'exe, les raccourcis, l'installeur) |
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

## 4. Créer un vrai installateur Windows (recommandé pour vos clients/utilisateurs)

Pour donner à vos utilisateurs un **vrai logiciel qui s'installe** (comme
n'importe quel programme Windows : assistant d'installation, choix du
dossier, raccourci créé automatiquement sur le **Bureau**, entrée dans le
**menu Démarrer**, et désinstalleur propre dans *Paramètres > Applications*),
suivez ces deux étapes, dans l'ordre :

**Étape 1 — Fabriquer l'exécutable brut**
Double-cliquez sur **`3_creer_executable_exe.bat`**. Cela crée
`dist\AMINA_FDS.exe` (ce fichier seul, s'il est lancé directement, ouvre
juste le logiciel — il ne s'"installe" pas, c'est normal, ce n'est qu'une
étape intermédiaire).

**Étape 2 — Fabriquer l'installateur**
Double-cliquez sur **`4_creer_installateur.bat`**.
- Si c'est la première fois, ce script vous demandera d'installer
  **Inno Setup** (logiciel gratuit) depuis https://jrsoftware.org/isdl.php
  — installez-le avec les options par défaut, puis relancez le script.
- Le résultat final est le fichier **`installer\Output\AMINA_FDS_Setup.exe`**.

**C'est ce fichier `AMINA_FDS_Setup.exe` qu'il faut distribuer.** Quand un
utilisateur le lance :
1. Un véritable assistant d'installation Windows s'affiche (en français).
2. Le logiciel est installé dans `Program Files\AMINA_FDS`.
3. Une case cochée par défaut crée **automatiquement un raccourci sur le
   Bureau**, ainsi qu'un raccourci dans le menu Démarrer.
4. Un désinstalleur est ajouté dans *Paramètres > Applications* (Windows),
   permettant de retirer le logiciel proprement.

> 💡 Vous pouvez aussi obtenir ce même fichier `AMINA_FDS_Setup.exe`
> automatiquement, sans rien installer sur votre PC, grâce à GitHub Actions
> (voir §4ter ci-dessous).

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

## 4ter. Compilation automatique sur GitHub (CI/CD)

Ce dépôt contient un workflow **GitHub Actions** (`.github/workflows/build.yml`)
qui fabrique automatiquement le **véritable installateur**
`AMINA_FDS_Setup.exe` (celui avec raccourci Bureau automatique, pas juste
l'exe brut) sur une machine Windows fournie gratuitement par GitHub, sans que
tu aies besoin d'installer Python, PyInstaller ou Inno Setup sur ton propre
ordinateur.

**Comment ça marche :**

1. Crée un dépôt GitHub et pousse (`git push`) tout ce dossier dedans
   (branche `main`), en incluant bien le dossier `installer/`.
2. Va dans l'onglet **Actions** du dépôt sur GitHub.com.
3. Le workflow **"Compiler l'installateur AMINA_FDS"** se lance
   automatiquement :
   - à chaque `git push` sur `main` ;
   - ou manuellement via le bouton **"Run workflow"** ;
   - ou automatiquement en créant un tag de version, ex. `v1.0` (
     `git tag v1.0 && git push origin v1.0`) — dans ce cas, GitHub crée
     en plus une **Release** avec `AMINA_FDS_Setup.exe` prêt à télécharger.
4. Une fois le workflow terminé (icône verte ✔), clique dessus puis va
   dans **Artifacts** en bas de page : télécharge `AMINA_FDS_Setup`, qui
   contient `AMINA_FDS_Setup.exe` — le vrai installateur, prêt à distribuer
   tel quel.

> Aucune donnée sensible n'est nécessaire : le workflow utilise uniquement
> le jeton `GITHUB_TOKEN` fourni automatiquement par GitHub pour publier la
> Release.

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

## 11. Dépenses

Le menu **Dépenses** (accessible aux niveaux 1 et 2) permet d'enregistrer
autant de dépenses que nécessaire au cours d'une même journée :
- **Date** : aujourd'hui par défaut, modifiable via le sélecteur 📅 ;
- **Libellé de la dépense** (ex : carburant, réparation, achat de sacs...) ;
- **Montant (F CFA)**.

La liste et le total des dépenses de la date sélectionnée s'affichent
juste en dessous du formulaire.

## 12. Modifier les prix de vente (Chef uniquement)

Depuis **Options avancées → Modifier les prix**, le chef (niveau 2) peut
à tout moment changer le **prix unitaire de vente** d'un produit semi-fini
ou fini déjà en stock, sans avoir à le supprimer/recréer. Le nouveau prix
s'applique immédiatement aux ventes suivantes.

## 13. Tableau de bord du Chef — indicateurs financiers du jour

Sur le tableau de bord, le **chef (niveau 2)** voit en plus trois
indicateurs mis à jour en temps réel pour la journée en cours :
- **Chiffre d'affaires du jour** (ventes + prestations de services) ;
- **Bénéfice brut du jour** (chiffre d'affaires − coût de revient des
  produits semi-finis/finis vendus, au coût actuellement enregistré en
  stock) ;
- **Bénéfice net du jour** (bénéfice brut − dépenses de la journée).

---

## 14. Support technique

Toutes les données sont stockées localement dans le fichier `anima_fds.db`
(base SQLite) situé dans `%APPDATA%\AMINA_FDS\` (voir §4bis). Pensez à en faire une
copie de sauvegarde régulièrement (clé USB, cloud, etc.).


## Mise à jour 1.2.1 — Facturation
- Bouton **« Enregistrer la facture »** déplacé à côté de **« Ajouter au panier »**.
- Total de la facture affiché et actualisé en temps réel dès qu'une ligne est ajoutée/retirée du panier ou que le transport/TVA change.
- Nom du client et téléphone obligatoires ; quartier/adresse désormais facultatif.
- Ajout du **transport à la charge du client**, facultatif, intégré au total et conservé sur la facture.
- Montant total écrit en toutes lettres sur l'aperçu et sur les factures enregistrées.
- Migration automatique de la base SQLite existante : les anciennes factures conservent un transport à 0 F CFA.
- Version installateur : **1.2.1**.
