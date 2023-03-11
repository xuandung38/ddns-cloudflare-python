import requests
import json
import time
import os
import redis

from telegram.ext import Updater, CommandHandler

# Các thông tin cần thiết để thực hiện truy vấn tới API của Cloudflare
zone_id = os.environ.get('CF_ZONE_ID')
record_id = os.environ.get('CF_RECORD_ID')
domain = os.environ.get('CF_RECORD_DOMAIN')
api_token = os.environ.get('CF_API_TOKEN')

# Các thông tin cần thiết để gửi thông báo tới Telegram
bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')

redis_host = os.environ.get('REDIS_HOST')
redis_port = os.environ.get('REDIS_PORT', 6379)

redis = redis.Redis(host=redis_host, port=redis_port, db=0, charset="utf-8", decode_responses=True)

def get_current_ip():
    # Thực hiện truy vấn tới API để lấy địa chỉ IP mới nhất
    response = requests.get('https://api64.ipify.org/?format=json')
    ip_address = json.loads(response.text)['ip']
    return ip_address


def update_cloudflare_record(ip_address):
    # Cập nhật địa chỉ IP mới nhất lên Cloudflare
    previous_ip = str(redis.get('previous_ip'))

    send_telegram_notification(f"Ip hiện tại {ip_address}, Ip cũ {previous_ip}")
    if ip_address == previous_ip:
        send_telegram_notification(f"Ip của bạn không thay đổi {previous_ip}")
        return
    redis.set('previous_ip', current_ip)

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }
    data = {
        "type": "A",
        "name": domain,  # Tên miền của bạn
        "content": ip_address,
        "ttl": 120,
        "proxied": True
    }
    url = f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}'
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        msg = f'Successfully updated Cloudflare record with IP address: {ip_address}'
        send_telegram_notification(msg)
        print(msg)
    else:
        msg = 'Error updating Cloudflare record'
        send_telegram_notification(msg)
        print(msg)


def send_telegram_notification(message):
    # Gửi thông báo tới Telegram
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'
    data = {'chat_id': chat_id, 'text': message}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print(f'Successfully sent Telegram notification: {message}')
    else:
        print('Error sending Telegram notification')


def start(update, context):
    # Gửi lời chào đến người dùng khi BOT được khởi động
    context.bot.send_message(chat_id=update.effective_chat.id,
                             text='Hello! I am your IP updater bot. Please use the /ip command to update your IP address.')


def update_ip_address(update, context):
    # Cập nhật địa chỉ IP mới nhất khi có yêu cầu từ người dùng
    current_ip = get_current_ip()
    update_cloudflare_record(current_ip)


# Thiết lập bot và khởi động lắng nghe tin nhắn từ người dùng
updater = Updater(token=bot_token, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start))
dispatcher.add_handler(CommandHandler('ip', update_ip_address))
updater.start_polling()

# Vòng lặp vô hạn để kiểm tra và cập nhật địa chỉ IP mới nhất
while True:
    current_ip = get_current_ip()
    update_cloudflare_record(current_ip)
    time.sleep(60)  # Chờ 5 phút trước khi kiểm tra lại
