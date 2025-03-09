import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import traceback

logger = logging.getLogger("modubot")

class Debug(commands.Cog):
    """Debug commands for bot development and troubleshooting"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @commands.is_owner()
    async def sync(self, ctx, guild_id: int = None, *, spec: str = None):
        """
        Sync app commands to Discord.
        
        guild_id: Guild ID to sync to (None for global)
        spec: "guild" to sync to current guild, "global" to sync globally, or "clear" to clear commands
        """
        try:
            # Determine where to sync
            if spec == "guild":
                guild_id = ctx.guild.id
            
            if guild_id:
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    return await ctx.send(f"Could not find guild with ID {guild_id}")
                
                if spec == "clear":
                    self.bot.tree.clear_commands(guild=guild)
                    await self.bot.tree.sync(guild=guild)
                    return await ctx.send(f"Cleared all commands in guild {guild.name}")
                else:
                    # Add basic commands for testing
                    @app_commands.command(name="debugping", description="Debug command to test slash functionality")
                    async def debug_ping(interaction: discord.Interaction):
                        await interaction.response.send_message("🏓 Debug Pong! Slash commands are working!")
                    
                    self.bot.tree.add_command(debug_ping, guild=guild)
                    
                    synced = await self.bot.tree.sync(guild=guild)
                    return await ctx.send(f"Synced {len(synced)} commands to guild {guild.name}")
            else:
                if spec == "clear":
                    self.bot.tree.clear_commands()
                    await self.bot.tree.sync()
                    return await ctx.send("Cleared all global commands")
                else:
                    synced = await self.bot.tree.sync()
                    return await ctx.send(f"Synced {len(synced)} global commands")
        
        except Exception as e:
            logger.error(f"Error syncing commands: {str(e)}")
            await ctx.send(f"Error: {str(e)}\n```{traceback.format_exc()}```")
    
    @commands.command()
    @commands.is_owner()
    async def list_commands(self, ctx):
        """List all registered slash commands"""
        try:
            # List global commands
            global_commands = await self.bot.tree.fetch_commands()
            
            # List guild commands if in a guild
            guild_commands = []
            if ctx.guild:
                guild_commands = await self.bot.tree.fetch_commands(guild=ctx.guild)
            
            # Format the output
            output = ["**Registered Slash Commands:**"]
            
            if global_commands:
                output.append("\n**Global Commands:**")
                for cmd in global_commands:
                    output.append(f"- `/{cmd.name}`: {cmd.description}")
            else:
                output.append("\n**No global commands registered.**")
            
            if guild_commands:
                output.append(f"\n**Guild Commands for {ctx.guild.name}:**")
                for cmd in guild_commands:
                    output.append(f"- `/{cmd.name}`: {cmd.description}")
            else:
                output.append(f"\n**No guild commands registered for {ctx.guild.name}.**")
            
            # Send the output in chunks if needed
            await ctx.send("\n".join(output))
        
        except Exception as e:
            logger.error(f"Error listing commands: {str(e)}")
            await ctx.send(f"Error: {str(e)}")
    
    @commands.command()
    @commands.is_owner()
    async def debug(self, ctx):
        """Run general debug checks on the bot"""
        try:
            output = []
            output.append("**Bot Debug Information:**")
            
            # Check basic connection info
            output.append(f"\n**Connection Status:**")
            output.append(f"- Connected: {self.bot.is_ready()}")
            output.append(f"- Latency: {round(self.bot.latency * 1000)}ms")
            output.append(f"- Guild Count: {len(self.bot.guilds)}")
            
            # Check loaded modules
            output.append(f"\n**Loaded Cogs:**")
            for cog_name in self.bot.cogs:
                output.append(f"- {cog_name}")
            
            # Check application command status
            output.append(f"\n**Application Command Status:**")
            global_commands = await self.bot.tree.fetch_commands()
            output.append(f"- Global Command Count: {len(global_commands)}")
            
            if ctx.guild:
                guild_commands = await self.bot.tree.fetch_commands(guild=ctx.guild)
                output.append(f"- Guild Command Count: {len(guild_commands)}")
            
            # Check internal tree structure
            tree_commands = self.bot.tree.get_commands()
            output.append(f"- Tree Command Count: {len(tree_commands)}")
            output.append(f"- Tree Command Names: {', '.join([cmd.name for cmd in tree_commands])}")
            
            # Send the output
            await ctx.send("\n".join(output))
        
        except Exception as e:
            logger.error(f"Error running debug: {str(e)}")
            await ctx.send(f"Error: {str(e)}")

async def setup(bot):
    await bot.add_cog(Debug(bot))
    logger.info("Debug cog loaded") 