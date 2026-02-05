# %%
from matplotlib.backend_tools import cursors

# Import
import logs

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

import warnings
warnings.filterwarnings("ignore")
# %% [markdown]
# ## Magasin
# 
# Définition d'une classe Magasin qui servira à interagir avec la base de donnée SQL
# %%
class Magasin:
    def __init__(self, host=logs.host, user=logs.user, port=logs.port,
                 password=logs.password, database=logs.database,
                 orders=None, order_payment=None, order_reviews=None,
                 customers=None, products=None, sellers=None,
                 order_items=None, geolocation=None, stock=None):

        self.host = host
        self.user = user
        self.port = port
        self.password = password
        self.database_name = database

        self.log_id = None
        self.log_pwd = None

        # Connexion à la base de données
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

        # Chargement des tables
        self.orders = orders if orders is not None else pd.read_sql(
            "SELECT * FROM orders", self.connection)
        self.order_payments = order_payment if order_payment is not None else pd.read_sql(
            "SELECT * FROM order_payments", self.connection)
        self.order_reviews = order_reviews if order_reviews is not None else pd.read_sql(
            "SELECT * FROM order_reviews", self.connection)
        self.customers = customers if customers is not None else pd.read_sql(
            "SELECT * FROM customers", self.connection)
        self.products = products if products is not None else pd.read_sql(
            "SELECT * FROM products", self.connection)
        self.sellers = sellers if sellers is not None else pd.read_sql(
            "SELECT * FROM sellers", self.connection)
        self.order_items = order_items if order_items is not None else pd.read_sql(
            "SELECT * FROM order_items", self.connection)
        self.stock = stock if stock is not None else pd.read_sql(
            "SELECT * FROM stock", self.connection)
        self.geolocation = geolocation if geolocation is not None else pd.read_sql(
            "SELECT * FROM geolocation", self.connection)

        self.database = None




    #Vue globale

    def describe_database(self):
        """
        Fusionne les principales tables autour des commandes
        et renvoie un describe() numérique.
        """
        df = self.orders.copy()

        df = df.merge(self.customers, on="customer_id", how="left")
        df = df.merge(self.order_items, on="order_id", how="left")
        df = df.merge(self.products, on="product_id", how="left")
        df = df.merge(self.sellers, on="seller_id", how="left")
        df = df.merge(self.order_payments, on="order_id", how="left")
        df = df.merge(self.order_reviews, on="order_id", how="left")
        df = df.merge(self.stock, on=["product_id", "seller_id"], how="left")

        self.database = df
        return df.describe()




    #Validation interne

    @staticmethod
    def _check_non_empty_string(value, field_name):
        if not isinstance(value, str) or value.strip() == "":
            raise ValueError(f"{field_name} ne doit pas être vide.")

    @staticmethod
    def _check_positive_number(value, field_name):
        try:
            v = float(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} doit être un nombre.")
        if v <= 0:
            raise ValueError(f"{field_name} doit être strictement positif.")
        return v

    @staticmethod
    def _check_year(value, field_name):
        try:
            year = int(value)
        except (TypeError, ValueError):
            raise ValueError(f"{field_name} doit être un entier (année).")
        current_year = datetime.now().year
        if year < 1980 or year > current_year + 1:
            raise ValueError(f"{field_name} doit être entre 1980 et {current_year + 1}.")
        return year




    # Log into Magasin

    def magasin_login(self, email, password):
        " Permet de se connecter au magasin en tant qu'utilisateur "

        row = self.customers[self.customers["email"] == email]

        if row.empty:
            return False

        stored_pwd = row.iloc[0]["password_hash"]
        if password == stored_pwd:
            self.log_id = email
            self.log_pwd = password
            return True
        return None

    def check_is_admin(self, email):
        " Check si un utilisateur est un administrateur"

        row = self.customers[self.customers["email"] == email]

        if row.empty:
            return False

        stored_is_admin = row.iloc[0]["is_admin"]
        return  stored_is_admin == 1




    #Opérations produits

    def add_product(self, product_name, product_category, product_platform,
                    product_esrb_rating, product_release_year,
                    product_price, product_weight_g, product_description):
        """Ajoute un produit au catalogue avec tests de base."""

        

        # Validations
        self._check_non_empty_string(product_name, "Nom du produit")
        self._check_non_empty_string(product_category, "Catégorie du produit")
        self._check_non_empty_string(product_platform, "Plateforme")
        self._check_non_empty_string(product_esrb_rating, "Classification ESRB")

        product_release_year = self._check_year(product_release_year, "Année de sortie")
        product_price = self._check_positive_number(product_price, "Prix")
        product_weight_g = self._check_positive_number(product_weight_g, "Poids (g)")

        cursor = self.connection.cursor()
        query = """
            INSERT INTO products
            (product_id, product_name, product_category, product_platform,
             product_esrb_rating, product_release_year, product_price,
             product_weight_g, product_description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        product_id = "PROD_" + "{:05d}".format(self.products.shape[0] + 1)

        try:
            cursor.execute(query, (
                product_id, product_name.strip(), product_category.strip(),
                product_platform.strip(), product_esrb_rating.strip(),
                int(product_release_year), float(product_price),
                int(product_weight_g), product_description
            ))
            self.connection.commit()
            print(f"Produit {product_id} ajouté avec succès.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de l'ajout du produit : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)

    def del_product(self, product_id):
        """Supprime un produit s'il existe."""

        

        self._check_non_empty_string(product_id, "product_id")

        if product_id not in set(self.products["product_id"]):
            print("Aucun produit avec cet identifiant.")
            return

        cursor = self.connection.cursor()
        query = "DELETE FROM products WHERE product_id = %s"
        try:
            cursor.execute(query, (product_id,))
            self.connection.commit()
            print(f"Produit {product_id} supprimé.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de la suppression : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)

    def modify_products(self, product_id, new_product_name=None,
                        new_product_category=None, new_product_platform=None,
                        new_product_esrb_rating=None,
                        new_product_release_year=None,
                        new_product_price=None,
                        new_product_weight_g=None,
                        new_product_description=None):
        """Modifie un produit ; seuls les champs non None sont mis à jour."""

        

        self._check_non_empty_string(product_id, "product_id")

        if product_id not in set(self.products["product_id"]):
            print("Aucun produit avec cet identifiant.")
            return

        # Préparation des champs à mettre à jour
        fields = []
        values = []

        if new_product_name is not None:
            self._check_non_empty_string(new_product_name, "Nom du produit")
            fields.append("product_name = %s")
            values.append(new_product_name.strip())

        if new_product_category is not None:
            self._check_non_empty_string(new_product_category, "Catégorie")
            fields.append("product_category = %s")
            values.append(new_product_category.strip())

        if new_product_platform is not None:
            self._check_non_empty_string(new_product_platform, "Plateforme")
            fields.append("product_platform = %s")
            values.append(new_product_platform.strip())

        if new_product_esrb_rating is not None:
            self._check_non_empty_string(new_product_esrb_rating, "ESRB")
            fields.append("product_esrb_rating = %s")
            values.append(new_product_esrb_rating.strip())

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
            print("Aucune modification demandée.")
            return

        set_clause = ", ".join(fields)
        values.append(product_id)

        cursor = self.connection.cursor()
        query = f"UPDATE products SET {set_clause} WHERE product_id = %s"

        try:
            cursor.execute(query, tuple(values))
            self.connection.commit()
            print(f"Produit {product_id} mis à jour.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de la mise à jour : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        self.products = pd.read_sql("SELECT * FROM products", self.connection)




    #Filtres produits

    def filter_products_id(self, product_id):
        return self.products[self.products["product_id"] == product_id]

    def filter_products_name(self, product_name):
        return self.products[self.products["product_name"].str.contains(product_name, case=False)]

    def filter_products_price(self, min_price, max_price):
        min_p = float(min_price)
        max_p = float(max_price)
        return self.products[
            (self.products["product_price"] >= min_p)
            & (self.products["product_price"] <= max_p)
        ]

    def filter_products_category(self, product_category):
        return self.products[self.products["product_category"] == product_category]




    #  Opérations clients

    def add_customer(self, first_name, last_name, email, password,
                     phone, zip_code_prefix, city, state,
                     address_line1=None, address_line2=None,
                     is_admin=0):
        """Ajoute un client dans la table customers."""

        

        # Validations simples
        self._check_non_empty_string(first_name, "Prénom")
        self._check_non_empty_string(last_name, "Nom")
        self._check_non_empty_string(email, "E-mail")
        self._check_non_empty_string(password, "Mot de passe")

        # Vérifier unicité de l'e-mail
        if email in set(self.customers["email"]):
            raise ValueError("Un client avec cet e-mail existe déjà.")

        # Générer un nouvel ID client
        new_id_num = self.customers.shape[0] + 1
        customer_id = "CUST_" + "{:06d}".format(new_id_num)

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
                    NOW(), NULL,
                    0, 0.00)
        """

        try:
            cursor.execute(query, (
                customer_id,
                first_name.strip(), last_name.strip(), email.strip(),
                password,  # dans un vrai projet : hash du mot de passe
                phone,
                int(zip_code_prefix), city, state,
                address_line1, address_line2,
                int(is_admin)
            ))
            self.connection.commit()
            print(f"Client {customer_id} ajouté avec succès.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de l'ajout du client : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        # Recharger les clients
        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def modify_customer(self, customer_id, first_name=None, last_name=None,
                        email=None, password=None, phone=None,
                        zip_code_prefix=None, city=None, state=None,
                        address_line1=None, address_line2=None,
                        is_admin=None):
        """Modifie un client existant (seuls les champs non None sont mis à jour)."""

        

        self._check_non_empty_string(customer_id, "customer_id")

        if customer_id not in set(self.customers["customer_id"]):
            print("Aucun client avec cet identifiant.")
            return

        fields = []
        values = []

        if first_name is not None:
            self._check_non_empty_string(first_name, "Prénom")
            fields.append("first_name = %s")
            values.append(first_name.strip())

        if last_name is not None:
            self._check_non_empty_string(last_name, "Nom")
            fields.append("last_name = %s")
            values.append(last_name.strip())

        if email is not None:
            self._check_non_empty_string(email, "E-mail")
            fields.append("email = %s")
            values.append(email.strip())

        if password is not None:
            self._check_non_empty_string(password, "Mot de passe")
            fields.append("password_hash = %s")
            values.append(password)

        if phone is not None:
            fields.append("phone = %s")
            values.append(phone)

        if zip_code_prefix is not None:
            fields.append("zip_code_prefix = %s")
            values.append(int(zip_code_prefix))

        if city is not None:
            fields.append("city = %s")
            values.append(city)

        if state is not None:
            fields.append("state = %s")
            values.append(state)

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
            print("Aucune modification demandée.")
            return

        set_clause = ", ".join(fields)
        values.append(customer_id)

        cursor = self.connection.cursor()
        query = f"UPDATE customers SET {set_clause} WHERE customer_id = %s"

        try:
            cursor.execute(query, tuple(values))
            self.connection.commit()
            print(f"Client {customer_id} mis à jour.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de la mise à jour du client : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)

    def del_customer(self, customer_id):
        """Supprime un client s'il existe (si contraintes FK le permettent)."""

        

        self._check_non_empty_string(customer_id, "customer_id")

        if customer_id not in set(self.customers["customer_id"]):
            print("Aucun client avec cet identifiant.")
            return

        cursor = self.connection.cursor()
        query = "DELETE FROM customers WHERE customer_id = %s"

        try:
            cursor.execute(query, (customer_id,))
            self.connection.commit()
            print(f"Client {customer_id} supprimé.")
        except mysql.connector.Error as err:
            print(f"Erreur MySQL lors de la suppression du client : {err}")
            self.connection.rollback()
        finally:
            cursor.close()

        self.customers = pd.read_sql("SELECT * FROM customers", self.connection)




    # Filtre sur clients

    def filter_customer_name(self, name):
        " Filtre les clients par leur nom (partie prénom ou nom, insensible à la casse) "

        

        if not isinstance(name, str) or name.strip() == "":
            print("Nom vide, aucun filtre appliqué.")
            return self.customers

        pattern = name.strip()
        mask = (
            self.customers["first_name"].str.contains(pattern, case=False, na=False)
            | self.customers["last_name"].str.contains(pattern, case=False, na=False)
        )
        return self.customers[mask]


    def filter_customer_email(self, email):
        " Filtre les clients par leur email (exact ou fragment) "

        if not isinstance(email, str) or email.strip() == "":
            print("Email vide, aucun filtre appliqué.")
            return self.customers

        pattern = email.strip()
        # pour recherche exacte, remplacer par == pattern
        return self.customers[self.customers["email"].str.contains(pattern, case=False, na=False)]


    def filter_customer_city(self, city):
        " Filtre les clients par leur lieu d'habitation (ville, insensible à la casse) "

        if not isinstance(city, str) or city.strip() == "":
            print("Ville vide, aucun filtre appliqué.")
            return self.customers

        pattern = city.strip()
        return self.customers[self.customers["city"].str.contains(pattern, case=False, na=False)]



    #Connexion

    def close_connection(self):
        if self.connection.is_connected():
            self.connection.close()
            print("Connexion fermée.")