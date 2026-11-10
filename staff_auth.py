from functools import wraps
from flask import session, redirect, url_for, flash, abort

def role_required(role):
    def deco(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            if not session.get('user_id'):
                flash('Staff sign-in required.', 'error')
                return redirect(url_for('admin.admin_login') if role=='admin' else url_for('chef.staff_login'))
            if session.get('role') != role:
                abort(403)
            return fn(*args, **kwargs)
        return wrapped
    return deco
