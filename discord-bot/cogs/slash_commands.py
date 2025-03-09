import discord
from discord import app_commands
from discord.ext import commands
import time
import datetime
import platform
import psutil
import sys
from typing import Optional, List, Literal

from utils.slash_helper import SlashHelper
from utils.embed_helper import EmbedHelper

class SlashCommands(commands.Cog):
    """Cog for slash commands implementation"""
    
    def __init__(self, bot):
        self.bot = bot
        
        # Add command groups - using app_commands directly to avoid any errors
        self.utility_group = app_commands.Group(name="utility", description="Utility commands")
        # Rename to avoid conflict with moderation_slash_commands.py
        self.info_group = app_commands.Group(name="info", description="Information commands")
        self.fun_group = app_commands.Group(name="fun", description="Fun commands")
        
        # Store group for direct reference in bot.py
        self.group = None  # Placeholder for compatibility
        
        # Add subcommands to groups (remove moderation_group to avoid conflict)
        self.bot.tree.add_command(self.utility_group)
        self.bot.tree.add_command(self.info_group)
        self.bot.tree.add_command(self.fun_group)
    
    @app_commands.command(name="ping", description="Check the bot's latency")
    async def slash_ping(self, interaction: discord.Interaction):
        """Check the bot's response time and latency"""
        start_time = time.time()
        await interaction.response.defer(thinking=True)
        end_time = time.time()
        
        api_latency = round(self.bot.latency * 1000)
        response_time = round((end_time - start_time) * 1000)
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=discord.Color.brand_green()
        )
        
        embed.add_field(name="Bot Latency", value=f"`{api_latency}ms`", inline=True)
        embed.add_field(name="Response Time", value=f"`{response_time}ms`", inline=True)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="help", description="Get help with bot commands")
    @app_commands.describe(command="The command to get help for")
    async def slash_help(self, interaction: discord.Interaction, command: Optional[str] = None):
        """Display help information about the bot's commands"""
        if command:
            # Find the specific command
            cmd = self.bot.tree.get_command(command)
            if not cmd:
                # Check if it's a group command
                for group in self.bot.tree.get_commands():
                    if isinstance(group, app_commands.Group) and group.name == command:
                        # It's a command group, show all commands in the group
                        embed = discord.Embed(
                            title=f"Command Group: /{group.name}",
                            description=group.description or "No description provided.",
                            color=discord.Color.blue()
                        )
                        
                        for subcmd in group.commands:
                            embed.add_field(
                                name=f"/{group.name} {subcmd.name}",
                                value=subcmd.description or "No description provided.",
                                inline=False
                            )
                        
                        await interaction.response.send_message(embed=embed)
                        return
                    
                    # Check subcommands
                    if isinstance(group, app_commands.Group):
                        for subcmd in group.commands:
                            if subcmd.name == command:
                                cmd = subcmd
                                break
                
                if not cmd:
                    await SlashHelper.error(
                        interaction,
                        title="Command Not Found",
                        description=f"No command named `/{command}` was found.",
                        ephemeral=True
                    )
                    return
            
            # Show help for the specific command
            embed = SlashHelper.format_command_help(cmd)
            await interaction.response.send_message(embed=embed)
        else:
            # Show general help with categories
            embed = discord.Embed(
                title="ModuBot Help",
                description="Here are the available commands. Use `/help [command]` to get detailed information about a specific command.",
                color=discord.Color.blue()
            )
            
            # Get all commands categorized by groups
            categories = {
                "General": [],
                "Utility": [],
                "Moderation": [],
                "Info": [],
                "Fun": []
            }
            
            # Add all top-level commands to General
            for cmd in self.bot.tree.get_commands():
                if isinstance(cmd, app_commands.Group):
                    # Add group commands to appropriate category
                    category_name = cmd.name.capitalize()
                    if category_name in categories:
                        for subcmd in cmd.commands:
                            categories[category_name].append(f"`/{cmd.name} {subcmd.name}`")
                    else:
                        # Create a new category if needed
                        categories[category_name] = [f"`/{cmd.name} {subcmd.name}`" for subcmd in cmd.commands]
                else:
                    # Add top-level commands to General
                    categories["General"].append(f"`/{cmd.name}`")
            
            # Add fields for each category
            for category, commands_list in categories.items():
                if commands_list:
                    embed.add_field(
                        name=f"{category} Commands",
                        value=", ".join(commands_list),
                        inline=False
                    )
            
            # Add footer with info about legacy commands
            embed.set_footer(text="ModuBot supports both slash (/) commands and traditional prefix (!) commands")
            
            await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="info", description="Get information about the bot")
    async def slash_info(self, interaction: discord.Interaction):
        """Display information about the bot, including version, uptime, and stats"""
        # Calculate uptime
        uptime = datetime.datetime.utcnow() - datetime.datetime.fromtimestamp(self.bot.launch_time) if hasattr(self.bot, 'launch_time') else None
        uptime_str = str(uptime).split('.')[0] if uptime else "Unknown"
        
        # Get memory usage
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024**2  # Convert to MB
        
        embed = discord.Embed(
            title="ModuBot Information",
            description="A modular Discord bot for server management and engagement",
            color=discord.Color.blue()
        )
        
        # Add bot stats
        embed.add_field(name="Version", value="`1.0.0`", inline=True)
        embed.add_field(name="Library", value=f"`discord.py {discord.__version__}`", inline=True)
        embed.add_field(name="Python", value=f"`{platform.python_version()}`", inline=True)
        
        embed.add_field(name="Servers", value=f"`{len(self.bot.guilds)}`", inline=True)
        embed.add_field(name="Users", value=f"`{sum(guild.member_count for guild in self.bot.guilds)}`", inline=True)
        embed.add_field(name="Commands", value=f"`{len(list(self.bot.tree.walk_commands()))}`", inline=True)
        
        embed.add_field(name="Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="Memory Usage", value=f"`{memory_usage:.2f} MB`", inline=True)
        embed.add_field(name="CPU Usage", value=f"`{psutil.cpu_percent()}%`", inline=True)
        
        # Add bot links
        embed.add_field(
            name="Links",
            value="[GitHub](https://github.com/yourusername/modubot) | [Invite Bot](https://discord.com/api/oauth2/authorize) | [Support Server](https://discord.gg/modubot)",
            inline=False
        )
        
        # Set thumbnail to bot avatar
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        
        # Set footer
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @self.utility_group.command(name="weather", description="Get current weather information for a location")
    @app_commands.describe(location="The city or location to get weather for")
    async def slash_weather(self, interaction: discord.Interaction, location: str):
        """Get detailed weather information for a specified location"""
        import requests
        import os
        
        # Defer response to allow time for API call
        await interaction.response.defer(thinking=True)
        
        api_key = os.getenv("OPENWEATHERMAP_API_KEY")
        if not api_key or api_key == "your_openweathermap_api_key_here":
            await SlashHelper.error(
                interaction,
                title="Configuration Error",
                description="Weather API key is not configured properly.",
                ephemeral=True
            )
            return
        
        try:
            # Get weather data
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code != 200:
                error_message = data.get('message', 'Unknown error')
                await SlashHelper.error(
                    interaction,
                    title="Weather Error",
                    description=f"Error fetching weather data: {error_message}",
                    ephemeral=True
                )
                return
            
            # Extract data
            city_name = data['name']
            country = data['sys']['country']
            weather_main = data['weather'][0]['main']
            weather_description = data['weather'][0]['description']
            temp = data['main']['temp']
            feels_like = data['main']['feels_like']
            humidity = data['main']['humidity']
            wind_speed = data['wind']['speed']
            wind_deg = data['wind'].get('deg', 0)
            
            # Prepare emoji based on weather condition
            weather_emoji = {
                'Clear': '☀️',
                'Clouds': '☁️',
                'Rain': '🌧️',
                'Drizzle': '🌦️',
                'Thunderstorm': '⛈️',
                'Snow': '❄️',
                'Mist': '🌫️',
                'Fog': '🌫️',
                'Haze': '🌫️',
                'Smoke': '🌫️',
                'Dust': '🌫️',
                'Sand': '🌫️',
                'Ash': '🌫️',
                'Squall': '💨',
                'Tornado': '🌪️'
            }
            
            emoji = weather_emoji.get(weather_main, '🌡️')
            
            # Get wind direction
            def get_wind_direction(degrees):
                directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
                index = round(degrees / 22.5) % 16
                return directions[index]
            
            wind_direction = get_wind_direction(wind_deg)
            
            # Get sunrise and sunset times
            sunrise_time = datetime.datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset_time = datetime.datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            
            # Create embed
            embed = discord.Embed(
                title=f"{emoji} Weather for {city_name}, {country}",
                description=f"**{weather_description.capitalize()}**",
                color=0x3498db
            )
            
            # Add fields
            embed.add_field(name="Temperature", value=f"🌡️ {temp}°C / {(temp * 9/5) + 32:.1f}°F\n🤔 Feels like: {feels_like}°C / {(feels_like * 9/5) + 32:.1f}°F", inline=False)
            embed.add_field(name="Conditions", value=f"💧 Humidity: {humidity}%", inline=True)
            embed.add_field(name="Wind", value=f"💨 {wind_speed} m/s {wind_direction}", inline=True)
            embed.add_field(name="Sun", value=f"🌅 Rise: {sunrise_time}\n🌇 Set: {sunset_time}", inline=True)
            
            # Add coordinates
            lat = data['coord']['lat']
            lon = data['coord']['lon']
            embed.add_field(name="Location", value=f"📍 [{lat}, {lon}](https://www.google.com/maps/search/?api=1&query={lat},{lon})", inline=False)
            
            # Set thumbnail
            weather_icon = data['weather'][0]['icon']
            embed.set_thumbnail(url=f"http://openweathermap.org/img/wn/{weather_icon}@2x.png")
            
            # Add footer
            embed.set_footer(text=f"Data from OpenWeatherMap • Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await SlashHelper.error(
                interaction,
                title="Error",
                description=f"An error occurred while fetching weather data: {str(e)}",
                ephemeral=True
            )

    @commands.command()
    @commands.is_owner()
    async def sync_commands(self, ctx):
        """Force sync slash commands (owner only)"""
        await ctx.send("🔄 Syncing slash commands, please wait...")
        
        try:
            # Sync globally
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} global slash commands.")
            
            # Sync to current guild for immediate effect
            if ctx.guild:
                guild_synced = await self.bot.tree.sync(guild=ctx.guild)
                await ctx.send(f"✅ Synced {len(guild_synced)} slash commands to this guild.")
        
        except Exception as e:
            await ctx.send(f"❌ Error syncing commands: {str(e)}")
    
    @commands.Cog.listener()
    async def on_ready(self):
        """Register commands when the bot is ready"""
        # This ensures the command groups are available for the bot to sync
        self.bot.logger.info(f"SlashCommands cog ready - ensuring command groups are registered")
        
        # Re-add command groups to make sure they're registered
        try:
            self.bot.tree.add_command(self.utility_group)
            self.bot.tree.add_command(self.info_group)
            self.bot.tree.add_command(self.fun_group)
            self.bot.logger.info("Re-registered SlashCommands command groups")
        except Exception as e:
            self.bot.logger.error(f"Error re-registering command groups: {str(e)}")

async def setup(bot):
    await bot.add_cog(SlashCommands(bot)) 