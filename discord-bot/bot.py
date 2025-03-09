import os
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import platform
import sys
from dotenv import load_dotenv
from utils.database import Database

# Force SelectorEventLoop on Windows (fixes aiodns issue)
if platform.system() == 'Windows':
    import asyncio
    import selectors
    # Use SelectorEventLoop instead of ProactorEventLoop on Windows
    if sys.version_info >= (3, 13):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("modubot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("modubot")

# Bot configuration
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
intents.presences = True

class ModuBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            help_command=None,
            description="ModuBot - A modular Discord bot for server management and engagement"
        )
        self.logger = logger
        self.initial_extensions = [
            'cogs.moderation',
            'cogs.entertainment',
            'cogs.utility',
            'cogs.custom_commands',
            'cogs.error_handler',
            'cogs.slash_commands',  # New cog for slash commands
            'cogs.guild_slash_commands',  # Guild-related slash commands
            'cogs.moderation_slash_commands',  # Moderation slash commands
            'cogs.economy_slash_commands',  # New economy system
            'utils.database_admin',  # Add database admin cog
            'utils.debug'  # Debug utilities with command sync tools
        ]
        self.db = Database()
        self.synced = False
        self.launch_time = None
        
    async def setup_hook(self):
        # Record launch time for uptime calculation
        self.launch_time = asyncio.get_event_loop().time()
        
        # Set up database first
        self.logger.info("Setting up database...")
        try:
            await self.db.setup_database()
        except Exception as e:
            self.logger.error(f"Error setting up database: {e}")
            self.logger.info("Continuing with limited database functionality...")
            
        # Load extensions
        self.logger.info("Setting up bot extensions...")
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                self.logger.info(f"Loaded extension {extension}")
            except Exception as e:
                self.logger.error(f"Failed to load extension {extension}: {e}")
        
        self.logger.info("All extensions processed")

    async def on_ready(self):
        # Always sync slash commands
        self.logger.info("Syncing application commands (always sync on startup)...")
        try:
            # Print registered commands for debugging
            self.logger.info("Currently registered command groups in tree:")
            for cmd in self.tree.get_commands():
                self.logger.info(f"Command: {cmd.name} - {type(cmd)}")
            
            # Forcefully sync all command groups
            for cog in self.cogs.values():
                if hasattr(cog, 'group'):
                    if isinstance(cog.group, app_commands.Group):
                        try:
                            self.tree.add_command(cog.group)
                            self.logger.info(f"Added command group from {cog.__class__.__name__}")
                        except discord.app_commands.errors.CommandAlreadyRegistered:
                            self.logger.info(f"Command group from {cog.__class__.__name__} already registered, skipping")
            
            # Sync globally
            self.logger.info("Syncing commands globally...")
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} global slash command(s)")
            
            # Also sync to all guilds to make commands appear instantly
            guild_count = 0
            for guild in self.guilds:
                try:
                    self.logger.info(f"Syncing commands to guild {guild.name} ({guild.id})...")
                    guild_commands = await self.tree.sync(guild=guild)
                    self.logger.info(f"Synced {len(guild_commands)} commands to guild {guild.name}")
                    guild_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to sync to guild {guild.id}: {e}")
            
            self.logger.info(f"Synced commands to {guild_count} guilds")
            self.synced = True
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")
            self.logger.error(f"Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
                
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="your server | /help"
            )
        )
        print(f"""
        ╔═══════════════════════════════════════════════╗
        ║                   ModuBot                     ║
        ║                                               ║
        ║  Bot is now online and ready to use!          ║
        ║  Logged in as: {self.user.name}               
        ║  Bot ID: {self.user.id}                       
        ║  Slash Commands: {'Enabled' if self.synced else 'Disabled'}
        ║  Economy System: Enabled                      
        ╚═══════════════════════════════════════════════╝
        """)

    async def on_message(self, message):
        if message.author.bot:
            return

        # Process commands
        await self.process_commands(message)

async def main():
    bot = ModuBot()
    async with bot:
        await bot.start(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    asyncio.run(main()) 