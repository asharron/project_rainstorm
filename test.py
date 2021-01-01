from raincloud.rainstick.BackupManager import BackupManager
from raincloud.rainstick.config import app_config

# print(app_config)
# BackupManager.create_rclone_config()
# BackupManager.create_backup_bucket()

print(BackupManager.get_backupable_service_paths())
