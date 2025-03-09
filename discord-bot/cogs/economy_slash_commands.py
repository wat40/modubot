import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
import json
import os
import datetime
from typing import Optional, Literal
import time

# File path to store economy data
ECONOMY_FILE = 'data/economy.json'

# Ensure data directory exists
os.makedirs(os.path.dirname(ECONOMY_FILE), exist_ok=True)

# Default settings
DEFAULT_STARTING_BALANCE = 500
DEFAULT_DAILY_AMOUNT = 200
DEFAULT_CURRENCY_NAME = "coins"
DEFAULT_CURRENCY_EMOJI = "🪙"  # Gold coin emoji

# Coin flip images
HEADS_IMAGE = "https://cdn.discordapp.com/attachments/1348088564499480658/1348141750677536879/george-washington-crossing-the-delaware-quarter-heads.png?ex=67ce6258&is=67cd10d8&hm=c0b6fecd0696ed2ef1c090e6be2e255225be085b2b33f77283423a9056061782&"
TAILS_IMAGE = "https://cdn.discordapp.com/attachments/1348088564499480658/1348142003677822997/quarter-dollar-us-coin-isolated-on-white.png?ex=67ce6294&is=67cd1114&hm=5ebd750b956fadc22bb7a25638c152455b3727ae2fbcf7253977685cefc4df2e&"

