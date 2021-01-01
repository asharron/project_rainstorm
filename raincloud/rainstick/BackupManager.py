import os
import yaml
from raincloud.rainstick.config import app_config
from raincloud.rainstick.Log import Log

logger = Log.get_logger()


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
        # TODO: Backup will be rainstorm's account, so the bucket will be for all users, not just one
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
        # TODO: Find the folders that need backing up | use the settings.yml file for each service to see if is backupable
        # TODO: Can toggle backups for each service
        # TODO: Backup those folders
        # TODO: Ensure the
        # TODO: Keep track of where those folders go on the FS
        # TODO: Restore from a backup
        pass

    @staticmethod
    def get_backupable_service_paths():
        backup_enabled_service_data_paths = []
        services_apps_path = "/mnt/usb/apps"
        service_names = os.listdir(services_apps_path)
        for service_name in service_names:
            service_data_path = "{}/{}".format(services_apps_path, service_name)
            service_settings_file_path = "{}/settings.yml".format(service_data_path)
            try:
                with open(service_settings_file_path, 'r') as settings_file:
                    service_settings = yaml.safe_load(settings_file)
                service_has_backup_enabled = service_settings['backup_options']['enabled']
                if service_has_backup_enabled:
                    backup_enabled_service_data_paths.append(service_data_path)
            except Exception as e:
                logger.warning("Could not open service settings file for {} service".format(service_name))

        return backup_enabled_service_data_paths

    @staticmethod
    def get_user_password_hash():
        password_hash = ""

        try:
            with open(app_config.path_to_password_hash_file, "r") as hash_file:
                password_hash = hash_file.readline()
        except Exception as error:
            print("An error occurred while opening the password hash file: ", error)

        return password_hash
