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

from utils.slash_helper import SlashHelper
from utils.embed_helper import EmbedHelper

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
HEADS_IMAGE = "https://i.imgur.com/1mu0idy.png"  # Update with user's actual heads image
TAILS_IMAGE = "https://i.imgur.com/JgGr5xz.png"  # Update with user's actual tails image

class Economy(commands.Cog):
    """Economy commands for currency, gambling, and shop features"""
    
    def __init__(self, bot):
        self.bot = bot
        self.currency_name = DEFAULT_CURRENCY_NAME
        self.currency_emoji = DEFAULT_CURRENCY_EMOJI
        self.economy_data = {}
        self.cooldowns = {}
        self.load_economy_data()
        
        # Setup the economy command group
        self.economy_group = app_commands.Group(name="economy", description="Economy and currency commands")
        self.gambling_group = app_commands.Group(name="gamble", description="Gambling commands for economy")
        
        # Add groups to the bot's command tree
        self.bot.tree.add_command(self.economy_group)
        self.bot.tree.add_command(self.gambling_group)
        
        # Shop items - Name, price, description, role_id (if applicable)
        self.shop_items = [
            {"id": "vip", "name": "VIP Status", "price": 5000, "description": "Exclusive VIP role in the server", "role_based": True, "role_id": None},
            {"id": "colorchange", "name": "Custom Color", "price": 2000, "description": "Change your name color in the server", "role_based": False},
            {"id": "lootbox", "name": "Mystery Lootbox", "price": 1000, "description": "Contains random amount of coins (500-2000)", "role_based": False}
        ]
    
    def load_economy_data(self):
        """Load economy data from file"""
        try:
            if os.path.exists(ECONOMY_FILE):
                with open(ECONOMY_FILE, 'r') as f:
                    self.economy_data = json.load(f)
                self.bot.logger.info("Economy data loaded successfully")
            else:
                self.economy_data = {"users": {}}
                self.save_economy_data()
                self.bot.logger.info("Created new economy data file")
        except Exception as e:
            self.bot.logger.error(f"Error loading economy data: {e}")
            self.economy_data = {"users": {}}
    
    def save_economy_data(self):
        """Save economy data to file"""
        try:
            with open(ECONOMY_FILE, 'w') as f:
                json.dump(self.economy_data, f, indent=4)
        except Exception as e:
            self.bot.logger.error(f"Error saving economy data: {e}")
    
    def get_user_data(self, user_id):
        """Get a user's economy data, creating it if it doesn't exist"""
        user_id = str(user_id)  # Convert to string for JSON serialization
        
        if user_id not in self.economy_data["users"]:
            self.economy_data["users"][user_id] = {
                "balance": DEFAULT_STARTING_BALANCE,
                "last_daily": 0,
                "inventory": [],
                "total_earned": DEFAULT_STARTING_BALANCE,
                "total_spent": 0,
                "transactions": []
            }
            self.save_economy_data()
            
        return self.economy_data["users"][user_id]
    
    def format_currency(self, amount):
        """Format currency amount with emoji and name"""
        return f"{self.currency_emoji} **{amount:,}** {self.currency_name}"
    
    @economy_group.command(name="balance", description="Check your or another user's balance")
    @app_commands.describe(user="The user to check balance for (defaults to yourself)")
    async def economy_balance(self, interaction: discord.Interaction, user: Optional[discord.User] = None):
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
    
    @economy_group.command(name="daily", description="Claim your daily reward")
    async def economy_daily(self, interaction: discord.Interaction):
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
                title="Daily Reward - On Cooldown",
                description=f"You've already claimed your daily reward. Please wait **{hours}h {minutes}m {seconds}s**.",
                color=discord.Color.red()
            )
            
            # Calculate next available time
            next_available = datetime.datetime.fromtimestamp(last_daily + cooldown)
            embed.add_field(
                name="Next Available",
                value=f"<t:{int(next_available.timestamp())}:R>",
                inline=False
            )
            
            embed.set_thumbnail(url="https://i.imgur.com/6YToyEF.png")  # Clock icon
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        # Calculate streak bonus
        streak = 1
        streak_bonus = 0
        
        if time_since_last < (cooldown * 2) and time_since_last >= cooldown:
            # User claimed within 48 hours of last claim
            streak = user_data.get("streak", 0) + 1
            streak_bonus = min(streak * 10, 100)  # Cap at 100 bonus
        else:
            # Reset streak
            streak = 1
        
        user_data["streak"] = streak
        
        # Calculate amount
        amount = DEFAULT_DAILY_AMOUNT + streak_bonus
        
        # Update user data
        user_data["balance"] += amount
        user_data["last_daily"] = current_time
        user_data["total_earned"] += amount
        
        # Add transaction record
        user_data["transactions"].append({
            "type": "daily",
            "amount": amount,
            "timestamp": current_time
        })
        
        # Save data
        self.save_economy_data()
        
        # Create embed response
        embed = discord.Embed(
            title="Daily Reward Claimed!",
            description=f"You've received {self.format_currency(amount)}!",
            color=discord.Color.green()
        )
        
        if streak_bonus > 0:
            embed.add_field(
                name="Streak Bonus",
                value=f"Streak: **{streak}** days\nBonus: +{self.format_currency(streak_bonus)}",
                inline=False
            )
        
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        embed.set_thumbnail(url="https://i.imgur.com/HvRReSJ.png")  # Coins icon
        embed.set_footer(text=f"Come back tomorrow for another reward! • Streak: {streak} day(s)")
        
        await interaction.response.send_message(embed=embed)
    
    @economy_group.command(name="give", description="Give money to another user")
    @app_commands.describe(
        user="The user to give money to",
        amount="The amount to give"
    )
    async def economy_give(self, interaction: discord.Interaction, user: discord.User, amount: int):
        """Give some of your currency to another user"""
        if user.id == interaction.user.id:
            await SlashHelper.error(
                interaction,
                title="Invalid Transfer",
                description="You can't give money to yourself!",
                ephemeral=True
            )
            return
            
        if amount <= 0:
            await SlashHelper.error(
                interaction,
                title="Invalid Amount",
                description="Please provide a positive amount to give.",
                ephemeral=True
            )
            return
        
        # Get user data
        sender_data = self.get_user_data(interaction.user.id)
        
        # Check if sender has enough money
        if sender_data["balance"] < amount:
            await SlashHelper.error(
                interaction,
                title="Insufficient Funds",
                description=f"You don't have enough {self.currency_name}. You have {self.format_currency(sender_data['balance'])}.",
                ephemeral=True
            )
            return
        
        # Get recipient data
        recipient_data = self.get_user_data(user.id)
        
        # Transfer the money
        sender_data["balance"] -= amount
        recipient_data["balance"] += amount
        sender_data["total_spent"] += amount
        recipient_data["total_earned"] += amount
        
        # Add transaction records
        current_time = time.time()
        
        sender_data["transactions"].append({
            "type": "transfer_out",
            "to": str(user.id),
            "amount": amount,
            "timestamp": current_time
        })
        
        recipient_data["transactions"].append({
            "type": "transfer_in",
            "from": str(interaction.user.id),
            "amount": amount,
            "timestamp": current_time
        })
        
        # Save data
        self.save_economy_data()
        
        # Create embed response
        embed = discord.Embed(
            title="Transfer Successful",
            description=f"You've sent {self.format_currency(amount)} to {user.mention}!",
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Your New Balance",
            value=self.format_currency(sender_data["balance"]),
            inline=True
        )
        
        embed.add_field(
            name=f"{user.display_name}'s New Balance",
            value=self.format_currency(recipient_data["balance"]),
            inline=True
        )
        
        embed.set_thumbnail(url="https://i.imgur.com/T2yCLMD.png")  # Money transfer icon
        embed.set_footer(text=f"Transaction ID: {int(current_time)}")
        
        await interaction.response.send_message(embed=embed)
        
        # Notify recipient
        try:
            recipient_embed = discord.Embed(
                title="Money Received!",
                description=f"You've received {self.format_currency(amount)} from {interaction.user.mention}!",
                color=discord.Color.green()
            )
            
            recipient_embed.add_field(
                name="Your New Balance",
                value=self.format_currency(recipient_data["balance"]),
                inline=True
            )
            
            recipient_embed.set_footer(text=f"Transaction ID: {int(current_time)}")
            
            await user.send(embed=recipient_embed)
        except:
            pass  # Ignore if we can't DM the user
    
    @economy_group.command(name="leaderboard", description="View the richest users in the server")
    async def economy_leaderboard(self, interaction: discord.Interaction):
        """Display a leaderboard of the richest users in the server"""
        await interaction.response.defer(thinking=True)
        
        # Get all users in the server and their balances
        server_users = []
        for user_id, data in self.economy_data["users"].items():
            try:
                # Check if user is in the server
                member = interaction.guild.get_member(int(user_id))
                if member:
                    server_users.append((
                        user_id,
                        data["balance"],
                        member.display_name
                    ))
            except:
                continue
        
        # Sort by balance (highest first)
        server_users.sort(key=lambda x: x[1], reverse=True)
        
        # Only show top 10
        top_users = server_users[:10]
        
        if not top_users:
            await SlashHelper.error(
                interaction,
                title="No Data Available",
                description="There are no users with economy data in this server yet.",
                ephemeral=True
            )
            return
        
        # Create the embed
        embed = discord.Embed(
            title=f"{interaction.guild.name} Economy Leaderboard",
            description=f"The richest users in the server",
            color=discord.Color.gold()
        )
        
        # Add fields for each user
        for i, (user_id, balance, display_name) in enumerate(top_users, 1):
            # Special formatting for top 3
            if i == 1:
                prefix = "🥇 "
            elif i == 2:
                prefix = "🥈 "
            elif i == 3:
                prefix = "🥉 "
            else:
                prefix = f"{i}. "
                
            embed.add_field(
                name=f"{prefix}{display_name}",
                value=self.format_currency(balance),
                inline=False
            )
        
        # Add user's rank if not in top 10
        if str(interaction.user.id) not in [user_id for user_id, _, _ in top_users]:
            # Find user's position
            user_rank = next((i for i, (user_id, _, _) in enumerate(server_users, 1) 
                             if user_id == str(interaction.user.id)), None)
            
            if user_rank:
                user_data = self.get_user_data(interaction.user.id)
                embed.add_field(
                    name="─" * 20,
                    value=f"**Your Rank: #{user_rank}**\nBalance: {self.format_currency(user_data['balance'])}",
                    inline=False
                )
        
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else None)
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • Updated {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        await interaction.followup.send(embed=embed)
    
    @economy_group.command(name="shop", description="View items available in the shop")
    async def economy_shop(self, interaction: discord.Interaction):
        """Display the shop with items available for purchase"""
        embed = discord.Embed(
            title="ModuBot Shop",
            description=f"Use `/economy buy <item_id>` to purchase an item",
            color=discord.Color.dark_purple()
        )
        
        # Get user data for showing if they can afford items
        user_data = self.get_user_data(interaction.user.id)
        user_balance = user_data["balance"]
        
        # List all shop items
        for item in self.shop_items:
            # Check if user can afford
            affordable = "✅" if user_balance >= item["price"] else "❌"
            
            # Format price
            price_str = f"{self.currency_emoji} **{item['price']:,}**"
            
            embed.add_field(
                name=f"{item['name']} ({item['id']})",
                value=f"{item['description']}\n**Price:** {price_str} {affordable}",
                inline=False
            )
        
        embed.add_field(
            name="Your Balance",
            value=self.format_currency(user_balance),
            inline=False
        )
            
        embed.set_thumbnail(url="https://i.imgur.com/VDC6Fas.png")  # Shop icon
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        await interaction.response.send_message(embed=embed)
    
    @economy_group.command(name="buy", description="Buy an item from the shop")
    @app_commands.describe(item_id="The ID of the item to buy")
    async def economy_buy(self, interaction: discord.Interaction, item_id: str):
        """Purchase an item from the shop using your currency"""
        # Find the item
        item = next((item for item in self.shop_items if item["id"].lower() == item_id.lower()), None)
        
        if not item:
            await SlashHelper.error(
                interaction,
                title="Item Not Found",
                description=f"Could not find an item with ID '{item_id}'. Use `/economy shop` to see available items.",
                ephemeral=True
            )
            return
        
        # Get user data
        user_data = self.get_user_data(interaction.user.id)
        
        # Check if user can afford
        if user_data["balance"] < item["price"]:
            await SlashHelper.error(
                interaction,
                title="Insufficient Funds",
                description=f"You need {self.format_currency(item['price'])} to buy this item. You have {self.format_currency(user_data['balance'])}.",
                ephemeral=True
            )
            return
        
        # Handle purchase based on item type
        if item["id"] == "vip":
            # Check if role exists and bot has permission
            vip_role = None
            if item["role_id"]:
                vip_role = interaction.guild.get_role(item["role_id"])
            
            # If no role is set or role doesn't exist, try to find one by name
            if not vip_role:
                vip_role = discord.utils.get(interaction.guild.roles, name="VIP")
            
            # If still no role, try to create one
            if not vip_role:
                try:
                    vip_role = await interaction.guild.create_role(
                        name="VIP",
                        color=discord.Color.gold(),
                        reason="ModuBot Economy: VIP role purchase"
                    )
                    item["role_id"] = vip_role.id
                    self.save_economy_data()
                except:
                    await SlashHelper.error(
                        interaction,
                        title="Role Error",
                        description="Could not find or create a VIP role. Please ask a server admin to set one up.",
                        ephemeral=True
                    )
                    return
            
            # Try to add role to user
            try:
                await interaction.user.add_roles(vip_role, reason="ModuBot Economy: Purchased VIP status")
            except:
                await SlashHelper.error(
                    interaction,
                    title="Permission Error",
                    description="I don't have permission to assign roles. Please ask a server admin for help.",
                    ephemeral=True
                )
                return
                
            purchase_description = f"You've purchased VIP status and received the {vip_role.mention} role!"
            
        elif item["id"] == "colorchange":
            # Start a process to select a color
            purchase_description = "You've purchased a custom color! A color picker will open after this message."
            
        elif item["id"] == "lootbox":
            # Random amount between 500-2000
            reward = random.randint(500, 2000)
            user_data["balance"] += reward  # Add the reward
            user_data["total_earned"] += reward
            purchase_description = f"You've opened a Mystery Lootbox and found {self.format_currency(reward)}!"
            
        else:
            purchase_description = f"You've purchased {item['name']}!"
        
        # Deduct the cost
        user_data["balance"] -= item["price"]
        user_data["total_spent"] += item["price"]
        
        # Add to inventory if it's an item to keep
        if item["id"] not in ["lootbox"]:  # Lootbox is used immediately
            user_data["inventory"].append({
                "item_id": item["id"],
                "name": item["name"],
                "purchased_at": time.time()
            })
        
        # Add transaction record
        user_data["transactions"].append({
            "type": "purchase",
            "item_id": item["id"],
            "name": item["name"],
            "price": item["price"],
            "timestamp": time.time()
        })
        
        # Save data
        self.save_economy_data()
        
        # Send success message
        embed = discord.Embed(
            title="Purchase Successful!",
            description=purchase_description,
            color=discord.Color.green()
        )
        
        embed.add_field(
            name="Item",
            value=item["name"],
            inline=True
        )
        
        embed.add_field(
            name="Price",
            value=self.format_currency(item["price"]),
            inline=True
        )
        
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        embed.set_thumbnail(url="https://i.imgur.com/VDC6Fas.png")  # Shop icon
        embed.set_footer(text=f"Thank you for your purchase, {interaction.user.display_name}!")
        
        await interaction.response.send_message(embed=embed)
        
        # Handle color change if that was purchased
        if item["id"] == "colorchange":
            # This would be handled with a view with color buttons
            # For simplicity, let's just ask for the color hex code
            await asyncio.sleep(2)  # Wait a bit for the first message to be read
            
            color_msg = await interaction.channel.send(
                f"{interaction.user.mention} Please enter a color hex code (e.g., #FF0000 for red):"
            )
            
            try:
                response_message = await self.bot.wait_for(
                    'message',
                    check=lambda m: m.author == interaction.user and m.channel == interaction.channel,
                    timeout=60.0
                )
                
                # Try to parse the color
                color_input = response_message.content.strip().lstrip('#')
                if len(color_input) == 6:
                    try:
                        color_value = int(color_input, 16)
                        color_obj = discord.Color(color_value)
                        
                        # Find a role named after the user or create one
                        role_name = f"{interaction.user.name}'s Color"
                        color_role = discord.utils.get(interaction.guild.roles, name=role_name)
                        
                        if color_role:
                            await color_role.edit(color=color_obj, reason="ModuBot Economy: Color change purchase")
                        else:
                            color_role = await interaction.guild.create_role(
                                name=role_name,
                                color=color_obj,
                                reason="ModuBot Economy: Color change purchase"
                            )
                            
                            # Add role to user
                            await interaction.user.add_roles(color_role, reason="ModuBot Economy: Color change purchase")
                        
                        await interaction.channel.send(
                            embed=discord.Embed(
                                title="Color Changed!",
                                description=f"Your color has been changed to #{color_input}!",
                                color=color_obj
                            )
                        )
                        
                    except Exception as e:
                        await interaction.channel.send(f"Error setting color: {e}")
                else:
                    await interaction.channel.send("Invalid color format. Please use a 6-digit hex code (e.g., FF0000 for red).")
                    
            except asyncio.TimeoutError:
                await interaction.channel.send("Color selection timed out. You can try again later with `/economy buy colorchange`")
            
            # Clean up the prompt message
            try:
                await color_msg.delete()
            except:
                pass
    
    @gambling_group.command(name="coinflip", description="Flip a coin and bet on the outcome")
    @app_commands.describe(
        amount="The amount to bet",
        choice="Your guess for the coin flip"
    )
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def gamble_coinflip(self, interaction: discord.Interaction, amount: int, choice: str):
        """Bet on a coin flip. Double your bet if you win!
        
        This is a simple gambling game where you bet on either heads or tails.
        If you guess correctly, you win the same amount you bet (doubling your money).
        If you guess incorrectly, you lose your bet.
        
        The coin flip is completely random, giving you a 50/50 chance to win.
        
        Examples:
        `/gamble coinflip 100 heads` - Bet 100 coins on heads
        `/gamble coinflip 500 tails` - Bet 500 coins on tails
        """
        # Validate bet amount
        if amount <= 0:
            await SlashHelper.error(
                interaction,
                title="Invalid Bet",
                description="Please provide a positive amount to bet.",
                ephemeral=True
            )
            return
        
        # Get user data
        user_data = self.get_user_data(interaction.user.id)
        
        # Check if user has enough money
        if user_data["balance"] < amount:
            await SlashHelper.error(
                interaction,
                title="Insufficient Funds",
                description=f"You don't have enough {self.currency_name}. You have {self.format_currency(user_data['balance'])}.",
                ephemeral=True
            )
            return
        
        # Show "thinking" response for suspense
        await interaction.response.defer(thinking=True)
        await asyncio.sleep(1.5)  # Add a slight delay for suspense
        
        # Flip the coin (50/50 chance)
        result = random.choice(["heads", "tails"])
        
        # Determine if user won
        won = choice.lower() == result
        
        # Calculate winnings
        if won:
            winnings = amount  # Double the bet (return original bet + winnings)
            user_data["balance"] += winnings
            user_data["total_earned"] += winnings
            
            outcome_title = "You Won!"
            outcome_color = discord.Color.green()
            outcome_description = f"The coin landed on **{result.title()}**. You won {self.format_currency(winnings)}!"
        else:
            user_data["balance"] -= amount
            user_data["total_spent"] += amount
            
            outcome_title = "You Lost!"
            outcome_color = discord.Color.red()
            outcome_description = f"The coin landed on **{result.title()}**. You lost {self.format_currency(amount)}."
        
        # Add transaction record
        user_data["transactions"].append({
            "type": "gambling",
            "game": "coinflip",
            "bet": amount,
            "choice": choice,
            "result": result,
            "outcome": "win" if won else "loss",
            "amount_change": winnings if won else -amount,
            "timestamp": time.time()
        })
        
        # Save data
        self.save_economy_data()
        
        # Create the embed
        embed = discord.Embed(
            title=f"Coin Flip: {outcome_title}",
            description=outcome_description,
            color=outcome_color
        )
        
        embed.add_field(
            name="Your Choice",
            value=choice.title(),
            inline=True
        )
        
        embed.add_field(
            name="Result",
            value=result.title(),
            inline=True
        )
        
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        # Set the thumbnail based on the result
        if result == "heads":
            embed.set_image(url=HEADS_IMAGE)
        else:
            embed.set_image(url=TAILS_IMAGE)
        
        # Set footer
        embed.set_footer(text=f"Gambling odds: 50/50 • Payout: 2x • Requested by {interaction.user.display_name}")
        
        await interaction.followup.send(embed=embed)
    
    @gambling_group.command(name="slots", description="Play the slot machine")
    @app_commands.describe(amount="The amount to bet")
    async def gamble_slots(self, interaction: discord.Interaction, amount: int):
        """Play the slot machine. Match symbols for different payouts!"""
        # Validate bet amount
        if amount <= 0:
            await SlashHelper.error(
                interaction,
                title="Invalid Bet",
                description="Please provide a positive amount to bet.",
                ephemeral=True
            )
            return
        
        # Get user data
        user_data = self.get_user_data(interaction.user.id)
        
        # Check if user has enough money
        if user_data["balance"] < amount:
            await SlashHelper.error(
                interaction,
                title="Insufficient Funds",
                description=f"You don't have enough {self.currency_name}. You have {self.format_currency(user_data['balance'])}.",
                ephemeral=True
            )
            return
        
        # Show "thinking" response while preparing the result
        await interaction.response.defer(thinking=True)
        
        # Slot machine symbols with weights
        symbols = ["🍒", "🍋", "🍇", "🍊", "🍉", "🍓", "💎", "7️⃣"]
        weights = [30, 25, 20, 15, 10, 7, 2, 1]  # Higher weight = more common
        
        # Roll the slots
        rolls = []
        for _ in range(3):
            rolls.append(random.choices(symbols, weights=weights, k=1)[0])
        
        # Determine winnings
        winnings = 0
        
        # All three matching
        if rolls[0] == rolls[1] == rolls[2]:
            if rolls[0] == "7️⃣":
                # Jackpot!
                multiplier = 50
            elif rolls[0] == "💎":
                multiplier = 25
            elif rolls[0] in ["🍓", "🍉"]:
                multiplier = 10
            elif rolls[0] in ["🍊", "🍇"]:
                multiplier = 5
            else:  # Common fruits
                multiplier = 3
                
            winnings = amount * multiplier
        
        # Two matching
        elif (rolls[0] == rolls[1]) or (rolls[1] == rolls[2]) or (rolls[0] == rolls[2]):
            # Find the matching symbol
            if rolls[0] == rolls[1] or rolls[0] == rolls[2]:
                match = rolls[0]
            else:
                match = rolls[1]
                
            if match == "7️⃣":
                multiplier = 7
            elif match == "💎":
                multiplier = 5
            elif match in ["🍓", "🍉"]:
                multiplier = 2
            else:
                multiplier = 1
                
            winnings = amount * multiplier
        
        # No matches - player loses
        
        # Update balance
        net_change = winnings - amount
        user_data["balance"] += net_change
        
        if net_change > 0:
            user_data["total_earned"] += winnings
            outcome = "win"
            
            title = "You Won!"
            color = discord.Color.green()
            description = f"You rolled [{rolls[0]} | {rolls[1]} | {rolls[2]}] and won {self.format_currency(winnings)}!"
            
        else:
            user_data["total_spent"] += amount
            outcome = "loss"
            
            title = "You Lost!"
            color = discord.Color.red()
            description = f"You rolled [{rolls[0]} | {rolls[1]} | {rolls[2]}] and lost {self.format_currency(amount)}."
        
        # Add transaction record
        user_data["transactions"].append({
            "type": "gambling",
            "game": "slots",
            "bet": amount,
            "result": rolls,
            "outcome": outcome,
            "amount_change": net_change,
            "timestamp": time.time()
        })
        
        # Save data
        self.save_economy_data()
        
        # Create the embed
        embed = discord.Embed(
            title=f"Slot Machine: {title}",
            description=description,
            color=color
        )
        
        embed.add_field(
            name="Bet",
            value=self.format_currency(amount),
            inline=True
        )
        
        embed.add_field(
            name="Result",
            value=f"{rolls[0]} | {rolls[1]} | {rolls[2]}",
            inline=True
        )
        
        if winnings > 0:
            embed.add_field(
                name="Payout",
                value=self.format_currency(winnings),
                inline=True
            )
            
        embed.add_field(
            name="New Balance",
            value=self.format_currency(user_data["balance"]),
            inline=False
        )
        
        # Set thumbnail to slot machine image
        embed.set_thumbnail(url="https://i.imgur.com/Nqpw7GK.png")  # Slot machine icon
        
        await interaction.followup.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.logger.info("Economy cog is ready")

async def setup(bot):
    await bot.add_cog(Economy(bot)) 