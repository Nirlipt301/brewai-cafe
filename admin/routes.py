from flask import Blueprint, render_template, request, redirect, url_for, flash, abort, session
from werkzeug.security import generate_password_hash, check_password_hash
from staff_auth import role_required
admin_bp=Blueprint('admin',__name__,url_prefix='/admin'); MAX_CHEFS=5

def get_db():
    from app import db
    return db()

@admin_bp.route('/login',methods=['GET','POST'])
def admin_login():
    if request.method=='POST':
        con=get_db(); user=con.execute("SELECT * FROM users WHERE email=? AND role='admin'",(request.form.get('email','').strip().lower(),)).fetchone(); con.close()
        if user and user['active'] and check_password_hash(user['password_hash'],request.form.get('password','')):
            session.clear(); session.update(user_id=user['id'],user_name=user['name'],role='admin'); return redirect(url_for('admin.dashboard'))
        flash('Invalid or inactive admin account.','error')
    return render_template('admin/login.html')


@admin_bp.route('/')
@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    con=get_db()
    stats={
      'today_orders':con.execute("SELECT COUNT(*) n FROM orders WHERE date(created_at)=date('now','localtime')").fetchone()['n'],
      'today_sales':con.execute("SELECT COALESCE(SUM(total),0) n FROM orders WHERE date(created_at)=date('now','localtime') AND status!='Cancelled'").fetchone()['n'],
      'aov':con.execute("SELECT COALESCE(ROUND(AVG(total)),0) n FROM orders WHERE status!='Cancelled'").fetchone()['n'],
      'customers':con.execute("SELECT COUNT(*) n FROM users WHERE role='customer'").fetchone()['n'],
      'new_customers':con.execute("SELECT COUNT(*) n FROM users WHERE role='customer' AND created_at>=datetime('now','-7 days')").fetchone()['n'],
      'active_chefs':con.execute("SELECT COUNT(*) n FROM users WHERE role='chef' AND active=1").fetchone()['n']}
    pop=con.execute("SELECT product_name,SUM(quantity) qty FROM order_items GROUP BY product_name ORDER BY qty DESC LIMIT 5").fetchall(); stats['popular']=pop[0]['product_name'] if pop else 'No orders yet'
    recent=con.execute('SELECT o.*,u.name customer_name FROM orders o LEFT JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC LIMIT 10').fetchall()
    trend=con.execute("SELECT date(created_at) day,COALESCE(SUM(total),0) sales,COUNT(*) orders FROM orders WHERE created_at>=datetime('now','-6 days') AND status!='Cancelled' GROUP BY date(created_at) ORDER BY day").fetchall(); con.close()
    return render_template('admin/dashboard.html',stats=stats,recent=recent,popular=pop,trend=trend)

@admin_bp.route('/orders')
@role_required('admin')
def orders():
    con=get_db(); rows=[dict(r) for r in con.execute('SELECT o.*,u.name customer_name,u.email customer_email FROM orders o LEFT JOIN users u ON u.id=o.user_id ORDER BY o.created_at DESC').fetchall()]
    for o in rows:o['items']=con.execute('SELECT * FROM order_items WHERE order_id=?',(o['id'],)).fetchall()
    con.close(); return render_template('admin/orders.html',orders=rows)
@admin_bp.post('/orders/<int:oid>/cancel')
@role_required('admin')
def cancel_order(oid):
    con=get_db(); con.execute("UPDATE orders SET status='Cancelled' WHERE id=? AND status!='Completed'",(oid,)); con.commit(); con.close(); flash('Order cancelled.','success'); return redirect(url_for('admin.orders'))

@admin_bp.route('/customers')
@role_required('admin')
def customers():
    con=get_db(); rows=con.execute("SELECT u.id,u.name,u.email,u.phone,u.loyalty_points,u.birthday_verified,COUNT(o.id) orders,COALESCE(SUM(o.total),0) spent FROM users u LEFT JOIN orders o ON o.user_id=u.id WHERE u.role='customer' GROUP BY u.id ORDER BY u.id DESC").fetchall(); con.close(); return render_template('admin/customers.html',customers=rows)

