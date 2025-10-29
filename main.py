import os
import time
import discord
import requests
from discord import Embed
from discord.ext import tasks, commands
from flask import Flask
from threading import Thread

# === Secrets ===
SERVER_ID = os.getenv("SERVER_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# === Keep-alive server ===
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

# === Discord Bot ===
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

def fetch_links():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "Content-Type": "application/json"
    }
    url = f"https://groups.roblox.com/v2/groups/{SERVER_ID}/wall/posts"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        posts = res.json().get("data", [])
        links = []
        for post in posts:
            text = post.get("body", "")
            for word in text.split():
                if word.startswith("https://www.roblox.com/share?code="):
                    links.append(word)
        return links
    except Exception as e:
        print(f"[Error fetching links]: {e}")
        return []

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    fetch_and_send.start()

@tasks.loop(minutes=2)
async def fetch_and_send():
    try:
        links = fetch_links()
        if not links:
            print("⚠️ No links found.")
            return

        channel = bot.get_channel(CHANNEL_ID)
        if not channel:
            print("⚠️ Channel not found.")
            return

        embed = Embed(
            title="🎮 New Private Server Links",
            description="\n".join(links[:30]),
            color=0x00ffcc,
            timestamp=discord.utils.utcnow()
        )
        embed.set_footer(text=f"Made by SAB-RS • Updated just now")

        await channel.send(embed=embed)
        print(f"✅ Sent {len(links)} links to Discord.")
    except Exception as e:
        print(f"[Send Error]: {e}")

keep_alive()
bot.run(DISCORD_TOKEN)
