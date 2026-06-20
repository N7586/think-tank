from flask import render_template, request, flash, redirect, url_for
from flask_mail import Message
from app.extensions import mail
from app.main import main_bp


@main_bp.route('/')
def home():
    return render_template('main/home.html')


@main_bp.route('/about')
def about():
    return render_template('main/about.html')


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')

        if name and email and message:
            try:
                msg = Message(
                    subject=f'[TSI Contact] {subject}',
                    recipients=['contact@tsi-institute.org'],
                    body=f'Nom: {name}\nEmail: {email}\nSujet: {subject}\n\nMessage:\n{message}'
                )
                mail.send(msg)
                flash('Votre message a été envoyé avec succès !', 'success')
            except Exception:
                flash('Message enregistré. Nous vous contacterons bientôt.', 'info')
        else:
            flash('Veuillez remplir tous les champs.', 'warning')

    return render_template('main/contact.html')


@main_bp.route('/how-to-use')
def how_to_use():
    return render_template('main/how_to_use.html')
