import discord
from discord.ext import commands
import traceback
import sys
from utils.embed_helper import EmbedHelper

class ErrorHandler(commands.Cog):
    """Error handling for ModuBot"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Handle command errors"""
        # If the command has a local error handler, let it handle the error
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Get the original error if it's wrapped in a CommandInvokeError
        error = getattr(error, 'original', error)
        
        # Command not found errors are ignored
        if isinstance(error, commands.CommandNotFound):
            return
        
        # Handle different types of errors
        if isinstance(error, commands.MissingRequiredArgument):
            # Missing argument errors
            param = error.param.name
            embed = EmbedHelper.error_embed(
                title="Missing Argument",
                description=f"You're missing the `{param}` argument.\n\nUse `{ctx.prefix}help {ctx.command}` for more information."
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.BadArgument):
            # Bad argument errors
            embed = EmbedHelper.error_embed(
                title="Invalid Argument",
                description=f"You've provided an invalid argument.\n\nUse `{ctx.prefix}help {ctx.command}` for more information."
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.MissingPermissions):
            # Missing permissions errors
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms = ", ".join(missing_perms)
            embed = EmbedHelper.error_embed(
                title="Missing Permissions",
                description=f"You're missing the required permissions to run this command: **{perms}**"
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.BotMissingPermissions):
            # Bot missing permissions errors
            missing_perms = [perm.replace('_', ' ').title() for perm in error.missing_permissions]
            perms = ", ".join(missing_perms)
            embed = EmbedHelper.error_embed(
                title="Bot Missing Permissions",
                description=f"I'm missing the required permissions to run this command: **{perms}**"
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.NotOwner):
            # Not owner errors
            embed = EmbedHelper.error_embed(
                title="Owner Only",
                description="This command can only be used by the bot owner."
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.CommandOnCooldown):
            # Cooldown errors
            embed = EmbedHelper.error_embed(
                title="Command on Cooldown",
                description=f"This command is on cooldown. Try again in {error.retry_after:.1f} seconds."
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.DisabledCommand):
            # Disabled command errors
            embed = EmbedHelper.error_embed(
                title="Command Disabled",
                description="This command is currently disabled."
            )
            await ctx.send(embed=embed)
        
        elif isinstance(error, commands.NoPrivateMessage):
            # No private message errors
            embed = EmbedHelper.error_embed(
                title="Server Only",
                description="This command can only be used in a server, not in DMs."
            )
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException:
                pass
        
        elif isinstance(error, discord.Forbidden):
            # Forbidden errors (Discord API denied access)
            embed = EmbedHelper.error_embed(
                title="Permission Error",
                description="I don't have permission to execute this command."
            )
            try:
                await ctx.send(embed=embed)
            except discord.HTTPException:
                pass
        
        else:
            # Unexpected errors
            error_traceback = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
            self.bot.logger.error(f"Unhandled error in command {ctx.command}: {error_traceback}")
            
            embed = EmbedHelper.error_embed(
                title="Unexpected Error",
                description="An unexpected error occurred. The bot developer has been notified."
            )
            await ctx.send(embed=embed)
            
            # Print error to console for debugging
            print(f'Ignoring exception in command {ctx.command}:', file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot)) 