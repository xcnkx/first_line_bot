import os
import sys
from flask import Flask, request, abort
from janome.tokenizer import Tokenizer

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)

app = Flask(__name__)

# 環境変数からchannel_secret・channel_access_tokenを取得
channel_secret = os.environ['CHANNEL_SECRET']
channel_access_token = os.environ['CHANNEL_ACCESS_TOKEN']

if channel_secret is None:
    print('Specify CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

@app.route("/")
def hello_world():
    return "hello world!"

@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


messages = ["頑張れ七海！！","ななみのこと大好きだよ！","応援してるよ！ななみ！","ななみ起きろよー！！","一緒に仕事頑張ろう！","えっちしたい"]


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    t = Tokenizer()
    tokens = t.tokenize(event.message.text, wakati=True)

    for i in tokens:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=i))

if __name__ == "__main__":
    app.run()