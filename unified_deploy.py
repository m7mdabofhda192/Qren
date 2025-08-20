#!/usr/bin/env python3
"""
نظام تشغيل نظام Qren Discord Bot الموحد
تشغيل 24/7 مع إعادة التشغيل التلقائي والمراقبة الشاملة
"""

import os
import sys
import time
import json
import signal
import asyncio
import logging
import threading
import subprocess
from datetime import datetime, timedelta
from flask import Flask, jsonify
import psutil

# إعداد نظام السجلات
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger('UnifiedQrenBot')

class UnifiedBotDeployment:
    def __init__(self):
        self.bot_process = None
        self.start_time = datetime.now()
        self.restart_count = 0
        self.running = True
        self.flask_app = Flask(__name__)
        self.setup_routes()
        
        # إعداد معالجات إشارات النظام
        signal.signal(signal.SIGTERM, self.signal_handler)
        signal.signal(signal.SIGINT, self.signal_handler)
        
        logger.info("🌟 ═══════════════════════════════════════")
        logger.info("🚀 Unified Qren Discord Bot System")
        logger.info("🔄 24/7 Deployment Mode")
        logger.info("🛡️ Auto-Recovery Enabled")
        logger.info("🌟 ═══════════════════════════════════════")
    
    def setup_routes(self):
        """إعداد نقاط النهاية لمراقبة النظام"""
        @self.flask_app.route('/')
        def status():
            uptime = datetime.now() - self.start_time
            return jsonify({
                'status': 'running',
                'bot_status': 'active' if self.is_bot_running() else 'inactive',
                'uptime': str(uptime),
                'restart_count': self.restart_count,
                'system': 'Unified Qren Bot'
            })
        
        @self.flask_app.route('/health')
        def health():
            return jsonify({
                'healthy': True,
                'bot_running': self.is_bot_running(),
                'timestamp': datetime.now().isoformat()
            })
    
    def start_flask_server(self):
        """تشغيل خادم Flask في خيط منفصل"""
        try:
            logger.info("🌐 Keep-alive server started")
            self.flask_app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        except Exception as e:
            logger.error(f"❌ Flask server error: {e}")
    
    def is_bot_running(self):
        """فحص ما إذا كان البوت يعمل"""
        if self.bot_process is None:
            return False
        try:
            return self.bot_process.poll() is None
        except:
            return False
    
    def start_bot(self):
        """بدء تشغيل البوت الموحد"""
        try:
            if self.is_bot_running():
                logger.warning("⚠️ Bot is already running")
                return
            
            logger.info("🚀 Starting Unified Qren Bot...")
            
            # التأكد من وجود المتطلبات
            self.check_environment()
            
            # تشغيل البوت الموحد
            self.bot_process = subprocess.Popen([
                sys.executable, 'run_unified_bot.py'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
            
            # انتظار قصير للتأكد من بدء التشغيل
            time.sleep(3)
            
            if self.is_bot_running():
                logger.info("✅ Unified Qren Bot started successfully")
                return True
            else:
                logger.error("❌ Bot failed to start")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting bot: {e}")
            return False
    
    def stop_bot(self):
        """إيقاف البوت بأمان"""
        if self.bot_process:
            try:
                logger.info("🛑 Stopping Unified Qren Bot...")
                self.bot_process.terminate()
                
                # انتظار الإغلاق الطبيعي
                try:
                    self.bot_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    logger.warning("⚠️ Force killing bot process...")
                    self.bot_process.kill()
                    self.bot_process.wait()
                
                self.bot_process = None
                logger.info("✅ Bot stopped successfully")
                
            except Exception as e:
                logger.error(f"❌ Error stopping bot: {e}")
    
    def restart_bot(self):
        """إعادة تشغيل البوت"""
        logger.info("🔄 Restarting Unified Qren Bot...")
        self.stop_bot()
        time.sleep(2)
        
        if self.start_bot():
            self.restart_count += 1
            logger.info(f"✅ Bot restarted successfully (Restart #{self.restart_count})")
        else:
            logger.error("❌ Bot restart failed")
    
    def check_environment(self):
        """فحص البيئة والمتطلبات"""
        required_files = [
            'unified_qren_bot.py',
            'run_unified_bot.py',
            'config.py'
        ]
        
        for file in required_files:
            if not os.path.exists(file):
                logger.error(f"❌ Required file missing: {file}")
                raise FileNotFoundError(f"Required file missing: {file}")
        
        # فحص متغيرات البيئة
        required_env = ['DISCORD_BOT_TOKEN']
        missing_env = [env for env in required_env if not os.getenv(env)]
        
        if missing_env:
            logger.error(f"❌ Missing environment variables: {missing_env}")
            raise EnvironmentError(f"Missing environment variables: {missing_env}")
        
        logger.info("✅ Environment check passed")
    
    def monitor_bot(self):
        """مراقبة البوت وإعادة تشغيله عند الحاجة"""
        logger.info("👁️ Bot monitoring started")
        
        while self.running:
            try:
                if not self.is_bot_running():
                    logger.warning("⚠️ Bot is not running, attempting restart...")
                    self.restart_bot()
                
                # فحص استهلاك الذاكرة
                try:
                    if self.bot_process:
                        process = psutil.Process(self.bot_process.pid)
                        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                        
                        if memory_usage > 500:  # إذا تجاوز 500 ميجابايت
                            logger.warning(f"⚠️ High memory usage: {memory_usage:.1f}MB")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                time.sleep(30)  # فحص كل 30 ثانية
                
            except Exception as e:
                logger.error(f"❌ Monitor error: {e}")
                time.sleep(30)
        
        logger.info("👁️ Bot monitoring stopped")
    
    def signal_handler(self, signum, frame):
        """معالج إشارات النظام للإغلاق الآمن"""
        logger.info(f"📡 Received signal {signum}")
        self.shutdown()
    
    def shutdown(self):
        """إغلاق النظام بأمان"""
        logger.info("🛑 Shutting down deployment system...")
        self.running = False
        self.stop_bot()
        logger.info("✅ Deployment system shut down successfully")
        sys.exit(0)
    
    def run(self):
        """تشغيل النظام الكامل"""
        try:
            # بدء خادم المراقبة
            flask_thread = threading.Thread(target=self.start_flask_server, daemon=True)
            flask_thread.start()
            
            # بدء البوت
            self.start_bot()
            
            # بدء المراقبة
            self.monitor_bot()
            
        except KeyboardInterrupt:
            logger.info("🔤 KeyboardInterrupt received")
            self.shutdown()
        except Exception as e:
            logger.error(f"❌ Deployment error: {e}")
            self.shutdown()

def main():
    """نقطة دخول النظام"""
    try:
        deployment = UnifiedBotDeployment()
        deployment.run()
    except Exception as e:
        logger.error(f"❌ Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()