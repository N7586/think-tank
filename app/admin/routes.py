from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_required, current_user
from functools import wraps
from app.extensions import db
from app.models.user import User
from app.admin import admin_bp


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            flash('Acces reserve aux administrateurs.', 'danger')
            return redirect(url_for('main.home'))
        if not session.get('admin_verified'):
            flash('Veuillez d\'abord verifier votre code de securite.', 'warning')
            return redirect(url_for('auth.admin_verify'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_users = User.query.filter_by(role='user').count()
    active_users = User.query.filter_by(role='user', is_active=True).count()
    blocked_users = User.query.filter_by(role='user', is_active=False).count()
    total_admins = User.query.filter_by(role='admin').count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           active_users=active_users,
                           blocked_users=blocked_users,
                           total_admins=total_admins,
                           recent_users=recent_users)


@admin_bp.route('/users')
@admin_required
def users_list():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)

    query = User.query.filter_by(role='user')

    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                User.phone.ilike(f'%{search}%')
            )
        )

    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'blocked':
        query = query.filter_by(is_active=False)

    users = query.order_by(User.created_at.desc()).paginate(page=page, per_page=15)

    return render_template('admin/users/list.html', users=users, search=search, status_filter=status_filter)


@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/users/detail.html', user=user)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas modifier votre propre compte.', 'warning')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    user.is_active = not user.is_active
    db.session.commit()

    status = 'activé' if user.is_active else 'bloqué'
    flash(f'Le compte de {user.full_name} a été {status}.', 'success')
    return redirect(url_for('admin.user_detail', user_id=user_id))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Vous ne pouvez pas supprimer votre propre compte.', 'warning')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    name = user.full_name
    db.session.delete(user)
    db.session.commit()

    flash(f'L\'utilisateur {name} a été supprimé.', 'success')
    return redirect(url_for('admin.users_list'))


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.first_name = request.form.get('first_name', user.first_name)
        user.last_name = request.form.get('last_name', user.last_name)
        user.email = request.form.get('email', user.email)
        user.phone = request.form.get('phone', user.phone)
        user.language = request.form.get('language', user.language)

        new_password = request.form.get('new_password', '')
        if new_password and len(new_password) >= 6:
            user.set_password(new_password)

        db.session.commit()
        flash(f'Les informations de {user.full_name} ont été mises à jour.', 'success')
        return redirect(url_for('admin.user_detail', user_id=user_id))

    return render_template('admin/users/edit.html', user=user)
