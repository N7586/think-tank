from flask import render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models.user import User
from app.auth.forms import LoginForm, RegisterForm, AdminRegisterForm
from app.auth import auth_bp
from app.config import Config

MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_MINUTES = 15
ADMIN_CODE = '12345'
ADMIN_CODE_ATTEMPTS = 3


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.is_admin:
            if not session.get('admin_verified'):
                return redirect(url_for('auth.admin_verify'))
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('member.dashboard'))

    login_attempts = session.get('login_attempts', 0)
    lockout_until = session.get('lockout_until', None)

    if lockout_until:
        from datetime import datetime as dt
        try:
            lockout_time = dt.fromisoformat(lockout_until)
            if dt.utcnow() < lockout_time:
                remaining = (lockout_time - dt.utcnow()).seconds // 60 + 1
                flash(f'Trop de tentatives. Réessayez dans {remaining} minute(s).', 'danger')
                return render_template('auth/login.html', form=LoginForm())
            else:
                session.pop('lockout_until', None)
                session['login_attempts'] = 0
                login_attempts = 0
        except (ValueError, TypeError):
            session.pop('lockout_until', None)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Votre compte a été bloqué. Contactez l\'administrateur.', 'danger')
                return render_template('auth/login.html', form=form)
            session.pop('login_attempts', None)
            session.pop('lockout_until', None)
            login_user(user, remember=form.remember.data)
            user.last_login = datetime.utcnow()
            db.session.commit()
            flash(f'Bienvenue {user.first_name} !', 'success')
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            if user.is_admin:
                session.pop('admin_verified', None)
                return redirect(url_for('auth.admin_verify'))
            return redirect(url_for('member.dashboard'))
        else:
            login_attempts += 1
            session['login_attempts'] = login_attempts
            if login_attempts >= MAX_LOGIN_ATTEMPTS:
                from datetime import datetime as dt, timedelta
                lockout_time = dt.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                session['lockout_until'] = lockout_time.isoformat()
                flash(f'Trop de tentatives. Compte verrouillé pour {LOCKOUT_MINUTES} minutes.', 'danger')
            else:
                remaining = MAX_LOGIN_ATTEMPTS - login_attempts
                flash(f'Email ou mot de passe incorrect. ({remaining} tentative(s) restante(s))', 'danger')

    return render_template('auth/login.html', form=form)


@auth_bp.route('/admin/verify', methods=['GET', 'POST'])
def admin_verify():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('auth.login'))

    if session.get('admin_verified'):
        return redirect(url_for('admin.dashboard'))

    code_attempts = session.get('admin_code_attempts', 0)
    lockout_until = session.get('admin_code_lockout', None)

    if lockout_until:
        from datetime import datetime as dt
        try:
            lockout_time = dt.fromisoformat(lockout_until)
            if dt.utcnow() < lockout_time:
                remaining = (lockout_time - dt.utcnow()).seconds // 60 + 1
                flash(f'Trop de tentatives. Réessayez dans {remaining} minute(s).', 'danger')
                return render_template('auth/admin_verify.html')
            else:
                session.pop('admin_code_lockout', None)
                session['admin_code_attempts'] = 0
                code_attempts = 0
        except (ValueError, TypeError):
            session.pop('admin_code_lockout', None)

    if request.method == 'POST':
        code = request.form.get('code', '').strip()
        if code == ADMIN_CODE:
            session['admin_verified'] = True
            session.pop('admin_code_attempts', None)
            session.pop('admin_code_lockout', None)
            flash('Code de securite verifie. Acces admin autorise.', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            code_attempts += 1
            session['admin_code_attempts'] = code_attempts
            if code_attempts >= ADMIN_CODE_ATTEMPTS:
                from datetime import datetime as dt, timedelta
                lockout_time = dt.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                session['admin_code_lockout'] = lockout_time.isoformat()
                flash(f'Trop de tentatives incorrectes. Compte verrouille pour {LOCKOUT_MINUTES} minutes.', 'danger')
                logout_user()
                return redirect(url_for('auth.login'))
            else:
                remaining = ADMIN_CODE_ATTEMPTS - code_attempts
                flash(f'Code incorrect. ({remaining} tentative(s) restante(s))', 'danger')

    return render_template('auth/admin_verify.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            email=form.email.data,
            phone=form.phone.data,
            language=form.language.data,
            role='user'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Compte créé avec succès ! Vous pouvez vous connecter.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('main.home'))


# --- Admin Code Verification ---
@auth_bp.route('/<secret_path>/register', methods=['GET', 'POST'])
def admin_register(secret_path):
    if secret_path != Config.ADMIN_SECRET_PATH:
        flash('Page introuvable.', 'danger')
        return redirect(url_for('main.home'))

    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    # Check if code was already verified in this session
    if session.get('admin_code_verified'):
        form = AdminRegisterForm()
        if form.validate_on_submit():
            user = User(
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                phone=form.phone.data,
                role='admin'
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            session.pop('admin_code_verified', None)
            flash('Compte administrateur créé avec succès !', 'success')
            return redirect(url_for('auth.login'))
        return render_template('auth/admin_register.html', form=form)

    # Code verification step
    code_attempts = session.get('admin_code_attempts', 0)
    lockout_until = session.get('admin_lockout_until', None)

    if lockout_until:
        from datetime import datetime as dt
        try:
            lockout_time = dt.fromisoformat(lockout_until)
            if dt.utcnow() < lockout_time:
                remaining = (lockout_time - dt.utcnow()).seconds // 60 + 1
                flash(f'Trop de tentatives. Réessayez dans {remaining} minute(s).', 'danger')
                return render_template('auth/admin_code.html')
            else:
                session.pop('admin_lockout_until', None)
                session['admin_code_attempts'] = 0
        except (ValueError, TypeError):
            session.pop('admin_lockout_until', None)

    if request.method == 'POST':
        code = request.form.get('admin_code', '')
        if code == ADMIN_CODE:
            session['admin_code_verified'] = True
            session.pop('admin_code_attempts', None)
            session.pop('admin_lockout_until', None)
            flash('Code vérifié. Créez votre compte administrateur.', 'success')
            return redirect(url_for('auth.admin_register', secret_path=secret_path))
        else:
            code_attempts += 1
            session['admin_code_attempts'] = code_attempts
            if code_attempts >= 5:
                from datetime import datetime as dt, timedelta
                lockout_time = dt.utcnow() + timedelta(minutes=15)
                session['admin_lockout_until'] = lockout_time.isoformat()
                flash('Code incorrect. Verrouillé pour 15 minutes.', 'danger')
            else:
                remaining = 5 - code_attempts
                flash(f'Code incorrect. ({remaining} tentative(s) restante(s))', 'danger')

    return render_template('auth/admin_code.html')
