# cogs/help.py — Slash command help panel for Sign4Me bot

import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show command usage for Sign4Me Bot")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="📘 Sign4Me Bot Help",
            description="🛠️ Setup your build correctly by following the command flow below.\n"
                        "Make sure to run `/setorigin` and `/sign_settings` before building anything.\n\n"
                        "Here are the available bot commands:",
            color=discord.Color.blurple()
        )

        # 🔧 Setup Commands
        embed.add_field(
            name="🔧 Setup Commands",
            value=(
                "**/setorigin** — Set the in-game X/Y/Z coordinates for sign placement.\n"
                "**/sign_settings** — View and fine-tune object settings like scale, spacing, origin, and offset.\n"
                "  ➤ Adjust object type used in builds.\n"
                "  ➤ Rebuild the last sign layout using updated settings."
            ),
            inline=False
        )

        # 🪧 Build Commands
        embed.add_field(
            name="🪧 Build Commands",
            value=(
                "**/signbuild** — Convert capitalized text into an in-game sign made of item objects.\n"
                "**/cleanup** — Delete the most recent build preview and export files."
            ),
            inline=False
        )

        # ⚙️ Configuration & Admin Tools
        embed.add_field(
            name="⚙️ Configuration & Admin Tools",
            value=(
                "**/setchannel** — Assign admin or gallery channels.\n"
                "**/giveperms** — Grant a user permission to use bot commands without an admin role.\n"
                "**/revokeperms** — Revoke a user’s permission to run Sign4Me commands."
            ),
            inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
