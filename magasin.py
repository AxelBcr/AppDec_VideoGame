"""
Magasin – couche métier / accès données.
Gère les produits, clients, commandes, stocks via MySQL.
"""

import re

import logs
import pandas as pd
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Patterns compilés pour les validations de format français
_PHONE_FR_RE = re.compile(r"0[1-9]\d{8}")
_ZIP_CODE_FR_RE = re.compile(r"\d{5}")


class Magasin:
    """Interface avec la base de données du magasin de jeux vidéo."""

    # ------------------------------------------------------------------ #
    #  Initialisation / Connexion
    # ------------------------------------------------------------------ #

    def __init__(self, host=logs.host, user=logs.user, port=logs.port,
                 password=logs.password, database=logs.database):

        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.database_name = database

        # Utilisateur connecté (email)
        self.log_id = None

        # Connexion MySQL
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                port=self.port,
                password=self.password,
                database=self.database_name
            )
            print("Connexion à la base réussie.")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Erreur : identifiants incorrects.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Erreur : base de données inexistante.")
            else:
                print(f"Erreur MySQL : {err}")
            raise

        # Chargement des tables en DataFrames
        self._reload_all()

    def _reload_all(self):
        """Recharge toutes les tables depuis MySQL."""
        self.orders = pd.read_sql("SELECT * FROM orders", self.connection)
        self.order_payments = pd.read_sql("SELECT * FROM order_payments", self.connection)
        self.order_reviews = pd.read_sql("SELECT * FROM order_reviews", self.connection)
        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)
        self.products = pd.read_sql("SELECT * FROM products", self.connection)
        self.sellers = pd.read_sql("SELECT * FROM sellers", self.connection)
        self.order_items = pd.read_sql("SELECT * FROM order_items", self.connection)
        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)
        self.geolocation = pd.read_sql("SELECT * FROM geolocation", self.connection)

    def _ensure_connection(self):
        """Reconnecte si la connexion MySQL a été perdue."""
        if not self.connection.is_connected():
            self.connection.reconnect(attempts=3, delay=2)

    def close_connection(self):
        """Ferme proprement la connexion."""
        if self.connection.is_connected():
            self.connection.close()
            print("Connexion fermée.")

    # ------------------------------------------------------------------ #
    #  Validation des entrées
    # ------------------------------------------------------------------ #

    @staticmethod
    def _check_non_empty_string(value, field_name):
        """Vérifie qu'une valeur est une chaîne non vide."""
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"{field_name} ne doit pas être vide.")
        return value.strip()

    @staticmethod
    def _check_positive_number(value, field_name):
        """Vérifie qu'une valeur est un nombre strictement positif."""
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} doit être un nombre.")
        if v <= 0:
            raise ValueError(f"{field_name} doit être strictement positif.")
        return v

    @staticmethod
    def _check_non_negative_int(value, field_name):
        """Vérifie qu'une valeur est un entier >= 0."""
        try:
            v = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} doit être un entier.")
        if v < 0:
            raise ValueError(f"{field_name} ne peut pas être négatif.")
        return v

    @staticmethod
    def _check_year(value, field_name):
        """Vérifie qu'une valeur est une année valide."""
        try:
            year = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} doit être un entier (année).")
        current_year = datetime.now().year
        if year < 1970 or year > current_year + 2:
            raise ValueError(f"{field_name} doit être entre 1970 et {current_year + 2}.")
        return year

    @staticmethod
    def _check_email(value, field_name="E-mail"):
        """Validation basique d'email."""
        value = value.strip()
        if "@" not in value or "." not in value.split("@")[-1]:
            raise ValueError(f"{field_name} invalide.")
        if len(value) > 254:
            raise ValueError(f"{field_name} trop long.")
        return value

    @staticmethod
    def _check_phone_fr(value, field_name="Téléphone"):
        """Vérifie le format français : exactement 10 chiffres commençant par 0."""
        value = value.strip()
        if not value:
            return value
        digits = re.sub(r"[\s.\-]", "", value)
        if not _PHONE_FR_RE.fullmatch(digits):
            raise ValueError(
                f"{field_name} doit contenir 10 chiffres "
                f"et commencer par 0 (format français)."
            )
        return digits

    @staticmethod
    def _check_zip_code_fr(value, field_name="Code postal"):
        """Vérifie le format français : exactement 5 chiffres."""
        value = str(value).strip()
        if not _ZIP_CODE_FR_RE.fullmatch(value):
            raise ValueError(
                f"{field_name} doit contenir exactement 5 chiffres "
                f"(format français)."
            )
        return value

    # ------------------------------------------------------------------ #
    #  Données d'autocomplétion
    # ------------------------------------------------------------------ #

    def get_unique_cities(self):
        """Retourne la liste des villes uniques depuis la géolocalisation."""
        if self.geolocation.empty:
            return []
        return sorted(
            self.geolocation["city"]
            .dropna().unique().tolist()
        )

    def get_unique_states(self):
        """Retourne la liste des régions/états uniques."""
        if self.geolocation.empty:
            return []
        return sorted(
            self.geolocation["state"]
            .dropna().unique().tolist()
        )

    def get_unique_zip_codes(self):
        """Retourne la liste des codes postaux uniques depuis la géolocalisation."""
        if self.geolocation.empty:
            return []
        return sorted(
            self.geolocation["zip_code_prefix"]
            .dropna().unique().astype(str).tolist()
        )

    def get_geolocation_entries(self, query=""):
        """
        Retourne les entrées de géolocalisation correspondant à la requête.
        Cherche dans zip_code_prefix, city et state.
        Retourne une liste de dicts {zip_code_prefix, city, state}.
        """
        if self.geolocation.empty:
            return []
        df = self.geolocation.copy()
        if query:
            q = query.lower()
            mask = (
                df["zip_code_prefix"].astype(str).str.contains(q, case=False, na=False)
                | df["city"].str.contains(q, case=False, na=False)
                | df["state"].str.contains(q, case=False, na=False)
            )
            df = df[mask]
        result = df[["zip_code_prefix", "city", "state"]].drop_duplicates()
        records = result.head(50).to_dict(orient="records")
        return [
            {
                "zip_code_prefix": str(r["zip_code_prefix"]),
                "city": r["city"],
                "state": r["state"],
            }
            for r in records
        ]

    def validate_geolocation(self, zip_code_prefix=None, city=None, state=None):
        """
        Vérifie que les valeurs de ville, région et code postal existent
        dans la table geolocation. Lève ValueError si non trouvé.
        """
        if self.geolocation.empty:
            return

        if zip_code_prefix is not None:
            zcp = str(zip_code_prefix).strip()
            if zcp:
                try:
                    zcp_int = int(zcp)
                except (ValueError, TypeError):
                    raise ValueError(
                        f"Le code postal « {zcp} » n'est pas un nombre valide."
                    )
                if zcp_int not in self.geolocation["zip_code_prefix"].values:
                    raise ValueError(
                        f"Le code postal « {zcp} » n'existe pas dans la base de géolocalisation."
                    )

        if city is not None:
            city_val = city.strip()
            if city_val:
                cities = self.geolocation["city"].str.lower().values
                if city_val.lower() not in cities:
                    raise ValueError(
                        f"La ville « {city_val} » n'existe pas dans la base de géolocalisation."
                    )

        if state is not None:
            state_val = state.strip()
            if state_val:
                states = self.geolocation["state"].str.lower().values
                if state_val.lower() not in states:
                    raise ValueError(
                        f"La région « {state_val} » n'existe pas dans la base de géolocalisation."
                    )

    def get_unique_categories(self):
        """Retourne la liste des catégories de produits uniques."""
        if self.products.empty:
            return []
        return sorted(
            self.products["product_category"]
            .dropna().unique().tolist()
        )

    def get_unique_platforms(self):
        """Retourne la liste des plateformes uniques."""
        if self.products.empty:
            return []
        return sorted(
            self.products["product_platform"]
            .dropna().unique().tolist()
        )

    # ------------------------------------------------------------------ #
    #  Génération d'IDs robuste (basée sur MAX existant, pas sur count)
    # ------------------------------------------------------------------ #

    def _next_id(self, df, column, prefix, width=5):
        """
        Génère le prochain ID unique pour une table.
        Ex : prefix='PROD_', width=5 → PROD_00042
        """
        if df.empty:
            return f"{prefix}{1:0{width}d}"

        nums = (
            df[column]
            .str.extract(rf"{prefix}(\d+)", expand=False)
            .dropna()
            .astype(int)
        )
        if nums.empty:
            return f"{prefix}{1:0{width}d}"
        return f"{prefix}{int(nums.max()) + 1:0{width}d}"

    # ------------------------------------------------------------------ #
    #  Authentification
    # ------------------------------------------------------------------ #

    def magasin_login(self, email, password):
        """
        Authentifie un utilisateur par email + mot de passe.
        Supporte le plain text (legacy) ET les hash werkzeug.
        Retourne True si OK, False sinon.
        """
        row = self.customers[self.customers["email"] == email]
        if row.empty:
            return False

        stored_pwd = str(row.iloc[0]["password_hash"])

        # Support hash werkzeug (commence par 'scrypt:' ou 'pbkdf2:')
        if stored_pwd.startswith(("scrypt:", "pbkdf2:")):
            ok = check_password_hash(stored_pwd, password)
        else:
            # Legacy : comparaison plain text
            ok = (password == stored_pwd)

        if ok:
            self.log_id = email
            return True
        return False

    def check_is_admin(self, email):
        """Vérifie si un utilisateur est administrateur."""
        if not email:
            return False
        row = self.customers[self.customers["email"] == email]
        if row.empty:
            return False
        return int(row.iloc[0]["is_admin"]) == 1

    # ------------------------------------------------------------------ #
    #  CRUD Produits
    # ------------------------------------------------------------------ #

    def add_product(self, product_name, product_category, product_platform,
                    product_esrb_rating, product_release_year,
                    product_price, product_weight_g, product_description):
        """Ajoute un produit au catalogue et crée une ligne de stock par défaut."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        # Validations
        product_name = self._check_non_empty_string(product_name, "Nom du produit")
        product_category = self._check_non_empty_string(product_category, "Catégorie")
        product_platform = self._check_non_empty_string(product_platform, "Plateforme")
        product_esrb_rating = self._check_non_empty_string(
            product_esrb_rating, "Classification ESRB"
        )
        product_release_year = self._check_year(product_release_year, "Année de sortie")
        product_price = self._check_positive_number(product_price, "Prix")
        product_weight_g = self._check_positive_number(product_weight_g, "Poids (g)")

        product_image_url = f"../static/images/{product_name}.png"
        product_id = self._next_id(self.products, "product_id", "PROD_")

        self._ensure_connection()
        cursor = self.connection.cursor()

        product_query = """
            INSERT INTO products
            (product_id, product_name, product_category, product_platform,
             product_esrb_rating, product_release_year, product_price,
             product_weight_g, product_description, product_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        # Stock par défaut
        default_seller_id = "SELLER_0001"
        stock_id = self._next_id(self.stock, "stock_id", "STOCK_")

        stock_query = """
            INSERT INTO stock
            (stock_id, seller_id, product_id,
             quantity_in_stock, quantity_reserved, quantity_available,
             min_stock_level, reorder_point, last_updated,
             warehouse_location, stock_condition)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s, %s)
        """

        try:
            cursor.execute(product_query, (
                product_id, product_name, product_category,
                product_platform, product_esrb_rating,
                int(product_release_year), float(product_price),
                int(product_weight_g), product_description or "", product_image_url
            ))
            cursor.execute(stock_query, (
                stock_id, default_seller_id, product_id,
                10, 0, 10, 3, 5, "A-00-00", "new"
            ))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)
        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)

    def del_product(self, product_id):
        """Supprime un produit et son stock associé."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        self._check_non_empty_string(product_id, "product_id")

        if product_id not in set(self.products["product_id"]):
            raise ValueError("Produit introuvable.")

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "SELECT 1 FROM order_items WHERE product_id = %s LIMIT 1",
                (product_id,)
            )
            if cursor.fetchone():
                raise ValueError(
                    "Impossible de supprimer ce produit : il est lié à des commandes."
                )
            cursor.execute("DELETE FROM stock WHERE product_id = %s", (product_id,))
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)
        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)

    def modify_products(self, product_id, new_product_name=None,
                        new_product_category=None, new_product_platform=None,
                        new_product_esrb_rating=None, new_product_release_year=None,
                        new_product_price=None, new_product_weight_g=None,
                        new_product_description=None):
        """Modifie un produit ; seuls les champs non None sont mis à jour."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        self._check_non_empty_string(product_id, "product_id")
        if product_id not in set(self.products["product_id"]):
            raise ValueError("Produit introuvable.")

        fields = []
        values = []

        if new_product_name is not None:
            name = self._check_non_empty_string(new_product_name, "Nom du produit")
            fields.append("product_name = %s")
            values.append(name)

        if new_product_category is not None:
            cat = self._check_non_empty_string(new_product_category, "Catégorie")
            fields.append("product_category = %s")
            values.append(cat)

        if new_product_platform is not None:
            plat = self._check_non_empty_string(new_product_platform, "Plateforme")
            fields.append("product_platform = %s")
            values.append(plat)

        if new_product_esrb_rating is not None:
            esrb = self._check_non_empty_string(new_product_esrb_rating, "ESRB")
            fields.append("product_esrb_rating = %s")
            values.append(esrb)

        if new_product_release_year is not None:
            year = self._check_year(new_product_release_year, "Année de sortie")
            fields.append("product_release_year = %s")
            values.append(int(year))

        if new_product_price is not None:
            price = self._check_positive_number(new_product_price, "Prix")
            fields.append("product_price = %s")
            values.append(float(price))

        if new_product_weight_g is not None:
            weight = self._check_positive_number(new_product_weight_g, "Poids (g)")
            fields.append("product_weight_g = %s")
            values.append(int(weight))

        if new_product_description is not None:
            fields.append("product_description = %s")
            values.append(new_product_description)

        if not fields:
            return  # Rien à modifier

        values.append(product_id)

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = f"UPDATE products SET {', '.join(fields)} WHERE product_id = %s"

        try:
            cursor.execute(query, tuple(values))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)

    # ------------------------------------------------------------------ #
    #  Filtres Produits
    # ------------------------------------------------------------------ #

    def filter_products_id(self, df, product_id):
        return df[df["product_id"] == product_id]

    def filter_products_name(self, df, product_name):
        if not isinstance(product_name, str) or product_name.strip() == "":
            return df
        return df[df["product_name"].str.contains(product_name.strip(), case=False, na=False)]

    def filter_products_price(self, df, min_price=None, max_price=None):
        if min_price is not None:
            s = str(min_price).strip()
            if s:
                try:
                    df = df[df["product_price"] >= float(s)]
                except ValueError:
                    pass
        if max_price is not None:
            s = str(max_price).strip()
            if s:
                try:
                    df = df[df["product_price"] <= float(s)]
                except ValueError:
                    pass
        return df

    def filter_products_category(self, df, product_category):
        if not isinstance(product_category, str) or product_category.strip() == "":
            return df
        return df[
            df["product_category"]
            .str.contains(product_category.strip(), case=False, na=False)
        ]

    # ------------------------------------------------------------------ #
    #  CRUD Clients
    # ------------------------------------------------------------------ #

    def add_customer(self, first_name, last_name, email, password,
                     phone, zip_code_prefix, city, state,
                     address_line1=None, address_line2=None, is_admin=0):
        """Ajoute un client avec mot de passe hashé."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        first_name = self._check_non_empty_string(first_name, "Prénom")
        last_name = self._check_non_empty_string(last_name, "Nom")
        email = self._check_email(email)
        self._check_non_empty_string(password, "Mot de passe")
        phone = self._check_phone_fr(phone, "Téléphone")
        zip_code_prefix = self._check_zip_code_fr(zip_code_prefix, "Code postal")

        # Validation géolocalisation
        self.validate_geolocation(
            zip_code_prefix=zip_code_prefix, city=city, state=state
        )

        if email in set(self.customers["email"]):
            raise ValueError("Un client avec cet e-mail existe déjà.")

        # Hash du mot de passe
        hashed_pwd = generate_password_hash(password)

        customer_id = self._next_id(self.customers, "customer_id", "CUST_", width=6)

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = """
            INSERT INTO customers
            (customer_id, first_name, last_name, email, password_hash,
             phone, zip_code_prefix, city, state,
             address_line1, address_line2, is_admin,
             registration_date, last_purchase_date,
             total_orders, total_spent)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, %s,
                    NOW(), NULL, 0, 0.00)
        """

        try:
            cursor.execute(query, (
                customer_id, first_name, last_name, email, hashed_pwd,
                phone or "", int(zip_code_prefix), city, state,
                address_line1 or "", address_line2 or "", int(is_admin)
            ))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def register_customer(self, first_name, last_name, email, password,
                          phone, zip_code_prefix, city, state,
                          address_line1=None, address_line2=None):
        """Inscription d'un nouveau client (sans droits admin requis)."""

        first_name = self._check_non_empty_string(first_name, "Prénom")
        last_name = self._check_non_empty_string(last_name, "Nom")
        email = self._check_email(email)
        self._check_non_empty_string(password, "Mot de passe")
        if len(password.strip()) < 4:
            raise ValueError("Le mot de passe doit contenir au moins 4 caractères.")
        phone = self._check_phone_fr(phone, "Téléphone")
        zip_code_prefix = self._check_zip_code_fr(zip_code_prefix, "Code postal")

        # Validation géolocalisation
        self.validate_geolocation(
            zip_code_prefix=zip_code_prefix, city=city, state=state
        )

        if email in set(self.customers["email"]):
            raise ValueError("Un compte avec cet e-mail existe déjà.")

        hashed_pwd = generate_password_hash(password)
        customer_id = self._next_id(self.customers, "customer_id", "CUST_", width=6)

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = """
            INSERT INTO customers
            (customer_id, first_name, last_name, email, password_hash,
             phone, zip_code_prefix, city, state,
             address_line1, address_line2, is_admin,
             registration_date, last_purchase_date,
             total_orders, total_spent)
            VALUES (%s, %s, %s, %s, %s,
                    %s, %s, %s, %s,
                    %s, %s, 0,
                    NOW(), NULL, 0, 0.00)
        """

        try:
            cursor.execute(query, (
                customer_id, first_name, last_name, email, hashed_pwd,
                phone or "", int(zip_code_prefix), city, state,
                address_line1 or "", address_line2 or ""
            ))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def update_profile(self, customer_id, first_name=None, last_name=None,
                       password=None, phone=None,
                       zip_code_prefix=None, city=None, state=None,
                       address_line1=None, address_line2=None):
        """Permet à un utilisateur de modifier son propre profil."""

        self._check_non_empty_string(customer_id, "customer_id")
        if customer_id not in set(self.customers["customer_id"]):
            raise ValueError("Client introuvable.")

        fields = []
        values = []

        if first_name is not None:
            first_name = self._check_non_empty_string(first_name, "Prénom")
            fields.append("first_name = %s")
            values.append(first_name)

        if last_name is not None:
            last_name = self._check_non_empty_string(last_name, "Nom")
            fields.append("last_name = %s")
            values.append(last_name)

        if password is not None:
            self._check_non_empty_string(password, "Mot de passe")
            if len(password.strip()) < 4:
                raise ValueError(
                    "Le mot de passe doit contenir au moins 4 caractères."
                )
            fields.append("password_hash = %s")
            values.append(generate_password_hash(password))

        if phone is not None:
            phone = self._check_phone_fr(phone, "Téléphone")
            fields.append("phone = %s")
            values.append(phone)

        if zip_code_prefix is not None:
            zip_code_prefix = self._check_zip_code_fr(
                zip_code_prefix, "Code postal"
            )
            fields.append("zip_code_prefix = %s")
            values.append(int(zip_code_prefix))

        if city is not None:
            fields.append("city = %s")
            values.append(city)

        if state is not None:
            fields.append("state = %s")
            values.append(state)

        # Validation géolocalisation pour les champs modifiés
        self.validate_geolocation(
            zip_code_prefix=zip_code_prefix,
            city=city,
            state=state,
        )

        if address_line1 is not None:
            fields.append("address_line1 = %s")
            values.append(address_line1)

        if address_line2 is not None:
            fields.append("address_line2 = %s")
            values.append(address_line2)

        if not fields:
            return

        values.append(customer_id)

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = f"UPDATE customers SET {', '.join(fields)} WHERE customer_id = %s"

        try:
            cursor.execute(query, tuple(values))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def modify_customer(self, customer_id, first_name=None, last_name=None,
                        email=None, password=None, phone=None,
                        zip_code_prefix=None, city=None, state=None,
                        address_line1=None, address_line2=None, is_admin=None):
        """Modifie un client ; seuls les champs non None sont mis à jour."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        self._check_non_empty_string(customer_id, "customer_id")
        if customer_id not in set(self.customers["customer_id"]):
            raise ValueError("Client introuvable.")

        fields = []
        values = []

        if first_name is not None:
            first_name = self._check_non_empty_string(first_name, "Prénom")
            fields.append("first_name = %s")
            values.append(first_name)

        if last_name is not None:
            last_name = self._check_non_empty_string(last_name, "Nom")
            fields.append("last_name = %s")
            values.append(last_name)

        if email is not None:
            email = self._check_email(email)
            fields.append("email = %s")
            values.append(email)

        if password is not None:
            self._check_non_empty_string(password, "Mot de passe")
            fields.append("password_hash = %s")
            values.append(generate_password_hash(password))

        if phone is not None:
            phone = self._check_phone_fr(phone, "Téléphone")
            fields.append("phone = %s")
            values.append(phone)

        if zip_code_prefix is not None:
            zip_code_prefix = self._check_zip_code_fr(
                zip_code_prefix, "Code postal"
            )
            fields.append("zip_code_prefix = %s")
            values.append(int(zip_code_prefix))

        if city is not None:
            fields.append("city = %s")
            values.append(city)

        if state is not None:
            fields.append("state = %s")
            values.append(state)

        # Validation géolocalisation pour les champs modifiés
        self.validate_geolocation(
            zip_code_prefix=zip_code_prefix,
            city=city,
            state=state,
        )

        if address_line1 is not None:
            fields.append("address_line1 = %s")
            values.append(address_line1)

        if address_line2 is not None:
            fields.append("address_line2 = %s")
            values.append(address_line2)

        if is_admin is not None:
            fields.append("is_admin = %s")
            values.append(int(is_admin))

        if not fields:
            return

        values.append(customer_id)

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = f"UPDATE customers SET {', '.join(fields)} WHERE customer_id = %s"

        try:
            cursor.execute(query, tuple(values))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def reset_password_by_email(self, email, new_password):
        """Réinitialise le mot de passe d'un client via son e-mail."""
        email = self._check_email(email)
        self._check_non_empty_string(new_password, "Mot de passe")

        row = self.customers[self.customers["email"] == email]
        if row.empty:
            return False

        self._ensure_connection()
        cursor = self.connection.cursor()
        query = "UPDATE customers SET password_hash = %s WHERE email = %s"

        try:
            cursor.execute(query, (generate_password_hash(new_password), email))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)
        return True

    def del_customer(self, customer_id):
        """Supprime un client."""

        if not self.check_is_admin(self.log_id):
            raise ValueError("Action réservée aux administrateurs.")

        self._check_non_empty_string(customer_id, "customer_id")
        if customer_id not in set(self.customers["customer_id"]):
            raise ValueError("Client introuvable.")

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute("DELETE FROM orders WHERE customer_id = %s", (customer_id,))
            cursor.execute("DELETE FROM customers WHERE customer_id = %s", (customer_id,))
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)
        self.orders = pd.read_sql("SELECT * FROM orders", self.connection)
        self.order_items = pd.read_sql("SELECT * FROM order_items", self.connection)
        self.order_payments = pd.read_sql("SELECT * FROM order_payments", self.connection)
        self.order_reviews = pd.read_sql("SELECT * FROM order_reviews", self.connection)

    # ------------------------------------------------------------------ #
    #  Filtres Clients
    # ------------------------------------------------------------------ #

    def filter_customer_name(self, df, name):
        if not isinstance(name, str) or name.strip() == "":
            return df
        pattern = name.strip()
        mask = (
            df["first_name"].str.contains(pattern, case=False, na=False)
            | df["last_name"].str.contains(pattern, case=False, na=False)
        )
        return df[mask]

    def filter_customer_email(self, df, email):
        if not isinstance(email, str) or email.strip() == "":
            return df
        return df[df["email"].str.contains(email.strip(), case=False, na=False)]

    def filter_customer_city(self, df, city):
        if not isinstance(city, str) or city.strip() == "":
            return df
        return df[df["city"].str.contains(city.strip(), case=False, na=False)]

    # ------------------------------------------------------------------ #
    #  Mise à jour dynamique des stats client
    # ------------------------------------------------------------------ #

    def _refresh_customer_stats(self, customer_id):
        """
        Recalcule total_orders, total_spent, last_purchase_date et
        customer_segment à partir des commandes réelles, puis met à jour
        la base et le DataFrame en mémoire.
        """
        self._ensure_connection()
        cursor = self.connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT
                    COUNT(DISTINCT o.order_id) AS total_orders,
                    COALESCE(SUM(oi.price * oi.quantity + oi.freight_value), 0)
                        AS total_spent,
                    MAX(o.order_purchase_timestamp) AS last_purchase_date
                FROM orders o
                JOIN order_items oi ON oi.order_id = o.order_id
                WHERE o.customer_id = %s
                  AND o.order_status <> 'cancelled'
                """,
                (customer_id,)
            )
            row = cursor.fetchone()
            total_orders = int(row["total_orders"]) if row["total_orders"] else 0
            total_spent = float(row["total_spent"]) if row["total_spent"] else 0.0
            last_purchase = row["last_purchase_date"]

            # Déterminer le segment en fonction du total dépensé
            if total_orders == 0:
                segment = "nouveau"
            elif total_spent < 200:
                segment = "casual"
            elif total_spent < 1000:
                segment = "regular"
            elif total_spent < 2000:
                segment = "premium"
            else:
                segment = "vip"

            cursor.execute(
                """
                UPDATE customers
                SET total_orders      = %s,
                    total_spent       = %s,
                    last_purchase_date = %s,
                    customer_segment  = %s
                WHERE customer_id = %s
                """,
                (total_orders, round(total_spent, 2),
                 last_purchase, segment, customer_id)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL (refresh stats) : {err}")
        finally:
            cursor.close()

        # Rafraîchir le DataFrame
        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    # ------------------------------------------------------------------ #
    #  Commandes – Création depuis panier
    # ------------------------------------------------------------------ #

    def create_order_from_cart(self, customer_id, cart):
        """
        Crée une commande à partir d'un panier {product_id: quantity}.
        Vérifie le stock, décrémente, insère order + order_items.
        Retourne order_id ou raise ValueError.
        """
        if not cart:
            raise ValueError("Panier vide.")

        # Vérification du stock
        stock_df = self.stock.groupby("product_id")["quantity_available"].sum().reset_index()
        stock_map = dict(zip(stock_df["product_id"], stock_df["quantity_available"]))

        for product_id, qty in cart.items():
            available = int(stock_map.get(product_id, 0))
            if available < qty:
                prod_row = self.products[self.products["product_id"] == product_id]
                name = prod_row.iloc[0]["product_name"] if not prod_row.empty else product_id
                raise ValueError(
                    f"Stock insuffisant pour « {name} » "
                    f"(disponible : {available}, demandé : {qty})."
                )

        order_id = self._next_id(self.orders, "order_id", "ORDER_", width=6)

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO orders
                   (order_id, customer_id, order_status,
                    order_purchase_timestamp, order_approved_at,
                    order_delivered_carrier_date, order_delivered_customer_date)
                   VALUES (%s, %s, %s, NOW(), NULL, NULL, NULL)""",
                (order_id, customer_id, "created")
            )

            item_num = 1
            today_limit = datetime.now().strftime("%Y-%m-%d 23:59:59")

            for product_id, qty in cart.items():
                prod_row = self.products[self.products["product_id"] == product_id]
                if prod_row.empty:
                    continue
                price = float(prod_row.iloc[0]["product_price"])

                prod_stock = (
                    self.stock[self.stock["product_id"] == product_id]
                    .copy()
                    .sort_values("quantity_available", ascending=False)
                )

                remaining = int(qty)
                for _, srow in prod_stock.iterrows():
                    if remaining <= 0:
                        break
                    available = int(srow["quantity_available"])
                    if available <= 0:
                        continue

                    use_qty = min(available, remaining)
                    cursor.execute(
                        """INSERT INTO order_items
                           (order_id, order_item_id, product_id, seller_id,
                            shipping_limit_date, price, freight_value, quantity)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                        (order_id, item_num, product_id, srow["seller_id"],
                         today_limit, price, 4.99, use_qty)
                    )
                    item_num += 1

                    cursor.execute(
                        """UPDATE stock
                           SET quantity_available = %s, last_updated = NOW()
                           WHERE stock_id = %s""",
                        (available - use_qty, srow["stock_id"])
                    )
                    remaining -= use_qty

                if remaining > 0:
                    raise ValueError(f"Stock incohérent pour le produit {product_id}.")

            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        except ValueError:
            self.connection.rollback()
            raise
        finally:
            cursor.close()

        self.orders = pd.read_sql("SELECT * FROM orders", self.connection)
        self.order_items = pd.read_sql("SELECT * FROM order_items", self.connection)
        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)

        # Mettre à jour total_orders, total_spent, customer_segment
        self._refresh_customer_stats(customer_id)

        return order_id

    # ------------------------------------------------------------------ #
    #  Commandes – Gestion admin
    # ------------------------------------------------------------------ #

    def get_all_orders(self):
        """
        Retourne toutes les commandes avec le total et infos client.
        """
        df_orders = self.orders.copy()
        df_items = self.order_items.copy()

        df_items["quantity"] = df_items["quantity"].fillna(1)
        df_items["price"] = df_items["price"].fillna(0)
        df_items["freight_value"] = df_items["freight_value"].fillna(0)
        df_items["line_total"] = (
            df_items["price"] * df_items["quantity"]
            + df_items["freight_value"]
        )

        totals = df_items.groupby("order_id")["line_total"].sum().reset_index(name="total_price")

        df_orders = df_orders.merge(totals, on="order_id", how="left")
        df_orders["total_price"] = df_orders["total_price"].fillna(0)

        # Joindre info client
        df_orders = df_orders.merge(
            self.customers[["customer_id", "first_name", "last_name", "email"]],
            on="customer_id", how="left"
        )

        return df_orders.sort_values("order_purchase_timestamp", ascending=False)

    def get_customer_orders(self, customer_id):
        """Retourne les commandes d'un client spécifique avec totaux."""
        df_orders = self.orders[self.orders["customer_id"] == customer_id].copy()
        df_items = self.order_items.copy()

        df_items["quantity"] = df_items["quantity"].fillna(1)
        df_items["price"] = df_items["price"].fillna(0)
        df_items["freight_value"] = df_items["freight_value"].fillna(0)
        df_items["line_total"] = (
            df_items["price"] * df_items["quantity"]
            + df_items["freight_value"]
        )

        totals = df_items.groupby("order_id")["line_total"].sum().reset_index(name="total_price")
        df_orders = df_orders.merge(totals, on="order_id", how="left")
        df_orders["total_price"] = df_orders["total_price"].fillna(0)

        return df_orders.sort_values("order_purchase_timestamp", ascending=False)

    def get_order_details(self, order_id):
        """Retourne les lignes d'une commande avec noms de produits."""
        df = self.order_items[self.order_items["order_id"] == order_id].copy()
        df = df.merge(
            self.products[["product_id", "product_name", "product_platform", "product_image"]],
            on="product_id", how="left"
        )
        df["quantity"] = df["quantity"].fillna(1)
        df["price"] = df["price"].fillna(0)
        df["freight_value"] = df["freight_value"].fillna(0)
        df["line_total"] = df["price"] * df["quantity"] + df["freight_value"]
        return df

    def update_order_status(self, order_id, new_status):
        """
        Met à jour le statut d'une commande.
        Statuts autorisés : created, approved, shipped, delivered, cancelled.
        """
        allowed = {"created", "approved", "shipped", "delivered", "cancelled"}
        if new_status not in allowed:
            raise ValueError(f"Statut invalide. Valeurs possibles : {', '.join(sorted(allowed))}")

        if order_id not in set(self.orders["order_id"]):
            raise ValueError("Commande introuvable.")

        self._ensure_connection()
        cursor = self.connection.cursor()

        # Mettre à jour les champs de date selon le statut
        extra_fields = ""
        extra_values = []

        if new_status == "approved":
            extra_fields = ", order_approved_at = NOW()"
        elif new_status == "shipped":
            extra_fields = ", order_delivered_carrier_date = NOW()"
        elif new_status == "delivered":
            extra_fields = ", order_delivered_customer_date = NOW()"
        elif new_status == "cancelled":
            # Restaurer le stock
            self._restore_stock_for_order(cursor, order_id)

        try:
            cursor.execute(
                f"UPDATE orders SET order_status = %s{extra_fields} WHERE order_id = %s",
                (new_status, order_id)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.orders = pd.read_sql("SELECT * FROM orders", self.connection)
        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)

        # Recalculer les stats du client (utile si commande annulée)
        order_row = self.orders[self.orders["order_id"] == order_id]
        if not order_row.empty:
            cid = order_row.iloc[0]["customer_id"]
            self._refresh_customer_stats(cid)

    def _restore_stock_for_order(self, cursor, order_id):
        """Restaure le stock quand une commande est annulée."""
        items = self.order_items[self.order_items["order_id"] == order_id]
        for _, item in items.iterrows():
            pid = item["product_id"]
            sid = item["seller_id"]
            qty = int(item.get("quantity", 1))

            stock_row = self.stock[
                (self.stock["product_id"] == pid) &
                (self.stock["seller_id"] == sid)
            ]
            if not stock_row.empty:
                stock_id = stock_row.iloc[0]["stock_id"]
                new_avail = int(stock_row.iloc[0]["quantity_available"]) + qty
                cursor.execute(
                    "UPDATE stock SET quantity_available = %s,"
                    " last_updated = NOW() WHERE stock_id = %s",
                    (new_avail, stock_id)
                )

    def filter_orders(self, df, status=None, customer_name=None,
                      min_total=None, max_total=None,
                      date_from=None, date_to=None):
        """Filtre un DataFrame de commandes selon plusieurs critères."""
        if status:
            df = df[df["order_status"] == status]

        if customer_name:
            pattern = customer_name.strip()
            mask = (
                df["first_name"].str.contains(pattern, case=False, na=False)
                | df["last_name"].str.contains(pattern, case=False, na=False)
            )
            df = df[mask]

        if min_total is not None:
            try:
                df = df[df["total_price"] >= float(min_total)]
            except (ValueError, TypeError):
                pass

        if max_total is not None:
            try:
                df = df[df["total_price"] <= float(max_total)]
            except (ValueError, TypeError):
                pass

        if date_from:
            try:
                df = df[df["order_purchase_timestamp"] >= pd.to_datetime(date_from)]
            except (ValueError, TypeError):
                pass

        if date_to:
            try:
                df = df[df["order_purchase_timestamp"] <= pd.to_datetime(date_to)]
            except (ValueError, TypeError):
                pass

        return df

    # ------------------------------------------------------------------ #
    #  Stock
    # ------------------------------------------------------------------ #

    def get_stock_view(self):
        """Stock joint avec infos produits."""
        return self.stock.merge(
            self.products[["product_id", "product_name", "product_platform", "product_price"]],
            on="product_id", how="left"
        )

    def update_stock(self, stock_id, quantity_in_stock=None,
                     quantity_reserved=None, min_stock_level=None,
                     reorder_point=None, seller_id=None,
                     warehouse_location=None, stock_condition=None):
        """Met à jour une ligne de stock et recalcule quantity_available."""

        row = self.stock[self.stock["stock_id"] == stock_id]
        if row.empty:
            raise ValueError("Ligne de stock introuvable.")

        current = row.iloc[0]

        q_stock = (
            int(quantity_in_stock)
            if quantity_in_stock is not None
            else int(current["quantity_in_stock"])
        )
        q_reserved = (
            int(quantity_reserved)
            if quantity_reserved is not None
            else int(current["quantity_reserved"])
        )
        min_level = (
            int(min_stock_level)
            if min_stock_level is not None
            else int(current["min_stock_level"])
        )
        reorder_val = (
            int(reorder_point)
            if reorder_point is not None
            else int(current["reorder_point"])
        )
        seller = (
            seller_id.strip()
            if (seller_id and seller_id.strip())
            else current["seller_id"]
        )
        wh_loc = (
            warehouse_location.strip()
            if (warehouse_location and warehouse_location.strip())
            else current["warehouse_location"]
        )
        cond = (
            stock_condition.strip()
            if (stock_condition and stock_condition.strip())
            else current["stock_condition"]
        )

        q_available = q_stock - q_reserved
        if q_available < 0:
            raise ValueError("La quantité disponible ne peut pas être négative (stock < réservé).")

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """UPDATE stock
                   SET quantity_in_stock = %s, quantity_reserved = %s,
                       quantity_available = %s, min_stock_level = %s,
                       reorder_point = %s, seller_id = %s,
                       warehouse_location = %s, stock_condition = %s,
                       last_updated = NOW()
                   WHERE stock_id = %s""",
                (q_stock, q_reserved, q_available, min_level, reorder_val,
                 seller, wh_loc, cond, stock_id)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.stock = pd.read_sql("SELECT * FROM stock", self.connection)

    # ------------------------------------------------------------------ #
    #  Avis clients (order_reviews)
    # ------------------------------------------------------------------ #

    def get_review_for_order(self, order_id):
        """Retourne l'avis associé à une commande (ou None)."""
        df = self.order_reviews[self.order_reviews["order_id"] == order_id]
        if df.empty:
            return None
        return df.iloc[0].to_dict()

    def get_reviews_for_product(self, product_id):
        """
        Retourne les avis liés à un produit via order_items.
        Résultat : liste de dicts avec review_score, title, message, date.
        """
        # Trouver les order_id contenant ce produit
        order_ids = self.order_items.loc[
            self.order_items["product_id"] == product_id, "order_id"
        ].unique()
        df = self.order_reviews[self.order_reviews["order_id"].isin(order_ids)].copy()
        if df.empty:
            return []
        # Joindre les infos client via orders
        df = df.merge(self.orders[["order_id", "customer_id"]], on="order_id", how="left")
        df = df.merge(
            self.customers[["customer_id", "first_name", "last_name"]],
            on="customer_id", how="left"
        )
        df = df.sort_values("review_creation_date", ascending=False)
        return df.to_dict(orient="records")

    def get_product_avg_score(self, product_id):
        """Retourne la note moyenne et le nombre d'avis pour un produit."""
        order_ids = self.order_items.loc[
            self.order_items["product_id"] == product_id, "order_id"
        ].unique()
        df = self.order_reviews[self.order_reviews["order_id"].isin(order_ids)]
        if df.empty:
            return None, 0
        return round(float(df["review_score"].mean()), 1), len(df)

    def get_all_product_ratings(self):
        """
        Retourne un dict {product_id: {avg_score, review_count}} pour tous les produits.
        """
        # Joindre order_items → order_reviews
        merged = self.order_items[["order_id", "product_id"]].merge(
            self.order_reviews[["order_id", "review_score"]],
            on="order_id", how="inner"
        )
        if merged.empty:
            return {}
        grouped = merged.groupby("product_id")["review_score"].agg(["mean", "count"])
        result = {}
        for pid, row in grouped.iterrows():
            result[pid] = {
                "avg_score": round(float(row["mean"]), 1),
                "review_count": int(row["count"]),
            }
        return result

    def get_recent_reviews(self, limit=6):
        """Retourne les N avis les plus récents avec infos produit et client."""
        df = self.order_reviews.copy()
        if df.empty:
            return []
        df = df.sort_values("review_creation_date", ascending=False).head(limit)
        # Joindre order → customer
        df = df.merge(self.orders[["order_id", "customer_id"]], on="order_id", how="left")
        df = df.merge(
            self.customers[["customer_id", "first_name", "last_name"]],
            on="customer_id", how="left"
        )
        # Joindre order_items → product (prendre le premier produit de la commande)
        first_product = self.order_items.drop_duplicates(
            subset=["order_id"]
        )[["order_id", "product_id"]]
        df = df.merge(first_product, on="order_id", how="left")
        df = df.merge(
            self.products[["product_id", "product_name", "product_image"]],
            on="product_id", how="left"
        )
        return df.to_dict(orient="records")

    def add_review(self, order_id, review_score, review_comment_title,
                   review_comment_message):
        """Ajoute un avis pour une commande."""
        # Vérifier que la commande existe
        if order_id not in set(self.orders["order_id"]):
            raise ValueError("Commande introuvable.")

        # Vérifier qu'il n'y a pas déjà un avis
        existing = self.order_reviews[self.order_reviews["order_id"] == order_id]
        if not existing.empty:
            raise ValueError("Un avis existe déjà pour cette commande.")

        # Valider le score
        try:
            score = int(review_score)
        except (TypeError, ValueError):
            raise ValueError("La note doit être un nombre entier.")
        if score < 1 or score > 5:
            raise ValueError("La note doit être entre 1 et 5.")

        review_id = self._next_id(self.order_reviews, "review_id", "REVIEW_", width=6)

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """INSERT INTO order_reviews
                   (review_id, order_id, review_score,
                    review_comment_title, review_comment_message,
                    review_creation_date)
                   VALUES (%s, %s, %s, %s, %s, NOW())""",
                (review_id, order_id, score,
                 review_comment_title.strip() if review_comment_title else None,
                 review_comment_message.strip() if review_comment_message else None)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.order_reviews = pd.read_sql("SELECT * FROM order_reviews", self.connection)
        return review_id

    def update_review(self, review_id, review_score=None,
                      review_comment_title=None, review_comment_message=None):
        """Met à jour un avis existant."""
        row = self.order_reviews[self.order_reviews["review_id"] == review_id]
        if row.empty:
            raise ValueError("Avis introuvable.")

        current = row.iloc[0]
        score = current["review_score"]
        title = current["review_comment_title"]
        message = current["review_comment_message"]

        if review_score is not None:
            try:
                score = int(review_score)
            except (TypeError, ValueError):
                raise ValueError("La note doit être un nombre entier.")
            if score < 1 or score > 5:
                raise ValueError("La note doit être entre 1 et 5.")

        if review_comment_title is not None:
            title = review_comment_title.strip() if review_comment_title else None
        if review_comment_message is not None:
            message = review_comment_message.strip() if review_comment_message else None

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                """UPDATE order_reviews
                   SET review_score = %s, review_comment_title = %s,
                       review_comment_message = %s
                   WHERE review_id = %s""",
                (score, title, message, review_id)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.order_reviews = pd.read_sql("SELECT * FROM order_reviews", self.connection)

    def delete_review(self, review_id):
        """Supprime un avis."""
        row = self.order_reviews[self.order_reviews["review_id"] == review_id]
        if row.empty:
            raise ValueError("Avis introuvable.")

        self._ensure_connection()
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "DELETE FROM order_reviews WHERE review_id = %s",
                (review_id,)
            )
            self.connection.commit()
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise ValueError(f"Erreur MySQL : {err}")
        finally:
            cursor.close()

        self.order_reviews = pd.read_sql("SELECT * FROM order_reviews", self.connection)

    # ------------------------------------------------------------------ #
    #  Vue globale (analytics)
    # ------------------------------------------------------------------ #

    def describe_database(self):
        """Fusionne les tables principales et retourne un describe()."""
        df = self.orders.copy()
        df = df.merge(self.customers, on="customer_id", how="left")
        df = df.merge(self.order_items, on="order_id", how="left")
        df = df.merge(self.products, on="product_id", how="left")
        df = df.merge(self.sellers, on="seller_id", how="left")
        df = df.merge(self.order_payments, on="order_id", how="left")
        df = df.merge(self.order_reviews, on="order_id", how="left")
        df = df.merge(self.stock, on=["product_id", "seller_id"], how="left")
        return df.describe()
