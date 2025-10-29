import sys, types
sys.modules['audioop'] = types.SimpleNamespace()
import os
import discord
import aiohttp
from discord import app_commands
from datetime import datetime, timezone

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = os.getenv("GROUP_ID")

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# === Fetch Roblox Group Wall Posts ===
async def get_group_wall_links():
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "Content-Type": "application/json"
    }
    url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?sortOrder=Desc&limit=100"
    links = []

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            if resp.status != 200:
                print(f"[{datetime.now(timezone.utc)}] Roblox API error: {resp.status}")
                return []
            data = await resp.json()

            for post in data.get("data", []):
                content = post.get("body", "")
                # Extract Roblox share links (example: https://www.roblox.com/share?code=XXXX&type=Server)
                for word in content.split():
                    if word.startswith("https://www.roblox.com/share?code="):
                        if word not in links:
                            links.append(word)

    # Limit to 30 links max
    return links[:30]

# === Slash Command ===
@tree.command(name="links", description="Fetch the latest Roblox group share links")
async def links_command(interaction: discord.Interaction):
    await interaction.response.defer()  # To prevent timeout while fetching
    links = await get_group_wall_links()

    if not links:
        await interaction.followup.send("⚠️ No links found on the group wall.")
        return

    embed = discord.Embed(
        title="Latest Roblox Private Server Links",
        color=discord.Color.green(),
        description="\n".join(links)
    )
    embed.set_footer(text=f"Made by SAB-RS • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    await interaction.followup.send(embed=embed)

# === When Bot Starts ===
@client.event
async def on_ready():
    await tree.sync()
    print(f"[{datetime.now(timezone.utc)}] ✅ Logged in as {client.user} (slash commands synced)")

client.run(DISCORD_TOKEN)
from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot running!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    # your discord bot launch below:
    import sys, types
    sys.modules['audioop'] = types.SimpleNamespace()
    import discord, asyncio
    # ... rest of bot startup code ...
