"""
Application Flask – Magasin de Jeux Vidéo.
Routes pour produits, clients, commandes, stock et panier.
"""

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, abort, jsonify
)
from config import Config
from magasin import Magasin

# ------------------------------------------------------------------ #
#  Initialisation
# ------------------------------------------------------------------ #

app = Flask(__name__)
app.config.from_object(Config)

magasin = Magasin()


# ------------------------------------------------------------------ #
#  Helpers
# ------------------------------------------------------------------ #

def current_user_email():
    return session.get("user_email")


def current_user_is_admin():
    email = current_user_email()
    if not email:
        return False
    return magasin.check_is_admin(email)


def current_customer_id():
    email = current_user_email()
    if not email:
        return None
    row = magasin.customers[magasin.customers["email"] == email]
    if row.empty:
        return None
    return row.iloc[0]["customer_id"]


def require_login():
    """Redirige vers login si non connecté. Retourne True si OK."""
    if "user_email" not in session:
        return False
    return True


def require_admin():
    """Retourne True si l'utilisateur est admin connecté."""
    return require_login() and current_user_is_admin()


def get_cart():
    cart = session.get("cart")
    if not isinstance(cart, dict):
        cart = {}
    return cart


def save_cart(cart):
    session["cart"] = cart
    session.modified = True


# ------------------------------------------------------------------ #
#  Context processor – variables disponibles dans tous les templates
# ------------------------------------------------------------------ #

@app.context_processor
def inject_user_role():
    email = current_user_email()
    return {
        "is_admin": magasin.check_is_admin(email) if email else False,
        "user_email": email,
    }


# ------------------------------------------------------------------ #
#  Routes – Auth
# ------------------------------------------------------------------ #

