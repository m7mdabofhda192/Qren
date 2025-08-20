import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

class BotStatusView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(
        label="تحديث الحالة",
        style=discord.ButtonStyle.primary,
        emoji="🔄"
    )
    async def refresh_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            guild = interaction.guild
            if not guild:
                await interaction.response.send_message("❌ خطأ في الوصول للسيرفر", ephemeral=True)
                return

            embed = discord.Embed(
                title="🤖 حالة البوتات",
                description="حالة جميع بوتات النظام",
                color=0x00ff00,
                timestamp=datetime.now()
            )

            # Check bot statuses
            bot_info = [
                ("🖼️ بوت الأفتار", "Qren Avatar", "متصل ويعمل"),
                ("🎛️ بوت التحكم", "Qren Control", "متصل ويعمل"),
                ("⚙️ بوت الكونسول", "Qren Console", "متصل ويعمل"),
                ("📢 بوت النشر", "Qren Share", "متصل ويعمل")
            ]

            for name, bot_name, status in bot_info:
                embed.add_field(
                    name=name,
                    value=f"**الاسم:** {bot_name}\n**الحالة:** ✅ {status}",
                    inline=True
                )

            embed.set_footer(text="آخر تحديث")
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            logger.error(f"Error refreshing bot status: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء تحديث الحالة", ephemeral=True)

class SystemToolsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.select(
        placeholder="اختر أداة النظام...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="إعداد بوت الأفتار",
                description="إعداد نظام مشاركة الأفتارات",
                emoji="🖼️",
                value="avatar_setup"
            ),
            discord.SelectOption(
                label="إعداد بوت النشر",
                description="إعداد نظام نشر السيرفرات",
                emoji="📢",
                value="publishing_setup"
            ),
            discord.SelectOption(
                label="إعداد بوت الكونسول",
                description="إعداد النظام الإداري",
                emoji="⚙️",
                value="console_setup"
            ),
            discord.SelectOption(
                label="مراقبة النظام",
                description="عرض سجلات وحالة النظام",
                emoji="📊",
                value="system_monitor"
            )
        ]
    )
    async def select_tool(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            selected = select.values[0]
            
            embeds = {
                "avatar_setup": discord.Embed(
                    title="🖼️ إعداد بوت الأفتار",
                    description="لإعداد بوت الأفتار، استخدم الأوامر التالية:",
                    color=0xff9900
                ).add_field(
                    name="الأوامر المتاحة",
                    value="`/upload_avatar` - رفع أفتار جديد\n`/list_avatars` - عرض جميع الأفتارات\n`/delete_avatar` - حذف أفتار",
                    inline=False
                ),
                
                "publishing_setup": discord.Embed(
                    title="📢 إعداد بوت النشر",
                    description="لإعداد نظام نشر السيرفرات:",
                    color=0x00ff00
                ).add_field(
                    name="خطوات الإعداد",
                    value="`/setup_promotion` - إعداد قائمة النشر\n`/setup_channels` - إعداد قنوات التصنيف",
                    inline=False
                ),
                
                "console_setup": discord.Embed(
                    title="⚙️ إعداد بوت الكونسول",
                    description="النظام الإداري للسيرفر:",
                    color=0xff0000
                ).add_field(
                    name="الأوامر الإدارية",
                    value="`/ban` - حظر عضو\n`/kick` - طرد عضو\n`/clear` - حذف رسائل",
                    inline=False
                ),
                
                "system_monitor": discord.Embed(
                    title="📊 مراقبة النظام",
                    description="حالة النظام ممتازة ✅",
                    color=0x00ff00
                ).add_field(
                    name="الإحصائيات",
                    value="• جميع البوتات متصلة\n• النظام يعمل بشكل طبيعي\n• لا توجد أخطاء",
                    inline=False
                )
            }
            
            embed = embeds.get(selected, discord.Embed(title="❌ خيار غير معروف", color=0xff0000))
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in tool selection: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء اختيار الأداة", ephemeral=True)

class UserInputModal(discord.ui.Modal):
    def __init__(self, action_type: str):
        super().__init__(title=f"إدخال معرف المستخدم - {action_type}")
        self.action_type = action_type

    user_input = discord.ui.TextInput(
        label='معرف المستخدم أو الاسم',
        placeholder='اكتب معرف المستخدم أو اسمه هنا...',
        required=True,
        max_length=100
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            user_identifier = self.user_input.value.strip()
            
            # Try to find the user
            user = None
            if user_identifier.isdigit():
                # If it's a digit, try to get user by ID
                try:
                    user = await interaction.client.fetch_user(int(user_identifier))
                except:
                    pass
            
            if not user and interaction.guild:
                # Try to find by name in guild
                for member in interaction.guild.members:
                    if (member.name.lower() == user_identifier.lower() or 
                        member.display_name.lower() == user_identifier.lower()):
                        user = member
                        break
            
            if not user:
                await interaction.response.send_message("❌ لم يتم العثور على المستخدم", ephemeral=True)
                return

            await interaction.response.defer(ephemeral=True)
            
            if self.action_type == "avatar":
                await self.get_user_avatar(interaction, user)
            elif self.action_type == "banner":
                await self.get_user_banner(interaction, user)
                
        except Exception as e:
            logger.error(f"Error in user input modal: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ حدث خطأ أثناء معالجة الطلب", ephemeral=True)
            else:
                await interaction.followup.send("❌ حدث خطأ أثناء معالجة الطلب", ephemeral=True)

    async def get_user_avatar(self, interaction: discord.Interaction, user):
        try:
            embed = discord.Embed(
                title=f"🖼️ أفتار {user.display_name}",
                color=0x00ff00
            )
            
            if user.avatar:
                embed.set_image(url=user.avatar.url)
                embed.add_field(
                    name="🔗 رابط التحميل",
                    value=f"[تحميل الأفتار]({user.avatar.url})",
                    inline=False
                )
            else:
                embed.description = "هذا المستخدم لا يملك أفتار مخصص"
            
            embed.set_footer(text=f"معرف المستخدم: {user.id}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting user avatar: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء جلب الأفتار", ephemeral=True)

    async def get_user_banner(self, interaction: discord.Interaction, user):
        try:
            # Fetch full user to get banner
            full_user = await interaction.client.fetch_user(user.id)
            
            embed = discord.Embed(
                title=f"🏷️ بنر {user.display_name}",
                color=0x0099ff
            )
            
            if full_user.banner:
                embed.set_image(url=full_user.banner.url)
                embed.add_field(
                    name="🔗 رابط التحميل",
                    value=f"[تحميل البنر]({full_user.banner.url})",
                    inline=False
                )
            else:
                embed.description = "هذا المستخدم لا يملك بنر مخصص"
            
            embed.set_footer(text=f"معرف المستخدم: {user.id}")
            await interaction.followup.send(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error getting user banner: {e}")
            await interaction.followup.send("❌ حدث خطأ أثناء جلب البنر", ephemeral=True)

class DownloadModal(discord.ui.Modal, title='تحميل مقطع أو ملف صوتي'):
    def __init__(self):
        super().__init__()

    url_input = discord.ui.TextInput(
        label='رابط المقطع أو الصوت',
        placeholder='ضع رابط YouTube، SoundCloud، أو أي رابط آخر...',
        required=True,
        max_length=500
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            url = self.url_input.value.strip()
            
            embed = discord.Embed(
                title="⬇️ طلب التحميل",
                description="تم استلام طلب التحميل",
                color=0xff9900
            )
            
            embed.add_field(
                name="🔗 الرابط المطلوب",
                value=f"```{url}```",
                inline=False
            )
            
            embed.add_field(
                name="ℹ️ ملاحظة",
                value="هذه الميزة قيد التطوير حالياً. سيتم إضافة نظام التحميل قريباً.",
                inline=False
            )
            
            embed.set_footer(text="قيد التطوير")
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error in download modal: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء معالجة طلب التحميل", ephemeral=True)

class ControlPanelView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.select(
        placeholder="اختر من القائمة...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Avatar",
                description="الحصول على أفتار مستخدم معين",
                value="avatar"
            ),
            discord.SelectOption(
                label="Banner",
                description="الحصول على بنر مستخدم معين",
                value="banner"
            ),
            discord.SelectOption(
                label="Download",
                description="تحميل مقطع أو ملف صوتي",
                value="download"  
            ),
            discord.SelectOption(
                label="Boost",
                description="معرفة حالة التطوير",
                value="boost"
            ),
            discord.SelectOption(
                label="Nitro",
                description="معرفة حالة التطوير",
                value="nitro"
            )
        ],
        row=0
    )
    async def control_menu(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            selected = select.values[0]
            
            if selected == "avatar":
                modal = UserInputModal("avatar")
                await interaction.response.send_modal(modal)
                
            elif selected == "banner":
                modal = UserInputModal("banner")
                await interaction.response.send_modal(modal)
                
            elif selected == "download":
                modal = DownloadModal()
                await interaction.response.send_modal(modal)
                
            elif selected == "boost":
                embed = discord.Embed(
                    title="📝 حالة التطوير - البوست",
                    description="معلومات حول تطوير إشارة البوست الخاصة بك",
                    color=0x0099ff
                )
                
                embed.add_field(
                    name="📊 الحالة الحالية",
                    value="> 🔄 قيد التطوير\n> 📅 مخطط للإصدار القادم\n> 🛠️ في مرحلة التصميم",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 الميزات المخططة",
                    value="> • فحص حالة البوست للمستخدمين\n> • عرض إشارات البوست\n> • إحصائيات البوست في السيرفر\n> • إشعارات البوست",
                    inline=False
                )
                
                embed.set_footer(text="قيد التطوير • متوقع قريباً")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
            elif selected == "nitro":
                embed = discord.Embed(
                    title="💎 حالة التطوير - النيترو",
                    description="معلومات حول تطوير ميزة النيترو",
                    color=0x9932cc
                )
                
                embed.add_field(
                    name="📊 الحالة الحالية", 
                    value="> 🔄 قيد التطوير\n> 📅 مخطط للإصدار القادم\n> 🛠️ في مرحلة التخطيط",
                    inline=False
                )
                
                embed.add_field(
                    name="🎯 الميزات المخططة",
                    value="> • فحص حالة النيترو للمستخدمين\n> • عرض مزايا النيترو\n> • إحصائيات النيترو في السيرفر\n> • إشعارات النيترو",
                    inline=False
                )
                
                embed.set_footer(text="قيد التطوير • متوقع قريباً")
                await interaction.response.send_message(embed=embed, ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in control menu selection: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء معالجة الطلب", ephemeral=True)

