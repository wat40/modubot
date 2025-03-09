import discord
from discord.ext import commands
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("sync.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("CommandSync")

class SyncBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.synced = False
    
    async def on_ready(self):
        if not self.synced:
            # Sync commands globally
            logger.info("Starting global command sync...")
            await self.tree.sync()
            logger.info("Global commands synced successfully!")
            
            # Output information about the registered commands
            global_commands = await self.http.get_global_commands(self.user.id)
            logger.info(f"Registered {len(global_commands)} global commands:")
            for cmd in global_commands:
                logger.info(f"- /{cmd['name']}: {cmd['description']}")
            
            self.synced = True
            logger.info(f"Logged in as {self.user.name} ({self.user.id})")
            logger.info("Command sync completed. You can now close this script.")
            
            # Close the bot after syncing
            await self.close()

async def main():
    # Get the bot token from environment variable
    token = os.getenv("DISCORD_TOKEN")
    
    if not token:
        logger.error("DISCORD_TOKEN environment variable not set.")
        logger.info("Please set your bot token using: set DISCORD_TOKEN=your_token_here")
        return
    
    # Initialize the bot with required intents
    intents = discord.Intents.default()
    intents.message_content = True
    
    bot = SyncBot(command_prefix="!", intents=intents)
    
    # Load the necessary cogs for syncing
    logger.info("Loading cogs for sync...")
    
    # List of cogs to load
    cogs = [
        "cogs.moderation_slash_commands",
        "cogs.global_commands",
        # Add other cogs that define slash commands here
    ]
    
    for cog in cogs:
        try:
            await bot.load_extension(cog)
            logger.info(f"Loaded {cog}")
        except Exception as e:
            logger.error(f"Failed to load {cog}: {e}")
    
    logger.info("All cogs loaded. Starting sync process...")
    
    # Start the bot to sync commands
    try:
        await bot.start(token)
    except discord.LoginFailure:
        logger.error("Invalid token provided. Please check your bot token.")
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        logger.info("Sync process completed or failed.")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 