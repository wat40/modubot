import discord
from discord import app_commands
from typing import Dict, List, Union, Any, Optional, Callable, TypeVar
import inspect
from functools import wraps
import logging

logger = logging.getLogger("modubot")

T = TypeVar('T')

class SlashHelper:
    """Helper class for creating and managing slash commands."""
    
    @staticmethod
    def group(name: str, description: str) -> app_commands.Group:
        """Create a slash command group."""
        return app_commands.Group(name=name, description=description)
    
    @staticmethod
    def command(
        name: str = None, 
        description: str = None,
        nsfw: bool = False
    ) -> Callable[[T], T]:
        """
        Decorator for creating slash commands with error handling.
        This provides consistent error handling across all slash commands.
        """
        def decorator(func: T) -> T:
            # Get the command name and description from the function if not provided
            cmd_name = name or func.__name__
            cmd_desc = description or (func.__doc__ or "No description provided.")
            
            # Apply the app_commands.command decorator
            app_command = app_commands.command(
                name=cmd_name,
                description=cmd_desc,
                nsfw=nsfw
            )(func)
            
            @wraps(app_command.callback)
            async def wrapper(self, interaction: discord.Interaction, *args, **kwargs):
                try:
                    await app_command.callback(self, interaction, *args, **kwargs)
                except app_commands.errors.CommandInvokeError as e:
                    # Log the original error
                    original = getattr(e, 'original', e)
                    logger.error(f"Error in slash command {cmd_name}: {str(original)}")
                    
                    # Reply with a user-friendly error message
                    await SlashHelper.error(
                        interaction, 
                        title="Command Error",
                        description=f"An error occurred while executing the command: {str(original)}",
                        ephemeral=True
                    )
                except Exception as e:
                    # Handle other exceptions
                    logger.error(f"Unexpected error in slash command {cmd_name}: {str(e)}")
                    await SlashHelper.error(
                        interaction, 
                        title="Unexpected Error",
                        description="An unexpected error occurred. Please try again later.",
                        ephemeral=True
                    )
            
            # Replace the callback with our wrapper
            app_command.callback = wrapper
            return app_command
        
        return decorator
    
    @staticmethod
    async def response(
        interaction: discord.Interaction,
        content: str = None,
        embeds: List[discord.Embed] = None,
        view: discord.ui.View = None,
        file: discord.File = None,
        files: List[discord.File] = None,
        ephemeral: bool = False,
        delete_after: float = None
    ) -> Optional[discord.WebhookMessage]:
        """
        Respond to an interaction with consistent formatting.
        
        Args:
            interaction: The interaction to respond to
            content: Text content of the response
            embeds: List of embeds to include
            view: View component to include
            file: Single file to attach
            files: List of files to attach
            ephemeral: Whether the response should be ephemeral
            delete_after: Delete the response after this many seconds
            
        Returns:
            The webhook message if successful, None otherwise
        """
        try:
            if interaction.response.is_done():
                # If already responded, use followup
                followup = await interaction.followup.send(
                    content=content,
                    embeds=embeds,
                    view=view,
                    file=file,
                    files=files,
                    ephemeral=ephemeral,
                    wait=True
                )
                
                if delete_after:
                    await followup.delete(delay=delete_after)
                
                return followup
            else:
                # Initial response
                await interaction.response.send_message(
                    content=content,
                    embeds=embeds,
                    view=view,
                    file=file,
                    files=files,
                    ephemeral=ephemeral
                )
                
                if delete_after:
                    msg = await interaction.original_response()
                    await msg.delete(delay=delete_after)
                
                return await interaction.original_response()
        except Exception as e:
            logger.error(f"Error sending interaction response: {str(e)}")
            return None
    
    @staticmethod
    async def success(
        interaction: discord.Interaction,
        title: str = "Success",
        description: str = None,
        **kwargs
    ) -> Optional[discord.WebhookMessage]:
        """Send a success response with a green embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.green()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        return await SlashHelper.response(interaction, embeds=[embed], **kwargs)
    
    @staticmethod
    async def error(
        interaction: discord.Interaction,
        title: str = "Error",
        description: str = None,
        **kwargs
    ) -> Optional[discord.WebhookMessage]:
        """Send an error response with a red embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.red()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        return await SlashHelper.response(interaction, embeds=[embed], **kwargs)
    
    @staticmethod
    async def info(
        interaction: discord.Interaction,
        title: str = "Information",
        description: str = None,
        **kwargs
    ) -> Optional[discord.WebhookMessage]:
        """Send an informational response with a blue embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        return await SlashHelper.response(interaction, embeds=[embed], **kwargs)
    
    @staticmethod
    async def warning(
        interaction: discord.Interaction,
        title: str = "Warning",
        description: str = None,
        **kwargs
    ) -> Optional[discord.WebhookMessage]:
        """Send a warning response with a yellow embed."""
        embed = discord.Embed(
            title=title,
            description=description,
            color=discord.Color.yellow()
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}")
        
        return await SlashHelper.response(interaction, embeds=[embed], **kwargs)
        
    @staticmethod
    def get_command_signature(command: app_commands.Command) -> str:
        """Get the signature of a slash command for help displays."""
        params = []
        
        for param in command._params.values():
            if param.required:
                params.append(f"<{param.name}>")
            else:
                params.append(f"[{param.name}]")
        
        return f"/{command.qualified_name} {' '.join(params)}".strip()
        
    @staticmethod
    def format_command_help(command: app_commands.Command) -> discord.Embed:
        """Format a command's help information into an embed."""
        embed = discord.Embed(
            title=f"Command: /{command.qualified_name}",
            description=command.description,
            color=discord.Color.blue()
        )
        
        # Add command signature
        embed.add_field(
            name="Usage",
            value=f"`{SlashHelper.get_command_signature(command)}`",
            inline=False
        )
        
        # Add parameters
        if command._params:
            params_text = ""
            for param in command._params.values():
                required = "Required" if param.required else "Optional"
                params_text += f"`{param.name}` ({required}): {param.description or 'No description'}\n"
            
            embed.add_field(
                name="Parameters",
                value=params_text,
                inline=False
            )
        
        return embed 