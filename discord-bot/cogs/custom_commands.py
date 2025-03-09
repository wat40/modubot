import discord
from discord.ext import commands
from utils.embed_helper import EmbedHelper
from utils.database import Database

class CustomCommands(commands.Cog):
    """Create and manage custom commands for your server"""
    
    def __init__(self, bot):
        self.bot = bot
        self.db = Database()
        self.cache = {}  # Format: {guild_id: {command_name: {"response": response, "id": id}}}
    
    async def cog_load(self):
        """Load custom commands into cache when the cog is loaded"""
        for guild in self.bot.guilds:
            await self.load_guild_commands(guild.id)
    
    async def load_guild_commands(self, guild_id):
        """Load all custom commands for a guild into the cache"""
        try:
            response = await self.db.get_custom_commands(guild_id)
            commands = response.data if hasattr(response, 'data') else []
            
            self.cache[guild_id] = {}
            for command in commands:
                self.cache[guild_id][command['command_name'].lower()] = {
                    "response": command['response'],
                    "id": command['id']
                }
        except Exception as e:
            self.bot.logger.error(f"Error loading custom commands for guild {guild_id}: {e}")
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        """Load custom commands when the bot joins a new guild"""
        await self.load_guild_commands(guild.id)
    
    @commands.Cog.listener()
    async def on_message(self, message):
        """Listen for custom commands in messages"""
        if message.author.bot or not isinstance(message.channel, discord.TextChannel):
            return
        
        if not message.content:
            return
        
        # Get the prefix for this guild
        guild_settings = await self.db.get_guild_settings(message.guild.id)
        prefix = guild_settings.get('prefix', '!')
        
        # Check if the message starts with the prefix
        if not message.content.startswith(prefix):
            return
        
        # Get the command name from the message
        command_name = message.content[len(prefix):].split()[0].lower()
        
        # Check if this is a custom command
        if message.guild.id in self.cache and command_name in self.cache[message.guild.id]:
            command_data = self.cache[message.guild.id][command_name]
            response_text = command_data["response"]
            
            # Increment the usage counter
            await self.db.increment_command_uses(command_data["id"])
            
            # Process placeholders in the response
            response_text = response_text.replace("{user}", message.author.mention)
            response_text = response_text.replace("{server}", message.guild.name)
            response_text = response_text.replace("{channel}", message.channel.mention)
            
            # If the response starts with "embed:", create an embed
            if response_text.lower().startswith("embed:"):
                try:
                    content = response_text[6:].strip()
                    title, description = content.split('|', 1) if '|' in content else (None, content)
                    
                    embed = EmbedHelper.create_embed(
                        title=title.strip() if title else None,
                        description=description.strip(),
                        color=0x5865F2
                    )
                    await message.channel.send(embed=embed)
                except Exception as e:
                    await message.channel.send(f"Error processing command response: {str(e)}")
            else:
                await message.channel.send(response_text)
    
    @commands.group(aliases=["cc"], invoke_without_command=True)
    async def customcommand(self, ctx):
        """Manage custom commands"""
        embed = EmbedHelper.info_embed(
            title="Custom Commands",
            description=f"Use `{ctx.prefix}cc add <name> <response>` to create a custom command.\n"
                       f"Use `{ctx.prefix}cc remove <name>` to remove a custom command.\n"
                       f"Use `{ctx.prefix}cc list` to see all custom commands.\n"
                       f"Use `{ctx.prefix}cc info <name>` to see information about a command."
        )
        await ctx.send(embed=embed)
    
    @customcommand.command(name="add")
    @commands.has_permissions(manage_guild=True)
    async def cc_add(self, ctx, name: str, *, response: str):
        """Add a custom command"""
        # Check if command name is valid
        if not name or len(name) > 20:
            embed = EmbedHelper.error_embed(
                title="Invalid Name",
                description="Command name must be between 1 and 20 characters."
            )
            return await ctx.send(embed=embed)
        
        # Check if the command response is valid
        if not response or len(response) > 2000:
            embed = EmbedHelper.error_embed(
                title="Invalid Response",
                description="Command response must be between 1 and 2000 characters."
            )
            return await ctx.send(embed=embed)
        
        # Check if the command already exists
        existing_cmd = await self.db.get_custom_command(ctx.guild.id, name)
        if existing_cmd.data and existing_cmd.data:
            embed = EmbedHelper.error_embed(
                title="Command Exists",
                description=f"A command named `{name}` already exists. Use `{ctx.prefix}cc edit {name} <new response>` to edit it."
            )
            return await ctx.send(embed=embed)
        
        # Add the command to the database
        try:
            result = await self.db.add_custom_command(ctx.guild.id, name, response, ctx.author.id)
            
            # Add to cache
            if ctx.guild.id not in self.cache:
                self.cache[ctx.guild.id] = {}
            
            command_id = result.data[0]['id'] if hasattr(result, 'data') and result.data else None
            self.cache[ctx.guild.id][name.lower()] = {
                "response": response,
                "id": command_id
            }
            
            embed = EmbedHelper.success_embed(
                title="Command Added",
                description=f"Added custom command `{name}`.\n\nUse it with `{ctx.prefix}{name}`."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"Failed to add command: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @customcommand.command(name="remove", aliases=["delete"])
    @commands.has_permissions(manage_guild=True)
    async def cc_remove(self, ctx, name: str):
        """Remove a custom command"""
        # Check if the command exists
        existing_cmd = await self.db.get_custom_command(ctx.guild.id, name)
        if not existing_cmd.data or not existing_cmd.data:
            embed = EmbedHelper.error_embed(
                title="Command Not Found",
                description=f"No custom command named `{name}` exists."
            )
            return await ctx.send(embed=embed)
        
        # Remove the command from the database
        try:
            command_id = existing_cmd.data[0]['id']
            await self.db.supabase.table('custom_commands').delete().eq('id', command_id).execute()
            
            # Remove from cache
            if ctx.guild.id in self.cache and name.lower() in self.cache[ctx.guild.id]:
                del self.cache[ctx.guild.id][name.lower()]
            
            embed = EmbedHelper.success_embed(
                title="Command Removed",
                description=f"Removed custom command `{name}`."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"Failed to remove command: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @customcommand.command(name="edit")
    @commands.has_permissions(manage_guild=True)
    async def cc_edit(self, ctx, name: str, *, response: str):
        """Edit a custom command"""
        # Check if the command exists
        existing_cmd = await self.db.get_custom_command(ctx.guild.id, name)
        if not existing_cmd.data or not existing_cmd.data:
            embed = EmbedHelper.error_embed(
                title="Command Not Found",
                description=f"No custom command named `{name}` exists."
            )
            return await ctx.send(embed=embed)
        
        # Check if the response is valid
        if not response or len(response) > 2000:
            embed = EmbedHelper.error_embed(
                title="Invalid Response",
                description="Command response must be between 1 and 2000 characters."
            )
            return await ctx.send(embed=embed)
        
        # Update the command in the database
        try:
            command_id = existing_cmd.data[0]['id']
            await self.db.supabase.table('custom_commands').update({'response': response}).eq('id', command_id).execute()
            
            # Update cache
            if ctx.guild.id in self.cache and name.lower() in self.cache[ctx.guild.id]:
                self.cache[ctx.guild.id][name.lower()]["response"] = response
            
            embed = EmbedHelper.success_embed(
                title="Command Updated",
                description=f"Updated custom command `{name}`."
            )
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"Failed to update command: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @customcommand.command(name="list")
    async def cc_list(self, ctx):
        """List all custom commands for this server"""
        try:
            response = await self.db.get_custom_commands(ctx.guild.id)
            commands = response.data if hasattr(response, 'data') else []
            
            if not commands:
                embed = EmbedHelper.info_embed(
                    title="Custom Commands",
                    description=f"This server has no custom commands.\n\nUse `{ctx.prefix}cc add <name> <response>` to create one."
                )
                return await ctx.send(embed=embed)
            
            # Sort commands by name
            commands.sort(key=lambda x: x['command_name'])
            
            # Create the embed
            embed = EmbedHelper.create_embed(
                title=f"Custom Commands for {ctx.guild.name}",
                description=f"This server has {len(commands)} custom commands.\n\nUse `{ctx.prefix}<command>` to use a command.",
                color=0x5865F2
            )
            
            # Add commands to the embed (group them if there are many)
            if len(commands) > 15:
                # Group commands in fields of 15 each
                for i in range(0, len(commands), 15):
                    group = commands[i:i+15]
                    field_value = ", ".join([f"`{cmd['command_name']}`" for cmd in group])
                    embed.add_field(name=f"Commands {i+1}-{i+len(group)}", value=field_value, inline=False)
            else:
                # List all commands in one field
                command_list = ", ".join([f"`{cmd['command_name']}`" for cmd in commands])
                embed.add_field(name="Commands", value=command_list, inline=False)
            
            await ctx.send(embed=embed)
        except Exception as e:
            embed = EmbedHelper.error_embed(
                title="Error",
                description=f"Failed to list commands: {str(e)}"
            )
            await ctx.send(embed=embed)
    
    @customcommand.command(name="info")
    async def cc_info(self, ctx, name: str):
        """Get information about a custom command"""
        # Check if the command exists
        existing_cmd = await self.db.get_custom_command(ctx.guild.id, name)
        if not existing_cmd.data or not existing_cmd.data:
            embed = EmbedHelper.error_embed(
                title="Command Not Found",
                description=f"No custom command named `{name}` exists."
            )
            return await ctx.send(embed=embed)
        
        command = existing_cmd.data[0]
        
        # Try to get the creator's name
        creator_id = int(command['created_by'])
        creator = ctx.guild.get_member(creator_id)
        creator_name = creator.display_name if creator else f"Unknown User ({creator_id})"
        
        # Create response preview (shortened if needed)
        response = command['response']
        if len(response) > 512:
            response = response[:509] + "..."
        
        # Create the embed
        embed = EmbedHelper.create_embed(
            title=f"Command: {command['command_name']}",
            description=f"**Usage:** `{ctx.prefix}{command['command_name']}`",
            color=0x5865F2,
            fields=[
                {"name": "Response", "value": f"```\n{response}\n```", "inline": False},
                {"name": "Created By", "value": creator_name, "inline": True},
                {"name": "Uses", "value": str(command['uses']), "inline": True},
                {"name": "Created At", "value": command['created_at'].split('T')[0] if 'T' in str(command['created_at']) else str(command['created_at']), "inline": True}
            ]
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(CustomCommands(bot)) 