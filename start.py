#!/usr/bin/env python3
"""
Main startup script for Replit Deployments
Addresses the undefined $file variable issue by providing a clear entry point
"""

import os
import sys
import asyncio
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging for deployment environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

logger = logging.getLogger(__name__)

async def main():
    """Main entry point for deployment"""
    try:
        logger.info("🚀 Starting Discord Bot Deployment System")
        logger.info("📂 Working directory: %s", os.getcwd())
        logger.info("🐍 Python version: %s", sys.version)
        
        # Import and run the deployment system
        from deploy_bots import DeploymentManager
        
        manager = DeploymentManager()
        await manager.run_deployment()
        
    except Exception as e:
        logger.error("❌ Deployment failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Deployment stopped by user")
    except Exception as e:
        logger.error("💥 Fatal error: %s", e)
        sys.exit(1)