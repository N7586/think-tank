from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.arf import ARFAsset, Subscription
from app.arf.forms import CreateARFForm, SubscribeForm
from app.arf import arf_bp
from app.admin.routes import admin_required


@arf_bp.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    sector = request.args.get('sector', '', type=str)
    risk = request.args.get('risk', '', type=str)
    country = request.args.get('country', '', type=str)

    query = ARFAsset.query.filter_by(status='active')

    if sector:
        query = query.filter_by(sector=sector)
    if risk:
        query = query.filter_by(risk_level=risk)
    if country:
        query = query.filter_by(country=country)

    arfs = query.order_by(ARFAsset.created_at.desc()).paginate(page=page, per_page=9)

    countries = db.session.query(ARFAsset.country).distinct().all()
    countries = [c[0] for c in countries]

    return render_template('arf/index.html', arfs=arfs, sector=sector, risk=risk,
                           country=country, countries=countries)


@arf_bp.route('/<int:arf_id>')
def detail(arf_id):
    arf = ARFAsset.query.get_or_404(arf_id)
    form = SubscribeForm() if current_user.is_authenticated else None
    return render_template('arf/detail.html', arf=arf, form=form)


@arf_bp.route('/<int:arf_id>/subscribe', methods=['POST'])
@login_required
def subscribe(arf_id):
    arf = ARFAsset.query.get_or_404(arf_id)

    if arf.status != 'active':
        flash('Cet ARF n\'est plus disponible.', 'danger')
        return redirect(url_for('arf.detail', arf_id=arf_id))

    form = SubscribeForm()
    if form.validate_on_submit():
        try:
            units = int(form.units.data)
        except (ValueError, TypeError):
            flash('Nombre de tikecs invalide.', 'danger')
            return redirect(url_for('arf.detail', arf_id=arf_id))

        if units <= 0:
            flash('Le nombre de tikecs doit être supérieur à 0.', 'danger')
            return redirect(url_for('arf.detail', arf_id=arf_id))

        if units > arf.units_available:
            flash(f'Il ne reste que {arf.units_available} tikecs disponibles.', 'danger')
            return redirect(url_for('arf.detail', arf_id=arf_id))

        amount = float(arf.unit_price) * units

        subscription = Subscription(
            user_id=current_user.id,
            arf_id=arf.id,
            units=units,
            amount=amount,
            payment_method=form.payment_method.data,
            phone_number=form.phone_number.data,
            status='pending'
        )

        arf.units_sold += units

        db.session.add(subscription)
        db.session.commit()

        flash(f'Souscription de {units} tikec(s) pour {amount:.2f} € enregistrée. Procédez au paiement.', 'success')
        return redirect(url_for('payment.initiate', subscription_id=subscription.id))

    flash('Erreur dans le formulaire. Veuillez réessayer.', 'danger')
    return redirect(url_for('arf.detail', arf_id=arf_id))


# --- Admin ARF CRUD ---
@arf_bp.route('/admin/create', methods=['GET', 'POST'])
@admin_required
def admin_create():
    form = CreateARFForm()
    if form.validate_on_submit():
        total_value = float(form.total_value.data)
        unit_price = float(form.unit_price.data)
        total_units = int(total_value / unit_price)

        arf = ARFAsset(
            name=form.name.data,
            description=form.description.data,
            sector=form.sector.data,
            country=form.country.data,
            total_value=total_value,
            unit_price=unit_price,
            total_units=total_units,
            expected_return=float(form.expected_return.data),
            risk_level=form.risk_level.data,
            status='active',
            created_by=current_user.id
        )
        db.session.add(arf)
        db.session.commit()
        flash(f'ARF "{arf.name}" créée avec succès !', 'success')
        return redirect(url_for('arf.admin_list'))

    return render_template('arf/admin_create.html', form=form)


@arf_bp.route('/admin/list')
@admin_required
def admin_list():
    page = request.args.get('page', 1, type=int)
    arfs = ARFAsset.query.order_by(ARFAsset.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('arf/admin_list.html', arfs=arfs)


@arf_bp.route('/admin/<int:arf_id>/edit', methods=['GET', 'POST'])
@admin_required
def admin_edit(arf_id):
    arf = ARFAsset.query.get_or_404(arf_id)
    form = CreateARFForm(obj=arf)

    if form.validate_on_submit():
        arf.name = form.name.data
        arf.description = form.description.data
        arf.sector = form.sector.data
        arf.country = form.country.data
        arf.total_value = float(form.total_value.data)
        arf.unit_price = float(form.unit_price.data)
        arf.total_units = int(arf.total_value / arf.unit_price)
        arf.expected_return = float(form.expected_return.data)
        arf.risk_level = form.risk_level.data

        db.session.commit()
        flash(f'ARF "{arf.name}" mise à jour.', 'success')
        return redirect(url_for('arf.admin_list'))

    return render_template('arf/admin_edit.html', form=form, arf=arf)


@arf_bp.route('/admin/<int:arf_id>/delete', methods=['POST'])
@admin_required
def admin_delete(arf_id):
    arf = ARFAsset.query.get_or_404(arf_id)
    name = arf.name
    db.session.delete(arf)
    db.session.commit()
    flash(f'ARF "{name}" supprimée.', 'success')
    return redirect(url_for('arf.admin_list'))


@arf_bp.route('/admin/<int:arf_id>/toggle-status', methods=['POST'])
@admin_required
def admin_toggle_status(arf_id):
    arf = ARFAsset.query.get_or_404(arf_id)
    if arf.status == 'active':
        arf.status = 'closed'
        flash(f'ARF "{arf.name}" fermée.', 'warning')
    else:
        arf.status = 'active'
        flash(f'ARF "{arf.name}" réactivée.', 'success')
    db.session.commit()
    return redirect(url_for('arf.admin_list'))
