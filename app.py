from flask import Flask, render_template, request, redirect, url_for, session, flash
from main_magasin import Magasin

app = Flask(__name__)
app.secret_key = "change_me_dev_only"

# Création d'une instance unique de Magasin
magasin = Magasin()


# ---------- Helpers ----------

def current_user_email():
    return session.get("user_email")


def current_user_is_admin():
    email = current_user_email()
    if not email:
        return False
    return magasin.check_is_admin(email)


# ---------- Routes ----------

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

        if magasin.magasin_login(email, password):
            session["user_email"] = email
            flash("Connexion réussie.", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Email ou mot de passe incorrect.", "error")
            return render_template("login.html")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Déconnecté.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user_email" not in session:
        return redirect(url_for("login"))

    return render_template(
        "dashboard.html",
        user_email=current_user_email(),
        is_admin=current_user_is_admin()
    )

@app.context_processor
def inject_user_role():
    return {
        "is_admin": magasin.check_is_admin(magasin.log_id),
        "user_email": magasin.log_id,
    }

# ---------- Produits ----------

@app.route("/products")
def products_list():
    if "user_email" not in session:
        return redirect(url_for("login"))

    name = request.args.get("name", "").strip()
    category = request.args.get("category", "").strip()
    min_price = request.args.get("min_price", "").strip()
    max_price = request.args.get("max_price", "").strip()

    # Point de départ : tous les produits
    df = magasin.products

    if name:
        df = magasin.filter_products_name(df, name)

    if category:
        df = magasin.filter_products_category(df, category)

    df = magasin.filter_products_price(
        df,
        min_price if min_price != "" else None,
        max_price if max_price != "" else None
    )

    products = df.to_dict(orient="records")

    return render_template(
        "products.html",
        products=products,
        is_admin=current_user_is_admin()
    )


@app.route("/products/add", methods=["POST"])
def products_add():
    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))

    try:
        name = request.form.get("name")
        category = request.form.get("category")
        platform = request.form.get("platform")
        esrb = request.form.get("esrb")
        year = request.form.get("year")
        price = request.form.get("price")
        weight = request.form.get("weight")
        description = request.form.get("description")

        magasin.add_product(name, category, platform, esrb, year, price, weight, description)
        flash("Produit ajouté avec succès.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("products_list"))


@app.route("/products/delete/<product_id>", methods=["POST"])
def products_delete(product_id):
    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))

    try:
        magasin.del_product(product_id)
        flash("Produit supprimé.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("products_list"))

# ---------- Formulaire modification produit ----------

@app.route("/products/edit/<product_id>", methods=["GET", "POST"])
def product_edit(product_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("products_list"))

    # Récupérer le produit courant
    df = magasin.filter_products_id(magasin.products, product_id)
    if df.empty:
        flash("Produit introuvable.", "error")
        return redirect(url_for("products_list"))

    product = df.iloc[0].to_dict()

    if request.method == "POST":
        # On récupère les valeurs du formulaire.
        # Si le champ est vide, on laisse None pour ne pas le modifier.
        name = request.form.get("name", "").strip() or None
        category = request.form.get("category", "").strip() or None
        platform = request.form.get("platform", "").strip() or None
        esrb = request.form.get("esrb", "").strip() or None
        year = request.form.get("year", "").strip() or None
        price = request.form.get("price", "").strip() or None
        weight = request.form.get("weight", "").strip() or None
        description = request.form.get("description", "").strip() or None

        try:
            magasin.modify_products(
                product_id,
                new_product_name=name,
                new_product_category=category,
                new_product_platform=platform,
                new_product_esrb_rating=esrb,
                new_product_release_year=year,
                new_product_price=price,
                new_product_weight_g=weight,
                new_product_description=description,
            )
            flash("Produit modifié avec succès.", "success")
            return redirect(url_for("products_list"))
        except ValueError as e:
            flash(str(e), "error")

    # GET : afficher le formulaire pré-rempli
    return render_template("edit_product.html", product=product)


# ---------- Clients ----------

@app.route("/customers")
def customers_list():
    if "user_email" not in session:
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

    return render_template(
        "customers.html",
        customers=customers,
        is_admin=current_user_is_admin()
    )


@app.route("/customers/add", methods=["POST"])
def customers_add():
    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))

    try:
        first = request.form.get("first_name")
        last = request.form.get("last_name")
        email = request.form.get("email")
        pwd = request.form.get("password")
        phone = request.form.get("phone")
        zip_code = request.form.get("zip_code_prefix")
        city = request.form.get("city")
        state = request.form.get("state")
        addr1 = request.form.get("address_line1")
        addr2 = request.form.get("address_line2")
        is_admin_flag = int(request.form.get("is_admin", "0"))

        magasin.add_customer(
            first, last, email, pwd, phone,
            zip_code, city, state, addr1, addr2, is_admin_flag
        )
        flash("Client ajouté avec succès.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("customers_list"))


@app.route("/customers/delete/<customer_id>", methods=["POST"])
def customers_delete(customer_id):
    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))

    try:
        magasin.del_customer(customer_id)
        flash("Client supprimé.", "success")
    except ValueError as e:
        flash(str(e), "error")

    return redirect(url_for("customers_list"))

# ---------- Formulaire modification client ----------

@app.route("/customers/edit/<customer_id>", methods=["GET", "POST"])
def customer_edit(customer_id):
    if "user_email" not in session:
        return redirect(url_for("login"))

    if not current_user_is_admin():
        flash("Action réservée aux administrateurs.", "error")
        return redirect(url_for("customers_list"))

    df = magasin.customers[magasin.customers["customer_id"] == customer_id]
    if df.empty:
        flash("Client introuvable.", "error")
        return redirect(url_for("customers_list"))

    customer = df.iloc[0].to_dict()

    if request.method == "POST":
        first = request.form.get("first_name", "").strip() or None
        last = request.form.get("last_name", "").strip() or None
        email = request.form.get("email", "").strip() or None
        pwd = request.form.get("password", "").strip() or None
        phone = request.form.get("phone", "").strip() or None
        zip_code = request.form.get("zip_code_prefix", "").strip() or None
        city = request.form.get("city", "").strip() or None
        state = request.form.get("state", "").strip() or None
        addr1 = request.form.get("address_line1", "").strip() or None
        addr2 = request.form.get("address_line2", "").strip() or None
        is_admin_flag = request.form.get("is_admin", "").strip()
        is_admin_val = int(is_admin_flag) if is_admin_flag != "" else None

        try:
            magasin.modify_customer(
                customer_id,
                first_name=first,
                last_name=last,
                email=email,
                password=pwd,
                phone=phone,
                zip_code_prefix=zip_code,
                city=city,
                state=state,
                address_line1=addr1,
                address_line2=addr2,
                is_admin=is_admin_val,
            )
            flash("Client modifié avec succès.", "success")
            return redirect(url_for("customers_list"))
        except ValueError as e:
            flash(str(e), "error")

    return render_template("edit_customer.html", customer=customer)

if __name__ == "__main__":
    app.run(debug=True)