@admin_bp.route('/chefs',methods=['GET','POST'])
@role_required('admin')
def chefs():
    con=get_db()
    if request.method=='POST':
        active=con.execute("SELECT COUNT(*) n FROM users WHERE role='chef' AND active=1").fetchone()['n']
        if active>=MAX_CHEFS: flash('Chef limit reached: BrewAI allows only 5 active chefs.','error')
        else:
            name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); password=request.form.get('password','')
            if not name or '@' not in email or len(password)<6: flash('Enter valid chef details and a password of at least 6 characters.','error')
            else:
                try:
                    existing=con.execute('SELECT id,role FROM users WHERE email=?',(email,)).fetchone()
                    if existing:
                        if existing['role']!='chef': raise ValueError('Email belongs to another account type.')
                        con.execute('UPDATE users SET name=?,password_hash=?,active=1 WHERE id=?',(name,generate_password_hash(password),existing['id']))
                    else: con.execute("INSERT INTO users(name,email,password_hash,role,active) VALUES(?,?,?,'chef',1)",(name,email,generate_password_hash(password)))
                    con.commit(); flash('Chef account added.','success')
                except Exception as e: con.rollback(); flash(str(e) or 'Could not add chef.','error')
    chefs=con.execute("SELECT id,name,email,active FROM users WHERE role='chef' ORDER BY id").fetchall(); active_count=sum(1 for c in chefs if c['active']); con.close(); return render_template('admin/chefs.html',chefs=chefs,active_count=active_count,max_chefs=MAX_CHEFS)
@admin_bp.post('/chefs/<int:uid>/remove')
@role_required('admin')
def remove_chef(uid):
    con=get_db(); con.execute("UPDATE users SET active=0 WHERE id=? AND role='chef'",(uid,)); con.commit(); con.close(); flash('Chef access removed.','success'); return redirect(url_for('admin.chefs'))

@admin_bp.route('/feedback')
@role_required('admin')
def feedback():
    con=get_db(); rows=con.execute('SELECT f.*,u.name customer_name,o.order_number FROM feedback f LEFT JOIN users u ON u.id=f.user_id LEFT JOIN orders o ON o.id=f.order_id ORDER BY f.created_at DESC').fetchall(); counts={r['sentiment']:r['n'] for r in con.execute('SELECT sentiment,COUNT(*) n FROM feedback GROUP BY sentiment').fetchall()}; cats=con.execute("SELECT category,COUNT(*) n FROM feedback WHERE sentiment IN ('Negative','Mixed') GROUP BY category ORDER BY n DESC").fetchall(); total=sum(counts.values()); negative=counts.get('Negative',0)+counts.get('Mixed',0); issue=cats[0]['category'] if cats else 'No recurring issue yet'; insight=(f'{negative} of {total} reviews are negative/mixed. Most common concern: {issue}.' if total else 'Collect more customer feedback to generate management insights.'); con.close(); return render_template('admin/feedback.html',feedback=rows,counts=counts,insight=insight)

@admin_bp.route('/products')
@role_required('admin')
def products():
    from app import PRODUCTS
    con=get_db(); states={r['product_id']:r['available'] for r in con.execute('SELECT * FROM product_status').fetchall()}; con.close(); return render_template('admin/products.html',products=PRODUCTS,states=states)
@admin_bp.post('/products/<int:pid>/toggle')
@role_required('admin')
def toggle_product(pid):
    con=get_db(); row=con.execute('SELECT available FROM product_status WHERE product_id=?',(pid,)).fetchone()
    if not row: con.close(); abort(404)
    con.execute('UPDATE product_status SET available=? WHERE product_id=?',(0 if row['available'] else 1,pid)); con.commit(); con.close(); return redirect(url_for('admin.products'))

@admin_bp.route('/table-qrs')
@role_required('admin')
def table_qrs(): return render_template('admin/table_qrs.html',tables=range(1,13))
