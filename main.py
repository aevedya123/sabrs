import os
import time
import re
import requests
import asyncio
import discord
from discord import Embed
from keep_alive import keep_alive

# Environment Variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = os.getenv("GROUP_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# Discord client setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

HEADERS = {
    "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}

POSTED_LINKS = set()
RETRIES = 10  # retry limit

def fetch_group_posts():
    """Fetch the group wall posts."""
    try:
        url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit=100&sortOrder=Desc"
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            posts = [p["body"] for p in data.get("data", [])]
            return posts
        else:
            print(f"⚠️ Error fetching posts: {response.status_code}")
    except Exception as e:
        print(f"❌ Exception while fetching posts: {e}")
    return []

async def send_links():
    """Fetch and send new links to Discord."""
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Could not find the Discord channel.")
        return

    print("✅ Bot started successfully! Monitoring group wall...")
    while not client.is_closed():
        posts = fetch_group_posts()
        new_links = []

        for post in posts:
            links = re.findall(r"https?://www\.roblox\.com/share\?[^ \n]+", post)
            for link in links:
                if link not in POSTED_LINKS:
                    POSTED_LINKS.add(link)
                    new_links.append(link)

        if new_links:
            embed = Embed(
                title="🔗 New Private Server Links",
                description="\n".join(new_links[:30]),
                color=0x00ffcc
            )
            embed.set_footer(text="Made by SAB-RS")
            await channel.send(embed=embed)
            print(f"✅ Sent {len(new_links[:30])} links to Discord.")

        await asyncio.sleep(60)  # Check once per minute

@client.event
async def on_ready():
    print(f"🤖 Logged in as {client.user}")
    client.loop.create_task(send_links())

def run_bot():
    """Attempt to run bot with retries."""
    keep_alive()  # Start once
    for attempt in range(RETRIES):
        try:
            client.run(DISCORD_TOKEN)
            break
        except Exception as e:
            print(f"⚠️ Bot crashed (attempt {attempt + 1}/{RETRIES}): {e}")
            time.sleep(5)
    print("❌ Bot failed after max retries.")

if __name__ == "__main__":
    run_bot()
