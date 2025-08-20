import discord
from discord.ext import commands
import logging
import asyncio

logger = logging.getLogger(__name__)

class ServerLinkModal(discord.ui.Modal, title='إدخال رابط السيرفر'):
    def __init__(self, server_type: str):
        super().__init__()
        self.server_type = server_type

    server_link = discord.ui.TextInput(
        label='رابط السيرفر',
        placeholder='https://discord.gg/example',
        required=True,
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            # Validate Discord invite link
            link = self.server_link.value.strip()
            if not (link.startswith('https://discord.gg/') or link.startswith('https://discord.com/invite/')):
                await interaction.response.send_message("❌ يجب أن يكون الرابط رابط دعوة ديسكورد صحيح", ephemeral=True)
                return

            # Defer the response since we'll use followup
            await interaction.response.defer(ephemeral=True)
            
            # Get the publishing commands cog
            bot = interaction.client
            if hasattr(bot, 'get_cog'):
                publishing_cog = bot.get_cog('PublishingCommands')
                if publishing_cog:
                    await publishing_cog.publish_server(interaction, link, self.server_type)
                else:
                    await interaction.followup.send("❌ نظام النشر غير متاح حالياً", ephemeral=True)
            else:
                await interaction.followup.send("❌ نظام النشر غير متاح حالياً", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error in server link modal: {e}")
            if not interaction.response.is_done():
                await interaction.response.send_message("❌ حدث خطأ أثناء معالجة الطلب", ephemeral=True)
            else:
                await interaction.followup.send("❌ حدث خطأ أثناء معالجة الطلب", ephemeral=True)



class ServerPromotionView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)  # Persistent view

    @discord.ui.select(
        placeholder="اختر من القائمة...",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(
                label="Avatar",
                description="نشر أفتارات وصور شخصية",
                value="avatar"
            ),
            discord.SelectOption(
                label="Server",
                description="نشر رابط السيرفر",
                value="server"
            ),
            discord.SelectOption(
                label="Store",
                description="نشر منتجات ومتاجر",
                value="store"
            )
        ]
    )
    async def select_server_type(self, interaction: discord.Interaction, select: discord.ui.Select):
        try:
            server_type = select.values[0]
            
            # Show the server link modal directly
            modal = ServerLinkModal(server_type)
            await interaction.response.send_modal(modal)
            
        except Exception as e:
            logger.error(f"Error in server type selection: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء اختيار النوع", ephemeral=True)

class AdminControlView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="إحصائيات",
        style=discord.ButtonStyle.primary,
        emoji="📊"
    )
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.manage_guild:
                await interaction.response.send_message("❌ هذا الزر متاح للإداريين فقط", ephemeral=True)
                return
            
            # Get the publishing commands cog
            bot = interaction.client
            if hasattr(bot, 'get_cog'):
                publishing_cog = bot.get_cog('PublishingCommands')
                if publishing_cog:
                    await publishing_cog.server_stats(interaction)
                else:
                    await interaction.response.send_message("❌ نظام الإحصائيات غير متاح حالياً", ephemeral=True)
            else:
                await interaction.response.send_message("❌ نظام الإحصائيات غير متاح حالياً", ephemeral=True)
                
        except Exception as e:
            logger.error(f"Error showing stats: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء عرض الإحصائيات", ephemeral=True)

    @discord.ui.button(
        label="إعدادات",
        style=discord.ButtonStyle.secondary,
        emoji="⚙️"
    )
    async def show_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if not interaction.guild or not isinstance(interaction.user, discord.Member) or not interaction.user.guild_permissions.administrator:
                await interaction.response.send_message("❌ هذا الزر متاح للإداريين فقط", ephemeral=True)
                return
            
            embed = discord.Embed(
                title="⚙️ إعدادات نظام النشر",
                description="استخدم الأوامر التالية لإعداد النظام:",
                color=0xff9900
            )
            embed.add_field(
                name="/setup_promotion",
                value="إعداد قائمة نشر السيرفرات",
                inline=False
            )
            embed.add_field(
                name="/setup_channels", 
                value="إعداد قنوات النشر حسب النوع",
                inline=False
            )
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
            
        except Exception as e:
            logger.error(f"Error showing settings: {e}")
            await interaction.response.send_message("❌ حدث خطأ أثناء عرض الإعدادات", ephemeral=True)