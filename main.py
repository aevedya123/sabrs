import discord
from discord.ext import tasks
import requests
import asyncio
import os
from datetime import datetime, timezone
from keep_alive import keep_alive

# ==============================
# CONFIGURATION
# ==============================
GROUP_ID = os.getenv("GROUP_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ==============================
# DISCORD CLIENT SETUP
# ==============================
intents = discord.Intents.default()
client = discord.Client(intents=intents)

headers = {
    "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
    "Content-Type": "application/json"
}

# Helper function to get group wall posts and extract share links
def get_group_links():
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts"
    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        links = []
        for post in data.get("data", []):
            text = post.get("body", "")
            for word in text.split():
                if word.startswith("https://www.roblox.com/share?code="):
                    links.append(word)
        return links[:30]  # Max 30 per minute
    except Exception as e:
        print(f"Error fetching group links: {e}")
        return []

# Task to post links
@tasks.loop(minutes=1)
async def fetch_and_send_links():
    try:
        channel = client.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Channel not found!")
            return

        links = get_group_links()
        if not links:
            print("No new links found.")
            return

        embed = discord.Embed(
            title="📦 New Roblox Private Server Links",
            description="\n".join(links),
            color=discord.Color.blue()
        )

        now = datetime.now(timezone.utc)
        embed.set_footer(
            text=f"Made by SAB-RS • {discord.utils.format_dt(now, style='R')}"
        )

        await channel.send(embed=embed)
        print(f"✅ Sent {len(links)} links to Discord.")

    except Exception as e:
        print(f"⚠️ Bot crashed: {e}")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    fetch_and_send_links.start()

# Start Flask keep_alive server
keep_alive()

# Start bot loop
try:
    asyncio.run(client.start(DISCORD_TOKEN))
except KeyboardInterrupt:
    print("Bot stopped manually.")
