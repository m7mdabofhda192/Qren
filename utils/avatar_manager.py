import json
import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class AvatarManager:
    def __init__(self, data_file="avatars_data.json"):
        self.data_file = data_file
        self.avatars = self._load_data()
        
        # Create avatars directory if it doesn't exist
        os.makedirs("avatars", exist_ok=True)
    
    def _load_data(self) -> Dict:
        """Load avatars data from JSON file"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading avatars data: {e}")
            return {}
    
    def _save_data(self):
        """Save avatars data to JSON file"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.avatars, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving avatars data: {e}")
    
    def add_avatar(self, avatar_info: Dict):
        """Add a new avatar to the collection"""
        try:
            avatar_name = avatar_info['name']
            self.avatars[avatar_name] = avatar_info
            self._save_data()
            logger.info(f"Avatar '{avatar_name}' added to collection")
        except Exception as e:
            logger.error(f"Error adding avatar: {e}")
            raise
    
    def get_avatar(self, avatar_name: str) -> Optional[Dict]:
        """Get avatar information by name"""
        return self.avatars.get(avatar_name)
    
    def remove_avatar(self, avatar_name: str) -> bool:
        """Remove an avatar from the collection"""
        try:
            if avatar_name in self.avatars:
                del self.avatars[avatar_name]
                self._save_data()
                logger.info(f"Avatar '{avatar_name}' removed from collection")
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing avatar: {e}")
            return False
    
    def list_avatars(self) -> List[Dict]:
        """Get list of all avatars"""
        return list(self.avatars.values())
    
    def avatar_exists(self, avatar_name: str) -> bool:
        """Check if an avatar exists"""
        return avatar_name in self.avatars
    
    def get_avatar_count(self) -> int:
        """Get total number of avatars"""
        return len(self.avatars)
    
    def search_avatars(self, query: str) -> List[Dict]:
        """Search avatars by name"""
        query = query.lower()
        return [
            avatar for avatar in self.avatars.values()
            if query in avatar['name'].lower()
        ]
