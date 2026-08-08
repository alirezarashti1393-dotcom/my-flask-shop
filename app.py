from flask import Flask, render_template, session, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash

import json
import os
import random
from datetime import datetime, timedelta


app = Flask(__name__)

app.secret_key = "game_shop_secret_key"


# =========================================================
# SETTINGS
# =========================================================

USERS_FILE = "users.json"
ORDERS_FILE = "orders.json"
BANNED_PHONES_FILE = "banned_phones.json"

CREATOR_USERNAME = "علیرضا قربانی"
CREATOR_PASSWORD = "Alireza1103"


# =========================================================
# USERS
# =========================================================

def load_users():

    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(
            USERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (json.JSONDecodeError, OSError):

        return []


def save_users(users):

    with open(
        USERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            users,
            file,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# BANNED PHONES
# =========================================================

def load_banned_phones():

    if not os.path.exists(BANNED_PHONES_FILE):
        return []

    try:

        with open(
            BANNED_PHONES_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (json.JSONDecodeError, OSError):

        return []


def save_banned_phones(banned_phones):

    with open(
        BANNED_PHONES_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            banned_phones,
            file,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# ORDERS
# =========================================================

def load_orders():

    if not os.path.exists(ORDERS_FILE):
        return []

    try:

        with open(
            ORDERS_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

            if isinstance(data, list):
                return data

            return []

    except (json.JSONDecodeError, OSError):

        return []


def save_orders(orders):

    with open(
        ORDERS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            orders,
            file,
            ensure_ascii=False,
            indent=4
        )


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# =========================================================
# REGISTER
# =========================================================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":

        return render_template(
            "register.html"
        )

    username = request.form.get(
        "username",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    # -----------------------------------------------------
    # USERNAME
    # -----------------------------------------------------

    if not username:

        return redirect(
            "/error?message=لطفاً نام کاربری خود را وارد کنید."
        )

    if len(username) < 3:

        return redirect(
            "/error?message=نام کاربری باید حداقل ۳ کاراکتر باشد."
        )

    # -----------------------------------------------------
    # PHONE
    # -----------------------------------------------------

    if not phone.isdigit():

        return redirect(
            "/error?message=لطفاً شماره موبایل را فقط با اعداد وارد کنید."
        )

    if not phone.startswith("09"):

        return redirect(
            "/error?message=شماره موبایل باید با 09 شروع شود."
        )

    if len(phone) != 11:

        return redirect(
            "/error?message=شماره موبایل باید 11 رقم باشد."
        )

    # -----------------------------------------------------
    # PASSWORD
    # -----------------------------------------------------

    if not password:

        return redirect(
            "/error?message=لطفاً رمز عبور خود را وارد کنید."
        )

    if len(password) < 4:

        return redirect(
            "/error?message=رمز عبور باید حداقل ۴ کاراکتر باشد."
        )

    # =====================================================
    # CREATOR
    # =====================================================

    if username == CREATOR_USERNAME:

        if password != CREATOR_PASSWORD:

            return redirect(
                "/error?message=رمز عبور سازنده اشتباه است."
            )

        # سازنده به عنوان کاربر عادی ذخیره نمی‌شود
        session["user"] = {

            "username": CREATOR_USERNAME,

            "phone": phone,

            "is_creator": True
        }

        return redirect("/profile")

    # =====================================================
    # NORMAL USER
    # =====================================================

    users = load_users()

    # -----------------------------------------------------
    # بررسی شماره تکراری
    # -----------------------------------------------------

    for saved_user in users:

        saved_phone = str(
            saved_user.get(
                "phone",
                ""
            )
        ).strip()

        if saved_phone == phone:

            return redirect(
                "/error?message=کاربر دیگری با این شماره موبایل داخل سایت عضو است."
            )

    # -----------------------------------------------------
    # بررسی نام کاربری تکراری
    # -----------------------------------------------------

    for saved_user in users:

        if saved_user.get(
            "username"
        ) == username:

            return redirect(
                "/error?message=این نام کاربری قبلاً استفاده شده است."
            )

    # -----------------------------------------------------
    # ساخت کاربر
    # -----------------------------------------------------

    new_user = {

        "username": username,

        "phone": phone,

        "password":
            generate_password_hash(
                password
            ),

        "is_creator": False,

        "banned": False,

        "ban_until": "",

        "ban_reason": ""
    }

    users.append(
        new_user
    )

    save_users(
        users
    )

    session["user"] = {

        "username": username,

        "phone": phone,

        "is_creator": False
    }

    return redirect(
        "/profile"
    )


# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "GET":

        return render_template(
            "login.html"
        )

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    password = request.form.get(
        "password",
        ""
    ).strip()

    if not phone or not password:

        return redirect(
            "/error?message=لطفاً شماره موبایل و رمز عبور خود را وارد کنید."
        )

    # =====================================================
    # شماره دائماً مسدود شده
    # =====================================================

    banned_phones = load_banned_phones()

    if phone in banned_phones:

        return redirect(
            "/error?message=این شماره موبایل اجازه ورود به سایت را ندارد."
        )

    # =====================================================
    # سازنده
    #
    # نکته مهم:
    # اگر رمز سازنده وارد شود، قبل از بررسی کاربران عادی
    # بررسی می‌شود؛ بنابراین وجود شماره در users.json
    # مانع ورود سازنده نمی‌شود.
    # =====================================================

    if password == CREATOR_PASSWORD:

        session["user"] = {

            "username": CREATOR_USERNAME,

            "phone": phone,

            "is_creator": True
        }

        return redirect(
            "/profile"
        )

    # =====================================================
    # کاربر عادی
    # =====================================================

    users = load_users()

    found_user = None

    for saved_user in users:

        saved_phone = str(
            saved_user.get(
                "phone",
                ""
            )
        ).strip()

        if saved_phone == phone:

            found_user = saved_user
            break

    # کاربر پیدا نشد

    if found_user is None:

        return redirect(
            "/error?message=کاربری با این شماره موبایل پیدا نشد. ابتدا ثبت نام کنید."
        )

    # =====================================================
    # بررسی بن موقت
    # =====================================================

    if found_user.get(
        "banned",
        False
    ):

        ban_until_text = found_user.get(
            "ban_until",
            ""
        )

        if ban_until_text:

            try:

                ban_until = datetime.fromisoformat(
                    ban_until_text
                )

                # هنوز بن فعال است

                if datetime.now() < ban_until:

                    return render_template(
                        "banned.html",
                        user=found_user,
                        ban_until=ban_until,
                        reason=found_user.get(
                            "ban_reason",
                            "دلیل مشخص نشده است."
                        )
                    )

                # مدت بن تمام شده

                found_user["banned"] = False
                found_user["ban_until"] = ""
                found_user["ban_reason"] = ""

                save_users(
                    users
                )

            except ValueError:

                pass

    # =====================================================
    # بررسی رمز
    # =====================================================

    saved_password = found_user.get(
        "password",
        ""
    )

    password_is_correct = False

    try:

        password_is_correct = check_password_hash(
            saved_password,
            password
        )

    except Exception:

        # پشتیبانی از رمزهای قدیمی
        password_is_correct = (
            saved_password == password
        )

    if not password_is_correct:

        return redirect(
            "/error?message=رمز عبور اشتباه است."
        )

    # =====================================================
    # ورود موفق
    # =====================================================

    session["user"] = {

        "username":
            found_user.get(
                "username",
                ""
            ),

        "phone":
            found_user.get(
                "phone",
                ""
            ),

        "is_creator": False
    }

    return redirect(
        "/profile"
    )


# =========================================================
# ERROR
# =========================================================

@app.route("/error")
def error():

    message = request.args.get(
        "message",
        "خطایی رخ داده است."
    )

    return render_template(
        "error.html",
        message=message
    )


# =========================================================
# PROFILE
# =========================================================

@app.route("/profile")
def profile():

    user = session.get(
        "user"
    )

    if not user:

        return redirect(
            "/register"
        )

    return render_template(
        "profile.html",
        user=user
    )


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.pop(
        "user",
        None
    )

    return redirect(
        "/"
    )


# =========================================================
# COINS
# =========================================================

@app.route("/coins")
def coins():

    return render_template(
        "coins.html"
    )


# =========================================================
# DIAMONDS
# =========================================================

@app.route("/diamonds")
def diamonds():

    return render_template(
        "diamonds.html"
    )


# =========================================================
# CHARACTERS
# =========================================================

@app.route("/characters")
def characters():

    return render_template(
        "characters.html"
    )


# =========================================================
# CHARACTER BUY
# =========================================================

@app.route("/character_buy")
def character_buy():

    try:

        price = int(
            request.args.get(
                "price",
                90000
            )
        )

    except ValueError:

        price = 90000

    character_type = request.args.get(
        "character_type",
        "لباس کارت قهرمان"
    )

    return render_template(
        "character_buy.html",
        price=price,
        character_type=character_type
    )


# =========================================================
# ADD PRODUCT
# =========================================================

@app.route("/add", methods=["POST"])
def add():

    name = request.form.get(
        "name",
        "محصول"
    )

    try:

        price = int(
            request.form.get(
                "price",
                0
            )
        )

    except ValueError:

        price = 0

    cart = session.get(
        "cart",
        []
    )

    cart.append({

        "name": name,

        "price": price
    })

    session["cart"] = cart

    return redirect(
        "/cart"
    )


# =========================================================
# ADD CHARACTER
# =========================================================

@app.route("/character_add", methods=["POST"])
def character_add():

    character_name = request.form.get(
        "character_name",
        ""
    ).strip()

    character_type = request.form.get(
        "character_type",
        "لباس کارت قهرمان"
    )

    try:

        price = int(
            request.form.get(
                "price",
                0
            )
        )

    except ValueError:

        price = 0

    cart = session.get(
        "cart",
        []
    )

    cart.append({

        "name":
            character_type
            + " - "
            + character_name,

        "price":
            price
    })

    session["cart"] = cart

    return redirect(
        "/cart"
    )


# =========================================================
# CART
# =========================================================

@app.route("/cart")
def cart():

    items = session.get(
        "cart",
        []
    )

    total = sum(
        int(
            item.get(
                "price",
                0
            )
        )
        for item in items
    )

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


# =========================================================
# CLEAR CART
# =========================================================

@app.route("/clear")
def clear():

    session["cart"] = []

    return redirect(
        "/cart"
    )


# =========================================================
# PAYMENT
# =========================================================

@app.route("/payment")
def payment():

    user = session.get(
        "user"
    )

    if not user:

        return redirect(
            "/error?message=ابتدا ثبت نام کنید."
        )

    items = session.get(
        "cart",
        []
    )

    if not items:

        return redirect(
            "/cart"
        )

    total = sum(
        int(
            item.get(
                "price",
                0
            )
        )
        for item in items
    )

    purchase_code = str(
        random.randint(
            100000,
            999999
        )
    )

    orders = load_orders()

    new_order = {

        "username":
            user.get(
                "username"
            ),

        "phone":
            user.get(
                "phone"
            ),

        "items":
            items,

        "total":
            total,

        "purchase_code":
            purchase_code,

        "completed":
            False,

        "rejected":
            False
    }

    orders.append(
        new_order
    )

    save_orders(
        orders
    )

    session["cart"] = []

    return render_template(
        "order_success.html",
        total=total,
        is_creator=user.get(
            "is_creator",
            False
        )
    )


# =========================================================
# MY ORDERS
# =========================================================

@app.route("/my_orders")
def my_orders():

    user = session.get(
        "user"
    )

    if not user:

        return redirect(
            "/register"
        )

    orders = load_orders()

    user_orders = []

    for order in orders:

        if order.get(
            "phone"
        ) == user.get(
            "phone"
        ):

            user_orders.append(
                order
            )

    return render_template(
        "my_orders.html",
        orders=user_orders
    )


# =========================================================
# CREATOR ORDERS
# =========================================================

@app.route("/orders")
def orders():

    user = session.get(
        "user"
    )

    if (
        not user
        or not user.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    orders_list = load_orders()

    return render_template(
        "orders.html",
        orders=orders_list
    )


# =========================================================
# COMPLETE ORDER
# =========================================================

@app.route(
    "/complete_order/<int:order_index>"
)
def complete_order(order_index):

    user = session.get(
        "user"
    )

    if (
        not user
        or not user.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    orders = load_orders()

    if (
        order_index < 0
        or order_index >= len(orders)
    ):

        return redirect(
            "/orders"
        )

    orders[order_index]["completed"] = True
    orders[order_index]["rejected"] = False

    save_orders(
        orders
    )

    return render_template(
        "order_completed_creator.html"
    )


# =========================================================
# REJECT ORDER
# =========================================================

@app.route(
    "/reject_order/<int:order_index>"
)
def reject_order(order_index):

    user = session.get(
        "user"
    )

    if (
        not user
        or not user.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    orders = load_orders()

    if (
        order_index < 0
        or order_index >= len(orders)
    ):

        return redirect(
            "/orders"
        )

    orders[order_index]["completed"] = False
    orders[order_index]["rejected"] = True

    save_orders(
        orders
    )

    return render_template(
        "order_rejected_creator.html"
    )


# =========================================================
# COMPLETED ORDERS
# =========================================================

@app.route("/completed_orders")
def completed_orders():

    user = session.get(
        "user"
    )

    if (
        not user
        or not user.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    orders = load_orders()

    completed = []

    for index, order in enumerate(
        orders
    ):

        if order.get(
            "completed",
            False
        ):

            completed.append({

                "index": index,

                "order": order
            })

    return render_template(
        "completed_orders.html",
        orders=completed
    )


# =========================================================
# USERS LIST
# =========================================================

@app.route("/users")
def users():

    user = session.get(
        "user"
    )

    if (
        not user
        or not user.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    return render_template(
        "users.html",
        users=users_list
    )


# =========================================================
# MANAGE / SEARCH USER
# =========================================================

@app.route(
    "/manage_user",
    methods=["GET", "POST"]
)
def manage_user():

    creator = session.get(
        "user"
    )

    if (
        not creator
        or not creator.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    user_found = None
    user_index = None
    error_message = None

    if request.method == "POST":

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        users_list = load_users()

        for index, saved_user in enumerate(
            users_list
        ):

            saved_phone = str(
                saved_user.get(
                    "phone",
                    ""
                )
            ).strip()

            if saved_phone == phone:

                user_found = saved_user
                user_index = index

                break

        if user_found is None:

            error_message = (
                "کاربری با این شماره موبایل پیدا نشد."
            )

    return render_template(
        "manage_user.html",
        user=user_found,
        user_index=user_index,
        error=error_message
    )


# =========================================================
# BAN USER
# =========================================================

@app.route(
    "/ban_user/<int:user_index>",
    methods=["GET", "POST"]
)
def ban_user(user_index):

    creator = session.get(
        "user"
    )

    if (
        not creator
        or not creator.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    if (
        user_index < 0
        or user_index >= len(users_list)
    ):

        return redirect(
            "/manage_user"
        )

    target_user = users_list[
        user_index
    ]

    # سازنده قابل بن شدن نیست

    if target_user.get(
        "is_creator"
    ):

        return redirect(
            "/manage_user"
        )

    # =====================================================
    # CONFIRM BAN
    # =====================================================

    if request.method == "POST":

        reason = request.form.get(
            "reason",
            ""
        ).strip()

        try:

            days = int(
                request.form.get(
                    "days",
                    "1"
                )
            )

        except ValueError:

            days = 1

        allowed_days = [
            1,
            3,
            4,
            7,
            10
        ]

        if days not in allowed_days:

            days = 1

        if not reason:

            reason = (
                "عدم رعایت قوانین سایت"
            )

        ban_until = (
            datetime.now()
            + timedelta(
                days=days
            )
        )

        target_user["banned"] = True

        target_user["ban_until"] = (
            ban_until.isoformat()
        )

        target_user["ban_reason"] = reason

        save_users(
            users_list
        )

        return render_template(
            "ban_success.html",
            user=target_user,
            days=days,
            reason=reason
        )

    # =====================================================
    # BAN FORM
    # =====================================================

    return render_template(
        "ban_user.html",
        user=target_user,
        user_index=user_index
    )


# =========================================================
# DELETE USER
# =========================================================

@app.route(
    "/delete_user/<int:user_index>",
    methods=["GET", "POST"]
)
def delete_user(user_index):

    creator = session.get(
        "user"
    )

    if (
        not creator
        or not creator.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    if (
        user_index < 0
        or user_index >= len(users_list)
    ):

        return redirect(
            "/manage_user"
        )

    target_user = users_list[
        user_index
    ]

    if target_user.get(
        "is_creator"
    ):

        return redirect(
            "/manage_user"
        )

    username = target_user.get(
        "username",
        "کاربر"
    )

    # =====================================================
    # DELETE ACCOUNT ONLY
    # =====================================================

    if request.method == "POST":

        users_list.pop(
            user_index
        )

        save_users(
            users_list
        )

        return render_template(
            "delete_success.html",
            username=username
        )

    return render_template(
        "delete_user.html",
        user=target_user,
        user_index=user_index
    )


# =========================================================
# DELETE USER + BAN PHONE
# =========================================================

@app.route(
    "/delete_user_and_phone/<int:user_index>",
    methods=["POST"]
)
def delete_user_and_phone(user_index):

    creator = session.get(
        "user"
    )

    if (
        not creator
        or not creator.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    if (
        user_index < 0
        or user_index >= len(users_list)
    ):

        return redirect(
            "/manage_user"
        )

    target_user = users_list[
        user_index
    ]

    if target_user.get(
        "is_creator"
    ):

        return redirect(
            "/manage_user"
        )

    username = target_user.get(
        "username",
        "کاربر"
    )

    phone = str(
        target_user.get(
            "phone",
            ""
        )
    ).strip()

    # حذف حساب

    users_list.pop(
        user_index
    )

    save_users(
        users_list
    )

    # مسدود کردن شماره

    if phone:

        banned_phones = load_banned_phones()

        if phone not in banned_phones:

            banned_phones.append(
                phone
            )

            save_banned_phones(
                banned_phones
            )

    return render_template(
        "delete_success.html",
        username=username
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset_password/<int:user_index>",
    methods=["GET", "POST"]
)
def reset_password(user_index):

    creator = session.get(
        "user"
    )

    if (
        not creator
        or not creator.get(
            "is_creator"
        )
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    if (
        user_index < 0
        or user_index >= len(users_list)
    ):

        return redirect(
            "/users"
        )

    target_user = users_list[
        user_index
    ]

    if target_user.get(
        "is_creator"
    ):

        return redirect(
            "/users"
        )

    if request.method == "POST":

        new_password = request.form.get(
            "new_password",
            ""
        ).strip()

        if len(new_password) < 4:

            return render_template(
                "reset_password.html",
                user=target_user,
                error=(
                    "رمز عبور باید حداقل ۴ کاراکتر باشد."
                )
            )

        target_user["password"] = (
            generate_password_hash(
                new_password
            )
        )

        save_users(
            users_list
        )

        return render_template(
            "reset_password.html",
            user=target_user,
            success=(
                "رمز عبور با موفقیت تغییر کرد."
            )
        )

    return render_template(
        "reset_password.html",
        user=target_user
    )


# =========================================================
# CHANGE USERNAME
# =========================================================

@app.route(
    "/change_username",
    methods=["GET", "POST"]
)
def change_username():

    current_user = session.get(
        "user"
    )

    if not current_user:

        return redirect(
            "/register"
        )

    if current_user.get(
        "is_creator"
    ):

        return redirect(
            "/profile"
        )

    users_list = load_users()

    current_username = current_user.get(
        "username"
    )

    user_index = None

    for index, saved_user in enumerate(
        users_list
    ):

        if saved_user.get(
            "username"
        ) == current_username:

            user_index = index

            break

    if user_index is None:

        return redirect(
            "/profile"
        )

    if request.method == "POST":

        new_username = request.form.get(
            "new_username",
            ""
        ).strip()

        if not new_username:

            return render_template(
                "change_username.html",
                error=(
                    "لطفاً نام کاربری جدید را وارد کنید."
                ),
                current_username=current_username
            )

        if len(new_username) < 3:

            return render_template(
                "change_username.html",
                error=(
                    "نام کاربری باید حداقل ۳ کاراکتر باشد."
                ),
                current_username=current_username
            )

        for saved_user in users_list:

            if (
                saved_user.get(
                    "username"
                ) == new_username
                and saved_user.get(
                    "username"
                ) != current_username
            ):

                return render_template(
                    "change_username.html",
                    error=(
                        "این نام کاربری قبلاً استفاده شده است."
                    ),
                    current_username=current_username
                )

        users_list[user_index][
            "username"
        ] = new_username

        save_users(
            users_list
        )

        session["user"]["username"] = (
            new_username
        )

        session.modified = True

        return render_template(
            "change_username.html",
            success=(
                "نام کاربری شما با موفقیت تغییر کرد."
            ),
            current_username=new_username
        )

    return render_template(
        "change_username.html",
        current_username=current_username
    )


# =========================================================
# CONTACT
# =========================================================

@app.route("/contact")
def contact():

    return render_template(
        "contact.html"
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True
    )