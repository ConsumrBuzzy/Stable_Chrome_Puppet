"""Local storage management functionality."""
from typing import Any, Dict, Optional, Union, List

class LocalStorageMixin:
    """Mixin class providing local storage management functionality."""
    
    def get_local_storage_item(self, key: str) -> Optional[str]:
        """Get an item from local storage.
        
        Args:
            key: The key of the item to get
            
        Returns:
            The value of the item or None if not found
        """
        return self.driver.execute_script(f'return window.localStorage.getItem("{key}");')
    
    def set_local_storage_item(self, key: str, value: str) -> None:
        """Set an item in local storage.
        
        Args:
            key: The key of the item to set
            value: The value to set
        """
        self.driver.execute_script(f'window.localStorage.setItem("{key}", "{value}");')
    
    def remove_local_storage_item(self, key: str) -> None:
        """Remove an item from local storage.
        
        Args:
            key: The key of the item to remove
        """
        self.driver.execute_script(f'window.localStorage.removeItem("{key}");')
    
    def clear_local_storage(self) -> None:
        """Clear all items from local storage."""
        self.driver.execute_script('window.localStorage.clear();')
    
    def get_local_storage_items(self) -> Dict[str, str]:
        """Get all items from local storage.
        
        Returns:
            Dictionary of all key-value pairs in local storage
        """
        return self.driver.execute_script(
            'const items = {}; '
            'for (let i = 0; i < localStorage.length; i++) { '
            '  const key = localStorage.key(i); '
            '  items[key] = localStorage.getItem(key); '
            '} '
            'return items;'
        )
    
    def get_local_storage_keys(self) -> List[str]:
        """Get all keys from local storage.
        
        Returns:
            List of all keys in local storage
        """
        return self.driver.execute_script(
            'const keys = []; '
            'for (let i = 0; i < localStorage.length; i++) { '
            '  keys.push(localStorage.key(i)); '
            '} '
            'return keys;'
        )
    
    def local_storage_contains_key(self, key: str) -> bool:
        """Check if a key exists in local storage.
        
        Args:
            key: The key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        return self.driver.execute_script(
            f'return localStorage.getItem("{key}") !== null;'
        )
    
    def get_local_storage_size(self) -> int:
        """Get the number of items in local storage.
        
        Returns:
            The number of items in local storage
        """
        return self.driver.execute_script('return localStorage.length;')
    
    def set_local_storage_items(self, items: Dict[str, str]) -> None:
        """Set multiple items in local storage.
        
        Args:
            items: Dictionary of key-value pairs to set
        """
        for key, value in items.items():
            self.set_local_storage_item(key, value)
    
    def get_local_storage_as_dict(self) -> Dict[str, str]:
        """Get all local storage items as a dictionary.
        
        Returns:
            Dictionary of all key-value pairs in local storage
        """
        return self.get_local_storage_items()
    
    def sync_local_storage(self, storage_dict: Dict[str, str]) -> None:
        """Synchronize local storage with the provided dictionary.
        
        This will clear the current local storage and set it to match the provided dictionary.
        
        Args:
            storage_dict: Dictionary of key-value pairs to set
        """
        self.clear_local_storage()
        self.set_local_storage_items(storage_dict)
