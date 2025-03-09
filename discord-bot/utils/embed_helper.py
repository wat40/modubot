import discord
from datetime import datetime

class EmbedHelper:
    @staticmethod
    def create_embed(title=None, description=None, color=0x5865F2, footer=None, thumbnail=None, image=None, author=None, fields=None, timestamp=True):
        """
        Creates a Discord embed with the specified parameters.
        
        Args:
            title (str, optional): The title of the embed.
            description (str, optional): The description of the embed.
            color (int, optional): The color of the embed. Defaults to Discord Blurple.
            footer (dict, optional): A dictionary containing 'text' and optionally 'icon_url'.
            thumbnail (str, optional): URL of the thumbnail.
            image (str, optional): URL of the image.
            author (dict, optional): A dictionary containing 'name' and optionally 'icon_url' and 'url'.
            fields (list, optional): A list of dictionaries containing 'name', 'value', and optionally 'inline'.
            timestamp (bool, optional): Whether to add the current timestamp. Defaults to True.
            
        Returns:
            discord.Embed: The created embed.
        """
        embed = discord.Embed(title=title, description=description, color=color)
        
        if timestamp:
            embed.timestamp = datetime.utcnow()
        
        if footer:
            embed.set_footer(text=footer.get('text', ''), icon_url=footer.get('icon_url', None))
        
        if thumbnail:
            embed.set_thumbnail(url=thumbnail)
        
        if image:
            embed.set_image(url=image)
        
        if author:
            embed.set_author(
                name=author.get('name', ''),
                icon_url=author.get('icon_url', None),
                url=author.get('url', None)
            )
        
        if fields:
            for field in fields:
                embed.add_field(
                    name=field.get('name', ''),
                    value=field.get('value', ''),
                    inline=field.get('inline', False)
                )
        
        return embed
    
    @staticmethod
    def success_embed(title="Success", description=None, **kwargs):
        """Creates a success embed with green color."""
        return EmbedHelper.create_embed(title=title, description=description, color=0x57F287, **kwargs)
    
    @staticmethod
    def error_embed(title="Error", description=None, **kwargs):
        """Creates an error embed with red color."""
        return EmbedHelper.create_embed(title=title, description=description, color=0xED4245, **kwargs)
    
    @staticmethod
    def warning_embed(title="Warning", description=None, **kwargs):
        """Creates a warning embed with yellow color."""
        return EmbedHelper.create_embed(title=title, description=description, color=0xFEE75C, **kwargs)
    
    @staticmethod
    def info_embed(title="Information", description=None, **kwargs):
        """Creates an info embed with blue color."""
        return EmbedHelper.create_embed(title=title, description=description, color=0x5865F2, **kwargs)
    
    @staticmethod
    def help_command_embed(command_name, description, usage, examples, **kwargs):
        """Creates a help embed for a specific command."""
        embed = EmbedHelper.create_embed(
            title=f"Command: {command_name}",
            description=description,
            color=0x5865F2,
            **kwargs
        )
        
        embed.add_field(name="Usage", value=f"```{usage}```", inline=False)
        embed.add_field(name="Examples", value=examples, inline=False)
        
        return embed
    
    @staticmethod
    def moderation_log_embed(action, target, moderator, reason=None, duration=None, **kwargs):
        """Creates a moderation log embed."""
        description = f"**Target:** {target.mention} ({target.id})\n**Moderator:** {moderator.mention}"
        
        if reason:
            description += f"\n**Reason:** {reason}"
        
        if duration:
            description += f"\n**Duration:** {duration}"
        
        return EmbedHelper.create_embed(
            title=f"Moderation Action: {action}",
            description=description,
            color=0xED4245,
            **kwargs
        ) 