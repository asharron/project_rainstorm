import os
import yaml
import shutil
import subprocess
import re
from datetime import datetime
from raincloud.rainstick.config import app_config
from raincloud.rainstick.Log import Log

logger = Log.get_logger()


class BackupManager:
    access_grant = "14zZEdH4uEZwjbd4fKNHZffoWy5AW8jrFkJF9Sxd5PHH9EtjxEGjX99Zf6u4EGAaCacfHnqyXjJuvBDgATSziN9i4yr6LszLgJcTK5mz5hjuzviBBap4KinhWYpgd3sw1sE4skEVLMQtKkXUVFC8C5pY6gaCXdGyjJApzVikuY9Cs1HAi7gDNSrDH5GNtD2ZU1aYKoKRHwYmpAhMpw7uBg5oB7dbDUA2qFbSB8ajEEmBfHx3PhxpSQdAUnVuB1RDnXEeJjRPUzf8VJKr9P"
    root_consolidation_folder_path = "/tmp/project_rainstorm/"

    @staticmethod
    def create_rclone_config():
        backup_command = "rclone config create rainstorm tardigrade access_grant {}" \
            .format(BackupManager.access_grant)
        os.system(backup_command)

    @staticmethod
    def create_restic_repo():
        # TODO: Backup will be rainstorm's account, so the bucket will be for all users, not just one
        if not app_config['path_to_password_hash_file']:
            print("Config is missing the path to password hash file. Aborting backups bucket creation.")
            return False

        # TODO: Handle repository master key and config already initialized
        try:
            os.system("restic -r rclone:rainstorm:backupstest/jimmy init --password-file {}"
                      .format(app_config['path_to_password_hash_file']))
        except OSError as error:
            print("Could not create backups bucket. Error: ", error)
            return False

        return True

    @staticmethod
    def create_root_bucket():
        try:
            os.system("rclone mkdir rainstorm:backupstest")
        except OSError as error:
            print("Could not create backups bucket. Error: ", error)
            return False
        return True


    @staticmethod
    def backup_rainstorm_data():
        # TODO: Keep track of where those folders go on the FS
        # TODO: Restore from a backup
        consolidation_folder_path = BackupManager.consolidate_backupable_files()
        # TODO: Have some kind of user identifier as a parent folder of the backup time
        backup_command = "restic -r rclone:rainstorm:backupstest backup {} --password-file {}".format(consolidation_folder_path, app_config['path_to_password_hash_file'])
        print("Performing backup of data with command " + backup_command)
        os.system(backup_command)
        print("Backup successfully completed")

    @staticmethod
    def get_repository_snapshots():
        os.system("restic -r rclone:rainstorm:backupstest snapshots --password-file {}".format(app_config['path_to_password_hash_file']))

    @staticmethod
    def consolidate_backupable_files():
        directories_to_backup = BackupManager.get_backupable_service_paths()
        backup_date = datetime.now().strftime("%Y%m%d-%H%M%S")
        dated_consolidation_folder_path = os.path.join(BackupManager.root_consolidation_folder_path, backup_date)

        if os.path.isdir(dated_consolidation_folder_path):
            print("Consolidation folder already exists. Aborting.")
            return ""

        backup_directories_fs_mapping = {}
        os.makedirs(dated_consolidation_folder_path)
        for directory_path in directories_to_backup:
            directory_to_backup_name = directory_path.split("/").pop()
            consolidation_folder_path = os.path.join(dated_consolidation_folder_path, directory_to_backup_name)
            print("Fixing file permissions for {}".format(directory_path))
            BackupManager.fix_file_permissions(directory_path)
            print("Copying {} to location {}".format(directory_path, consolidation_folder_path))
            shutil.copytree(directory_path, consolidation_folder_path)
            backup_directories_fs_mapping[consolidation_folder_path] = directory_path
        backup_fs_mapping_path = os.path.join(dated_consolidation_folder_path, "fs_restore_mappings.yml")
        # TODO: Do error handling here
        with open(backup_fs_mapping_path, 'w') as f:
            yaml.dump(backup_directories_fs_mapping, f)
        print("Consolidation finished")
        return dated_consolidation_folder_path

    @staticmethod
    def get_available_backups():
        command = "restic -r rclone:rainstorm:backupstest2 snapshots --password-file {}"\
            .format(app_config['path_to_password_hash_file'])
        formatted_command = command.split(" ")
        completed_process = subprocess.run(formatted_command, capture_output=True)
        error_output = completed_process.stderr.decode("utf-8")
        if "Fatal: unable to open config file: <config/> does not exist" in error_output:
            print("Restic repo does not exist")
            return []
        formatted_output = completed_process.stdout.decode("utf-8")
        output_as_list = formatted_output.split("\n")
        output_length = len(output_as_list)
        snapshots_as_strings = output_as_list[2:output_length-3]
        snapshots = []
        for snapshot_string in snapshots_as_strings:
            snapshot_id = re.search("^[a-zA-Z0-9]{8}", snapshot_string).group()
            snapshot_time = re.search("\d+-\d+-\d+\s\d+:\d+:\d+", snapshot_string).group()
            snapshot_info = {
                "snapshot_id": snapshot_id,
                "snapshot_time": snapshot_time
            }
            snapshots.append(snapshot_info)
        return snapshots

    @staticmethod
    def restore_from_backup(snapshot_id):
        restore_command = "restic --repo rclone:rainstorm:backupstest restore {} --target / --password-file {}"\
            .format(snapshot_id, app_config['path_to_password_hash_file'])
        os.system(restore_command)
        print("Restored snapshot successfully")

    @staticmethod
    def fix_file_permissions(directory_path):
        print("Ignoring fixing file permissions")
        # os.system("sudo chown -R drop:drop {}".format(directory_path))

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
