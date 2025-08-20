import discord
from discord.ext import commands
import logging
import os
import asyncio
import json
from datetime import datetime
from commands.unified_commands import (
    AvatarCommands, 
    ControlCommands, 
    ConsoleCommands, 
    PublishingCommands, 
    TagSearchCommands
)
from utils.avatar_manager import AvatarManager
# Load configuration
BOT_CONFIG = {
    'prefix': '!',
    'description': 'Qren Unified Discord Bot'
}

logger = logging.getLogger(__name__)

class UnifiedQrenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        intents.members = True
        
        super().__init__(
            command_prefix=BOT_CONFIG['prefix'],
            intents=intents,
            help_command=None
        )
        
        # Initialize managers and data
        self.avatar_manager = AvatarManager()
        self.tags_db_path = "tags_data.json"
        self.tags_data = self.load_tags_data()
        
    def load_tags_data(self):
        """Load tags data from JSON file"""
        try:
            if os.path.exists(self.tags_db_path):
                with open(self.tags_db_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {}
        except Exception as e:
            logger.error(f"Error loading tags data: {e}")
            return {}
    
    def save_tags_data(self):
        """Save tags data to JSON file"""
        try:
            with open(self.tags_db_path, 'w', encoding='utf-8') as f:
                json.dump(self.tags_data, f, ensure_ascii=False, indent=2)
            logger.info("Tags data saved successfully")
        except Exception as e:
            logger.error(f"Error saving tags data: {e}")
        
    async def setup_hook(self):
        """Called when the bot is starting up"""
        try:
            # Load all command modules
            await self.add_cog(AvatarCommands(self))
            await self.add_cog(ControlCommands(self))
            await self.add_cog(ConsoleCommands(self))
            await self.add_cog(PublishingCommands(self))
            await self.add_cog(TagSearchCommands(self))
            
            logger.info("All commands loaded successfully")
            
            # Sync slash commands
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s)")
            
        except Exception as e:
            logger.error(f"Error in setup_hook: {e}")
    
    async def on_ready(self):
        """Called when the bot is ready"""
        logger.info(f'{self.user} has connected to Discord!')
        logger.info(f'Unified Qren Bot is in {len(self.guilds)} guilds')
        
        # Set bot status
        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="Qren System 🌟"
        )
        await self.change_presence(status=discord.Status.online, activity=activity)
    
    async def on_command_error(self, ctx, error):
        """Global error handler"""
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("❌ ليس لديك الصلاحيات المطلوبة لاستخدام هذا الأمر")
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(f"⏰ الأمر في فترة انتظار. حاول مرة أخرى خلال {error.retry_after:.2f} ثانية.")
        else:
            logger.error(f"Unhandled error in {ctx.command}: {error}")
            await ctx.send("❌ حدث خطأ غير متوقع. الرجاء المحاولة لاحقاً.")
    
    async def on_application_command_error(self, interaction, error):
        """Global slash command error handler"""
        try:
            if isinstance(error, discord.app_commands.MissingPermissions):
                await interaction.response.send_message("❌ ليس لديك صلاحية لاستخدام هذا الأمر!", ephemeral=True)
            elif isinstance(error, discord.app_commands.CommandOnCooldown):
                await interaction.response.send_message(f"⏰ الأمر في فترة انتظار. حاول مرة أخرى خلال {error.retry_after:.2f} ثانية.", ephemeral=True)
            else:
                logger.error(f"Unhandled slash command error: {error}")
                message = "❌ حدث خطأ غير متوقع. الرجاء المحاولة لاحقاً."
                
                if interaction.response.is_done():
                    await interaction.followup.send(message, ephemeral=True)
                else:
                    await interaction.response.send_message(message, ephemeral=True)
        except Exception as e:
            logger.error(f"Error in error handler: {e}")