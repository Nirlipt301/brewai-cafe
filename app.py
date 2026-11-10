from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
import sqlite3, os, random, string, secrets
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-change-this-secret-before-deploy')
app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE='Lax', PERMANENT_SESSION_LIFETIME=timedelta(days=30))
DB = os.path.join(os.path.dirname(__file__), 'cafe.db')

# id, name, category, description, price, image filename, default availability
PRODUCTS = [
    (1,'Cappuccino','Coffee','Rich espresso with steamed milk',149,'cappuccino.jpg',1),
    (7,'Classic Americano','Coffee','Bold espresso topped with hot water',129,'americano.jpg',1),
    (8,'Cafe Mocha','Coffee','Espresso, chocolate and silky steamed milk',189,'mocha.jpg',1),
    (17,'Masala Chai','Tea','Indian spiced tea with milk and warming spices',99,'masala_chai.jpg',1),
    (10,'Mango Iced Tea','Tea','Refreshing mango tea over ice',159,'mango_iced_tea.jpg',1),
    (2,'Caramel Iced Latte','Cold Drinks','Espresso, caramel and chilled milk',199,'Caramel_Iced_Latte.jpg',1),
    (3,'Hazelnut Cold Coffee','Cold Drinks','Creamy cold coffee with hazelnut',209,'Hazelnut_Cold_Coffee.jpg',1),
    (9,'Vanilla Cold Brew','Cold Drinks','Slow brewed coffee with vanilla cream',219,'vanila_coldbrew.jpg',1),
    (4,'Veg Grilled Sandwich','Snacks','Grilled vegetables, cheese and herbs',169,'Grilled_Sandwich.jpg',1),
    (11,'Paneer Tikka Panini','Snacks','Spiced paneer, peppers and cheese',229,'panini.jpg',1),
    (12,'Cheesy Garlic Bread','Snacks','Toasted garlic bread with melted cheese',149,'garlic_bread.jpg',1),
    (18,'Peri Peri Fries','Snacks','Crispy fries tossed in peri peri seasoning',139,'periperi_fries.jpg',1),
    (19,'Loaded Nachos','Snacks','Nachos with cheese, salsa and vegetables',199,'nachos.jpg',1),
    (13,'Margherita Flatbread','Meals','Tomato, basil and mozzarella flatbread',249,'flatbread.jpg',1),
    (14,'Pesto Pasta Bowl','Meals','Creamy basil pesto pasta with vegetables',279,'pasta.jpg',1),
    (5,'Chocolate Brownie','Desserts','Warm, fudgy chocolate brownie',119,'Chocolate_Brownie.jpg',1),
    (6,'Chocolate Pastry','Desserts','Soft chocolate cake with ganache',139,'Chocolate_Pastry.jpg',1),
    (15,'Blueberry Cheesecake','Desserts','Creamy cheesecake with blueberry compote',179,'cheesecake.jpg',1),
    (16,'Tiramisu Cup','Desserts','Coffee-soaked sponge with mascarpone cream',189,'tiramisu.jpg',1),
    (20,'Red Velvet Slice','Desserts','Velvety cocoa cake with cream cheese',169,'slice.jpg',1),
]

