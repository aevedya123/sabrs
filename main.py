import os
import re
import time
import asyncio
import requests
import discord
from discord import Embed
from datetime import datetime
from keep_alive import keep_alive

# ---- ENVIRONMENT VARIABLES ----
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
GROUP_ID = os.getenv("GROUP_ID")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

# ---- DISCORD CLIENT SETUP ----
intents = discord.Intents.default()

class RobloxLinkBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.posted_links = set()
        self.headers = {
            "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json"
        }

    async def setup_hook(self):
        """Async-safe setup hook (replaces on_ready loop tasks)."""
        self.bg_task = asyncio.create_task(self.monitor_group_wall())

    async def on_ready(self):
        print(f"🤖 Logged in as {self.user}")
        print("✅ Bot started successfully! Monitoring group wall...")

    def fetch_group_posts(self):
        """Fetch posts from the group wall."""
        try:
            url = f"https://groups.roblox.com/v2/groups/{GROUP_ID}/wall/posts?limit=100&sortOrder=Desc"
            r = requests.get(url, headers=self.headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                return [p["body"] for p in data.get("data", [])]
            else:
                print(f"⚠️ Error fetching posts: {r.status_code}")
        except Exception as e:
            print(f"❌ Exception while fetching posts: {e}")
        return []

    async def monitor_group_wall(self):
        """Monitors the group wall for new share links."""
        await self.wait_until_ready()
        channel = self.get_channel(CHANNEL_ID)
        if not channel:
            print("❌ Channel not found. Check CHANNEL_ID.")
            return

        while not self.is_closed():
            posts = self.fetch_group_posts()
            new_links = []

            for post in posts:
                links = re.findall(r"https?://www\.roblox\.com/share\?[^ \n]+", post)
                for link in links:
                    if link not in self.posted_links:
                        self.posted_links.add(link)
                        new_links.append(link)

            if new_links:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                embed = Embed(
                    title="🔗 New Private Server Links",
                    description="\n".join(new_links[:30]),
                    color=0x00ffcc
                )
                embed.set_footer(text=f"Made by SAB-RS | {now}")
                await channel.send(embed=embed)
                print(f"✅ Sent {len(new_links[:30])} links to Discord at {now}.")

            await asyncio.sleep(60)  # Wait 1 minute before checking again


# ---- RUN BOT ----
def run_bot():
    keep_alive()
    bot = RobloxLinkBot()

    for attempt in range(10):
        try:
            bot.run(DISCORD_TOKEN)
            break
        except Exception as e:
            print(f"⚠️ Bot crashed (attempt {attempt + 1}/10): {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
