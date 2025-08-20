import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
import json
import asyncio
import aiofiles
import aiohttp
import re
import subprocess
from datetime import datetime, timedelta
from typing import Optional
from utils.button_views import AvatarButtonView
from utils.control_panel_views import ControlPanelView, SystemToolsView, BotStatusView
from utils.publishing_views import ServerPromotionView
from utils.avatar_manager import AvatarManager
# Load configuration
BOT_CONFIG = {
    'prefix': '!',
    'description': 'Qren Unified Discord Bot'
}


logger = logging.getLogger(__name__)

# ==================== AVATAR COMMANDS ====================
class AvatarCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.avatar_manager = AvatarManager()
    
    def is_admin(self, user):
        """Check if user has admin permissions"""
        if isinstance(user, discord.Member):
            return user.guild_permissions.administrator
        return False
    
    @app_commands.command(name="upload_avatar", description="رفع أفتار جديد (للإداريين فقط)")
    @app_commands.describe(
        image="صورة الأفتار المراد رفعها",
        name="اسم الأفتار (اختياري)"
    )
    async def upload_avatar(self, interaction: discord.Interaction, image: discord.Attachment, name: str = ""):
        """Upload a new avatar image"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط!", ephemeral=True)
                return
            
            if not image.content_type or not image.content_type.startswith('image/'):
                await interaction.response.send_message("❌ الرجاء رفع ملف صورة صحيح!", ephemeral=True)
                return
            
            if image.size > 10 * 1024 * 1024:
                await interaction.response.send_message("❌ حجم الصورة كبير جداً! الحد الأقصى 10 ميجابايت.", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            if not name or name == "":
                name = image.filename.split('.')[0]
            
            import re
            clean_name = re.sub(r'[<>:"/\\|?*]', '_', name)
            clean_name = re.sub(r'https?_+', '', clean_name)
            clean_name = clean_name.strip('_')
            
            if not clean_name:
                clean_name = f"avatar_{image.id}"
            
            filename = f"{clean_name}_{image.id}.{image.filename.split('.')[-1]}"
            filepath = os.path.join("avatars", filename)
            
            data = await image.read()
            async with aiofiles.open(filepath, 'wb') as f:
                await f.write(data)
            
            avatar_info = {
                'name': name,
                'clean_name': clean_name,
                'filename': filename,
                'filepath': filepath,
                'uploader': interaction.user.id,
                'upload_time': discord.utils.utcnow().isoformat()
            }
            
            self.avatar_manager.add_avatar(avatar_info)
            
            await interaction.followup.send(f"✅ تم رفع الأفتار '{name}' بنجاح!")
            logger.info(f"Avatar '{name}' uploaded by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error uploading avatar: {e}")
            if interaction.response.is_done():
                await interaction.followup.send("❌ فشل في رفع الأفتار. حاول مرة أخرى.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ فشل في رفع الأفتار. حاول مرة أخرى.", ephemeral=True)
    
    @app_commands.command(name="post_avatar", description="نشر أفتار مع زر التحميل (للإداريين فقط)")
    @app_commands.describe(avatar_name="اسم الأفتار المراد نشره")
    async def post_avatar(self, interaction: discord.Interaction, avatar_name: str):
        """Post an avatar with interactive button"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط!", ephemeral=True)
                return
            
            avatar_info = self.avatar_manager.get_avatar(avatar_name)
            if not avatar_info:
                await interaction.response.send_message(f"❌ لم يتم العثور على الأفتار '{avatar_name}'!", ephemeral=True)
                return
            
            if not os.path.exists(avatar_info['filepath']):
                await interaction.response.send_message(f"❌ ملف الأفتار غير موجود: {avatar_info['filepath']}", ephemeral=True)
                return
            
            await interaction.response.defer()
            
            embed = discord.Embed(
                title="Qren Avatar",
                description="",
                color=discord.Color.blue()
            )
            
            file = discord.File(avatar_info['filepath'])
            embed.set_image(url=f"attachment://{avatar_info['filename']}")
            
            view = AvatarButtonView(avatar_info, self.bot)
            
            await interaction.followup.send(embed=embed, file=file, view=view)
            logger.info(f"Avatar '{avatar_name}' posted by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error posting avatar: {e}")
            if interaction.response.is_done():
                await interaction.followup.send("❌ فشل في نشر الأفتار. حاول مرة أخرى.", ephemeral=True)
            else:
                await interaction.response.send_message("❌ فشل في نشر الأفتار. حاول مرة أخرى.", ephemeral=True)
    
    @app_commands.command(name="list_avatars", description="عرض جميع الأفاتارات المتاحة (للإداريين فقط)")
    async def list_avatars(self, interaction: discord.Interaction):
        """List all available avatars"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط!", ephemeral=True)
                return
            
            avatars = self.avatar_manager.list_avatars()
            
            if not avatars:
                await interaction.response.send_message("📭 لا توجد أفاتارات مرفوعة بعد!", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="📂 الأفاتارات المتاحة",
                description=f"المجموع: {len(avatars)} أفتار",
                color=discord.Color.green()
            )
            
            for i, avatar in enumerate(avatars[:25], 1):
                embed.add_field(
                    name=f"{i}. {avatar['name']}",
                    value=f"الملف: `{avatar['filename']}`",
                    inline=False
                )
            
            if len(avatars) > 25:
                embed.set_footer(text=f"عرض أول 25 من {len(avatars)} أفتار")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error listing avatars: {e}")
            await interaction.response.send_message("❌ فشل في عرض الأفاتارات. حاول مرة أخرى.", ephemeral=True)
    
    @app_commands.command(name="delete_avatar", description="حذف أفتار (للإداريين فقط)")
    @app_commands.describe(avatar_name="اسم الأفتار المراد حذفه")
    async def delete_avatar(self, interaction: discord.Interaction, avatar_name: str):
        """Delete an avatar"""
        try:
            if not self.is_admin(interaction.user):
                await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط!", ephemeral=True)
                return
            
            avatar_info = self.avatar_manager.get_avatar(avatar_name)
            if not avatar_info:
                await interaction.response.send_message(f"❌ لم يتم العثور على الأفتار '{avatar_name}'!", ephemeral=True)
                return
            
            if os.path.exists(avatar_info['filepath']):
                os.remove(avatar_info['filepath'])
            
            self.avatar_manager.remove_avatar(avatar_name)
            
            await interaction.response.send_message(f"✅ تم حذف الأفتار '{avatar_name}' بنجاح!", ephemeral=True)
            logger.info(f"Avatar '{avatar_name}' deleted by {interaction.user}")
            
        except Exception as e:
            logger.error(f"Error deleting avatar: {e}")
            await interaction.response.send_message("❌ فشل في حذف الأفتار. حاول مرة أخرى.", ephemeral=True)
    
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
            ][:25]
            return choices
        except Exception as e:
            logger.error(f"Error in autocomplete: {e}")
            return []

# ==================== CONTROL COMMANDS ====================
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
            embed = discord.Embed(
                title="Control Panel",
                description="اختر من القائمة أدناه لتنفيذ أحد الخيارات\n\nلأخذ أفتار شخص معين\n**Avatar**\n\nلأخذ بنر شخص معين\n**Banner**\n\nللتحميل مقطع\n**Download**\n\nلمعرفة حالة تطوير إشارة البوست الخاصة بك\n**Boost**\n\nلمعرفة حالة تطوير إشارة النيترو الخاصة بك\n**Nitro**",
                color=0x0099ff
            )
            
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            view = ControlPanelView()
            
            message = await channel.send(embed=embed, view=view)
            
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
            
            text_channels = len([c for c in guild.channels if isinstance(c, discord.TextChannel)])
            voice_channels = len([c for c in guild.channels if isinstance(c, discord.VoiceChannel)])
            categories = len([c for c in guild.channels if isinstance(c, discord.CategoryChannel)])
            
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

# ==================== CONSOLE COMMANDS ====================
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
            
            embed = discord.Embed(
                title="🖥️ حالة السيرفر",
                color=discord.Color.green()
            )
            
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
            
            try:
                with open('bot.log', 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    recent_logs = ''.join(lines[-10:])
                
                if len(recent_logs) > 1900:
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

# ==================== PUBLISHING COMMANDS ====================
class PublishingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers_data_file = "servers_data.json"
        self.user_cooldowns_file = "user_cooldowns.json"
        self.load_servers_data()
        self.load_user_cooldowns()
        
        self.channel_mapping = {
            "avatar": "سيرفر-افتار",
            "server": "سيرفر",        
            "store": "متجر"
        }
        
        self.publish_cooldown = 3600  # 1 hour in seconds
    
    def load_servers_data(self):
        """Load servers data from JSON file"""
        try:
            if os.path.exists(self.servers_data_file):
                with open(self.servers_data_file, 'r', encoding='utf-8') as f:
                    self.servers_data = json.load(f)
            else:
                self.servers_data = {}
        except Exception as e:
            logger.error(f"Error loading servers data: {e}")
            self.servers_data = {}
    
    def save_servers_data(self):
        """Save servers data to JSON file"""
        try:
            with open(self.servers_data_file, 'w', encoding='utf-8') as f:
                json.dump(self.servers_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving servers data: {e}")
    
    def load_user_cooldowns(self):
        """Load user cooldowns from JSON file"""
        try:
            if os.path.exists(self.user_cooldowns_file):
                with open(self.user_cooldowns_file, 'r', encoding='utf-8') as f:
                    self.user_cooldowns = json.load(f)
            else:
                self.user_cooldowns = {}
        except Exception as e:
            logger.error(f"Error loading user cooldowns: {e}")
            self.user_cooldowns = {}
    
    def save_user_cooldowns(self):
        """Save user cooldowns to JSON file"""
        try:
            with open(self.user_cooldowns_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_cooldowns, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving user cooldowns: {e}")
    
    def check_user_cooldown(self, user_id: int, guild_id: int) -> tuple[bool, int]:
        """Check if user is on cooldown. Returns (can_publish, remaining_seconds)"""
        user_key = f"{guild_id}_{user_id}"
        
        if user_key not in self.user_cooldowns:
            return True, 0
        
        last_publish_time = datetime.fromisoformat(self.user_cooldowns[user_key])
        current_time = datetime.now()
        time_diff = (current_time - last_publish_time).total_seconds()
        
        if time_diff >= self.publish_cooldown:
            return True, 0
        else:
            remaining = int(self.publish_cooldown - time_diff)
            return False, remaining
    
    def update_user_cooldown(self, user_id: int, guild_id: int):
        """Update user's last publish time"""
        user_key = f"{guild_id}_{user_id}"
        self.user_cooldowns[user_key] = datetime.now().isoformat()
        self.save_user_cooldowns()
    
    def format_time_remaining(self, seconds: int) -> str:
        """Format remaining cooldown time in Arabic"""
        if seconds >= 3600:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            if minutes > 0:
                return f"{hours} ساعة و {minutes} دقيقة"
            else:
                return f"{hours} ساعة"
        elif seconds >= 60:
            minutes = seconds // 60
            return f"{minutes} دقيقة"
        else:
            return f"{seconds} ثانية"
    
    def extract_server_id_from_invite(self, invite_link: str) -> Optional[str]:
        """Extract server ID from Discord invite link"""
        patterns = [
            r'discord\.gg/([A-Za-z0-9]+)',
            r'discord\.com/invite/([A-Za-z0-9]+)',
            r'discordapp\.com/invite/([A-Za-z0-9]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, invite_link)
            if match:
                return match.group(1)
        return None
    
    async def get_server_info_from_invite(self, invite_code: str):
        """Get server information from invite code"""
        try:
            async with aiohttp.ClientSession() as session:
                clean_invite = invite_code.strip().split('/')[-1].split('?')[0]
                url = f"https://discord.com/api/v10/invites/{clean_invite}?with_counts=true"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        guild_info = data.get('guild', {})
                        
                        logger.info(f"Successfully fetched server info for: {guild_info.get('name', 'Unknown')}")
                        
                        return {
                            'name': guild_info.get('name'),
                            'icon': guild_info.get('icon'),
                            'member_count': data.get('approximate_member_count', 0),
                            'online_count': data.get('approximate_presence_count', 0),
                            'guild_id': guild_info.get('id')
                        }
                    else:
                        logger.warning(f"Failed to fetch server info, status: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching server info: {e}")
        return None

    @app_commands.command(name="setup_promotion", description="إعداد نظام نشر السيرفرات")
    @app_commands.describe(channel="القناة التي ستحتوي على قائمة نشر السيرفرات")
    async def setup_server_promotion(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Setup the server promotion system"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            embed = discord.Embed(
                title="Share Panel",
                description="اختر نوع المحتوى الذي تريد نشره\n\n**Publication Types**\n\nنشر أفتارات وصور شخصية - **Avatar**\n\nنشر رابط السيرفر - **Server**\n\nنشر منتجات ومتاجر - **Store**",
                color=0x00ff00
            )
            
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            view = ServerPromotionView()
            
            try:
                file_path = "qren_logo_new.png"
                if os.path.exists(file_path):
                    file = discord.File(file_path, filename="qren_logo.png")
                    embed.set_image(url="attachment://qren_logo.png")
                    message = await channel.send(embed=embed, view=view, file=file)
                else:
                    embed.set_footer(text="Qren Share System")
                    message = await channel.send(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Error attaching logo image: {e}")
                embed.set_footer(text="Qren Share System")
                message = await channel.send(embed=embed, view=view)
            
            guild_id = str(interaction.guild.id)
            if guild_id not in self.servers_data:
                self.servers_data[guild_id] = {}
            
            self.servers_data[guild_id]['promotion_channel'] = channel.id
            self.servers_data[guild_id]['promotion_message'] = message.id
            self.save_servers_data()
            
            await interaction.response.send_message(f"✅ تم إعداد نظام نشر السيرفرات في {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up server promotion: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعداد النظام", ephemeral=True)

    async def publish_server(self, interaction: discord.Interaction, server_link: str, server_type: str):
        """Publish a server to the appropriate channel"""
        try:
            if not interaction.guild:
                await interaction.followup.send("❌ هذا الأمر متاح في السيرفرات فقط", ephemeral=True)
                return
                
            guild_id = str(interaction.guild.id)
            user_id = interaction.user.id
            
            # Check user cooldown first
            can_publish, remaining_seconds = self.check_user_cooldown(user_id, int(guild_id))
            if not can_publish:
                time_remaining = self.format_time_remaining(remaining_seconds)
                embed = discord.Embed(
                    title="⏱️ انتظار مطلوب",
                    description=f"لا يمكنك نشر سيرفر جديد الآن.\nيجب الانتظار **{time_remaining}** قبل النشر مرة أخرى.",
                    color=0xff6b6b
                )
                embed.add_field(
                    name="📋 القواعد",
                    value="• يمكن نشر سيرفر واحد كل ساعة فقط\n• هذا النظام لضمان جودة المحتوى",
                    inline=False
                )
                embed.set_footer(text="Qren Share System")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Check if channels are configured
            if guild_id not in self.servers_data or 'channels' not in self.servers_data[guild_id]:
                await interaction.followup.send("❌ لم يتم إعداد القنوات بعد. يرجى التواصل مع الإدارة", ephemeral=True)
                return
            
            # Get the appropriate channel
            channel_id = self.servers_data[guild_id]['channels'].get(server_type)
            if not channel_id:
                await interaction.followup.send("❌ لم يتم إعداد القناة المطلوبة", ephemeral=True)
                return
            
            channel = self.bot.get_channel(channel_id)
            if not channel:
                await interaction.followup.send("❌ لم يتم العثور على القناة", ephemeral=True)
                return
            
            # Get server information from invite link
            invite_code = self.extract_server_id_from_invite(server_link)
            server_info = None
            if invite_code:
                server_info = await self.get_server_info_from_invite(invite_code)
            
            # Create server promotion embed
            embed = discord.Embed(
                title="سيرفر جديد",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            type_info = {
                "avatar": {"name": "سيرفر افتار"},
                "server": {"name": "سيرفر عام"},
                "store": {"name": "متجر"}
            }
            
            info = type_info.get(server_type, {"name": "سيرفر"})
            
            # Apply server information to embed if available
            if server_info:
                if server_info.get('name'):
                    embed.title = f"📢 {server_info['name']}"
                    embed.description = f"**{info['name']}**"
                    
                if server_info.get('icon') and server_info.get('guild_id'):
                    icon_extension = "gif" if server_info['icon'].startswith('a_') else "png"
                    icon_url = f"https://cdn.discordapp.com/icons/{server_info['guild_id']}/{server_info['icon']}.{icon_extension}?size=256"
                    embed.set_thumbnail(url=icon_url)
                    
                if server_info.get('member_count', 0) > 0:
                    embed.add_field(
                        name="عدد الأعضاء",
                        value=f"👥 {server_info['member_count']:,} عضو",
                        inline=True
                    )
            else:
                embed.description = f"**{info['name']}** - لا يمكن الحصول على معلومات السيرفر"
            
            embed.add_field(
                name="نوع السيرفر",
                value=info['name'],
                inline=True
            )
            embed.add_field(
                name="منشر بواسطة",
                value=interaction.user.mention,
                inline=True
            )
            embed.add_field(
                name="الرابط",
                value=server_link,
                inline=False
            )
            
            embed.set_footer(text="Qren Share System")
            embed.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url)
            
            # Send to the appropriate channel
            await channel.send(embed=embed)
            
            # Save server publishing data
            server_publish_data = {
                "link": server_link,
                "type": server_type,
                "publisher": str(interaction.user.id),
                "published_at": datetime.now().isoformat(),
                "channel_id": channel_id
            }
            
            if 'published_servers' not in self.servers_data[guild_id]:
                self.servers_data[guild_id]['published_servers'] = []
            
            self.servers_data[guild_id]['published_servers'].append(server_publish_data)
            self.save_servers_data()
            
            # Update user cooldown after successful publish
            self.update_user_cooldown(user_id, int(guild_id))
            
            embed = discord.Embed(
                title="✅ تم نشر السيرفر بنجاح",
                description=f"تم نشر سيرفرك في {channel.mention}",
                color=0x00ff00
            )
            embed.add_field(
                name="⏱️ الانتظار القادم",
                value="يمكنك نشر سيرفر جديد بعد ساعة واحدة",
                inline=False
            )
            embed.set_footer(text="Qren Share System")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error publishing server: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء نشر السيرفر", ephemeral=True)

    @app_commands.command(name="setup_channels", description="إعداد قنوات نشر السيرفرات حسب النوع")
    @app_commands.describe(
        avatar_channel="قناة سيرفرات الافتار",
        server_channel="قناة السيرفرات العامة", 
        store_channel="قناة المتاجر"
    )
    async def setup_channels(self, interaction: discord.Interaction, 
                           avatar_channel: discord.TextChannel,
                           server_channel: discord.TextChannel,
                           store_channel: discord.TextChannel):
        """Setup channels for different server types"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            guild_id = str(interaction.guild.id)
            if guild_id not in self.servers_data:
                self.servers_data[guild_id] = {}
            
            self.servers_data[guild_id]['channels'] = {
                'avatar': avatar_channel.id,
                'server': server_channel.id,
                'store': store_channel.id
            }
            self.save_servers_data()
            
            embed = discord.Embed(
                title="✅ تم إعداد القنوات بنجاح",
                color=0x00ff00
            )
            embed.add_field(name="🖼️ سيرفرات الافتار", value=avatar_channel.mention, inline=True)
            embed.add_field(name="🏠 السيرفرات العامة", value=server_channel.mention, inline=True)
            embed.add_field(name="🛒 المتاجر", value=store_channel.mention, inline=True)
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up channels: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعداد القنوات", ephemeral=True)

    @app_commands.command(name="server_stats", description="إحصائيات السيرفرات المنشورة")
    async def server_stats(self, interaction: discord.Interaction):
        """Show server publishing statistics"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            guild_id = str(interaction.guild.id)
            
            if guild_id not in self.servers_data or 'published_servers' not in self.servers_data[guild_id]:
                await interaction.response.send_message("📊 لا توجد إحصائيات متاحة", ephemeral=True)
                return
            
            servers = self.servers_data[guild_id]['published_servers']
            
            # Count by type
            stats = {"avatar": 0, "server": 0, "store": 0}
            for server in servers:
                server_type = server.get('type', 'server')
                if server_type in stats:
                    stats[server_type] += 1
            
            embed = discord.Embed(
                title="📊 إحصائيات السيرفرات المنشورة",
                color=0x0099ff
            )
            
            embed.add_field(name="🖼️ سيرفرات الافتار", value=str(stats['avatar']), inline=True)
            embed.add_field(name="🏠 السيرفرات العامة", value=str(stats['server']), inline=True) 
            embed.add_field(name="🛒 المتاجر", value=str(stats['store']), inline=True)
            embed.add_field(name="📈 المجموع", value=str(len(servers)), inline=False)
            
            embed.set_footer(text="Qren Share System")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing server stats: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء عرض الإحصائيات", ephemeral=True)

    @app_commands.command(name="cooldown_status", description="فحص حالة انتظار المستخدمين")
    @app_commands.describe(user="المستخدم المراد فحص حالته (اختياري)")
    async def cooldown_status(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        """Check cooldown status for user or all users"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            guild_id = interaction.guild.id
            
            if user:
                # Check specific user
                can_publish, remaining = self.check_user_cooldown(user.id, guild_id)
                
                embed = discord.Embed(
                    title=f"⏱️ حالة انتظار {user.display_name}",
                    color=0x00ff00 if can_publish else 0xff6b6b
                )
                
                if can_publish:
                    embed.add_field(
                        name="✅ الحالة",
                        value="يمكن النشر الآن",
                        inline=False
                    )
                else:
                    time_remaining = self.format_time_remaining(remaining)
                    embed.add_field(
                        name="⏳ وقت الانتظار المتبقي",
                        value=time_remaining,
                        inline=False
                    )
                
                embed.set_thumbnail(url=user.display_avatar.url)
                
            else:
                # Show all active cooldowns
                embed = discord.Embed(
                    title="⏱️ حالة انتظار جميع المستخدمين",
                    color=0x0099ff
                )
                
                active_cooldowns = []
                current_time = datetime.now()
                
                for user_key, last_publish in self.user_cooldowns.items():
                    if user_key.startswith(f"{guild_id}_"):
                        user_id = int(user_key.split("_")[1])
                        member = interaction.guild.get_member(user_id)
                        
                        if member:
                            last_time = datetime.fromisoformat(last_publish)
                            time_diff = (current_time - last_time).total_seconds()
                            
                            if time_diff < self.publish_cooldown:
                                remaining = int(self.publish_cooldown - time_diff)
                                time_remaining = self.format_time_remaining(remaining)
                                active_cooldowns.append(f"• {member.display_name}: {time_remaining}")
                
                if active_cooldowns:
                    embed.add_field(
                        name="👥 مستخدمون في فترة انتظار",
                        value="\n".join(active_cooldowns[:10]),
                        inline=False
                    )
                    
                    if len(active_cooldowns) > 10:
                        embed.add_field(
                            name="📊 المجموع",
                            value=f"{len(active_cooldowns)} مستخدم في انتظار",
                            inline=False
                        )
                else:
                    embed.add_field(
                        name="✅ جميع المستخدمين",
                        value="يمكن لجميع المستخدمين النشر الآن",
                        inline=False
                    )
            
            embed.set_footer(text="Qren Share System")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error checking cooldown status: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء فحص حالة الانتظار", ephemeral=True)

    @app_commands.command(name="reset_cooldown", description="إعادة تعيين فترة انتظار مستخدم")
    @app_commands.describe(user="المستخدم المراد إعادة تعيين انتظاره")
    async def reset_cooldown(self, interaction: discord.Interaction, user: discord.Member):
        """Reset user's publishing cooldown"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            guild_id = interaction.guild.id
            user_key = f"{guild_id}_{user.id}"
            
            if user_key in self.user_cooldowns:
                del self.user_cooldowns[user_key]
                self.save_user_cooldowns()
                
                embed = discord.Embed(
                    title="✅ تم إعادة التعيين",
                    description=f"تم إعادة تعيين فترة انتظار {user.mention}\nيمكنه الآن نشر سيرفر جديد",
                    color=0x00ff00
                )
                embed.set_thumbnail(url=user.display_avatar.url)
                
                logger.info(f"Admin {interaction.user} reset cooldown for user {user}")
                
            else:
                embed = discord.Embed(
                    title="ℹ️ لا يوجد انتظار",
                    description=f"{user.mention} غير موجود في قائمة الانتظار",
                    color=0x0099ff
                )
            
            embed.set_footer(text="Qren Share System")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error resetting cooldown: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعادة تعيين الانتظار", ephemeral=True)

# ==================== TAG SEARCH COMMANDS ====================
class TagSearchCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldown_file = "search_cooldowns.json"
        self.load_cooldowns()
    
    def load_cooldowns(self):
        """Load cooldown data from file"""
        try:
            if os.path.exists(self.cooldown_file):
                with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                    self.cooldowns = json.load(f)
            else:
                self.cooldowns = {}
        except:
            self.cooldowns = {}
    
    def save_cooldowns(self):
        """Save cooldown data to file"""
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.cooldowns, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def check_cooldown(self, user_id):
        """Check if user is on cooldown"""
        user_id_str = str(user_id)
        if user_id_str not in self.cooldowns:
            return False, 0
        
        last_search = datetime.fromisoformat(self.cooldowns[user_id_str])
        now = datetime.now()
        time_diff = now - last_search
        
        if time_diff < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - time_diff
            return True, remaining.total_seconds()
        
        return False, 0
    
    def set_cooldown(self, user_id):
        """Set cooldown for user"""
        self.cooldowns[str(user_id)] = datetime.now().isoformat()
        self.save_cooldowns()

    @app_commands.command(name="بحث", description="البحث عن تاق معين والحصول على روابط السيرفرات")
    @app_commands.describe(tag="التاق المراد البحث عنه")
    async def search_tag(self, interaction: discord.Interaction, tag: str):
        """Search for a tag and return all server links that have this tag"""
        try:
            # Check cooldown
            on_cooldown, remaining_seconds = self.check_cooldown(interaction.user.id)
            
            if on_cooldown:
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                
                embed = discord.Embed(
                    title="انتظر قليلاً",
                    description=f"يمكنك البحث مرة واحدة كل 5 دقائق\n\n**الوقت المتبقي:** {remaining_minutes} دقيقة و {remaining_secs} ثانية",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            await interaction.response.defer()
            
            tag = tag.strip()
            if not tag:
                await interaction.followup.send("الرجاء إدخال تاق للبحث", ephemeral=True)
                return
            
            # Set cooldown for user
            self.set_cooldown(interaction.user.id)
            
            # Search in stored tags data
            search_results = []
            
            if hasattr(self.bot, 'tags_data') and self.bot.tags_data:
                for server_id, server_data in self.bot.tags_data.items():
                    if "tags" in server_data and isinstance(server_data["tags"], list):
                        for tag_entry in server_data["tags"]:
                            entry_tag = tag_entry.get("tag", "").lower().strip()
                            search_tag = tag.lower().strip()
                            
                            if search_tag in entry_tag or entry_tag == search_tag:
                                search_results.append({
                                    "tag": tag_entry.get("tag", ""),
                                    "server_link": tag_entry.get("server_link", ""),
                                    "server_name": tag_entry.get("server_name", "غير محدد"),
                                    "description": tag_entry.get("description", ""),
                                    "added_by": tag_entry.get("added_by", "غير معروف")
                                })
            
            # Add popular servers for common tags
            popular_servers = {
                'gaming': 'https://discord.gg/gaming',
                'anime': 'https://discord.gg/anime',
                'music': 'https://discord.gg/music',
                'arabic': 'https://discord.gg/arabic',
                'art': 'https://discord.gg/art',
                'chat': 'https://discord.gg/chat',
                'minecraft': 'https://discord.gg/minecraft',
                'valorant': 'https://discord.gg/valorant'
            }
            
            tag_lower = tag.lower()
            for popular_tag, link in popular_servers.items():
                if tag_lower == popular_tag or tag_lower in popular_tag:
                    search_results.append({
                        "tag": tag,
                        "server_link": link,
                        "server_name": f"{popular_tag.title()} Community",
                        "description": "سيرفر شائع ومشهور",
                        "added_by": "النظام"
                    })
            
            if not search_results:
                embed = discord.Embed(
                    title="نتائج البحث",
                    description=f"لم أجد سيرفرات للتاق: `{tag}`\n\n💡 جرب تاقات شائعة مثل: gaming, anime, music, arabic, art",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Remove duplicates
            unique_results = []
            seen_links = set()
            for result in search_results:
                if result['server_link'] not in seen_links:
                    unique_results.append(result)
                    seen_links.add(result['server_link'])
            
            embed = discord.Embed(
                title="نتائج البحث",
                description=f"تم العثور على **{len(unique_results)} سيرفر** للتاق: `{tag}`",
                color=0x00ff00
            )
            
            # Show up to 8 results
            for i, result in enumerate(unique_results[:8], 1):
                server_name = result.get('server_name', 'سيرفر غير محدد')
                server_link = result.get('server_link', '')
                description = result.get('description', '')
                
                field_value = f"**🔗 انضم الآن:** {server_link}\\n"
                if description:
                    field_value += f"**الوصف:** {description}\\n"
                field_value += f"**أضافه:** {result.get('added_by', 'غير معروف')}"
                
                embed.add_field(
                    name=f"{i}. {server_name}",
                    value=field_value,
                    inline=False
                )
            
            embed.set_footer(text=f"إجمالي النتائج: {len(unique_results)} سيرفر")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in search_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء البحث عن التاق. الرجاء المحاولة مرة أخرى.", ephemeral=True)
    
    @app_commands.command(name="اضافة", description="إضافة تاق جديد مع رابط السيرفر")
    @app_commands.describe(
        tag="التاق المراد إضافته",
        server_link="رابط السيرفر",
        server_name="اسم السيرفر (اختياري)",
        description="وصف السيرفر (اختياري)"
    )
    async def add_tag(self, interaction: discord.Interaction, tag: str, server_link: str, server_name: str | None = None, description: str | None = None):
        """Add a new tag with server link and optional description"""
        await interaction.response.defer()
        
        try:
            # Clean and validate the tag
            tag = tag.strip()
            if len(tag) < 2:
                await interaction.followup.send("❌ التاق يجب أن يكون على الأقل حرفين!")
                return
            
            if len(tag) > 50:
                await interaction.followup.send("❌ التاق طويل جداً! الحد الأقصى 50 حرف.")
                return
            
            # Validate server link
            if not (server_link.startswith("https://discord.gg/") or server_link.startswith("discord.gg/")):
                embed = discord.Embed(
                    title="❌ رابط غير صحيح",
                    description="الرجاء إدخال رابط سيرفر Discord صحيح\\n\\n**أمثلة صحيحة:**\\n• `https://discord.gg/abc123`\\n• `discord.gg/abc123`",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Normalize the link
            if not server_link.startswith("https://"):
                server_link = "https://" + server_link
            
            # Use global storage
            global_server_id = "global_tags"
            
            # Initialize global entry if doesn't exist
            if global_server_id not in self.bot.tags_data:
                self.bot.tags_data[global_server_id] = {
                    "server_name": "Global Tags Database",
                    "tags": []
                }
            
            # Check if this exact server link already has this tag
            existing_entry = None
            for tag_entry in self.bot.tags_data[global_server_id]["tags"]:
                if tag_entry["server_link"] == server_link and tag_entry["tag"].lower() == tag.lower():
                    existing_entry = tag_entry
                    break
            
            if existing_entry:
                await interaction.followup.send(f"❌ هذا السيرفر يحتوي بالفعل على التاق: `{existing_entry['tag']}`")
                return
            
            # Add new tag
            new_tag = {
                "tag": tag,
                "server_link": server_link,
                "server_name": server_name or "غير محدد",
                "description": description or "",
                "added_by": str(interaction.user.id),
                "added_at": datetime.now().isoformat(),
                "added_from_guild": str(interaction.guild_id) if interaction.guild else "DM"
            }
            
            self.bot.tags_data[global_server_id]["tags"].append(new_tag)
            self.bot.save_tags_data()
            
            embed = discord.Embed(
                title="✅ تم إضافة التاق بنجاح",
                description="تم حفظ التاق في قاعدة البيانات وأصبح متاح للبحث",
                color=0x57f287
            )
            embed.add_field(name="🏷️ التاق", value=f"`{tag}`", inline=True)
            embed.add_field(name="🌐 اسم السيرفر", value=server_name or "غير محدد", inline=True)
            embed.add_field(name="👤 أضافه", value=interaction.user.mention, inline=True)
            embed.add_field(name="🔗 رابط السيرفر", value=f"[انضم للسيرفر]({server_link})", inline=False)
            
            if description:
                embed.add_field(name="📝 الوصف", value=description, inline=False)
                
            embed.set_footer(text=f"يمكن البحث عن هذا التاق باستخدام: /بحث {tag}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in add_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء إضافة التاق. الرجاء المحاولة مرة أخرى.")
    
    @app_commands.command(name="حذف", description="حذف تاق موجود")
    @app_commands.describe(
        tag="التاق المراد حذفه",
        server_link="رابط السيرفر (اختياري للتحديد الدقيق)"
    )
    async def remove_tag(self, interaction: discord.Interaction, tag: str, server_link: str | None = None):
        """Remove an existing tag"""
        await interaction.response.defer()
        
        try:
            global_server_id = "global_tags"
            
            if global_server_id not in self.bot.tags_data or not self.bot.tags_data[global_server_id]["tags"]:
                await interaction.followup.send("❌ لا توجد تاقات مسجلة في قاعدة البيانات.")
                return
            
            # Find matching tags
            tags_list = self.bot.tags_data[global_server_id]["tags"]
            matching_tags = []
            
            for tag_entry in tags_list:
                if tag_entry["tag"].lower() == tag.lower():
                    if server_link is None or tag_entry["server_link"] == server_link:
                        matching_tags.append(tag_entry)
            
            if not matching_tags:
                await interaction.followup.send(f"❌ لم يتم العثور على التاق: `{tag}`")
                return
            
            # Check permissions
            member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
            is_admin = member.guild_permissions.administrator if member else False
            user_id = str(interaction.user.id)
            
            # Filter tags that user can delete
            deletable_tags = []
            for tag_entry in matching_tags:
                if is_admin or tag_entry["added_by"] == user_id:
                    deletable_tags.append(tag_entry)
            
            if not deletable_tags:
                await interaction.followup.send("❌ يمكنك حذف التاقات التي أضفتها أنت فقط، أو كن أدمن لحذف أي تاق.")
                return
            
            # If multiple matches and no specific server_link provided, show options
            if len(deletable_tags) > 1 and server_link is None:
                embed = discord.Embed(
                    title="🔍 عدة نتائج للتاق",
                    description=f"تم العثور على {len(deletable_tags)} سيرفر يحتوي على التاق `{tag}`\\n\\nحدد السيرفر المراد حذف التاق منه:",
                    color=0xffa500
                )
                
                for i, tag_entry in enumerate(deletable_tags[:10], 1):
                    embed.add_field(
                        name=f"{i}. {tag_entry['server_name']}",
                        value=f"**الرابط:** {tag_entry['server_link']}\\n**أضافه:** <@{tag_entry['added_by']}>",
                        inline=False
                    )
                
                embed.set_footer(text="استخدم الأمر مع تحديد رابط السيرفر: /حذف تاق [التاق] [رابط_السيرفر]")
                await interaction.followup.send(embed=embed)
                return
            
            # Remove the tag(s)
            removed_count = 0
            for tag_entry in deletable_tags:
                if tag_entry in tags_list:
                    tags_list.remove(tag_entry)
                    removed_count += 1
            
            self.bot.save_tags_data()
            
            embed = discord.Embed(
                title="🗑️ تم حذف التاق بنجاح",
                description=f"تم حذف {removed_count} تاق بالاسم: `{tag}`",
                color=0xff6b6b
            )
            
            if removed_count == 1:
                deleted_tag = deletable_tags[0]
                embed.add_field(name="السيرفر", value=deleted_tag['server_name'], inline=True)
                embed.add_field(name="الرابط", value=deleted_tag['server_link'], inline=True)
            
            embed.add_field(name="حذفه", value=interaction.user.mention, inline=True)
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in remove_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء حذف التاق.")
    
    @app_commands.command(name="قائمة", description="عرض جميع التاقات المتاحة")
    @app_commands.describe(
        filter_tag="فلترة التاقات (اختياري)",
        show_my_tags="عرض التاقات التي أضفتها أنت فقط"
    )
    async def list_tags(self, interaction: discord.Interaction, filter_tag: str | None = None, show_my_tags: bool = False):
        """List all available tags with optional filtering"""
        await interaction.response.defer()
        
        try:
            global_server_id = "global_tags"
            
            if global_server_id not in self.bot.tags_data or not self.bot.tags_data[global_server_id]["tags"]:
                embed = discord.Embed(
                    title="📋 قائمة التاقات",
                    description="لا توجد تاقات مسجلة في قاعدة البيانات.\\n\\n💡 استخدم `/اضافة` لإضافة تاق جديد!",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed)
                return
            
            tags_list = self.bot.tags_data[global_server_id]["tags"]
            
            # Apply filters
            filtered_tags = []
            user_id = str(interaction.user.id)
            
            for tag_entry in tags_list:
                # Filter by user if requested
                if show_my_tags and tag_entry.get("added_by") != user_id:
                    continue
                
                # Filter by tag text if provided
                if filter_tag and filter_tag.lower() not in tag_entry["tag"].lower():
                    continue
                
                filtered_tags.append(tag_entry)
            
            if not filtered_tags:
                filter_desc = ""
                if show_my_tags:
                    filter_desc += "التي أضفتها أنت "
                if filter_tag:
                    filter_desc += f"التي تحتوي على '{filter_tag}' "
                
                embed = discord.Embed(
                    title="📋 قائمة التاقات",
                    description=f"لا توجد تاقات {filter_desc}في قاعدة البيانات.",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create pages for tags
            tags_per_page = 10
            total_pages = (len(filtered_tags) + tags_per_page - 1) // tags_per_page
            
            embed = discord.Embed(
                title="📋 قائمة التاقات المتاحة",
                description=f"إجمالي التاقات: **{len(filtered_tags)}** تاق",
                color=0x57f287
            )
            
            # Show first page
            page_tags = filtered_tags[:tags_per_page]
            for i, tag_entry in enumerate(page_tags, 1):
                tag_name = tag_entry.get("tag", "غير محدد")
                server_name = tag_entry.get("server_name", "غير محدد")
                added_by = tag_entry.get("added_by", "غير معروف")
                
                embed.add_field(
                    name=f"{i}. `{tag_name}`",
                    value=f"**السيرفر:** {server_name}\\n**أضافه:** <@{added_by}>",
                    inline=True
                )
            
            if total_pages > 1:
                embed.set_footer(text=f"الصفحة 1 من {total_pages} • استخدم /قائمة مع الفلترة لتحديد البحث")
            else:
                embed.set_footer(text=f"مجموع التاقات: {len(filtered_tags)}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list_tags: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء عرض قائمة التاقات.")

    @app_commands.command(name="setup_tag_search", description="إعداد نظام البحث بالتاقات")
    @app_commands.describe(channel="القناة التي ستحتوي على نظام البحث")
    async def setup_tag_search(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Setup the tag search system"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            from utils.button_views import TagSearchView
            
            embed = discord.Embed(
                title="🔍 نظام البحث بالتاقات",
                description="استخدم الأزرار أدناه للبحث عن السيرفرات أو إضافة تاقات جديدة",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🔍 البحث عن تاق",
                value="ابحث عن سيرفرات باستخدام التاقات",
                inline=True
            )
            
            embed.add_field(
                name="➕ إضافة تاق",
                value="أضف تاق جديد لسيرفر",
                inline=True
            )
            
            embed.set_footer(text="Qren Tag Search System")
            
            view = TagSearchView(self.bot)
            message = await channel.send(embed=embed, view=view)
            
            await interaction.response.send_message(f"✅ تم إعداد نظام البحث بالتاقات في {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up tag search: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعداد النظام", ephemeral=True)
    
    def load_cooldowns(self):
        """Load cooldown data from file"""
        try:
            if os.path.exists(self.cooldown_file):
                with open(self.cooldown_file, 'r', encoding='utf-8') as f:
                    self.cooldowns = json.load(f)
            else:
                self.cooldowns = {}
        except:
            self.cooldowns = {}
    
    def save_cooldowns(self):
        """Save cooldown data to file"""
        try:
            with open(self.cooldown_file, 'w', encoding='utf-8') as f:
                json.dump(self.cooldowns, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def check_cooldown(self, user_id):
        """Check if user is on cooldown"""
        user_id_str = str(user_id)
        if user_id_str not in self.cooldowns:
            return False, 0
        
        last_search = datetime.fromisoformat(self.cooldowns[user_id_str])
        now = datetime.now()
        time_diff = now - last_search
        
        if time_diff < timedelta(minutes=5):
            remaining = timedelta(minutes=5) - time_diff
            return True, remaining.total_seconds()
        
        return False, 0
    
    def set_cooldown(self, user_id):
        """Set cooldown for user"""
        self.cooldowns[str(user_id)] = datetime.now().isoformat()
        self.save_cooldowns()

    @app_commands.command(name="بحث", description="البحث عن تاق معين والحصول على روابط السيرفرات")
    @app_commands.describe(tag="التاق المراد البحث عنه")
    async def search_tag(self, interaction: discord.Interaction, tag: str):
        """Search for a tag and return all server links that have this tag"""
        try:
            # Check cooldown
            on_cooldown, remaining_seconds = self.check_cooldown(interaction.user.id)
            
            if on_cooldown:
                remaining_minutes = int(remaining_seconds // 60)
                remaining_secs = int(remaining_seconds % 60)
                
                embed = discord.Embed(
                    title="انتظر قليلاً",
                    description=f"يمكنك البحث مرة واحدة كل 5 دقائق\n\n**الوقت المتبقي:** {remaining_minutes} دقيقة و {remaining_secs} ثانية",
                    color=0xff6b6b
                )
                await interaction.response.send_message(embed=embed, ephemeral=True)
                return
            
            await interaction.response.defer()
            
            tag = tag.strip()
            if not tag:
                await interaction.followup.send("الرجاء إدخال تاق للبحث", ephemeral=True)
                return
            
            # Set cooldown for user
            self.set_cooldown(interaction.user.id)
            
            # Search in stored tags data
            search_results = []
            
            if hasattr(self.bot, 'tags_data') and self.bot.tags_data:
                for server_id, server_data in self.bot.tags_data.items():
                    if "tags" in server_data and isinstance(server_data["tags"], list):
                        for tag_entry in server_data["tags"]:
                            entry_tag = tag_entry.get("tag", "").lower().strip()
                            search_tag = tag.lower().strip()
                            
                            if search_tag in entry_tag or entry_tag == search_tag:
                                search_results.append({
                                    "tag": tag_entry.get("tag", ""),
                                    "server_link": tag_entry.get("server_link", ""),
                                    "server_name": tag_entry.get("server_name", "غير محدد"),
                                    "description": tag_entry.get("description", ""),
                                    "added_by": tag_entry.get("added_by", "غير معروف")
                                })
            
            # Add popular servers for common tags
            popular_servers = {
                'gaming': 'https://discord.gg/gaming',
                'anime': 'https://discord.gg/anime',
                'music': 'https://discord.gg/music',
                'arabic': 'https://discord.gg/arabic',
                'art': 'https://discord.gg/art',
                'chat': 'https://discord.gg/chat',
                'minecraft': 'https://discord.gg/minecraft',
                'valorant': 'https://discord.gg/valorant'
            }
            
            tag_lower = tag.lower()
            for popular_tag, link in popular_servers.items():
                if tag_lower == popular_tag or tag_lower in popular_tag:
                    search_results.append({
                        "tag": tag,
                        "server_link": link,
                        "server_name": f"{popular_tag.title()} Community",
                        "description": "سيرفر شائع ومشهور",
                        "added_by": "النظام"
                    })
            
            if not search_results:
                embed = discord.Embed(
                    title="نتائج البحث",
                    description=f"لم أجد سيرفرات للتاق: `{tag}`\n\n💡 جرب تاقات شائعة مثل: gaming, anime, music, arabic, art",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed, ephemeral=True)
                return
            
            # Remove duplicates
            unique_results = []
            seen_links = set()
            for result in search_results:
                if result['server_link'] not in seen_links:
                    unique_results.append(result)
                    seen_links.add(result['server_link'])
            
            embed = discord.Embed(
                title="نتائج البحث",
                description=f"تم العثور على **{len(unique_results)} سيرفر** للتاق: `{tag}`",
                color=0x00ff00
            )
            
            # Show up to 8 results
            for i, result in enumerate(unique_results[:8], 1):
                server_name = result.get('server_name', 'سيرفر غير محدد')
                server_link = result.get('server_link', '')
                description = result.get('description', '')
                
                field_value = f"**🔗 انضم الآن:** {server_link}\n"
                if description:
                    field_value += f"**الوصف:** {description}\n"
                field_value += f"**أضافه:** {result.get('added_by', 'غير معروف')}"
                
                embed.add_field(
                    name=f"{i}. {server_name}",
                    value=field_value,
                    inline=False
                )
            
            embed.set_footer(text=f"إجمالي النتائج: {len(unique_results)} سيرفر")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in search_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء البحث عن التاق. الرجاء المحاولة مرة أخرى.", ephemeral=True)
    
    @app_commands.command(name="اضافة", description="إضافة تاق جديد مع رابط السيرفر")
    @app_commands.describe(
        tag="التاق المراد إضافته",
        server_link="رابط السيرفر",
        server_name="اسم السيرفر (اختياري)",
        description="وصف السيرفر (اختياري)"
    )
    async def add_tag(self, interaction: discord.Interaction, tag: str, server_link: str, server_name: str | None = None, description: str | None = None):
        """Add a new tag with server link and optional description"""
        await interaction.response.defer()
        
        try:
            # Clean and validate the tag
            tag = tag.strip()
            if len(tag) < 2:
                await interaction.followup.send("❌ التاق يجب أن يكون على الأقل حرفين!")
                return
            
            if len(tag) > 50:
                await interaction.followup.send("❌ التاق طويل جداً! الحد الأقصى 50 حرف.")
                return
            
            # Validate server link
            if not (server_link.startswith("https://discord.gg/") or server_link.startswith("discord.gg/")):
                embed = discord.Embed(
                    title="❌ رابط غير صحيح",
                    description="الرجاء إدخال رابط سيرفر Discord صحيح\n\n**أمثلة صحيحة:**\n• `https://discord.gg/abc123`\n• `discord.gg/abc123`",
                    color=0xff6b6b
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Normalize the link
            if not server_link.startswith("https://"):
                server_link = "https://" + server_link
            
            # Use global storage
            global_server_id = "global_tags"
            
            # Initialize global entry if doesn't exist
            if global_server_id not in self.bot.tags_data:
                self.bot.tags_data[global_server_id] = {
                    "server_name": "Global Tags Database",
                    "tags": []
                }
            
            # Check if this exact server link already has this tag
            existing_entry = None
            for tag_entry in self.bot.tags_data[global_server_id]["tags"]:
                if tag_entry["server_link"] == server_link and tag_entry["tag"].lower() == tag.lower():
                    existing_entry = tag_entry
                    break
            
            if existing_entry:
                await interaction.followup.send(f"❌ هذا السيرفر يحتوي بالفعل على التاق: `{existing_entry['tag']}`")
                return
            
            # Add new tag
            new_tag = {
                "tag": tag,
                "server_link": server_link,
                "server_name": server_name or "غير محدد",
                "description": description or "",
                "added_by": str(interaction.user.id),
                "added_at": datetime.now().isoformat(),
                "added_from_guild": str(interaction.guild_id) if interaction.guild else "DM"
            }
            
            self.bot.tags_data[global_server_id]["tags"].append(new_tag)
            self.bot.save_tags_data()
            
            embed = discord.Embed(
                title="✅ تم إضافة التاق بنجاح",
                description="تم حفظ التاق في قاعدة البيانات وأصبح متاح للبحث",
                color=0x57f287
            )
            embed.add_field(name="🏷️ التاق", value=f"`{tag}`", inline=True)
            embed.add_field(name="🌐 اسم السيرفر", value=server_name or "غير محدد", inline=True)
            embed.add_field(name="👤 أضافه", value=interaction.user.mention, inline=True)
            embed.add_field(name="🔗 رابط السيرفر", value=f"[انضم للسيرفر]({server_link})", inline=False)
            
            if description:
                embed.add_field(name="📝 الوصف", value=description, inline=False)
                
            embed.set_footer(text=f"يمكن البحث عن هذا التاق باستخدام: /بحث {tag}")
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in add_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء إضافة التاق. الرجاء المحاولة مرة أخرى.")
    
    @app_commands.command(name="حذف", description="حذف تاق موجود")
    @app_commands.describe(
        tag="التاق المراد حذفه",
        server_link="رابط السيرفر (اختياري للتحديد الدقيق)"
    )
    async def remove_tag(self, interaction: discord.Interaction, tag: str, server_link: str | None = None):
        """Remove an existing tag"""
        await interaction.response.defer()
        
        try:
            global_server_id = "global_tags"
            
            if global_server_id not in self.bot.tags_data or not self.bot.tags_data[global_server_id]["tags"]:
                await interaction.followup.send("❌ لا توجد تاقات مسجلة في قاعدة البيانات.")
                return
            
            # Find matching tags
            tags_list = self.bot.tags_data[global_server_id]["tags"]
            matching_tags = []
            
            for tag_entry in tags_list:
                if tag_entry["tag"].lower() == tag.lower():
                    if server_link is None or tag_entry["server_link"] == server_link:
                        matching_tags.append(tag_entry)
            
            if not matching_tags:
                await interaction.followup.send(f"❌ لم يتم العثور على التاق: `{tag}`")
                return
            
            # Check permissions
            member = interaction.guild.get_member(interaction.user.id) if interaction.guild else None
            is_admin = member.guild_permissions.administrator if member else False
            user_id = str(interaction.user.id)
            
            # Filter tags that user can delete
            deletable_tags = []
            for tag_entry in matching_tags:
                if is_admin or tag_entry["added_by"] == user_id:
                    deletable_tags.append(tag_entry)
            
            if not deletable_tags:
                await interaction.followup.send("❌ يمكنك حذف التاقات التي أضفتها أنت فقط، أو كن أدمن لحذف أي تاق.")
                return
            
            # If multiple matches and no specific server_link provided, show options
            if len(deletable_tags) > 1 and server_link is None:
                embed = discord.Embed(
                    title="🔍 عدة نتائج للتاق",
                    description=f"تم العثور على {len(deletable_tags)} سيرفر يحتوي على التاق `{tag}`\n\nحدد السيرفر المراد حذف التاق منه:",
                    color=0xffa500
                )
                
                for i, tag_entry in enumerate(deletable_tags[:10], 1):
                    embed.add_field(
                        name=f"{i}. {tag_entry['server_name']}",
                        value=f"**الرابط:** {tag_entry['server_link']}\n**أضافه:** <@{tag_entry['added_by']}>",
                        inline=False
                    )
                
                embed.set_footer(text="استخدم الأمر مع تحديد رابط السيرفر: /حذف تاق [التاق] [رابط_السيرفر]")
                await interaction.followup.send(embed=embed)
                return
            
            # Remove the tag(s)
            removed_count = 0
            for tag_entry in deletable_tags:
                if tag_entry in tags_list:
                    tags_list.remove(tag_entry)
                    removed_count += 1
            
            self.bot.save_tags_data()
            
            embed = discord.Embed(
                title="🗑️ تم حذف التاق بنجاح",
                description=f"تم حذف {removed_count} تاق بالاسم: `{tag}`",
                color=0xff6b6b
            )
            
            if removed_count == 1:
                deleted_tag = deletable_tags[0]
                embed.add_field(name="السيرفر", value=deleted_tag['server_name'], inline=True)
                embed.add_field(name="الرابط", value=deleted_tag['server_link'], inline=True)
            
            embed.add_field(name="حذفه", value=interaction.user.mention, inline=True)
            embed.timestamp = datetime.now()
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in remove_tag: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء حذف التاق.")
    
    @app_commands.command(name="قائمة", description="عرض جميع التاقات المتاحة")
    @app_commands.describe(
        filter_tag="فلترة التاقات (اختياري)",
        show_my_tags="عرض التاقات التي أضفتها أنت فقط"
    )
    async def list_tags(self, interaction: discord.Interaction, filter_tag: str | None = None, show_my_tags: bool = False):
        """List all available tags with optional filtering"""
        await interaction.response.defer()
        
        try:
            global_server_id = "global_tags"
            
            if global_server_id not in self.bot.tags_data or not self.bot.tags_data[global_server_id]["tags"]:
                embed = discord.Embed(
                    title="📋 قائمة التاقات",
                    description="لا توجد تاقات مسجلة في قاعدة البيانات.\n\n💡 استخدم `/اضافة` لإضافة تاق جديد!",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed)
                return
            
            tags_list = self.bot.tags_data[global_server_id]["tags"]
            
            # Apply filters
            filtered_tags = []
            user_id = str(interaction.user.id)
            
            for tag_entry in tags_list:
                # Filter by user if requested
                if show_my_tags and tag_entry.get("added_by") != user_id:
                    continue
                
                # Filter by tag text if provided
                if filter_tag and filter_tag.lower() not in tag_entry["tag"].lower():
                    continue
                
                filtered_tags.append(tag_entry)
            
            if not filtered_tags:
                filter_desc = ""
                if show_my_tags:
                    filter_desc += "التي أضفتها أنت "
                if filter_tag:
                    filter_desc += f"التي تحتوي على '{filter_tag}' "
                
                embed = discord.Embed(
                    title="📋 قائمة التاقات",
                    description=f"لا توجد تاقات {filter_desc}في قاعدة البيانات.",
                    color=0xffa500
                )
                await interaction.followup.send(embed=embed)
                return
            
            # Create pages for tags
            tags_per_page = 10
            total_pages = (len(filtered_tags) + tags_per_page - 1) // tags_per_page
            
            embed = discord.Embed(
                title="📋 قائمة التاقات المتاحة",
                description=f"إجمالي التاقات: **{len(filtered_tags)}** تاق",
                color=0x57f287
            )
            
            # Show first page
            page_tags = filtered_tags[:tags_per_page]
            for i, tag_entry in enumerate(page_tags, 1):
                tag_name = tag_entry.get("tag", "غير محدد")
                server_name = tag_entry.get("server_name", "غير محدد")
                added_by = tag_entry.get("added_by", "غير معروف")
                
                embed.add_field(
                    name=f"{i}. `{tag_name}`",
                    value=f"**السيرفر:** {server_name}\n**أضافه:** <@{added_by}>",
                    inline=True
                )
            
            if total_pages > 1:
                embed.set_footer(text=f"الصفحة 1 من {total_pages} • استخدم /قائمة مع الفلترة لتحديد البحث")
            else:
                embed.set_footer(text=f"مجموع التاقات: {len(filtered_tags)}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Error in list_tags: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء عرض قائمة التاقات.")

    @app_commands.command(name="setup_tag_search", description="إعداد نظام البحث بالتاقات")
    @app_commands.describe(channel="القناة التي ستحتوي على نظام البحث")
    async def setup_tag_search(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Setup the tag search system"""
        if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ هذا الأمر متاح للإداريين فقط", ephemeral=True)
            return
        
        try:
            from utils.button_views import TagSearchView
            
            embed = discord.Embed(
                title="🔍 نظام البحث بالتاقات",
                description="استخدم الأزرار أدناه للبحث عن السيرفرات أو إضافة تاقات جديدة",
                color=0x0099ff
            )
            
            embed.add_field(
                name="🔍 البحث عن تاق",
                value="ابحث عن سيرفرات باستخدام التاقات",
                inline=True
            )
            
            embed.add_field(
                name="➕ إضافة تاق",
                value="أضف تاق جديد لسيرفر",
                inline=True
            )
            
            embed.set_footer(text="Qren Tag Search System")
            
            view = TagSearchView(self.bot)
            message = await channel.send(embed=embed, view=view)
            
            await interaction.response.send_message(f"✅ تم إعداد نظام البحث بالتاقات في {channel.mention}", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error setting up tag search: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء إعداد النظام", ephemeral=True)