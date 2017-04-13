from flask import Flask, request, redirect, render_template
import requests
import os
import threading
from messengerbot import MessengerClient, attachments, templates, elements, webhooks
import messages, quick_replies
import MySQLdb

app = Flask(__name__)

# wp parse sample = site_domain + 'wp-json/wp/v2/posts?tags=38&per_page=1'
site_domain = 'http://worket.tk/'


def get_posts(tid, pp):
    resp = requests.get(f'{site_domain}wp-json/wp/v2/posts?tags={tid}&per_page={pp}')
    if resp.status_code == 200:
        resp.json()
        return True


def db_query(uid, qid, sib=0):
    try:
        mysql = MySQLdb.connect(host=os.environ['DB_HOST'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'],
                                db='fbmsgbot', autocommit=True)
        sql_resp = [f'SELECT sub FROM bot_rol WHERE id=\'{uid}\'',
                    f'INSERT INTO bot_rol (id, sub) VALUES (\'{int(uid)}\', \'{int(sib)}\')',
                    f'UPDATE bot_rol SET sub={sib} WHERE id={uid})']
        with mysql.cursor() as cursor:
            sql = sql_resp[qid]
            cursor.execute(sql)
            return cursor.fetchone()[0] if cursor.fetchone() is not None else True
    except Exception as expc:
        print(expc)


def send_fb_msg(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + os.environ['FACEBOOK_TOKEN'],
                         json=data)
    print(resp.content)


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
                "payload": "NENU_STORIES"
            },
            {
                "type": "postback",
                "title": "Send a message",
                "payload": "MENU_SENDMSG"
            },
            {
                "type": "postback",
                "title": "Help",
                "payload": "GET_HELP"
            }
        ]}
    try:
        print('Trying set menu: ')
        resp = requests.post(
            "https://graph.facebook.com/v2.6/me/thread_settings?access_token=" + os.environ['FACEBOOK_TOKEN'],
            json=data)
        print(resp.content)
    except Exception as excp:
        print(excp)


def send_share(uid):
    data = {
        "recipient": {"id": uid},
        "message": {"attachment": {
            "type": "template",
            "payload": {
                "template_type": "generic",
                "elements": [
                    {
                        "title": "Breaking News: Record Thunderstorms",
                        "subtitle": "The local area is due for record thunderstorms over the weekend.",
                        "image_url": "https://thechangreport.com/img/lightning.png",
                        "buttons": [
                            {
                                "type": "element_share"
                            }
                        ]
                    }
                ]
            }
        }
        }}
    try:
        print('Share')
        resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + os.environ['FACEBOOK_TOKEN'],
                             json=data)
        print(resp.content)
    except Exception as excp:
        print(excp)


# Init facebook client
messenger = MessengerClient(access_token=os.environ['FACEBOOK_TOKEN'])