@app.route("/")
def index():
    if "user_email" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()

        if not email or not password:
            flash("Veuillez remplir tous les champs.", "error")
            return render_template("login.html")

        if magasin.magasin_login(email, password):
            # Régénérer la session pour éviter la fixation de session
            session.clear()
            session["user_email"] = email
            flash("Connexion réussie.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou mot de passe incorrect.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        try:
            magasin.register_customer(
                request.form.get("first_name", "").strip(),
                request.form.get("last_name", "").strip(),
                request.form.get("email", "").strip(),
                request.form.get("password", "").strip(),
                request.form.get("phone", "").strip(),
                request.form.get("zip_code_prefix", "").strip(),
                request.form.get("city", "").strip(),
                request.form.get("state", "").strip(),
                request.form.get("address_line1", "").strip(),
                request.form.get("address_line2", "").strip(),
            )
            flash("Compte créé avec succès ! Vous pouvez maintenant vous connecter.", "success")
            return redirect(url_for("login"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if not require_login():
        return redirect(url_for("login"))

    if current_user_is_admin():
        # Quelques KPI rapides pour le dashboard admin
        nb_products = len(magasin.products)
        nb_customers = len(magasin.customers)
        nb_orders = len(magasin.orders)

        # Produits en stock critique
        stock_view = magasin.get_stock_view()
        critical = stock_view[stock_view["quantity_available"] <= stock_view["min_stock_level"]]
        nb_critical = len(critical)

        return render_template(
            "dashboard.html",
            user_email=current_user_email(),
            is_admin=True,
            nb_products=nb_products,
            nb_customers=nb_customers,
            nb_orders=nb_orders,
            nb_critical=nb_critical,
        )
    else:
        recent_reviews = magasin.get_recent_reviews(limit=6)
        return render_template(
            "dashboard_client.html",
            user_email=current_user_email(),
            is_admin=False,
            recent_reviews=recent_reviews
        )


# ------------------------------------------------------------------ #
#  Routes – Profil utilisateur
# ------------------------------------------------------------------ #

@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not require_login():
        return redirect(url_for("login"))

    customer_id = current_customer_id()
    if not customer_id:
        flash("Impossible de récupérer votre compte.", "error")
        return redirect(url_for("dashboard"))

    df = magasin.customers[magasin.customers["customer_id"] == customer_id]
    if df.empty:
        flash("Profil introuvable.", "error")
        return redirect(url_for("dashboard"))

    customer = df.iloc[0].to_dict()

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        try:
            magasin.update_profile(
                customer_id,
                first_name=request.form.get("first_name", "").strip() or None,
                last_name=request.form.get("last_name", "").strip() or None,
                password=request.form.get("password", "").strip() or None,
                phone=request.form.get("phone", "").strip() or None,
                zip_code_prefix=request.form.get("zip_code_prefix", "").strip() or None,
                city=request.form.get("city", "").strip() or None,
                state=request.form.get("state", "").strip() or None,
                address_line1=request.form.get("address_line1", "").strip() or None,
                address_line2=request.form.get("address_line2", "").strip() or None,
            )
            msg = "Profil mis à jour avec succès."
            if is_ajax:
                return jsonify(ok=True, message=msg)
            flash(msg, "success")
            return redirect(url_for("profile"))
        except ValueError as e:
            if is_ajax:
                return jsonify(ok=False, message=str(e))
            flash(str(e), "error")

    return render_template(
        "profile.html",
        customer=customer,
        is_admin=current_user_is_admin()
    )


# ------------------------------------------------------------------ #
#  Routes – Produits
# ------------------------------------------------------------------ #

@app.route("/products")
def products_list():
    if not require_login():
        return redirect(url_for("login"))

    name = request.args.get("name", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    df = magasin.products
    if name:
        df = magasin.filter_products_name(df, name)
    if category:
        df = magasin.filter_products_category(df, category)
    df = magasin.filter_products_price(
        df,
        min_price if min_price else None,
        max_price if max_price else None
    )

    products = df.to_dict(orient="records")
    is_admin = current_user_is_admin()

    if is_admin:
        return render_template("products.html", products=products, is_admin=True)
    else:
        # Compute available stock per product for quantity limits
        stock_avail = (
            magasin.stock.groupby("product_id")["quantity_available"]
            .sum()
            .to_dict()
        )
        # Compute average ratings for products
        product_ratings = magasin.get_all_product_ratings()
        for p in products:
            p["stock_available"] = int(stock_avail.get(p["product_id"], 0))
            rating_info = product_ratings.get(p["product_id"], {})
            p["avg_score"] = rating_info.get("avg_score")
            p["review_count"] = rating_info.get("review_count", 0)
        return render_template("products_store.html", products=products, is_admin=False)


@app.route("/products/add", methods=["POST"])
def products_add():
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        magasin.add_product(
            request.form.get("name", "").strip(),
            request.form.get("category", "").strip(),
            request.form.get("platform", "").strip(),
            request.form.get("esrb", "").strip(),
            request.form.get("year", "").strip(),
            request.form.get("price", "").strip(),
            request.form.get("weight", "").strip(),
            request.form.get("description", "").strip(),
        )
        msg = "Produit ajouté avec succès."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("products_list"))


@app.route("/products/delete/<product_id>", methods=["POST"])
def products_delete(product_id):
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))
    try:
        magasin.del_product(product_id)
        flash("Produit supprimé.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("products_list"))


@app.route("/products/edit/<product_id>", methods=["GET", "POST"])
def product_edit(product_id):
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))

    df = magasin.filter_products_id(magasin.products, product_id)
    if df.empty:
        flash("Produit introuvable.", "error")
        return redirect(url_for("products_list"))

    product = df.iloc[0].to_dict()

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        try:
            magasin.modify_products(
                product_id,
                new_product_name=request.form.get("name", "").strip() or None,
                new_product_category=request.form.get("category", "").strip() or None,
                new_product_platform=request.form.get("platform", "").strip() or None,
                new_product_esrb_rating=request.form.get("esrb", "").strip() or None,
                new_product_release_year=request.form.get("year", "").strip() or None,
                new_product_price=request.form.get("price", "").strip() or None,
                new_product_weight_g=request.form.get("weight", "").strip() or None,
                new_product_description=request.form.get("description", "").strip() or None,
            )
            msg = "Produit modifié avec succès."
            if is_ajax:
                return jsonify(ok=True, message=msg)
            flash(msg, "success")
            return redirect(url_for("products_list"))
        except ValueError as e:
            if is_ajax:
                return jsonify(ok=False, message=str(e))
            flash(str(e), "error")

    return render_template("edit_product.html", product=product)


# ------------------------------------------------------------------ #
#  Routes – Clients
# ------------------------------------------------------------------ #

@app.route("/customers")
def customers_list():
    if not require_login():
        return redirect(url_for("login"))

    name = request.args.get("name", "").strip()
    email = request.args.get("email", "").strip()
    city = request.args.get("city", "").strip()

    df = magasin.customers
    if name:
        df = magasin.filter_customer_name(df, name)
    if email:
        df = magasin.filter_customer_email(df, email)
    if city:
        df = magasin.filter_customer_city(df, city)

    customers = df.to_dict(orient="records")
    return render_template("customers.html", customers=customers, is_admin=current_user_is_admin())


