import os
import yaml
import shutil
import subprocess
import re
from collections import namedtuple
from datetime import datetime

from raincloud.models.service import Service
from raincloud.rainstick.config import app_config
from raincloud.rainstick.Log import Log

logger = Log.get_logger()
ServiceFileStoragePaths = namedtuple("ServiceFileStoragePaths", "service_data_path file_storage_path")

# TODO: Convert print statements to debug and warn
class BackupManager:
    ACCESS_GRANT = "14zZEdH4uEZwjbd4fKNHZffoWy5AW8jrFkJF9Sxd5PHH9EtjxEGjX99Zf6u4EGAaCacfHnqyXjJuvBDgATSziN9i4yr6LszLgJcTK5mz5hjuzviBBap4KinhWYpgd3sw1sE4skEVLMQtKkXUVFC8C5pY6gaCXdGyjJApzVikuY9Cs1HAi7gDNSrDH5GNtD2ZU1aYKoKRHwYmpAhMpw7uBg5oB7dbDUA2qFbSB8ajEEmBfHx3PhxpSQdAUnVuB1RDnXEeJjRPUzf8VJKr9P"
    ROOT_CONSOLIDATION_FOLDER_PATH = "/tmp/project_rainstorm/"
    SERVICE_DATA_FOLDER_NAME = "service_data"
    FILE_STORAGE_FOLDER_NAME = "file_storage"

    @staticmethod
    def create_rclone_config():
        backup_command = "rclone config create rainstorm tardigrade access_grant {}" \
            .format(BackupManager.ACCESS_GRANT)
        os.system(backup_command)

    @staticmethod
    def create_restic_repo_for_service(service_name):
        if not app_config['path_to_password_hash_file']:
            print("Config is missing the path to password hash file. Aborting backups bucket creation.")
            return False

        return_code = os.system("restic -r rclone:rainstorm:backupstest/{} snapshots --password-file {}"
                  .format(service_name, app_config['path_to_password_hash_file']))

        if return_code == 0:
            print("Repo for service already exists")
            return


        return_status = os.system("restic -r rclone:rainstorm:backupstest/{} init --password-file {}"
                  .format(service_name, app_config['path_to_password_hash_file']))
        if not return_status == 0:
            print("Could not create restic repo for {}", service_name)

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
    def backup_all_services():
        consolidated_services_mapping = BackupManager.consolidate_all_backup_enabled_service_files()
        for service_name, consolidated_service_path in consolidated_services_mapping.items():
            BackupManager.create_restic_repo_for_service(service_name)
            backup_command = "restic -r rclone:rainstorm:backupstest/{} backup {} --password-file {}"\
                .format(service_name, consolidated_service_path, app_config['path_to_password_hash_file'])
            print("Performing backup of data with command " + backup_command)
            os.system(backup_command)
            print("Backed up {} successfully".format(service_name))
        print("Backup successfully completed")

    # TODO: Backup a single service
    @staticmethod
    def backup_service(service_name):
        service_to_backup = Service(service_name)
        service_app_settings = service_to_backup.app_settings
        if not service_app_settings['backup_options'] or not service_app_settings['backup_options']['enabled']:
            logger.warn("Backups not enabled for service {}".format(service_name))
            return

        # TODO: Move files to own folder and back it up!!!
        consolidated_service_folder = BackupManager.consolidate_service_backup_enabled_files(service_to_backup)
        BackupManager.create_restic_repo_for_service(service_to_backup.name)
        backup_command = "restic -r rclone:rainstorm:backupstest/{} backup {} --password-file {}" \
            .format(service_name, consolidated_service_folder, app_config['path_to_password_hash_file'])
        returncode = os.system(backup_command)

        if not returncode == 0:
            raise BackupError("Could not backup the service {} using restic".format(service_name))
        logger.info("Successfully backed up {}".format(service_name))

    @staticmethod
    def consolidate_all_backup_enabled_service_files():
        consolidated_services_mapping = {}
        directories_to_backup = BackupManager.get_backupable_service_paths()
        backup_date = datetime.now().strftime("%Y%m%d-%H%M%S")
        dated_consolidation_folder_path = os.path.join(BackupManager.ROOT_CONSOLIDATION_FOLDER_PATH, backup_date)

        if os.path.isdir(dated_consolidation_folder_path):
            print("Consolidation folder already exists. Aborting.")
            return ""

        backup_directories_fs_mapping = {}
        os.makedirs(dated_consolidation_folder_path)
        for service_name, service_file_storage_paths in directories_to_backup.items():
            consolidation_folder_path = os.path.join(dated_consolidation_folder_path, service_name)
            service_data_consolidation_folder_path = os.path.join(consolidation_folder_path,
                                                                  BackupManager.SERVICE_DATA_FOLDER_NAME)
            file_storage_consolidation_folder_path = os.path.join(consolidation_folder_path,
                                                                  BackupManager.FILE_STORAGE_FOLDER_NAME)

            BackupManager.fix_file_permissions(service_file_storage_paths.service_data_path)

            print("Copying {} to location {}".format(service_file_storage_paths.service_data_path, service_data_consolidation_folder_path))
            shutil.copytree(service_file_storage_paths.service_data_path, service_data_consolidation_folder_path)
            print("Copying {} to location {}".format(service_file_storage_paths.file_storage_path, file_storage_consolidation_folder_path))
            shutil.copytree(service_file_storage_paths.file_storage_path, file_storage_consolidation_folder_path)
            backup_directories_fs_mapping[service_name] = dict(service_file_storage_paths._asdict())
            consolidated_services_mapping[service_name] = consolidation_folder_path
        backup_fs_mapping_path = os.path.join(dated_consolidation_folder_path, "fs_restore_mappings.yml")
        try:
            with open(backup_fs_mapping_path, 'w') as f:
                yaml.dump(backup_directories_fs_mapping, f)
        except OSError as error:
            print("Could not write the fs mapping file ", error)
        print("Consolidation finished")
        return consolidated_services_mapping

    @staticmethod
    def consolidate_service_backup_enabled_files(service: Service) -> str:
        logger.info("Consolidating app and file storage for {}".format(service.name))
        backup_date = datetime.now().strftime("%Y%m%d-%H%M%S")
        dated_consolidation_folder_path = os.path.join(BackupManager.ROOT_CONSOLIDATION_FOLDER_PATH, backup_date)
        dated_service_consolidation_path = os.path.join(dated_consolidation_folder_path, service.name)

        service_data_consolidation_folder_path = os.path.join(dated_service_consolidation_path,
                                                              BackupManager.SERVICE_DATA_FOLDER_NAME)
        file_storage_consolidation_folder_path = os.path.join(dated_service_consolidation_path,
                                                              BackupManager.FILE_STORAGE_FOLDER_NAME)

        try:
            os.makedirs(dated_service_consolidation_path, exist_ok=True)
            shutil.copytree(service.data_folder_path, service_data_consolidation_folder_path)
            shutil.copytree(service.file_storage_folder_path, file_storage_consolidation_folder_path)
        except OSError as e:
            logger.warn("Could not consolidate files for {}: {}".format(service.name, e))
            raise BackupError("Could not consolidate files for ".format(service.name))
        logger.info("File consolidation complete for {}".format(service.name))
        return dated_service_consolidation_path

    @staticmethod
    def get_available_backups_for_all_services():
        all_backup_snapshots = {}
        for service in Service.all():
            service_backup_snapshots = BackupManager.get_available_backups_for_service(service.name)
            all_backup_snapshots[service.name] = service_backup_snapshots
        return all_backup_snapshots

    @staticmethod
    def get_available_backups_for_service(service_name):
        command = "restic -r rclone:rainstorm:backupstest/{} snapshots --password-file {}"\
            .format(service_name, app_config['path_to_password_hash_file'])
        formatted_command = command.split(" ")
        completed_process = subprocess.run(formatted_command, capture_output=True)
        if not completed_process.returncode == 0:
            print("Restic repo for service {} does not exist".format(service_name))
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
    def restore_service_from_backup(service_name, snapshot_id):
        service_to_restore = Service(service_name)
        print("Preparing to restore service {}. Disabling the container temporarily.")
        service_to_restore.disable()
        restore_command = "restic -r rclone:rainstorm:backupstest/{} restore {} --target / --password-file {}"\
            .format(service_name, snapshot_id, app_config['path_to_password_hash_file'])
        restore_command_formatted = restore_command.split(" ")
        completed_restore_process = subprocess.run(restore_command_formatted, capture_output=True)
        if not completed_restore_process.returncode == 0:
            print("Was unable to restore the service successfully from backup. Snapshot unable to be restored")
            print("Re-enabling service {}".format(service_name))
            service_to_restore.enable()
            return
        print("Restored snapshot successfully. Copying files to correct location...")
        formatted_process_output = completed_restore_process.stdout.decode("utf-8")
        opening_bracket_idx = formatted_process_output.find("[")
        closing_bracket_idx = formatted_process_output.find("]")
        restored_folder_file_path = formatted_process_output[opening_bracket_idx+1:closing_bracket_idx]
        print("Restored folder file path: ", restored_folder_file_path)
        restored_service_data_path = os.path.join(restored_folder_file_path, BackupManager.SERVICE_DATA_FOLDER_NAME)
        restored_file_storage_path = os.path.join(restored_folder_file_path, BackupManager.FILE_STORAGE_FOLDER_NAME)

        service_data_path = os.path.join(app_config["path_to_service_data"], service_name)
        file_storage_path = os.path.join(app_config["path_to_file_storage"], service_name)

        print("Removing {}".format(service_data_path))
        shutil.rmtree(service_data_path, ignore_errors=True)

        print("Copying {} to location {}".format(restored_service_data_path, service_data_path))
        shutil.copytree(restored_service_data_path, service_data_path)

        print("Removing {}".format(file_storage_path))
        shutil.rmtree(file_storage_path, ignore_errors=True)

        print("Copying {} to location {}".format(restored_file_storage_path, file_storage_path))
        shutil.copytree(restored_file_storage_path, file_storage_path)

        print("Restore complete. Re-enabling service {}".format(service_name))
        service_to_restore.enable()

    @staticmethod
    def fix_file_permissions(directory_path):
        # print("Ignoring fixing file permissions")
        print("Fixing file permissions for {}".format(directory_path))
        os.system("sudo chown -R drop:drop {}".format(directory_path))

    @staticmethod
    def get_backupable_service_paths():
        backup_enabled_service_data_paths = {}
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
                    file_storage_path = "/mnt/usb/files/" + service_name
                    service_storage_file_paths = ServiceFileStoragePaths(service_data_path, file_storage_path)
                    backup_enabled_service_data_paths[service_name]  = service_storage_file_paths
            except OSError as e:
                logger.warning("Could not open service settings file for {} service: {}".format(service_name, e))

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

class BackupError(Exception):
    pass