def reply_lib(user_id, msg=None, pload=None, err=None):
    if msg == 'set_menu':
        set_menu()
    try:
        recipient = messages.Recipient(recipient_id=user_id)
        sub_id = db_query(user_id, 0)
        ## BEGIN MENU ##
        if err:
            message = messages.Message(text=err)
            # elif sub_id is not None:
            # message = messages.Message(text=f'You are subscribed to: {sub_id}')
        #############
        elif msg == 'test':
            pback_one = elements.PostbackButton(
                title='Button One',
                payload='PB_ONE'
            )
            pback_two = elements.PostbackButton(
                title='Button Two',
                payload='PB_TWO'
            )
            share_el = elements.Element(
                title='Test GenericTemplate',
                subtitle='Subtitle for this here.',
                image_url='https://farbio.xyz/images/ava.jpg',
                buttons=[pback_one, pback_two]
            )
            template = templates.GenericTemplate([share_el])
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        #############
        elif pload == 'MNG_ALERTS' or msg == 'mng':
            pback_en_stor = elements.PostbackButton(
                title='Enable Alerts',
                payload='EN_SUB_STORIES'
            )
            pback_dis_stor = elements.PostbackButton(
                title='Disable Alerts',
                payload='DIS_SUB_STORIES'
            )
            el_stories = elements.Element(
                title='Stories',
                subtitle='Subtitle for this here.',
                image_url='https://farbio.xyz/images/ava.jpg',
                buttons=[pback_en_stor, pback_dis_stor]
            )

            pback_en_lstyle = elements.PostbackButton(
                title='Enable Alerts',
                payload='EN_SUB_LSTYLE'
            )
            pback_dis_lstyle = elements.PostbackButton(
                title='Disable Alerts',
                payload='DIS_SUB_LSTYLE'
            )
            el_lifestyle = elements.Element(
                title='Life Programs',
                subtitle='Subtitle for this here.',
                image_url='https://getmdl.io/assets/demos/welcome_card.jpg',
                buttons=[pback_en_lstyle, pback_dis_lstyle]
            )
            template = templates.GenericTemplate([el_stories, el_lifestyle])
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        #############
        elif pload == 'WANT_SUB_STORIES':
            msg = f'You will start receiving the daily briefing\n' \
                  f'You can change your subscription at any time by typing "help"\n'
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
            message = messages.Message(text='Would you like to see the hottest Stories now?', quick_replies=replies)
        #############
        elif pload == 'WANT_SUB_LIVEPROG':
            r_msg = f'Great! We`ll send you a message before our Live Program start\n' \
                    f'You can change your subscription at any time by typing \"help\"\n' \
                    f'Would you like to view our recent lifestreams?'
            messenger.send(messages.MessageRequest(recipient, messages.Message(text=r_msg)))
            pback_lives = elements.PostbackButton(
                title='Yes, sure',
                payload='WANT_SUB_LIVE'
            )
            template = templates.ButtonTemplate(
                text=r_msg,
                buttons=[pback_lives]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        #############
        else:
            r_msg = "Hi! Welcome to Radio One Lebanon Messanger. " \
                    "We'd love to share the hottest Celeb & Lifestyle Stories with you and notify you when our Live Programs start."
            pback_stories = elements.PostbackButton(
                title="stories",
                payload='WANT_SUB_STORIES'
            )
            pback_liveprog = elements.PostbackButton(
                title="programs",
                payload='WANT_SUB_LIVEPROG'
            )
            pback_nosub = elements.PostbackButton(
                title="not",
                payload='NOTHING_SUB'
            )
            template = templates.ButtonTemplate(
                text=r_msg,
                buttons=[pback_stories, pback_liveprog, pback_nosub]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        ## END OF MENU ##
        req = messages.MessageRequest(recipient, message)
        messenger.send(req)
    except Exception as excp:
        print(f'Except sending message: {excp}')


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return f'Python flask webhook listener on server: {os.environ["SERVER_NAME"]} - Active threads: {threading.active_count()}', 200
    # return redirect('http://farbio.xyz', 301)
    # return render_template('index.html')


# noinspection PyBroadException
@app.route('/', methods=['POST'])
def handle_incoming_messages():
    # noinspection PyUnreachableCode
    try:
        data = request.json
        sender = data['entry'][0]['messaging'][0]['sender']['id']
        print(str(data))
        msg = data['entry'][0]['messaging'][0]
        if 'postback' in msg:
            pload = msg['postback']['payload']
            threading.Thread(target=reply_lib(sender, pload=pload)).start()
            # reply_lib(sender, pload=pload)
        elif 'message' in msg:
            msg = msg['message']
            if 'quick_reply' in msg:
                pload = msg['quick_reply']['payload']
                threading.Thread(target=reply_lib(sender, pload=pload)).start()
                # reply_lib(sender, pload=pload)
            elif 'text' in msg:
                message = msg['text']
                # message = msg['text'][::-1]
                if message == 'share1':
                    send_share(sender)
                elif message == 'share2':
                    send_share2(sender)
                else:
                    threading.Thread(target=reply_lib(sender, msg=message)).start()
                    # reply_lib(sender, msg=message)
    except Exception as excp:
        reply_lib(sender, err=f'Exception: {excp}')
    finally:
        return "post: " + str(request.json)


def web_process():
    if __name__ == '__main__':
        app.run(debug=True, host=os.environ.get('address', '0.0.0.0'), port=int(os.environ.get('PORT', 80)))


flask_thread = threading.Thread(target=web_process())
flask_thread.start()
