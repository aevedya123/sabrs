import os
import re
import aiohttp
import asyncio
import discord
import audioop
from discord import Embed
from flask import Flask
from threading import Thread

# === Environment Variables ===
TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
GROUP_ID = os.getenv("SERVER_ID")
COOKIE = os.getenv("ROBLOX_COOKIE")

BASE_URL = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"

# === Discord Setup ===
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# === Flask Keep-Alive ===
app = Flask(__name__)

@app.route('/')
def home():
    return "✅ SAB-RS Bot is alive."

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    Thread(target=run_flask).start()

# === Memory to avoid duplicate links ===
seen_post_ids = set()
seen_links = set()

# === Fetch Roblox Group Wall ===
async def fetch_group_posts():
    headers = {
        "Cookie": f".ROBLOSECURITY={COOKIE}",
        "User-Agent": "Mozilla/5.0"
    }
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(BASE_URL) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("data", [])
            else:
                print(f"⚠️ Roblox API error {resp.status}")
                return []

# === Extract ONLY Private Server Links ===
async def extract_private_links():
    posts = await fetch_group_posts()
    new_links = []
    for post in posts:
        post_id = post.get("id")
        if post_id in seen_post_ids:
            continue
        seen_post_ids.add(post_id)

        body = post.get("body", "")
        # Only match private server/share links
        matches = re.findall(r"https://www\.roblox\.com/share\?code=[A-Za-z0-9]+&type=Server", body)
        for link in matches:
            if link not in seen_links:
                seen_links.add(link)
                new_links.append(link)

    return new_links[:30]  # limit 30 per minute

# === Discord on_ready event ===
@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    channel = client.get_channel(CHANNEL_ID)
    while True:
        links = await extract_private_links()
        if links:
            formatted = "\n".join([f"• {l}" for l in links])
            embed = Embed(
                title="🔗 New Roblox Private Server Links",
                description=formatted,
                color=discord.Color.teal()
            )
            embed.set_footer(text="Made by SAB-RS")
            await channel.send(embed=embed)
            print(f"📤 Sent {len(links)} new private server links.")
        else:
            print("🔍 No new private server links found.")
        await asyncio.sleep(60)  # Check every minute

# === Start Everything ===
if __name__ == "__main__":
    keep_alive()
    client.run(TOKEN)
