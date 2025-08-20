import os

# Bot configuration
BOT_CONFIG = {
    'prefix': '!',
    'description': 'Avatar Bot - Share avatars with interactive buttons',
    'owner_id': None,  # Set this to your Discord user ID if needed
    'max_file_size': 10 * 1024 * 1024,  # 10MB in bytes
    'allowed_extensions': ['.png', '.jpg', '.jpeg', '.gif', '.webp'],
    'avatars_per_page': 10,
}

# Discord API limits and settings
DISCORD_CONFIG = {
    'embed_color': 0x7289DA,  # Discord blurple
    'max_embed_fields': 25,
    'max_embed_description': 4096,
    'max_message_length': 2000,
    'button_timeout': None,  # Persistent buttons
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': 'bot.log'
}

# File paths
PATHS = {
    'avatars_dir': 'avatars',
    'data_file': 'avatars_data.json',
    'log_file': 'bot.log'
}

# Rate limiting (optional - Discord handles most of this)
RATE_LIMITS = {
    'commands_per_minute': 30,
    'dm_sends_per_minute': 10,
}

# Environment variables with defaults
def get_env_var(key: str, default=None):
    """Get environment variable with optional default"""
    return os.getenv(key, default)

# Bot token from environment
DISCORD_BOT_TOKEN = get_env_var('DISCORD_BOT_TOKEN')

# Admin user IDs (comma-separated string in env var)
ADMIN_USER_IDS = []
admin_ids_str = get_env_var('ADMIN_USER_IDS', '')
if admin_ids_str:
    try:
        ADMIN_USER_IDS = [int(uid.strip()) for uid in admin_ids_str.split(',') if uid.strip()]
    except ValueError:
        pass

# Feature flags
FEATURES = {
    'auto_delete_commands': True,
    'dm_fallback_enabled': True,
    'avatar_stats_tracking': True,
    'admin_notifications': False,
}
