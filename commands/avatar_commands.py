import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import aiofiles
import asyncio
from utils.button_views import AvatarButtonView
from utils.avatar_manager import AvatarManager
from config import BOT_CONFIG

logger = logging.getLogger(__name__)

class AvatarCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.avatar_manager = AvatarManager()
    
    def is_admin(self, user):
        """Check if user has admin permissions"""
        if isinstance(user, discord.Member):
            return user.guild_permissions.administrator
        return False
    
    @app_commands.command(name="upload_avatar", description="Upload a new avatar image (Admin only)")
    @app_commands.describe(
        image="The avatar image to upload",
        name="Name for this avatar (optional)"
    )
    async def upload_avatar(self, interaction: discord.Interaction, image: discord.Attachment, name: str = ""):
        """Upload a new avatar image"""
        try:
            # Check permissions
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ Only administrators can upload avatars!", ephemeral=True)
                return
            
            # Validate file type
            if not image.content_type or not image.content_type.startswith('image/'):
                await interaction.response.send_message("❌ Please upload a valid image file!", ephemeral=True)
                return
            
            # Check file size (10MB limit)
            if image.size > 10 * 1024 * 1024:
                await interaction.response.send_message("❌ Image file is too large! Maximum size is 10MB.", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # Generate filename
            if not name or name == "":
                name = image.filename.split('.')[0]
            
            # Clean the name to remove invalid characters for filenames
            import re
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', name)  # Replace invalid chars with underscore
            clean_name = re.sub(r'https?_+', '', clean_name)  # Remove http/https prefixes
            clean_name = clean_name.strip('_')  # Remove leading/trailing underscores
            
            # If clean_name is empty after cleaning, use default
            if not clean_name:
                clean_name = f"avatar_{image.id}"
            
            filename = f"{clean_name}_{image.id}.{image.filename.split('.')[-1]}"
            filepath = os.path.join("avatars", filename)
            
            # Download and save the image
            data = await image.read()
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(data)
            
            # Add to avatar manager
            avatar_info = {
                'name': name,  # Keep original name for display
                'clean_name': clean_name,  # Store cleaned name for reference
                'filename': filename,
                'filepath': filepath,
                'uploader': interaction.user.id,
                'upload_time': discord.utils.utcnow().isoformat()
            }
            
            self.avatar_manager.add_avatar(avatar_info)
            
            await interaction.followup.send(f"✅ Avatar '{name}' uploaded successfully!")
            logger.info(f"Avatar '{name}' uploaded by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error uploading avatar: {e}")
            if interaction.response.is_done():
                await interaction.followup.send("❌ Failed to upload avatar. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to upload avatar. Please try again.", ephemeral=True)
    
    @app_commands.command(name="post_avatar", description="Post an avatar with download button (Admin only)")
    @app_commands.describe(avatar_name="Name of the avatar to post")
    async def post_avatar(self, interaction: discord.Interaction, avatar_name: str):
        """Post an avatar with interactive button"""
        try:
            # Check permissions
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ Only administrators can post avatars!", ephemeral=True)
                return
            
            # Get avatar info
            avatar_info = self.avatar_manager.get_avatar(avatar_name)
            if not avatar_info:
                await interaction.response.send_message(f"❌ Avatar '{avatar_name}' not found!", ephemeral=True)
                return
            
            # Check if file exists
            if not os.path.exists(avatar_info['filepath']):
                await interaction.response.send_message(f"❌ Avatar file not found: {avatar_info['filepath']}", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            # Create embed
            embed = discord.Embed(
                title="Qren Avatar",
                description="",
                color=discord.Color.blue()
            )
            
            # Add image to embed
            file = discord.File(avatar_info['filepath'])
            embed.set_image(url=f"attachment://{avatar_info['filename']}")
            # Remove footer text
            
            # Create button view
            view = AvatarButtonView(avatar_info, self.bot)
            
            await interaction.followup.send(embed=embed, file=file, view=view)
            logger.info(f"Avatar '{avatar_name}' posted by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error posting avatar: {e}")
            if interaction.response.is_done():
                await interaction.followup.send("❌ Failed to post avatar. Please try again.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Failed to post avatar. Please try again.", ephemeral=True)
    
    @app_commands.command(name="list_avatars", description="List all available avatars (Admin only)")
    async def list_avatars(self, interaction: discord.Interaction):
        """List all available avatars"""
        try:
            # Check permissions
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ Only administrators can view the avatar list!", ephemeral=True)
                return
            
            avatars = self.avatar_manager.list_avatars()
            
            if not avatars:
                await interaction.response.send_message("📭 No avatars uploaded yet!", ephemeral=True)
                return
            
            # Create embed with avatar list
            embed = discord.Embed(
                title="📂 Available Avatars",
                description=f"Total: {len(avatars)} avatars",
                color=discord.Color.green()
            )
            
            for i, avatar in enumerate(avatars[:25], 1):  # Limit to 25 to avoid embed limits
                embed.add_field(
                    name=f"{i}. {avatar['name']}",
                    value=f"File: `{avatar['filename']}`",
                    inline=False
                )
            
            if len(avatars) > 25:
                embed.set_footer(text=f"Showing first 25 of {len(avatars)} avatars")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing avatars: {e}")
            await interaction.response.send_message("❌ Failed to list avatars. Please try again.", ephemeral=True)
    
    @app_commands.command(name="delete_avatar", description="Delete an avatar (Admin only)")
    @app_commands.describe(avatar_name="Name of the avatar to delete")
    async def delete_avatar(self, interaction: discord.Interaction, avatar_name: str):
        """Delete an avatar"""
        try:
            # Check permissions
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ Only administrators can delete avatars!", ephemeral=True)
                return
            
            # Get avatar info
            avatar_info = self.avatar_manager.get_avatar(avatar_name)
            if not avatar_info:
                await interaction.response.send_message(f"❌ Avatar '{avatar_name}' not found!", ephemeral=True)
                return
            
            # Delete file if it exists
            if os.path.exists(avatar_info['filepath']):
                os.remove(avatar_info['filepath'])
            
            # Remove from manager
            self.avatar_manager.remove_avatar(avatar_name)
            
            await interaction.response.send_message(f"✅ Avatar '{avatar_name}' deleted successfully!", ephemeral=True)
            logger.info(f"Avatar '{avatar_name}' deleted by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error deleting avatar: {e}")
            await interaction.response.send_message("❌ Failed to delete avatar. Please try again.", ephemeral=True)
    
    @post_avatar.autocomplete('avatar_name')
    @delete_avatar.autocomplete('avatar_name')
    async def avatar_name_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for avatar names"""
        try:
            avatars = self.avatar_manager.list_avatars()
            choices = [
                app_commands.Choice(name=avatar['name'], value=avatar['name'])
                for avatar in avatars
                if current.lower() in avatar['name'].lower()
            ][:25]  # Discord limits to 25 choices
            return choices
        except Exception as e:
            logger.error(f"Error in autocomplete: {e}")
            return []