@app.route("/customers/add", methods=["POST"])
def customers_add():
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    try:
        magasin.add_customer(
            request.form.get("first_name", "").strip(),
            request.form.get("last_name", "").strip(),
            request.form.get("email", "").strip(),
            request.form.get("password", "").strip(),
            request.form.get("phone", "").strip(),
            request.form.get("zip_code_prefix", "").strip(),
            request.form.get("city", "").strip(),
            request.form.get("state", "").strip(),
            request.form.get("address_line1", "").strip(),
            request.form.get("address_line2", "").strip(),
            int(request.form.get("is_admin", "0")),
        )
        msg = "Client ajouté avec succès."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("customers_list"))


@app.route("/customers/delete/<customer_id>", methods=["POST"])
def customers_delete(customer_id):
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))
    try:
        magasin.del_customer(customer_id)
        flash("Client supprimé.", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("customers_list"))


@app.route("/customers/edit/<customer_id>", methods=["GET", "POST"])
def customer_edit(customer_id):
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))

    df = magasin.customers[magasin.customers["customer_id"] == customer_id]
    if df.empty:
        flash("Client introuvable.", "error")
        return redirect(url_for("customers_list"))

    customer = df.iloc[0].to_dict()

    if request.method == "POST":
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
        try:
            magasin.modify_customer(
                customer_id,
                first_name=request.form.get("first_name", "").strip() or None,
                last_name=request.form.get("last_name", "").strip() or None,
                email=request.form.get("email", "").strip() or None,
                password=request.form.get("password", "").strip() or None,
                phone=request.form.get("phone", "").strip() or None,
                zip_code_prefix=request.form.get("zip_code_prefix", "").strip() or None,
                city=request.form.get("city", "").strip() or None,
                state=request.form.get("state", "").strip() or None,
                address_line1=request.form.get("address_line1", "").strip() or None,
                address_line2=request.form.get("address_line2", "").strip() or None,
                is_admin=(
                    int(request.form["is_admin"])
                    if request.form.get("is_admin", "") != ""
                    else None
                ),
            )
            msg = "Client modifié avec succès."
            if is_ajax:
                return jsonify(ok=True, message=msg)
            flash(msg, "success")
            return redirect(url_for("customers_list"))
        except ValueError as e:
            if is_ajax:
                return jsonify(ok=False, message=str(e))
            flash(str(e), "error")

    return render_template("edit_customer.html", customer=customer)


# ------------------------------------------------------------------ #
#  Routes – Panier
# ------------------------------------------------------------------ #

@app.route("/cart")
def cart_view():
    if not require_login():
        return redirect(url_for("login"))

    cart = get_cart()
    if not cart:
        return render_template("cart.html", products=[], total=0.0)

    df = magasin.products[magasin.products["product_id"].isin(cart.keys())].copy()
    df["quantity"] = df["product_id"].map(cart)
    df["line_total"] = df["product_price"] * df["quantity"]
    products = df.to_dict(orient="records")
    total = float(df["line_total"].sum())
    return render_template("cart.html", products=products, total=total)


@app.route("/cart/add/<product_id>", methods=["POST"])
def cart_add(product_id):
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    if not require_login():
        if is_ajax:
            return jsonify(ok=False, message="Non connecté."), 401
        return redirect(url_for("login"))

    if product_id not in set(magasin.products["product_id"]):
        if is_ajax:
            return jsonify(ok=False, message="Produit introuvable.")
        flash("Produit introuvable.", "error")
        return redirect(url_for("products_list"))

    cart = get_cart()
    try:
        qty = max(1, int(request.form.get("quantity", "1").strip() or "1"))
    except ValueError:
        qty = 1

    # Check available stock
    stock_avail = int(
        magasin.stock.loc[
            magasin.stock["product_id"] == product_id, "quantity_available"
        ].sum()
    )
    already_in_cart = cart.get(product_id, 0)
    if already_in_cart + qty > stock_avail:
        msg = (
            f"Stock insuffisant (disponible : {stock_avail}, "
            f"déjà dans le panier : {already_in_cart})."
        )
        if is_ajax:
            return jsonify(ok=False, message=msg, stock=stock_avail)
        flash(msg, "error")
        return redirect(url_for("products_list"))

    cart[product_id] = already_in_cart + qty
    save_cart(cart)

    if is_ajax:
        return jsonify(ok=True, message="Produit ajouté au panier.")
    flash("Produit ajouté au panier.", "success")
    return redirect(url_for("products_list"))


