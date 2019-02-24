import os
from os.path import join, dirname
import sys
from flask import Flask, request, abort
from janome.tokenizer import Tokenizer
import random

import codecs

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage, StickerSendMessage, StickerMessage
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

class CorpusElement:
    def __init__(self, text='', tokens=[], pn_scores=[]):
        self.text = text # テキスト本文
        self.tokens = tokens # 構文木解析されたトークンのリスト
        self.pn_scores = pn_scores # 感情極性値(後述)


# CorpusElementのリスト
naive_corpus = []

naive_tokenizer = Tokenizer()


# pn_ja.dicファイルから、単語をキー、極性値を値とする辞書を得る
def load_pn_dict():
    dic = {}

    with codecs.open('./database/pn_ja.dic', 'r', 'shift_jis') as f:
        lines = f.readlines()

        for line in lines:
            # 各行は"良い:よい:形容詞:0.999995"
            columns = line.split(':')
            dic[columns[0]] = float(columns[3])

    return dic


# トークンリストから極性値リストを得る
def get_pn_scores(tokens, pn_dic):
    scores = []

    for surface in [t.surface for t in tokens if t.part_of_speech.split(',')[0] in ['動詞', '名詞', '形容詞', '副詞']]:
        if surface in pn_dic:
            scores.append(pn_dic[surface])

    return scores


# 感情極性対応表のロード
pn_dic = load_pn_dict()
print(pn_dic['良い'])
# 0.999995

# 各文章の極性値リストを得る
for element in naive_corpus:
    element.pn_scores = get_pn_scores(element.tokens, pn_dic)

# 1件目の文章の極性値を表示する

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


messages = ["頑張れ七海！！","ななみのこと大好きだよ！","応援してるよ！ななみ！","ななみ起きろよー！！","一緒に仕事頑張ろう！"]


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    t = Tokenizer()
    naive_corpus = []

    text = event.message.text
    tokens = t.tokenize(text)
    element = CorpusElement(text, tokens)
    naive_corpus.append(element)

    element.pn_scores = get_pn_scores(element.tokens, pn_dic)

    N = len(element.pn_scores)
    if N != 0:
        s = sum(element.pn_scores)
        mean = s / N
        if mean > 0:
            p_id = 1
            s_id = 125
        else:
            p_id = 1
            s_id = 16
    else:
        mean = 'None'
        p_id = 1
        s_id = 2

    line_bot_api.reply_message(
        event.reply_token,
        [StickerSendMessage(package_id=p_id,sticker_id=s_id),
            TextSendMessage(text="pn_score:　{}".format(str(mean)), type=text)]
    )


if __name__ == "__main__":
    app.run(debug=True, port=os.getenv('PORT'))