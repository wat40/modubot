import discord
from discord.ext import commands
import datetime
import asyncio
import pytz
import requests
import json
import time
import os
from utils.embed_helper import EmbedHelper
from utils.database import Database

class Utility(commands.Cog):
    """Utility commands for practical server functions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.reminders = {}  # Format: {reminder_id: (channel_id, user_id, message, end_time)}
        self.polls = {}  # Format: {message_id: {"question": question, "options": options, "votes": {}, "end_time": end_time}}
    
    @commands.command()
    async def ping(self, ctx):
        """Check the bot's latency"""
        start_time = time.time()
        message = await ctx.send("Pinging...")
        end_time = time.time()
        
        api_latency = round(self.bot.latency * 1000)
        message_latency = round((end_time - start_time) * 1000)
        
        embed = EmbedHelper.create_embed(
            title="🏓 Pong!",
            description=f"**API Latency:** {api_latency}ms\n**Message Latency:** {message_latency}ms",
            color=0x00C09A
        )
        
        await message.edit(content=None, embed=embed)
    
    @commands.command()
    async def serverinfo(self, ctx):
        """Display information about the server"""
        guild = ctx.guild
        
        # Count channels by type
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        categories = len(guild.categories)
        announcement_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel) and c.is_news()])
        stage_channels = len([c for c in guild.channels if isinstance(c, discord.StageChannel)])
        forum_channels = len([c for c in guild.channels if hasattr(c, "is_forum") and c.is_forum()])
        threads = len(guild.threads)
        
        # Count members by status
        online = sum(1 for member in guild.members if member.status == discord.Status.online)
        idle = sum(1 for member in guild.members if member.status == discord.Status.idle)
        dnd = sum(1 for member in guild.members if member.status == discord.Status.dnd)
        offline = sum(1 for member in guild.members if member.status == discord.Status.offline)
        
        # Count bots
        bots = sum(1 for member in guild.members if member.bot)
        humans = guild.member_count - bots
        
        # Server age
        server_age = datetime.datetime.utcnow() - guild.created_at
        server_age_str = f"{server_age.days} days"
        if server_age.days > 365:
            years = server_age.days // 365
            days = server_age.days % 365
            server_age_str = f"{years} year{'s' if years != 1 else ''}, {days} day{'s' if days != 1 else ''}"
        
        # Get server features
        features = [f.replace("_", " ").title() for f in guild.features]
        features_str = ", ".join(features) if features else "None"
        
        # Get verification level
        verification_levels = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest"
        }
        verification = verification_levels.get(guild.verification_level, "Unknown")
        
        # Count emojis by animated status
        static_emojis = len([e for e in guild.emojis if not e.animated])
        animated_emojis = len([e for e in guild.emojis if e.animated])
        
        # Create the embed
        embed = discord.Embed(
            title=f"{guild.name}",
            description=f"**Server ID:** {guild.id}\n**Owner:** {guild.owner.mention} ({guild.owner.id})\n**Created:** {guild.created_at.strftime('%B %d, %Y')} ({server_age_str} ago)",
            color=0x5865F2  # Discord Blurple
        )
        
        # Set server icon as thumbnail if available
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        
        # Add server banner as image if available
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        # Add member stats
        embed.add_field(
            name="Members",
            value=f"**Total:** {guild.member_count}\n"
                  f"**Humans:** {humans}\n"
                  f"**Bots:** {bots}",
            inline=True
        )
        
        # Add status counts
        embed.add_field(
            name="Statuses",
            value=f"🟢 {online} Online\n"
                  f"🟠 {idle} Idle\n"
                  f"🔴 {dnd} DND\n"
                  f"⚫ {offline} Offline",
            inline=True
        )
        
        # Add channel counts
        embed.add_field(
            name="Channels",
            value=f"**Text:** {text_channels}\n"
                  f"**Voice:** {voice_channels}\n"
                  f"**Categories:** {categories}\n"
                  f"**Total:** {len(guild.channels)}",
            inline=True
        )
        
        # Add extended channel info if any specialized channels exist
        if announcement_channels or stage_channels or forum_channels or threads:
            specialized_channels = []
            if announcement_channels:
                specialized_channels.append(f"**Announcement:** {announcement_channels}")
            if stage_channels:
                specialized_channels.append(f"**Stage:** {stage_channels}")
            if forum_channels:
                specialized_channels.append(f"**Forum:** {forum_channels}")
            if threads:
                specialized_channels.append(f"**Threads:** {threads}")
                
            embed.add_field(
                name="Special Channels",
                value="\n".join(specialized_channels),
                inline=True
            )
        
        # Add emoji stats
        embed.add_field(
            name="Emojis",
            value=f"**Static:** {static_emojis}\n"
                  f"**Animated:** {animated_emojis}\n"
                  f"**Total:** {len(guild.emojis)}/{guild.emoji_limit}",
            inline=True
        )
        
        # Add server settings
        embed.add_field(
            name="Server Settings",
            value=f"**Verification Level:** {verification}\n"
                  f"**Boost Level:** Level {guild.premium_tier}\n"
                  f"**Boosts:** {guild.premium_subscription_count}",
            inline=True
        )
        
        # Add server features if any
        if features:
            embed.add_field(
                name="Server Features",
                value=features_str,
                inline=False
            )
        
        # Add footer with timestamp
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        embed.timestamp = datetime.datetime.utcnow()
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def userinfo(self, ctx, member: discord.Member = None):
        """Display information about a user"""
        member = member or ctx.author
        
        # Calculate join position
        join_position = sorted(ctx.guild.members, key=lambda m: m.joined_at or datetime.datetime.utcnow()).index(member) + 1
        
        # Get roles (excluding @everyone)
        roles = [role.mention for role in member.roles if role.name != "@everyone"]
        roles.reverse()  # Show highest roles first
        roles_str = ", ".join(roles) if roles else "None"
        
        # Get key permissions
        key_permissions = []
        permissions = member.guild_permissions
        if permissions.administrator:
            key_permissions.append("Administrator")
        if permissions.manage_guild:
            key_permissions.append("Manage Server")
        if permissions.ban_members:
            key_permissions.append("Ban Members")
        if permissions.kick_members:
            key_permissions.append("Kick Members")
        if permissions.manage_channels:
            key_permissions.append("Manage Channels")
        if permissions.manage_roles:
            key_permissions.append("Manage Roles")
        if permissions.mention_everyone:
            key_permissions.append("Mention Everyone")
        if permissions.manage_webhooks:
            key_permissions.append("Manage Webhooks")
        if permissions.manage_messages:
            key_permissions.append("Manage Messages")
        
        perms_str = ", ".join(key_permissions) if key_permissions else "None"
        
        # Calculate account age
        account_age = datetime.datetime.utcnow() - member.created_at
        account_age_str = f"{account_age.days} days"
        if account_age.days > 365:
            years = account_age.days // 365
            days = account_age.days % 365
            account_age_str = f"{years} year{'s' if years != 1 else ''}, {days} day{'s' if days != 1 else ''}"
            
        # Calculate server membership time
        if member.joined_at:
            server_age = datetime.datetime.utcnow() - member.joined_at
            server_age_str = f"{server_age.days} days"
            if server_age.days > 365:
                years = server_age.days // 365
                days = server_age.days % 365
                server_age_str = f"{years} year{'s' if years != 1 else ''}, {days} day{'s' if days != 1 else ''}"
        else:
            server_age_str = "Unknown"
        
        # Determine the presence and activity
        status_emojis = {
            discord.Status.online: "🟢",
            discord.Status.idle: "🟠",
            discord.Status.dnd: "🔴",
            discord.Status.offline: "⚫"
        }
        
        status_emoji = status_emojis.get(member.status, "⚪")
        status_text = f"{status_emoji} {str(member.status).capitalize()}"
        
        # Get their activity
        activity = "None"
        if member.activity:
            if isinstance(member.activity, discord.Game):
                activity = f"Playing **{member.activity.name}**"
            elif isinstance(member.activity, discord.Streaming):
                activity = f"Streaming [**{member.activity.name}**]({member.activity.url})"
            elif isinstance(member.activity, discord.Spotify):
                activity = f"Listening to **{member.activity.title}** by **{member.activity.artist}**"
            elif isinstance(member.activity, discord.CustomActivity):
                if member.activity.emoji:
                    activity = f"{member.activity.emoji} {member.activity.name or ''}"
                else:
                    activity = member.activity.name or "Custom status"
        
        # Create the embed with direct discord.Embed for more control
        embed = discord.Embed(
            title=f"{member.display_name}'s Profile",
            description=f"**User ID:** {member.id}\n**Account Created:** {member.created_at.strftime('%B %d, %Y')} ({account_age_str} ago)",
            color=member.color,
            timestamp=datetime.datetime.utcnow()
        )
        
        # Add the user's avatar
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # Add profile information fields
        embed.add_field(
            name="Server Info",
            value=f"**Joined Server:** {member.joined_at.strftime('%B %d, %Y') if member.joined_at else 'Unknown'}\n"
                  f"**Join Position:** #{join_position}\n"
                  f"**Time in Server:** {server_age_str}",
            inline=True
        )
        
        embed.add_field(
            name="Names",
            value=f"**Username:** {member.name}\n"
                  f"**Display Name:** {member.display_name}\n"
                  f"**Nickname:** {member.nick or 'None'}\n"
                  f"**Global Name:** {member.global_name or 'None'}",
            inline=True
        )
        
        embed.add_field(
            name="Presence",
            value=f"**Status:** {status_text}\n"
                  f"**Activity:** {activity}\n"
                  f"**Bot Account:** {'Yes' if member.bot else 'No'}",
            inline=False
        )
        
        # Add key permissions if any
        if key_permissions:
            embed.add_field(
                name="Key Permissions",
                value=perms_str,
                inline=False
            )
        
        # Add roles (limit to not exceed embed limits)
        if roles:
            # Trim if too many roles to fit
            if len(roles_str) > 1024:
                roles_display = []
                total_length = 0
                for role in roles:
                    if total_length + len(role) + 2 > 1000:  # +2 for comma and space
                        roles_display.append(f"... and {len(roles) - len(roles_display)} more")
                        break
                    roles_display.append(role)
                    total_length += len(role) + 2
                roles_str = ", ".join(roles_display)
            
            embed.add_field(
                name=f"Roles ({len(roles)})",
                value=roles_str,
                inline=False
            )
        
        # Add footer with who requested the info
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        # Add timestamp
        if member.joined_at:
            # Add a jump link to when they joined if possible
            early_message = None
            try:
                async for message in ctx.channel.history(limit=1, oldest_first=True):
                    early_message = message
                    break
                
                if early_message and early_message.created_at > member.joined_at:
                    embed.description += f"\n[Jump to channel history]({early_message.jump_url})"
            except:
                pass
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def avatar(self, ctx, member: discord.Member = None):
        """Get a user's avatar"""
        member = member or ctx.author
        
        embed = EmbedHelper.create_embed(
            title=f"{member.display_name}'s Avatar",
            color=member.color,
            image=member.display_avatar.url,
            url=member.display_avatar.url,
            footer={"text": f"Requested by {ctx.author.display_name}"}
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_roles=True)
    async def role(self, ctx, member: discord.Member, *, role: discord.Role):
        """Add or remove a role from a member"""
        if role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="You cannot manage a role that is higher than or equal to your highest role."
            )
            return await ctx.send(embed=embed)
        
        if role >= ctx.me.top_role:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I cannot manage a role that is higher than my highest role."
            )
            return await ctx.send(embed=embed)
        
        try:
            if role in member.roles:
                # Remove the role
                await member.remove_roles(role)
                embed = EmbedHelper.success_embed(
                    title="Role Removed",
                    description=f"Removed {role.mention} from {member.mention}."
                )
            else:
                # Add the role
                await member.add_roles(role)
                embed = EmbedHelper.success_embed(
                    title="Role Added",
                    description=f"Added {role.mention} to {member.mention}."
                )
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to manage roles."
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def poll(self, ctx, duration: int, question: str, *options):
        """Create a poll (duration in minutes, max 10 options)"""
        if duration <= 0 or duration > 1440:  # Max 24 hours
            embed = EmbedHelper.error_embed(
                title="Invalid Duration",
                description="Please specify a duration between 1 and 1440 minutes (24 hours)."
            )
            return await ctx.send(embed=embed)
        
        if not question:
            embed = EmbedHelper.error_embed(
                title="Missing Question",
                description="Please provide a question for your poll."
            )
            return await ctx.send(embed=embed)
        
        if len(options) < 2:
            embed = EmbedHelper.error_embed(
                title="Too Few Options",
                description="Please provide at least 2 options for your poll."
            )
            return await ctx.send(embed=embed)
        
        if len(options) > 10:
            embed = EmbedHelper.error_embed(
                title="Too Many Options",
                description="You can only have up to 10 options in a poll."
            )
            return await ctx.send(embed=embed)
        
        # Emoji numbers for options
        emoji_numbers = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        # Create the poll embed
        description = f"**{question}**\n\n"
        for i, option in enumerate(options):
            description += f"{emoji_numbers[i]} {option}\n"
        
        end_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=duration)
        time_str = f"<t:{int(end_time.timestamp())}:R>"
        
        embed = EmbedHelper.create_embed(
            title="📊 Poll",
            description=description,
            color=0x3498DB,
            footer={"text": f"Poll by {ctx.author.display_name} | Ends {time_str}"}
        )
        
        # Send the poll and add reactions
        poll_message = await ctx.send(embed=embed)
        
        for i in range(len(options)):
            await poll_message.add_reaction(emoji_numbers[i])
        
        # Store poll information
        self.polls[poll_message.id] = {
            "question": question,
            "options": options,
            "emoji_numbers": emoji_numbers[:len(options)],
            "end_time": end_time,
            "author_id": ctx.author.id,
            "channel_id": ctx.channel.id
        }
        
        # Schedule poll end
        await asyncio.sleep(duration * 60)
        
        # Check if the poll still exists (hasn't been manually ended)
        if poll_message.id in self.polls:
            await self.end_poll(poll_message)
    
    async def end_poll(self, message):
        """End a poll and display the results"""
        if message.id not in self.polls:
            return
        
        poll_data = self.polls.pop(message.id)
        
        try:
            # Fetch the message to get the latest reactions
            message = await message.channel.fetch_message(message.id)
            
            # Count votes
            results = []
            for i, emoji in enumerate(poll_data["emoji_numbers"]):
                reaction = discord.utils.get(message.reactions, emoji=emoji)
                count = 0
                if reaction:
                    count = reaction.count - 1  # Subtract 1 to exclude the bot's reaction
                results.append((poll_data["options"][i], count))
            
            # Sort results by vote count (descending)
            results.sort(key=lambda x: x[1], reverse=True)
            
            # Create results embed
            description = f"**{poll_data['question']}**\n\n"
            
            total_votes = sum(count for _, count in results)
            for option, count in results:
                percentage = (count / total_votes) * 100 if total_votes > 0 else 0
                bar_length = 20
                filled_length = int(bar_length * percentage / 100)
                bar = "█" * filled_length + "░" * (bar_length - filled_length)
                
                description += f"{option}: {count} votes ({percentage:.1f}%)\n{bar}\n"
            
            embed = EmbedHelper.create_embed(
                title="📊 Poll Results",
                description=description,
                color=0x3498DB,
                footer={"text": f"Poll by {self.bot.get_user(poll_data['author_id']).display_name if self.bot.get_user(poll_data['author_id']) else 'Unknown'} | {total_votes} total votes"}
            )
            
            await message.channel.send(embed=embed)
            
            # Edit original message to show it's ended
            try:
                original_embed = message.embeds[0]
                original_embed.title = "📊 Poll [ENDED]"
                original_embed.set_footer(text=f"Poll by {self.bot.get_user(poll_data['author_id']).display_name if self.bot.get_user(poll_data['author_id']) else 'Unknown'} | Poll has ended")
                await message.edit(embed=original_embed)
            except:
                pass
        except (discord.NotFound, discord.Forbidden):
            # Message was deleted or bot doesn't have permissions
            pass
    
    @commands.command()
    async def remind(self, ctx, duration: str, *, reminder: str):
        """Set a reminder (e.g., 1h30m Check email)"""
        if not reminder:
            embed = EmbedHelper.error_embed(
                title="Missing Reminder",
                description="Please specify what you'd like to be reminded about."
            )
            return await ctx.send(embed=embed)
        
        # Parse the duration (e.g., 1h30m)
        total_seconds = 0
        time_units = {"d": 86400, "h": 3600, "m": 60, "s": 1}
        
        current_num = ""
        for char in duration:
            if char.isdigit():
                current_num += char
            elif char.lower() in time_units and current_num:
                total_seconds += int(current_num) * time_units[char.lower()]
                current_num = ""
        
        if total_seconds <= 0 or total_seconds > 7776000:  # Max 90 days
            embed = EmbedHelper.error_embed(
                title="Invalid Duration",
                description="Please specify a valid duration between 1 second and 90 days."
            )
            return await ctx.send(embed=embed)
        
        # Calculate end time
        end_time = datetime.datetime.utcnow() + datetime.timedelta(seconds=total_seconds)
        time_str = f"<t:{int(end_time.timestamp())}:R>"
        
        # Generate a unique ID for this reminder
        reminder_id = str(ctx.message.id)
        
        # Store the reminder
        self.reminders[reminder_id] = (ctx.channel.id, ctx.author.id, reminder, end_time)
        
        # Send confirmation
        embed = EmbedHelper.success_embed(
            title="Reminder Set",
            description=f"I'll remind you about: **{reminder}**\nTime: {time_str}"
        )
        await ctx.send(embed=embed)
        
        # Schedule the reminder
        await asyncio.sleep(total_seconds)
        
        # Check if the reminder still exists (hasn't been manually cancelled)
        if reminder_id in self.reminders:
            channel_id, user_id, reminder_text, _ = self.reminders.pop(reminder_id)
            
            try:
                channel = self.bot.get_channel(channel_id)
                if channel:
                    user = self.bot.get_user(user_id)
                    if user:
                        embed = EmbedHelper.info_embed(
                            title="Reminder",
                            description=f"{user.mention}, you asked me to remind you: **{reminder_text}**"
                        )
                        await channel.send(content=user.mention, embed=embed)
            except:
                pass
    
    @commands.command()
    async def weather(self, ctx, *, location: str = None):
        """Get the current weather for a location"""
        if not location:
            embed = EmbedHelper.error_embed(
                title="Missing Location",
                description="Please specify a location to check the weather for.\nExample: `!weather New York`"
            )
            return await ctx.send(embed=embed)
        
        try:
            # Use OpenWeatherMap API to get weather data
            api_key = os.getenv("OPENWEATHERMAP_API_KEY")
            if not api_key or api_key == "your_openweathermap_api_key_here":
                embed = EmbedHelper.error_embed(
                    title="API Key Missing",
                    description="The OpenWeatherMap API key is not configured properly. Please check the bot's `.env` file."
                )
                return await ctx.send(embed=embed)
            
            # Send a typing indicator while fetching data
            async with ctx.typing():
                # Get weather data
                response = requests.get(
                    f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric",
                    timeout=10  # Add timeout to prevent hanging
                )
                
                if response.status_code != 200:
                    if response.status_code == 404:
                        embed = EmbedHelper.error_embed(
                            title="Location Not Found",
                            description=f"Could not find weather data for '{location}'.\nPlease check your spelling or try a different location."
                        )
                    else:
                        error_message = response.json().get('message', 'Unknown error') if response.content else 'Unknown error'
                        embed = EmbedHelper.error_embed(
                            title="API Error",
                            description=f"Error getting weather data: {error_message}\nStatus code: {response.status_code}"
                        )
                    return await ctx.send(embed=embed)
                
                data = response.json()
                
                # Extract weather information
                city_name = data["name"]
                country = data["sys"]["country"]
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                temp_min = data["main"]["temp_min"]
                temp_max = data["main"]["temp_max"]
                humidity = data["main"]["humidity"]
                pressure = data["main"]["pressure"]
                wind_speed = data["wind"]["speed"]
                wind_direction = data["wind"].get("deg", 0)
                clouds = data["clouds"]["all"]
                description = data["weather"][0]["description"].capitalize()
                main_weather = data["weather"][0]["main"]
                icon_code = data["weather"][0]["icon"]
                
                # Get sunrise and sunset times
                sunrise = datetime.datetime.fromtimestamp(data["sys"]["sunrise"], datetime.timezone.utc)
                sunset = datetime.datetime.fromtimestamp(data["sys"]["sunset"], datetime.timezone.utc)
                local_offset = data["timezone"]  # Offset from UTC in seconds
                
                # Convert to local time
                local_sunrise = sunrise + datetime.timedelta(seconds=local_offset)
                local_sunset = sunset + datetime.timedelta(seconds=local_offset)
                
                # Convert temperature to Fahrenheit
                temp_f = (temp * 9/5) + 32
                feels_like_f = (feels_like * 9/5) + 32
                temp_min_f = (temp_min * 9/5) + 32
                temp_max_f = (temp_max * 9/5) + 32
                
                # Get cardinal direction from degrees
                def get_wind_direction(degrees):
                    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                    index = round(degrees / (360. / len(directions))) % len(directions)
                    return directions[index]
                
                wind_cardinal = get_wind_direction(wind_direction)
                
                # Get appropriate emoji for weather
                weather_emojis = {
                    "Clear": "☀️",
                    "Clouds": "☁️",
                    "Rain": "🌧️",
                    "Drizzle": "🌦️",
                    "Thunderstorm": "⛈️",
                    "Snow": "❄️",
                    "Mist": "🌫️",
                    "Fog": "🌫️",
                    "Haze": "🌫️",
                    "Smoke": "🌫️",
                    "Dust": "🌫️",
                    "Sand": "🌫️",
                    "Ash": "🌫️",
                    "Squall": "💨",
                    "Tornado": "🌪️"
                }
                
                weather_emoji = weather_emojis.get(main_weather, "🌡️")
                
                # Create the embed
                embed = discord.Embed(
                    title=f"{weather_emoji} Weather in {city_name}, {country}",
                    description=f"**{description}**",
                    color=0x3498DB,
                    timestamp=datetime.datetime.utcnow()
                )
                
                # Add thumbnail
                embed.set_thumbnail(url=f"http://openweathermap.org/img/w/{icon_code}.png")
                
                # Add main weather information
                embed.add_field(
                    name="Temperature", 
                    value=f"**Current:** {temp:.1f}°C / {temp_f:.1f}°F\n**Feels Like:** {feels_like:.1f}°C / {feels_like_f:.1f}°F\n**Min:** {temp_min:.1f}°C / {temp_min_f:.1f}°F\n**Max:** {temp_max:.1f}°C / {temp_max_f:.1f}°F", 
                    inline=True
                )
                
                embed.add_field(
                    name="Conditions", 
                    value=f"**Humidity:** {humidity}%\n**Pressure:** {pressure} hPa\n**Clouds:** {clouds}%", 
                    inline=True
                )
                
                embed.add_field(
                    name="Wind", 
                    value=f"**Speed:** {wind_speed} m/s\n**Direction:** {wind_cardinal} ({wind_direction}°)", 
                    inline=True
                )
                
                # Add sunrise/sunset info
                embed.add_field(
                    name="☀️ Sunrise/Sunset",
                    value=f"**Sunrise:** {local_sunrise.strftime('%H:%M:%S')}\n**Sunset:** {local_sunset.strftime('%H:%M:%S')}",
                    inline=False
                )
                
                # Add geocoordinates
                lat, lon = data["coord"]["lat"], data["coord"]["lon"]
                embed.add_field(
                    name="📍 Location",
                    value=f"**Latitude:** {lat}\n**Longitude:** {lon}\n[View on Map](https://www.google.com/maps/search/?api=1&query={lat},{lon})",
                    inline=False
                )
                
                # Footer
                embed.set_footer(text=f"Data from OpenWeatherMap • Local time", icon_url="https://openweathermap.org/themes/openweathermap/assets/vendor/owm/img/icons/logo_16x16.png")
                
                await ctx.send(embed=embed)
                
        except requests.exceptions.RequestException as e:
            embed = EmbedHelper.error_embed(
                title="Connection Error",
                description=f"Failed to connect to weather service: {str(e)}\nPlease try again later."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"An unexpected error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def urban(self, ctx, *, term: str):
        """Look up a term on Urban Dictionary"""
        if not term:
            embed = EmbedHelper.error_embed(
                title="Missing Term",
                description="Please specify a term to look up."
            )
            return await ctx.send(embed=embed)
        
        # Show typing indicator while fetching data
        async with ctx.typing():
            try:
                # Get Urban Dictionary definition
                response = requests.get(
                    f"https://api.urbandictionary.com/v0/define?term={term}"
                )
                data = response.json()
                
                if not data["list"]:
                    embed = EmbedHelper.error_embed(
                        title="No Results Found",
                        description=f"No definitions found for '{term}'."
                    )
                    return await ctx.send(embed=embed)
                
                # Sort definitions by thumbs up count
                definitions = sorted(data["list"], key=lambda x: x["thumbs_up"], reverse=True)
                definition = definitions[0]  # Get the most upvoted definition
                
                # Format the definition and example
                def_text = definition["definition"].replace("[", "").replace("]", "")
                example_text = definition["example"].replace("[", "").replace("]", "")
                
                if len(def_text) > 1024:
                    def_text = def_text[:1021] + "..."
                
                if len(example_text) > 1024:
                    example_text = example_text[:1021] + "..."
                
                # Calculate the ratio of thumbs up to thumbs down
                thumbs_up = definition["thumbs_up"]
                thumbs_down = definition["thumbs_down"]
                total_votes = thumbs_up + thumbs_down
                ratio = thumbs_up / total_votes if total_votes > 0 else 0
                ratio_percent = f"{ratio:.0%}"
                
                # Create a visual representation of the ratio
                bar_length = 10
                filled_bars = round(ratio * bar_length)
                ratio_bar = "🟩" * filled_bars + "⬜" * (bar_length - filled_bars)
                
                # Create the embed
                embed = discord.Embed(
                    title=f"📚 Urban Dictionary: {definition['word']}",
                    url=definition["permalink"],
                    color=0x1D2439  # Urban Dictionary's dark blue color
                )
                
                # Add Urban Dictionary logo as thumbnail
                embed.set_thumbnail(url="https://i.imgur.com/VFXr0ID.png")
                
                # Add definition and example
                embed.add_field(name="Definition", value=def_text, inline=False)
                
                if example_text.strip():
                    embed.add_field(name="Example", value=f"*{example_text}*", inline=False)
                
                # Add voting information
                embed.add_field(
                    name="Votes",
                    value=f"👍 {thumbs_up} | 👎 {thumbs_down} | Approval: {ratio_percent}\n{ratio_bar}",
                    inline=True
                )
                
                # Add author and date
                embed.add_field(
                    name="Author",
                    value=definition["author"],
                    inline=True
                )
                
                # Add date
                date = datetime.datetime.fromisoformat(definition["written_on"].replace("Z", "+00:00"))
                embed.add_field(
                    name="Written",
                    value=date.strftime("%B %d, %Y"),
                    inline=True
                )
                
                # Add tags if available
                if "tags" in data and data["tags"]:
                    tags = ", ".join([f"`{tag}`" for tag in data["tags"][:10]])
                    embed.add_field(name="Related Tags", value=tags, inline=False)
                
                # Add navigation for multiple definitions
                if len(definitions) > 1:
                    embed.set_footer(text=f"Definition 1 of {len(definitions)} | Sorted by popularity")
                
                await ctx.send(embed=embed)
                
            except Exception as e:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description=f"An error occurred while fetching the definition: {str(e)}"
                )
                await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, ctx, prefix=None):
        """Set the bot's command prefix for this server"""
        if not prefix:
            guild_settings = await self.db.get_guild_settings(ctx.guild.id)
            current_prefix = guild_settings.get('prefix', '!')
            
            embed = EmbedHelper.info_embed(
                title="Current Prefix",
                description=f"The current command prefix is `{current_prefix}`\nUse `{current_prefix}setprefix <new_prefix>` to change it."
            )
            return await ctx.send(embed=embed)
        
        if len(prefix) > 5:
            embed = EmbedHelper.error_embed(
                title="Prefix Too Long",
                description="The prefix can't be longer than 5 characters."
            )
            return await ctx.send(embed=embed)
        
        # Update the prefix in the database
        await self.db.update_guild_settings(ctx.guild.id, {'prefix': prefix})
        
        embed = EmbedHelper.success_embed(
            title="Prefix Updated",
            description=f"The command prefix has been set to `{prefix}`\nExample: `{prefix}help`"
        )
        await ctx.send(embed=embed)
    
    @commands.command()
    async def help(self, ctx, command=None):
        """Show help for commands"""
        if command:
            # Help for a specific command
            cmd = self.bot.get_command(command)
            if not cmd:
                embed = EmbedHelper.error_embed(
                    title="Command Not Found",
                    description=f"No command called `{command}` was found."
                )
                return await ctx.send(embed=embed)
            
            embed = EmbedHelper.help_command_embed(
                command_name=cmd.name,
                description=cmd.help or "No description available.",
                usage=f"{ctx.prefix}{cmd.name} {cmd.signature}",
                examples=f"{ctx.prefix}{cmd.name}",
                color=0x5865F2
            )
            
            if cmd.aliases:
                aliases = ", ".join([f"`{alias}`" for alias in cmd.aliases])
                embed.add_field(name="Aliases", value=aliases, inline=False)
            
            await ctx.send(embed=embed)
        else:
            # General help command
            embed = EmbedHelper.create_embed(
                title="ModuBot Help",
                description="Here are all the available commands. Use `!help <command>` for more details about a specific command.",
                color=0x5865F2
            )
            
            # Group commands by cog
            for cog_name, cog in self.bot.cogs.items():
                # Skip if no commands in this cog
                commands_list = [cmd for cmd in cog.get_commands() if not cmd.hidden]
                if not commands_list:
                    continue
                
                # Add a field for this cog with its commands
                commands_text = ", ".join([f"`{cmd.name}`" for cmd in commands_list])
                embed.add_field(name=cog_name, value=commands_text, inline=False)
            
            # Add uncategorized commands
            uncategorized = [cmd for cmd in self.bot.commands if not cmd.cog and not cmd.hidden]
            if uncategorized:
                commands_text = ", ".join([f"`{cmd.name}`" for cmd in uncategorized])
                embed.add_field(name="Uncategorized", value=commands_text, inline=False)
            
            # Add footer with invite link
            embed.set_footer(text=f"Use {ctx.prefix}invite to add ModuBot to your server | {len(self.bot.commands)} commands total")
            
            await ctx.send(embed=embed)
    
    @commands.command()
    async def invite(self, ctx):
        """Get an invite link for the bot"""
        permissions = discord.Permissions(
            send_messages=True,
            embed_links=True,
            attach_files=True,
            read_messages=True,
            read_message_history=True,
            add_reactions=True,
            use_external_emojis=True,
            manage_messages=True,
            manage_roles=True,
            connect=True,
            speak=True
        )
        
        invite_url = discord.utils.oauth_url(self.bot.user.id, permissions=permissions)
        
        embed = EmbedHelper.create_embed(
            title="Invite ModuBot",
            description=f"[Click here to invite ModuBot to your server]({invite_url})",
            color=0x5865F2,
            thumbnail=self.bot.user.display_avatar.url,
            fields=[
                {"name": "Support Server", "value": "[Join our support server](https://discord.gg/ModuBot)", "inline": False},
                {"name": "Website", "value": "[Visit our dashboard](https://modubot.example.com)", "inline": False}
            ]
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.has_permissions(manage_channels=True)
    async def slowmode(self, ctx, seconds: int = 0):
        """Set the slowmode delay for the current channel"""
        if seconds < 0 or seconds > 21600:  # Max 6 hours
            embed = EmbedHelper.error_embed(
                title="Invalid Duration",
                description="Slowmode delay must be between 0 and 21600 seconds (6 hours)."
            )
            return await ctx.send(embed=embed)
        
        try:
            await ctx.channel.edit(slowmode_delay=seconds)
            
            if seconds == 0:
                embed = EmbedHelper.success_embed(
                    title="Slowmode Disabled",
                    description=f"Slowmode has been disabled in {ctx.channel.mention}."
                )
            else:
                embed = EmbedHelper.success_embed(
                    title="Slowmode Enabled",
                    description=f"Slowmode has been set to {seconds} seconds in {ctx.channel.mention}."
                )
            
            await ctx.send(embed=embed)
        except discord.Forbidden:
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to edit this channel."
            )
            await ctx.send(embed=embed)
        except discord.HTTPException as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)

    @commands.command()
    async def time(self, ctx, *, timezone=None):
        """Get the current time in a specific timezone"""
        # Define common timezone emojis
        timezone_emojis = {
            "UTC": "🌐",
            "Europe/London": "🇬🇧",
            "Europe/Paris": "🇫🇷",
            "Europe/Berlin": "🇩🇪",
            "Europe/Moscow": "🇷🇺",
            "America/New_York": "🗽",
            "America/Chicago": "🌽",
            "America/Denver": "🏔️",
            "America/Los_Angeles": "🌉",
            "America/Toronto": "🇨🇦",
            "America/Mexico_City": "🇲🇽",
            "America/Sao_Paulo": "🇧🇷",
            "Asia/Tokyo": "🇯🇵",
            "Asia/Shanghai": "🇨🇳",
            "Asia/Seoul": "🇰🇷",
            "Asia/Singapore": "🇸🇬",
            "Asia/Dubai": "🇦🇪",
            "Asia/Kolkata": "🇮🇳",
            "Australia/Sydney": "🇦🇺",
            "Pacific/Auckland": "🇳🇿",
        }
        
        # If no timezone specified, show multiple timezones
        if not timezone:
            # Create a visually appealing embed with multiple timezones
            embed = discord.Embed(
                title="🕒 World Time",
                description="Current times around the world:",
                color=0x5865F2
            )
            
            # Get current UTC time for reference
            utc_now = datetime.datetime.now(pytz.UTC)
            
            # Add fields for different regions
            
            # North America
            na_times = []
            for tz, emoji in [("America/New_York", "🗽"), ("America/Chicago", "🌽"), 
                             ("America/Denver", "🏔️"), ("America/Los_Angeles", "🌉")]:
                local_time = utc_now.astimezone(pytz.timezone(tz))
                offset = local_time.strftime("%z")
                offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                na_times.append(f"{emoji} **{tz.split('/')[-1].replace('_', ' ')}**: {local_time.strftime('%H:%M:%S')} ({offset_formatted})")
            
            embed.add_field(name="North America", value="\n".join(na_times), inline=False)
            
            # Europe
            eu_times = []
            for tz, emoji in [("Europe/London", "🇬🇧"), ("Europe/Paris", "🇫🇷"), 
                             ("Europe/Berlin", "🇩🇪"), ("Europe/Moscow", "🇷🇺")]:
                local_time = utc_now.astimezone(pytz.timezone(tz))
                offset = local_time.strftime("%z")
                offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                eu_times.append(f"{emoji} **{tz.split('/')[-1]}**: {local_time.strftime('%H:%M:%S')} ({offset_formatted})")
            
            embed.add_field(name="Europe", value="\n".join(eu_times), inline=False)
            
            # Asia/Pacific
            ap_times = []
            for tz, emoji in [("Asia/Tokyo", "🇯🇵"), ("Asia/Shanghai", "🇨🇳"), 
                             ("Asia/Kolkata", "🇮🇳"), ("Australia/Sydney", "🇦🇺")]:
                local_time = utc_now.astimezone(pytz.timezone(tz))
                offset = local_time.strftime("%z")
                offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
                ap_times.append(f"{emoji} **{tz.split('/')[-1]}**: {local_time.strftime('%H:%M:%S')} ({offset_formatted})")
            
            embed.add_field(name="Asia/Pacific", value="\n".join(ap_times), inline=False)
            
            # Add reference UTC time
            embed.add_field(
                name="Reference",
                value=f"🌐 **UTC**: {utc_now.strftime('%H:%M:%S')}\n📅 **Date**: {utc_now.strftime('%A, %B %d, %Y')}",
                inline=False
            )
            
            # Add footer with command help
            embed.set_footer(text=f"Use {ctx.prefix}time <timezone> to check a specific timezone")
            
            return await ctx.send(embed=embed)
        
        # If a specific timezone was requested
        try:
            # Try to find the timezone
            try:
                # Try direct match first
                tz = pytz.timezone(timezone)
                tz_name = timezone
            except pytz.exceptions.UnknownTimeZoneError:
                # If not found, try to find a match
                matching_timezones = [tz for tz in pytz.all_timezones if timezone.lower() in tz.lower()]
                
                if not matching_timezones:
                    embed = EmbedHelper.error_embed(
                        title="Timezone Not Found",
                        description=f"Could not find timezone '{timezone}'. Try using a standard timezone format like 'America/New_York' or 'Europe/London'."
                    )
                    return await ctx.send(embed=embed)
                
                # Use the first match
                tz_name = matching_timezones[0]
                tz = pytz.timezone(tz_name)
            
            # Get current time in the requested timezone
            local_time = datetime.datetime.now(tz)
            
            # Get UTC offset
            offset = local_time.strftime("%z")
            offset_formatted = f"UTC{offset[:3]}:{offset[3:]}"
            
            # Get emoji for the timezone if available
            emoji = timezone_emojis.get(tz_name, "🕒")
            
            # Create embed
            embed = discord.Embed(
                title=f"{emoji} Time in {tz_name.replace('_', ' ')}",
                description=f"**Current Time**: {local_time.strftime('%H:%M:%S')}\n"
                           f"**Date**: {local_time.strftime('%A, %B %d, %Y')}\n"
                           f"**Timezone**: {tz_name} ({offset_formatted})",
                color=0x5865F2
            )
            
            # Add UTC reference
            utc_now = datetime.datetime.now(pytz.UTC)
            embed.add_field(
                name="UTC Reference",
                value=f"**UTC Time**: {utc_now.strftime('%H:%M:%S')}\n"
                     f"**UTC Date**: {utc_now.strftime('%A, %B %d, %Y')}",
                inline=False
            )
            
            # Add time difference
            time_diff = int(offset[:3]) * 60 + (int(offset[3:]) if len(offset) > 3 else 0)
            time_diff_hours = abs(time_diff) // 60
            time_diff_minutes = abs(time_diff) % 60
            time_diff_str = f"{time_diff_hours} hour{'s' if time_diff_hours != 1 else ''}"
            if time_diff_minutes > 0:
                time_diff_str += f" and {time_diff_minutes} minute{'s' if time_diff_minutes != 1 else ''}"
            time_diff_str += f" {'ahead of' if time_diff > 0 else 'behind'} UTC"
            
            embed.add_field(
                name="Time Difference",
                value=time_diff_str,
                inline=False
            )
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"An error occurred: {str(e)}"
            )
            await ctx.send(embed=embed)
            
async def setup(bot):
    await bot.add_cog(Utility(bot)) 