import cv2
import numpy as np
import pyautogui
import time
import random
import threading
import tkinter as tk
from tkinter import filedialog, ttk

# Variáveis globais
monitoring = False
selected_area = None
log_entries = []

def select_screen_area():
    global selected_area
    print("Selecione a área para monitorar...")
    selected_area = pyautogui.screenshot()
    print("Área selecionada com sucesso!")

def detect_and_click():
    global monitoring, selected_area, log_entries
    
    while monitoring:
        if selected_area is None:
            continue
        
        screenshot = pyautogui.screenshot()
        screen_np = np.array(screenshot)
        
        # Converter para escala de cinza
        gray = cv2.cvtColor(screen_np, cv2.COLOR_BGR2GRAY)
        
        # Detecção do botão verde "DAR LANCE"
        lower_green = np.array([50, 100, 50])  # Tom aproximado de verde
        upper_green = np.array([100, 255, 100])
        mask = cv2.inRange(screen_np, lower_green, upper_green)
        
        # Encontra contornos na máscara
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                pyautogui.click(x + w // 2, y + h // 2)
                log_entries.append(f"Clique realizado em ({x}, {y})")
                time.sleep(random.randint(1, 60))
        
        time.sleep(1)

def start_bot():
    global monitoring
    monitoring = True
    thread = threading.Thread(target=detect_and_click)
    thread.start()

def stop_bot():
    global monitoring
    monitoring = False

def save_log():
    file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        with open(file_path, "w") as file:
            for entry in log_entries:
                file.write(entry + "\n")
        print("Log salvo com sucesso!")

# Criar interface gráfica
root = tk.Tk()
root.title("Bot de Lances Automático")
root.geometry("400x300")
root.configure(bg="#f8f9fa")

style = ttk.Style()
style.configure("TButton", font=("Arial", 12), padding=10)
style.configure("TLabel", font=("Arial", 14), background="#f8f9fa")

frame = ttk.Frame(root, padding=20)
frame.pack(expand=True)

ttk.Label(frame, text="Controle do Bot de Lances", font=("Arial", 16, "bold")).pack(pady=10)

ttk.Button(frame, text="Selecionar Área", command=select_screen_area).pack(fill="x", pady=5)
ttk.Button(frame, text="Iniciar Bot", command=start_bot).pack(fill="x", pady=5)
ttk.Button(frame, text="Parar Bot", command=stop_bot).pack(fill="x", pady=5)
ttk.Button(frame, text="Salvar Log", command=save_log).pack(fill="x", pady=5)

root.mainloop()
