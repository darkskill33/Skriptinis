import os
import shutil
import time
import sys
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar

#Nurodome aplankalus, kurie gali būti sukuriami ir jų talpinamus failus.
TARGET_FOLDERS = {
    "Dokumentai": [".pdf", ".docx", ".txt", ".xlsx", ".pptx", ".dotx", ".doc", ".xls", ".csv"],
    "Nuotraukos": [".jpg", ".jpeg", ".png", ".gif"],
    "Muzika": [".mp3", ".wav"],
    "Video": [".mp4"],
    "Archyvai": [".zip", ".rar", ".7z"],
    "Programos": [".exe", ".msi"],
    "Unknown": []
}

TEMP_FILES = [".local", ".tmh", ".templates", ".settings", 
              ".project", ".objects", ".ipynb_checkpoints", ".entities", ".mysql-9.1.0-winx64"]

LOG_FILE = "file_log.txt"
category_stats = {}
script_start_time = None

#Aprašome log failo pradžią
def write_log_header():
    global script_start_time
    script_start_time = datetime.now()
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write("\n====== Skripto paleidimas ======\n")
            f.write("Data: " + script_start_time.strftime("%Y-%m-%d") + "\n")
            f.write("Laikas: " + script_start_time.strftime("%H:%M:%S") + "\n")
            f.write("=================================\n")
            
    except Exception as e:
        print(f"Klaida rašant log antraštę: {e}")


#Aprašome log pabaigą
def write_log_footer():
    try:
        script_end_time = datetime.now()
        duration = script_end_time - script_start_time
        minutes, seconds = divmod(duration.total_seconds(), 60)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            
            total_files = sum(category_stats.values())
            f.write(f"Iš viso perkelta failų: {total_files}\n")
            f.write(f"Skripto trukmė: {int(minutes)} min. {int(seconds)} sek.\n")
            f.write("------------------------------------------------------\n") 
            
        return f"Skripto trukmė: {int(minutes)} min. {int(seconds)} sek."
    except Exception as e:
        return f"Klaida rašant log pabaigą: {e}"

# Formatuojame log eilutę
def format_log(file, source, target):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"[{time_str}] {file} | {source} -> {target}"

# Įrašome log į log failą
def save_log(entry):
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry + "\n")
            
    except Exception as e:
        print(f"Klaida rašant į log failą: {e}")

# Failų perkelimo funkcija
def move_files(folder_path, enabled_categories, progress_callback=None):
    total_files = len([f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))])
    processed = 0
    write_log_header()

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        # Tikriname ar tai failas, jei ne - praleidžiam jį 
        if not os.path.isfile(file_path):
            continue

        # Jei failas baigiasi "temporary files" sąraše esančiu formatu - praleidžiam.
        if any(filename.endswith(ext) for ext in TEMP_FILES):
            processed += 1
            if progress_callback:
                progress_callback(processed, total_files)
            continue

        file_ext = os.path.splitext(filename)[1].lower()
        moved = False
        matched_any_category = False
        
        # Tikriname ar failas atitinka nurodytuose kategorijose, jei ne - tesiame paiešką
        for folder, extensions in TARGET_FOLDERS.items():
            if file_ext in extensions:
                matched_any_category = True
                # Perkeliame tik jei ši kategorija pažymėta
                if folder in enabled_categories:
                    target_folder = os.path.join(folder_path, folder)
                    moved = True
                    break

        # Jei failų nėra aprašytose kategorijose - dedam viską į unknown
        if not moved:
            if not matched_any_category and "Unknown" in enabled_categories:
                folder = "Unknown"
                target_folder = os.path.join(folder_path, folder)
            else:
                processed += 1
                if progress_callback:
                    progress_callback(processed, total_files)
                continue

        try:
            # Sukuriame naujus aplankalus ir bandome perkelti failus į naują aplanką
            os.makedirs(target_folder, exist_ok=True)
            new_path = os.path.join(target_folder, filename)
            shutil.move(file_path, new_path)

            # Papildome log failą
            log_entry = format_log(filename, file_path, new_path)
            save_log(log_entry)

            category_stats[folder] = category_stats.get(folder, 0) + 1
        except Exception as e:
            save_log(f"[KLAIDA] {filename}: {e}")

        # Pažymime kiek failų perkėlėme
        processed += 1
        if progress_callback:
            progress_callback(processed, total_files)

