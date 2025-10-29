import os
import asyncio
import json
import requests
from datetime import datetime, timezone
from threading import Thread
from flask import Flask
import discord
from discord.ext import tasks

# --- Prevent audioop import issue ---
import sys, types
sys.modules['audioop'] = types.SimpleNamespace()

# --- Environment Variables ---
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# --- Flask Keepalive Server ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive", 200

def run_flask():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_flask, daemon=True).start()

# --- Discord Client Setup ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# --- Roblox API Fetch Function ---
def fetch_group_wall_posts():
    try:
        headers = {
            "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
            "User-Agent": "Mozilla/5.0"
        }
        url = f"https://groups.roblox.com/v2/groups/{SERVER_ID}/wall/posts?sortOrder=Desc&limit=10"
        resp = requests.get(url, headers=headers)

        if resp.status_code != 200:
            print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status_code}")
            return []

        data = resp.json()
        posts = data.get("data", [])
        links = []

        for post in posts:
            content = post.get("body", "")
            for word in content.split():
                if word.startswith("https://www.roblox.com/share?code="):
                    links.append(word)
        return links

    except Exception as e:
        print(f"[{datetime.now(timezone.utc)}] ❌ Error fetching wall posts: {e}")
        return []

# --- Background Task ---
last_sent_links = set()

@tasks.loop(minutes=3)
async def check_and_send_links():
    global last_sent_links
    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        print(f"[{datetime.now(timezone.utc)}] ⚠️ Channel not found.")
        return

    links = fetch_group_wall_posts()
    new_links = [link for link in links if link not in last_sent_links]

    if new_links:
        for link in new_links:
            try:
                await channel.send(link)
                print(f"[{datetime.now(timezone.utc)}] ✅ Sent: {link}")
            except Exception as e:
                print(f"[{datetime.now(timezone.utc)}] ❌ Failed to send {link}: {e}")
        last_sent_links.update(new_links)
    else:
        print(f"[{datetime.now(timezone.utc)}] No new links found.")

# --- On Ready Event ---
@client.event
async def on_ready():
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user}")
    check_and_send_links.start()

# --- Run the Bot ---
if __name__ == "__main__":
    client.run(DISCORD_TOKEN)
