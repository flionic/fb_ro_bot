from flask import Flask, request
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


def reply_lib(user_id, msg):
    recipient = messages.Recipient(recipient_id=user_id)
    # Send button template
    web_button = elements.WebUrlButton(
        title='Show website',
        url='http://farbio.xyz'
    )
    postback_button = elements.PostbackButton(
        title='Start chatting',
        payload='USER_DEFINED_PAYLOAD'
    )
    template = templates.ButtonTemplate(
        text='What do you want to do next?',
        buttons=[web_button, postback_button]
    )
    attachment = attachments.TemplateAttachment(template=template)

    message = messages.Message(text=msg, attachment=attachment)
    request = messages.MessageRequest(recipient, message)
    messenger.send(request)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    reply_lib(sender, message[::-1])

    return "ok"


"""
@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    reply(sender, message[::-1])

    return "ok"
"""


def web_process():
    if __name__ == '__main__':
        port = int(os.environ.get('PORT', 80))
        app.run(debug=True, host=os.environ.get('address', '0.0.0.0'), port=port)


flask_thread = threading.Thread(target=web_process())
flask_thread.start()
