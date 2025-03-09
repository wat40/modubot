import discord
from discord.ext import commands
import random
import asyncio
import json
import requests
from datetime import datetime
from utils.embed_helper import EmbedHelper
from utils.database import Database

class Entertainment(commands.Cog):
    """Entertainment commands for fun and engagement"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.trivia_categories = None
        self.trivia_sessions = {}
        self.hangman_games = {}
        self.eight_ball_responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes, definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful."
        ]
        
    @commands.command()
    async def meme(self, ctx):
        """Get a random meme from Reddit"""
        try:
            # Fetch meme data from Reddit's meme subreddits
            subreddits = ["memes", "dankmemes", "wholesomememes", "me_irl"]
            subreddit = random.choice(subreddits)
            
            response = requests.get(f"https://www.reddit.com/r/{subreddit}/hot.json?limit=50", 
                                    headers={"User-Agent": "ModuBot Discord Bot"})
            
            if response.status_code != 200:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description="Failed to fetch memes. Please try again later."
                )
                return await ctx.send(embed=embed)
                
            posts = [post for post in response.json()["data"]["children"] 
                     if not post["data"]["stickied"] and post["data"]["url"].endswith(("jpg", "jpeg", "png", "gif"))]
            
            if not posts:
                embed = EmbedHelper.error_embed(
                    title="No Memes Found",
                    description="Couldn't find any memes. Please try again later."
                )
                return await ctx.send(embed=embed)
            
            post = random.choice(posts)
            title = post["data"]["title"]
            url = post["data"]["url"]
            permalink = post["data"]["permalink"]
            post_url = f"https://reddit.com{permalink}"
            author = post["data"]["author"]
            subreddit_name = post["data"]["subreddit_name_prefixed"]
            ups = post["data"]["ups"]
            
            embed = EmbedHelper.create_embed(
                title=title,
                color=0xFF4500,  # Reddit orange
                footer={"text": f"👍 {ups} | Posted by u/{author} in {subreddit_name}"},
                image=url,
                url=post_url
            )
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"An error occurred while fetching memes: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.command(aliases=["8ball"])
    async def eightball(self, ctx, *, question=None):
        """Ask the magic 8-ball a question"""
        if not question:
            embed = EmbedHelper.error_embed(
                title="Missing Question",
                description="You need to ask the 8-ball a question!"
            )
            return await ctx.send(embed=embed)
        
        response = random.choice(self.eight_ball_responses)
        
        embed = EmbedHelper.create_embed(
            title="Magic 8-Ball",
            color=0x8B008B,  # Dark Magenta
            fields=[
                {"name": "Question", "value": question},
                {"name": "Answer", "value": response}
            ],
            thumbnail="https://i.imgur.com/XlAqDVF.png"  # 8-ball image
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trivia(self, ctx, category=None):
        """Start a trivia game. Optionally specify a category."""
        if ctx.channel.id in self.trivia_sessions:
            embed = EmbedHelper.warning_embed(
                title="Trivia In Progress",
                description="There's already a trivia game running in this channel. Please wait for it to finish."
            )
            return await ctx.send(embed=embed)
            
        if not self.trivia_categories:
            try:
                # Fetch trivia categories from Open Trivia DB
                response = requests.get("https://opentdb.com/api_category.php")
                if response.status_code == 200:
                    self.trivia_categories = response.json()["trivia_categories"]
                else:
                    embed = EmbedHelper.error_embed(
                        title="Error",
                        description="Failed to fetch trivia categories. Using a random category."
                    )
                    await ctx.send(embed=embed)
            except Exception:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description="Failed to fetch trivia categories. Using a random category."
                )
                await ctx.send(embed=embed)
        
        category_id = None
        category_name = "Random"
        
        if category and self.trivia_categories:
            # Try to match the category
            for cat in self.trivia_categories:
                if category.lower() in cat["name"].lower():
                    category_id = cat["id"]
                    category_name = cat["name"]
                    break
        
        try:
            # Build the API URL
            url = "https://opentdb.com/api.php?amount=1&type=multiple"
            if category_id:
                url += f"&category={category_id}"
            
            # Fetch a trivia question
            response = requests.get(url)
            if response.status_code != 200:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description="Failed to fetch trivia questions. Please try again later."
                )
                return await ctx.send(embed=embed)
            
            data = response.json()
            if data["response_code"] != 0 or not data["results"]:
                embed = EmbedHelper.error_embed(
                    title="Error",
                    description="Failed to fetch trivia questions. Please try again later."
                )
                return await ctx.send(embed=embed)
            
            # Process the question
            result = data["results"][0]
            question = result["question"].replace("&quot;", "\"").replace("&#039;", "'").replace("&amp;", "&")
            correct_answer = result["correct_answer"].replace("&quot;", "\"").replace("&#039;", "'").replace("&amp;", "&")
            incorrect_answers = [answer.replace("&quot;", "\"").replace("&#039;", "'").replace("&amp;", "&") for answer in result["incorrect_answers"]]
            
            # All possible answers
            answers = [correct_answer] + incorrect_answers
            random.shuffle(answers)
            
            # Find the correct answer's index
            correct_index = answers.index(correct_answer)
            
            # Create the question embed
            embed = EmbedHelper.create_embed(
                title=f"Trivia: {category_name}",
                description=f"**Difficulty:** {result['difficulty'].capitalize()}\n\n{question}",
                color=0x3498DB,  # Blue
                fields=[{"name": "Answers", "value": "\n".join([f"{i+1}. {answer}" for i, answer in enumerate(answers)])}],
                footer={"text": "You have 15 seconds to answer. Reply with the number of your answer."}
            )
            
            # Send the question
            question_message = await ctx.send(embed=embed)
            
            # Setup trivia session
            self.trivia_sessions[ctx.channel.id] = {
                "correct_answer": correct_answer,
                "correct_index": correct_index,
                "answers": answers,
                "players": {},
                "answered": set()
            }
            
            # Wait for answers
            await asyncio.sleep(15)
            
            # Clean up the session
            if ctx.channel.id in self.trivia_sessions:
                session = self.trivia_sessions.pop(ctx.channel.id)
                
                # Check if anyone answered
                if not session["players"]:
                    embed = EmbedHelper.warning_embed(
                        title="Trivia Ended",
                        description=f"Time's up! No one answered.\n\nThe correct answer was: **{correct_answer}**"
                    )
                    await ctx.send(embed=embed)
                else:
                    # Create results message
                    correct_players = [player for player, answer in session["players"].items() if answer == correct_index]
                    
                    if correct_players:
                        correct_mentions = ", ".join([f"{ctx.guild.get_member(player).mention}" for player in correct_players if ctx.guild.get_member(player)])
                        embed = EmbedHelper.success_embed(
                            title="Trivia Results",
                            description=f"The correct answer was: **{correct_answer}**\n\nCorrect players: {correct_mentions}",
                            fields=[{"name": "Question", "value": question}]
                        )
                    else:
                        embed = EmbedHelper.error_embed(
                            title="Trivia Results",
                            description=f"No one got it right!\n\nThe correct answer was: **{correct_answer}**",
                            fields=[{"name": "Question", "value": question}]
                        )
                    
                    await ctx.send(embed=embed)
                
        except Exception as e:
            if ctx.channel.id in self.trivia_sessions:
                del self.trivia_sessions[ctx.channel.id]
            
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"An error occurred during the trivia game: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not isinstance(message.channel, discord.TextChannel):
            return
            
        # Handle trivia answers
        if message.channel.id in self.trivia_sessions:
            session = self.trivia_sessions[message.channel.id]
            
            # Check if the message is an answer (a number from 1 to 4)
            if message.content.isdigit() and 1 <= int(message.content) <= len(session["answers"]):
                # Prevent multiple answers from the same player
                if message.author.id not in session["answered"]:
                    session["answered"].add(message.author.id)
                    session["players"][message.author.id] = int(message.content) - 1
                    await message.add_reaction("✅")
        
        # Handle hangman guesses
        if message.channel.id in self.hangman_games:
            game = self.hangman_games[message.channel.id]
            
            # Ensure this is not the game starter to prevent accidental guesses
            if message.author.id != game["starter_id"] and not message.author.bot:
                content = message.content.strip().lower()
                
                # Check if it's a single letter guess
                if len(content) == 1 and content.isalpha() and content not in game["guessed_letters"]:
                    await self.process_hangman_guess(message.channel, message.author, content)
                
                # Check if it's a word guess (same length as the answer)
                elif len(content) == len(game["word"]) and content.isalpha():
                    await self.process_hangman_word_guess(message.channel, message.author, content)
    
    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.channel)
    async def hangman(self, ctx):
        """Start a game of hangman"""
        if ctx.channel.id in self.hangman_games:
            embed = EmbedHelper.warning_embed(
                title="Game In Progress",
                description="There's already a hangman game running in this channel. Please wait for it to finish."
            )
            return await ctx.send(embed=embed)
        
        # Word lists for hangman
        word_lists = {
            "animals": ["elephant", "giraffe", "penguin", "dolphin", "koala", "tiger", "zebra", "kangaroo", "panda", "monkey"],
            "fruits": ["banana", "apple", "orange", "strawberry", "watermelon", "pineapple", "grape", "mango", "kiwi", "lemon"],
            "countries": ["canada", "japan", "brazil", "australia", "germany", "france", "egypt", "mexico", "italy", "sweden"],
            "professions": ["doctor", "teacher", "engineer", "chef", "artist", "pilot", "actor", "scientist", "athlete", "musician"],
            "video_games": ["minecraft", "fortnite", "zelda", "pokemon", "tetris", "mario", "skyrim", "overwatch", "minecraft", "doom"]
        }
        
        # Choose a random category and word
        category = random.choice(list(word_lists.keys()))
        word = random.choice(word_lists[category])
        
        # Initialize the game state
        self.hangman_games[ctx.channel.id] = {
            "word": word,
            "category": category,
            "guessed_letters": set(),
            "incorrect_guesses": 0,
            "max_incorrect": 6,
            "starter_id": ctx.author.id,
            "timestamp": datetime.utcnow()
        }
        
        # Create initial display
        display = self.get_hangman_display(ctx.channel.id)
        
        embed = EmbedHelper.create_embed(
            title="Hangman Game",
            description=f"Category: **{category.capitalize()}**\n\n{display}",
            color=0x00C09A,
            footer={"text": "Guess letters by typing them in the chat. You have 6 incorrect guesses before the game ends."}
        )
        
        await ctx.send(embed=embed)
        
        # Set a timeout for the game (2 minutes)
        await asyncio.sleep(120)
        
        # Check if the game is still running and hasn't been updated in 2 minutes
        if ctx.channel.id in self.hangman_games:
            game = self.hangman_games[ctx.channel.id]
            time_diff = (datetime.utcnow() - game["timestamp"]).total_seconds()
            
            if time_diff >= 115:  # If no activity in the last ~2 minutes
                # End the game due to inactivity
                embed = EmbedHelper.warning_embed(
                    title="Hangman Game Ended",
                    description=f"The game has ended due to inactivity.\n\nThe word was: **{game['word']}**"
                )
                await ctx.send(embed=embed)
                del self.hangman_games[ctx.channel.id]
    
    def get_hangman_display(self, channel_id):
        """Generate the hangman display for the current game state"""
        game = self.hangman_games[channel_id]
        word = game["word"]
        guessed = game["guessed_letters"]
        incorrect = game["incorrect_guesses"]
        
        # Hangman ASCII art stages
        hangman_stages = [
            "```\n  +---+\n  |   |\n      |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n      |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n  |   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|   |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n      |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n /    |\n      |\n=========```",
            "```\n  +---+\n  |   |\n  O   |\n /|\\  |\n / \\  |\n      |\n=========```"
        ]
        
        # Word display with correctly guessed letters
        word_display = " ".join([letter if letter.lower() in guessed else "_" for letter in word])
        
        # List of guessed letters
        guessed_letters = ", ".join(sorted(guessed)) if guessed else "None"
        
        # Combine all elements
        return f"{hangman_stages[incorrect]}\n\nWord: **{word_display}**\n\nGuessed Letters: {guessed_letters}\nIncorrect Guesses: {incorrect}/{game['max_incorrect']}"
    
    async def process_hangman_guess(self, channel, user, letter):
        """Process a letter guess in hangman"""
        game = self.hangman_games[channel.id]
        game["timestamp"] = datetime.utcnow()  # Update timestamp to prevent timeout
        
        # Add the letter to guessed letters
        game["guessed_letters"].add(letter)
        
        # Check if the letter is in the word
        if letter in game["word"].lower():
            # Check if the word is complete
            is_complete = True
            for char in game["word"]:
                if char.lower() not in game["guessed_letters"]:
                    is_complete = False
                    break
            
            if is_complete:
                await self.end_hangman_game(channel, True)
            else:
                # Update the display
                display = self.get_hangman_display(channel.id)
                
                embed = EmbedHelper.create_embed(
                    title="Hangman Game",
                    description=f"Category: **{game['category'].capitalize()}**\n\n{display}\n\n✅ {user.mention} guessed '{letter}' correctly!",
                    color=0x00C09A
                )
                
                await channel.send(embed=embed)
        else:
            # Incorrect guess
            game["incorrect_guesses"] += 1
            
            # Check if the game is over
            if game["incorrect_guesses"] >= game["max_incorrect"]:
                await self.end_hangman_game(channel, False)
            else:
                # Update the display
                display = self.get_hangman_display(channel.id)
                
                embed = EmbedHelper.create_embed(
                    title="Hangman Game",
                    description=f"Category: **{game['category'].capitalize()}**\n\n{display}\n\n❌ {user.mention} guessed '{letter}' incorrectly!",
                    color=0x00C09A
                )
                
                await channel.send(embed=embed)
    
    async def process_hangman_word_guess(self, channel, user, word_guess):
        """Process a word guess in hangman"""
        game = self.hangman_games[channel.id]
        game["timestamp"] = datetime.utcnow()  # Update timestamp to prevent timeout
        
        # Check if the guess is correct
        if word_guess.lower() == game["word"].lower():
            # Add all letters to guessed letters
            for letter in game["word"].lower():
                game["guessed_letters"].add(letter)
            
            await self.end_hangman_game(channel, True, user)
        else:
            # Incorrect word guess (counts as one incorrect letter guess)
            game["incorrect_guesses"] += 1
            
            # Check if the game is over
            if game["incorrect_guesses"] >= game["max_incorrect"]:
                await self.end_hangman_game(channel, False)
            else:
                # Update the display
                display = self.get_hangman_display(channel.id)
                
                embed = EmbedHelper.create_embed(
                    title="Hangman Game",
                    description=f"Category: **{game['category'].capitalize()}**\n\n{display}\n\n❌ {user.mention} guessed '{word_guess}' incorrectly!",
                    color=0x00C09A
                )
                
                await channel.send(embed=embed)
    
    async def end_hangman_game(self, channel, is_win, winner=None):
        """End a hangman game"""
        game = self.hangman_games[channel.id]
        word = game["word"]
        
        if is_win:
            embed = EmbedHelper.success_embed(
                title="Hangman Game Won!",
                description=f"🎉 {'You' if not winner else winner.mention} won! The word was: **{word}**\n\nThanks for playing!"
            )
        else:
            embed = EmbedHelper.error_embed(
                title="Hangman Game Over",
                description=f"Game over! You ran out of guesses.\n\nThe word was: **{word}**\n\nBetter luck next time!"
            )
        
        await channel.send(embed=embed)
        
        # Remove the game
        del self.hangman_games[channel.id]
    
    @commands.command()
    async def roll(self, ctx, dice="1d20"):
        """Roll dice (format: NdM = N dice with M sides each)"""
        try:
            # Parse the dice format
            parts = dice.lower().split("d")
            if len(parts) != 2:
                raise ValueError("Invalid dice format")
            
            num_dice = int(parts[0]) if parts[0] else 1
            num_sides = int(parts[1])
            
            # Validate the input
            if num_dice <= 0 or num_sides <= 0:
                raise ValueError("Dice count and sides must be positive")
            if num_dice > 100:
                raise ValueError("Cannot roll more than 100 dice at once")
            if num_sides > 1000:
                raise ValueError("Dice cannot have more than 1000 sides")
            
            # Roll the dice
            results = [random.randint(1, num_sides) for _ in range(num_dice)]
            total = sum(results)
            
            # Create the result message
            if num_dice == 1:
                description = f"You rolled a **{total}**"
            else:
                description = f"You rolled a total of **{total}**\n\nIndividual dice: {', '.join(map(str, results))}"
            
            embed = EmbedHelper.create_embed(
                title=f"Dice Roll: {dice}",
                description=description,
                color=0xE91E63,  # Pink
                thumbnail="https://i.imgur.com/SCoZd65.png"  # Dice image
            )
            
            await ctx.send(embed=embed)
        except ValueError as e:
            embed = EmbedHelper.error_embed(
                title="Invalid Dice Format",
                description=f"Error: {str(e)}\n\nUse the format: NdM (e.g., 1d20, 3d6)"
            )
            await ctx.send(embed=embed)
    
    @commands.command()
    async def coinflip(self, ctx):
        """Flip a coin"""
        result = random.choice(["Heads", "Tails"])
        
        embed = EmbedHelper.create_embed(
            title="Coin Flip",
            description=f"The coin landed on **{result}**!",
            color=0xFFD700,  # Gold
            thumbnail="https://i.imgur.com/SBHsPQU.png"  # Coin image
        )
        
        await ctx.send(embed=embed)
    
    @commands.command()
    async def choose(self, ctx, *, options=None):
        """Choose between multiple options (comma-separated)"""
        if not options:
            embed = EmbedHelper.error_embed(
                title="Missing Options",
                description="Please provide options to choose from, separated by commas."
            )
            return await ctx.send(embed=embed)
            
        # Split options and clean whitespace
        choices = [option.strip() for option in options.split(",") if option.strip()]
        
        if len(choices) < 2:
            embed = EmbedHelper.error_embed(
                title="Not Enough Options",
                description="Please provide at least two options separated by commas."
            )
            return await ctx.send(embed=embed)
            
        selected = random.choice(choices)
        
        embed = EmbedHelper.create_embed(
            title="I Choose...",
            description=f"🤔 Among {len(choices)} options, I choose: **{selected}**",
            color=0x9B59B6,  # Purple
            fields=[{"name": "All Options", "value": "\n".join([f"• {choice}" for choice in choices])}]
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Entertainment(bot)) 