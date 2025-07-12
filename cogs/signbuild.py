# cogs/signbuild.py

import discord
from discord.ext import commands
from discord import app_commands
import os
import json

from utils.config_utils import get_guild_config, save_guild_config
from logic.text_matrix import generate_letter_matrix
from logic.render_sign_preview import render_sign_preview
from sign_generator import letter_to_object_list, OBJECT_CLASS_MAP
from sign_packager import create_sign_zip
from utils.channel_utils import get_channel_id
from utils.permissions import is_admin_user

MAX_OBJECTS = 1200

class SignBuild(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="signbuild", description="Convert text into a DayZ item sign layout")
    @app_commands.describe(
        text="The capital letters to build as a sign (A-Z only)",
        overall_scale="Overall object scale multiplier (default 0.5 or overridden per object)",
        object_spacing="Spacing between objects (default 1.0 or overridden per object)",
        object_type="Choose the object to use for the sign",
        orientation="Object orientation: upright (billboard) or flat (ground)"
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
        ],
        orientation=[
            app_commands.Choice(name="Upright (Billboard Style)", value="upright"),
            app_commands.Choice(name="Flat (On Ground)", value="flat")
        ]
    )
    async def signbuild(
        self,
        interaction: discord.Interaction,
        text: str,
        object_type: app_commands.Choice[str],
        orientation: app_commands.Choice[str] = None,
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

        overall_scale = overall_scale or config.get("custom_scale", {}).get(obj_type, config.get("defaultScale", 0.5))
        object_spacing = object_spacing or config.get("custom_spacing", {}).get(obj_type, config.get("defaultSpacing", 1.0))

        # ✅ Step 1: Generate character matrix
        matrix = [row[::-1] for row in generate_letter_matrix(text.upper())[::-1]]

        if not matrix or not any('#' in row for row in matrix):
            await interaction.followup.send("⚠️ No valid characters detected. Please use capital A–Z letters only.", ephemeral=True)
            return

        # 🔄 Adjust origin logic for upright mode (Z→Y stacking)
        ypr_mode = orientation.value if orientation else "upright"
        if ypr_mode == "upright":
            origin = {
                "x": origin["x"],
                "y": origin["y"],  # ✅ correct: Y stays Y
                "z": origin["z"]   # ✅ correct: Z stays Z
            }

        # ✅ Step 2: Generate objects from matrix using internal YPR mode
        try:
            objects = letter_to_object_list(
                matrix=matrix,
                object_type=obj_type,
                origin=origin,
                offset=offset,
                scale=overall_scale,
                spacing=object_spacing,
                ypr_mode=ypr_mode
            )

        except ValueError as e:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
            return

        if not objects:
            await interaction.followup.send("⚠️ Sign generation failed. No objects were created. Check your origin and spacing settings.", ephemeral=True)
            return

        if len(objects) >= MAX_OBJECTS:
            await interaction.followup.send(
                f"⚠️ Object cap reached ({MAX_OBJECTS} max). The sign may be incomplete.",
                ephemeral=True
            )

        # ✅ Step 3: Write to JSON and preview
        output_json_path = os.path.join("outputs", "Sign4ME.json")
        preview_path = os.path.join("previews", "sign_preview.png")

        os.makedirs("outputs", exist_ok=True)
        os.makedirs("previews", exist_ok=True)

        with open(output_json_path, "w") as f:
            json.dump({"Objects": objects}, f, indent=2)

        render_sign_preview(matrix, preview_path, object_type=obj_type)

        # ✅ Step 4: Save config
        config["default_object"] = obj_type
        config["defaultScale"] = overall_scale
        config["defaultSpacing"] = object_spacing
        config.setdefault("custom_scale", {})[obj_type] = overall_scale
        config.setdefault("custom_spacing", {})[obj_type] = object_spacing
        config["last_sign_data"] = text
        config["object_output_path"] = output_json_path
        config["preview_output_path"] = preview_path
        save_guild_config(guild_id, config)

        # ✅ Step 5: Package ZIP
        final_path = create_sign_zip(
            output_json_path,
            preview_path,
            config.get("zip_output_path", "Sign4ME.zip"),
            extra_text=(f"Sign Size: {len(matrix[0])}x{len(matrix)}\n"
                        f"Total Objects: {len(objects)}\n"
                        f"Object Used: {OBJECT_CLASS_MAP.get(obj_type, obj_type)}\n"
                        f"Scale: {overall_scale} | Spacing: {object_spacing}\n"
                        f"Orientation: {orientation.value if orientation else 'upright'}"),
            export_mode="json"
        )

        # ✅ Step 6: Gallery or Admin Channel Post
        channel_id = get_channel_id("gallery", guild_id) or config.get("admin_channel_id")
        channel = self.bot.get_channel(int(channel_id)) if channel_id else None

        if not channel:
            await interaction.followup.send("❌ Could not find configured gallery/admin channel.", ephemeral=True)
            return

        await channel.send(
            content=(f"🪧 **Sign Build Complete**\n"
                     f"• Size: {len(matrix[0])}x{len(matrix)}\n"
                     f"• Objects: {len(objects)}\n"
                     f"• Type: `{OBJECT_CLASS_MAP.get(obj_type, obj_type)}`\n"
                     f"• Scale: `{overall_scale}` | Spacing: `{object_spacing}`\n"
                     f"• Orientation: `{orientation.value if orientation else 'upright'}`\n"
                     f"• Origin: X: {origin['x']}, Y: {origin['y']}, Z: {origin['z']}"),
            files=[
                discord.File(output_json_path, filename="Sign4ME.json"),
                discord.File(preview_path, filename="sign_preview.png")
            ]
        )

        await interaction.followup.send("✅ Sign build generated and posted in gallery channel.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SignBuild(bot))
