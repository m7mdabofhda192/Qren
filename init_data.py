#!/usr/bin/env python3
"""
Initialize data files for first deployment
Creates empty JSON files if they don't exist
"""

import json
import os

def create_empty_data_files():
    """Create empty data files for bot initialization"""
    
    data_files = {
        'avatars_data.json': {},
        'user_cooldowns.json': {},
        'tags_data.json': {},
        'servers_data.json': {},
        'search_cooldowns.json': {},
        'control_panel_data.json': {}
    }
    
    for filename, default_data in data_files.items():
        if not os.path.exists(filename):
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(default_data, f, ensure_ascii=False, indent=2)
            print(f"✅ Created {filename}")
        else:
            print(f"📁 {filename} already exists")
    
    # Create avatars directory if it doesn't exist
    if not os.path.exists('avatars'):
        os.makedirs('avatars')
        print("✅ Created avatars/ directory")
    else:
        print("📁 avatars/ directory already exists")

if __name__ == "__main__":
    print("🚀 Initializing data files for deployment...")
    create_empty_data_files()
    print("✅ Data initialization complete!")