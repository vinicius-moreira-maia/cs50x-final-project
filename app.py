import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
import datetime

from helpers import apology, login_required, lookup, usd

# Criando a aplicação Flask
app = Flask(__name__)

# Filtro para o Jinja
app.jinja_env.filters["usd"] = usd

# Configurando a sessão (Login)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Usando o módulo cs50 para criar o banco de dados SQLite
db = SQL("sqlite:///finance.db")

# checando o uso da chave da API (inserida via terminal)
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")

# implementado pelo cs50
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def index():

    # selecionando todas as transações
    transactions_list = db.execute('SELECT symbol, SUM(shares) AS shares, price FROM transactions WHERE user_id=? GROUP BY symbol', session['user_id'])

    # montando uma lista de dicionários com as informações atualizadas para apresentação de portfólio (baseada na consulta SQL acima)
    # assim é possível ver os lucros baseados nas flutuações das ações
    current = []
    grand_total = 0 # cash + shares * actual_price

    for line in transactions_list:
        actual_price = lookup(line['symbol'])
        actual_price = actual_price['price']
        shares = line['shares']
        name = lookup(line['symbol'])
        name = name['name']

        grand_total += shares * actual_price

        current.append({line['symbol']: shares, 'actual_price': usd(actual_price), 'name': name, 'total': usd(shares * actual_price)})

    # selecionando o caixa do usuário logado
    cash = db.execute('SELECT cash FROM users WHERE id = ?', session['user_id'])
    cash = cash[0]['cash']

    grand_total += cash

    return render_template("index.html", transactions_list=transactions_list, cash=usd(cash), current=current, grand_total=usd(grand_total))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    if request.method == 'POST':

        # recebendo os dados do formulário
        symbol = request.form.get('symbol')
        shares = int(request.form.get('shares'))

        # validando os dados recebidos
        if not shares or not symbol:
            return apology('all fields are required')

        if shares < 0:
            return apology('invalid share')

        # checando a existência ou não do símbolo
        stock_status = lookup(symbol.upper().strip())
        if not stock_status:
            return apology('not found')

        # vendo se há caixa o suficiente
        cash = db.execute('SELECT cash FROM users WHERE id=?', session['user_id'])
        cash = cash[0]['cash']

        transaction_value = stock_status['price'] * shares

        if cash < transaction_value:
            return apology('not enough cash')

        # atualizando o cash de users
        db.execute('UPDATE users SET cash=? WHERE id=?', cash - transaction_value, session['user_id'])

        # inserir nova transação
        date = datetime.datetime.now()
        db.execute("INSERT INTO transactions(user_id, symbol, shares, price, date) VALUES(?,?,?,?,?)", session['user_id'], stock_status['symbol'], shares, stock_status['price'], date)

        flash("Bought!")

        return redirect('/')

    else: # GET

        return render_template('buy.html')

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    transactions = db.execute('SELECT * FROM transactions WHERE user_id=? ORDER BY date DESC', session['user_id'])

    return render_template('history.html', transactions=transactions)

# implementado pelo cs50
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():

    if request.method == 'POST':

        # recebendo e validando os dados do formulário
        symbol = request.form.get('symbol')
        if not symbol:
            return apology("you must enter a stock's symbol")

        # checando a existência ou não do símbolo
        stock_status = lookup(symbol.upper().strip())
        if not stock_status:
            return apology('not found')

        return render_template('quoted.html', stock_status = stock_status)

    else: # GET

        return render_template('quote.html')

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == 'POST':

        # recebendo os dados do formulário
        username = request.form.get('username')
        password = request.form.get('password')
        confirmation = request.form.get('confirmation')

        # validando os dados do formulário
        if not username or not password or not confirmation:
            return apology('all fields are required')
        if password != confirmation:
            return apology("passwords don't match")

        # ver se o username já existe
        username_db = db.execute('SELECT * FROM users WHERE username=?', username)
        if len(username_db) != 0:
            return apology('username already exist')

        # cadastrando novo usuario no banco
        hash = generate_password_hash(password)
        db.execute("INSERT INTO users(username, hash) VALUES(?,?)", username, hash)

        return redirect("/login")

    else: # GET

        return render_template("register.html")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == 'POST':
        # recebendo os dados do formulário
        symbol = request.form.get('symbol')
        shares = int(request.form.get('shares'))

        # validando os dados recebidos
        if not shares or not symbol:
            return apology('all fields are required')

        if shares < 0:
            return apology('invalid share')

        # acessando o símbolo com os valores atualizados
        stock_status = lookup(symbol.upper().strip())
        if not stock_status:
            return apology('not found')

        # acessando o caixa do usuário
        cash = db.execute('SELECT cash FROM users WHERE id=?', session['user_id'])
        cash = cash[0]['cash']

        # vendo se o usuário possui a quantidade de ações que pretende vender
        user_shares = db.execute('SELECT shares FROM transactions WHERE user_id=? AND symbol=? GROUP BY symbol', session['user_id'], symbol)
        user_shares = user_shares[0]['shares']

        if shares > user_shares:
            return apology('not enough shares')

        transaction_value = stock_status['price'] * shares

        # atualizando o cash de users
        db.execute('UPDATE users SET cash=? WHERE id=?', cash + transaction_value, session['user_id'])

        # inserir nova transação
        date = datetime.datetime.now()
        db.execute("INSERT INTO transactions(user_id, symbol, shares, price, date) VALUES(?,?,?,?,?)", session['user_id'], stock_status['symbol'], (-1) * shares, stock_status['price'], date)

        flash("Sold!")

        return redirect('/')

    else : # GET
        symbols_user = db.execute('SELECT symbol FROM transactions WHERE user_id=? GROUP BY symbol HAVING SUM(shares) > 0', session['user_id'])

        return render_template('sell.html', symbols = [row['symbol'] for row in symbols_user])

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():

    if request.method == 'POST':

        # recebendo os dados do formulário
        new_password = request.form.get('new_password')
        confirmation = request.form.get('confirmation')

        # validando os dados do formulário
        if not confirmation or not new_password:
            return apology('all fields are required')
        if new_password != confirmation:
            return apology("new passwords don't match")

        # atualizando a senha
        new_hash = generate_password_hash(new_password)
        db.execute('UPDATE users SET hash = ? WHERE id = ?', new_hash, session['user_id'])

        # feedback para o usuário
        flash("Password changed!")

        return redirect("/")

    else: # GET

        return render_template("change.html")

