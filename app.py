from flask import Flask, request, redirect
import requests
import os
import threading
from messengerbot import MessengerClient, messages, attachments, templates, elements

app = Flask(__name__)

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


def reply_lib(user_id, msg='', pload=''):
    recipient = messages.Recipient(recipient_id=user_id)

    if pload == 'WANT_SUB_YES':
        postback_sub_games = elements.PostbackButton(
            title='Games',
            payload='SUB_GAMES'
        )
        postback_sub_movies = elements.PostbackButton(
            title='Movies',
            payload='SUB_MOVIES'
        )
        postback_sub_all = elements.PostbackButton(
            title='All',
            payload='SUB_ALL'
        )
        template = templates.ButtonTemplate(
            text='Please, select the category that you interests',
            buttons=[postback_sub_games, postback_sub_movies, postback_sub_all]
        )
        attachment = attachments.TemplateAttachment(template=template)
        message = messages.Message(attachment=attachment)
    elif pload == 'WANT_SUB_NO':
        message = messages.Message(text='Oh, its bad :(\nCome back anytime, we will wait for you!')
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
            text='Great! Did you subscribe to notifications of live streams?',
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
            payload='WANT_SUB_YES'
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

    # return "Hello world", 200
    return redirect('http://farbio.xyz', 301)


# noinspection PyBroadException
@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    print(str(data))
    try:
        message = data['entry'][0]['messaging'][0]['message']['text'][::-1]
        reply_lib(sender, msg=message)
    except:
        try:
            pload = data['entry'][0]['postback']['payload']
            reply_lib(sender, pload=pload)
        except:
            pass
    finally:
        return "ok"


def web_process():
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 80))
        app.run(debug=True, host=os.environ.get('address', '0.0.0.0'), port=port)


flask_thread = threading.Thread(target=web_process())
flask_thread.start()
