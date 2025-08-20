import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import json
import os
import re
import aiohttp
from datetime import datetime, timedelta
from typing import Optional
from utils.publishing_views import ServerPromotionView

logger = logging.getLogger(__name__)

class PublishingCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.servers_data_file = "servers_data.json"
        self.user_cooldowns_file = "user_cooldowns.json"
        self.load_servers_data()
        self.load_user_cooldowns()
        
        # Channel configurations for different server types
        self.channel_mapping = {
            "avatar": "سيرفر-افتار",  # Avatar servers channel
            "server": "سيرفر",        # General servers channel  
            "store": "متجر"          # Store servers channel
        }
        
        # Cooldown settings (1 hour = 3600 seconds)
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
        # Extract invite code from various Discord invite formats
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
            import aiohttp
            # Use Discord's public API to get invite information
            async with aiohttp.ClientSession() as session:
                # Clean the invite code to remove any extra characters
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
            # Create the main promotion embed
            embed = discord.Embed(
                title="Share Panel",
                description="اختر نوع المحتوى الذي تريد نشره\n\n**Publication Types**\n\nنشر أفتارات وصور شخصية - **Avatar**\n\nنشر رابط السيرفر - **Server**\n\nنشر منتجات ومتاجر - **Store**",
                color=0x00ff00
            )
            
            # Add server icon as thumbnail if available
            if interaction.guild.icon:
                embed.set_thumbnail(url=interaction.guild.icon.url)
            
            # Create the view with the promotion button
            view = ServerPromotionView()
            
            # Add the Qren logo as image and send message
            try:
                # Try to attach the new Qren logo file
                file_path = "qren_logo_new.png"
                if os.path.exists(file_path):
                    file = discord.File(file_path, filename="qren_logo.png")
                    embed.set_image(url="attachment://qren_logo.png")
                    # Send the message with file attachment
                    message = await channel.send(embed=embed, view=view, file=file)
                else:
                    # Fallback: send without image
                    embed.set_footer(text="Qren Share System")
                    message = await channel.send(embed=embed, view=view)
            except Exception as e:
                logger.error(f"Error attaching logo image: {e}")
                embed.set_footer(text="Qren Share System")
                # Send the message without image
                message = await channel.send(embed=embed, view=view)
            
            # Save the setup information
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
            
            # Save channel configurations
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
            logger.info(f"🔗 Processing invite link: {server_link}")
            invite_code = self.extract_server_id_from_invite(server_link)
            server_info = None
            if invite_code:
                logger.info(f"📥 Extracted invite code: {invite_code}")
                server_info = await self.get_server_info_from_invite(invite_code)
                logger.info(f"📊 Raw server info response: {server_info}")
            else:
                logger.warning(f"⚠️ Could not extract invite code from: {server_link}")
            
            # Create server promotion embed without emojis
            embed = discord.Embed(
                title="سيرفر جديد",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Different descriptions based on server type (no emojis)
            type_info = {
                "avatar": {"name": "سيرفر افتار"},
                "server": {"name": "سيرفر عام"},
                "store": {"name": "متجر"}
            }
            
            info = type_info.get(server_type, {"name": "سيرفر"})
            
            # Debug: Log server info details
            logger.info(f"🔍 Debug - Server info received: {server_info}")
            
            # Apply server information to embed if available
            if server_info:
                if server_info.get('name'):
                    logger.info(f"✅ Applying server name: {server_info['name']}")
                    embed.title = f"📢 {server_info['name']}"
                    embed.description = f"**{info['name']}**"
                else:
                    logger.warning("⚠️ Server name not found in response")
                    
                if server_info.get('icon') and server_info.get('guild_id'):
                    icon_extension = "gif" if server_info['icon'].startswith('a_') else "png"
                    icon_url = f"https://cdn.discordapp.com/icons/{server_info['guild_id']}/{server_info['icon']}.{icon_extension}?size=256"
                    logger.info(f"🖼️ Applying server icon: {icon_url}")
                    embed.set_thumbnail(url=icon_url)
                else:
                    logger.warning("⚠️ Server icon not available")
                    
                if server_info.get('member_count', 0) > 0:
                    logger.info(f"👥 Applying member count: {server_info['member_count']}")
                    embed.add_field(
                        name="عدد الأعضاء",
                        value=f"👥 {server_info['member_count']:,} عضو",
                        inline=True
                    )
                else:
                    logger.warning("⚠️ Member count not available or zero")
            else:
                logger.error(f"❌ No server info available for: {server_link}")
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
                        value="\n".join(active_cooldowns[:10]),  # Show max 10
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