#!/usr/bin/env python3
"""
Render Deployment Script for Unified Qren Bot
Optimized for Render.com hosting platform
"""

import os
import sys
import time
import logging
import asyncio
import signal
from flask import Flask, jsonify
from threading import Thread
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('RenderDeploy')

# Import the unified bot
try:
    from unified_qren_bot import UnifiedQrenBot
except ImportError as e:
    logger.error(f"❌ Failed to import bot: {e}")
    sys.exit(1)

# Flask app for health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    """Health check endpoint for Render"""
    return jsonify({
        "status": "healthy",
        "bot": "Unified Qren Bot",
        "platform": "Render",
        "timestamp": time.time()
    })

@app.route('/status')
def bot_status():
    """Bot status endpoint"""
    return jsonify({
        "bot_running": bot_instance is not None,
        "platform": "Render",
        "uptime": time.time() - start_time if 'start_time' in globals() else 0
    })

# Global variables
bot_instance = None
start_time = time.time()
shutdown_requested = False

def run_flask():
    """Run Flask app in a separate thread"""
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global shutdown_requested
    logger.info(f"🛑 Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True
    
    if bot_instance:
        try:
            asyncio.create_task(bot_instance.close())
        except:
            pass
    
    sys.exit(0)

async def run_bot():
    """Run the unified bot"""
    global bot_instance
    
    try:
        # Check for required environment variables
        token = os.getenv('DISCORD_BOT_TOKEN')
        if not token:
            logger.error("❌ DISCORD_BOT_TOKEN environment variable is required")
            return False
        
        logger.info("🚀 Starting Unified Qren Bot for Render...")
        
        # Create and start bot
        bot_instance = UnifiedQrenBot()
        await bot_instance.start(token)
        
    except Exception as e:
        logger.error(f"❌ Error running bot: {e}")
        return False
    
    return True

def main():
    """Main function for Render deployment"""
    global start_time
    start_time = time.time()
    
    # Set up signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    logger.info("🌟 ═══════════════════════════════════════")
    logger.info("🚀 Unified Qren Bot - Render Deployment")
    logger.info("🌐 Starting health check server...")
    logger.info("🌟 ═══════════════════════════════════════")
    
    # Start Flask app in background thread
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Wait a moment for Flask to start
    time.sleep(2)
    
    # Run the bot
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    finally:
        logger.info("🔄 Bot deployment ended")

if __name__ == "__main__":
    main()