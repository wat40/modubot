import discord
from discord import app_commands
from discord.ext import commands
import datetime
import random
from typing import Optional, List

class GlobalCommands(commands.Cog):
    """Global commands that work across all servers"""
    
    def __init__(self, bot):
        self.bot = bot
        # Define and register a global command group
        self.global_group = app_commands.Group(name="global", description="Global commands that work across all servers")
        bot.tree.add_command(self.global_group)
    
    @global_group.command(name="profile")
    @app_commands.describe(
        user="The user to show profile for (defaults to yourself)"
    )
    async def profile_command(
        self, 
        interaction: discord.Interaction,
        user: Optional[discord.Member] = None
    ):
        """View your or another user's global profile"""
        # Default to the interaction user if no user is specified
        target_user = user or interaction.user
        
        # Create an embed with the user's profile
        embed = discord.Embed(
            title=f"{target_user.display_name}'s Global Profile",
            color=target_user.color,
            timestamp=datetime.datetime.now()
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        
        # Mock profile data (in a real bot, this would come from a database)
        embed.add_field(name="Global Rank", value="Level 5", inline=True)
        embed.add_field(name="Global XP", value="1,250 XP", inline=True)
        embed.add_field(name="Global Balance", value="5,280 🪙", inline=True)
        
        # Passive income stats
        embed.add_field(name="Income Rate", value="155 🪙/hour", inline=True)
        embed.add_field(name="Inventory Items", value="8 items", inline=True)
        embed.add_field(name="Achievements", value="2/10 unlocked", inline=True)
        
        # Add join date
        embed.add_field(
            name="Discord Member Since", 
            value=f"<t:{int(target_user.created_at.timestamp())}:R>", 
            inline=False
        )
        
        # Add a footer
        embed.set_footer(text="Use /global collect to collect your passive income")
        
        await interaction.response.send_message(embed=embed)
    
    @global_group.command(name="collect")
    async def collect_command(self, interaction: discord.Interaction):
        """Collect income from all your passive income sources"""
        # Mock collection (in a real bot, this would interact with a database)
        amount = random.randint(100, 600)
        hours = random.randint(1, 8)
        
        embed = discord.Embed(
            title="Income Collected!",
            description=f"You collected **{amount} 🪙** from your passive income sources!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Time Accumulated", value=f"{hours} hours", inline=True)
        embed.add_field(name="Next Collection", value="Available now", inline=True)
        
        # Add a footer with a tip
        embed.set_footer(text="Tip: Buy more passive income items to increase your hourly rate")
        
        await interaction.response.send_message(embed=embed)
    
    @global_group.command(name="leaderboard")
    @app_commands.describe(
        category="The category to show leaderboard for"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="Balance", value="balance"),
        app_commands.Choice(name="Income Rate", value="income"),
        app_commands.Choice(name="XP Level", value="xp"),
    ])
    async def leaderboard_command(
        self, 
        interaction: discord.Interaction,
        category: str = "balance"
    ):
        """View the global leaderboard"""
        # Create a mock leaderboard (in a real bot, this would come from a database)
        mock_users = [
            {"name": "User1", "value": 10500, "rank": 1},
            {"name": "User2", "value": 8200, "rank": 2},
            {"name": "User3", "value": 7800, "rank": 3},
            {"name": "User4", "value": 6500, "rank": 4},
            {"name": "You", "value": 5280, "rank": 5},
            {"name": "User6", "value": 4900, "rank": 6},
            {"name": "User7", "value": 3700, "rank": 7},
            {"name": "User8", "value": 2500, "rank": 8},
            {"name": "User9", "value": 1800, "rank": 9},
            {"name": "User10", "value": 1200, "rank": 10},
        ]
        
        title_map = {
            "balance": "Global Balance Leaderboard",
            "income": "Global Income Rate Leaderboard",
            "xp": "Global XP Leaderboard"
        }
        
        suffix_map = {
            "balance": "🪙",
            "income": "🪙/hr",
            "xp": "XP"
        }
        
        embed = discord.Embed(
            title=title_map.get(category, "Global Leaderboard"),
            color=discord.Color.gold(),
            timestamp=datetime.datetime.now()
        )
        
        # Format leaderboard entries
        leaderboard_text = ""
        for user in mock_users:
            marker = "► " if user["name"] == "You" else ""
            rank_emoji = ["🥇", "🥈", "🥉"]
            rank_display = rank_emoji[user["rank"]-1] if user["rank"] <= 3 else f"`#{user['rank']}`"
            
            if user["name"] == "You":
                leaderboard_text += f"**{marker}{rank_display} {user['name']}: {user['value']:,} {suffix_map.get(category, '')}**\n"
            else:
                leaderboard_text += f"{marker}{rank_display} {user['name']}: {user['value']:,} {suffix_map.get(category, '')}\n"
        
        embed.description = leaderboard_text
        
        # Add a footer
        embed.set_footer(text="Updated every 30 minutes")
        
        await interaction.response.send_message(embed=embed)
    
    @global_group.command(name="shop")
    async def shop_command(self, interaction: discord.Interaction):
        """View the global shop for passive income items"""
        embed = discord.Embed(
            title="Global Shop",
            description="Purchase passive income items that work across all servers!",
            color=discord.Color.blue(),
            timestamp=datetime.datetime.now()
        )
        
        # Passive income items
        embed.add_field(
            name="🌀 Windmill - 7,500 🪙", 
            value="Generates 15 coins per hour",
            inline=False
        )
        
        embed.add_field(
            name="🌾 Small Farm - 15,000 🪙", 
            value="Generates 40 coins per hour",
            inline=False
        )
        
        embed.add_field(
            name="⛏️ Gold Mine - 30,000 🪙", 
            value="Generates 100 coins per hour",
            inline=False
        )
        
        embed.add_field(
            name="🏭 Factory - 50,000 🪙", 
            value="Generates 180 coins per hour",
            inline=False
        )
        
        # Add a footer with instructions
        embed.set_footer(text="Use /global buy [item] to purchase these items")
        
        await interaction.response.send_message(embed=embed)
    
    @global_group.command(name="buy")
    @app_commands.describe(
        item="The item to purchase"
    )
    @app_commands.choices(item=[
        app_commands.Choice(name="Windmill", value="windmill"),
        app_commands.Choice(name="Small Farm", value="farm"),
        app_commands.Choice(name="Gold Mine", value="mine"),
        app_commands.Choice(name="Factory", value="factory"),
    ])
    async def buy_command(
        self, 
        interaction: discord.Interaction,
        item: str
    ):
        """Purchase an item from the global shop"""
        # Item details (in a real bot, this would be in a database or config)
        items = {
            "windmill": {"name": "Windmill", "price": 7500, "income": 15, "emoji": "🌀"},
            "farm": {"name": "Small Farm", "price": 15000, "income": 40, "emoji": "🌾"},
            "mine": {"name": "Gold Mine", "price": 30000, "income": 100, "emoji": "⛏️"},
            "factory": {"name": "Factory", "price": 50000, "income": 180, "emoji": "🏭"},
        }
        
        if item not in items:
            await interaction.response.send_message("Invalid item. Use /global shop to see available items.", ephemeral=True)
            return
        
        selected_item = items[item]
        
        # Mock purchase (in a real bot, this would check the user's balance and update the database)
        # For demo purposes, we'll simulate a successful purchase
        
        embed = discord.Embed(
            title="Item Purchased!",
            description=f"You purchased a {selected_item['emoji']} **{selected_item['name']}** for **{selected_item['price']:,} 🪙**",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Income Rate", value=f"+{selected_item['income']} 🪙/hour", inline=True)
        embed.add_field(name="ROI Time", value=f"~{selected_item['price'] // selected_item['income']} hours", inline=True)
        
        # Add a footer with a tip
        embed.set_footer(text="View your items with /global profile")
        
        await interaction.response.send_message(embed=embed)
    
    @global_group.command(name="daily")
    async def daily_command(self, interaction: discord.Interaction):
        """Claim your daily reward"""
        # Mock daily reward (in a real bot, this would check if the user has already claimed today)
        amount = random.randint(200, 500)
        streak = random.randint(1, 10)
        
        embed = discord.Embed(
            title="Daily Reward Claimed!",
            description=f"You received **{amount} 🪙** as your daily reward!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(name="Current Streak", value=f"{streak} days", inline=True)
        embed.add_field(name="Next Reward", value="24 hours", inline=True)
        
        if streak % 7 == 0:
            embed.add_field(name="Streak Bonus", value=f"+{100 * (streak // 7)} 🪙", inline=False)
        
        # Add a footer with a tip
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(GlobalCommands(bot)) 