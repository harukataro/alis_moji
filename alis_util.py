import requests
import json
from warrant.aws_srp import AWSSRP
from datetime import datetime, timedelta, timezone
import base64
import urllib.request

JST = timezone(timedelta(hours=+9), 'JST')
DELTA_JST = 9 * 60 * 60 * 60


def download_file(url, dst_path):
    try:
        with urllib.request.urlopen(url) as web_file, open(dst_path, 'wb') as local_file:
            local_file.write(web_file.read())
    except urllib.error.URLError as e:
        print(e)


def get_user_name(user_id):
    url = f'https://alis.to/api/users/{user_id}/info'
    data = json.loads(requests.get(url).text)

    if 'user_display_name' in data:
        return data['user_display_name']
    else:
        return 'none'

def get_access_token(username, password):
    POOL_ID = 'ap-northeast-1_HNT0fUj4J'
    POOL_REGION = 'ap-northeast-1'
    CLIENT_ID = '2gri5iuukve302i4ghclh6p5rg'
    aws = AWSSRP(username=username, password=password, pool_id=POOL_ID, client_id=CLIENT_ID, pool_region=POOL_REGION)
    return aws.authenticate_user()['AuthenticationResult']['IdToken']


def get_article_tip_users(article_id):
    users = []
    url = f'https://alis.to/api/articles/{article_id}/supporters'
    data = json.loads(requests.get(url).text)

    for comment in data['Items']:
        users.append(comment['user_id'])
    return users


def get_comment_users(article_id):
    users = []
    data = json.load(requests.get(f'https://alis.to/api/articles/{article_id}/comments').text)

    for comment in data['Items']:
        users.append(comment['user_id'])
    return users


def get_comment_tip_users_new(article_id, done_users):
    users = []
    data = json.loads(requests.get(f'https://alis.to/api/articles/{article_id}/comments').text)
    for comment in data['Items']:
        if comment['user_id'] not in done_users:
            users.append(comment['user_id'])

    data = json.loads(requests.get(f'https://alis.to/api/articles/{article_id}/supporters').text)
    for comment in data['Items']:
        if comment['user_id'] not in done_users:
            users.append(comment['user_id'])
    return users


def get_article_list_period(user_id, starttime, endtime):

    alis_start_time = datetime(2018, 4, 1, 0, 0).timestamp() - DELTA_JST
    current_time = datetime.now(JST).timestamp()
    if starttime < alis_start_time:
        starttime = alis_start_time
    if endtime > current_time:
        endtime = current_time

    loops = 20  # avoid  loop endless
    article_list = []
    sort_key = 0
    article_id = ''
    num_of_total = 0

    for page in range(loops):
        if page == 0:
            url = f'https://alis.to/api/users/{user_id}/articles/public?limit=100'
        else:
            url = f'https://alis.to/api/users/{user_id}/articles/public?limit=100&article_id={article_id}&sort_key={sort_key}'

        data = json.loads(requests.get(url).text)

        num_of_data = 0
        created_time = endtime
        for article in data['Items']:
            created_time = datetime.fromtimestamp(article['created_at']).timestamp()
            if created_time < starttime:
                break
            article_id = article['article_id']
            sort_key = article['sort_key']


            article_list.append(article_id)
            num_of_data += 1

        num_of_total += num_of_data
        if num_of_data != 100 or created_time < starttime:
            break

    return article_list


def get_all_text(article_ids):
    all_text =''
    for article_id in article_ids:
        url = f'https://alis.to/api/articles/{article_id}'
        data = json.loads(requests.get(url).text)
        all_text = all_text + data['title'] + data['body']
    return all_text


def get_like_total(article_ids):
    like_total = 0
    for article_id in article_ids:
        url = f'https://alis.to/api/articles/{article_id}/likes'
        data = json.loads(requests.get(url).text)
        like_total += int(data["count"])
    return like_total


def get_tip_statics(article_ids):
    num = 0
    users = {}

    for article_id in article_ids:
        url = f'https://alis.to/api/articles/{article_id}/supporters'
        data = json.loads(requests.get(url).text)
        num += len(data['Items'])

        for user in data['Items']:
            if user['user_id'] not in users:
                users[user['user_id']] = 1
            else:
                users[user['user_id']] += 1

    if len(users) == 0:
        users['none'] = 0
    top_user = max(users, key=users.get)
    return num, top_user


def get_comment_statics(article_ids):
    num = 0
    users = {}

    for article_id in article_ids:
        url = f'https://alis.to/api/articles/{article_id}/comments?limit=100'
        data = json.loads(requests.get(url).text)
        if 'Items' in data:
            num += len(data['Items'])

            for user in data['Items']:
                if user['user_id'] not in users:
                    users[user['user_id']] = 1
                else:
                    users[user['user_id']] += 1
    if len(users) == 0:
        users['none'] = 0
    top_user = max(users, key=users.get)
    return num, top_user


def update_article(accesstoken, title_txt, body, article_id):
    url = f'https://alis.to/api/me/articles/{article_id}/public/title'
    method = 'PUT'
    headers = {'Authorization': accesstoken}
    data = {
        'title': title_txt,
    }
    request = urllib.request.Request(url, json.dumps(data).encode(), method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        print(response.code)


    url = f'https://alis.to/api/me/articles/{article_id}/public/body'
    method = 'PUT'
    headers = {'Authorization': accesstoken}
    data = {
        'body': body,
    }
    request = urllib.request.Request(url, json.dumps(data).encode(), method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        print(response.code)

    #republish
    url = f'https://alis.to/api/me/articles/{article_id}/public/republish_with_header'
    method = 'PUT'
    headers = {'Authorization': accesstoken}
    data = {
        'topic': "technology",
        'tags': ["白組"],
        'eye_catch_url': "https://alis.to/d/api/articles_images/haruka/39rQgyyQvqy7/b50eb999-1d1c-432b-9630-7f8284c87aba.png"
    }
    request = urllib.request.Request(url, json.dumps(data).encode(), method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        print(response.code)
    return 0



def upload_image(accesstoken, article_id, image_file):

    url = f'https://alis.to/api/me/articles/{article_id}/images'
    image_data = open(image_file, "rb").read()

    method = 'POST'
    headers = {
        'Authorization': accesstoken,
        'accept': 'application/json application/octet-stream',
        'content-type': 'image/png',
    }
    data = {
        'article_image': base64.b64encode(image_data).decode('utf-8'),
    }

    request = urllib.request.Request(url, json.dumps(data).encode(), method=method, headers=headers)
    with urllib.request.urlopen(request) as response:
        response_body = json.load(response)
    return response_body['image_url']