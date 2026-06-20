from app.blog import blog_bp


@blog_bp.route('/')
def index():
    return 'Blog - Coming soon'


@blog_bp.route('/<slug>')
def article(slug):
    return f'Article: {slug} - Coming soon'
