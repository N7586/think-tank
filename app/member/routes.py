from flask import render_template, redirect, url_for
from flask_login import login_required, current_user
from app.extensions import db
from app.models.arf import Subscription
from app.member import member_bp


@member_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    total_invested = sum(float(s.amount) for s in subscriptions if s.status == 'completed')
    total_units = sum(s.units for s in subscriptions if s.status == 'completed')

    return render_template('member/dashboard.html',
                           subscriptions=subscriptions,
                           total_invested=total_invested,
                           total_units=total_units)


@member_bp.route('/portfolio')
@login_required
def portfolio():
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    return render_template('member/portfolio.html', subscriptions=subscriptions)


@member_bp.route('/transactions')
@login_required
def transactions():
    subscriptions = Subscription.query.filter_by(user_id=current_user.id).order_by(Subscription.created_at.desc()).all()
    return render_template('member/transactions.html', subscriptions=subscriptions)
