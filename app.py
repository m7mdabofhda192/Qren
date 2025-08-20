#!/usr/bin/env python3
"""
Alternative entry point for cloud platforms
Compatible with Heroku, Railway, and other platforms
"""

import os
import sys

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the render deployment script
try:
    from render_deploy import main
    
    if __name__ == "__main__":
        main()
        
except ImportError:
    # Fallback to unified deploy
    try:
        from unified_deploy import main
        main()
    except ImportError:
        print("❌ Error: Could not import deployment scripts")
        sys.exit(1)