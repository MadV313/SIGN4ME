# bot.py — Main launcher for the Sign4Me bot

import discord
from discord.ext import commands
import asyncio
import os
import json

TOKEN_PATH = "config.json"

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Sign4Me bot is online as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Failed to sync commands: {e}")

async def main():
    # Load all cogs in /cogs
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")

    # Load token from config.json
    if not os.path.exists(TOKEN_PATH):
        print("❌ config.json not found.")
        return
    with open(TOKEN_PATH, "r") as f:
        config = json.load(f)
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("❌ Bot token missing in config.json")
        return

    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())