META = {
  1:dict(temp='hot',taste=['strong','creamy'],diet='vegetarian',hunger='light'), 7:dict(temp='hot',taste=['strong'],diet='vegan',hunger='light'),
  8:dict(temp='hot',taste=['sweet','strong','creamy'],diet='vegetarian',hunger='light'),17:dict(temp='hot',taste=['sweet','strong'],diet='vegetarian',hunger='light'),
 10:dict(temp='cold',taste=['sweet','refreshing'],diet='vegan',hunger='light'),2:dict(temp='cold',taste=['sweet','creamy'],diet='vegetarian',hunger='light'),
  3:dict(temp='cold',taste=['sweet','strong'],diet='vegetarian',hunger='light'),9:dict(temp='cold',taste=['sweet','strong'],diet='vegetarian',hunger='light'),
  4:dict(temp='hot',taste=['savory'],diet='vegetarian',hunger='medium'),11:dict(temp='hot',taste=['savory'],diet='vegetarian',hunger='medium'),
 12:dict(temp='hot',taste=['savory'],diet='vegetarian',hunger='medium'),18:dict(temp='hot',taste=['savory','spicy'],diet='vegan',hunger='medium'),
 19:dict(temp='hot',taste=['savory'],diet='vegetarian',hunger='medium'),13:dict(temp='hot',taste=['savory'],diet='vegetarian',hunger='heavy'),
 14:dict(temp='hot',taste=['savory','creamy'],diet='vegetarian',hunger='heavy'),5:dict(temp='room',taste=['sweet'],diet='vegetarian',hunger='light'),
  6:dict(temp='room',taste=['sweet'],diet='vegetarian',hunger='light'),15:dict(temp='cold',taste=['sweet'],diet='vegetarian',hunger='light'),
 16:dict(temp='cold',taste=['sweet','strong'],diet='vegetarian',hunger='light'),20:dict(temp='cold',taste=['sweet'],diet='vegetarian',hunger='light'),
}
FREE_POINT_ITEMS = {1:'Cappuccino', 4:'Veg Grilled Sandwich', 5:'Chocolate Brownie', 3:'Hazelnut Cold Coffee'}

def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def column_names(con, table): return {r['name'] for r in con.execute(f'PRAGMA table_info({table})').fetchall()}
def ensure_column(con, table, name, definition):
    if name not in column_names(con, table): con.execute(f'ALTER TABLE {table} ADD COLUMN {name} {definition}')

