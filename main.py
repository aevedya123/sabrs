import os
import requests
import discord
from discord.ext import commands, tasks
import asyncio
import datetime
from keep_alive import keep_alive
keep_alive()

# ==== CONFIG ====
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
SERVER_ID = os.getenv("SERVER_ID")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ==== GRAB LINKS FUNCTION ====
async def grab_links():
    headers = {
        ".ROBLOSECURITY": ROBLOX_COOKIE,
        "User-Agent": "Roblox/WinInet"
    }
    url = f"https://groups.roblox.com/v1/groups/{SERVER_ID}/wall/posts"
    response = requests.get(url, cookies=headers)

    if response.status_code != 200:
        return None

    data = response.json()
    posts = data.get("data", [])
    links = [p["body"] for p in posts if "roblox.com/share?code=" in p["body"]]
    return links[:10] if links else None


# ==== TASK TO SEND LINKS ====
@tasks.loop(minutes=10)
async def send_links():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        print("❌ Channel not found.")
        return

    links = await grab_links()
    if not links:
        await channel.send("⚠️ No new links found.")
        return

    # Prepare formatted link text
    links_text = "\n".join(f"• {link}" for link in links)

    # Timestamp for Discord (local for each user)
    timestamp = int(datetime.datetime.utcnow().timestamp())

    embed = discord.Embed(
        title="🔗 Roblox Private Server Links",
        description=f"{links_text}\n\n🕒 Posted <t:{timestamp}:R>",
        color=0x00ffcc
    )
    embed.set_footer(text="Made by SAB-RS")

    await channel.send(embed=embed)
    print(f"✅ Sent {len(links)} links at {datetime.datetime.now()}")


# ==== EVENTS ====
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    send_links.start()


# ==== KEEP ALIVE (if using Flask/ping) ====
from keep_alive import keep_alive
keep_alive()

# ==== RUN ====
async def main():
    async with bot:
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())
