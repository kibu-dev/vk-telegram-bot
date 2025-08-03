import os
import requests
from telegram import Bot, InputMediaPhoto
from dotenv import load_dotenv

load_dotenv()

VK_TOKEN = os.getenv("VK_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHANNEL = os.getenv("TELEGRAM_CHANNEL")
VK_GROUP_IDS = os.getenv("VK_GROUP_IDS").split(",")

bot = Bot(token=TELEGRAM_TOKEN)
STATE_DIR = "group_states"

if not os.path.exists(STATE_DIR):
    os.makedirs(STATE_DIR)

def get_last_post_id(group):
    path = os.path.join(STATE_DIR, f"{group}.txt")
    if os.path.exists(path):
        with open(path, "r") as f:
            return int(f.read().strip())
    return 0

def save_last_post_id(group, post_id):
    path = os.path.join(STATE_DIR, f"{group}.txt")
    with open(path, "w") as f:
        f.write(str(post_id))

def get_latest_post(group):
    url = "https://api.vk.com/method/wall.get"
    params = {
        "access_token": VK_TOKEN,
        "v": "5.131",
        "domain": group,
        "count": 1
    }
    try:
        r = requests.get(url, params=params).json()
        return r['response']['items'][0]
    except:
        return None

def extract_photos(attachments):
    photo_urls = []
    for att in attachments:
        if att['type'] == 'photo':
            sizes = att['photo']['sizes']
            largest = sorted(sizes, key=lambda s: s['width'] * s['height'])[-1]
            photo_urls.append(largest['url'])
    return photo_urls

def extract_video_links(attachments):
    video_links = []
    for att in attachments:
        if att['type'] == 'video':
            video = att['video']
            owner_id = video['owner_id']
            video_id = video['id']
            access_key = video.get('access_key', '')
            link = f"https://vk.com/video{owner_id}_{video_id}"
            if access_key:
                link += f"?access_key={access_key}"
            video_links.append(link)
    return video_links

def post_to_telegram(text, photos, videos):
    if photos:
        media_group = []
        for i, url in enumerate(photos[:10]):
            if i == 0 and text:
                media_group.append(InputMediaPhoto(media=url, caption=text))
            else:
                media_group.append(InputMediaPhoto(media=url))
        bot.send_media_group(chat_id=TELEGRAM_CHANNEL, media=media_group)
    elif text:
        bot.send_message(chat_id=TELEGRAM_CHANNEL, text=text)

    for video in videos:
        bot.send_message(chat_id=TELEGRAM_CHANNEL, text=f"🎥 Видео: {video}")

for group in VK_GROUP_IDS:
    print(f"🔍 Проверка группы: {group}")
    last_post_id = get_last_post_id(group)
    post = get_latest_post(group)

    if post and post['id'] != last_post_id:
        text = post.get("text", "")
        attachments = post.get("attachments", [])
        photos = extract_photos(attachments)
        videos = extract_video_links(attachments)

        post_to_telegram(text, photos, videos)
        save_last_post_id(group, post['id'])
        print(f"✅ Новый пост из {group} опубликован.")
    else:
        print(f"⏳ Нет новых постов в {group}")