def init_db():
    con=db(); c=con.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,phone TEXT,dob TEXT,password_hash TEXT NOT NULL,loyalty_points INTEGER DEFAULT 0,birthday_verified INTEGER DEFAULT 0,birthday_verified_at TEXT)''')
    ensure_column(con,'users','role',"TEXT NOT NULL DEFAULT 'customer'"); ensure_column(con,'users','active','INTEGER NOT NULL DEFAULT 1'); ensure_column(con,'users','created_at','DATETIME DEFAULT CURRENT_TIMESTAMP')
    c.execute('''CREATE TABLE IF NOT EXISTS addresses(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER NOT NULL,label TEXT DEFAULT 'Home',address TEXT NOT NULL,created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,order_number TEXT UNIQUE,total INTEGER,payment_method TEXT,status TEXT DEFAULT 'New',created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    for name,definition in [('order_type',"TEXT DEFAULT 'Delivery'"),('delivery_address','TEXT'),('discount','INTEGER DEFAULT 0'),('table_number','INTEGER')]: ensure_column(con,'orders',name,definition)
    c.execute('''CREATE TABLE IF NOT EXISTS order_items(id INTEGER PRIMARY KEY AUTOINCREMENT,order_id INTEGER NOT NULL,product_id INTEGER,product_name TEXT NOT NULL,quantity INTEGER NOT NULL,unit_price INTEGER NOT NULL,customization TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS wallet_transactions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,amount INTEGER,note TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS product_status(product_id INTEGER PRIMARY KEY,available INTEGER NOT NULL DEFAULT 1)''')
    c.execute('''CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,order_id INTEGER,rating INTEGER,review TEXT,sentiment TEXT,category TEXT,created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reward_redemptions(id INTEGER PRIMARY KEY AUTOINCREMENT,user_id INTEGER,reward_type TEXT,year INTEGER,order_id INTEGER,created_at DATETIME DEFAULT CURRENT_TIMESTAMP)''')
    for p in PRODUCTS: c.execute('INSERT OR IGNORE INTO product_status(product_id,available) VALUES(?,1)',(p[0],))
    staff=[('BrewAI Admin','admin@brewai.com','admin','BrewAIAdmin!26'),('Chef 1','chef1@brewai.com','chef','ChefOne!26'),('Chef 2','chef2@brewai.com','chef','ChefTwo!26'),('Chef 3','chef3@brewai.com','chef','ChefThree!26'),('Chef 4','chef4@brewai.com','chef','ChefFour!26'),('Chef 5','chef5@brewai.com','chef','ChefFive!26')]
    for n,e,r,pw in staff:
        if not c.execute('SELECT id FROM users WHERE email=?',(e,)).fetchone(): c.execute('INSERT INTO users(name,email,password_hash,role,active) VALUES(?,?,?,?,1)',(n,e,generate_password_hash(pw),r))
    con.commit(); con.close()
init_db()

def availability_map():
    con=db(); rows=con.execute('SELECT product_id,available FROM product_status').fetchall(); con.close(); return {r['product_id']:bool(r['available']) for r in rows}
def product_by_id(pid): return next((p for p in PRODUCTS if p[0]==pid),None)
def cart_entries(): return session.get('cart',[]) if isinstance(session.get('cart',[]),list) else []
def cart_count(): return sum(max(0,int(e.get('qty',0))) for e in cart_entries())

def customer_guard():
    if not session.get('user_id'):
        flash('Please login or create an account before adding items or placing an order.','error'); return redirect(url_for('login',next=request.path))
    if session.get('role')!='customer': abort(403)

def customization_for(p):
    size=request.form.get('size','Regular'); milk=request.form.get('milk','Regular'); sugar=request.form.get('sugar','1'); shot=request.form.get('extra_shot')=='yes'; addon=request.form.get('addon','None')
    extra=0; parts=[]
    if p[2] in ('Coffee','Cold Drinks','Tea'):
        parts += [size, f'{sugar} sugar', f'{milk} milk']
        if size=='Large': extra+=40
        if milk in ('Oat','Almond'): extra+=30
        if shot and p[2] in ('Coffee','Cold Drinks'): extra+=40; parts.append('Extra espresso shot')
    elif p[2] in ('Snacks','Meals') and addon!='None': extra+=30; parts.append(addon)
    return extra,' · '.join(parts)

def cart_details():
    items=[]; subtotal=0
    for e in cart_entries():
        p=product_by_id(int(e.get('pid',0)))
        if not p: continue
        qty=max(1,int(e.get('qty',1))); extra=max(0,int(e.get('extra',0))); unit=p[4]+extra; line=unit*qty
        items.append((e['key'],p,qty,line,unit,e.get('custom',''))); subtotal+=line
    delivery=0 if subtotal>=299 or subtotal==0 or session.get('table_number') else 30
    return items,subtotal,delivery,subtotal+delivery

def wallet_balance(uid):
    con=db(); row=con.execute('SELECT COALESCE(SUM(amount),0) balance FROM wallet_transactions WHERE user_id=?',(uid,)).fetchone(); con.close(); return row['balance'] if row else 0

def personalized_offer(uid):
    con=db()
    rows=con.execute('''SELECT oi.product_name,SUM(oi.quantity) qty FROM order_items oi JOIN orders o ON o.id=oi.order_id WHERE o.user_id=? AND o.status!='Cancelled' GROUP BY oi.product_name ORDER BY qty DESC LIMIT 1''',(uid,)).fetchall()
    con.close()
    if not rows: return 'Place your first order and BrewAI will start personalizing rewards for you.'
    favourite=rows[0]['product_name']
    p=next((x for x in PRODUCTS if x[1]==favourite),None)
    if not p: return f'You often choose {favourite}. Watch this space for a matching reward.'
    if p[2] in ('Coffee','Tea','Cold Drinks'): return f'Based on your orders, {favourite} is a favourite. Your next drink recommendation will prioritize similar flavours.'
    if p[2] in ('Desserts',): return f'You seem to enjoy {favourite}. BrewAI will prioritize dessert offers and pairings for you.'
    return f'You often order {favourite}. BrewAI will prioritize similar food and combo suggestions for you.'

def birthday_reward_eligible(user, con):
    if not user or not user['birthday_verified'] or not user['dob']: return False
    try:
        dob=datetime.strptime(user['dob'],'%Y-%m-%d').date(); today=date.today(); this_year=date(today.year,dob.month,dob.day)
    except ValueError: return False
    if abs((today-this_year).days)>3: return False
    used=con.execute("SELECT 1 FROM reward_redemptions WHERE user_id=? AND reward_type='birthday' AND year=?",(user['id'],today.year)).fetchone()
    return not bool(used)

@app.context_processor
def globals_():
    return {'cart_count':cart_count(),'wallet_balance':wallet_balance(session['user_id']) if session.get('user_id') else 0,'table_number':session.get('table_number')}

@app.route('/')
def home(): return render_template('index.html',products=PRODUCTS[:4],availability=availability_map())
@app.route('/menu')
def menu(): return render_template('menu.html',products=PRODUCTS,availability=availability_map())
@app.route('/rewards')
def rewards(): return render_template('rewards.html',personal_offer=personalized_offer(session['user_id']) if session.get('user_id') and session.get('role')=='customer' else None)
@app.route('/why-brewai')
def why_brewai(): return render_template('why_brewai.html')
@app.route('/table/<int:number>')
def table_order(number):
    if number<1 or number>50: abort(404)
    session['table_number']=number; flash(f'Table {number:02d} selected. Your order will go directly to the kitchen.','success'); return redirect(url_for('menu'))
@app.route('/table/clear')
def clear_table(): session.pop('table_number',None); return redirect(url_for('home'))

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); phone=request.form.get('phone','').strip(); dob=request.form.get('dob',''); pw=request.form.get('password','')
        if not name or '@' not in email or len(pw)<6: flash('Enter a valid name/email and a password of at least 6 characters.','error'); return render_template('register.html')
        try:
            con=db(); con.execute("INSERT INTO users(name,email,phone,dob,password_hash,role) VALUES(?,?,?,?,?,'customer')",(name,email,phone,dob,generate_password_hash(pw))); con.commit(); con.close(); flash('Account created. Please log in.','success'); return redirect(url_for('login'))
        except sqlite3.IntegrityError: flash('An account with that email already exists.','error')
    return render_template('register.html')

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        con=db(); user=con.execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').strip().lower(),)).fetchone(); con.close()
        if user and user['active'] and check_password_hash(user['password_hash'],request.form.get('password','')):
            if user['role']!='customer': flash('Staff accounts must use the Staff Portal login.','error'); return redirect(url_for('chef.staff_login'))
            table=session.get('table_number'); session.clear(); session.permanent=bool(request.form.get('remember')); session.update(user_id=user['id'],user_name=user['name'],role='customer')
            if table: session['table_number']=table
            flash('Welcome back!','success'); return redirect(request.args.get('next') or url_for('home'))
        flash('Invalid email or password.','error')
    return render_template('login.html')
