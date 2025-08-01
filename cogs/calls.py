import discord
from discord.ext import commands, tasks
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

        # store summary message ids per guild so we can edit them
        self.summary_messages = {}

        # start the periodic task after bot is ready
        self.call_summary.start()

    def cog_unload(self):
        # ensure the task is cancelled when the cog is unloaded
        self.call_summary.cancel()

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

    @tasks.loop(minutes=30)
    async def call_summary(self):
        """Post the estimated wait time between calls for each guild."""
        # get list of configured channels
        cur = self.conn.execute("SELECT guild_id, channel_id FROM channel")
        channels = cur.fetchall()
        for guild_id, channel_id in channels:
            # compute average minutes for calls from today (local time)
            avg_cur = self.conn.execute(
                "SELECT AVG(minutes) FROM calls WHERE guild_id = ? AND date(timestamp) = date('now','localtime')",
                (guild_id,),
            )
            avg_row = avg_cur.fetchone()
            if not avg_row or avg_row[0] is None:
                continue
            average = float(avg_row[0])
            guild = self.bot.get_guild(guild_id)
            if not guild:
                continue
            channel = guild.get_channel(channel_id)
            if not channel:
                continue

            # build the embed with a timestamp
            ts = int(discord.utils.utcnow().timestamp())
            embed = discord.Embed(
                title="Estimated Wait Time",
                description=(
                    f"Estimated wait time between calls today: {average:.2f} minute(s).\n"
                    f"Last updated: <t:{ts}:f>"
                ),
                color=discord.Color.blue(),
                timestamp=discord.utils.utcnow(),
            )

            msg_id = self.summary_messages.get(guild_id)
            message = None
            if msg_id:
                try:
                    message = await channel.fetch_message(msg_id)
                except discord.NotFound:
                    message = None

            if message:
                await message.edit(embed=embed)
            else:
                sent = await channel.send(embed=embed)
                self.summary_messages[guild_id] = sent.id

    @call_summary.before_loop
    async def before_summary(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(CallCog(bot))
