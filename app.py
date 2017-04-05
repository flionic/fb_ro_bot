from flask import Flask, request
import requests

app = Flask(__name__)

#ACCESS_TOKEN = "EAAP9MMaGh1cBAHS7jZCnuQgm2GWx5grLraIElFlWlIw2r3Afb34m2c2rP0xdkkkKEeiBOykGINAP0tScwmL5NNBJQN9ayPCuq13syvWocmbYZA7BXL86FsZCyZBxTmkgYYp8MDulLc1Tx70FGdU5ebQZAJV28nMkZD"


def reply(user_id, msg):
    data = {
        "recipient": {"id": user_id},
        "message": {"text": msg}
    }
    resp = requests.post("https://graph.facebook.com/v2.6/me/messages?access_token=" + ACCESS_TOKEN, json=data)
    print(resp.content)


@app.route('/', methods=['POST'])
def handle_incoming_messages():
    data = request.json
    sender = data['entry'][0]['messaging'][0]['sender']['id']
    message = data['entry'][0]['messaging'][0]['message']['text']
    reply(sender, message[::-1])

    return "ok"


if __name__ == '__main__':
    app.run(debug=True)