@app.route('/logout')
def logout(): session.clear(); flash('You have been logged out.','success'); return redirect(url_for('home'))

@app.post('/cart/add/<int:pid>')
def add_cart(pid):
    guard=customer_guard()
    if guard:return guard
    p=product_by_id(pid)
    if not p: abort(404)
    if not availability_map().get(pid,True): flash(f'{p[1]} is currently out of stock.','error'); return redirect(request.referrer or url_for('menu'))
    extra,custom=customization_for(p); cart=cart_entries()
    same=next((e for e in cart if int(e['pid'])==pid and e.get('custom','')==custom and int(e.get('extra',0))==extra),None)
    if same: same['qty']=int(same.get('qty',1))+1
    else: cart.append({'key':secrets.token_hex(5),'pid':pid,'qty':1,'extra':extra,'custom':custom})
    session['cart']=cart; flash(f'{p[1]} added to your cart.','success'); return redirect(request.referrer or url_for('menu'))

@app.route('/cart')
def cart():
    guard=customer_guard()
    if guard:return guard
    items,subtotal,delivery,total=cart_details(); return render_template('cart.html',items=items,subtotal=subtotal,delivery=delivery,total=total)
@app.post('/cart/update/<key>/<action>')
def update_cart(key,action):
    guard=customer_guard()
    if guard:return guard
    cart=cart_entries(); entry=next((e for e in cart if e.get('key')==key),None)
    if not entry:return redirect(url_for('cart'))
    if action=='plus': entry['qty']=int(entry.get('qty',1))+1
    elif action=='minus': entry['qty']=int(entry.get('qty',1))-1
    elif action=='remove': entry['qty']=0
    else: abort(400)
    cart=[e for e in cart if int(e.get('qty',0))>0]; session['cart']=cart; return redirect(url_for('cart'))

