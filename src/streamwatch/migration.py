"""
Migration utilities for transitioning from JSON storage to SQLite database.

This module provides tools to migrate existing JSON data to the new SQLite
database format while preserving all user data and settings.
"""

import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from . import config
from .database import StreamDatabase, get_database
from .models import StreamInfo, StreamStatus

logger = logging.getLogger(config.APP_NAME + ".migration")


class MigrationError(Exception):
    """Exception raised during migration operations."""
    pass


class DataMigrator:
    """
    Handles migration from JSON storage to SQLite database.
    
    Provides safe migration with backup and rollback capabilities.
    """
    
    def __init__(self, db: Optional[StreamDatabase] = None):
        """
        Initialize migrator.
        
        Args:
            db: Database instance to use. If None, uses global instance.
        """
        self.db = db or get_database()
        self.backup_dir = Path.home() / ".config" / "streamwatch" / "migration_backup"
    
    def check_migration_needed(self) -> bool:
        """
        Check if migration from JSON to SQLite is needed.
        
        Returns:
            True if migration is needed, False otherwise
        """
        try:
            # Check if JSON files exist
            streams_file = config.STREAMS_FILE_PATH
            config_file = config.CONFIG_FILE_PATH
            
            json_exists = streams_file.exists() or config_file.exists()
            
            # Check if database has any data
            db_info = self.db.get_database_info()
            db_has_data = db_info.get("stream_count", 0) > 0
            
            # Migration needed if JSON exists and database is empty
            migration_needed = json_exists and not db_has_data
            
            logger.info(f"Migration check: JSON exists={json_exists}, DB has data={db_has_data}, Migration needed={migration_needed}")
            
            return migration_needed
            
        except Exception as e:
            logger.error(f"Failed to check migration status: {e}")
            return False
    
    def create_backup(self) -> Path:
        """
        Create backup of existing JSON files.
        
        Returns:
            Path to backup directory
        """
        try:
            # Create backup directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = self.backup_dir / f"backup_{timestamp}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup streams file
            streams_file = config.STREAMS_FILE_PATH
            if streams_file.exists():
                shutil.copy2(streams_file, backup_path / "streams.json")
                logger.info(f"Backed up streams.json to {backup_path}")

            # Backup config file
            config_file = config.CONFIG_FILE_PATH
            if config_file.exists():
                shutil.copy2(config_file, backup_path / "config.ini")
                logger.info(f"Backed up config.ini to {backup_path}")
            
            # Create backup info file
            backup_info = {
                "created_at": datetime.now().isoformat(),
                "source_files": {
                    "streams": str(streams_file) if streams_file.exists() else None,
                    "config": str(config_file) if config_file.exists() else None
                },
                "migration_version": "1.0.0"
            }
            
            with open(backup_path / "backup_info.json", "w") as f:
                json.dump(backup_info, f, indent=2)
            
            logger.info(f"Created backup at: {backup_path}")
            return backup_path
            
        except Exception as e:
            raise MigrationError(f"Failed to create backup: {e}")
    
    def migrate_streams(self) -> int:
        """
        Migrate streams from JSON to database.
        
        Returns:
            Number of streams migrated
        """
        try:
            streams_file = config.STREAMS_FILE_PATH
            if not streams_file.exists():
                logger.info("No streams.json file found, skipping stream migration")
                return 0
            
            # Load JSON data
            with open(streams_file, 'r') as f:
                json_data = json.load(f)
            
            if not isinstance(json_data, list):
                logger.warning("Invalid streams.json format, expected list")
                return 0
            
            migrated_count = 0
            
            for stream_data in json_data:
                try:
                    # Use the enhanced StreamInfo.from_dict method for migration
                    stream = StreamInfo.from_dict(stream_data)
                    
                    # Save to database
                    self.db.save_stream(stream)
                    migrated_count += 1
                    
                    logger.debug(f"Migrated stream: {stream.alias}")
                    
                except Exception as e:
                    logger.warning(f"Failed to migrate stream {stream_data.get('url', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully migrated {migrated_count} streams")
            return migrated_count
            
        except Exception as e:
            raise MigrationError(f"Failed to migrate streams: {e}")
    
    def migrate_config(self) -> int:
        """
        Migrate configuration from INI to database.
        
        Returns:
            Number of config values migrated
        """
        try:
            config_file = config.CONFIG_FILE_PATH
            if not config_file.exists():
                logger.info("No config.ini file found, skipping config migration")
                return 0
            
            # Import configparser here to avoid dependency issues
            import configparser
            
            config_parser = configparser.ConfigParser()
            config_parser.read(config_file)
            
            migrated_count = 0
            
            for section_name in config_parser.sections():
                for key, value in config_parser[section_name].items():
                    try:
                        # Create a namespaced key
                        db_key = f"{section_name.lower()}.{key}"
                        
                        # Try to determine the correct data type
                        migrated_value = self._convert_config_value(value)
                        
                        # Save to database
                        self.db.save_config_value(
                            db_key, 
                            migrated_value, 
                            f"Migrated from [{section_name}] {key}"
                        )
                        
                        migrated_count += 1
                        logger.debug(f"Migrated config: {db_key} = {migrated_value}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to migrate config {section_name}.{key}: {e}")
                        continue
            
            logger.info(f"Successfully migrated {migrated_count} config values")
            return migrated_count
            
        except Exception as e:
            raise MigrationError(f"Failed to migrate config: {e}")
    
    def _convert_config_value(self, value: str) -> Any:
        """
        Convert string config value to appropriate Python type.
        
        Args:
            value: String value from INI file
            
        Returns:
            Converted value with appropriate type
        """
        # Try boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Try integer
        try:
            return int(value)
        except ValueError:
            pass
        
        # Try float
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def perform_migration(self, create_backup: bool = True) -> Dict[str, Any]:
        """
        Perform complete migration from JSON to SQLite.
        
        Args:
            create_backup: Whether to create backup before migration
            
        Returns:
            Migration results summary
        """
        try:
            logger.info("Starting migration from JSON to SQLite")
            
            # Check if migration is needed
            if not self.check_migration_needed():
                logger.info("Migration not needed")
                return {
                    "success": True,
                    "message": "Migration not needed",
                    "streams_migrated": 0,
                    "config_migrated": 0,
                    "backup_path": None
                }
            
            backup_path = None
            if create_backup:
                backup_path = self.create_backup()
            
            # Perform migrations
            streams_migrated = self.migrate_streams()
            config_migrated = self.migrate_config()
            
            # Verify migration
            db_info = self.db.get_database_info()
            
            result = {
                "success": True,
                "message": f"Migration completed successfully",
                "streams_migrated": streams_migrated,
                "config_migrated": config_migrated,
                "backup_path": str(backup_path) if backup_path else None,
                "database_info": db_info
            }
            
            logger.info(f"Migration completed: {streams_migrated} streams, {config_migrated} config values")
            return result
            
        except Exception as e:
            logger.error(f"Migration failed: {e}")
            return {
                "success": False,
                "message": f"Migration failed: {e}",
                "streams_migrated": 0,
                "config_migrated": 0,
                "backup_path": str(backup_path) if 'backup_path' in locals() and backup_path else None
            }
    
    def rollback_migration(self, backup_path: Path) -> bool:
        """
        Rollback migration by restoring from backup.
        
        Args:
            backup_path: Path to backup directory
            
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            if not backup_path.exists():
                logger.error(f"Backup path does not exist: {backup_path}")
                return False
            
            # Restore streams file
            backup_streams = backup_path / "streams.json"
            if backup_streams.exists():
                streams_file = config.STREAMS_FILE_PATH
                shutil.copy2(backup_streams, streams_file)
                logger.info(f"Restored streams.json from backup")

            # Restore config file
            backup_config = backup_path / "config.ini"
            if backup_config.exists():
                config_file = config.CONFIG_FILE_PATH
                shutil.copy2(backup_config, config_file)
                logger.info(f"Restored config.ini from backup")
            
            logger.info(f"Rollback completed from backup: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False


def migrate_to_database(create_backup: bool = True) -> Dict[str, Any]:
    """
    Convenience function to perform migration to SQLite database.
    
    Args:
        create_backup: Whether to create backup before migration
        
    Returns:
        Migration results summary
    """
    migrator = DataMigrator()
    return migrator.perform_migration(create_backup=create_backup)


def check_migration_status() -> Dict[str, Any]:
    """
    Check current migration status.
    
    Returns:
        Dictionary with migration status information
    """
    try:
        migrator = DataMigrator()
        
        # Check files
        streams_file = config.STREAMS_FILE_PATH
        config_file = config.CONFIG_FILE_PATH
        
        # Check database
        db_info = migrator.db.get_database_info()
        
        return {
            "json_files": {
                "streams_exists": streams_file.exists(),
                "config_exists": config_file.exists(),
                "streams_path": str(streams_file),
                "config_path": str(config_file)
            },
            "database": db_info,
            "migration_needed": migrator.check_migration_needed(),
            "backup_directory": str(migrator.backup_dir)
        }
        
    except Exception as e:
        logger.error(f"Failed to check migration status: {e}")
        return {"error": str(e)}
