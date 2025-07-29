import os
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class WorkBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            application_id=int(os.getenv("APP_ID")),
        )
        self.synced = False

    async def setup_hook(self):
        # load all cogs
        for file in os.listdir("./cogs"):
            if file.endswith(".py"):
                await self.load_extension(f"cogs.{file[:-3]}")
        # sync slash commands to a test guild or globally
        test_guild = discord.Object(id=int(os.getenv("TEST_GUILD_ID")))
        self.tree.copy_global_to(guild=test_guild)
        await self.tree.sync(guild=test_guild)
        self.synced = True

    async def on_ready(self):
        if not self.synced:
            await self.tree.sync()
            self.synced = True
        print(f"Logged in as {self.user} (ID: {self.user.id})")

bot = WorkBot()

@bot.command()
async def ping(ctx):
    await ctx.send("pong")

bot.run(os.getenv("DISCORD_TOKEN"))
