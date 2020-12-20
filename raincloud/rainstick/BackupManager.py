import os
from raincloud.rainstick.config import app_config


class BackupManager:
    api_key = "13Yqe8kt2jcT11GoLtcKnQxgAbtYu9JLiffZ3dw1w4D3oTH8Ts7Rq7jhQ9YLfGnuW9VbZ9B227cTKkuBURjadmEPW7bLUVHzHdtfHdS"
    access_grant = "14zZEdH4uEZwjbd4fKNHZffoWy5AW8jrFkJF9Sxd5PHH9EtjxEGjX99Zf6u4EGAaCacfHnqyXjJuvBDgATSziN9i4yr6LszLgJcTK5mz5hjuzviBBap4KinhWYpgd3sw1sE4skEVLMQtKkXUVFC8C5pY6gaCXdGyjJApzVikuY9Cs1HAi7gDNSrDH5GNtD2ZU1aYKoKRHwYmpAhMpw7uBg5oB7dbDUA2qFbSB8ajEEmBfHx3PhxpSQdAUnVuB1RDnXEeJjRPUzf8VJKr9P"
    satellite_address = "13EayRS2V1kEsWESU9QMRseFhdxYxKicsiFmxrsLZHeLUtdps3S@us-central-1.tardigrade.io:7777"

    @staticmethod
    def create_rclone_config():
        backup_command = "rclone config create rainstorm tardigrade access_grant {}" \
            .format(BackupManager.access_grant)
        os.system(backup_command)

    @staticmethod
    def create_backup_bucket():
        if not app_config['path_to_password_hash_file']:
            print("Config is missing the path to password hash file. Aborting backups bucket creation.")
            return False

        # TODO: Handle repository master key and config already initialized
        try:
            os.system("rclone mkdir rainstorm:backups")
            os.system("restic -r rclone:rainstorm:backups init --password-file {}"
                      .format(app_config['path_to_password_hash_file']))
        except OSError as error:
            print("Could not create backups bucket. Error: ", error)
            return False

        return True

    @staticmethod
    def backup_rainstorm_data():
        # TODO: Find the folders that need backing up
        # TODO: The folders that need backing up can be toggled per service
        # TODO: Backup those folders
        # TODO: Keep track of where those folders go on the FS
        # TODO: Restore from a backup
        pass

    @staticmethod
    def get_user_password_hash():
        password_hash = ""

        try:
            with open(app_config.path_to_password_hash_file, "r") as hash_file:
                password_hash = hash_file.readline()
        except Exception as error:
            print("An error occurred while opening the password hash file: ", error)

        return password_hash
