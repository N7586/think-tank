from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models.marketplace import MarketplaceOffer
from app.marketplace.forms import MarketplaceOfferForm
from app.marketplace import marketplace_bp
from app.admin.routes import admin_required


@marketplace_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    contract_type = request.args.get('type', '', type=str)
    status = request.args.get('status', '', type=str)

    query = MarketplaceOffer.query

    if contract_type:
        query = query.filter_by(contract_type=contract_type)
    if status:
        query = query.filter_by(status=status)
    else:
        query = query.filter_by(status='available')

    offers = query.order_by(MarketplaceOffer.created_at.desc()).paginate(page=page, per_page=12)

    return render_template('marketplace/index.html', offers=offers,
                           contract_type=contract_type, status=status)


@marketplace_bp.route('/<int:offer_id>')
def detail(offer_id):
    offer = MarketplaceOffer.query.get_or_404(offer_id)
    return render_template('marketplace/detail.html', offer=offer)


@marketplace_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = MarketplaceOfferForm()
    if form.validate_on_submit():
        deadline = None
        if form.deadline.data:
            try:
                deadline = datetime.strptime(form.deadline.data, '%Y-%m-%d').date()
            except ValueError:
                flash('Format de date invalide.', 'danger')
                return render_template('marketplace/create.html', form=form)

        offer = MarketplaceOffer(
            user_id=current_user.id,
            title=form.title.data,
            description=form.description.data,
            contract_type=form.contract_type.data,
            value=float(form.value.data),
            deadline=deadline,
            status='available'
        )
        db.session.add(offer)
        db.session.commit()
        flash('Votre offre a été publiée avec succès !', 'success')
        return redirect(url_for('marketplace.detail', offer_id=offer.id))

    return render_template('marketplace/create.html', form=form)


@marketplace_bp.route('/my-offers')
@login_required
def my_offers():
    offers = MarketplaceOffer.query.filter_by(user_id=current_user.id).order_by(MarketplaceOffer.created_at.desc()).all()
    return render_template('marketplace/my_offers.html', offers=offers)


# --- Admin ---
@marketplace_bp.route('/admin/list')
@admin_required
def admin_list():
    page = request.args.get('page', 1, type=int)
    offers = MarketplaceOffer.query.order_by(MarketplaceOffer.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('marketplace/admin_list.html', offers=offers)


@marketplace_bp.route('/admin/<int:offer_id>/delete', methods=['POST'])
@admin_required
def admin_delete(offer_id):
    offer = MarketplaceOffer.query.get_or_404(offer_id)
    title = offer.title
    db.session.delete(offer)
    db.session.commit()
    flash(f'Offre "{title}" supprimée.', 'success')
    return redirect(url_for('marketplace.admin_list'))


@marketplace_bp.route('/admin/<int:offer_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_status(offer_id):
    offer = MarketplaceOffer.query.get_or_404(offer_id)
    if offer.status == 'available':
        offer.status = 'sold'
        flash(f'Offre "{offer.title}" marquée comme vendue.', 'success')
    elif offer.status == 'sold':
        offer.status = 'available'
        flash(f'Offre "{offer.title}" remise en vente.', 'success')
    else:
        offer.status = 'available'
        flash(f'Offre "{offer.title}" réactivée.', 'success')
    db.session.commit()
    return redirect(url_for('marketplace.admin_list'))
