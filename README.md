<div align="center">

# Magasin de Jeux Video

**Plateforme e-commerce de vente de jeux video**

Flask / MySQL / Pandas

<br>

<table>
<tr>
<td><strong>Langage</strong></td>
<td><strong>Framework</strong></td>
<td><strong>Base de donnees</strong></td>
<td><strong>Deploiement</strong></td>
</tr>
<tr>
<td>Python 3.10+</td>
<td>Flask 3.0</td>
<td>MySQL 8.x</td>
<td>Gunicorn</td>
</tr>
</table>

</div>

---

## Table des matieres

<details>
<summary>Afficher / Masquer</summary>

1. [Presentation du projet](#presentation-du-projet)
2. [Fonctionnalites](#fonctionnalites)
3. [Architecture technique](#architecture-technique)
4. [Structure du projet](#structure-du-projet)
5. [Modele de donnees](#modele-de-donnees)
6. [Routes et API](#routes-et-api)
7. [Couche metier](#couche-metier)
8. [Templates et interface](#templates-et-interface)
9. [Installation et configuration](#installation-et-configuration)
10. [Utilisation](#utilisation)
11. [Securite](#securite)
12. [Documentation complementaire](#documentation-complementaire)

</details>

---

## Presentation du projet

Ce projet est une application web e-commerce dediee a la vente de jeux video. Elle propose un catalogue de **60 titres** couvrant les principales plateformes du marche (PS5, Xbox, Nintendo Switch, PC) et offre une experience complete allant de la navigation dans le catalogue jusqu'a la gestion des commandes, en passant par un panier d'achat, un systeme d'avis clients et un tableau de bord administrateur.

L'application repose sur une architecture **MVC** avec :

- **`app.py`** -- routeur Flask (controleur / vue)
- **`magasin.py`** -- logique metier et acces aux donnees (modele)
- **`config.py`** -- configuration applicative

Le projet est entierement redige en **francais** (interface utilisateur, commentaires, noms de variables).

---

## Fonctionnalites

### Espace client

<table>
<thead>
<tr>
<th>Module</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Inscription / Connexion</strong></td>
<td>Creation de compte avec validation des champs (email unique, telephone au format francais, code postal, geolocalisation). Authentification par email et mot de passe hache.</td>
</tr>
<tr>
<td><strong>Catalogue</strong></td>
<td>Navigation dans les 60 jeux disponibles avec filtres par nom, categorie, plateforme, classification ESRB et fourchette de prix.</td>
</tr>
<tr>
<td><strong>Panier</strong></td>
<td>Ajout, suppression et modification des quantites. Le panier est conserve en session.</td>
</tr>
<tr>
<td><strong>Commandes</strong></td>
<td>Validation du panier, creation de commande avec mise a jour automatique des stocks. Suivi du statut et possibilite d'annulation.</td>
</tr>
<tr>
<td><strong>Avis</strong></td>
<td>Systeme de notation de 1 a 5 etoiles avec titre et commentaire. Un avis par commande, modifiable et supprimable.</td>
</tr>
<tr>
<td><strong>Profil</strong></td>
<td>Modification des informations personnelles (nom, email, telephone, adresse) avec autocompletion geographique.</td>
</tr>
<tr>
<td><strong>Tableau de bord</strong></td>
<td>Resume des commandes, historique d'achats et avis recents.</td>
</tr>
</tbody>
</table>

### Espace administrateur

<table>
<thead>
<tr>
<th>Module</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><strong>Gestion des produits</strong></td>
<td>CRUD complet : ajout, modification, suppression de jeux. Gestion des images, descriptions et metadonnees.</td>
</tr>
<tr>
<td><strong>Gestion des clients</strong></td>
<td>Consultation, ajout, modification et suppression de comptes clients. Segmentation automatique (premium, regular, casual, vip).</td>
</tr>
<tr>
<td><strong>Gestion des commandes</strong></td>
<td>Visualisation de toutes les commandes, filtrage par statut ou client, mise a jour du statut (pending, processing, shipped, delivered, cancelled).</td>
</tr>
<tr>
<td><strong>Gestion des stocks</strong></td>
<td>Suivi des quantites en stock, reservees et disponibles par produit et vendeur. Seuils d'alerte (stock minimum, point de reapprovisionnement).</td>
</tr>
<tr>
<td><strong>Tableau de bord</strong></td>
<td>Vue d'ensemble avec acces rapide a toutes les sections d'administration.</td>
</tr>
</tbody>
</table>

---

## Architecture technique

### Stack technologique

<table>
<thead>
<tr>
<th>Couche</th>
<th>Technologie</th>
<th>Version</th>
<th>Role</th>
</tr>
</thead>
<tbody>
<tr>
<td>Framework web</td>
<td>Flask</td>
<td>3.0+</td>
<td>Routage HTTP, sessions, templates Jinja2</td>
</tr>
<tr>
<td>Langage</td>
<td>Python</td>
<td>3.10+</td>
<td>Logique applicative</td>
</tr>
<tr>
<td>Base de donnees</td>
<td>MySQL</td>
<td>8.x</td>
<td>Persistance des donnees</td>
</tr>
<tr>
<td>Connecteur BDD</td>
<td>mysql-connector-python</td>
<td>8.0+</td>
<td>Communication avec MySQL</td>
</tr>
<tr>
<td>Traitement de donnees</td>
<td>Pandas</td>
<td>2.0+</td>
<td>Manipulation des donnees en DataFrames</td>
</tr>
<tr>
<td>Hachage</td>
<td>Werkzeug</td>
<td>3.0+</td>
<td>Hachage bcrypt des mots de passe</td>
</tr>
<tr>
<td>Serveur WSGI</td>
<td>Gunicorn</td>
<td>21.2+</td>
<td>Deploiement en production</td>
</tr>
<tr>
<td>Front-end</td>
<td>HTML5, CSS3, JavaScript</td>
<td>--</td>
<td>Interface utilisateur (sans framework JS)</td>
</tr>
</tbody>
</table>

### Diagramme d'architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Navigateur                         │
│              HTML / CSS / JavaScript                    │
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                    Flask (app.py)                        │
│         Routes, Sessions, Templates Jinja2              │
└──────────────────────┬──────────────────────────────────┘
                       │ Appels de methodes
┌──────────────────────▼──────────────────────────────────┐
│               Magasin (magasin.py)                       │
│     Logique metier, Validation, Pandas DataFrames       │
└──────────────────────┬──────────────────────────────────┘
                       │ mysql-connector-python
┌──────────────────────▼──────────────────────────────────┐
│                    MySQL 8.x                            │
│              9 tables, donnees de test                   │
└─────────────────────────────────────────────────────────┘
```

---

## Structure du projet

```
AppDec_VideoGame/
│
├── app.py                      # Application Flask (routes, controleurs)
├── magasin.py                  # Couche metier et acces aux donnees
├── config.py                   # Configuration Flask (cle secrete, cookies)
├── requirements.txt            # Dependances Python
├── .gitignore                  # Fichiers exclus du depot
│
├── templates/                  # Templates Jinja2
│   ├── base.html               #   Template de base (navigation, footer)
│   ├── login.html              #   Page de connexion
│   ├── register.html           #   Page d'inscription
│   ├── dashboard.html          #   Tableau de bord administrateur
│   ├── dashboard_client.html   #   Tableau de bord client
│   ├── profile.html            #   Edition du profil utilisateur
│   ├── products.html           #   Liste des produits (admin)
│   ├── products_store.html     #   Boutique (client)
│   ├── edit_product.html       #   Edition d'un produit (admin)
│   ├── customers.html          #   Liste des clients (admin)
│   ├── edit_customer.html      #   Edition d'un client (admin)
│   ├── cart.html               #   Panier d'achat
│   ├── orders.html             #   Commandes du client
│   ├── orders_admin.html       #   Commandes (admin)
│   ├── order_detail.html       #   Detail d'une commande et avis
│   └── stock.html              #   Gestion des stocks (admin)
│
├── static/
│   ├── css/
│   │   └── style.css           # Feuille de style principale
│   └── images/                 # Images des 60 jeux du catalogue
│
└── docs/
    ├── magasin_jeux_video.sql          # Schema et donnees SQL complet
    ├── README_populate.txt             # Instructions de peuplement BDD
    ├── Cahier des charges.pdf          # Cahier des charges du projet
    ├── cahier_analyse_specifications.docx  # Analyse et specifications
    └── diagrammes/
        ├── UML.jpg                     # Diagramme de classes UML
        ├── UML.loo                     # Source du diagramme (Looping)
        ├── UML_magasin.txt             # Schema UML en format texte
        ├── Activité_Ajout_Produits.png # Diagramme d'activite
        ├── Activité_Ajout_Produits.mdj # Source du diagramme d'activite
        └── LoopingImage.jpg            # Diagramme relationnel
```

---

## Modele de donnees

L'application repose sur **9 tables** MySQL interconnectees. Le schema complet est disponible dans `docs/magasin_jeux_video.sql`.

### Schema relationnel

```
geolocation ─────┬──────── customers ──────── orders ──────┬── order_items
  (zip_code)     │         (customer_id)     (order_id)    │   (order_id, item_id)
                 │                                          │       │         │
                 │                                          ├── order_payments │
                 │                                          │   (order_id)     │
                 │                                          │                  │
                 └──────── sellers ──────── stock           └── order_reviews  │
                           (seller_id)     (stock_id)           (review_id)   │
                               │                                              │
                               └────────────── products ◄─────────────────────┘
                                               (product_id)
```

### Description des tables

<details>
<summary><strong>geolocation</strong> -- Referentiel geographique (38 villes francaises)</summary>

| Colonne | Type | Description |
|---|---|---|
| `zip_code_prefix` | `INT` | Code postal (cle primaire) |
| `city` | `VARCHAR(100)` | Nom de la ville |
| `state` | `VARCHAR(50)` | Departement |
| `region` | `VARCHAR(100)` | Region administrative |
| `latitude` | `DECIMAL(10,7)` | Coordonnee GPS |
| `longitude` | `DECIMAL(10,7)` | Coordonnee GPS |

</details>

<details>
<summary><strong>customers</strong> -- Clients (100 enregistrements)</summary>

| Colonne | Type | Description |
|---|---|---|
| `customer_id` | `VARCHAR(50)` | Identifiant unique (CUST_XXXXX) |
| `first_name` | `VARCHAR(100)` | Prenom |
| `last_name` | `VARCHAR(100)` | Nom |
| `email` | `VARCHAR(255)` | Adresse email (unique) |
| `password_hash` | `VARCHAR(255)` | Mot de passe hache (bcrypt) |
| `is_admin` | `TINYINT(1)` | Role administrateur (0 ou 1) |
| `phone` | `VARCHAR(20)` | Telephone (format FR) |
| `zip_code_prefix` | `INT` | Code postal (FK geolocation) |
| `city` | `VARCHAR(100)` | Ville |
| `state` | `VARCHAR(50)` | Departement |
| `address_line1` | `VARCHAR(255)` | Adresse ligne 1 |
| `address_line2` | `VARCHAR(255)` | Adresse ligne 2 |
| `customer_segment` | `VARCHAR(50)` | Segment (premium, regular, casual, vip) |
| `registration_date` | `DATETIME` | Date d'inscription |
| `last_purchase_date` | `DATETIME` | Dernier achat |
| `total_orders` | `INT` | Nombre total de commandes |
| `total_spent` | `DECIMAL(10,2)` | Montant total depense |

</details>

<details>
<summary><strong>products</strong> -- Catalogue de jeux video (60 titres)</summary>

| Colonne | Type | Description |
|---|---|---|
| `product_id` | `VARCHAR(50)` | Identifiant unique (PROD_XXXXX) |
| `product_name` | `VARCHAR(255)` | Nom du jeu |
| `product_category` | `VARCHAR(100)` | Categorie (Action RPG, Sports, Aventure...) |
| `product_platform` | `VARCHAR(50)` | Plateforme (PS5, Xbox, Switch, PC, Multi) |
| `product_esrb_rating` | `VARCHAR(20)` | Classification d'age (3+, 7+, 12+, 16+, 18+) |
| `product_release_year` | `INT` | Annee de sortie |
| `product_price` | `DECIMAL(10,2)` | Prix en euros |
| `product_weight_g` | `INT` | Poids en grammes |
| `product_description` | `TEXT` | Description du jeu |
| `product_image` | `TEXT` | Chemin vers l'image |
| `created_at` | `DATETIME` | Date de creation |

</details>

<details>
<summary><strong>sellers</strong> -- Vendeurs et points de vente</summary>

| Colonne | Type | Description |
|---|---|---|
| `seller_id` | `VARCHAR(50)` | Identifiant unique (SELLER_XXXX) |
| `seller_name` | `VARCHAR(255)` | Nom du vendeur |
| `seller_type` | `VARCHAR(50)` | Type (Store, Warehouse, Distributor) |
| `zip_code_prefix` | `INT` | Code postal (FK geolocation) |
| `city` | `VARCHAR(100)` | Ville |
| `state` | `VARCHAR(50)` | Departement |
| `created_at` | `DATETIME` | Date de creation |

</details>

<details>
<summary><strong>orders</strong> -- Commandes (350+ enregistrements)</summary>

| Colonne | Type | Description |
|---|---|---|
| `order_id` | `VARCHAR(50)` | Identifiant unique (ORDER_XXXXXX) |
| `customer_id` | `VARCHAR(50)` | Client (FK customers) |
| `order_status` | `VARCHAR(50)` | Statut de la commande |
| `order_purchase_timestamp` | `DATETIME` | Date de creation |
| `order_approved_at` | `DATETIME` | Date d'approbation |
| `order_delivered_carrier_date` | `DATETIME` | Date de remise au transporteur |
| `order_delivered_customer_date` | `DATETIME` | Date de livraison |

**Cycle de vie d'une commande :**

```
pending ──► processing ──► shipped ──► delivered
               │
               └──► cancelled
```

</details>

<details>
<summary><strong>order_items</strong> -- Lignes de commande</summary>

| Colonne | Type | Description |
|---|---|---|
| `order_id` | `VARCHAR(50)` | Commande (FK orders, CASCADE) |
| `order_item_id` | `INT` | Numero de ligne |
| `product_id` | `VARCHAR(50)` | Produit (FK products) |
| `seller_id` | `VARCHAR(50)` | Vendeur (FK sellers) |
| `price` | `DECIMAL(10,2)` | Prix unitaire au moment de l'achat |
| `freight_value` | `DECIMAL(10,2)` | Frais de livraison |
| `quantity` | `INT` | Quantite commandee |
| `shipping_limit_date` | `DATETIME` | Date limite d'expedition |

Cle primaire composite : `(order_id, order_item_id)`

</details>

<details>
<summary><strong>order_payments</strong> -- Paiements</summary>

| Colonne | Type | Description |
|---|---|---|
| `order_id` | `VARCHAR(50)` | Commande (FK orders, CASCADE) |
| `payment_sequential` | `INT` | Numero sequentiel du paiement |
| `payment_type` | `VARCHAR(50)` | Type (credit_card, paypal, etc.) |
| `payment_installments` | `INT` | Nombre d'echeances |
| `payment_value` | `DECIMAL(10,2)` | Montant du paiement |
| `payment_approved_at` | `DATETIME` | Date d'approbation |

Cle primaire composite : `(order_id, payment_sequential)`

</details>

<details>
<summary><strong>order_reviews</strong> -- Avis clients</summary>

| Colonne | Type | Description |
|---|---|---|
| `review_id` | `VARCHAR(50)` | Identifiant unique (REVIEW_XXXXX) |
| `order_id` | `VARCHAR(50)` | Commande (FK orders, CASCADE) |
| `review_score` | `INT` | Note de 1 a 5 |
| `review_comment_title` | `VARCHAR(255)` | Titre de l'avis |
| `review_comment_message` | `TEXT` | Contenu de l'avis |
| `review_creation_date` | `DATETIME` | Date de creation |

</details>

<details>
<summary><strong>stock</strong> -- Gestion des stocks</summary>

| Colonne | Type | Description |
|---|---|---|
| `stock_id` | `VARCHAR(50)` | Identifiant unique (STOCK_XXXXX) |
| `product_id` | `VARCHAR(50)` | Produit (FK products) |
| `seller_id` | `VARCHAR(50)` | Vendeur (FK sellers) |
| `quantity_in_stock` | `INT` | Quantite totale en stock |
| `quantity_reserved` | `INT` | Quantite reservee (commandes en cours) |
| `quantity_available` | `INT` | Quantite disponible a la vente |
| `min_stock_level` | `INT` | Seuil minimum d'alerte (defaut : 12) |
| `reorder_point` | `INT` | Point de reapprovisionnement (defaut : 19) |
| `last_updated` | `DATETIME` | Derniere mise a jour |
| `warehouse_location` | `VARCHAR(50)` | Emplacement en entrepot |
| `stock_condition` | `VARCHAR(50)` | Etat (new, used, refurbished) |

Contrainte d'unicite : `(seller_id, product_id)`

</details>

---

## Routes et API

### Pages web

<table>
<thead>
<tr>
<th>Methode</th>
<th>Route</th>
<th>Acces</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr><td colspan="4"><strong>Authentification</strong></td></tr>
<tr>
<td><code>GET</code> <code>POST</code></td>
<td><code>/login</code></td>
<td>Public</td>
<td>Connexion utilisateur</td>
</tr>
<tr>
<td><code>GET</code> <code>POST</code></td>
<td><code>/register</code></td>
<td>Public</td>
<td>Inscription d'un nouveau client</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/logout</code></td>
<td>Connecte</td>
<td>Deconnexion et suppression de session</td>
</tr>
<tr><td colspan="4"><strong>Tableaux de bord</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/</code></td>
<td>Connecte</td>
<td>Redirection vers le tableau de bord</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/dashboard</code></td>
<td>Connecte</td>
<td>Tableau de bord (admin ou client selon le role)</td>
</tr>
<tr><td colspan="4"><strong>Profil</strong></td></tr>
<tr>
<td><code>GET</code> <code>POST</code></td>
<td><code>/profile</code></td>
<td>Connecte</td>
<td>Consultation et modification du profil</td>
</tr>
<tr><td colspan="4"><strong>Produits</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/products</code></td>
<td>Admin</td>
<td>Liste des produits (administration)</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/products/add</code></td>
<td>Admin</td>
<td>Ajout d'un produit</td>
</tr>
<tr>
<td><code>GET</code> <code>POST</code></td>
<td><code>/products/edit/&lt;id&gt;</code></td>
<td>Admin</td>
<td>Modification d'un produit</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/products/delete/&lt;id&gt;</code></td>
<td>Admin</td>
<td>Suppression d'un produit</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/products_store</code></td>
<td>Client</td>
<td>Boutique avec filtres et catalogue</td>
</tr>
<tr><td colspan="4"><strong>Clients</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/customers</code></td>
<td>Admin</td>
<td>Liste des clients</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/customers/add</code></td>
<td>Admin</td>
<td>Ajout d'un client</td>
</tr>
<tr>
<td><code>GET</code> <code>POST</code></td>
<td><code>/customers/edit/&lt;id&gt;</code></td>
<td>Admin</td>
<td>Modification d'un client</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/customers/delete/&lt;id&gt;</code></td>
<td>Admin</td>
<td>Suppression d'un client</td>
</tr>
<tr><td colspan="4"><strong>Panier</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/cart</code></td>
<td>Client</td>
<td>Affichage du panier</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/cart/add/&lt;id&gt;</code></td>
<td>Client</td>
<td>Ajout d'un article au panier</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/cart/remove/&lt;id&gt;</code></td>
<td>Client</td>
<td>Retrait d'un article du panier</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/cart/update</code></td>
<td>Client</td>
<td>Mise a jour des quantites</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/cart/checkout</code></td>
<td>Client</td>
<td>Validation et creation de la commande</td>
</tr>
<tr><td colspan="4"><strong>Commandes</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/orders</code></td>
<td>Connecte</td>
<td>Liste des commandes (admin : toutes ; client : les siennes)</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/orders/&lt;id&gt;</code></td>
<td>Connecte</td>
<td>Detail d'une commande</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/orders/&lt;id&gt;/status</code></td>
<td>Admin</td>
<td>Mise a jour du statut</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/orders/&lt;id&gt;/cancel</code></td>
<td>Connecte</td>
<td>Annulation de commande (restauration du stock)</td>
</tr>
<tr><td colspan="4"><strong>Avis</strong></td></tr>
<tr>
<td><code>POST</code></td>
<td><code>/reviews/add/&lt;order_id&gt;</code></td>
<td>Client</td>
<td>Ajout d'un avis sur une commande</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/reviews/edit/&lt;review_id&gt;</code></td>
<td>Client</td>
<td>Modification d'un avis</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/reviews/delete/&lt;review_id&gt;</code></td>
<td>Client</td>
<td>Suppression d'un avis</td>
</tr>
<tr><td colspan="4"><strong>Stock</strong></td></tr>
<tr>
<td><code>GET</code></td>
<td><code>/stock</code></td>
<td>Admin</td>
<td>Vue d'ensemble des stocks</td>
</tr>
<tr>
<td><code>POST</code></td>
<td><code>/stock/update/&lt;id&gt;</code></td>
<td>Admin</td>
<td>Mise a jour des quantites</td>
</tr>
</tbody>
</table>

### API JSON (autocompletion)

Ces endpoints fournissent des donnees JSON pour l'autocompletion des formulaires d'adresse.

<table>
<thead>
<tr>
<th>Methode</th>
<th>Route</th>
<th>Description</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>GET</code></td>
<td><code>/api/cities</code></td>
<td>Liste des villes disponibles</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/states</code></td>
<td>Liste des departements</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/zip_codes</code></td>
<td>Liste des codes postaux</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/geolocation</code></td>
<td>Recherche croisee ville / departement / code postal</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/categories</code></td>
<td>Categories de produits</td>
</tr>
<tr>
<td><code>GET</code></td>
<td><code>/api/platforms</code></td>
<td>Plateformes de jeu</td>
</tr>
</tbody>
</table>

---

## Couche metier

La classe `Magasin` dans `magasin.py` encapsule toute la logique metier et l'acces aux donnees. Elle utilise des **DataFrames Pandas** comme couche intermediaire pour la manipulation des donnees.

### Principaux modules

<details>
<summary><strong>Authentification et utilisateurs</strong></summary>

| Methode | Description |
|---|---|
| `magasin_login(email, password)` | Verification des identifiants avec comparaison bcrypt |
| `check_is_admin(email)` | Verification du role administrateur |
| `register_customer(...)` | Inscription avec generation d'identifiant et validation |
| `add_customer(...)` | Ajout d'un client par l'administrateur |
| `update_profile(customer_id, ...)` | Mise a jour du profil par le client |
| `modify_customer(customer_id, ...)` | Modification d'un client par l'administrateur |
| `del_customer(customer_id)` | Suppression d'un client |

</details>

<details>
<summary><strong>Gestion des produits</strong></summary>

| Methode | Description |
|---|---|
| `add_product(name, category, ...)` | Ajout d'un jeu au catalogue |
| `modify_products(product_id, ...)` | Modification des informations d'un produit |
| `del_product(product_id)` | Suppression d'un produit |
| `filter_products_id(df, product_id)` | Filtrage par identifiant |
| `filter_products_name(df, name)` | Recherche par nom (partielle) |
| `filter_products_price(df, min, max)` | Filtrage par fourchette de prix |
| `filter_products_category(df, category)` | Filtrage par categorie |

</details>

<details>
<summary><strong>Commandes et panier</strong></summary>

| Methode | Description |
|---|---|
| `create_order_from_cart(customer_id, cart)` | Creation d'une commande a partir du panier avec mise a jour du stock |
| `get_all_orders()` | Recuperation de toutes les commandes |
| `get_customer_orders(customer_id)` | Commandes d'un client specifique |
| `get_order_details(order_id)` | Detail complet d'une commande (items, paiements) |
| `update_order_status(order_id, status)` | Changement de statut avec mise a jour des statistiques client |
| `filter_orders(df, status, customer_name)` | Filtrage des commandes |

</details>

<details>
<summary><strong>Stocks</strong></summary>

| Methode | Description |
|---|---|
| `get_stock_view()` | Vue globale des niveaux de stock |
| `update_stock(stock_id, ...)` | Modification des quantites |
| `_restore_stock_for_order(cursor, order_id)` | Restauration du stock lors d'une annulation |

</details>

<details>
<summary><strong>Avis clients</strong></summary>

| Methode | Description |
|---|---|
| `add_review(order_id, score, title, message)` | Creation d'un avis |
| `update_review(review_id, ...)` | Modification d'un avis existant |
| `delete_review(review_id)` | Suppression d'un avis |
| `get_review_for_order(order_id)` | Avis associe a une commande |
| `get_reviews_for_product(product_id)` | Tous les avis d'un produit |
| `get_product_avg_score(product_id)` | Note moyenne d'un produit |
| `get_recent_reviews(limit)` | Derniers avis publies |

</details>

<details>
<summary><strong>Validation des donnees</strong></summary>

| Methode | Description |
|---|---|
| `_check_non_empty_string(value)` | Chaine non vide |
| `_check_positive_number(value)` | Nombre strictement positif |
| `_check_email(value)` | Format email valide |
| `_check_phone_fr(value)` | Telephone au format francais (0X XX XX XX XX) |
| `_check_zip_code_fr(value)` | Code postal francais (5 chiffres) |
| `_check_year(value)` | Annee valide |
| `validate_geolocation(zip, city, state)` | Validation croisee code postal / ville / departement |

</details>

---

## Templates et interface

L'interface utilise **16 templates Jinja2** avec un systeme d'heritage base sur `base.html`. Le design est responsive et s'adapte au role de l'utilisateur (client ou administrateur).

### Hierarchie des templates

```
base.html
├── login.html
├── register.html
├── dashboard.html              (admin)
├── dashboard_client.html       (client)
├── profile.html
├── products.html               (admin)
├── products_store.html         (client)
├── edit_product.html           (admin)
├── customers.html              (admin)
├── edit_customer.html          (admin)
├── cart.html                   (client)
├── orders.html                 (client)
├── orders_admin.html           (admin)
├── order_detail.html
├── stock.html                  (admin)
```

### Charte graphique

<table>
<thead>
<tr>
<th>Element</th>
<th>Couleur</th>
<th>Utilisation</th>
</tr>
</thead>
<tbody>
<tr>
<td><code>#1a1a2e</code></td>
<td>Bleu nuit</td>
<td>En-tete et navigation (mode client)</td>
</tr>
<tr>
<td><code>#6b0f1a</code></td>
<td>Rouge sombre</td>
<td>En-tete et navigation (mode admin)</td>
</tr>
<tr>
<td><code>#f0f2f5</code></td>
<td>Gris clair</td>
<td>Arriere-plan du corps de page</td>
</tr>
<tr>
<td><code>#2a5298</code></td>
<td>Bleu</td>
<td>Boutons et liens principaux</td>
</tr>
</tbody>
</table>

---

## Installation et configuration

### Pre-requis

- **Python** 3.10 ou superieur
- **MySQL** 8.x (serveur local ou distant)
- **pip** (gestionnaire de paquets Python)

### Etape 1 -- Cloner le depot

```bash
git clone https://github.com/AxelBcr/AppDec_VideoGame.git
cd AppDec_VideoGame
```

### Etape 2 -- Installer les dependances

```bash
pip install -r requirements.txt
```

Les dependances installees sont les suivantes :

| Paquet | Version | Role |
|---|---|---|
| `flask` | 3.0+ | Framework web |
| `mysql-connector-python` | 8.0+ | Connecteur MySQL |
| `pandas` | 2.0+ | Manipulation de donnees |
| `werkzeug` | 3.0+ | Utilitaires WSGI et hachage |
| `gunicorn` | 21.2+ | Serveur WSGI de production |

### Etape 3 -- Configurer la base de donnees

Creer un fichier `logs.py` a la racine du projet contenant les identifiants de connexion MySQL :

```python
host = "localhost"
port = 3306
user = "votre_utilisateur"
password = "votre_mot_de_passe"
database = "magasin_jeux_video"
```

> **Note :** Ce fichier est exclu du depot via `.gitignore` pour des raisons de securite.

### Etape 4 -- Initialiser la base de donnees

Importer le schema et les donnees de test :

```bash
mysql -u votre_utilisateur -p magasin_jeux_video < docs/magasin_jeux_video.sql
```

Ce script cree les 9 tables et insere les donnees de demonstration :
- 100 clients
- 60 produits (jeux video)
- 350+ commandes
- Stocks, vendeurs, paiements et avis

### Etape 5 -- Lancer l'application

**En developpement :**

```bash
python app.py
```

L'application est accessible sur `http://localhost:5000`.

**En production :**

```bash
gunicorn app:app --bind 0.0.0.0:8000
```

### Configuration avancee

La configuration de Flask se fait dans `config.py` :

| Parametre | Valeur par defaut | Description |
|---|---|---|
| `SECRET_KEY` | Generee aleatoirement | Cle de chiffrement des sessions |
| `SESSION_COOKIE_HTTPONLY` | `True` | Protection contre les attaques XSS |
| `SESSION_COOKIE_SAMESITE` | `Lax` | Protection contre les attaques CSRF |
| `SESSION_COOKIE_SECURE` | `False` | A passer a `True` en production (HTTPS) |

Pour definir une cle secrete persistante, utiliser la variable d'environnement :

```bash
export FLASK_SECRET_KEY="votre_cle_secrete_ici"
```

---

## Utilisation

### Comptes de demonstration

Les donnees de test incluent des comptes pre-configures. L'administrateur principal est :

| Champ | Valeur |
|---|---|
| Email | *(voir les donnees insérées dans le SQL)* |
| Role | Administrateur (`is_admin = 1`) |

### Parcours client type

<table>
<thead>
<tr>
<th>Etape</th>
<th>Action</th>
<th>Route</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>Creer un compte</td>
<td><code>/register</code></td>
</tr>
<tr>
<td>2</td>
<td>Se connecter</td>
<td><code>/login</code></td>
</tr>
<tr>
<td>3</td>
<td>Parcourir le catalogue</td>
<td><code>/products_store</code></td>
</tr>
<tr>
<td>4</td>
<td>Ajouter des jeux au panier</td>
<td><code>/cart/add/&lt;id&gt;</code></td>
</tr>
<tr>
<td>5</td>
<td>Consulter le panier</td>
<td><code>/cart</code></td>
</tr>
<tr>
<td>6</td>
<td>Valider la commande</td>
<td><code>/cart/checkout</code></td>
</tr>
<tr>
<td>7</td>
<td>Suivre la commande</td>
<td><code>/orders/&lt;id&gt;</code></td>
</tr>
<tr>
<td>8</td>
<td>Laisser un avis</td>
<td><code>/reviews/add/&lt;order_id&gt;</code></td>
</tr>
</tbody>
</table>

### Parcours administrateur type

<table>
<thead>
<tr>
<th>Etape</th>
<th>Action</th>
<th>Route</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>Se connecter (compte admin)</td>
<td><code>/login</code></td>
</tr>
<tr>
<td>2</td>
<td>Consulter le tableau de bord</td>
<td><code>/dashboard</code></td>
</tr>
<tr>
<td>3</td>
<td>Gerer le catalogue</td>
<td><code>/products</code></td>
</tr>
<tr>
<td>4</td>
<td>Gerer les clients</td>
<td><code>/customers</code></td>
</tr>
<tr>
<td>5</td>
<td>Traiter les commandes</td>
<td><code>/orders</code></td>
</tr>
<tr>
<td>6</td>
<td>Surveiller les stocks</td>
<td><code>/stock</code></td>
</tr>
</tbody>
</table>

---

## Securite

<table>
<thead>
<tr>
<th>Mesure</th>
<th>Implementation</th>
</tr>
</thead>
<tbody>
<tr>
<td>Hachage des mots de passe</td>
<td>Werkzeug <code>generate_password_hash</code> / <code>check_password_hash</code> (bcrypt)</td>
</tr>
<tr>
<td>Protection XSS</td>
<td>Cookies HTTPOnly, echappement automatique Jinja2</td>
</tr>
<tr>
<td>Protection CSRF</td>
<td>Cookies SameSite=Lax</td>
</tr>
<tr>
<td>Controle d'acces</td>
<td>Verification du role (admin/client) sur chaque route protegee</td>
</tr>
<tr>
<td>Credentials</td>
<td>Fichier <code>logs.py</code> exclu du depot Git</td>
</tr>
<tr>
<td>Cle secrete</td>
<td>Generee aleatoirement ou via variable d'environnement</td>
</tr>
<tr>
<td>Validation des entrees</td>
<td>Controles sur l'email, le telephone (FR), le code postal (FR), les prix et quantites</td>
</tr>
<tr>
<td>Integrite referentielle</td>
<td>Cles etrangeres avec suppression en cascade sur les commandes</td>
</tr>
</tbody>
</table>

---

## Documentation complementaire

Les documents suivants sont disponibles dans le repertoire `docs/` :

| Document | Description |
|---|---|
| `magasin_jeux_video.sql` | Schema SQL complet avec donnees de test |
| `README_populate.txt` | Instructions de peuplement de la base |
| `Cahier des charges.pdf` | Cahier des charges du projet |
| `cahier_analyse_specifications.docx` | Analyse et specifications detaillees |
| `diagrammes/UML.jpg` | Diagramme de classes UML |
| `diagrammes/Activité_Ajout_Produits.png` | Diagramme d'activite (ajout de produits) |
| `diagrammes/LoopingImage.jpg` | Modele relationnel (Looping) |
| `diagrammes/UML_magasin.txt` | Schema UML en format texte |

---

<div align="center">

**Magasin de Jeux Video** -- Application e-commerce Flask / MySQL / Pandas

</div>
