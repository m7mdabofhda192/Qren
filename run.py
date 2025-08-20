#!/usr/bin/env python3
"""
Production Deployment Entry Point
Fixes GCE deployment '$file' variable issue
"""

import sys
import os
import asyncio
import logging

# Setup logging for deployment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - DEPLOY - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger('ProductionDeploy')

def main():
    """Main deployment entry point"""
    logger.info("🚀 Starting Discord Bot System for Production Deployment")
    
    # Ensure Python path is set correctly
    if '.' not in sys.path:
        sys.path.insert(0, '.')
    
    # Set environment variables for production
    os.environ['PYTHONUNBUFFERED'] = '1'
    os.environ['PYTHONPATH'] = '.'
    
    try:
        # Import and run the deployment system
        from deploy_bots import DeploymentManager
        
        # Create deployment manager
        manager = DeploymentManager()
        
        # Run the deployment
        logger.info("✅ Starting bot deployment system...")
        asyncio.run(manager.run_deployment())
        
    except KeyboardInterrupt:
        logger.info("🛑 Deployment interrupted by user")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()