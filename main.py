#!/usr/bin/env python3
"""
MAIN DEPLOYMENT ENTRY POINT
Fixes: undefined $file variable issue for Replit Deployments
"""

import sys
import os

# Ensure we can import from current directory
if '.' not in sys.path:
    sys.path.insert(0, '.')

print("🚀 Discord Bot System - Fixed Deployment Entry Point")

# Direct execution of deploy_bots.py to avoid any variable issues
if __name__ == "__main__":
    try:
        # Execute deploy_bots.py directly
        import runpy
        runpy.run_path('deploy_bots.py', run_name='__main__')
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        # Fallback: try direct import method
        try:
            exec(open('deploy_bots.py').read())
        except Exception as e2:
            print(f"❌ Fallback failed: {e2}")
            sys.exit(1)