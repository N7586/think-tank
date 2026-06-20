from datetime import datetime
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.extensions import db
from app.models.meeting import Meeting, MeetingParticipant
from app.models.article import Article
from app.reseau.forms import MeetingForm, ArticleForm
from app.reseau import reseau_bp
from app.admin.routes import admin_required


# ========== HUB RESEAU ==========

@reseau_bp.route('/')
@login_required
def index():
    active_meetings = Meeting.query.filter_by(status='active').order_by(Meeting.created_at.desc()).all()
    recent_articles = Article.query.filter_by(status='published').order_by(Article.published_at.desc()).limit(6).all()
    pending_articles_count = Article.query.filter_by(status='pending').count() if current_user.is_admin else 0
    return render_template('reseau/index.html',
                           active_meetings=active_meetings,
                           recent_articles=recent_articles,
                           pending_articles_count=pending_articles_count)


# ========== REUNIONS ==========

@reseau_bp.route('/meetings')
@login_required
def meetings_list():
    active_meetings = Meeting.query.filter_by(status='active').order_by(Meeting.created_at.desc()).all()
    my_meetings = Meeting.query.filter_by(host_id=current_user.id).order_by(Meeting.created_at.desc()).all()
    return render_template('reseau/meetings/list.html',
                           active_meetings=active_meetings,
                           my_meetings=my_meetings)


@reseau_bp.route('/meetings/create', methods=['GET', 'POST'])
@login_required
def meetings_create():
    form = MeetingForm()
    if form.validate_on_submit():
        meeting = Meeting(
            title=form.title.data,
            description=form.description.data or '',
            host_id=current_user.id,
            status='active'
        )
        db.session.add(meeting)
        db.session.commit()

        participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=current_user.id,
            role='host'
        )
        db.session.add(participant)
        db.session.commit()

        flash('Reunion creee ! Vous etes maintenant l\'organisateur.', 'success')
        return redirect(url_for('reseau.meetings_room', room_id=meeting.room_id))

    return render_template('reseau/meetings/create.html', form=form)


@reseau_bp.route('/meetings/<room_id>')
@login_required
def meetings_room(room_id):
    meeting = Meeting.query.filter_by(room_id=room_id).first_or_404()

    if not meeting.is_active:
        flash('Cette reunion est terminee.', 'info')
        return redirect(url_for('reseau.meetings_list'))

    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id,
        user_id=current_user.id,
        is_kicked=False
    ).first()

    if not participant:
        participant = MeetingParticipant(
            meeting_id=meeting.id,
            user_id=current_user.id,
            role='host' if meeting.host_id == current_user.id else 'participant'
        )
        db.session.add(participant)
        db.session.commit()

    is_host = meeting.host_id == current_user.id
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id, is_kicked=False).all()

    return render_template('reseau/meetings/room.html',
                           meeting=meeting,
                           is_host=is_host,
                           participants=participants)


@reseau_bp.route('/meetings/<room_id>/end', methods=['POST'])
@login_required
def meetings_end(room_id):
    meeting = Meeting.query.filter_by(room_id=room_id).first_or_404()

    if meeting.host_id != current_user.id:
        flash('Seul l\'organisateur peut terminer la reunion.', 'danger')
        return redirect(url_for('reseau.meetings_room', room_id=room_id))

    meeting.status = 'ended'
    meeting.ended_at = datetime.utcnow()
    db.session.commit()

    flash('Reunion terminee avec succes.', 'success')
    return redirect(url_for('reseau.meetings_list'))


@reseau_bp.route('/meetings/<room_id>/participants')
@login_required
def meetings_participants(room_id):
    meeting = Meeting.query.filter_by(room_id=room_id).first_or_404()
    participants = MeetingParticipant.query.filter_by(meeting_id=meeting.id).all()
    return render_template('reseau/meetings/participants.html',
                           meeting=meeting, participants=participants)


@reseau_bp.route('/meetings/<room_id>/kick/<int:user_id>', methods=['POST'])
@login_required
def meetings_kick(room_id, user_id):
    meeting = Meeting.query.filter_by(room_id=room_id).first_or_404()

    if meeting.host_id != current_user.id:
        flash('Seul l\'organisateur peut expulser un participant.', 'danger')
        return redirect(url_for('reseau.meetings_room', room_id=room_id))

    participant = MeetingParticipant.query.filter_by(
        meeting_id=meeting.id, user_id=user_id
    ).first()

    if participant:
        participant.is_kicked = True
        participant.left_at = datetime.utcnow()
        db.session.commit()
        flash('Participant expulse de la reunion.', 'success')

    return redirect(url_for('reseau.meetings_participants', room_id=room_id))


# ========== ARTICLES ==========

@reseau_bp.route('/articles')
@login_required
def articles_list():
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category', '', type=str)

    query = Article.query.filter_by(status='published')
    if category:
        query = query.filter_by(category=category)

    articles = query.order_by(Article.published_at.desc()).paginate(page=page, per_page=9)
    return render_template('reseau/articles/list.html', articles=articles, category=category)


@reseau_bp.route('/articles/<int:article_id>')
@login_required
def articles_detail(article_id):
    article = Article.query.get_or_404(article_id)
    article.views += 1
    db.session.commit()
    return render_template('reseau/articles/detail.html', article=article)


@reseau_bp.route('/articles/create', methods=['GET', 'POST'])
@login_required
def articles_create():
    form = ArticleForm()
    if form.validate_on_submit():
        article = Article(
            user_id=current_user.id,
            title=form.title.data,
            content=form.content.data,
            category=form.category.data,
            status='pending'
        )
        db.session.add(article)
        db.session.commit()
        flash('Votre article a ete soumis pour validation par un administrateur.', 'info')
        return redirect(url_for('reseau.articles_my'))

    return render_template('reseau/articles/create.html', form=form)


@reseau_bp.route('/articles/my')
@login_required
def articles_my():
    articles = Article.query.filter_by(user_id=current_user.id).order_by(Article.created_at.desc()).all()
    return render_template('reseau/articles/my_articles.html', articles=articles)


# ========== ADMIN ARTICLES ==========

@reseau_bp.route('/admin/articles')
@admin_required
def admin_articles():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)

    query = Article.query
    if status_filter:
        query = query.filter_by(status=status_filter)

    articles = query.order_by(Article.created_at.desc()).paginate(page=page, per_page=15)
    return render_template('reseau/admin/articles.html', articles=articles, status_filter=status_filter)


@reseau_bp.route('/admin/articles/<int:article_id>/review', methods=['POST'])
@admin_required
def admin_review_article(article_id):
    article = Article.query.get_or_404(article_id)
    action = request.form.get('action', '')
    comment = request.form.get('comment', '')

    if action == 'publish':
        article.status = 'published'
        article.published_at = datetime.utcnow()
        article.admin_comment = comment
        db.session.commit()
        flash(f'Article "{article.title}" publie avec succes !', 'success')
    elif action == 'reject':
        article.status = 'rejected'
        article.admin_comment = comment
        db.session.commit()
        flash(f'Article "{article.title}" rejete.', 'warning')
    elif action == 'archive':
        article.status = 'archived'
        article.admin_comment = comment
        db.session.commit()
        flash(f'Article "{article.title}" archive.', 'info')

    return redirect(url_for('reseau.admin_articles'))
