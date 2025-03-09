import discord
from discord.ext import commands
import asyncio
from datetime import datetime, timedelta
from utils.embed_helper import EmbedHelper
from utils.database import Database

class Moderation(commands.Cog):
    """Moderation commands for server management"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.spam_check = {}  # Format: {user_id: [message_count, first_message_time]}
        self.spam_threshold = 5  # Number of messages
        self.spam_timeframe = 5  # Seconds
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel):
            return
        
        # Check for spam
        await self.check_spam(message)
        
        # Check for banned links/words (configurable from the database)
        guild_settings = await self.db.get_guild_settings(message.guild.id)
        if guild_settings.get('moderation_enabled', True):
            # Auto-delete banned links if configured
            if guild_settings.get('banned_links_enabled', False):
                banned_links = guild_settings.get('banned_links', [])
                if any(link in message.content for link in banned_links):
                    try:
                        await message.delete()
                        embed = EmbedHelper.warning_embed(
                            title="Message Deleted",
                            description=f"{message.author.mention}, your message was deleted because it contained a banned link."
                        )
                        await message.channel.send(embed=embed, delete_after=5)
                    except discord.Forbidden:
                        pass
    
    async def check_spam(self, message):
        user_id = message.author.id
        current_time = datetime.utcnow()
        
        if user_id in self.spam_check:
            # Update existing entry
            message_count, first_message_time = self.spam_check[user_id]
            
            # Check if we're still in the timeframe
            if (current_time - first_message_time).total_seconds() <= self.spam_timeframe:
                self.spam_check[user_id] = [message_count + 1, first_message_time]
                
                # Check if user has exceeded threshold
                if message_count + 1 >= self.spam_threshold:
                    # Apply spam action (mute or warn)
                    await self.handle_spam(message)
                    # Reset counter
                    self.spam_check.pop(user_id, None)
            else:
                # Outside timeframe, reset counter
                self.spam_check[user_id] = [1, current_time]
        else:
            # First message from this user
            self.spam_check[user_id] = [1, current_time]
    
    async def handle_spam(self, message):
        guild_settings = await self.db.get_guild_settings(message.guild.id)
        mute_duration = guild_settings.get('spam_mute_duration', 5)  # minutes
        
        # Send warning
        embed = EmbedHelper.warning_embed(
            title="Spam Detected",
            description=f"{message.author.mention}, please slow down! You're sending messages too quickly."
        )
        await message.channel.send(embed=embed)
        
        # Log the spam action
        await self.db.add_moderation_log(
            message.guild.id, 
            "spam_warning", 
            message.author.id, 
            self.bot.user.id,
            "Automated spam detection"
        )
        
        # Temp mute if configured
        if guild_settings.get('spam_mute_enabled', False):
            mute_role_id = guild_settings.get('mute_role_id')
            if mute_role_id:
                try:
                    mute_role = message.guild.get_role(int(mute_role_id))
                    if mute_role:
                        await message.author.add_roles(mute_role)
                        embed = EmbedHelper.error_embed(
                            title="User Muted",
                            description=f"{message.author.mention} has been temporarily muted for {mute_duration} minutes due to spamming."
                        )
                        await message.channel.send(embed=embed)
                        
                        # Log the mute action
                        await self.db.add_moderation_log(
                            message.guild.id, 
                            "temp_mute", 
                            message.author.id, 
                            self.bot.user.id,
                            "Automated spam detection",
                            f"{mute_duration} minutes"
                        )
                        
                        # Schedule unmute
                        await asyncio.sleep(mute_duration * 60)
                        await message.author.remove_roles(mute_role)
                except discord.Forbidden:
                    pass
    
    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Kick a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="You cannot kick someone with a higher or equal role to yours."
            )
            return await ctx.send(embed=embed)
        
        try:
            await member.kick(reason=reason)
            embed = EmbedHelper.success_embed(
                title="User Kicked",
                description=f"{member.mention} has been kicked from the server.",
                fields=[{"name": "Reason", "value": reason}]
            )
            await ctx.send(embed=embed)
            
            # Log the action
            await self.db.add_moderation_log(
                ctx.guild.id, 
                "kick", 
                member.id, 
                ctx.author.id,
                reason
            )
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to kick that member."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Ban a member from the server"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = EmbedHelper.error_embed(
                title="Permission Error", 
                description="You cannot ban someone with a higher or equal role to yours."
            )
            return await ctx.send(embed=embed)
        
        try:
            await member.ban(reason=reason)
            embed = EmbedHelper.success_embed(
                title="User Banned",
                description=f"{member.mention} has been banned from the server.",
                fields=[{"name": "Reason", "value": reason}]
            )
            await ctx.send(embed=embed)
            
            # Log the action
            await self.db.add_moderation_log(
                ctx.guild.id, 
                "ban", 
                member.id, 
                ctx.author.id,
                reason
            )
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to ban that member."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason="No reason provided"):
        """Unban a user by ID"""
        try:
            user = await self.bot.fetch_user(user_id)
            banned_users = [entry.user for entry in await ctx.guild.bans()]
            
            if user not in banned_users:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description=f"User with ID {user_id} is not banned."
                )
                return await ctx.send(embed=embed)
            
            await ctx.guild.unban(user, reason=reason)
            embed = EmbedHelper.success_embed(
                title="User Unbanned",
                description=f"{user.mention} has been unbanned from the server.",
                fields=[{"name": "Reason", "value": reason}]
            )
            await ctx.send(embed=embed)
            
            # Log the action
            await self.db.add_moderation_log(
                ctx.guild.id, 
                "unban", 
                user.id, 
                ctx.author.id,
                reason
            )
        except discord.NotFound:
            embed = EmbedHelper.error_embed(
                title="User Not Found",
                description=f"No user with ID {user_id} was found."
            )
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to unban users."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def mute(self, ctx, member: discord.Member, duration: int = 0, *, reason="No reason provided"):
        """Mute a member (duration in minutes, 0 for indefinite)"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="You cannot mute someone with a higher or equal role to yours."
            )
            return await ctx.send(embed=embed)
        
        guild_settings = await self.db.get_guild_settings(ctx.guild.id)
        mute_role_id = guild_settings.get('mute_role_id')
        
        if not mute_role_id:
            # Create mute role if it doesn't exist
            try:
                mute_role = await ctx.guild.create_role(name="Muted", reason="ModuBot: Creating mute role")
                
                # Update permissions for all channels
                for channel in ctx.guild.channels:
                    await channel.set_permissions(mute_role, send_messages=False, add_reactions=False, speak=False)
                
                # Update settings in database
                await self.db.update_guild_settings(ctx.guild.id, {'mute_role_id': str(mute_role.id)})
            except discord.Forbidden:
                embed = EmbedHelper.error_embed(
                    title="Permission Error",
                    description="I don't have permission to create roles or modify channel permissions."
                )
                return await ctx.send(embed=embed)
        else:
            mute_role = ctx.guild.get_role(int(mute_role_id))
            if not mute_role:
                embed = EmbedHelper.error_embed(
                    title="Role Not Found",
                    description="The mute role could not be found. Please reconfigure it using the `muterole` command."
                )
                return await ctx.send(embed=embed)
        
        try:
            await member.add_roles(mute_role)
            
            if duration > 0:
                embed = EmbedHelper.success_embed(
                    title="User Muted",
                    description=f"{member.mention} has been muted for {duration} minutes.",
                    fields=[{"name": "Reason", "value": reason}]
                )
                
                # Log the action
                await self.db.add_moderation_log(
                    ctx.guild.id, 
                    "temp_mute", 
                    member.id, 
                    ctx.author.id,
                    reason,
                    f"{duration} minutes"
                )
                
                # Schedule unmute
                await ctx.send(embed=embed)
                await asyncio.sleep(duration * 60)
                
                # Check if user still has mute role
                member = ctx.guild.get_member(member.id)
                if member and mute_role in member.roles:
                    await member.remove_roles(mute_role)
                    embed = EmbedHelper.info_embed(
                        title="User Unmuted",
                        description=f"{member.mention} has been automatically unmuted after {duration} minutes."
                    )
                    await ctx.send(embed=embed)
            else:
                embed = EmbedHelper.success_embed(
                    title="User Muted",
                    description=f"{member.mention} has been muted indefinitely.",
                    fields=[{"name": "Reason", "value": reason}]
                )
                await ctx.send(embed=embed)
                
                # Log the action
                await self.db.add_moderation_log(
                    ctx.guild.id, 
                    "mute", 
                    member.id, 
                    ctx.author.id,
                    reason
                )
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to modify that member's roles."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Unmute a muted member"""
        guild_settings = await self.db.get_guild_settings(ctx.guild.id)
        mute_role_id = guild_settings.get('mute_role_id')
        
        if not mute_role_id:
            embed = EmbedHelper.error_embed(
                title="Role Not Configured",
                description="The mute role has not been configured. Use the `muterole` command to set it up."
            )
            return await ctx.send(embed=embed)
        
        mute_role = ctx.guild.get_role(int(mute_role_id))
        if not mute_role:
            embed = EmbedHelper.error_embed(
                title="Role Not Found",
                description="The mute role could not be found. Please reconfigure it using the `muterole` command."
            )
            return await ctx.send(embed=embed)
        
        if mute_role not in member.roles:
            embed = EmbedHelper.error_embed(
                title="Not Muted",
                description=f"{member.mention} is not currently muted."
            )
            return await ctx.send(embed=embed)
        
        try:
            await member.remove_roles(mute_role)
            embed = EmbedHelper.success_embed(
                title="User Unmuted",
                description=f"{member.mention} has been unmuted.",
                fields=[{"name": "Reason", "value": reason}]
            )
            await ctx.send(embed=embed)
            
            # Log the action
            await self.db.add_moderation_log(
                ctx.guild.id, 
                "unmute", 
                member.id, 
                ctx.author.id,
                reason
            )
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to modify that member's roles."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = 5):
        """Clear a specified number of messages (default: 5)"""
        if amount <= 0:
            embed = EmbedHelper.error_embed(
                title="Invalid Amount",
                description="Please specify a positive number of messages to delete."
            )
            return await ctx.send(embed=embed)
        
        if amount > 100:
            embed = EmbedHelper.warning_embed(
                title="Amount Limited",
                description="You can only delete up to 100 messages at once. Setting amount to 100."
            )
            await ctx.send(embed=embed)
            amount = 100
        
        try:
            deleted = await ctx.channel.purge(limit=amount + 1)  # +1 to include the command itself
            embed = EmbedHelper.success_embed(
                title="Messages Cleared",
                description=f"Deleted {len(deleted) - 1} messages."
            )
            await ctx.send(embed=embed, delete_after=5)
            
            # Log the action
            await self.db.add_moderation_log(
                ctx.guild.id, 
                "clear", 
                ctx.channel.id, 
                ctx.author.id,
                f"Cleared {len(deleted) - 1} messages in #{ctx.channel.name}"
            )
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to delete messages in this channel."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def strike(self, ctx, member: discord.Member, *, reason="No reason provided"):
        """Give a strike to a user for rule violations"""
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="You cannot strike someone with a higher or equal role to yours."
            )
            return await ctx.send(embed=embed)
        
        # Add strike to database
        await self.db.add_moderation_log(
            ctx.guild.id, 
            "strike", 
            member.id, 
            ctx.author.id,
            reason
        )
        
        # Get current strikes
        strikes_response = await self.db.get_user_strikes(ctx.guild.id, member.id)
        strikes = strikes_response.data if hasattr(strikes_response, 'data') else []
        
        embed = EmbedHelper.warning_embed(
            title="User Struck",
            description=f"{member.mention} has received a strike.",
            fields=[
                {"name": "Reason", "value": reason},
                {"name": "Total Strikes", "value": str(len(strikes) + 1)}
            ]
        )
        await ctx.send(embed=embed)
        
        # DM the user
        try:
            user_embed = EmbedHelper.warning_embed(
                title=f"Strike Received in {ctx.guild.name}",
                description=f"You have received a strike from {ctx.author.display_name}.",
                fields=[
                    {"name": "Reason", "value": reason},
                    {"name": "Total Strikes", "value": str(len(strikes) + 1)}
                ]
            )
            await member.send(embed=user_embed)
        except discord.Forbidden:
            pass  # User has DMs disabled
        
        # Check for automatic actions based on strike count
        guild_settings = await self.db.get_guild_settings(ctx.guild.id)
        auto_actions = guild_settings.get('strike_actions', {})
        
        strike_count = len(strikes) + 1
        if str(strike_count) in auto_actions:
            action = auto_actions[str(strike_count)]
            if action == "mute":
                mute_duration = guild_settings.get('strike_mute_duration', 10)
                await self.mute(ctx, member, mute_duration, reason=f"Automatic mute after {strike_count} strikes")
            elif action == "kick":
                await self.kick(ctx, member, reason=f"Automatic kick after {strike_count} strikes")
            elif action == "ban":
                await self.ban(ctx, member, reason=f"Automatic ban after {strike_count} strikes")
    
    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def strikes(self, ctx, member: discord.Member):
        """Show strikes for a user"""
        strikes_response = await self.db.get_user_strikes(ctx.guild.id, member.id)
        strikes = strikes_response.data if hasattr(strikes_response, 'data') else []
        
        if not strikes:
            embed = EmbedHelper.info_embed(
                title="User Strikes",
                description=f"{member.mention} has no strikes in this server."
            )
            return await ctx.send(embed=embed)
        
        embed = EmbedHelper.info_embed(
            title="User Strikes",
            description=f"{member.mention} has {len(strikes)} strikes in this server."
        )
        
        for i, strike in enumerate(strikes, 1):
            moderator = ctx.guild.get_member(int(strike.get('moderator_id')))
            moderator_name = moderator.display_name if moderator else "Unknown Moderator"
            
            embed.add_field(
                name=f"Strike {i} - {strike.get('timestamp', 'Unknown date')}",
                value=f"**Reason:** {strike.get('reason', 'No reason provided')}\n**Moderator:** {moderator_name}",
                inline=False
            )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def muterole(self, ctx, role: discord.Role = None):
        """Set or show the mute role"""
        if role:
            await self.db.update_guild_settings(ctx.guild.id, {'mute_role_id': str(role.id)})
            embed = EmbedHelper.success_embed(
                title="Mute Role Set",
                description=f"The mute role has been set to {role.mention}."
            )
            await ctx.send(embed=embed)
        else:
            guild_settings = await self.db.get_guild_settings(ctx.guild.id)
            mute_role_id = guild_settings.get('mute_role_id')
            
            if not mute_role_id:
                embed = EmbedHelper.info_embed(
                    title="Mute Role",
                    description="No mute role has been configured. Use `!muterole @role` to set one."
                )
            else:
                mute_role = ctx.guild.get_role(int(mute_role_id))
                if mute_role:
                    embed = EmbedHelper.info_embed(
                        title="Mute Role",
                        description=f"The current mute role is {mute_role.mention}."
                    )
                else:
                    embed = EmbedHelper.warning_embed(
                        title="Mute Role",
                        description="The configured mute role no longer exists. Please set a new one."
                    )
            
            await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx, channel: discord.TextChannel = None):
        """Set or show the moderation log channel"""
        if channel:
            await self.db.update_guild_settings(ctx.guild.id, {'log_channel_id': str(channel.id)})
            embed = EmbedHelper.success_embed(
                title="Log Channel Set",
                description=f"The moderation log channel has been set to {channel.mention}."
            )
            await ctx.send(embed=embed)
        else:
            guild_settings = await self.db.get_guild_settings(ctx.guild.id)
            log_channel_id = guild_settings.get('log_channel_id')
            
            if not log_channel_id:
                embed = EmbedHelper.info_embed(
                    title="Log Channel",
                    description="No log channel has been configured. Use `!logchannel #channel` to set one."
                )
            else:
                log_channel = ctx.guild.get_channel(int(log_channel_id))
                if log_channel:
                    embed = EmbedHelper.info_embed(
                        title="Log Channel",
                        description=f"The current log channel is {log_channel.mention}."
                    )
                else:
                    embed = EmbedHelper.warning_embed(
                        title="Log Channel",
                        description="The configured log channel no longer exists. Please set a new one."
                    )
            
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot)) 