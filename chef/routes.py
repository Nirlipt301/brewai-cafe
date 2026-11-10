from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash
from staff_auth import role_required

chef_bp=Blueprint('chef',__name__,url_prefix='/chef')
def get_db():
    from app import db
    return db()

def order_rows(statuses=None):
    con=get_db(); q='SELECT o.*,u.name customer_name FROM orders o LEFT JOIN users u ON u.id=o.user_id'; params=[]
    if statuses:q+=' WHERE o.status IN (%s)' % ','.join('?'*len(statuses)); params=list(statuses)
    q+=' ORDER BY o.created_at ASC'; orders=[dict(r) for r in con.execute(q,params).fetchall()]
    for o in orders:o['items']=con.execute('SELECT * FROM order_items WHERE order_id=?',(o['id'],)).fetchall()
    con.close(); return orders

@chef_bp.route('/login',methods=['GET','POST'])
def staff_login():
    if request.method=='POST':
        con=get_db(); user=con.execute("SELECT * FROM users WHERE email=? AND role='chef'",(request.form.get('email','').strip().lower(),)).fetchone(); con.close()
        if user and user['active'] and check_password_hash(user['password_hash'],request.form.get('password','')):
            session.clear(); session.update(user_id=user['id'],user_name=user['name'],role='chef'); return redirect(url_for('chef.dashboard'))
        flash('Invalid or inactive staff account.','error')
    return render_template('chef/login.html')

@chef_bp.route('/')
@role_required('chef')
def dashboard(): return render_template('chef/dashboard.html',orders=order_rows(['New','Preparing','Ready']))

@chef_bp.post('/orders/<int:oid>/status')
@role_required('chef')
def status(oid):
    allowed={'New':'Preparing','Preparing':'Ready','Ready':'Completed'}; con=get_db(); row=con.execute('SELECT status FROM orders WHERE id=?',(oid,)).fetchone()
    if not row: con.close(); abort(404)
    if row['status'] in allowed: con.execute('UPDATE orders SET status=? WHERE id=?',(allowed[row['status']],oid)); con.commit()
    con.close(); return redirect(url_for('chef.dashboard'))

@chef_bp.route('/availability')
@role_required('chef')
def availability():
    from app import PRODUCTS
    con=get_db(); states={r['product_id']:r['available'] for r in con.execute('SELECT * FROM product_status').fetchall()}; con.close(); return render_template('chef/availability.html',products=PRODUCTS,states=states)

@chef_bp.post('/availability/<int:pid>')
@role_required('chef')
def toggle_availability(pid):
    con=get_db(); row=con.execute('SELECT available FROM product_status WHERE product_id=?',(pid,)).fetchone()
    if not row: con.close(); abort(404)
    con.execute('UPDATE product_status SET available=? WHERE product_id=?',(0 if row['available'] else 1,pid)); con.commit(); con.close(); return redirect(url_for('chef.availability'))
