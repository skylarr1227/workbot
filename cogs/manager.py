import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from discord.ext.commands import Greedy

class Manager(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="load", description="Load a cog extension by name")
    @app_commands.describe(extension="The cog filename (without .py)")
    async def load(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.load_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"✅ Loaded `{extension}`.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to load `{extension}`: {e}", ephemeral=True)

    @app_commands.command(name="unload", description="Unload a cog extension")
    @app_commands.describe(extension="Cog filename to unload")
    async def unload(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.unload_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"✅ Unloaded `{extension}`.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to unload `{extension}`: {e}", ephemeral=True)

    @app_commands.command(name="reload", description="Reload a cog extension")
    @app_commands.describe(extension="Cog filename to reload")
    async def reload(self, interaction: discord.Interaction, extension: str):
        try:
            await self.bot.reload_extension(f"cogs.{extension}")
            await interaction.response.send_message(f"🔄 Reloaded `{extension}`.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to reload `{extension}`: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Manager(bot))
