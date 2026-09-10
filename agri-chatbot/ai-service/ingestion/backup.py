import os
import shutil
import datetime

def create_backup(base_data_dir=None):
    if not base_data_dir:
        base_data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data"))
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = os.path.join(base_data_dir, "backups", timestamp)
    os.makedirs(backup_path, exist_ok=True)
    
    backed_up_items = []
    for item in ["manifests", "processed", "raw", "sources", "recovered"]:
        src = os.path.join(base_data_dir, item)
        if os.path.exists(src):
            dst = os.path.join(backup_path, item)
            shutil.copytree(src, dst, dirs_exist_ok=True)
            backed_up_items.append(item)
            
    return backup_path, backed_up_items

if __name__ == "__main__":
    path, items = create_backup()
    print(f"Backup created at: {path} with folders: {items}")
