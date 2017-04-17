import datetime
import html
import logging
import os
import threading
from logging import Formatter

import MySQLdb
import requests
from flask import Flask, request, render_template, Markup
from messengerbot import MessengerClient, attachments, templates, elements

import messages
import quick_replies

# wp parse sample = site_domain + 'wp-json/wp/v2/posts?tags=38&per_page=5'
app = Flask(__name__, static_folder='web/static', template_folder='web')
admin_pass = 'LYb25FwFO7zOjUO5zafgiTiyIyRbVNwqeIj'


def get_posts(category_id):
    resp = requests.get(f'http://www.radioone.fm/wp-json/wp/v2/posts?categories={category_id}&per_page=5').json()
    all_elem = []
    for i in resp:
        img_attach = requests.get(i['_links']['wp:attachment'][0]['href']).json()
        if img_attach:
            img = img_attach[0]['source_url']
        else:
            img_media = requests.get(i['_links']['wp:featuredmedia'][0]['href']).json()
            img = img_media['source_url'] if 'source_url' in img_media \
                else 'http://www.radioone.fm/wp-content/uploads/2017/04/radiologo.png'
        title = html.unescape(i['title']['rendered'])
        subtitle = html.unescape(i['excerpt']['rendered'])
        button = elements.WebUrlButton(
            title='Read more',
            url=i['link']
        )
        element = elements.Element(
            title=title[:40] + '..' if len(title) > 40 else title,
            subtitle=subtitle[3:75] + '..' if len(subtitle) > 75 else subtitle[3:-3],
            image_url=img,
            buttons=[button]
        )
        all_elem.append(element)
    return all_elem


def db_query(user_id, query, sub_ib=0):
    try:
        mysql = MySQLdb.connect(host=os.environ['DB_HOST'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'],
                                db='fbmsgbot', autocommit=True)
        sql_req = {'SELECT': f'SELECT sub_id FROM bot_rol WHERE id=\'{int(user_id)}\'',
                   'INSERT': f'INSERT INTO bot_rol (id, sub_id) VALUES (\'{int(user_id)}\', \'{int(sub_ib)}\')',
                   'UPDATE': f'UPDATE bot_rol SET sub_id={sub_ib} WHERE id={int(user_id)}'}
        with mysql.cursor() as cursor:
            sql = sql_req[query]
            app.logger.info(f'SQL Req: {sql_req[query]}')
            cursor.execute(sql)
            row = cursor.fetchone()
            sql_resp = row[0] if row else None
            app.logger.info(f'SQL Resp: {sql_resp}')
            if query == 'SELECT':
                return sql_resp if sql_resp else None
    except Exception as excp:
        app.logger.exception('Database query', exc_info=excp)
        return None


# Facebook Manual Module
def subscribe_this(domains):  # -> :type domain: list
    data = {"whitelisted_domains": domains}
    resp = requests.post(
        "https://graph.facebook.com/v2.6/me/subscribed_apps?access_token=" + os.environ['FACEBOOK_TOKEN'],
        json=data)
    app.logger.info(f'Subscribe this:\n{resp.content}')


def send_fb_msg(user_id=None, msg=None, json=None):
    data = json if json else {"recipient": {"id": user_id}, "message": {"text": msg}}
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + os.environ['FACEBOOK_TOKEN'],
                         json=data)
    app.logger.info(f'Send message: \n{resp.content}')


def add_to_wlist(domains):  # -> :type domain: list
    data = {"whitelisted_domains": domains}  # -> :type domain: list
    resp = requests.post(
        "https://graph.facebook.com/v2.6/me/messenger_profile?access_token=" + os.environ['FACEBOOK_TOKEN'],
        json=data)
    app.logger.info(f'Add domain to white list:\n{resp.content}')


def set_start_msg(payload):  # -> :type payload: string
    data = {
        "get_started": {
            "payload": payload
        }
    }
    try:
        resp = requests.post(
            "https://graph.facebook.com/v2.6/me/messenger_profile?access_token=" + os.environ['FACEBOOK_TOKEN'],
            json=data)
        app.logger.info(f'Set start payload: {resp.content}')
        return 'OK'
    except Exception as excp:
        app.logger.exception('Set start msg', exc_info=excp)
        return f'{excp}\nSee log for details'


def set_menu():
    data = {
        "setting_type": "call_to_actions",
        "thread_state": "existing_thread",
        "call_to_actions": [
            {
                "type": "postback",
                "title": "Recent Lifestreams",
                "payload": "MENU_LSTREAMS"
            },
            {
                "type": "postback",
                "title": "Hottest Stories",
                "payload": "MENU_STORIES"
            },
            {
                "type": "postback",
                "title": "Help",
                "payload": "GET_HELP"
            }
        ]}
    try:
        resp = requests.post(
            "https://graph.facebook.com/v2.6/me/thread_settings?access_token=" + os.environ['FACEBOOK_TOKEN'],
            json=data)
        app.logger.info(f'Set FB Menu: {resp.content}')
        return 'OK'
    except Exception as excp:
        app.logger.exception('Set FB Menu', exc_info=excp)
        return f'{excp}\nSee log for details'


