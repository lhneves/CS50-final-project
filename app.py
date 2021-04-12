import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
def page():
    return render_template("page.html")

@app.route("/index")
@login_required
def index():
    """Show portfolio of stocks"""

    rows = db.execute("SELECT * FROM stocks WHERE user_id = :user", user=session["user_id"])
    cash = db.execute("SELECT cash FROM users WHERE id = :user", user=session["user_id"])[0]['cash']

    total = cash
    stocks = []
    stocks_chart = []

    for counter, row in enumerate(rows):

        stock_info = lookup(rows[counter]['symbol'])

        stocks.append(list((stock_info['symbol'], stock_info['name'], row['shares'], stock_info['price'], round(stock_info['price'] * row['shares'], 2))))
        total += stocks[counter][4]

    for counter, row in enumerate(rows):
        stock_info = lookup(rows[counter]['symbol'])
        stock_total = round(stock_info['price'] * row['shares'], 2)
        stocks_cash = round((total - cash), 2)
        percent = round((stock_total/stocks_cash),2)
        stocks_chart.append(list((stock_info['symbol'], percent * 100)))

    total = usd(total)
    cash = usd(cash)

    for stock in stocks:
        stock[3] = usd(stock[3])
        stock[4] = usd(stock[4])

    return render_template("index.html", cash=cash, stocks=stocks, total=total, stocks_chart=stocks_chart)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return render_template("login.html", z_index_u=1)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return render_template("login.html", z_index_p=1)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return render_template("login.html", z_index_e=1)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/index")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("register.html", z_index_u=1)

        elif not request.form.get("password"):
            return render_template("register.html", z_index_p=1)

        elif request.form.get("password") != request.form.get("confirm-password"):
            return render_template("register.html", z_index_m=1)

        elif db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username")):
            return render_template("register.html", z_index_e=1)

        else:
            db.execute("INSERT INTO users(username, hash) VALUES (:username, :hash)", username=request.form.get("username"), hash=generate_password_hash(request.form.get("password")))

        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        return redirect("/index")

    else:

        return render_template("register.html")


@app.route("/change", methods=["GET", "POST"])
def change():

    if request.method == "POST":

        if not request.form.get("username"):
            return render_template("change.html", z_index_u=1)

        elif not request.form.get("old-password"):
            return render_template("change.html", z_index_p=1)

        elif not request.form.get("password"):
            return render_template("change.html", z_index_n_p=1)

        elif request.form.get("password") != request.form.get("confirm-password"):
            return render_template("change.html", z_index_m=1)

        username = db.execute("SELECT username FROM users WHERE username = :username", username=request.form.get("username"))

        if not username:
            return render_template("change.html", z_index_e=1)

        else:
            rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

            if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("old-password")):
                return render_template("change.html", z_index_i=1)

            else:
                new_password = request.form.get("password")
                db.execute("UPDATE users SET hash = :hash WHERE username = :username", hash=generate_password_hash(new_password), username = request.form.get("username"))

        flash("Changed!")
        return redirect("/index")

    else:

        return render_template("change.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    if request.method == "POST":

        if not request.form.get("symbol"):
            return render_template("buy.html", z_index_stock=1)

        if not request.form.get("shares"):
            return render_template("buy.html", z_index_shares=1)

        if not lookup(request.form.get("symbol")):
            return render_template("buy.html", z_index_i=1)

        shares_before = int(request.form.get("shares"))
        shares = int(request.form.get("shares"))
        symbol = lookup(request.form.get("symbol"))['symbol']

        price = lookup(request.form.get("symbol"))['price']
        cash = db.execute("SELECT cash FROM users WHERE id = :user", user=session["user_id"])[0]['cash']

        if price * float(shares) > cash:
            return render_template("buy.html", z_index_a=1)

        stock = db.execute("SELECT shares FROM stocks WHERE symbol = :symbol AND user_id = :user", symbol=symbol, user = session["user_id"])

        if not stock:
            db.execute("INSERT INTO stocks(user_id, symbol, shares) VALUES(:user, :symbol, :shares)", user=session["user_id"], symbol=symbol, shares=shares)
        else:
            shares += stock[0]['shares']
            db.execute("UPDATE stocks SET shares = :shares WHERE user_id = :user AND symbol = :symbol", shares=shares, user=session["user_id"], symbol=symbol)

        after_cash = cash - price * float(shares)
        db.execute("UPDATE users SET cash = :cash WHERE id = :user", cash = after_cash, user=session["user_id"])

        db.execute("INSERT INTO transactions(user_id, symbol, shares, value) VALUES(:user, :symbol, :shares, :value)", user=session["user_id"], symbol=symbol, shares=shares_before, value= price*float(shares))

        flash("Bought!")
        return redirect("/index")

    else:

        return render_template("buy.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    if request.method == "POST":
        symbols = db.execute("SELECT symbol FROM stocks WHERE user_id = :user", user=session["user_id"])

        if not request.form.get("symbol"):
            return render_template("sell.html", z_index_stock=1, symbols=symbols)

        if not request.form.get("shares"):
            return render_template("sell.html", z_index_shares=1, symbols=symbols)

        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))
        price = lookup(request.form.get("symbol"))['price']
        cash = db.execute("SELECT cash FROM users WHERE id = :user", user=session["user_id"])[0]['cash']
        after_cash = cash + price * float(shares)
        stock = db.execute("SELECT shares FROM stocks WHERE symbol = :symbol AND user_id = :user", symbol=symbol, user = session["user_id"])[0]['shares']

        if stock < float(shares):
            return render_template("sell.html", z_index_enough_shares=1, symbols=symbols)

        else:
            after_shares = stock - shares
            if after_shares == 0:
                db.execute("DELETE FROM stocks WHERE symbol = :symbol AND user_id = :user", symbol=symbol, user = session["user_id"])

            else:
                db.execute("UPDATE stocks SET shares = :shares WHERE symbol = :symbol AND user_id = :user", shares = after_shares, symbol=symbol, user=session["user_id"])

            db.execute("UPDATE users SET cash = :cash WHERE id = :user", cash = after_cash, user=session["user_id"])

            db.execute("INSERT INTO transactions(user_id, symbol, shares, value) VALUES(:user, :symbol, :shares, :value)", user=session["user_id"], symbol=symbol, shares=-shares, value= price*float(shares))

        flash("Sold!")
        return redirect("/index")

    else:
        symbols = db.execute("SELECT symbol FROM stocks WHERE user_id = :user", user=session["user_id"])

        return render_template("sell.html", symbols=symbols)

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":
        stock = lookup(request.form.get("symbol"))

        if not stock:
            return render_template("quote.html", z_index_s=1)
        else:
            stock['price']=usd(stock['price'])
            return render_template("quote.html", stock=stock)
    else:
        return render_template("quote.html", stock="")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    rows = db.execute("SELECT * FROM transactions WHERE user_id = :user",
                            user=session["user_id"])

    transactions = []
    for row in rows:

        transactions.append(list((row['symbol'], row['shares'], row['value'], row['date'])))

    for transaction in transactions:
        transaction[2] = usd(transaction[2])

    return render_template("history.html", transactions=transactions)



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