@app.route("/cart/remove/<product_id>", methods=["POST"])
def cart_remove(product_id):
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    cart = get_cart()
    if product_id in cart:
        cart.pop(product_id)
        save_cart(cart)
        if is_ajax:
            return jsonify(ok=True, message="Produit retiré du panier.")
        flash("Produit retiré du panier.", "info")
    else:
        if is_ajax:
            return jsonify(ok=False, message="Produit non trouvé dans le panier.")
        flash("Produit non trouvé dans le panier.", "error")
    return redirect(url_for("cart_view"))


@app.route("/cart/update", methods=["POST"])
def cart_update():
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    cart = get_cart()
    for field, value in request.form.items():
        if not field.startswith("qty_"):
            continue
        pid = field[4:]  # enlever "qty_"
        try:
            qty = int(value)
        except ValueError:
            continue
        if qty <= 0:
            cart.pop(pid, None)
        else:
            cart[pid] = qty

    save_cart(cart)
    if is_ajax:
        return jsonify(ok=True, message="Panier mis à jour.")
    flash("Panier mis à jour.", "success")
    return redirect(url_for("cart_view"))


@app.route("/cart/checkout", methods=["POST"])
def cart_checkout():
    if not require_login():
        return redirect(url_for("login"))

    customer_id = current_customer_id()
    if not customer_id:
        flash("Impossible de récupérer votre compte client.", "error")
        return redirect(url_for("cart_view"))

    cart = get_cart()
    if not cart:
        flash("Votre panier est vide.", "error")
        return redirect(url_for("cart_view"))

    try:
        order_id = magasin.create_order_from_cart(customer_id, cart)
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("cart_view"))

    if not order_id:
        flash("Erreur lors de la création de la commande.", "error")
        return redirect(url_for("cart_view"))

    save_cart({})
    flash(f"Commande {order_id} créée avec succès !", "success")
    return redirect(url_for("orders_list"))


# ------------------------------------------------------------------ #
#  Routes – Commandes
# ------------------------------------------------------------------ #

@app.route("/orders")
def orders_list():
    if not require_login():
        return redirect(url_for("login"))

    if current_user_is_admin():
        # Admin : voir TOUTES les commandes avec filtres
        df = magasin.get_all_orders()

        # Appliquer les filtres GET
        status = request.args.get("status", "").strip()
        customer_name = request.args.get("customer_name", "").strip()
        min_total = request.args.get("min_total", "").strip()
        max_total = request.args.get("max_total", "").strip()
        date_from = request.args.get("date_from", "").strip()
        date_to = request.args.get("date_to", "").strip()

        df = magasin.filter_orders(
            df,
            status=status or None,
            customer_name=customer_name or None,
            min_total=min_total or None,
            max_total=max_total or None,
            date_from=date_from or None,
            date_to=date_to or None,
        )

        orders = df.to_dict(orient="records")
        return render_template("orders_admin.html", orders=orders, is_admin=True)
    else:
        # Client : ses commandes uniquement
        customer_id = current_customer_id()
        if not customer_id:
            flash("Impossible de récupérer votre compte.", "error")
            return redirect(url_for("dashboard"))

        df = magasin.get_customer_orders(customer_id)
        orders = df.to_dict(orient="records")
        return render_template("orders.html", orders=orders, is_admin=False)


@app.route("/orders/<order_id>")
def order_detail(order_id):
    """Affiche les détails d'une commande."""
    if not require_login():
        return redirect(url_for("login"))

    # Vérifier que la commande existe
    order_row = magasin.orders[magasin.orders["order_id"] == order_id]
    if order_row.empty:
        flash("Commande introuvable.", "error")
        return redirect(url_for("orders_list"))

    order = order_row.iloc[0].to_dict()

    # Si client, vérifier que c'est bien sa commande
    if not current_user_is_admin():
        if order["customer_id"] != current_customer_id():
            flash("Vous n'avez pas accès à cette commande.", "error")
            return redirect(url_for("orders_list"))

    items_df = magasin.get_order_details(order_id)
    items = items_df.to_dict(orient="records")
    total = float(items_df["line_total"].sum()) if not items_df.empty else 0.0

    # Récupérer l'avis existant pour cette commande
    review = magasin.get_review_for_order(order_id)

    return render_template(
        "order_detail.html",
        order=order,
        items=items,
        total=total,
        review=review,
        is_admin=current_user_is_admin()
    )


