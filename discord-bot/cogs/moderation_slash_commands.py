import discord
from discord import app_commands
from discord.ext import commands
import datetime
import asyncio
from typing import Optional, List, Literal

from utils.slash_helper import SlashHelper
from utils.embed_helper import EmbedHelper

class ModerationSlashCommands(commands.Cog):
    """Moderation commands using slash commands"""
    
    def __init__(self, bot):
        self.bot = bot
        # Define and register the command group
        self.mod_group = app_commands.Group(name="mod", description="Moderation commands")
        bot.tree.add_command(self.mod_group)
    
    @app_commands.command(name="ban", description="Ban a user from the server with optional message deletion period")
    @app_commands.default_permissions(ban_members=True)
    async def ban_command(self, interaction: discord.Interaction):
        """Standalone /ban command for backward compatibility"""
        await interaction.response.send_message("This command has been moved to /mod ban", ephemeral=True)
    
    @mod_group.command(name="ban")
    @app_commands.describe(
        user="The user to ban",
        reason="The reason for the ban",
        delete_days="Number of days of messages to delete (0-7)"
    )
    @app_commands.choices(delete_days=[
        app_commands.Choice(name="None", value=0),
        app_commands.Choice(name="1 day", value=1),
        app_commands.Choice(name="3 days", value=3),
        app_commands.Choice(name="7 days", value=7),
    ])
    @app_commands.default_permissions(ban_members=True)
    async def slash_ban(
        self, 
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = "No reason provided",
        delete_days: Optional[int] = 1
    ):
        """Ban a user from the server with optional message deletion period"""
        # Check permissions
        if not interaction.user.guild_permissions.ban_members:
            await interaction.response.send_message("You don't have permission to ban members.", ephemeral=True)
            return
            
        # Check if the user can be banned
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot ban someone with a higher or equal role than you.", ephemeral=True)
            return
            
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message("You cannot ban the server owner.", ephemeral=True)
            return
            
        if user.id == self.bot.user.id:
            await interaction.response.send_message("I cannot ban myself.", ephemeral=True)
            return
            
        # Set up the ban
        try:
            # Create embed for confirmation
            embed = discord.Embed(
                title="⚠️ User Banned",
                description=f"{user.mention} has been banned from the server.",
                color=discord.Color.red(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Banned by", value=interaction.user.mention)
            embed.add_field(name="Message Deletion", value=f"{delete_days} day(s)")
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Attempt to DM the user
            try:
                dm_embed = discord.Embed(
                    title="You have been banned",
                    description=f"You have been banned from {interaction.guild.name}.",
                    color=discord.Color.red()
                )
                dm_embed.add_field(name="Reason", value=reason)
                dm_embed.set_footer(text=f"Banned by: {interaction.user}")
                
                await user.send(embed=dm_embed)
            except:
                # User might have DMs closed
                pass
                
            # Ban the user
            await interaction.guild.ban(user, reason=reason, delete_message_days=delete_days)
            
            # Log to mod logs if available
            # This would normally check for a mod log channel and log the ban there
            
            # Respond to interaction
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to ban that user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.default_permissions(kick_members=True)
    async def kick_command(self, interaction: discord.Interaction):
        """Standalone /kick command for backward compatibility"""
        await interaction.response.send_message("This command has been moved to /mod kick", ephemeral=True)
            
    @mod_group.command(name="kick")
    @app_commands.describe(
        user="The user to kick",
        reason="The reason for the kick"
    )
    @app_commands.default_permissions(kick_members=True)
    async def slash_kick(
        self, 
        interaction: discord.Interaction,
        user: discord.Member,
        reason: Optional[str] = "No reason provided"
    ):
        """Kick a user from the server"""
        # Check permissions
        if not interaction.user.guild_permissions.kick_members:
            await interaction.response.send_message("You don't have permission to kick members.", ephemeral=True)
            return
            
        # Check if the user can be kicked
        if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
            await interaction.response.send_message("You cannot kick someone with a higher or equal role than you.", ephemeral=True)
            return
            
        if user.id == interaction.guild.owner_id:
            await interaction.response.send_message("You cannot kick the server owner.", ephemeral=True)
            return
            
        if user.id == self.bot.user.id:
            await interaction.response.send_message("I cannot kick myself.", ephemeral=True)
            return
            
        # Set up the kick
        try:
            # Create embed for confirmation
            embed = discord.Embed(
                title="⚠️ User Kicked",
                description=f"{user.mention} has been kicked from the server.",
                color=discord.Color.orange(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Kicked by", value=interaction.user.mention)
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Attempt to DM the user
            try:
                dm_embed = discord.Embed(
                    title="You have been kicked",
                    description=f"You have been kicked from {interaction.guild.name}.",
                    color=discord.Color.orange()
                )
                dm_embed.add_field(name="Reason", value=reason)
                dm_embed.set_footer(text=f"Kicked by: {interaction.user}")
                
                await user.send(embed=dm_embed)
            except:
                # User might have DMs closed
                pass
                
            # Kick the user
            await interaction.guild.kick(user, reason=reason)
            
            # Respond to interaction
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to kick that user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="timeout", description="Timeout a user for a specified duration")
    @app_commands.default_permissions(moderate_members=True)
    async def timeout_command(self, interaction: discord.Interaction):
        """Standalone /timeout command for backward compatibility"""
        await interaction.response.send_message("This command has been moved to /mod timeout", ephemeral=True)
            
    @mod_group.command(name="timeout")
    @app_commands.describe(
        user="The user to timeout",
        duration="Duration of the timeout",
        reason="The reason for the timeout"
    )
    @app_commands.choices(duration=[
        app_commands.Choice(name="60 seconds", value="60s"),
        app_commands.Choice(name="5 minutes", value="5m"),
        app_commands.Choice(name="10 minutes", value="10m"),
        app_commands.Choice(name="1 hour", value="1h"),
        app_commands.Choice(name="1 day", value="1d"),
        app_commands.Choice(name="1 week", value="1w"),
    ])
    @app_commands.default_permissions(moderate_members=True)
    async def slash_timeout(
        self, 
        interaction: discord.Interaction,
        user: discord.Member,
        duration: str,
        reason: Optional[str] = "No reason provided"
    ):
        """Timeout a user for a specified duration"""
        # Check permissions
        if not interaction.user.guild_permissions.moderate_members:
            await interaction.response.send_message("You don't have permission to timeout members.", ephemeral=True)
            return
            
        # Parse duration
        duration_seconds = 0
        duration_text = ""
        
        if duration.endswith("s"):
            duration_seconds = int(duration[:-1])
            duration_text = f"{duration_seconds} seconds"
        elif duration.endswith("m"):
            duration_seconds = int(duration[:-1]) * 60
            duration_text = f"{int(duration[:-1])} minutes"
        elif duration.endswith("h"):
            duration_seconds = int(duration[:-1]) * 3600
            duration_text = f"{int(duration[:-1])} hours"
        elif duration.endswith("d"):
            duration_seconds = int(duration[:-1]) * 86400
            duration_text = f"{int(duration[:-1])} days"
        elif duration.endswith("w"):
            duration_seconds = int(duration[:-1]) * 604800
            duration_text = f"{int(duration[:-1])} weeks"
        else:
            await interaction.response.send_message("Invalid duration format. Use s for seconds, m for minutes, h for hours, d for days, or w for weeks.", ephemeral=True)
            return
            
        # Calculate end time
        until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=duration_seconds)
        
        # Apply timeout
        try:
            await user.timeout(until, reason=reason)
            
            # Create embed for confirmation
            embed = discord.Embed(
                title="⏱️ User Timed Out",
                description=f"{user.mention} has been timed out for {duration_text}.",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Timed out by", value=interaction.user.mention)
            embed.add_field(name="Duration", value=duration_text)
            embed.add_field(name="Expires", value=f"<t:{int(until.timestamp())}:R>")
            embed.set_thumbnail(url=user.display_avatar.url)
            
            # Respond to interaction
            await interaction.response.send_message(embed=embed)
            
        except discord.Forbidden:
            await interaction.response.send_message("I don't have permission to timeout that user.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {str(e)}", ephemeral=True)
    
    @app_commands.command(name="clear", description="Clear a specified number of messages in the channel")
    @app_commands.default_permissions(manage_messages=True)
    async def clear_command(self, interaction: discord.Interaction):
        """Standalone /clear command for backward compatibility"""
        await interaction.response.send_message("This command has been moved to /mod clear", ephemeral=True)
            
    @mod_group.command(name="clear")
    @app_commands.describe(
        amount="Number of messages to delete (1-100)",
        user="Only delete messages from this user",
        contains="Only delete messages containing this text"
    )
    @app_commands.default_permissions(manage_messages=True)
    async def slash_clear(
        self, 
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
        user: Optional[discord.Member] = None,
        contains: Optional[str] = None
    ):
        """Clear a specified number of messages in the channel"""
        # Check permissions
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You don't have permission to clear messages.", ephemeral=True)
            return
            
        # Defer response since this might take a moment
        await interaction.response.defer(ephemeral=True)
        
        # Define function to check if a message should be deleted
        def message_check(message):
            if user and message.author.id != user.id:
                return False
                
            if contains and contains.lower() not in message.content.lower():
                return False
                
            return True
        
        # Get messages
        try:
            channel = interaction.channel
            messages = []
            
            # We need to fetch one more than requested for the purge to work correctly
            async for message in channel.history(limit=amount + 1):
                if len(messages) >= amount:
                    break
                    
                if message_check(message):
                    messages.append(message)
            
            # Delete messages
            deleted = 0
            
            if len(messages) > 0:
                try:
                    deleted = len(await channel.purge(limit=amount, check=message_check))
                except discord.Forbidden:
                    await interaction.followup.send("I don't have permission to delete messages.", ephemeral=True)
                    return
                except discord.HTTPException as e:
                    # If messages are too old (>14 days), Discord won't bulk delete them
                    if e.code == 50034:
                        await interaction.followup.send("Some messages couldn't be deleted because they are older than 14 days.", ephemeral=True)
                        return
                    else:
                        await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)
                        return
            
            # Send confirmation
            filter_text = ""
            if user:
                filter_text += f" from {user.mention}"
            if contains:
                filter_text += f" containing '{contains}'"
                
            await interaction.followup.send(f"Deleted {deleted} message(s){filter_text}.", ephemeral=True)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ModerationSlashCommands(bot)) 