@app.route('/ai-picks',methods=['GET','POST'])
def ai_picks():
    rec=None
    if request.method=='POST':
        pref={k:request.form.get(k,'') for k in ['category','mood','budget','temperature','taste','hunger','diet']}; surprise=request.form.get('surprise')=='yes'
        candidates=[p for p in PRODUCTS if availability_map().get(p[0],True)]; scored=[]
        for p in candidates:
            m=META[p[0]]; score=20; reasons=[]; cat=pref['category']
            catmatch=(cat in ('','Surprise Me') or cat==p[2] or (cat=='Cold Drink' and p[2] in ('Cold Drinks','Tea') and m['temp']=='cold') or (cat=='Food' and p[2] in ('Snacks','Meals')) or (cat=='Dessert' and p[2]=='Desserts'))
            if catmatch: score+=18
            elif not surprise: score-=15
            if pref['temperature'] in ('','any') or pref['temperature']==m['temp']: score+=14
            if pref['taste'] in ('','any') or pref['taste'] in m['taste']: score+=15
            if pref['hunger'] in ('','any') or pref['hunger']==m['hunger']: score+=10
            if pref['diet'] in ('','any') or pref['diet']==m['diet'] or (pref['diet']=='vegetarian' and m['diet']=='vegan'): score+=10
            b=pref['budget']; ok=(b in ('','any') or (b=='150' and p[4]<=150) or (b=='200' and p[4]<=200) or (b=='300' and p[4]<=300)); score += 8 if ok else -15
            moodmap={'Energy':['strong'],'Sweet':['sweet'],'Relax':['creamy','sweet'],'Healthy':['refreshing','savory']}
            if pref['mood'] and any(x in m['taste'] for x in moodmap.get(pref['mood'],[])): score+=10
            if surprise: score+=random.randint(0,4)
            scored.append((score,p))
        scored.sort(key=lambda x:x[0],reverse=True)
        if scored:
            score,p=scored[0]; pct=max(70,min(98,score)); bits=[]
            if pref['temperature'] not in ('','any'): bits.append(pref['temperature'])
            if pref['taste'] not in ('','any'): bits.append(pref['taste'])
            if pref['budget'] not in ('','any'): bits.append('under ₹'+pref['budget'])
            if pref['diet'] not in ('','any'): bits.append(pref['diet'])
            why=('You wanted something '+', '.join(bits)+'.' if bits else 'This best fits your overall preferences and the live menu.')
            rec=(p,pct,why)
    return render_template('ai_picks.html',recommendation=rec)

@app.route('/checkout')
def checkout():
    guard=customer_guard()
    if guard:return guard
    items,subtotal,delivery,total=cart_details()
    if not items: flash('Your cart is empty.','error'); return redirect(url_for('menu'))
    con=db(); user=con.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); addresses=con.execute('SELECT * FROM addresses WHERE user_id=? ORDER BY id DESC',(session['user_id'],)).fetchall(); birthday=birthday_reward_eligible(user,con); con.close()
    return render_template('checkout.html',items=items,subtotal=subtotal,delivery=delivery,total=total,user=user,addresses=addresses,birthday_eligible=birthday,free_point_items=FREE_POINT_ITEMS)

def unique_order_number(con):
    while True:
        n='BR'+''.join(random.choices(string.digits,k=6))
        if not con.execute('SELECT 1 FROM orders WHERE order_number=?',(n,)).fetchone(): return n