def run_gui():
    # Leidžiamas aplankalo pasirinkimas
    def select_folder():
        path = filedialog.askdirectory()
        if path:
            folder_var.set(path)
            run_btn.config(state="normal")

    # Perkėlimo progreso juostos parodymas.
    def update_progress(current, total):
        percent = int((current / total) * 100)
        progress["value"] = percent
        progress_label.config(text=f"{percent}% ({current}/{total})")
        root.update_idletasks()

    # Pagrindinis skriptas, kuris apjungia failų perkėlimą
    def run_script():
        folder = folder_var.get()
        enabled = [cat for cat, var in check_vars.items() if var.get()]
        
        if not enabled:
            messagebox.showwarning("Pasirinkimai", "Pasirink bent vieną kategoriją.")
            return

        progress["value"] = 0
        progress_label.config(text="0%")
        move_files(folder, enabled, update_progress)

        result = write_log_footer()
        result_msg = result + "\n\n" + "\n".join([f"{k}: {v} failai" for k, v in category_stats.items() if v > 0])
        messagebox.showinfo(" Perkelimas baigtas", result_msg + "\n\nLangas užsidarys po 15 sek.")
        # Automatinis skripto pabaigimas/uždarymas po 15 sek.
        root.after(15000, root.quit) 

    # Formatuojame vaizdą, kurį matysime skripto lange
    root = tk.Tk()
    root.title("Failų Tvarkymo Įrankis")
    root.geometry("600x550")

    # Aplankalo pasirinkimas
    tk.Label(root, text="Pasirinkite aplanką:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10)
    folder_var = tk.StringVar()
    tk.Entry(root, textvariable=folder_var, width=60).grid(row=1, column=0, padx=10)
    tk.Button(root, text="Naršyti...", command=select_folder).grid(row=2, column=0, padx=10, pady=5)
    
    tk.Label(root, text="Pasirink kategorijas:", font=("Arial", 12)).grid(row=3, column=0, padx=10, pady=10)
    check_vars = {}

    # Kategorijų išskaidymas į 2 stulpelius
    row = 4
    col = 0
    for category in TARGET_FOLDERS.keys():
        var = tk.BooleanVar(value=True)
        check = tk.Checkbutton(root, text=category, variable=var)
        check.grid(row=row, column=col, padx=10, pady=5, sticky="w")  
        check_vars[category] = var

        col += 1
        if col == 2: 
            col = 0
            row += 1

    # Mygtuko paslėpimas, kol nebus pasirinktos kategorijos
    run_btn = tk.Button(root, text="Tvarkyti Failus", font=("Arial", 14), command=run_script)
    run_btn.grid(row=row + 1, column=0, pady=20)
    run_btn.config(state="disabled")

    # Progreso juostos aprašymas
    tk.Label(root, text="Progreso juosta:", font=("Arial", 12)).grid(row=row + 2, column=0, padx=10, pady=10)
    progress = Progressbar(root, length=400, mode="determinate")
    progress.grid(row=row + 3, column=0, padx=10, pady=5)
    progress_label = tk.Label(root, text="0%")
    progress_label.grid(row=row + 4, column=0, padx=10, pady=5)

    # Lango uždarymo mygtukas
    close_btn = tk.Button(root, text="Uždaryti", font=("Arial", 12), command=root.quit)
    close_btn.grid(row=row + 5, column=0, pady=10)
    close_btn.config(state="normal")

    root.mainloop()

if __name__ == "__main__":
    run_gui()