class EconomySlashCommands(commands.Cog):
    """Economy commands using slash commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = DEFAULT_CURRENCY_NAME
        self.currency_emoji = DEFAULT_CURRENCY_EMOJI
        self.economy_data = {}
        self.load_economy_data()
        
        # Initialize command groups
        self.economy_group = app_commands.Group(name="economy", description="Economy and currency commands")
        self.gambling_group = app_commands.Group(name="gamble", description="Gambling commands for economy")
        
        # Add groups to the command tree
        bot.tree.add_command(self.economy_group)
        bot.tree.add_command(self.gambling_group)
        
        # Shop items - Name, price, description, role_id (if applicable)
        self.shop_items = {
            "role1": {
                "name": "VIP Role",
                "price": 5000,
                "description": "A special VIP role that changes your color",
                "type": "role",
                "role_id": None  # Will be set per-server
            },
            "nickname": {
                "name": "Nickname Change",
                "price": 1000,
                "description": "Change your nickname with a custom color",
                "type": "consumable"
            },
            "lootbox": {
                "name": "Mystery Lootbox",
                "price": 2500,
                "description": "A mystery box that contains a random amount of coins",
                "type": "consumable"
            },
            "windmill": {
                "name": "Windmill",
                "price": 7500,
                "description": "Generates 15 coins every hour passively",
                "type": "passive_income",
                "income_rate": 15,
                "income_period": 3600,  # 1 hour in seconds
                "image_url": "https://cdn.discordapp.com/attachments/1348088564499480658/1348464651057373204/windmill.png"
            },
            "farm": {
                "name": "Small Farm",
                "price": 15000,
                "description": "Generates 40 coins every hour passively",
                "type": "passive_income",
                "income_rate": 40,
                "income_period": 3600,  # 1 hour in seconds
                "image_url": "https://cdn.discordapp.com/attachments/1348088564499480658/1348464650784800888/farm.png"
            },
            "mine": {
                "name": "Gold Mine",
                "price": 30000,
                "description": "Generates 100 coins every hour passively",
                "type": "passive_income",
                "income_rate": 100,
                "income_period": 3600,  # 1 hour in seconds
                "image_url": "https://cdn.discordapp.com/attachments/1348088564499480658/1348464650487140382/mine.png"
            },
            "factory": {
                "name": "Factory",
                "price": 50000,
                "description": "Generates 180 coins every hour passively",
                "type": "passive_income",
                "income_rate": 180,
                "income_period": 3600,  # 1 hour in seconds
                "image_url": "https://cdn.discordapp.com/attachments/1348088564499480658/1348464650214551632/factory.png"
            }
        }
    
    def load_economy_data(self):
        """Load economy data from file"""
        try:
            if os.path.exists(ECONOMY_FILE):
                with open(ECONOMY_FILE, 'r') as f:
                    self.economy_data = json.load(f)
            else:
                self.economy_data = {}
                self.save_economy_data()
        except Exception as e:
            print(f"Error loading economy data: {e}")
            self.economy_data = {}
    
    def save_economy_data(self):
        """Save economy data to file"""
        try:
            with open(ECONOMY_FILE, 'w') as f:
                json.dump(self.economy_data, f, indent=4)
        except Exception as e:
            print(f"Error saving economy data: {e}")
    
    def get_user_data(self, user_id):
        """Get a user's economy data, creating it if it doesn't exist"""
        # Convert to string for JSON compatibility
        user_id = str(user_id)
        
        if user_id not in self.economy_data:
            self.economy_data[user_id] = {
                "balance": DEFAULT_STARTING_BALANCE,
                "last_daily": 0,
                "inventory": [],
                "total_earned": DEFAULT_STARTING_BALANCE,
                "total_spent": 0
            }
            self.save_economy_data()
            
        return self.economy_data[user_id]
    
    def format_currency(self, amount):
        """Format a currency amount with the currency symbol"""
        return f"{self.currency_emoji} **{amount:,}** {self.currency_name}"
    
    @app_commands.command(name="balance")
    @app_commands.describe(user="The user to check balance for (defaults to yourself)")
    async def balance_command(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
        """Check your or another user's current balance"""
        target_user = user or interaction.user
        user_data = self.get_user_data(target_user.id)
        
        embed = discord.Embed(
            title=f"{target_user.display_name}'s Balance",
            color=discord.Color.gold()
        )
        
        embed.add_field(
            name="Current Balance", 
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        # Add some stats
        embed.add_field(
            name="Total Earned",
            value=self.format_currency(user_data["total_earned"]),
            inline=True
        )
        
        embed.add_field(
            name="Total Spent",
            value=self.format_currency(user_data["total_spent"]),
            inline=True
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="daily")
    async def daily_command(self, interaction: discord.Interaction):
        """Claim your daily currency reward (once every 24 hours)"""
        user_id = str(interaction.user.id)
        user_data = self.get_user_data(user_id)
        
        # Check cooldown
        last_daily = user_data["last_daily"]
        current_time = time.time()
        time_since_last = current_time - last_daily
        cooldown = 86400  # 24 hours in seconds
        
        if last_daily > 0 and time_since_last < cooldown:
            remaining = cooldown - time_since_last
            hours, remainder = divmod(int(remaining), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            embed = discord.Embed(
                title="Daily Reward Cooldown",
                description=f"You've already claimed your daily reward.\nYou can claim again in **{hours}h {minutes}m {seconds}s**.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url="https://i.imgur.com/fgNUHdL.png")  # Clock icon
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Award the daily amount
        reward = DEFAULT_DAILY_AMOUNT
        
        # Check for streak bonuses (TODO: Implement streak logic)
        streak = 1
        
        # Update user data
        user_data["balance"] += reward
        user_data["last_daily"] = current_time
        user_data["total_earned"] += reward
        self.save_economy_data()
        
        # Create embed
        embed = discord.Embed(
            title="Daily Reward Claimed!",
            description=f"You've received your daily reward of {self.format_currency(reward)}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        if streak > 1:
            embed.add_field(
                name="Current Streak",
                value=f"🔥 {streak} days",
                inline=True
            )
            
        embed.set_thumbnail(url="https://i.imgur.com/MoMxkgm.png")  # Gift box icon
        embed.set_footer(text="Come back tomorrow for another reward!")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="give")
    @app_commands.describe(
        user="The user to give money to",
        amount="The amount to give"
    )
    async def give_command(self, interaction: discord.Interaction, user: discord.User, amount: int):
        """Give money to another user"""
        if user.id == interaction.user.id:
            embed = discord.Embed(
                title="Error",
                description="You can't give money to yourself!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if user.bot:
            embed = discord.Embed(
                title="Error",
                description="You can't give money to bots!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        if amount <= 0:
            embed = discord.Embed(
                title="Error",
                description="You must give at least 1 coin!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get user data
        giver_data = self.get_user_data(interaction.user.id)
        
        # Check if the giver has enough money
        if giver_data["balance"] < amount:
            embed = discord.Embed(
                title="Insufficient Funds",
                description=f"You don't have enough coins! You need {self.format_currency(amount)} but only have {self.format_currency(giver_data['balance'])}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get receiver data
        receiver_data = self.get_user_data(user.id)
        
        # Transfer the money
        giver_data["balance"] -= amount
        receiver_data["balance"] += amount
        receiver_data["total_earned"] += amount
        
        # Save data
        self.save_economy_data()
        
        # Create embed
        embed = discord.Embed(
            title="Money Transfer Successful",
            description=f"You have given {self.format_currency(amount)} to {user.mention}!",
            color=discord.Color.green(),
            timestamp=datetime.datetime.now()
        )
        
        embed.add_field(
            name="Your New Balance",
            value=self.format_currency(giver_data["balance"]),
            inline=True
        )
        
        embed.set_thumbnail(url="https://i.imgur.com/2Qjj1HL.png")  # Money transfer icon
        embed.set_footer(text=f"Transaction ID: {interaction.id}")
        
        await interaction.response.send_message(embed=embed)
        
        # Send a DM to the recipient
        try:
            recipient_embed = discord.Embed(
                title="Money Received!",
                description=f"You've received {self.format_currency(amount)} from {interaction.user.mention}!",
                color=discord.Color.gold(),
                timestamp=datetime.datetime.now()
            )
            
            recipient_embed.add_field(
                name="New Balance",
                value=self.format_currency(receiver_data["balance"]),
                inline=True
            )
            
            recipient_embed.set_thumbnail(url="https://i.imgur.com/MoMxkgm.png")  # Gift box icon
            recipient_embed.set_footer(text=f"Transaction ID: {interaction.id}")
            
            await user.send(embed=recipient_embed)
        except:
            # User might have DMs disabled
            pass
    
    @app_commands.command(name="leaderboard")
    async def leaderboard_command(self, interaction: discord.Interaction):
        """View the richest users in the server"""
        await interaction.response.defer(thinking=True)
        
        # Filter for users in the current guild
        guild_members = interaction.guild.members
        member_ids = [str(member.id) for member in guild_members]
        
        # Get economy data for users in this guild
        user_balances = []
        for user_id, data in self.economy_data.items():
            if user_id in member_ids:
                user = interaction.guild.get_member(int(user_id))
                if user:
                    user_balances.append((user, data["balance"]))
        
        # Sort by balance (highest to lowest)
        user_balances.sort(key=lambda x: x[1], reverse=True)
        
        # Only show top 10
        top_users = user_balances[:10]
        
        if not top_users:
            embed = discord.Embed(
                title="Economy Leaderboard",
                description="No users have economy data yet!",
                color=discord.Color.blue()
            )
            await interaction.followup.send(embed=embed)
            return
            
        # Create embed
        embed = discord.Embed(
            title=f"💰 Economy Leaderboard - {interaction.guild.name}",
            description="The richest users in the server:",
            color=discord.Color.gold()
        )
        
        # Add leaderboard positions
        for i, (user, balance) in enumerate(top_users, 1):
            medal = ""
            if i == 1:
                medal = "🥇 "
            elif i == 2:
                medal = "🥈 "
            elif i == 3:
                medal = "🥉 "
            else:
                medal = f"{i}. "
                
            embed.add_field(
                name=f"{medal}{user.display_name}",
                value=self.format_currency(balance),
                inline=False
            )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)
    
    @app_commands.command(name="shop")
    async def shop_command(self, interaction: discord.Interaction):
        """View items available in the shop"""
        user_data = self.get_user_data(interaction.user.id)
        
        # Create embed
        embed = discord.Embed(
            title="🛒 Server Shop",
            description=f"Your balance: {self.format_currency(user_data['balance'])}\nUse `/economy buy <item_id>` to purchase items.",
            color=discord.Color.blue()
        )
        
        # Add shop items
        for item_id, item in self.shop_items.items():
            embed.add_field(
                name=f"{item['name']} - {self.format_currency(item['price'])}",
                value=f"**ID:** `{item_id}`\n{item['description']}\n**Type:** {item['type'].capitalize()}",
                inline=False
            )
        
        embed.set_thumbnail(url="https://i.imgur.com/cQ4R4xC.png")  # Shop icon
        embed.set_footer(text="Shop prices are subject to change")
        
        await interaction.response.send_message(embed=embed)
    
    @app_commands.command(name="buy")
    @app_commands.describe(item_id="The ID of the item to buy")
    async def buy_command(self, interaction: discord.Interaction, item_id: str):
        """Buy an item from the shop"""
        # Check if item exists
        if item_id not in self.shop_items:
            embed = discord.Embed(
                title="Error",
                description=f"Item with ID `{item_id}` does not exist in the shop. Use `/economy shop` to see available items.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get user data and item info
        user_data = self.get_user_data(interaction.user.id)
        item = self.shop_items[item_id]
        
        # Check if user has enough money
        if user_data["balance"] < item["price"]:
            embed = discord.Embed(
                title="Insufficient Funds",
                description=f"You need {self.format_currency(item['price'])} to buy {item['name']}, but you only have {self.format_currency(user_data['balance'])}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Process the purchase based on item type
        if item["type"] == "role":
            # Handle role purchase
            role_id = item.get("role_id")
            
            # Check if role is configured for this server
            if not role_id:
                embed = discord.Embed(
                    title="Role Not Configured",
                    description=f"The role for {item['name']} has not been configured for this server yet.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Get the role
            role = interaction.guild.get_role(role_id)
            if not role:
                embed = discord.Embed(
                    title="Role Not Found",
                    description=f"The role for {item['name']} could not be found. Please contact an administrator.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
            # Give the role to the user
            try:
                await interaction.user.add_roles(role, reason=f"Purchased from shop for {item['price']} coins")
            except discord.Forbidden:
                embed = discord.Embed(
                    title="Permission Error",
                    description="I don't have permission to give you that role.",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            except Exception as e:
                embed = discord.Embed(
                    title="Error",
                    description=f"An error occurred while giving you the role: {str(e)}",
                    color=discord.Color.red()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
                
        elif item["type"] == "consumable":
            if item_id == "lootbox":
                # Process lootbox
                min_reward = item["price"] // 2
                max_reward = item["price"] * 2
                reward = random.randint(min_reward, max_reward)
                
                # Add reward to user's balance
                user_data["balance"] += reward
                user_data["total_earned"] += reward
                
                # Create special lootbox embed
                lootbox_embed = discord.Embed(
                    title="🎁 Lootbox Opened!",
                    description=f"You opened a Mystery Lootbox and found...\n\n{self.format_currency(reward)}!",
                    color=discord.Color.purple()
                )
                
                if reward > item["price"]:
                    lootbox_embed.description += f"\n\n🎉 You made a profit of {self.format_currency(reward - item['price'])}!"
                    
                lootbox_embed.set_thumbnail(url="https://i.imgur.com/MoMxkgm.png")
                
                # Deduct price from balance later
                
            elif item_id == "nickname":
                # Give them the ability to set a nickname
                # Here we just acknowledge the purchase; actual nickname change would be handled in a separate command
                pass
                
        # Save the inventory if needed (for inventory tracking)
        if not item["type"] == "consumable" or not item_id == "lootbox":  # Skip lootbox since it's immediately consumed
            if "inventory" not in user_data:
                user_data["inventory"] = []
                
            user_data["inventory"].append({
                "id": item_id,
                "name": item["name"],
                "purchased_at": time.time()
            })
        
        # Deduct the price
        user_data["balance"] -= item["price"]
        user_data["total_spent"] += item["price"]
        
        # Save data
        self.save_economy_data()
        
        # Send purchase confirmation
        embed = discord.Embed(
            title="Purchase Successful",
            description=f"You have purchased {item['name']} for {self.format_currency(item['price'])}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        await interaction.response.send_message(embed=embed)
        
        # Send lootbox result after purchase if applicable
        if item_id == "lootbox":
            await interaction.followup.send(embed=lootbox_embed)

    @app_commands.command(name="coinflip")
    @app_commands.describe(
        amount="The amount to bet",
        choice="Your guess for the coin flip"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip_command(self, interaction: discord.Interaction, amount: int, choice: str):
        """Flip a coin and bet on the outcome"""
        # Validate the bet amount
        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Bet",
                description="You must bet at least 1 coin!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get user data
        user_data = self.get_user_data(interaction.user.id)
        
        # Check if user has enough money
        if user_data["balance"] < amount:
            embed = discord.Embed(
                title="Insufficient Funds",
                description=f"You need {self.format_currency(amount)} to place this bet, but you only have {self.format_currency(user_data['balance'])}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Defer response to build suspense
        await interaction.response.defer(thinking=True)
        
        # Build initial embed
        embed = discord.Embed(
            title="🎲 Coin Flip",
            description=f"{interaction.user.mention} is betting {self.format_currency(amount)} on **{choice.capitalize()}**!",
            color=discord.Color.gold()
        )
        
        embed.set_image(url="https://i.imgur.com/7RJLnZY.gif")  # Coin flip GIF
        await interaction.followup.send(embed=embed)
        
        # Wait for animation
        await asyncio.sleep(2)
        
        # Determine the result
        result = random.choice(["heads", "tails"])
        won = result == choice.lower()
        
        # Update user balance
        if won:
            winnings = amount
            user_data["balance"] += winnings
            user_data["total_earned"] += winnings
            result_text = f"You won {self.format_currency(winnings)}!"
            color = discord.Color.green()
        else:
            user_data["balance"] -= amount
            user_data["total_spent"] += amount
            result_text = f"You lost {self.format_currency(amount)}!"
            color = discord.Color.red()
            
        # Save data
        self.save_economy_data()
        
        # Update the embed with result
        result_embed = discord.Embed(
            title=f"🎲 Coin Flip - {result.capitalize()}!",
            description=f"{interaction.user.mention} bet on **{choice.capitalize()}** and **{result.capitalize()}** came up.\n\n{result_text}",
            color=color
        )
        
        result_embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        # Set the appropriate image
        if result == "heads":
            result_embed.set_image(url=HEADS_IMAGE)
        else:
            result_embed.set_image(url=TAILS_IMAGE)
            
        await interaction.edit_original_response(embed=result_embed)

    @app_commands.command(name="slots")
    @app_commands.describe(amount="The amount to bet")
    async def slots_command(self, interaction: discord.Interaction, amount: int):
        """Play the slot machine"""
        # Validate the bet amount
        if amount <= 0:
            embed = discord.Embed(
                title="Invalid Bet",
                description="You must bet at least 1 coin!",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Get user data
        user_data = self.get_user_data(interaction.user.id)
        
        # Check if user has enough money
        if user_data["balance"] < amount:
            embed = discord.Embed(
                title="Insufficient Funds",
                description=f"You need {self.format_currency(amount)} to play slots, but you only have {self.format_currency(user_data['balance'])}.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
            
        # Defer response
        await interaction.response.defer(thinking=True)
        
        # Define slot machine symbols and their payouts
        symbols = ["🍒", "🍊", "🍋", "🍇", "🍉", "💎", "7️⃣"]
        weights = [20, 15, 15, 10, 10, 5, 2]  # Higher weight = more common
        payouts = {
            "🍒": 1.5,  # Three cherries pays 1.5x
            "🍊": 2,    # Three oranges pays 2x
            "🍋": 2,    # Three lemons pays 2x
            "🍇": 2.5,  # Three grapes pays 2.5x
            "🍉": 3,    # Three watermelons pays 3x
            "💎": 5,    # Three diamonds pays 5x
            "7️⃣": 10   # Three sevens pays 10x
        }
        
        # Special combination payouts
        special_combos = {
            "mixed_fruits": 1,  # Any 3 fruits pays 1x
            "mixed_symbols": 0.5  # Any 3 different symbols pays 0.5x
        }
        
        # Show initial slot machine
        slots_embed = discord.Embed(
            title="🎰 Slot Machine",
            description=f"{interaction.user.mention} is spinning the slot machine for {self.format_currency(amount)}!",
            color=discord.Color.blurple()
        )
        
        slots_embed.add_field(
            name="Spinning...",
            value="❓ | ❓ | ❓",
            inline=False
        )
        
        message = await interaction.followup.send(embed=slots_embed)
        
        # Simulate spinning animation
        await asyncio.sleep(1)
        
        # Generate results with weighted randomness
        results = random.choices(symbols, weights=weights, k=3)
        
        # Wait a bit between each reveal for suspense
        for i in range(3):
            revealed = results[:i+1] + ["❓"] * (2-i)
            spins_text = " | ".join(revealed)
            
            slots_embed.set_field_at(
                0,
                name="Spinning..." if i < 2 else "Result",
                value=spins_text,
                inline=False
            )
            
            await message.edit(embed=slots_embed)
            await asyncio.sleep(0.7)
        
        # Determine winnings
        winnings = 0
        
        # Check for matching symbols
        if results[0] == results[1] == results[2]:
            # All three symbols match
            multiplier = payouts[results[0]]
            winnings = amount * multiplier
            result_text = f"**JACKPOT!** Three {results[0]} symbols! {multiplier}x payout!"
        elif all(s in ["🍒", "🍊", "🍋", "🍇", "🍉"] for s in results):
            # All fruits combo
            winnings = amount * special_combos["mixed_fruits"]
            result_text = f"All fruits! {special_combos['mixed_fruits']}x payout!"
        elif results[0] != results[1] and results[1] != results[2] and results[0] != results[2]:
            # All different symbols
            winnings = amount * special_combos["mixed_symbols"]
            result_text = f"All different symbols! {special_combos['mixed_symbols']}x payout!"
        else:
            # No win
            winnings = 0
            result_text = "No matching symbols. Better luck next time!"
            
        # Round winnings to nearest integer
        winnings = int(winnings)
        
        # Update user balance
        if winnings > 0:
            user_data["balance"] += winnings
            user_data["total_earned"] += winnings
            color = discord.Color.green()
        else:
            user_data["balance"] -= amount
            user_data["total_spent"] += amount
            color = discord.Color.red()
            
        # Save data
        self.save_economy_data()
        
        # Update the embed with final result
        slots_embed = discord.Embed(
            title="🎰 Slot Machine Results",
            description=f"{interaction.user.mention} bet {self.format_currency(amount)}",
            color=color
        )
        
        slots_embed.add_field(
            name="Result",
            value=" | ".join(results),
            inline=False
        )
        
        slots_embed.add_field(
            name="Outcome",
            value=result_text,
            inline=False
        )
        
        if winnings > 0:
            slots_embed.add_field(
                name="Winnings",
                value=self.format_currency(winnings),
                inline=True
            )
        
        slots_embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=True
        )
        
        # Set thumbnail to slot machine image
        slots_embed.set_thumbnail(url="https://i.imgur.com/Nqpw7GK.png")  # Slot machine icon
        
        await message.edit(embed=slots_embed)

    async def calculate_passive_income(self, user_id):
        """Calculate passive income for a user based on their owned income-generating items"""
        user_data = self.get_user_data(user_id)
        if "inventory" not in user_data or not user_data["inventory"]:
            return 0
            
        # Get current time
        current_time = time.time()
        total_income = 0
        last_collected = user_data.get("last_income_collection", 0)
        
        # Calculate time since last collection
        time_elapsed = current_time - last_collected
        
        # Process each inventory item
        for item in user_data["inventory"]:
            item_id = item.get("id")
            purchase_time = item.get("purchased_at", 0)
            
            # Skip non-passive income items
            if item_id not in self.shop_items:
                continue
                
            shop_item = self.shop_items[item_id]
            if shop_item.get("type") != "passive_income":
                continue
                
            # Calculate income based on time elapsed
            income_rate = shop_item.get("income_rate", 0)
            income_period = shop_item.get("income_period", 3600)  # Default to hourly
            
            # Calculate periods elapsed (e.g., how many hours) since last collection
            periods_elapsed = time_elapsed / income_period
            
            # Calculate income for this item
            item_income = int(income_rate * periods_elapsed)
            total_income += item_income
            
        # Return the calculated total income
        return int(total_income)
        
    @app_commands.command(name="collect")
    async def collect_command(self, interaction: discord.Interaction):
        """Collect income from your passive income sources"""
        user_id = str(interaction.user.id)
        user_data = self.get_user_data(user_id)
        
        # Calculate income
        income = await self.calculate_passive_income(user_id)
        
        # Update user data
        if income > 0:
            user_data["balance"] += income
            user_data["total_earned"] += income
            user_data["last_income_collection"] = time.time()
            self.save_economy_data()
            
            # Create embed
            embed = discord.Embed(
                title="💰 Income Collected!",
                description=f"You have collected {self.format_currency(income)} from your passive income sources!",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="New Balance",
                value=self.format_currency(user_data["balance"]),
                inline=False
            )
            
            # List active income sources
            active_sources = []
            for item in user_data["inventory"]:
                if item["id"] in self.shop_items and self.shop_items[item["id"]]["type"] == "passive_income":
                    source = self.shop_items[item["id"]]
                    active_sources.append(f"• {source['name']}: {self.format_currency(source['income_rate'])} per hour")
            
            if active_sources:
                embed.add_field(
                    name="Active Income Sources",
                    value="\n".join(active_sources),
                    inline=False
                )
                
            embed.set_footer(text="Income is generated over time even when you're offline!")
            await interaction.response.send_message(embed=embed)
        else:
            # No income or no passive income sources
            if not any(item["id"] in self.shop_items and self.shop_items[item["id"]]["type"] == "passive_income" 
                      for item in user_data.get("inventory", [])):
                embed = discord.Embed(
                    title="No Income Sources",
                    description="You don't have any passive income sources yet. Visit the shop to purchase windmills, farms, or other income-generating items!",
                    color=discord.Color.red()
                )
                embed.set_footer(text="Use /economy shop to browse available items")
            else:
                embed = discord.Embed(
                    title="No Income to Collect",
                    description="You don't have any income to collect right now. Check back later!",
                    color=discord.Color.gold()
                )
                
                # Calculate time until next significant income
                best_item = None
                best_rate = 0
                for item in user_data["inventory"]:
                    if item["id"] in self.shop_items and self.shop_items[item["id"]]["type"] == "passive_income":
                        rate = self.shop_items[item["id"]]["income_rate"]
                        if rate > best_rate:
                            best_rate = rate
                            best_item = self.shop_items[item["id"]]
                
                if best_item:
                    embed.set_footer(text=f"Your {best_item['name']} generates {self.format_currency(best_item['income_rate'])} per hour")
                
            await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    # First, remove the old economy commands if they exist
    try:
        await bot.unload_extension("cogs.economy")
        bot.logger.info("Unloaded old economy extension")
    except:
        pass
        
    # Load the new slash-based economy commands
    await bot.add_cog(EconomySlashCommands(bot))
    bot.logger.info("Loaded economy slash commands extension") 