import discord
from discord.ext import commands
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

class AvatarButtonView(discord.ui.View):
    def __init__(self, avatar_info, bot):
        super().__init__(timeout=None)  # Persistent view
        self.avatar_info = avatar_info
        self.bot = bot
    
    @discord.ui.button(
        label="⏼",
        style=discord.ButtonStyle.primary
    )
    async def get_avatar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Handle avatar download button click"""
        try:
            await interaction.response.defer(ephemeral=True)
            
            # Check if file exists
            if not os.path.exists(self.avatar_info['filepath']):
                await interaction.followup.send("❌ Avatar file not found. Please contact an administrator.", ephemeral=True)
                logger.error(f"Avatar file not found: {self.avatar_info['filepath']}")
                return
            
            # Try to send DM to user first
            user = interaction.user
            try:
                # Create embed for DM
                embed = discord.Embed(
                    title="Qren Avatar",
                    description="",
                    color=discord.Color.green()
                )
                
                # Send avatar file in DM
                file = discord.File(self.avatar_info['filepath'])
                embed.set_image(url=f"attachment://{self.avatar_info['filename']}")
                
                await user.send(embed=embed, file=file)
                
                # Send confirmation message in the same channel
                await interaction.followup.send(f"✅ تم ارسال الصورة في الخاص {user.mention}", ephemeral=False)
                logger.info(f"Avatar '{self.avatar_info['name']}' sent to {user} ({user.id})")
                
            except discord.Forbidden:
                # User has DMs disabled
                await interaction.followup.send(
                    f"❌ لا يمكن ارسال الصورة لـ {user.mention} لأن الرسائل الخاصة مغلقة",
                    ephemeral=False
                )
                logger.warning(f"Failed to DM {interaction.user} - DMs disabled")
                
            except discord.HTTPException as e:
                # Other Discord API errors
                await interaction.followup.send(
                    f"❌ فشل في ارسال الصورة لـ {user.mention}",
                    ephemeral=False
                )
                logger.error(f"Discord HTTP error sending avatar to {interaction.user}: {e}")
                
        except Exception as e:
            logger.error(f"Error in avatar button handler: {e}")
            try:
                if interaction.response.is_done():
                    await interaction.followup.send("❌ An unexpected error occurred. Please try again.", ephemeral=True)
                else:
                    await interaction.response.send_message("❌ An unexpected error occurred. Please try again.", ephemeral=True)
            except:
                pass  # Ignore if we can't send error message

class ConfirmDeleteView(discord.ui.View):
    def __init__(self, avatar_name: str, callback):
        super().__init__(timeout=30)
        self.avatar_name = avatar_name
        self.callback = callback
        self.result = None
    
    @discord.ui.button(label="✅ Confirm", style=discord.ButtonStyle.danger)
    async def confirm_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Confirm deletion"""
        self.result = True
        self.stop()
        await interaction.response.defer()
    
    @discord.ui.button(label="❌ Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Cancel deletion"""
        self.result = False
        self.stop()
        await interaction.response.send_message("❌ Deletion cancelled.", ephemeral=True)
    
    async def on_timeout(self):
        """Handle timeout"""
        self.result = False
        self.stop()
