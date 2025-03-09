import discord
from discord import app_commands
from discord.ext import commands
import datetime
from typing import Optional

from utils.slash_helper import SlashHelper
from utils.embed_helper import EmbedHelper

class GuildSlashCommands(commands.Cog):
    """Guild-related slash commands for server and user information"""
    
    def __init__(self, bot):
        self.bot = bot
        # Add group property for bot.py sync compatibility
        self.group = None
    
    @app_commands.command(name="serverinfo", description="Get detailed information about the server")
    async def server_info(self, interaction: discord.Interaction):
        """Display detailed information about the current server"""
        guild = interaction.guild
        
        # Count channel types
        text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
        voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
        categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
        announcement_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])
        stage_channels = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        forum_channels = len([c for c in guild.channels if isinstance(c, discord.ForumChannel)])
        
        # Count threads
        threads = 0
        for channel in guild.text_channels:
            threads += len(channel.threads)
        
        # Count member statuses
        online = len([m for m in guild.members if m.status == discord.Status.online]) if guild.member_count < 1000 else "N/A"
        idle = len([m for m in guild.members if m.status == discord.Status.idle]) if guild.member_count < 1000 else "N/A"
        dnd = len([m for m in guild.members if m.status == discord.Status.dnd]) if guild.member_count < 1000 else "N/A"
        offline = len([m for m in guild.members if m.status == discord.Status.offline]) if guild.member_count < 1000 else "N/A"
        
        # Calculate server age
        created_at = guild.created_at
        server_age = datetime.datetime.now(datetime.timezone.utc) - created_at
        years, remainder = divmod(server_age.days, 365)
        months, days = divmod(remainder, 30)
        
        if years > 0:
            age_string = f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
        elif months > 0:
            age_string = f"{months} month{'s' if months != 1 else ''}, {days} day{'s' if days != 1 else ''}"
        else:
            age_string = f"{days} day{'s' if days != 1 else ''}"
        
        # Count emojis
        emoji_stats = {"static": 0, "animated": 0, "total": len(guild.emojis)}
        for emoji in guild.emojis:
            if emoji.animated:
                emoji_stats["animated"] += 1
            else:
                emoji_stats["static"] += 1
        
        # Get verification level
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        verification = verification_levels.get(guild.verification_level, "Unknown")
        
        # Create embed
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            description=guild.description or "No description set",
            color=discord.Color.blue()
        )
        
        # General info
        embed.add_field(name="Server Name", value=f"📝 {guild.name}", inline=True)
        embed.add_field(name="Server ID", value=f"🆔 {guild.id}", inline=True)
        embed.add_field(name="Owner", value=f"👑 {guild.owner.mention if guild.owner else 'Unknown'}", inline=True)
        
        # Date info
        embed.add_field(name="Created On", value=f"📅 {discord.utils.format_dt(created_at, 'F')} ({discord.utils.format_dt(created_at, 'R')})\n⏳ {age_string} old", inline=False)
        
        # Member stats
        embed.add_field(
            name=f"Member Stats ({guild.member_count} total)",
            value=f"👥 Humans: {len([m for m in guild.members if not m.bot])}\n🤖 Bots: {len([m for m in guild.members if m.bot])}",
            inline=True
        )
        
        # Status counts
        if guild.member_count < 1000:  # Only for smaller servers to avoid performance issues
            embed.add_field(
                name="Status Counts",
                value=f"🟢 Online: {online}\n🟡 Idle: {idle}\n🔴 DND: {dnd}\n⚫ Offline: {offline}",
                inline=True
            )
        
        # Channel counts
        embed.add_field(
            name=f"Channel Counts ({len(guild.channels)} total)",
            value=f"💬 Text: {text_channels}\n🔊 Voice: {voice_channels}\n📂 Categories: {categories}",
            inline=True
        )
        
        # Special channels
        special_channels = []
        if announcement_channels > 0:
            special_channels.append(f"📢 Announcement: {announcement_channels}")
        if stage_channels > 0:
            special_channels.append(f"🎭 Stage: {stage_channels}")
        if forum_channels > 0:
            special_channels.append(f"📋 Forum: {forum_channels}")
        if threads > 0:
            special_channels.append(f"🧵 Threads: {threads}")
            
        if special_channels:
            embed.add_field(
                name="Special Channels",
                value="\n".join(special_channels),
                inline=True
            )
        
        # Emoji stats
        embed.add_field(
            name=f"Emoji Stats ({emoji_stats['total']}/{guild.emoji_limit*2} slots)",
            value=f"⭐ Static: {emoji_stats['static']}/{guild.emoji_limit}\n✨ Animated: {emoji_stats['animated']}/{guild.emoji_limit}",
            inline=True
        )
        
        # Server settings
        server_settings = []
        server_settings.append(f"🔒 Verification: {verification}")
        if guild.system_channel:
            server_settings.append(f"🔔 System Channel: {guild.system_channel.mention}")
        if guild.rules_channel:
            server_settings.append(f"📜 Rules Channel: {guild.rules_channel.mention}")
        
        if server_settings:
            embed.add_field(
                name="Server Settings",
                value="\n".join(server_settings),
                inline=False
            )
        
        # Server features
        if guild.features:
            readable_features = []
            for feature in guild.features:
                readable_name = feature.replace('_', ' ').title()
                readable_features.append(f"✅ {readable_name}")
            
            embed.add_field(
                name="Server Features",
                value="\n".join(readable_features[:10]) + (f"\n*...and {len(readable_features) - 10} more*" if len(readable_features) > 10 else ""),
                inline=False
            )
        
        # Set server icon as thumbnail
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Set server banner as image if available
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="userinfo", description="Get detailed information about a user")
    @app_commands.describe(user="The user to get information about (defaults to yourself)")
    async def user_info(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Display detailed information about a user in the server"""
        # Use the command user if no user is specified
        user = user or interaction.user
        
        # Get user's join position
        if len(interaction.guild.members) < 1000:  # Only for smaller servers
            members = sorted(interaction.guild.members, key=lambda m: m.joined_at or discord.utils.utcnow())
            join_pos = members.index(user) + 1
        else:
            join_pos = "Unknown (server too large)"
        
        # Calculate account age
        created_at = user.created_at
        account_age = datetime.datetime.now(datetime.timezone.utc) - created_at
        years, remainder = divmod(account_age.days, 365)
        months, days = divmod(remainder, 30)
        
        if years > 0:
            age_string = f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
        elif months > 0:
            age_string = f"{months} month{'s' if months != 1 else ''}, {days} day{'s' if days != 1 else ''}"
        else:
            age_string = f"{days} day{'s' if days != 1 else ''}"
        
        # Calculate server membership time
        joined_at = user.joined_at
        if joined_at:
            membership_time = datetime.datetime.now(datetime.timezone.utc) - joined_at
            years, remainder = divmod(membership_time.days, 365)
            months, days = divmod(remainder, 30)
            
            if years > 0:
                membership_string = f"{years} year{'s' if years != 1 else ''}, {months} month{'s' if months != 1 else ''}"
            elif months > 0:
                membership_string = f"{months} month{'s' if months != 1 else ''}, {days} day{'s' if days != 1 else ''}"
            else:
                membership_string = f"{days} day{'s' if days != 1 else ''}"
        else:
            membership_string = "Unknown"
        
        # Get key permissions for the user
        key_perms = []
        permissions = user.guild_permissions
        
        if permissions.administrator:
            key_perms.append("Administrator")
        else:
            if permissions.manage_guild:
                key_perms.append("Manage Server")
            if permissions.ban_members:
                key_perms.append("Ban Members")
            if permissions.kick_members:
                key_perms.append("Kick Members")
            if permissions.manage_channels:
                key_perms.append("Manage Channels")
            if permissions.manage_messages:
                key_perms.append("Manage Messages")
            if permissions.manage_roles:
                key_perms.append("Manage Roles")
            if permissions.mention_everyone:
                key_perms.append("Mention Everyone")
            if permissions.manage_webhooks:
                key_perms.append("Manage Webhooks")
            if permissions.manage_emojis:
                key_perms.append("Manage Emojis")
        
        # Create status emoji mapping
        status_emoji = {
            discord.Status.online: "🟢 Online",
            discord.Status.idle: "🟡 Idle",
            discord.Status.dnd: "🔴 Do Not Disturb",
            discord.Status.offline: "⚫ Offline"
        }
        
        # Get user's status and activity
        status = status_emoji.get(user.status, "⚪ Unknown")
        activity = None
        
        if user.activity:
            if isinstance(user.activity, discord.Game):
                activity = f"Playing {user.activity.name}"
            elif isinstance(user.activity, discord.Streaming):
                activity = f"Streaming [{user.activity.name}]({user.activity.url})"
            elif isinstance(user.activity, discord.Spotify):
                activity = f"Listening to [{user.activity.title}](https://open.spotify.com/track/{user.activity.track_id}) by {user.activity.artist}"
            elif isinstance(user.activity, discord.CustomActivity):
                activity = f"{user.activity.emoji or ''} {user.activity.name or ''}"
            else:
                activity = str(user.activity)
        
        # Create embed
        embed = discord.Embed(
            title=f"{user.display_name}'s Information",
            color=user.color if user.color != discord.Color.default() else discord.Color.blue()
        )
        
        # Server Info
        embed.add_field(
            name="Server Info",
            value=f"📋 **Nickname:** {user.nick or 'None'}\n"
                  f"📊 **Join Position:** {join_pos}\n"
                  f"⏱️ **Joined:** {discord.utils.format_dt(joined_at, 'F') if joined_at else 'Unknown'} ({discord.utils.format_dt(joined_at, 'R') if joined_at else 'Unknown'})\n"
                  f"⌛ **Membership:** {membership_string}",
            inline=False
        )
        
        # Names
        embed.add_field(
            name="Names",
            value=f"🏷️ **Username:** {user.name}\n"
                  f"#️⃣ **Discriminator:** {user.discriminator}\n"
                  f"🆔 **ID:** {user.id}\n"
                  f"🔖 **Display Name:** {user.display_name}",
            inline=True
        )
        
        # Presence
        presence_info = [f"🔵 **Status:** {status}"]
        if activity:
            presence_info.append(f"🎮 **Activity:** {activity}")
        
        embed.add_field(
            name="Presence",
            value="\n".join(presence_info),
            inline=True
        )
        
        # Key Permissions
        if key_perms:
            embed.add_field(
                name="Key Permissions",
                value=", ".join(key_perms),
                inline=False
            )
        
        # Account Age
        embed.add_field(
            name="Account Age",
            value=f"📅 **Created:** {discord.utils.format_dt(created_at, 'F')} ({discord.utils.format_dt(created_at, 'R')})\n"
                  f"⏳ **Age:** {age_string}",
            inline=True
        )
        
        # Roles
        roles = [role.mention for role in reversed(user.roles) if role.name != "@everyone"]
        
        if len(roles) > 0:
            # If there are too many roles, show count instead of listing all
            if len(" ".join(roles)) > 1024:
                embed.add_field(
                    name=f"Roles [{len(roles)}]",
                    value=f"Too many to display. User has {len(roles)} roles.",
                    inline=False
                )
            else:
                embed.add_field(
                    name=f"Roles [{len(roles)}]",
                    value=" ".join(roles) or "None",
                    inline=False
                )
        
        # Add jump link to the message if it's in a channel
        if isinstance(interaction.channel, discord.TextChannel):
            jump_url = f"https://discord.com/channels/{interaction.guild.id}/{interaction.channel.id}/{interaction.id}"
            embed.add_field(
                name="Jump Link",
                value=f"[Jump to this message]({jump_url})",
                inline=False
            )
        
        # Set user avatar
        embed.set_thumbnail(url=user.display_avatar.url)
        
        # Set banner if available
        if hasattr(user, 'banner') and user.banner:
            embed.set_image(url=user.banner.url)
        
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
        
async def setup(bot):
    await bot.add_cog(GuildSlashCommands(bot)) 