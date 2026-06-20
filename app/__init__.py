from flask import Flask, request, session, render_template
from flask_babel import Babel
from app.config import config
from app.extensions import db, login_manager, mail, migrate

babel = Babel()


def get_locale():
    if 'language' in session:
        return session['language']
    return request.accept_languages.best_match(['fr', 'en'], 'fr')


def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    babel.init_app(app, locale_selector=get_locale)

    with app.app_context():
        from app.models import User, ARFAsset, Subscription, MarketplaceOffer, Transaction, Meeting, MeetingParticipant, Article
        db.create_all()

    @app.after_request
    def set_security_headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        return response

    @app.before_request
    def set_language():
        if 'language' not in session:
            session['language'] = 'fr'

    @app.route('/set-language/<language>')
    def set_lang(language):
        if language in ['fr', 'en']:
            session['language'] = language
        return request.referrer or '/'

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template('errors/500.html'), 500

    from app.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    from app.auth import auth_bp
    from app.admin import admin_bp
    from app.main import main_bp
    from app.blog import blog_bp
    from app.arf import arf_bp
    from app.marketplace import marketplace_bp
    from app.simulator import simulator_bp
    from app.member import member_bp
    from app.payment.routes import payment_bp
    from app.reseau import reseau_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(blog_bp)
    app.register_blueprint(arf_bp)
    app.register_blueprint(marketplace_bp)
    app.register_blueprint(simulator_bp)
    app.register_blueprint(member_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(reseau_bp)

    return app
