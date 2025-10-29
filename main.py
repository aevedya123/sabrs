import os
import re
import time
import types
import asyncio
import aiohttp
import discord
from discord import Embed
from datetime import datetime, timezone
from flask import Flask

# Patch audioop for Python 3.13
import sys
sys.modules['audioop'] = types.SimpleNamespace()

# Environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")

# Flask keep-alive server for Render
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# Discord setup
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# Regex for Roblox share links
LINK_REGEX = re.compile(r"https:\/\/www\.roblox\.com\/share\?code=[A-Za-z0-9]+&type=Server")

# For remembering seen posts
seen_posts = set()

async def fetch_group_posts():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status}")
                return []
            data = await resp.json()
            posts = data.get("data", [])
            links = []

            for post in posts:
                post_id = post.get("id")
                if post_id in seen_posts:
                    continue
                seen_posts.add(post_id)
                content = post.get("body", "")
                found = LINK_REGEX.findall(content)
                links.extend(found)

            return links[:30]  # limit to 30 links per minute

async def send_links_periodically():
    await client.wait_until_ready()
    channel = client.get_channel(CHANNEL_ID)

    if not channel:
        print("❌ Channel not found. Check CHANNEL_ID.")
        return

    while not client.is_closed():
        links = await fetch_group_posts()
        if links:
            embed = Embed(
                title="🌀 New Roblox Private Server Links",
                description="\n".join(links),
                color=discord.Color.blue(),
                timestamp=datetime.now(timezone.utc)
            )
            relative_time = discord.utils.format_dt(datetime.now(timezone.utc), style='R')
            embed.set_footer(text=f"Made by SAB-RS • {relative_time}")
            await channel.send(embed=embed)
            print(f"[{datetime.now(timezone.utc)}] ✅ Sent {len(links)} links.")
        else:
            print(f"[{datetime.now(timezone.utc)}] No new links found.")
        await asyncio.sleep(60)  # wait 1 minute

@client.event
async def on_ready():
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user}")
    client.loop.create_task(send_links_periodically())

if __name__ == "__main__":
    from threading import Thread
    Thread(target=run_flask).start()
    client.run(DISCORD_TOKEN)
