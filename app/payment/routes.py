from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
import os
from app.extensions import db
from app.models.transaction import Transaction
from app.models.arf import Subscription, ARFAsset
from app.payment.orange_money import OrangeMoneyAPI, OrangeMoneySimulator
from app.payment.mtn_momo import MTNMoMoAPI, MTNMoMoSimulator

payment_bp = Blueprint('payment', __name__, url_prefix='/payment')

USE_SIMULATION = os.environ.get('PAYMENT_SIMULATION', 'true').lower() == 'true'


def get_orange_client():
    if USE_SIMULATION:
        return OrangeMoneySimulator()
    return OrangeMoneyAPI(
        client_id=os.environ.get('ORANGE_CLIENT_ID', ''),
        client_secret=os.environ.get('ORANGE_CLIENT_SECRET', ''),
        merchant_key=os.environ.get('ORANGE_MERCHANT_KEY', '')
    )


def get_mtn_client():
    if USE_SIMULATION:
        return MTNMoMoSimulator()
    return MTNMoMoAPI(
        api_user=os.environ.get('MTN_API_USER', ''),
        api_key=os.environ.get('MTN_API_KEY', ''),
        subscription_key=os.environ.get('MTN_SUBSCRIPTION_KEY', ''),
        environment=os.environ.get('MTN_ENVIRONMENT', 'sandbox')
    )


@payment_bp.route('/initiate/<int:subscription_id>', methods=['POST'])
@login_required
def initiate(subscription_id):
    subscription = Subscription.query.get_or_404(subscription_id)

    if subscription.user_id != current_user.id:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('member.dashboard'))

    if subscription.status != 'pending':
        flash('Cette transaction est déjà traitée.', 'info')
        return redirect(url_for('member.portfolio'))

    reference = Transaction.generate_reference()
    transaction = Transaction(
        user_id=current_user.id,
        subscription_id=subscription.id,
        type='subscription',
        amount=subscription.amount,
        currency='XOF',
        payment_method=subscription.payment_method,
        phone_number=subscription.phone_number,
        reference=reference,
        status='processing'
    )
    db.session.add(transaction)
    db.session.commit()

    if subscription.payment_method == 'orange_money':
        client = get_orange_client()
        result = client.initiate_payment(
            amount=float(subscription.amount),
            phone_number=subscription.phone_number,
            order_id=reference,
            description=f'ARF: {subscription.arf.name}'
        )
    elif subscription.payment_method == 'mtn_momo':
        client = get_mtn_client()
        result = client.request_to_pay(
            amount=float(subscription.amount),
            phone_number=subscription.phone_number,
            external_id=reference,
            payer_message=f'Investir dans {subscription.arf.name}'
        )
    else:
        result = {'status': 'error', 'message': 'Méthode de paiement inconnue'}

    if result.get('status') == 'success':
        if result.get('simulated'):
            transaction.status = 'completed'
            subscription.status = 'completed'
            db.session.commit()
            flash(f'Paiement simulé avec succès ! Référence: {reference}', 'success')
            return redirect(url_for('member.portfolio'))
        else:
            transaction.provider_ref = result.get('pay_token') or result.get('reference_id')
            db.session.commit()
            payment_url = result.get('payment_url')
            if payment_url:
                return redirect(payment_url)
            flash('Paiement initié. Vérifiez votre téléphone pour confirmer.', 'info')
            return redirect(url_for('payment.status', reference=reference))
    else:
        transaction.status = 'failed'
        transaction.failure_reason = result.get('message', 'Erreur inconnue')
        db.session.commit()
        flash(f'Erreur de paiement: {result.get("message")}', 'danger')
        return redirect(url_for('arf.detail', arf_id=subscription.arf_id))


@payment_bp.route('/status/<reference>')
@login_required
def status(reference):
    transaction = Transaction.query.filter_by(reference=reference).first_or_404()

    if transaction.user_id != current_user.id and not current_user.is_admin:
        flash('Accès non autorisé.', 'danger')
        return redirect(url_for('member.dashboard'))

    return render_template('payment/status.html', transaction=transaction)


@payment_bp.route('/history')
@login_required
def history():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    return render_template('payment/history.html', transactions=transactions)


# --- Webhooks callbacks ---
@payment_bp.route('/callback/orange', methods=['POST'])
def orange_callback():
    data = request.get_json() or request.form.to_dict()
    reference = data.get('order_id') or data.get('txnorderid')

    if reference:
        transaction = Transaction.query.filter_by(reference=reference).first()
        if transaction:
            status = data.get('status', '').upper()
            if status in ['SUCCESS', 'SUCCESSFUL', 'TXN_SUCCESSFUL']:
                transaction.status = 'completed'
                if transaction.subscription:
                    transaction.subscription.status = 'completed'
            elif status in ['FAILED', 'TXN_FAILED']:
                transaction.status = 'failed'
                transaction.failure_reason = data.get('reason', 'Paiement échoué')
            db.session.commit()

    return jsonify({'status': 'ok'}), 200


@payment_bp.route('/callback/mtn', methods=['POST'])
def mtn_callback():
    data = request.get_json() or request.form.to_dict()
    reference = data.get('externalId')

    if reference:
        transaction = Transaction.query.filter_by(reference=reference).first()
        if transaction:
            status = data.get('status', '').upper()
            if status in ['SUCCESSFUL', 'SUCCESS']:
                transaction.status = 'completed'
                if transaction.subscription:
                    transaction.subscription.status = 'completed'
            elif status in ['FAILED']:
                transaction.status = 'failed'
                transaction.failure_reason = data.get('reason', 'Paiement échoué')
            db.session.commit()

    return jsonify({'status': 'ok'}), 200


@payment_bp.route('/webhook/orange', methods=['POST'])
def orange_webhook():
    data = request.get_json() or {}
    reference = data.get('order_id')
    if reference:
        transaction = Transaction.query.filter_by(reference=reference).first()
        if transaction and transaction.status == 'processing':
            txn_status = data.get('txnstatus', '').upper()
            if txn_status == 'SUCCESS':
                transaction.status = 'completed'
                if transaction.subscription:
                    transaction.subscription.status = 'completed'
                db.session.commit()
    return jsonify({'status': 'ok'}), 200


@payment_bp.route('/webhook/mtn', methods=['POST'])
def mtn_webhook():
    data = request.get_json() or {}
    reference = data.get('externalId')
    if reference:
        transaction = Transaction.query.filter_by(reference=reference).first()
        if transaction and transaction.status == 'processing':
            txn_status = data.get('status', '').upper()
            if txn_status == 'SUCCESSFUL':
                transaction.status = 'completed'
                if transaction.subscription:
                    transaction.subscription.status = 'completed'
                db.session.commit()
    return jsonify({'status': 'ok'}), 200
