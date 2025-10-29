import os
import re
import json
import asyncio
import aiohttp
import datetime
from discord import Embed, Intents
from discord.ext import commands
from flask import Flask
from threading import Thread

# ---- ENVIRONMENT VARIABLES ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

if not all([DISCORD_TOKEN, CHANNEL_ID, GROUP_ID, ROBLOX_COOKIE]):
    raise SystemExit("Missing one or more required environment variables.")

# ---- SETTINGS ----
CHECK_INTERVAL = 60  # seconds
MAX_LINKS = 30
POSTED_FILE = "posted_links.json"
USER_AGENT = "SABRS-LinkBot/2.0"
LINK_REGEX = re.compile(r"https?://(?:www\.)?roblox\.com/share\?[^\s)\"'<>]+", re.IGNORECASE)

# ---- DISCORD SETUP ----
intents = Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---- FLASK KEEP-ALIVE ----
app = Flask(__name__)

@app.route("/")
def home():
    return "SABRS-LinkBot is running."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---- DATA STORAGE ----
def load_posted():
    if os.path.exists(POSTED_FILE):
        with open(POSTED_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_posted(posted):
    with open(POSTED_FILE, "w", encoding="utf-8") as f:
        json.dump(sorted(list(posted)), f, indent=2)

# ---- FETCH GROUP WALL ----
async def fetch_group_posts(session, limit=50):
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?sortOrder=Desc&limit={limit}"
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"
    }
    async with session.get(url, headers=headers) as resp:
        if resp.status == 200:
            data = await resp.json()
            return data.get("data", [])
        return []

# ---- POLL LOOP ----
async def poll_links():
    await bot.wait_until_ready()
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Invalid Discord channel ID.")
        return

    posted = load_posted()

    async with aiohttp.ClientSession() as session:
        while not bot.is_closed():
            print(f"[{datetime.datetime.now()}] Checking for new links...")
            posts = await fetch_group_posts(session, limit=50)
            new_links = []

            for post in reversed(posts):
                post_id = str(post.get("id"))
                body = post.get("body", "")
                matches = LINK_REGEX.findall(body)
                for link in matches:
                    key = f"{post_id}|{link}"
                    if key not in posted:
                        new_links.append((link, key))

            if new_links:
                all_links = [link for link, _ in new_links][-MAX_LINKS:]
                description = "\n".join(f"• {link}" for link in all_links)
                timestamp = int(datetime.datetime.now(datetime.UTC).timestamp())

                embed = Embed(
                    title="🔗 New Roblox Private Server Links",
                    description=description,
                    color=0x00FFCC,
                    timestamp=datetime.datetime.now(datetime.UTC)
                )
                embed.set_footer(text=f"Made by SAB-RS • Posted <t:{timestamp}:R>")

                try:
                    await channel.send(embed=embed)
                    print(f"✅ Sent {len(all_links)} new links.")
                    for _, key in new_links:
                        posted.add(key)
                    save_posted(posted)
                except Exception as e:
                    print(f"⚠️ Failed to send embed: {e}")
            else:
                print("No new share links found.")

            await asyncio.sleep(CHECK_INTERVAL)

# ---- STARTUP ----
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    bot.loop.create_task(poll_links())

if __name__ == "__main__":
    Thread(target=run_flask, daemon=True).start()
    bot.run(DISCORD_TOKEN)
