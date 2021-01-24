from raincloud.rainstick.BackupManager import BackupManager
from raincloud.rainstick.config import app_config

# print(app_config)
# BackupManager.create_rclone_config()
# BackupManager.create_restic_repo()
# print(app_config['path_to_password_hash_file'])

# print(BackupManager.consolidate_backupable_files())
# BackupManager.create_restic_repo_for_service("plex")
# BackupManager.backup_all_services()
# print(BackupManager.get_backupable_service_paths())
# print(BackupManager.get_available_backups())
# BackupManager.restore_from_backup('39239fcd')
# print(BackupManager.get_available_backups_for_all_services())
# print(BackupManager.get_available_backups_for_service('transmission'))
# BackupManager.restore_service_from_backup('transmission', 'fe8b3a89')
BackupManager.backup_service("transmission")