# Init facebook client
messenger = MessengerClient(access_token=os.environ['FACEBOOK_TOKEN'])


# noinspection PyBroadException
def reply_lib(user_id, msg=None, pload=None, message=None):
    msg = msg.upper() if msg else ''
    pload = msg if not pload else pload
    try:
        recipient = messages.Recipient(recipient_id=user_id)
        sub_id = db_query(user_id, 'SELECT')  # Note: check user
        app.logger.info(f'User: {user_id} | Subscribe id: {sub_id}')
        # BEGIN MENU ##
        # TODO! Ответы в обычных кнопках не более 20 символов
        if pload == 'START_MESSAGE':
            r_msg = "Hi! Welcome to Radio One Lebanon Messenger." \
                    "We'd love to share the hottest Celeb & Lifestyle Stories with you and notify you when our Live Programs start."
            pback_stories = elements.PostbackButton(
                title="Subscribe stories",  # Great, send me your best stories daily.
                payload='EN_SUB_STORIES'
            )
            pback_liveprog = elements.PostbackButton(
                title="Subscribe Programs",  # Love your Programs. Notify me when they start.
                payload='EN_SUB_LIVEPROG'
            )
            pback_nosub = elements.PostbackButton(
                title="Not now, thank you",
                payload='NOTHING_SUB'
            )
            template = templates.ButtonTemplate(
                text=r_msg,
                buttons=[pback_stories, pback_liveprog, pback_nosub]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif msg == 'GET_NEWS':
            template = templates.GenericTemplate(get_posts('51'))
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif msg == 'SET_START_PLOAD':
            message = messages.Message(text=set_start_msg('START_MESSAGE'))
        # Settings / help
        elif pload == 'SETTINGS' or msg == 'HELP':
            pback_mng_alerts = elements.PostbackButton(
                title='Manage you alerts',
                payload='MNG_ALERTS'
            )
            el_settings = elements.Element(
                title='Personalize notifications',
                # subtitle='Send me your best stories daily.',
                # image_url='https://farbio.xyz/images/ava.jpg',
                buttons=[pback_mng_alerts]
            )
            template = templates.GenericTemplate([el_settings])
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        # TODO! Subtitle и картинки для категорий настройках
        # Alerts Manager
        elif pload == 'MNG_ALERTS':
            # Stories
            if int(sub_id) == 1 or int(sub_id) == 3:
                pback_stor = elements.PostbackButton(
                    title='Disable Alerts',
                    payload='DIS_SUB_STORIES'
                )
            else:
                pback_stor = elements.PostbackButton(
                    title='Enable Alerts',
                    payload='EN_SUB_STORIES'
                )
            el_stories = elements.Element(
                title='Stories',
                subtitle='Send me your best stories daily.',
                image_url='https://farbio.xyz/images/ava.jpg',
                buttons=[pback_stor]
            )
            # Live Programs
            if int(sub_id) == 2 or int(sub_id) == 3:
                pback_lstyle = elements.PostbackButton(
                    title='Disable Alerts',
                    payload='DIS_SUB_LIVEPROG'
                )
            else:
                pback_lstyle = elements.PostbackButton(
                    title='Enable Alerts',
                    payload='EN_SUB_LIVEPROG'
                )
            el_lifestyle = elements.Element(
                title='Life Programs',
                subtitle='Love your Programs. Notify me when they start.',
                image_url='https://getmdl.io/assets/demos/welcome_card.jpg',
                buttons=[pback_lstyle]
            )
            template = templates.GenericTemplate([el_stories, el_lifestyle])
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        # Sub/unsub stories
        elif pload == 'EN_SUB_STORIES':
            r_msg = f'\nYou will start receiving the daily briefing\n' \
                    f'You can change your subscription at any time by typing "help"\n' \
                    f'Would you like to see the hottest Stories now?'
            if sub_id and int(sub_id) != 1 and int(sub_id) != 3:
                db_query(user_id, 'UPDATE', int(sub_id) + 1)
            elif not sub_id:
                db_query(user_id, 'INSERT', 1)
            qr_celebrity = quick_replies.QuickReplyItem(
                content_type='text',
                title='Celebrity',
                payload='GET_CELEBRITY'
            )
            qr_music = quick_replies.QuickReplyItem(
                content_type='text',
                title='Music',
                payload='GET_MUSIC'
            )
            qr_rships = quick_replies.QuickReplyItem(
                content_type='text',
                title='Relationships',
                payload='GET_RSHIPS'
            )
            qr_lstyle = quick_replies.QuickReplyItem(
                content_type='text',
                title='Lifestyle',
                payload='GET_LSTYLE'
            )
            replies = quick_replies.QuickReplies(quick_replies=[qr_celebrity, qr_music, qr_rships, qr_lstyle])
            message = messages.Message(text=r_msg, quick_replies=replies)
        #############
        elif pload == 'DIS_SUB_STORIES':
            if int(sub_id) == 1 or int(sub_id) == 3:
                db_query(user_id, 'UPDATE', int(sub_id) - 1)
            reply_lib(user_id, pload='MNG_ALERTS')
        # Sub/unsub live programs
        elif pload == 'EN_SUB_LIVEPROG':
            r_msg = f'Great! We`ll send you a message before our Live Program start\n' \
                    f'You can change your subscription at any time by typing \"help\"\n' \
                    f'Would you like to view our recent lifestreams?'
            if sub_id and int(sub_id) != 2 and int(sub_id) != 3:
                db_query(user_id, 'UPDATE', int(sub_id) + 2)
            elif not sub_id:
                db_query(user_id, 'INSERT', 2)
            pback_lives = elements.PostbackButton(
                title='Yes, sure',
                payload='GET_LIVEPG'
            )
            template = templates.ButtonTemplate(
                text=r_msg,
                buttons=[pback_lives]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        ###
        elif pload == 'DIS_SUB_LIVEPROG':
            if int(sub_id) == 2 or int(sub_id) == 3:
                db_query(user_id, 'UPDATE', int(sub_id) - 2)
            reply_lib(user_id, pload='MNG_ALERTS')
        # Get news from site
        elif pload == 'GET_CELEBRITY':
            template = templates.GenericTemplate(get_posts('48'))
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif pload == 'GET_MUSIC':
            template = templates.GenericTemplate(get_posts('51'))
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif pload == 'GET_RSHIPS':
            template = templates.GenericTemplate(get_posts('236'))
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif pload == 'GET_LSTYLE':
            template = templates.GenericTemplate(get_posts('231'))
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif pload == 'GET_LIVEPG':
            button = elements.WebUrlButton(
                title='Open last',
                url='https://www.facebook.com/Radioonelebanon/videos/1855981917757533/'
            )
            element = elements.Element(
                title='Live Programs',
                image_url='http://www.radioone.fm/wp-content/uploads/2017/04/radiologo.png',
                buttons=[button]
            )
            template = templates.GenericTemplate([element])
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        # How can i help you?
        else:
            r_msg = 'How can i help you?'
            qr_celebrity = quick_replies.QuickReplyItem(
                content_type='text',
                title='Celebrity',
                payload='GET_CELEBRITY'
            )
            qr_music = quick_replies.QuickReplyItem(
                content_type='text',
                title='Music',
                payload='GET_MUSIC'
            )
            qr_rships = quick_replies.QuickReplyItem(
                content_type='text',
                title='Relationships',
                payload='GET_RSHIPS'
            )
            qr_lstyle = quick_replies.QuickReplyItem(
                content_type='text',
                title='Lifestyle',
                payload='GET_LSTYLE'
            )
            qr_livepg = quick_replies.QuickReplyItem(
                content_type='text',
                title='Live Programs',
                payload='GET_LIVEPG'
            )
            qr_settings = quick_replies.QuickReplyItem(
                content_type='text',
                title='Settings',
                payload='SETTINGS'
            )
            replies = quick_replies.QuickReplies(
                quick_replies=[qr_celebrity, qr_music, qr_rships, qr_lstyle, qr_livepg, qr_settings])
            message = messages.Message(text=r_msg, quick_replies=replies)
        # END OF MENU #
        app.logger.info(f'Response for {user_id}')
        if message:
            req = messages.MessageRequest(recipient, message)
            messenger.send(req)
    except Exception as excp:
        app.logger.exception('Except send_msg:', exc_info=excp)


@app.route('/', methods=['POST'])
def handle_incoming_messages():
    try:
        data = request.json
        entry_msg = data['entry'][0]['messaging'][0]
        sender = entry_msg['sender']['id']
        app.logger.info(f'Request: {data}')
        if 'postback' in entry_msg:
            pload = entry_msg['postback']['payload']
            threading.Thread(target=reply_lib(sender, pload=pload)).start()
        elif 'message' in entry_msg:
            if 'quick_reply' in entry_msg['message']:
                pload = entry_msg['message']['quick_reply']['payload']
                threading.Thread(target=reply_lib(sender, pload=pload)).start()
            elif 'text' in entry_msg['message']:
                message = entry_msg['message']['text']
                threading.Thread(target=reply_lib(sender, msg=message)).start()
    except Exception as excp:
        app.logger.exception('Except hand_msg:', exc_info=excp)
    finally:
        return f'post: {request.json}'


@app.route('/', methods=['GET'])
def verify(get_log=''):
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    for line in list(open('file.log')):
        if 'ERROR' in line:
            line = '<span style="color: #F44336">' + line + '</span>'
        elif 'WARNING' in line:
            line = '<span style="color: #9C27B0">' + line + '</span>'
        get_log += line
    return render_template('log.html', log_text=Markup(get_log), date=datetime.datetime.now(),
                           threads=threading.active_count())


def web_thread():
    if __name__ == '__main__':
        handler = logging.FileHandler('file.log')
        handler.setLevel(logging.INFO)
        handler.setFormatter(Formatter('• %(asctime)s | %(levelname)s: %(message)s'))
        app.logger.addHandler(handler)
        app.run(debug=True, host=os.environ.get('address', '0.0.0.0'), port=int(os.environ.get('PORT', 80)))


flask_thread = threading.Thread(target=web_thread())
flask_thread.start()
