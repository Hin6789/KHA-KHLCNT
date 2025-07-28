import requests
from bs4 import BeautifulSoup
import json
import time
import datetime
import threading
from config import WEBHOOK_URL, PROVINCE_NAME

def fetch_latest_packages():
    url = "https://muasamcong.mpi.gov.vn/web/guest/ke-hoach-lua-chon-nha-thau"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')

    script_tag = soup.find('script', string=lambda text: 'window.__INITIAL_STATE__' in text if text else False)
    if not script_tag:
        return []

    json_text = script_tag.string.strip().split(' = ', 1)[-1].rstrip(';')
    data = json.loads(json_text)
    try:
        plans = data['planList']['list']
    except KeyError:
        return []

    results = []
    for plan in plans:
        if PROVINCE_NAME in plan.get('districtName', ''):
            results.append({
                'tenderName': plan['tenderName'],
                'bidNo': plan['bidNo'],
                'investorName': plan['investorName'],
                'publicDate': plan['publicDate'],
                'link': f"https://muasamcong.mpi.gov.vn/web/guest/ke-hoach-lua-chon-nha-thau/-/view_details/{plan['id']}"
            })

    return results

def send_to_discord(message):
    data = {"content": message}
    response = requests.post(WEBHOOK_URL, json=data)
    return response.status_code == 204

def notify_new_plans():
    notified = set()
    while True:
        try:
            new_data = fetch_latest_packages()
            for item in new_data:
                if item['bidNo'] not in notified:
                    msg = (
                        f"📌 **{item['tenderName']}**\n"
                        f"🆔 Mã gói: `{item['bidNo']}`\n"
                        f"🏢 Chủ đầu tư: {item['investorName']}\n"
                        f"📅 Ngày công bố: {item['publicDate']}\n"
                        f"🔗 [Xem chi tiết]({item['link']})"
                    )
                    send_to_discord(msg)
                    notified.add(item['bidNo'])
        except Exception as e:
            print("Lỗi:", e)

        time.sleep(60 * 5)  # kiểm tra mỗi 5 phút

if __name__ == "__main__":
    notify_thread = threading.Thread(target=notify_new_plans)
    notify_thread.start()
