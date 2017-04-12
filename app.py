from flask import Flask, request, redirect, render_template
import requests
import os
import threading
from messengerbot import MessengerClient, attachments, templates, elements
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


# Init facebook client
messenger = MessengerClient(access_token=os.environ['FACEBOOK_TOKEN'])


def reply_lib(user_id, msg=None, pload=None, err=None):
    try:
        recipient = messages.Recipient(recipient_id=user_id)
        sub_id = db_query(user_id, 0)
        if err:
            message = messages.Message(text=err)
            # elif sub_id is not None:
            # message = messages.Message(text=f'You are subscribed to: {sub_id}')
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
                title='- Yes, sure',
                payload='WANT_SUB_LIVE'
            )
            template = templates.ButtonTemplate(
                text=f'------',
                buttons=[pback_lives]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
    #############
        elif pload == 'NOTHING_SUB':
            pback_stories = elements.PostbackButton(
                title='Hottest Stories',
                payload='GET_STORIES'
            )
            pback_streams = elements.PostbackButton(
                title='Recent Lifestreams',
                payload='GET_STREAMS'
            )
            pback_help = elements.PostbackButton(
                title='Help',
                payload='GET_HELP'
            )
            template = templates.ButtonTemplate(
                text='Main menu',
                buttons=[pback_stories, pback_streams, pback_help]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
    #############
        else:
            r_msg = "Hi! Welcome to Radio One Lebanon Messanger. " \
                    "We'd love to share the hottest Celeb & Lifestyle Stories with you and notify you when our Live Programs start."
            pback_stories = elements.PostbackButton(
                title="- Great, send me your best stories daily.",
                payload='WANT_SUB_STORIES'
            )
            pback_liveprog = elements.PostbackButton(
                title="- Love your Programs. Notify me when they start.",
                payload='WANT_SUB_LIVEPROG'
            )
            pback_nosub = elements.PostbackButton(
                title="- Not now, thank you",
                payload='NOTHING_SUB'
            )
            template = templates.ButtonTemplate(
                text=r_msg,
                buttons=[pback_stories, pback_liveprog, pback_nosub]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        # message = messages.Message(text=msg)
        req = messages.MessageRequest(recipient, message)
        messenger.send(req)
    except Exception as excp:
        print(excp)


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
    #return render_template('index.html')


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
                message = msg['text'][::-1]
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
