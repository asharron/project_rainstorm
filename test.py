from raincloud.rainstick.BackupManager import BackupManager
from raincloud.rainstick.config import app_config

# print(app_config)
BackupManager.create_rclone_config()
BackupManager.create_backup_bucket()
