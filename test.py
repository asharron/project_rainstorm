from raincloud.rainstick.BackupManager import BackupManager
from raincloud.rainstick.config import app_config

# print(app_config)
# BackupManager.create_rclone_config()
# BackupManager.create_backup_bucket()
# print(app_config['path_to_password_hash_file'])

#print(BackupManager.consolidate_backupable_files())
# BackupManager.backup_rainstorm_data()
BackupManager.get_repository_snapshots()
