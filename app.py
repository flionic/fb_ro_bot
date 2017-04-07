from flask import Flask, request, redirect
import requests
import os
import threading
from messengerbot import MessengerClient, attachments, templates, elements
import messages, quick_replies
import MySQLdb

app = Flask(__name__)
thr_id = 0
# wp parse sample = site_domain + 'wp-json/wp/v2/posts?tags=38&per_page=1'
site_domain = 'http://worket.tk/'
def get_posts(tid, pp):
    resp = requests.get(f'{site_domain}wp-json/wp/v2/posts?tags={tid}&per_page={pp}')
    if resp.status_code == 200:
        resp.json()
        return True

def db_query(uid, qid, sib=None):
    try:
        sqldbc = MySQLdb.connect(host=os.environ['DB_HOST'], user=os.environ['DB_USER'], password=os.environ['DB_PASS'],
                                 db='fbmsgbot', autocommit=True)
        sqlrsp = [f'SELECT sub FROM bot_rol WHERE id=\'{uid}\'',
                  f'INSERT INTO bot_rol (id, sub) VALUES (\'{int(uid)}\', \'{int(sib)}\')',
                  f'UPDATE bot_rol SET sub={sib} WHERE id={uid})']
        with sqldbc.cursor() as cursor:
            sql = sqlrsp[qid]
            cursor.execute(sql)
            return cursor.fetchone()[0]
    except Exception as expc:
        print(expc)

# Init facebook client
messenger = MessengerClient(access_token=os.environ['FACEBOOK_TOKEN'])

def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + os.environ['FACEBOOK_TOKEN'], json=data)
    print(resp.content)


def reply_lib(user_id, msg=None, pload=None, err=None):
    try:
        recipient = messages.Recipient(recipient_id=user_id)
        sub_id = db_query(user_id, 0)
        if err:
            message = messages.Message(text=err)
        # elif sub_id is not None:
            # message = messages.Message(text=f'You are subscribed to: {sub_id}')
        elif pload == 'WANT_SUB_YES':
            qr_sub_games = quick_replies.QuickReplyItem(
                content_type='text',
                title='Games',
                payload='SUB_GAMES'
            )
            qr_sub_movies = quick_replies.QuickReplyItem(
                content_type='text',
                title='Movies',
                payload='SUB_MOVIES'
            )
            qr_sub_all = quick_replies.QuickReplyItem(
                content_type='text',
                title='Both',
                payload='SUB_ALL'
            )
            qr_sub_no = quick_replies.QuickReplyItem(
                content_type='text',
                title='Cancel',
                payload='WANT_SUB_NO'
            )
            replies = quick_replies.QuickReplies(quick_replies=[qr_sub_games, qr_sub_movies, qr_sub_all, qr_sub_no])
            message = messages.Message(text='Please, select the category that you interests 🤔', quick_replies=replies)
        elif pload == 'WANT_SUB_NO':
            message = messages.Message(text='Oh, its bad 😞\nCome back anytime, we will wait for you! 😉 ')
        elif pload == 'SUB_GAMES' or pload == 'SUB_MOVIES' or pload == 'SUB_ALL':
            sub = db_query(user_id, 1, 1)
            postback_brn_yes = elements.PostbackButton(
                title='Yes, do it!',
                payload='SUB_LIVE_YES'
            )
            postback_brn_no = elements.PostbackButton(
                title='No, thanks',
                payload='SUB_LIVE_NO'
            )
            template = templates.ButtonTemplate(
                text=f'Great! {sub} Did you subscribe to notifications of live streams? 😏',
                buttons=[postback_brn_yes, postback_brn_no]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        elif pload == 'SUB_LIVE_YES':
            message = messages.Message(text='Oh, beautiful! Thank you for subscribe, wait for news from me 😌')
        elif pload == 'SUB_LIVE_NO':
            postback_brn_yes = elements.PostbackButton(
                title='Sub streams',
                payload='SUB_LIVE_YES'
            )
            postback_brn_no = elements.PostbackButton(
                title='Settings',
                payload='OPEN_SETTINGS'
            )
            template = templates.ButtonTemplate(
                text='Okay. Just wait for hot news from me 😄',
                buttons=[postback_brn_yes, postback_brn_no]
            )
            attachment = attachments.TemplateAttachment(template=template)
            message = messages.Message(attachment=attachment)
        else:
            web_button = elements.WebUrlButton(
                title='Show website',
                url='http://farbio.xyz'
            )
            postback_btn_yes = elements.PostbackButton(
                title='Yes, do it!',
                payload='WANT_SUB_YES'
            )
            postback_btn_no = elements.PostbackButton(
                title='No, thanks',
                payload='WANT_SUB_NO'
            )
            template = templates.ButtonTemplate(
                text='Are you want to subscribe hot every day news?',
                buttons=[web_button, postback_btn_yes, postback_btn_no]
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

    #return "Python flask webhook listener on server: " + os.environ["SERVER_NAME"], 200
    #threading.Thread(target=get_posts('38', '5'), name='getnews_thread').start()
    # threading.Thread(name='getnews_thread').join()
    return f'Python flask webhook listener on server: {os.environ["SERVER_NAME"]} - Active threads: {threading.active_count()}', 200
    # return redirect('http://farbio.xyz', 301)


# noinspection PyBroadException
@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    print(str(data))
    try:
        try:
            pload = data['entry'][0]['messaging'][0]['postback']['payload']
            threading.Thread(target=reply_lib, args=(sender,), kwargs={'pload':pload}).start()
            # reply_lib(sender, pload=pload)
        except:
            try:
                pload = data['entry'][0]['messaging'][0]['message']['quick_reply']['payload']
                threading.Thread(target=reply_lib, args=(sender,), kwargs={'pload': pload}).start()
                # reply_lib(sender, pload=pload)
            except:
                message = data['entry'][0]['messaging'][0]['message']['text'][::-1]
                threading.Thread(target=reply_lib, args=(sender,), kwargs={'msg': message}).start()
                # reply_lib(sender, msg=message)
    except Exception as excp:
            reply_lib(sender, err=f'Exception: {excp}')
    finally:
        return "ok"


def web_process():

    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 80))
        app.run(debug=True, host=os.environ.get('address', '0.0.0.0'), port=port)

flask_thread = threading.Thread(target=web_process())
flask_thread.start()
