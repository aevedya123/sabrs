import os
import requests
import time
import re
from keep_alive import keep_alive
keep_alive()
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
WEBHOOK_URL = os.getenv("WEBHOOK_URL") or os.getenv("BOT_LINK")

HEADERS = {
    "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
    "User-Agent": "RobloxGroupScraper/1.0"
}

LINK_PATTERN = re.compile(r"(https?://[^\s]+)")
seen_links = set()

def get_group_posts(group_id, limit=10):
    url = f"https://groups.roblox.com/v2/groups/{group_id}/wall/posts?limit={limit}"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json().get("data", [])
    else:
        print(f"Failed to fetch posts: {response.status_code}")
        return []

def extract_links_from_posts(posts):
    links = []
    for post in posts:
        content = post.get("body", "")
        found = LINK_PATTERN.findall(content)
        links.extend(found)
    return links

def send_to_discord(links):
    if not links:
        return
    embed = {
        "title": "🔗 New Private Server Links Found",
        "description": "\n".join(links),
        "color": 0x2ECC71,
        "footer": {"text": "Made by SAB-RS"}
    }
    payload = {"embeds": [embed]}
    requests.post(WEBHOOK_URL, json=payload)

def main():
    print("✅ Started monitoring Roblox group wall!")
    while True:
        posts = get_group_posts(GROUP_ID, limit=20)
        new_links = []
        for link in extract_links_from_posts(posts):
            if link not in seen_links and "private" in link.lower():
                seen_links.add(link)
                new_links.append(link)
        if new_links:
            print(f"Found {len(new_links)} new private links")
            send_to_discord(new_links[:30])
        time.sleep(60)  # every minute

if __name__ == "__main__":
    main()
