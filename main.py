import os
import threading
import requests
import discord
from discord.ext import tasks
from flask import Flask
from datetime import datetime

# ==== ENV VARS ====
SERVER_ID = os.getenv("SERVER_ID")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ==== DISCORD SETUP ====
intents = discord.Intents.default()
client = discord.Client(intents=intents)

# ==== FETCH LINKS ====
def fetch_links():
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    url = f"https://groups.roblox.com/v2/groups/{SERVER_ID}/wall/posts?limit=30&sortOrder=Desc"
    try:
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        posts = res.json().get("data", [])
        links = []
        for p in posts:
            body = p.get("body", "")
            for w in body.split():
                if w.startswith("https://www.roblox.com/share?code="):
                    links.append(w)
        return links
    except Exception as e:
        print(f"[fetch_links] {e}")
        return []

# ==== DISCORD TASK ====
@tasks.loop(minutes=1)
async def fetch_and_send():
    try:
        channel = await client.fetch_channel(CHANNEL_ID)
        links = fetch_links()
        if not links:
            print(f"[{datetime.utcnow().isoformat()}] No links found.")
            return
        links = list(dict.fromkeys(links))[:30]  # unique + limit 30
        embed = discord.Embed(
            title="🎮 New Private Server Links",
            description="\n".join(f"• {l}" for l in links),
            color=0x00FFCC,
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text="Made by SAB-RS • Updated just now")
        await channel.send(embed=embed)
        print(f"[{datetime.utcnow().isoformat()}] Sent {len(links)} links.")
    except Exception as e:
        print(f"[fetch_and_send] {e}")

@client.event
async def on_ready():
    print(f"✅ Logged in as {client.user}")
    if not fetch_and_send.is_running():
        fetch_and_send.start()

# ==== FLASK KEEP-ALIVE ====
app = Flask(__name__)

@app.route("/")
def home():
    return "SAB-RS bot active"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

def run_discord():
    client.run(DISCORD_TOKEN)

# ==== START BOTH ====
if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_discord()
