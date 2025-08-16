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
from typing import Any, Dict, List, Optional

from . import config
from .database import StreamDatabase, get_database
from .models import StreamInfo, StreamStatus
from .stream_utils import parse_url_metadata

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
                    "config": str(config_file) if config_file.exists() else None,
                },
                "migration_version": "1.0.0",
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
            with open(streams_file, "r") as f:
                json_data = json.load(f)

            if not isinstance(json_data, list):
                logger.warning("Invalid streams.json format, expected list")
                return 0

            migrated_count = 0

            for stream_data in json_data:
                try:
                    url = stream_data["url"]
                    alias = stream_data["alias"]

                    # --- INTELLIGENT PARSING STEP ---
                    # Parse the URL to get the correct platform and username
                    parsed_info = parse_url_metadata(url)
                    platform = parsed_info.get("platform", "Unknown")
                    username = parsed_info.get("username", "unknown_stream")

                    # Create a complete, validated StreamInfo object with correct data
                    stream = StreamInfo(
                        url=url, alias=alias, platform=platform, username=username
                    )

                    # Save the CORRECT object to the database
                    self.db.save_stream(stream)
                    migrated_count += 1

                    logger.debug(f"Migrated stream: {stream.alias}")

                except Exception as e:
                    logger.warning(
                        f"Failed to migrate stream {stream_data.get('url', 'unknown')}: {e}"
                    )
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
                            f"Migrated from [{section_name}] {key}",
                        )

                        migrated_count += 1
                        logger.debug(f"Migrated config: {db_key} = {migrated_value}")

                    except Exception as e:
                        logger.warning(
                            f"Failed to migrate config {section_name}.{key}: {e}"
                        )
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
        if value.lower() in ("true", "false"):
            return value.lower() == "true"

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
        Perform complete migration from JSON to SQLite, checking for required migrations internally.
        """
        try:
            logger.info("Checking for necessary data migrations...")

            streams_migrated = 0
            config_migrated = 0
            backup_path = None

            # Check if streams.json exists and the database has no streams
            streams_file_exists = config.STREAMS_FILE_PATH.exists()
            db_has_streams = self.db.get_database_info().get("stream_count", 0) > 0

            if streams_file_exists and not db_has_streams:
                logger.info("Migration for streams.json is needed.")
                if create_backup and not backup_path:
                    backup_path = self.create_backup()

                streams_migrated = self.migrate_streams()

            # For simplicity, we can assume config needs migration if streams did, or if the db is empty
            config_file_exists = config.CONFIG_FILE_PATH.exists()
            if config_file_exists and (streams_migrated > 0 or not db_has_streams):
                logger.info("Migration for config.ini is needed.")
                if create_backup and not backup_path:
                    backup_path = self.create_backup()

                config_migrated = self.migrate_config()

            if streams_migrated == 0 and config_migrated == 0:
                logger.info("No data migration was needed.")
                return {"success": True, "message": "Migration not needed."}

            result = {
                "success": True,
                "message": "Migration completed successfully",
                "streams_migrated": streams_migrated,
                "config_migrated": config_migrated,
                "backup_path": str(backup_path) if backup_path else None,
            }

            logger.info(
                f"Migration finished: {streams_migrated} streams, {config_migrated} config values"
            )
            return result

        except Exception as e:
            logger.error(f"Migration failed: {e}", exc_info=True)
            return {"success": False, "message": f"Migration failed: {e}"}

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
                "config_path": str(config_file),
            },
            "database": db_info,
            "migration_needed": migrator.check_migration_needed(),
            "backup_directory": str(migrator.backup_dir),
        }

    except Exception as e:
        logger.error(f"Failed to check migration status: {e}")
        return {"error": str(e)}
