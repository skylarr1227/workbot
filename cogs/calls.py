import discord
from discord.ext import commands
from discord import app_commands
import sqlite3

class CallCog(commands.Cog):
    """Manage call wait time posts."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.conn = sqlite3.connect("calls.db")
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS channel (
                   guild_id INTEGER PRIMARY KEY,
                   channel_id INTEGER NOT NULL
               )"""
        )
        self.conn.execute(
            """CREATE TABLE IF NOT EXISTS calls (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   guild_id INTEGER,
                   user_id INTEGER,
                   minutes INTEGER,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
               )"""
        )
        self.conn.commit()

    @app_commands.command(name="channel", description="Set the channel for call posts")
    @app_commands.checks.has_permissions(administrator=True)
    async def set_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Specify the channel where call posts will be sent."""
        with self.conn:
            self.conn.execute(
                "REPLACE INTO channel (guild_id, channel_id) VALUES (?, ?)",
                (interaction.guild.id, channel.id),
            )
        await interaction.response.send_message(
            f"Channel set to {channel.mention}", ephemeral=True
        )

    @app_commands.command(name="call", description="Post a completed call")
    async def call(self, interaction: discord.Interaction, minutes: int):
        """Post a call embed to the configured channel."""
        cur = self.conn.execute(
            "SELECT channel_id FROM channel WHERE guild_id = ?",
            (interaction.guild.id,),
        )
        row = cur.fetchone()
        if not row:
            await interaction.response.send_message(
                "No channel configured. Ask an admin to run /channel.",
                ephemeral=True,
            )
            return
        channel = interaction.guild.get_channel(row[0])
        if channel is None:
            await interaction.response.send_message(
                "Configured channel not found.", ephemeral=True
            )
            return

        embed = discord.Embed(title="Call Notification", color=discord.Color.blue())
        embed.add_field(name="User", value=interaction.user.mention, inline=True)
        embed.add_field(name="Wait Time", value=f"{minutes} minute(s)", inline=True)
        await channel.send(embed=embed)

        with self.conn:
            self.conn.execute(
                "INSERT INTO calls (guild_id, user_id, minutes) VALUES (?, ?, ?)",
                (interaction.guild.id, interaction.user.id, minutes),
            )
        await interaction.response.send_message(
            "Your call has been posted.", ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(CallCog(bot))
