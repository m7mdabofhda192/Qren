import discord
from discord.ext import commands
from discord import app_commands
import logging
import json
import os
from datetime import datetime
from utils.control_panel_views import ControlPanelView

logger = logging.getLogger(__name__)

class ControlCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.control_data_file = "control_panel_data.json"
        self.load_control_data()
    
    def load_control_data(self):
        """Load control panel data from JSON file"""
        try:
            if os.path.exists(self.control_data_file):
                with open(self.control_data_file, 'r', encoding='utf-8') as f:
                    self.control_data = json.load(f)
            else:
                self.control_data = {}
        except Exception as e:
            logger.error(f"Error loading control data: {e}")
            self.control_data = {}
    
    def save_control_data(self):
        """Save control panel data to JSON file"""
        try:
            with open(self.control_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.control_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving control data: {e}")
    
    def is_admin(self, user):
        """Check if user has admin permissions"""
        if isinstance(user, discord.Member):
            return user.guild_permissions.administrator
        return False

    @app_commands.command(name="setup_control_panel", description="إعداد لوحة التحكم الرئيسية")
    @app_commands.describe(channel="القناة التي ستحتوي على لوحة التحكم")
    async def setup_control_panel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Setup the main control panel"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            # Create simple control panel embed
            embed = discord.Embed(
                title="Control Panel",
                description="اختر من القائمة أدناه لتنفيذ أحد الخيارات\n\nلأخذ أفتار شخص معين\n**Avatar**\n\nلأخذ بنر شخص معين\n**Banner**\n\nللتحميل مقطع\n**Download**\n\nلمعرفة حالة تطوير إشارة البوست الخاصة بك\n**Boost**\n\nلمعرفة حالة تطوير إشارة النيترو الخاصة بك\n**Nitro**",
                color=0x0099ff
            )
            
            # Add server icon as thumbnail if available
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            # Create the control panel view
            view = ControlPanelView()
            
            # Send the control panel
            message = await channel.send(embed=embed, view=view)
            
            # Save the setup information
            guild_id = str(interaction.guild.id)
            if guild_id not in self.control_data:
                self.control_data[guild_id] = {}
            
            self.control_data[guild_id]['control_panel_channel'] = channel.id
            self.control_data[guild_id]['control_panel_message'] = message.id
            self.control_data[guild_id]['setup_date'] = datetime.now().isoformat()
            self.save_control_data()
            
            await interaction.response.send_message(f"✅ تم إعداد لوحة التحكم في {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up control panel: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعداد لوحة التحكم", ephemeral=True)

    async def get_server_stats(self, interaction: discord.Interaction):
        """Get server statistics"""
        try:
            if not interaction.guild:
                await interaction.response.send_message("❌ هذا الأمر يجب استخدامه في سيرفر", ephemeral=True)
                return
            
            guild = interaction.guild
            
            # Count different channel types
            text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
            voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
            categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
            
            # Count members by status
            online_members = sum(1 for m in guild.members if m.status != discord.Status.offline)
            bots = sum(1 for m in guild.members if m.bot)
            
            embed = discord.Embed(
                title=f"📊 إحصائيات {guild.name}",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(name="👥 إجمالي الأعضاء", value=str(guild.member_count), inline=True)
            embed.add_field(name="🟢 متصل", value=str(online_members), inline=True)
            embed.add_field(name="🤖 البوتات", value=str(bots), inline=True)
            
            embed.add_field(name="💬 قنوات نصية", value=str(text_channels), inline=True)  
            embed.add_field(name="🔊 قنوات صوتية", value=str(voice_channels), inline=True)
            embed.add_field(name="📁 الفئات", value=str(categories), inline=True)
            
            embed.add_field(name="👑 المالك", value=guild.owner.mention if guild.owner else "غير محدد", inline=True)
            embed.add_field(name="📅 تم الإنشاء", value=guild.created_at.strftime("%Y-%m-%d"), inline=True)
            embed.add_field(name="📈 مستوى البوست", value=str(guild.premium_tier), inline=True)
            
            if guild.icon:
                embed.set_thumbnail(url=guild.icon.url)
            
            embed.set_footer(text="Qren Control Panel")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting server stats: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء جلب الإحصائيات", ephemeral=True)
    
    @app_commands.command(name="kick", description="طرد عضو من السيرفر")
    @app_commands.describe(member="العضو المراد طرده", reason="سبب الطرد")
    async def kick_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        """Kick a member from the server"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط!", ephemeral=True)
                return
            
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message("❌ لا يمكنك طرد هذا العضو!", ephemeral=True)
                return
            
            await member.kick(reason=reason)
            await interaction.response.send_message(f"✅ تم طرد {member.mention} - السبب: {reason}")
            logger.info(f"{member} kicked by {interaction.user} - Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error kicking member: {e}")
            await interaction.response.send_message("❌ حدث خطأ في طرد العضو", ephemeral=True)
    
    @app_commands.command(name="ban", description="حظر عضو من السيرفر")
    @app_commands.describe(member="العضو المراد حظره", reason="سبب الحظر")
    async def ban_member(self, interaction: discord.Interaction, member: discord.Member, reason: str = "لا يوجد سبب"):
        """Ban a member from the server"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط!", ephemeral=True)
                return
            
            if member.top_role >= interaction.user.top_role:
                await interaction.response.send_message("❌ لا يمكنك حظر هذا العضو!", ephemeral=True)
                return
            
            await member.ban(reason=reason)
            await interaction.response.send_message(f"✅ تم حظر {member.mention} - السبب: {reason}")
            logger.info(f"{member} banned by {interaction.user} - Reason: {reason}")
            
        except Exception as e:
            logger.error(f"Error banning member: {e}")
            await interaction.response.send_message("❌ حدث خطأ في حظر العضو", ephemeral=True)
    
    @app_commands.command(name="clear", description="حذف رسائل من القناة")
    @app_commands.describe(amount="عدد الرسائل المراد حذفها")
    async def clear_messages(self, interaction: discord.Interaction, amount: int):
        """Clear messages from channel"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر للمشرفين فقط!", ephemeral=True)
                return
            
            if amount > 100:
                await interaction.response.send_message("❌ لا يمكن حذف أكثر من 100 رسالة في المرة الواحدة!", ephemeral=True)
                return
            
            await interaction.response.defer()
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.followup.send(f"✅ تم حذف {len(deleted)} رسالة")
            logger.info(f"{len(deleted)} messages cleared by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            await interaction.followup.send("❌ حدث خطأ في حذف الرسائل")

async def setup(bot):
    await bot.add_cog(ControlCommands(bot))