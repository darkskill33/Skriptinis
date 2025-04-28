import os
import shutil
import time
import sys
from datetime import datetime
from colorama import Fore, Style, init


if len(sys.argv) > 1:
    user_name = sys.argv[1]
    print(f"Aktyvuota {user_name} vartotojo versija!")
else:
    user_name = None

def get_downloads_folder():
    if user_name:
        return os.path.join("C:\\Users", user_name, "Downloads_1")
    else:
        return os.path.join(os.path.expanduser("~"), "Downloads_1")

DOWNLOADS_FOLDER = get_downloads_folder()

if not os.path.exists(DOWNLOADS_FOLDER):
    print(f"Klaida: Vartotojo {user_name or 'nežinomo'} 'Downloads' aplankas neegzistuoja!")
    sys.exit(1)


TARGET_FOLDERS = {
    "Dokumentai": [".pdf", ".docx", ".txt", ".xlsx", ".pptx",".dotx", ".doc", ".xls", ".csv"],
    "Nuotraukos": [".jpg", ".jpeg", ".png", ".gif"],
    "Muzika": [".mp3", ".wav"],
    "Archyvai": [".zip", ".rar", ".7z"],
    "Programos": [".exe", ".msi"],
    "Unknown": []
}

TEMP_FILES = [".local", ".tmh", ".templates", ".settings", 
            ".project", ".objects", ".ipynb_checkpoints", ".entities", ".mysql-9.1.0-winx64"]

script_start_time = datetime.now()
total_moved = 0
LOG_FILE = "file_log.txt"

def write_log_header():
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n")
            f.write("====== Skripto paleidimas ======\n")
            f.write("Data: " + script_start_time.strftime("%Y-%m-%d") + "\n")
            f.write("Laikas: " + script_start_time.strftime("%H:%M:%S") + "\n")
            f.write("=================================\n")
    except Exception as e:
        print(f"Klaida rašant log antraštę: {e}")

def write_log_footer():
    try:
        script_end_time = datetime.now()
        duration = script_end_time - script_start_time
        minutes, seconds = divmod(duration.total_seconds(), 60)

        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"Iš viso perkelta failų: {total_moved}\n")
            f.write(f"Skripto trukmė: {int(minutes)} min. {int(seconds)} sek.\n")
            f.write("------------------------------------------------------\n")
        print(f"\nIš viso perkelta failų: {total_moved}")
        print(f"Skripto trukmė: {int(minutes)} min. {int(seconds)} sek.")
    except Exception as e:
        print(f"Klaida rašant log pabaigą: {e}")

def format_log(file, source, target):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{time_str}] {file} | {source} -> {target}"

def save_log(entry):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
    except Exception as e:
        print(f"Klaida rašant į log failą: {e}")

def move_files():
    global total_moved

    for filename in os.listdir(DOWNLOADS_FOLDER):
        file_path = os.path.join(DOWNLOADS_FOLDER, filename)

        if not os.path.isfile(file_path):
            continue

        if any(filename.endswith(ext) for ext in TEMP_FILES):
            print(Fore.LIGHTYELLOW_EX + f"Failas neperkeltas dėl failo tipo: {filename}")
            skipped_files += 1
            continue

        file_ext = os.path.splitext(filename)[1].lower()
        moved = False

        for folder, extensions in TARGET_FOLDERS.items():
            if file_ext in extensions:
                target_folder = os.path.join(DOWNLOADS_FOLDER, folder)
                moved = True
                break

        if not moved:
            folder = "Unknown"
            target_folder = os.path.join(DOWNLOADS_FOLDER, folder)

        try:
            if not os.path.exists(target_folder):
                os.makedirs(target_folder, exist_ok=True)
                print(f"Sukurtas naujas aplankas {target_folder}")
        except Exception as e:
            print(f"Klaida kuriant aplanką {target_folder}: {e}")
            continue

        new_path = os.path.join(target_folder, filename)

        try:
            shutil.move(file_path, new_path)
            print(Fore.GREEN + f"✅ Perkeltas: {filename} → {folder}" + Style.RESET_ALL)
            log_entry = format_log(
                filename,
                os.path.relpath(file_path, start=os.path.expanduser("~")),
                os.path.relpath(new_path, start=os.path.expanduser("~"))
            )
            print(log_entry)
            save_log(log_entry)
            total_moved += 1
        except Exception as e:
            error_msg = f"Klaida perkeliant {filename}: {e}"
            print(Fore.RED + f"❌ {error_msg}" + Style.RESET_ALL)
            save_log("[KLAIDA] " + error_msg)


if __name__ == "__main__":
    print("Pradedamas failų tvarkymas... (Spausk Ctrl+C, kad sustabdytum)")
    write_log_header()

    try:
        move_files()
        write_log_footer()
        print("\n😎 Skriptas Baigtas! Log failą rasi aplanke, kuriame leidi skriptą! 📁\n")
    except KeyboardInterrupt:
        print("\nSkriptas sustabdytas rankiniu būdu.")
        write_log_footer()
    except Exception as e:
        print(f"Netikėta klaida: {e}")
        save_log(f"[NETIKĖTA KLAIDA] {e}")
