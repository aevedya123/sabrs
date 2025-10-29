import os
import re
import asyncio
import discord
import requests
from discord import Embed
from discord.ext import tasks, commands
from datetime import datetime, timezone
from flask import Flask
from threading import Thread

# --- ENV variables ---
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# --- Discord setup ---
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# --- Flask keep-alive setup ---
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    thread = Thread(target=run_flask)
    thread.start()

# --- Roblox Group Post Scraper ---
def get_group_links():
    url = f"https://groups.roblox.com/v1/groups/{SERVER_ID}/wall/posts?limit=100"
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        print(f"❌ Error {response.status_code}: {response.text}")
        return []

    data = response.json()
    posts = data.get("data", [])
    links = []

    for post in posts:
        content = post.get("body", "")
        found_links = re.findall(r"https:\/\/www\.roblox\.com\/share\?code=[a-zA-Z0-9]+", content)
        links.extend(found_links)

    return links

# --- Task Loop to Monitor Wall ---
@tasks.loop(seconds=60)
async def check_group_wall():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("⚠️ Channel not found.")
        return

    links = get_group_links()
    if not links:
        print("ℹ️ No new links found.")
        return

    for link in links[:30]:  # Limit to 30 per minute
        embed = Embed(
            title="📢 New Private Server Link Found!",
            description=f"[Join Here]({link})",
            color=0x00ff88,
            timestamp=datetime.now(timezone.utc)
        )
        embed.set_footer(text="Made by SAB-RS")
        await channel.send(embed=embed)

# --- Startup Events ---
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not check_group_wall.is_running():
        check_group_wall.start()

# --- Run ---
if __name__ == "__main__":
    keep_alive()
    bot.run(DISCORD_TOKEN)
