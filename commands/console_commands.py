import discord
from discord.ext import commands
from discord import app_commands
import logging
import subprocess
import os

logger = logging.getLogger(__name__)

class ConsoleCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    def is_admin(self, user):
        """Check if user has admin permissions"""
        if isinstance(user, discord.Member):
            return user.guild_permissions.administrator
        return False
    
    @app_commands.command(name="status", description="فحص حالة السيرفر")
    async def server_status(self, interaction: discord.Interaction):
        """Check server status"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط!", ephemeral=True)
                return
            
            # Get basic system info
            embed = discord.Embed(
                title="🖥️ حالة السيرفر",
                color=discord.Color.green()
            )
            
            # Add server info
            embed.add_field(name="📊 المعلومات", value=f"السيرفر: {interaction.guild.name}\nالأعضاء: {interaction.guild.member_count}", inline=False)
            embed.add_field(name="🤖 البوت", value="متصل وجاهز", inline=False)
            
            await interaction.response.send_message(embed=embed)
            logger.info(f"Server status checked by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error checking server status: {e}")
            await interaction.response.send_message("❌ حدث خطأ في فحص الحالة", ephemeral=True)
    
    @app_commands.command(name="ping", description="فحص سرعة الاستجابة")
    async def ping(self, interaction: discord.Interaction):
        """Check bot latency"""
        try:
            latency = round(self.bot.latency * 1000)
            embed = discord.Embed(
                title="🏓 سرعة الاستجابة",
                description=f"⏱️ الزمن: {latency}ms",
                color=discord.Color.blue()
            )
            await interaction.response.send_message(embed=embed)
            logger.info(f"Ping command used by {interaction.user} - Latency: {latency}ms")
            
        except Exception as e:
            logger.error(f"Error in ping command: {e}")
            await interaction.response.send_message("❌ حدث خطأ في فحص السرعة", ephemeral=True)
    
    @app_commands.command(name="logs", description="عرض آخر سجلات النظام")
    async def show_logs(self, interaction: discord.Interaction):
        """Show recent system logs"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط!", ephemeral=True)
                return
            
            # Read last few lines from log file
            try:
                with open('bot.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_logs = ''.join(lines[-10:])  # Last 10 lines
                
                if len(recent_logs) > 1900:  # Discord limit
                    recent_logs = recent_logs[-1900:]
                
                embed = discord.Embed(
                    title="📋 آخر السجلات",
                    description=f"```\n{recent_logs}\n```",
                    color=discord.Color.orange()
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            except FileNotFoundError:
                await interaction.response.send_message("❌ لم يتم العثور على ملف السجلات", ephemeral=True)
            
            logger.info(f"Logs requested by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error showing logs: {e}")
            await interaction.response.send_message("❌ حدث خطأ في عرض السجلات", ephemeral=True)

async def setup(bot):
    await bot.add_cog(ConsoleCommands(bot))