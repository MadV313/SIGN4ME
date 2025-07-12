# cogs/sign_settings.py — Adjust sign build parameters for Sign4Me bot

import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from utils.config_utils import get_guild_config, update_guild_config
from utils.permissions import is_admin_user
from logic.text_matrix import generate_letter_matrix
from logic.render_sign_preview import render_sign_preview
from zip_packager import create_qr_zip
from utils.channel_utils import get_channel_id

OBJECT_SIZE_ADJUSTMENTS = {
    "Armband_Black": 0.5,
    "JerryCan": 1.0,
    "BoxWooden": 1.0,
    "SmallProtectiveCase": 1.0,
    "WoodenCrate": 1.1,
    "ImprovisedContainer": 1.0,
    "DryBag_Black": 1.25
}

class SignSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="sign_settings", description="View current Sign4Me settings and optionally rebuild")
    async def sign_settings(self, interaction: discord.Interaction):
        if not is_admin_user(interaction):
            await interaction.response.send_message("❌ You do not have permission.", ephemeral=True)
            return

        guild_id = str(interaction.guild.id)
        config = get_guild_config(guild_id)
        view = SignAdjustPanelView(config, guild_id)
        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
        view.message = await interaction.original_response()

class SignAdjustPanelView(discord.ui.View):
    def __init__(self, config, guild_id):
        super().__init__(timeout=900)
        self.config = config
        self.guild_id = guild_id
        self.message = None

    def build_embed(self):
        obj = self.config.get("default_object", "WoodenCrate")
        spacing = self.config.get("custom_spacing", {}).get(obj, OBJECT_SIZE_ADJUSTMENTS.get(obj, 1.0))
        scale = self.config.get("custom_scale", {}).get(obj, self.config.get("defaultScale", 0.5))
        origin = self.config.get("origin_position", {"x": 5000.0, "y": 0.0, "z": 5000.0})

        embed = discord.Embed(title="🔧 Adjust Sign Settings", color=0x2ECC71)
        embed.add_field(name="Object Type", value=f"`{obj}`", inline=True)
        embed.add_field(name="Spacing", value=f"`{spacing}`", inline=True)
        embed.add_field(name="Scale", value=f"`{scale}`", inline=True)
        embed.add_field(
            name="Origin (User Input)",
            value=f"`X: {origin['x']}, Z: {origin['y']}`",
            inline=False
        )
        embed.add_field(
            name="⚠️ Placement Warning",
            value="Ensure scale/spacing is appropriate to avoid overlap or huge distances in-game.",
            inline=False
        )
        return embed

    async def interaction_check(self, interaction: discord.Interaction):
        return is_admin_user(interaction)

    @discord.ui.button(label="🧱 Adjust Object", style=discord.ButtonStyle.secondary)
    async def adjust_object(self, interaction: discord.Interaction, button: discord.ui.Button):
        options = [
            discord.SelectOption(label=obj, value=obj)
            for obj in OBJECT_SIZE_ADJUSTMENTS.keys()
        ]
        select = discord.ui.Select(placeholder="Select object", options=options)
        view = discord.ui.View(timeout=60)
        view.add_item(select)

        async def callback(i: discord.Interaction):
            selected = select.values[0]
            self.config["default_object"] = selected
            update_guild_config(self.guild_id, self.config)

            confirm = await i.response.send_message(f"✅ Object changed to `{selected}`", ephemeral=True)
            if self.message:
                await self.message.edit(embed=self.build_embed(), view=self)

            try:
                await i.message.delete()
            except:
                pass

            await asyncio.sleep(2)
            try:
                followup = await confirm
                await followup.delete()
            except:
                pass

        select.callback = callback
        await interaction.response.send_message("🔄 Choose object:", view=view, ephemeral=True)

    @discord.ui.button(label="📏 Adjust Scale", style=discord.ButtonStyle.secondary)
    async def adjust_scale(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdjustScaleModal(self))

    @discord.ui.button(label="📐 Adjust Spacing", style=discord.ButtonStyle.secondary)
    async def adjust_spacing(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdjustSpacingModal(self))

    @discord.ui.button(label="🌍 Adjust Origin", style=discord.ButtonStyle.secondary)
    async def adjust_origin(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdjustOriginModal(self))

    @discord.ui.button(label="🧮 Adjust Offset", style=discord.ButtonStyle.secondary)
    async def adjust_offset(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(AdjustOffsetModal(self))

    @discord.ui.button(label="✅ Approve + Rebuild", style=discord.ButtonStyle.green)
    async def approve_and_rebuild(self, interaction: discord.Interaction, button: discord.ui.Button):
        if "last_sign_data" not in self.config:
            await interaction.response.send_message("⚠️ No previous sign data found. Use `/signbuild` first.", ephemeral=True)
            return
        if self.message:
            try:
                await self.message.delete()
            except:
                pass
        await interaction.response.defer(ephemeral=True)
        await handle_sign_rebuild(interaction, self.config, self.guild_id)

# ─────────────── Modals ───────────────

class AdjustScaleModal(discord.ui.Modal, title="Set Scale"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        current = view.config.get("custom_scale", {}).get(view.config.get("default_object", "WoodenCrate"), view.config.get("defaultScale", 0.5))
        self.add_item(discord.ui.TextInput(label="Scale", default=str(current), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = float(self.children[0].value)
            obj = self.view.config.get("default_object", "WoodenCrate")
            self.view.config.setdefault("custom_scale", {})[obj] = val
            update_guild_config(self.view.guild_id, self.view.config)
            await interaction.response.edit_message(embed=self.view.build_embed(), view=self.view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid scale. Use a number.", ephemeral=True)

class AdjustSpacingModal(discord.ui.Modal, title="Set Spacing"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        obj = view.config.get("default_object", "WoodenCrate")
        val = view.config.get("custom_spacing", {}).get(obj, OBJECT_SIZE_ADJUSTMENTS.get(obj, 1.0))
        self.add_item(discord.ui.TextInput(label="Spacing", default=str(val), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = float(self.children[0].value)
            obj = self.view.config.get("default_object", "WoodenCrate")
            self.view.config.setdefault("custom_spacing", {})[obj] = val
            update_guild_config(self.view.guild_id, self.view.config)
            await interaction.response.edit_message(embed=self.view.build_embed(), view=self.view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid spacing. Use a number.", ephemeral=True)

class AdjustOriginModal(discord.ui.Modal, title="Set Origin Coordinates"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        origin = view.config.get("origin_position", {"x": 5000.0, "y": 0.0, "z": 5000.0})
        self.add_item(discord.ui.TextInput(label="Origin X", default=str(origin["x"]), required=True))
        self.add_item(discord.ui.TextInput(label="Origin Z (Depth)", default=str(origin["y"]), required=True))
        self.add_item(discord.ui.TextInput(label="Height (Y)", default=str(origin["z"]), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            x = float(self.children[0].value)
            z = float(self.children[1].value)
            y = float(self.children[2].value)
            self.view.config["origin_position"] = {"x": x, "y": z, "z": y}
            update_guild_config(self.view.guild_id, self.view.config)
            await interaction.response.edit_message(embed=self.view.build_embed(), view=self.view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid origin values.", ephemeral=True)

class AdjustOffsetModal(discord.ui.Modal, title="Set Origin Offset"):
    def __init__(self, view):
        super().__init__()
        self.view = view
        offset = view.config.get("originOffset", {"x": 0.0, "y": 0.0, "z": 0.0})
        self.add_item(discord.ui.TextInput(label="Offset X", default=str(offset["x"]), required=True))
        self.add_item(discord.ui.TextInput(label="Offset Y", default=str(offset["y"]), required=True))
        self.add_item(discord.ui.TextInput(label="Offset Z", default=str(offset["z"]), required=True))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            x = float(self.children[0].value)
            y = float(self.children[1].value)
            z = float(self.children[2].value)
            self.view.config["originOffset"] = {"x": x, "y": y, "z": z}
            update_guild_config(self.view.guild_id, self.view.config)
            await interaction.response.edit_message(embed=self.view.build_embed(), view=self.view)
        except ValueError:
            await interaction.response.send_message("❌ Invalid offset values.", ephemeral=True)

# ─────────────── Rebuild Logic ───────────────

async def handle_sign_rebuild(interaction: discord.Interaction, config: dict, guild_id: str):
    from logic.text_matrix import generate_letter_matrix
    from logic.render_sign_preview import render_sign_preview
    import json

    text = config["last_sign_data"]
    obj = config.get("default_object", "WoodenCrate")
    scale = config.get("custom_scale", {}).get(obj, config.get("defaultScale", 0.5))
    spacing = config.get("custom_spacing", {}).get(obj, config.get("defaultSpacing", 1.0))
    origin = config.get("origin_position", {"x": 5000.0, "y": 0.0, "z": 5000.0})
    offset = config.get("originOffset", {"x": 0.0, "y": 0.0, "z": 0.0})

    matrix = generate_letter_matrix(text)
    from cogs.signbuild import letter_to_object_list
    objects = letter_to_object_list(matrix, obj, origin, offset, scale=scale, spacing=spacing)

    with open(config["object_output_path"], "w") as f:
        json.dump(objects, f, indent=2)

    render_sign_preview(matrix, config["preview_output_path"], object_type=obj)

    channel_id = get_channel_id("gallery", guild_id) or config.get("admin_channel_id")
    channel = interaction.client.get_channel(int(channel_id)) if channel_id else None

    if channel:
        await channel.send(
            content=(
                f"🪧 **Sign Rebuild Complete**\n"
                f"• Size: {len(matrix[0])}x{len(matrix)}\n"
                f"• Objects: {len(objects)}\n"
                f"• Type: `{obj}`\n"
                f"• Scale: `{scale}` | Spacing: `{spacing}`\n"
                f"• Origin: X: {origin['x']}, Y: {origin['y']}, Z: {origin['z']}"
            ),
            files=[
                discord.File(config["object_output_path"], filename="Sign4ME.json"),
                discord.File(config["preview_output_path"])
            ]
        )

    await interaction.followup.send("✅ Settings applied and sign rebuilt.", ephemeral=True)

# ✅ Load this cog
async def setup(bot):
    await bot.add_cog(SignSettings(bot))