@app.route("/orders/<order_id>/status", methods=["POST"])
def order_update_status(order_id):
    """Admin : change le statut d'une commande."""
    if not require_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("orders_list"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
    new_status = request.form.get("status", "").strip()
    try:
        magasin.update_order_status(order_id, new_status)
        msg = f"Commande {order_id} → {new_status}."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/orders/<order_id>/cancel", methods=["POST"])
def order_cancel(order_id):
    """Client : annule sa propre commande (si statut = created)."""
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    order_row = magasin.orders[magasin.orders["order_id"] == order_id]
    if order_row.empty:
        if is_ajax:
            return jsonify(ok=False, message="Commande introuvable.")
        flash("Commande introuvable.", "error")
        return redirect(url_for("orders_list"))

    order = order_row.iloc[0]

    # Vérifier propriété ou admin
    if not current_user_is_admin():
        if order["customer_id"] != current_customer_id():
            if is_ajax:
                return jsonify(ok=False, message="Vous n'avez pas accès à cette commande.")
            flash("Vous n'avez pas accès à cette commande.", "error")
            return redirect(url_for("orders_list"))

    if order["order_status"] not in ("created", "approved"):
        msg = "Cette commande ne peut plus être annulée."
        if is_ajax:
            return jsonify(ok=False, message=msg)
        flash(msg, "error")
        return redirect(url_for("order_detail", order_id=order_id))

    try:
        magasin.update_order_status(order_id, "cancelled")
        msg = f"Commande {order_id} annulée."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("order_detail", order_id=order_id))


# ------------------------------------------------------------------ #
#  Routes – Avis clients
# ------------------------------------------------------------------ #

@app.route("/reviews/add/<order_id>", methods=["POST"])
def review_add(order_id):
    """Ajouter un avis pour une commande livrée."""
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # Vérifier que la commande appartient au client
    order_row = magasin.orders[magasin.orders["order_id"] == order_id]
    if order_row.empty:
        msg = "Commande introuvable."
        if is_ajax:
            return jsonify(ok=False, message=msg)
        flash(msg, "error")
        return redirect(url_for("orders_list"))

    order = order_row.iloc[0]
    if not current_user_is_admin() and order["customer_id"] != current_customer_id():
        msg = "Vous n'avez pas accès à cette commande."
        if is_ajax:
            return jsonify(ok=False, message=msg)
        flash(msg, "error")
        return redirect(url_for("orders_list"))

    try:
        magasin.add_review(
            order_id,
            request.form.get("review_score", ""),
            request.form.get("review_comment_title", ""),
            request.form.get("review_comment_message", ""),
        )
        msg = "Avis ajouté avec succès."
        if is_ajax:
            review = magasin.get_review_for_order(order_id)
            return jsonify(ok=True, message=msg, review=review)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("order_detail", order_id=order_id))


@app.route("/reviews/edit/<review_id>", methods=["POST"])
def review_edit(review_id):
    """Modifier un avis existant."""
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    # Vérifier que l'avis appartient au client
    review_row = magasin.order_reviews[magasin.order_reviews["review_id"] == review_id]
    if review_row.empty:
        msg = "Avis introuvable."
        if is_ajax:
            return jsonify(ok=False, message=msg)
        flash(msg, "error")
        return redirect(url_for("orders_list"))

    oid = review_row.iloc[0]["order_id"]
    order_row = magasin.orders[magasin.orders["order_id"] == oid]
    if not order_row.empty and not current_user_is_admin():
        if order_row.iloc[0]["customer_id"] != current_customer_id():
            msg = "Vous n'avez pas le droit de modifier cet avis."
            if is_ajax:
                return jsonify(ok=False, message=msg)
            flash(msg, "error")
            return redirect(url_for("orders_list"))

    try:
        magasin.update_review(
            review_id,
            review_score=request.form.get("review_score", "").strip() or None,
            review_comment_title=request.form.get("review_comment_title", ""),
            review_comment_message=request.form.get("review_comment_message", ""),
        )
        msg = "Avis modifié avec succès."
        if is_ajax:
            review = magasin.get_review_for_order(oid)
            return jsonify(ok=True, message=msg, review=review)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("order_detail", order_id=oid))


