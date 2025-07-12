# cogs/signbuild.py

import discord
from discord.ext import commands
from discord import app_commands
import os

from utils.config_utils import get_guild_config, save_guild_config
from logic.text_matrix import generate_letter_matrix
from logic.render_sign_preview import render_sign_preview
from sign_packager import create_qr_zip
from utils.channel_utils import get_channel_id
from utils.permissions import is_admin_user

def letter_to_object_list(matrix, object_type, origin, offset, scale=0.5, spacing=1.0):
    objects = []
    for y, row in enumerate(matrix):
        for x, cell in enumerate(row):
            if cell != "#":
                continue
            pos_x = origin["x"] + offset["x"] + (x * spacing * scale)
            pos_y = origin["y"] + offset["y"]
            pos_z = origin["z"] + offset["z"] + (y * spacing * scale)
            objects.append({
                "name": object_type,
                "pos": [round(pos_x, 2), round(pos_y, 2), round(pos_z, 2)],
                "ypr": [0, 0, 0]
            })
    return objects

class SignBuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="signbuild", description="Convert text into a DayZ item sign layout")
    @app_commands.describe(
        text="The capital letters to build as a sign (A-Z only)",
        overall_scale="Overall object scale multiplier (default 0.5 or overridden per object)",
        object_spacing="Spacing between objects (default 1.0 or overridden per object)",
        object_type="Choose the object to use for the sign"
    )
    @app_commands.choices(
        object_type=[
            app_commands.Choice(name="Armband (Black)", value="Armband_Black"),
            app_commands.Choice(name="Jerry Can", value="JerryCan"),
            app_commands.Choice(name="Box Wooden", value="BoxWooden"),
            app_commands.Choice(name="Small Protective Case", value="SmallProtectiveCase"),
            app_commands.Choice(name="Wooden Crate", value="WoodenCrate"),
            app_commands.Choice(name="Improvised Container", value="ImprovisedContainer"),
            app_commands.Choice(name="Dry Bag (Black)", value="DryBag_Black"),
        ]
    )
    async def signbuild(
        self,
        interaction: discord.Interaction,
        text: str,
        object_type: app_commands.Choice[str],
        overall_scale: float = None,
        object_spacing: float = None
    ):
        if not is_admin_user(interaction):
            await interaction.response.send_message("❌ You do not have permission to use this command.", ephemeral=True)
            return

        await interaction.response.defer()

        guild_id = str(interaction.guild.id)
        config = get_guild_config(guild_id)
        obj_type = object_type.value
        origin = config.get("origin_position", {"x": 0.0, "y": 0.0, "z": 0.0})
        offset = config.get("originOffset", {"x": 0.0, "y": 0.0, "z": 0.0})

        # Use overrides or fallback config values
        overall_scale = overall_scale or config.get("custom_scale", {}).get(obj_type, config.get("defaultScale", 0.5))
        object_spacing = object_spacing or config.get("custom_spacing", {}).get(obj_type, config.get("defaultSpacing", 1.0))

        # Step 1: Generate matrix from letter map
        matrix = generate_letter_matrix(text)

        # Step 2: Convert matrix to object list
        objects = letter_to_object_list(
            matrix,
            obj_type,
            origin,
            offset,
            scale=overall_scale,
            spacing=object_spacing
        )

        # Step 3: Save object layout JSON
        output_json_path = os.path.join("outputs", "Sign4ME.json")
        preview_path = os.path.join("previews", "sign_preview.png")

        os.makedirs("outputs", exist_ok=True)
        os.makedirs("previews", exist_ok=True)

        with open(output_json_path, "w") as f:
            import json
            json.dump(objects, f, indent=2)

        # Step 4: Render preview image
        render_sign_preview(matrix, preview_path, object_type=obj_type)

        # Step 5: Update and save config
        config["default_object"] = obj_type
        config["defaultScale"] = overall_scale
        config["defaultSpacing"] = object_spacing
        config.setdefault("custom_scale", {})[obj_type] = overall_scale
        config.setdefault("custom_spacing", {})[obj_type] = object_spacing
        config["last_sign_data"] = text
        config["object_output_path"] = output_json_path
        config["preview_output_path"] = preview_path
        save_guild_config(guild_id, config)

        # Step 6: Create .zip bundle (JSON + PNG)
        final_path = create_qr_zip(
            output_json_path,
            preview_path,
            config.get("zip_output_path", "Sign4ME.zip"),
            extra_text=(
                f"Sign Size: {len(matrix[0])}x{len(matrix)}\n"
                f"Total Objects: {len(objects)}\n"
                f"Object Used: {obj_type}\n"
                f"Scale: {overall_scale} | Spacing: {object_spacing}"
            ),
            export_mode="json"
        )

        # Step 7: Post to gallery
        channel_id = get_channel_id("gallery", guild_id) or config.get("admin_channel_id")
        channel = self.bot.get_channel(int(channel_id)) if channel_id else None

        if not channel:
            await interaction.followup.send("❌ Could not find configured gallery channel.", ephemeral=True)
            return

        await channel.send(
            content=(
                f"🪧 **Sign Build Complete**\n"
                f"• Size: {len(matrix[0])}x{len(matrix)}\n"
                f"• Objects: {len(objects)}\n"
                f"• Type: `{obj_type}`\n"
                f"• Scale: `{overall_scale}` | Spacing: `{object_spacing}`\n"
                f"• Origin: X: {origin['x']}, Y: {origin['y']}, Z: {origin['z']}"
            ),
            files=[
                discord.File(output_json_path, filename="Sign4ME.json"),
                discord.File(preview_path, filename="sign_preview.png")
            ]
        )

        await interaction.followup.send("✅ Sign build generated and posted in gallery channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SignBuild(bot))
