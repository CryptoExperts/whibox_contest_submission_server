import time

from datetime import datetime
from traceback import print_exc
from feedwerk.atom import AtomFeed
from flask import render_template, url_for, request, request_started
from flask_login import current_user

from app import app, db, login_manager
from app.models.user import User
from app.models.program import Program
from app.models.whiteboxbreak import WhiteboxBreak
from app.utils import crx_flash, redirect

from . import user, submit, challenge, breaks  # noqa


def need_to_check(url_rule):
    if url_rule.startswith('/static/') \
       or (url_rule.startswith('/user/') and url_rule != "/user/show") \
       or url_rule == '/rules' \
       or url_rule == '/submit/candidate':
        return False
    return True


def update_strawberries(sender, **extra):
    url_rule = str(request.url_rule)
    if not need_to_check(url_rule):
        return

    app.logger.info(f"Updating strawberries for {url_rule}")
    now = int(time.time())
    try:
        programs = Program.get_programs_requiring_update(now)

        # update the strawberries and carrots for each program
        for program in programs:
            program.update_strawberries(now)

        # refresh program and user ranking
        Program.refresh_all_strawberry_rankings()
        User.refresh_all_strawberry_rankings()

        db.session.commit()
    except:
        db.session.rollback()
        print_exc()


request_started.connect(update_strawberries, app)


@app.route('/', methods=['GET'])
def index():
    total_number_of_users = User.get_total_number_of_users()
    users = User.get_all_sorted_by_bananas()
    programs_to_plot = Program.get_all_published_sorted_by_ranking(
        max_rank=app.config['MAX_RANK_OF_PLOTED_CHALLENGES'])
    programs = Program.get_all_published_sorted_by_ranking()
    number_of_unbroken_programs = Program.get_number_of_unbroken_programs()
    number_of_broken_programs = Program.get_number_of_broken_programs()
    total_programs = number_of_broken_programs + number_of_unbroken_programs
    if not total_programs:
        broken_ratio = None
    else:
        broken_ratio = round(number_of_broken_programs*100 / total_programs)
    wb_breaks = WhiteboxBreak.get_all()
    programs_broken_by_current_user = None
    if current_user and current_user.is_authenticated:
        wb_breaks_by_current_user = WhiteboxBreak.get_all_by_user(current_user)
        programs_broken_by_current_user = [
            wb_break.program for wb_break in wb_breaks_by_current_user]

    return render_template(
        'index.html',
        active_page='index',
        users=users,
        total_number_of_users=total_number_of_users,
        programs=programs,
        wb_breaks=wb_breaks,
        programs_broken_by_current_user=programs_broken_by_current_user,
        number_of_unbroken_programs=number_of_unbroken_programs,
        number_of_broken_programs=number_of_broken_programs,
        broken_ratio=broken_ratio,
        programs_to_plot=programs_to_plot
    )


@app.route('/rules', methods=['GET'])
def rules():
    return render_template(
        'rules.html',
        active_page="rules",
        challenge_max_source_size_in_mb=app.config['CHALLENGE_MAX_SOURCE_SIZE_IN_MB'],
        challenge_max_mem_for_compilation_in_mb=app.config['CHALLENGE_MAX_MEM_COMPILATION_IN_MB'],
        challenge_max_time_for_compilation_in_secs=app.config[
            'CHALLENGE_MAX_TIME_COMPILATION_IN_SECS'],
        challenge_max_binary_size_in_mb=app.config['CHALLENGE_MAX_BINARY_SIZE_IN_MB'],
        challenge_max_mem_execution_in_mb=app.config['CHALLENGE_MAX_MEM_EXECUTION_IN_MB'],
        challenge_max_time_execution_in_secs=app.config['CHALLENGE_MAX_TIME_EXECUTION_IN_SECS'],
        use_math=True,
    )


@app.route('/rss.xml', methods=['GET'])
def recent_feed():
    feed = AtomFeed('WhibOx Contest 3nd Edition -- CHES 2021 Challenge',
                    feed_url=request.url, url=request.url_root,
                    author="WhibOx organizing committee",
                    subtitle="Submitted challenged order by published date descending"
                    )
    programs = Program.get_all_published_sorted_by_published_time()

    for program in programs:
        item_url = "%scandidate/%d" % (
            request.url_root, program._id)
        title = 'New challenge "<strong>%s</strong>" submitted' % program.funny_name
        author = program.user.nickname
        content = render_template('candidate.html', program=program, feed=True)

        if not author or not author.strip():
            author = program.user.username
        feed.add(id=item_url,
                 title=title,
                 title_type='html',
                 updated=datetime.fromtimestamp(program._timestamp_published),
                 author=author,
                 url=item_url,
                 categories=[{'term': program.status}],
                 content=content,
                 content_type='html',)
    return feed.get_response()


def unauthorized_handler():
    crx_flash('PLEASE_SIGN_IN')
    try:
        return redirect(url_for('user_login', next=url_for(request.endpoint)))
    except:
        return redirect(url_for('index'))


login_manager.unauthorized_handler(unauthorized_handler)