@app.route("/reviews/delete/<review_id>", methods=["POST"])
def review_delete(review_id):
    """Supprimer un avis."""
    if not require_login():
        return redirect(url_for("login"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    review_row = magasin.order_reviews[magasin.order_reviews["review_id"] == review_id]
    if review_row.empty:
        msg = "Avis introuvable."
        if is_ajax:
            return jsonify(ok=False, message=msg)
        flash(msg, "error")
        return redirect(url_for("orders_list"))

    oid = review_row.iloc[0]["order_id"]
    order_row = magasin.orders[magasin.orders["order_id"] == oid]
    if not order_row.empty and not current_user_is_admin():
        if order_row.iloc[0]["customer_id"] != current_customer_id():
            msg = "Vous n'avez pas le droit de supprimer cet avis."
            if is_ajax:
                return jsonify(ok=False, message=msg)
            flash(msg, "error")
            return redirect(url_for("orders_list"))

    try:
        magasin.delete_review(review_id)
        msg = "Avis supprimé."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("order_detail", order_id=oid))


# ------------------------------------------------------------------ #
#  Routes – Stock
# ------------------------------------------------------------------ #

@app.route("/stock")
def stock_list():
    if not require_admin():
        flash("Accès réservé aux administrateurs.", "error")
        return redirect(url_for("dashboard"))

    df = magasin.get_stock_view().sort_values(["product_name", "seller_id"])
    stock_rows = df.to_dict(orient="records")
    return render_template("stock.html", stock_rows=stock_rows)


@app.route("/stock/update/<stock_id>", methods=["POST"])
def stock_update(stock_id):
    if not require_admin():
        flash("Accès réservé aux administrateurs.", "error")
        return redirect(url_for("dashboard"))

    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

    def parse_int(val):
        val = val.strip() if val else ""
        return int(val) if val else None

    try:
        magasin.update_stock(
            stock_id,
            quantity_in_stock=parse_int(request.form.get("quantity_in_stock", "")),
            quantity_reserved=parse_int(request.form.get("quantity_reserved", "")),
            min_stock_level=parse_int(request.form.get("min_stock_level", "")),
            reorder_point=parse_int(request.form.get("reorder_point", "")),
            seller_id=request.form.get("seller_id", "").strip() or None,
            warehouse_location=request.form.get("warehouse_location", "").strip() or None,
            stock_condition=request.form.get("stock_condition", "").strip() or None,
        )
        msg = f"Stock {stock_id} mis à jour."
        if is_ajax:
            return jsonify(ok=True, message=msg)
        flash(msg, "success")
    except ValueError as e:
        if is_ajax:
            return jsonify(ok=False, message=str(e))
        flash(str(e), "error")

    return redirect(url_for("stock_list"))


# ------------------------------------------------------------------ #
#  API – Autocomplétion
# ------------------------------------------------------------------ #

@app.route("/api/cities")
def api_cities():
    """Retourne les villes uniques (JSON) pour l'autocomplétion."""
    query = request.args.get("q", "").strip().lower()
    cities = magasin.get_unique_cities()
    if query:
        cities = [c for c in cities if query in c.lower()]
    return jsonify(cities[:50])


@app.route("/api/states")
def api_states():
    """Retourne les régions/états uniques (JSON) pour l'autocomplétion."""
    query = request.args.get("q", "").strip().lower()
    states = magasin.get_unique_states()
    if query:
        states = [s for s in states if query in s.lower()]
    return jsonify(states[:50])


@app.route("/api/zip_codes")
def api_zip_codes():
    """Retourne les codes postaux uniques (JSON) pour l'autocomplétion."""
    query = request.args.get("q", "").strip()
    zip_codes = magasin.get_unique_zip_codes()
    if query:
        zip_codes = [z for z in zip_codes if query in z]
    return jsonify(zip_codes[:50])


@app.route("/api/geolocation")
def api_geolocation():
    """Retourne les entrées de géolocalisation (JSON) pour l'autocomplétion croisée."""
    query = request.args.get("q", "").strip()
    entries = magasin.get_geolocation_entries(query)
    return jsonify(entries)


@app.route("/api/categories")
def api_categories():
    """Retourne les catégories de produits uniques (JSON)."""
    categories = magasin.get_unique_categories()
    return jsonify(categories)


@app.route("/api/platforms")
def api_platforms():
    """Retourne les plateformes uniques (JSON)."""
    platforms = magasin.get_unique_platforms()
    return jsonify(platforms)


# ------------------------------------------------------------------ #
#  Lancement
# ------------------------------------------------------------------ #

if __name__ == "__main__":
    app.run(debug=True)
