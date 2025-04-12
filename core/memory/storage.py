import os
import json
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

class StorageManager:
    """
    Manages persistent storage of data for the agent.
    """
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.base_dir = os.path.join("workspace", session_id)
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Initialized storage manager for session {session_id}")
    
    def save_data(self, data: Dict, filename: str) -> bool:
        """
        Save data to a JSON file.
        
        Args:
            data: Dictionary data to save
            filename: Name of the file (without extension)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = os.path.join(self.base_dir, f"{filename}.json")
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving data to {filename}: {str(e)}")
            return False
    
 def load_data(self, filename: str) -> Optional[Dict]:
        """
        Load data from a JSON file.
        
        Args:
            filename: Name of the file (without extension)
        
        Returns:
            Dictionary data if successful, None otherwise
        """
        try:
            filepath = os.path.join(self.base_dir, f"{filename}.json")
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data from {filename}: {str(e)}")
            return None
    
    def save_text(self, text: str, filename: str) -> bool:
        """
        Save text to a file.
        
        Args:
            text: Text to save
            filename: Name of the file (without extension)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            filepath = os.path.join(self.base_dir, f"{filename}.txt")
            with open(filepath, 'w') as f:
                f.write(text)
            return True
        except Exception as e:
            logger.error(f"Error saving text to {filename}: {str(e)}")
            return False
    
    def load_text(self, filename: str) -> Optional[str]:
        """
        Load text from a file.
        
        Args:
            filename: Name of the file (without extension)
        
        Returns:
            Text if successful, None otherwise
        """
        try:
            filepath = os.path.join(self.base_dir, f"{filename}.txt")
            if not os.path.exists(filepath):
                return None
                
            with open(filepath, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error loading text from {filename}: {str(e)}")
            return None
    
    def list_files(self, extension: Optional[str] = None) -> List[str]:
        """
        List files in the storage directory.
        
        Args:
            extension: Optional file extension filter (without dot)
        
        Returns:
            List of filenames
        """
        try:
            files = os.listdir(self.base_dir)
            if extension:
                return [f for f in files if f.endswith(f".{extension}")]
            return files
        except Exception as e:
            logger.error(f"Error listing files: {str(e)}")
            return []