@app.post('/place-order')
def place_order():
    guard=customer_guard()
    if guard:return guard
    items,subtotal,delivery,total=cart_details()
    if not items: flash('Your cart is empty.','error'); return redirect(url_for('menu'))
    method=request.form.get('payment_method','cod'); discount=cashback=0; offer=[]
    if method not in {'cod','card','upi'}: abort(400)
    if method=='card':
        number=''.join(x for x in request.form.get('card_number','') if x.isdigit()); cvv=request.form.get('cvv',''); expiry=request.form.get('expiry','')
        if not request.form.get('card_name') or len(number)<12 or len(cvv)<3 or len(expiry)<4: flash('Enter complete demo card details. No card details are stored.','error'); return redirect(url_for('checkout'))
        issuer=request.form.get('card_offer','other')
        if issuer=='amex': cashback=min(round(total*.08),150); offer.append(f'₹{cashback} BrewWallet cashback earned (demo offer)')
        elif issuer=='hdfc': discount=min(round(total*.05),100); offer.append(f'₹{discount} instant discount applied (demo offer)')
    uid=session['user_id']; table=session.get('table_number'); order_type='Table Service' if table else request.form.get('order_type','Delivery')
    if order_type not in {'Delivery','Pickup','Table Service'}: abort(400)
    address=''
    if order_type=='Delivery':
        saved=request.form.get('saved_address','').strip(); typed=request.form.get('delivery_address','').strip(); address=typed or saved
        if not address: flash('Enter or select a delivery address.','error'); return redirect(url_for('checkout'))
    final=max(total-discount,0); con=db()
    try:
        user=con.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone(); num=unique_order_number(con)
        cur=con.execute('INSERT INTO orders(user_id,order_number,total,payment_method,status,order_type,delivery_address,discount,table_number) VALUES(?,?,?,?,?,?,?,?,?)',(uid,num,final,method,'New',order_type,address,discount,table)); oid=cur.lastrowid
        for key,p,q,line,unit,custom in items: con.execute('INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,customization) VALUES(?,?,?,?,?,?)',(oid,p[0],p[1],q,unit,custom))
        if subtotal>=499:
            con.execute("INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,customization) VALUES(?,?,?,?,?,?)",(oid,5,'Chocolate Brownie',1,0,'FREE ₹499 cart reward')); offer.append('Free Chocolate Brownie unlocked')
        reward_pid=request.form.get('points_reward','').strip()
        if reward_pid and int(user['loyalty_points'] or 0)>=500 and int(reward_pid) in FREE_POINT_ITEMS:
            rp=product_by_id(int(reward_pid)); con.execute('INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,customization) VALUES(?,?,?,?,?,?)',(oid,rp[0],rp[1],1,0,'FREE 500 BrewPoints reward')); con.execute('UPDATE users SET loyalty_points=loyalty_points-500 WHERE id=?',(uid,)); offer.append(f'500 BrewPoints redeemed for {rp[1]}')
        if subtotal>=199 and birthday_reward_eligible(user,con):
            con.execute("INSERT INTO order_items(order_id,product_id,product_name,quantity,unit_price,customization) VALUES(?,?,?,?,?,?)",(oid,6,'Chocolate Pastry',1,0,'FREE verified birthday reward')); con.execute("INSERT INTO reward_redemptions(user_id,reward_type,year,order_id) VALUES(?,'birthday',?,?)",(uid,date.today().year,oid)); offer.append('Verified birthday gift: free Chocolate Pastry')
        if cashback: con.execute('INSERT INTO wallet_transactions(user_id,amount,note) VALUES(?,?,?)',(uid,cashback,'AmEx demo cashback - '+num))
        earned=(final//100)*10; con.execute('UPDATE users SET loyalty_points=loyalty_points+? WHERE id=?',(earned,uid))
        if order_type=='Delivery' and request.form.get('save_address')=='yes' and request.form.get('delivery_address','').strip(): con.execute('INSERT INTO addresses(user_id,label,address) VALUES(?,?,?)',(uid,request.form.get('address_label','Home').strip() or 'Home',address))
        con.commit()
    except Exception:
        con.rollback(); con.close(); app.logger.exception('Order creation failed'); flash('We could not create the order. Please try again.','error'); return redirect(url_for('checkout'))
    con.close(); session['cart']=[]; return render_template('order_success.html',order_number=num,total=final,method=method,offer=' · '.join(offer),cashback=cashback,table_number=table)

@app.route('/orders')
def my_orders():
    guard=customer_guard()
    if guard:return guard
    con=db(); orders=[dict(r) for r in con.execute('SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC',(session['user_id'],)).fetchall()]
    for o in orders:o['items']=con.execute('SELECT * FROM order_items WHERE order_id=?',(o['id'],)).fetchall()
    con.close(); return render_template('orders.html',orders=orders)
@app.route('/profile')
def profile():
    guard=customer_guard()
    if guard:return guard
    con=db(); user=con.execute('SELECT id,name,email,phone,dob,loyalty_points,birthday_verified FROM users WHERE id=?',(session['user_id'],)).fetchone(); tx=con.execute('SELECT * FROM wallet_transactions WHERE user_id=? ORDER BY created_at DESC LIMIT 10',(session['user_id'],)).fetchall(); con.close(); return render_template('profile.html',user=user,transactions=tx,personal_offer=personalized_offer(session['user_id']))
@app.route('/birthday-verification',methods=['GET','POST'])
def birthday_verification():
    guard=customer_guard()
    if guard:return guard
    con=db(); user=con.execute('SELECT dob,birthday_verified FROM users WHERE id=?',(session['user_id'],)).fetchone()
    if user['birthday_verified']: con.close(); flash('Your birthday is already verified and locked.','success'); return redirect(url_for('profile'))
    if request.method=='POST':
        uploaded=request.files.get('id_proof'); id_dob=request.form.get('id_dob','')
        try:
            if not uploaded or not uploaded.filename: flash('Choose an ID proof file.','error'); return render_template('birthday_verification.html')
            ext=os.path.splitext(uploaded.filename.lower())[1]
            if ext not in {'.jpg','.jpeg','.png','.pdf'}: flash('Use a JPG, PNG or PDF ID proof.','error'); return render_template('birthday_verification.html')
            # Demo-safe lifecycle: consume only a bounded amount, persist nothing, then release the reference.
            uploaded.stream.read(5*1024*1024 + 1)
            if id_dob and user['dob'] and id_dob==user['dob']:
                con.execute('UPDATE users SET birthday_verified=1,birthday_verified_at=CURRENT_TIMESTAMP WHERE id=?',(session['user_id'],)); con.commit(); flash('Birthday verified. Your DOB is now locked.','success'); return redirect(url_for('profile'))
            flash('The DOB entered from the ID does not match your account DOB.','error')
        finally:
            if uploaded:
                try: uploaded.close()
                except Exception: pass
            uploaded=None
            con.close()
    else: con.close()
    return render_template('birthday_verification.html')
@app.route('/feedback/<int:order_id>',methods=['GET','POST'])
def feedback(order_id):
    guard=customer_guard()
    if guard:return guard
    con=db(); order=con.execute('SELECT * FROM orders WHERE id=? AND user_id=?',(order_id,session['user_id'])).fetchone()
    if not order:con.close(); abort(404)
    if request.method=='POST':
        try: rating=max(1,min(5,int(request.form.get('rating',5))))
        except ValueError: rating=5
        review=request.form.get('review','').strip(); low=review.lower(); neg=any(w in low for w in ['slow','late','bad','cold','delay','poor']); pos=any(w in low for w in ['good','great','amazing','love','tasty','nice','excellent']); sentiment='Mixed' if pos and neg else ('Negative' if neg else 'Positive' if pos or rating>=4 else 'Neutral'); category='Delivery' if any(w in low for w in ['delivery','late','delay']) else 'Food/Drink'; con.execute('INSERT INTO feedback(user_id,order_id,rating,review,sentiment,category) VALUES(?,?,?,?,?,?)',(session['user_id'],order_id,rating,review,sentiment,category)); con.commit(); con.close(); flash(f'Feedback saved. BrewAI sentiment: {sentiment}.','success'); return redirect(url_for('my_orders'))
    con.close(); return render_template('feedback.html',order=order)

from chef.routes import chef_bp
from admin.routes import admin_bp
app.register_blueprint(chef_bp); app.register_blueprint(admin_bp)

if __name__=='__main__': app.run(debug=True)
