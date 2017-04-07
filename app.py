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

ACCESS_TOKEN = os.environ['FACEBOOK_TOKEN']

# Init facebook client
messenger = MessengerClient(access_token=ACCESS_TOKEN)


def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + ACCESS_TOKEN, json=data)
    print(resp.content)


def reply_lib(user_id, msg=None, pload=None, err=None):
    recipient = messages.Recipient(recipient_id=user_id)
    if err:
        message = messages.Message(text=err)
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
        postback_brn_yes = elements.PostbackButton(
            title='Yes, do it!',
            payload='SUB_LIVE_YES'
        )
        postback_brn_no = elements.PostbackButton(
            title='No, thanks',
            payload='SUB_LIVE_NO'
        )
        template = templates.ButtonTemplate(
            text='Great! Did you subscribe to notifications of live streams? 😏',
            buttons=[postback_brn_yes, postback_brn_no]
        )
        attachment = attachments.TemplateAttachment(template=template)
        message = messages.Message(attachment=attachment)
    elif pload == 'SUB_LIVE_YES':
        message = messages.Message(text='Oh, beautiful! Thank you for subscribe, wait for news from me 😌')
    elif pload == 'SUB_LIVE_NO':
        qr_joke = quick_replies.QuickReplyItem(
            content_type='text',
            title='Joke! I want subscribe',
            payload='SUB_WANT_YES'
        )
        message = messages.Message(text='Okay. Just wait for hot news from me 😄', quick_replies=[qr_joke])
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
            threading.Thread(target=reply_lib, args=sender, kwargs={'pload':pload})
            # reply_lib(sender, pload=pload)
        except:
            try:
                pload = data['entry'][0]['messaging'][0]['message']['quick_reply']['payload']
                threading.Thread(target=reply_lib, args=sender, kwargs={'pload': pload})
                # reply_lib(sender, pload=pload)
            except:
                message = data['entry'][0]['messaging'][0]['message']['text'][::-1]
                threading.Thread(target=reply_lib, kwargs={'msg': message})
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