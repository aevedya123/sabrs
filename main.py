import sys, types
sys.modules['audioop'] = types.SimpleNamespace()
import os
import re
import json
import asyncio
from datetime import datetime
import aiohttp
import discord
from discord import Embed
from keep_alive import keep_alive

# Start Flask keep-alive server
keep_alive()

# --- Environment variables ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# --- Config ---
CHECK_INTERVAL = 60
POSTED_FILE = "posted_links.json"
USER_AGENT = "SABRS-LinkBot/2.0"
SHARE_REGEX = re.compile(r"https?://(?:www\.)?roblox\.com/share\?[^\s)\"'<>]+", re.IGNORECASE)

# --- Discord setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

def load_posted():
    if not os.path.exists(POSTED_FILE):
        return set()
    try:
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    except:
        return set()

def save_posted(data):
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(data)), f)

async def fetch_group_wall(session, limit=30):
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit={limit}&sortOrder=Desc"
    headers = {
        "User-Agent": USER_AGENT,
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "Accept": "application/json"
    }
    async with session.get(url, headers=headers, timeout=20) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("data", [])
        else:
            print(f"[{datetime.utcnow()}] Roblox API error: {resp.status}")
            return []

def extract_links(text):
    return SHARE_REGEX.findall(text or "")

async def poll_loop():
    await client.wait_until_ready()
    channel = await client.fetch_channel(CHANNEL_ID)
    posted = load_posted()

    async with aiohttp.ClientSession() as session:
        while not client.is_closed():
            try:
                posts = await fetch_group_wall(session)
                new_links = []

                for post in reversed(posts):
                    body = post.get("body", "")
                    pid = str(post.get("id"))
                    links = extract_links(body)
                    for link in links:
                        key = f"{pid}|{link}"
                        if key not in posted:
                            new_links.append((link, key))

                if new_links:
                    BATCH = 10
                    for i in range(0, len(new_links), BATCH):
                        chunk = [li for li, _ in new_links[i:i+BATCH]]
                        desc = "\n".join(f"• {c}" for c in chunk)
                        embed = Embed(
                            title="🔗 New Roblox Share Links",
                            description=desc,
                            color=0x00FFCC,
                            timestamp=datetime.utcnow()
                        )
                        embed.set_footer(text=f"Made by SAB-RS • Updated {datetime.utcnow().strftime('%H:%M:%S UTC')}")
                        await channel.send(embed=embed)
                    
                    for _, key in new_links:
                        posted.add(key)
                    save_posted(posted)

                await asyncio.sleep(CHECK_INTERVAL)

            except Exception as e:
                print(f"[{datetime.utcnow()}] Error in poll loop: {e}")
                await asyncio.sleep(30)

@client.event
async def on_ready():
    print(f"[{datetime.utcnow()}] ✅ Logged in as {client.user}")
    asyncio.create_task(poll_loop())

if __name__ == "__main__":
    print(f"[{datetime.utcnow()}] Starting bot...")
    client.run(DISCORD_TOKEN)
