import requests
import json
import glob
import re
import  alis_util as alis
import idpw
import os
import shutil
import cv2
from datetime import datetime
from janome.tokenizer import Tokenizer
from collections import defaultdict
from wordcloud import WordCloud

DELTA_JST = 9 * 60 * 60 * 60
START_TIME = datetime(2019, 1, 1, 0, 0).timestamp() - DELTA_JST
END_TIME = datetime(2020, 1, 1, 0, 0).timestamp() - DELTA_JST
REQ_ARTICLE = '3bNnmrBWAAQJ'
BASE_ARTICLE = '3bNnmrBWAAQJ'
IMAGE_ARTICLE = '3bNnmrBWAAQJ'
ACCESS_TOKEN = alis.get_access_token(idpw.ID, idpw.PW)
title_txt = "赤組も白組も2019年を振り返りましょう♪"

def test_delete_file():
    target_dir = './images'
    if os.path.isdir(target_dir):
        shutil.rmtree(target_dir)
    os.mkdir(target_dir)

def check_request(article_id):
    done_users = list(map(lambda image: image[9:-4], glob.glob("./images/*.png")))
    return alis.get_comment_tip_users_new(article_id, done_users)


def get_client_article_ids(clients):
    client_article_ids = {}
    for client in clients:
        client_article_ids[client] = alis.get_article_list_period(client, START_TIME, END_TIME)
    return client_article_ids


# def addIcon(client):
#     icon_file = f'./icon/{client}.png'
#     wc_file = f'./images/{client}.png'
#
#     if not os.path.isfile(icon_file):
#         url = f'https://alis.to/api/users/{client}/info'
#         icon_url = json.loads(requests.get(url).text)["icon_image_url"]
#         alis.download_file(icon_url, icon_file)
#
#     img1 = cv2.imread(wc_file)
#     img2 = cv2.imread(icon_file)
#
#     height, width = img1.shape[:2]
#     img2[0:height, 0:width] = img1
#
#     cv2.imwrite('new.jpg', img2)



def make_wordcloud(client_article_ids):
    for client, article_ids in client_article_ids.items():
        text_all = alis.get_all_text(article_ids)
        if text_all == '':
            text_all = '来年は記事書くぞー'
        wordcount(text_all, client)
    return 0


def make_statics(client_article_ids):

    client_statics = {}

    for client, article_ids in client_article_ids.items():
        print('statics:', client)
        like_num = alis.get_like_total(article_ids)
        tip_num, tip_top_user = alis.get_tip_statics(article_ids)
        comment_num, comment_top_user = alis.get_comment_statics(article_ids)
        image_url = alis.upload_image(ACCESS_TOKEN, IMAGE_ARTICLE, f'./images/{client}.png')

        client_statics[client] = {
            'article_num': len(article_ids),
            'like_num': like_num,
            'tip_num': tip_num,
            'tip_top_user': tip_top_user,
            'comment_num': comment_num,
            'comment_top_user': comment_top_user,
            'image_url': image_url
        }

    return client_statics


def wordcount(texts, user_id):
    texts = re.sub('<[^>]*?>', '', texts)
    texts = re.sub('さっき|ここ|自分|わけ|わたし|https|net|ja|mycryptoheroes|企画|参加|イベント|image|nbsp|alis|articles|figure|img|記事|こと|よう|それ|とき|こちら|みんな|これ|そう|そこ|ため|投げ銭|mm|ALIS|金額|画面|活動|数字|ちゃん|さん|もの', '', texts)

    t = Tokenizer()
    words_count = defaultdict(int)
    words = []
    tokens = t.tokenize(texts)
    for token in tokens:
        pos = token.part_of_speech.split(',')[0]
        if pos in ["名詞"]:
            words_count[token.base_form] += 1
            words.append(token.base_form)

    text = ' '.join(words)
    fpath = './font/logo_type_gisic.otf'
    image_name = f"./images/{user_id}.png"
    wordcloud = WordCloud(background_color="white", font_path=fpath, width=800, height=419).generate(text)
    wordcloud.to_file(image_name)

    return 0


def get_curret_article(article_id):
    url = f'https://alis.to/api/articles/{article_id}'
    data = json.loads(requests.get(url).text)
    return data['body']


def make_alis_article(statics):
    new_strings = ''

    for k, v in statics.items():
        new_strings += f'<h2>{alis.get_user_name(k)}</h2>\n'
        new_strings += f'<img src= {v["image_url"]}>\n'
        new_strings += f'総記事数: {v["article_num"]}<br>\n'
        new_strings += f'総投げ銭数: {v["tip_num"]}<br>\n'
        new_strings += f'総コメント数: {v["comment_num"]}<br>\n'
        new_strings += f'トップチッパー: {alis.get_user_name(v["tip_top_user"])}<br>\n'
        new_strings += f'トップコメンター: {alis.get_user_name(v["comment_top_user"])}<br>\n'
        new_strings += '<br><br><br>'
    return get_curret_article(BASE_ARTICLE) + new_strings


if __name__ == '__main__':

    # print('test')
    # test_delete_file()

    print('check request')
    clients = check_request(REQ_ARTICLE)
    print(clients)

    print('get infromations')
    client_article_ids = get_client_article_ids(clients)
    print('make word cloud')
    make_wordcloud(client_article_ids)
    statics = make_statics(client_article_ids)

    print('generate article and post')
    contents = make_alis_article(statics)

    #contents = '<img src= "https://alis.to/d/api/articles_images/haruka/39rQgyyQvqy7/b50eb999-1d1c-432b-9630-7f8284c87aba.png"> <br><br>          2019年もありがとうございました。今年もALISでみなさんと触れ合えて楽しかったです。こちらの記事にコメントや投げ銭をしていただくと、あなたのALISライフの総括ができます。1日の数回アップデートしますのでまた遊びにきてくださいね。'

    alis.update_article(ACCESS_TOKEN, title_txt, contents, BASE_ARTICLE)
