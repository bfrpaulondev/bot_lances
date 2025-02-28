import tkinter as tk
from tkinter import messagebox, ttk
import pyautogui
import cv2
import numpy as np
import pytesseract
import time
import random
import re
from PIL import Image

# Configure o caminho do Tesseract (ajuste conforme seu sistema)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class Bot:
    def __init__(self, root):
        self.root = root
        self.area = None  # (x, y, largura, altura)
        self.running = False
        self.selection_window = None
        self.lance_count = 0  # Contador de lances

        # Carregar as imagens de referência para o botão
        print("Carregando imagens de referência...")
        self.green_button = cv2.imread('assets/dar_lance_verde.png')
        self.gray_button = cv2.imread('assets/dar_lance_cinza.png')

        # Verificar se as imagens foram carregadas corretamente
        if self.green_button is None:
            print("Erro: Não foi possível carregar dar_lance_verde.png")
        if self.gray_button is None:
            print("Erro: Não foi possível carregar dar_lance_cinza.png")

        if self.green_button is None or self.gray_button is None:
            messagebox.showerror("Erro", "Não foi possível carregar as imagens dos botões em assets/")
            self.root.destroy()
            return

        # Criar a UI
        self.root.title("Bot de Lances")
        self.root.geometry("400x400")

        self.select_button = tk.Button(root, text="Selecionar Área", command=self.select_area)
        self.select_button.pack(pady=5)

        self.start_button = tk.Button(root, text="Iniciar", command=self.start)
        self.start_button.pack(pady=5)

        self.stop_button = tk.Button(root, text="Parar", command=self.stop)
        self.stop_button.pack(pady=5)

        self.lance_label = tk.Label(root, text="Lances dados: 0")
        self.lance_label.pack(pady=5)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, pady=5)

        self.time_tab = tk.Frame(self.notebook)
        self.notebook.add(self.time_tab, text="Tempo")
        self.time_log = tk.Text(self.time_tab, height=10, width=50, state='disabled')
        self.time_log.pack(fill="both", expand=True)

        self.lance_tab = tk.Frame(self.notebook)
        self.notebook.add(self.lance_tab, text="Lances")
        self.lance_log = tk.Text(self.lance_tab, height=10, width=50, state='disabled')
        self.lance_log.pack(fill="both", expand=True)

        self.button_tab = tk.Frame(self.notebook)
        self.notebook.add(self.button_tab, text="Botão Encontrado")
        self.button_log = tk.Text(self.button_tab, height=10, width=50, state='disabled')
        self.button_log.pack(fill="both", expand=True)

    def log_to_tab(self, tab, message):
        try:
            tab.config(state='normal')
            tab.insert(tk.END, message + "\n")
            tab.see(tk.END)
            tab.config(state='disabled')
        except Exception as e:
            print(f"Erro ao registrar log na aba: {e}")

    def select_area(self):
        if self.selection_window:
            return

        self.selection_window = tk.Toplevel(self.root)
        self.selection_window.attributes('-alpha', 0.3)
        self.selection_window.attributes('-topmost', True)
        self.selection_window.overrideredirect(1)

        self.start_x = None
        self.start_y = None
        self.rect = None

        self.canvas = tk.Canvas(self.selection_window, cursor="cross")
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.selection_window.geometry("300x200")
        self.selection_window.update()
        self.selection_window.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")

    def on_press(self, event):
        self.start_x = self.canvas.winfo_rootx() + event.x
        self.start_y = self.canvas.winfo_rooty() + event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

    def on_drag(self, event):
        self.canvas.coords(self.rect, self.start_x - self.canvas.winfo_rootx(), 
                           self.start_y - self.canvas.winfo_rooty(), 
                           event.x, event.y)

    def on_release(self, event):
        end_x = self.canvas.winfo_rootx() + event.x
        end_y = self.canvas.winfo_rooty() + event.y
        x = min(self.start_x, end_x)
        y = min(self.start_y, end_y)
        width = abs(end_x - self.start_x)
        height = abs(end_y - self.start_y)
        self.area = (x, y, width, height)
        self.selection_window.destroy()
        self.selection_window = None
        messagebox.showinfo("Área Selecionada", f"Área: x={x}, y={y}, largura={width}, altura={height}")

    def start(self):
        if not self.area:
            messagebox.showwarning("Erro", "Selecione uma área primeiro!")
            return
        x, y, width, height = self.area
        print(f"Área selecionada: x={x}, y={y}, largura={width}, altura={height}")
        if x < 0 or y < 0 or width <= 0 or height <= 0:
            messagebox.showwarning("Erro", "Área selecionada inválida!")
            return
        print("Iniciando o bot...")
        self.running = True
        self.root.after(100, self.monitor)

    def stop(self):
        print("Parando o bot...")
        self.running = False

    def find_buttons(self, image, template, threshold=0.7):
        """Encontra todas as correspondências do template na imagem com confiança acima do limiar."""
        try:
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            locations = np.where(result >= threshold)
            locations = list(zip(*locations[::-1]))  # Lista de (x, y)
            return locations, result
        except Exception as e:
            print(f"Erro no template matching: {e}")
            return [], np.array([])

    def is_region_green(self, image, x, y, w, h):
        """Verifica se a região do botão é predominantemente verde (mínima aparência verde)."""
        region = image[y:y+h, x:x+w]
        if region.size == 0:
            return False
        mean_color = cv2.mean(region)[:3]  # BGR
        blue, green, red = mean_color
        print(f"Cor média da região ({x}, {y}): B={blue:.1f}, G={green:.1f}, R={red:.1f}")
        return green > red and green > blue  # Apenas verifica se o verde é o canal dominante

    def update_lance_count(self):
        try:
            self.lance_count += 1
            self.lance_label.config(text=f"Lances dados: {self.lance_count}")
        except Exception as e:
            print(f"Erro ao atualizar contador de lances: {e}")

    def monitor(self):
        try:
            if not self.running:
                print("Bot parado.")
                return

            print("Capturando tela...")
            screenshot = pyautogui.screenshot(region=self.area)
            image = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)

            h, w, _ = image.shape
            print(f"Dimensões da captura: {h}x{w}")
            if h == 0 or w == 0:
                print("Erro: Captura de tela vazia. Verifique a área selecionada.")
                self.root.after(100, self.monitor)
                return

            # Encontrar todos os botões "DAR LANCE" (verdes e cinzas)
            green_locations, green_result = self.find_buttons(image, self.green_button, threshold=0.7)
            gray_locations, gray_result = self.find_buttons(image, self.gray_button, threshold=0.7)

            buttons = []
            button_h, button_w, _ = self.green_button.shape

            # Processar botões verdes
            for loc in green_locations:
                x, y = loc
                confidence = green_result[y, x]
                buttons.append((x, y, confidence, "Verde"))

            # Processar botões cinzas
            for loc in gray_locations:
                x, y = loc
                confidence = gray_result[y, x]
                if not any(abs(bx - x) < 5 and abs(by - y) < 5 for bx, by, _, _ in buttons):
                    buttons.append((x, y, confidence, "Cinza"))

            clicked = False
            for button_x, button_y, confidence, initial_status in buttons:
                is_green = self.is_region_green(image, button_x, button_y, button_w, button_h)
                button_status = "Verde" if is_green else "Cinza"
                print(f"Botão encontrado em: ({button_x}, {button_y}), status inicial: {initial_status}, status final: {button_status}, confiança: {confidence}")

                button_area = button_w * button_h
                image_area = h * w
                area_percentage = (button_area / image_area) * 100
                print(f"Área do botão: {button_area}, Área total: {image_area}, Percentual: {area_percentage:.2f}%")

                self.log_to_tab(self.button_log, f"{time.strftime('%H:%M:%S')} - Botão em ({button_x}, {button_y}), Status: {button_status}, Área: {area_percentage:.2f}%")

                if area_percentage < 1:
                    print("Botão é muito pequeno (menos de 1% da imagem). Ignorando.")
                    continue

                # Ajustar as posições relativas com base na imagem fornecida
                name_x, name_y = button_x - 200, button_y  # Nome à esquerda do botão
                name_width, name_height = 200, 30
                time_x, time_y = button_x - 200, button_y + 40  # Tempo 40 pixels abaixo do botão
                time_width, time_height = 100, 40

                name_y = max(0, name_y)
                name_x = max(0, name_x)
                name_height = min(name_height, h - name_y)
                name_width = min(name_width, w - name_x)

                time_y = max(0, time_y)
                time_x = max(0, time_x)
                time_height = min(time_height, h - time_y)
                time_width = min(time_width, w - time_x)

                name_area = image[name_y:name_y+name_height, name_x:name_x+name_width]
                time_area = image[time_y:time_y+time_height, time_x:time_x+time_width]

                print(f"Área do nome: ({name_x}, {name_y}, {name_width}x{name_height})")
                print(f"Área do tempo: ({time_x}, {time_y}, {time_width}x{time_height})")

                cv2.imwrite(f"name_area_{button_x}_{button_y}.png", name_area)
                cv2.imwrite(f"time_area_{button_x}_{button_y}.png", time_area)

                player_name = "Desconhecido"
                time_value = 0

                if name_area.size > 0:
                    name_gray = cv2.cvtColor(name_area, cv2.COLOR_BGR2GRAY)
                    _, name_thresh = cv2.threshold(name_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    player_name = pytesseract.image_to_string(name_thresh, config='--psm 6').strip()
                    print(f"Nome do jogador detectado: {player_name}")
                else:
                    print("Área do nome vazia.")

                if time_area.size > 0:
                    time_gray = cv2.cvtColor(time_area, cv2.COLOR_BGR2GRAY)
                    time_gray = cv2.equalizeHist(time_gray)
                    _, time_thresh = cv2.threshold(time_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    time_text = pytesseract.image_to_string(time_thresh, config='--psm 6 digits').strip()
                    print(f"Tempo detectado (texto bruto): {time_text}")
                    time_match = re.search(r'(\d+):(\d+)', time_text)
                    if time_match:
                        minutes, seconds = map(int, time_match.groups())
                        time_value = minutes * 60 + seconds
                    else:
                        time_match = re.search(r'\d+', time_text)
                        time_value = int(time_match.group()) if time_match else 0
                    print(f"Tempo detectado (valor em segundos): {time_value}")
                else:
                    print("Área do tempo vazia.")

                self.log_to_tab(self.time_log, f"{time.strftime('%H:%M:%S')} - Botão ({button_x}, {button_y}) - Tempo: {time_value} segundos")

                # Lógica de clique: Clicar se o botão for verde, independentemente de qualquer outra condição
                print(f"Botão verde: {is_green}")
                if is_green:
                    print("Botão verde detectado. Clicando...")
                    click_x = self.area[0] + button_x + button_w // 2
                    click_y = self.area[1] + button_y + button_h // 2
                    print(f"Coordenadas de clique: ({click_x}, {click_y})")
                    pyautogui.moveTo(click_x, click_y)
                    pyautogui.click(click_x, click_y)
                    print("Clique realizado!")

                    self.update_lance_count()

                    lance_message = f"{time.strftime('%H:%M:%S')} - Jogador: {player_name} - Tempo: {time_value}s"
                    with open('log_lances.txt', 'a', encoding='utf-8') as f:
                        f.write(lance_message + "\n")
                    self.log_to_tab(self.lance_log, lance_message)

                    sleep_time = random.uniform(1, 15) * 1000  # Intervalo de 1 a 15 segundos
                    print(f"Esperando {sleep_time/1000} segundos...")
                    self.root.after(int(sleep_time), self.monitor)
                    clicked = True
                    break
                else:
                    print("Botão não é verde. Ignorando.")

            if not clicked:
                print("Monitorando novamente em 100ms...")
                self.root.after(100, self.monitor)

        except Exception as e:
            print(f"Erro no monitoramento: {e}")
            self.root.after(100, self.monitor)

if __name__ == "__main__":
    root = tk.Tk()
    bot = Bot(root)
    root.mainloop()