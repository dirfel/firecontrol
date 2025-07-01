import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Label
from PIL import Image, ImageTk
from ppadb.client import Client as AdbClient
import threading
import time
import json
import os
import socket
from datetime import datetime

CONFIG_PATH = "config.json"
FIRE_TV_PORT = 5555

def salvar_ip(ip):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"ultimo_ip": ip}, f)

def carregar_ip():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                dados = json.load(f)
                return dados.get("ultimo_ip", "")
        except:
            return ""
    return ""

def conectar_firetv(ip, status_callback):
    client = AdbClient(host="127.0.0.1", port=5037)
    try:
        client.remote_connect(ip, FIRE_TV_PORT)
    except Exception as e:
        status_callback(f"Erro ao conectar via ADB: {e}")
        return None

    while True:
        devices = client.devices()
        device = next((d for d in devices if d.serial == f"{ip}:{FIRE_TV_PORT}"), None)

        if device:
            try:
                state = device.get_state()
                if state == "unauthorized":
                    status_callback("Dispositivo detectado, mas não autorizado. Autorize na TV.")
                elif state == "device":
                    status_callback("Conectado e autorizado com sucesso.")
                    return device
                else:
                    status_callback(f"Estado inesperado: {state}")
            except:
                status_callback("Falha ao obter estado. Aguardando autorização...")
        else:
            status_callback("Aguardando conexão...")
        time.sleep(2)

def enviar_comando(device, comando, status_callback):
    comandos = {
        "↑": "input keyevent 19",
        "↓": "input keyevent 20",
        "←": "input keyevent 21",
        "→": "input keyevent 22",
        "OK": "input keyevent 23",
        "Voltar": "input keyevent 4",
        "Home": "input keyevent 3",
        "Menu": "input keyevent 82",
        "Play/Pause": "input keyevent 85",
        "Configurações": "am start -a android.settings.SETTINGS",
        "Netflix": "monkey -p com.netflix.ninja -c android.intent.category.LAUNCHER 1",
        "YouTube": "monkey -p com.google.android.youtube.tv -c android.intent.category.LAUNCHER 1",
        "Prime Video": "monkey -p com.amazon.avod.thirdpartyclient -c android.intent.category.LAUNCHER 1"
    }
    if device and comando in comandos:
        try:
            device.shell(comandos[comando])
            status_callback(f"Comando '{comando}' enviado.")
        except Exception as e:
            status_callback(f"Erro ao enviar comando: {e}")
    else:
        status_callback("Dispositivo desconectado ou comando inválido.")

def enviar_texto(device, texto, status_callback):
    if device:
        try:
            texto_formatado = texto.replace(" ", "%s")
            device.shell(f"input text {texto_formatado}")
            status_callback(f"Texto enviado: {texto}")
        except Exception as e:
            status_callback(f"Erro ao enviar texto: {e}")
    else:
        status_callback("Dispositivo desconectado.")

def capturar_tela(device, status_callback, preview_callback):
    if device:
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nome_arquivo = f"screenshot_{timestamp}.png"
            caminho_local = os.path.join(os.getcwd(), nome_arquivo)
            device.shell("screencap -p /sdcard/screen.png")
            device.pull("/sdcard/screen.png", caminho_local)
            status_callback(f"Captura salva: {caminho_local}")
            preview_callback(caminho_local)
        except Exception as e:
            status_callback(f"Erro ao capturar tela: {e}")
    else:
        status_callback("Dispositivo desconectado.")

class FireTVGUI:
    def __init__(self, root):
        self.root = root
        self.theme = "dark"
        self.device = None

        self.set_theme_colors()

        # Indicador de status conexão
        self.status_frame = tk.Frame(root, bg=self.bg_color)
        self.status_frame.pack(fill=tk.X, pady=2)

        self.status_color_box = tk.Frame(self.status_frame, bg="red", width=20, height=20)
        self.status_color_box.pack(side=tk.LEFT, padx=5, pady=2)
        self.status_color_box.pack_propagate(False)

        self.status_conexao_label = tk.Label(self.status_frame, text="Desconectado", fg=self.fg_color, bg=self.bg_color, font=("Arial", 12, "bold"))
        self.status_conexao_label.pack(side=tk.LEFT, padx=5)

        self.ip_frame = tk.Frame(root, bg=self.bg_color)
        self.ip_frame.pack(pady=5)

        tk.Label(self.ip_frame, text="IP do Fire TV:", fg=self.fg_color, bg=self.bg_color).pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(self.ip_frame, width=20, bg=self.entry_bg, fg=self.entry_fg)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        tk.Button(self.ip_frame, text="Conectar", command=self.iniciar_conexao).pack(side=tk.LEFT)
        tk.Button(self.ip_frame, text="Escanear LAN", command=self.varrer_rede).pack(side=tk.LEFT)

        self.dpad_frame = tk.Frame(root, bg=self.bg_color)
        self.dpad_frame.pack(pady=10)

        self._add_dpad_button(row=0, column=1, text="↑")
        self._add_dpad_button(row=1, column=0, text="←")
        self._add_dpad_button(row=1, column=1, text="OK")
        self._add_dpad_button(row=1, column=2, text="→")
        self._add_dpad_button(row=2, column=1, text="↓")

        self.extra_frame = tk.Frame(root, bg=self.bg_color)
        self.extra_frame.pack(pady=5)
        for i, nome in enumerate(["Voltar", "Home", "Menu", "Play/Pause"]):
            b = tk.Button(self.extra_frame, text=nome, width=10,
                          command=lambda c=nome: enviar_comando(self.device, c, self.atualizar_status),
                          bg=self.bg_color, fg=self.fg_color)
            b.grid(row=0, column=i, padx=3)

        for i, nome in enumerate(["Configurações", "Netflix", "YouTube", "Prime Video"]):
            b = tk.Button(self.extra_frame, text=nome, width=10,
                          command=lambda c=nome: enviar_comando(self.device, c, self.atualizar_status),
                          bg=self.bg_color, fg=self.fg_color)
            b.grid(row=1, column=i, padx=3)

        self.text_entry = tk.Entry(root, width=50, bg=self.entry_bg, fg=self.entry_fg)
        self.text_entry.pack(pady=5)
        tk.Button(root, text="Enviar Texto", command=self.enviar_texto,
                  bg=self.bg_color, fg=self.fg_color).pack()

        tk.Button(root, text="Capturar Tela", command=self.capturar_tela,
                  bg=self.bg_color, fg=self.fg_color).pack(pady=5)

        self.btn_toggle_theme = tk.Button(root, text="Alternar Tema", command=self.toggle_theme,
                                          bg=self.bg_color, fg=self.fg_color)
        self.btn_toggle_theme.pack(pady=5)

        self.status_text = tk.Text(root, height=6, width=60, state='disabled',
                                   bg=self.entry_bg, fg=self.entry_fg)
        self.status_text.pack(pady=10)

        ultimo_ip = carregar_ip()
        self.ip_entry.insert(0, ultimo_ip)

    def atualizar_status_conexao(self, cor, texto):
        self.status_color_box.configure(bg=cor)
        self.status_conexao_label.configure(text=texto)

    def set_theme_colors(self):
        if self.theme == "dark":
            self.bg_color = "#1e1e1e"
            self.fg_color = "white"
            self.entry_bg = "#2d2d2d"
            self.entry_fg = "white"
        else:
            self.bg_color = "white"
            self.fg_color = "black"
            self.entry_bg = "white"
            self.entry_fg = "black"
        self.root.configure(bg=self.bg_color)

    def update_colors(self):
        self.status_frame.configure(bg=self.bg_color)
        self.status_conexao_label.configure(bg=self.bg_color, fg=self.fg_color)
        self.status_color_box.configure(bg=self.status_color_box["bg"])  # mantém cor atual

        self.ip_frame.configure(bg=self.bg_color)
        for widget in self.ip_frame.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=self.bg_color, fg=self.fg_color)
            elif isinstance(widget, tk.Entry):
                widget.configure(bg=self.entry_bg, fg=self.entry_fg)

        self.dpad_frame.configure(bg=self.bg_color)
        for widget in self.dpad_frame.winfo_children():
            widget.configure(bg=self.bg_color, fg=self.fg_color)

        self.extra_frame.configure(bg=self.bg_color)
        for widget in self.extra_frame.winfo_children():
            widget.configure(bg=self.bg_color, fg=self.fg_color)

        self.text_entry.configure(bg=self.entry_bg, fg=self.entry_fg)
        self.status_text.configure(bg=self.entry_bg, fg=self.entry_fg)

        self.btn_toggle_theme.configure(bg=self.bg_color, fg=self.fg_color)

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.set_theme_colors()
        self.update_colors()

    def _add_dpad_button(self, row, column, text):
        b = tk.Button(self.dpad_frame, text=text, width=5, height=2,
                      font=("Arial", 14), bg=self.bg_color, fg=self.fg_color,
                      command=lambda: enviar_comando(self.device, text, self.atualizar_status))
        b.grid(row=row, column=column, padx=5, pady=5)

    def atualizar_status(self, mensagem):
        self.status_text.configure(state='normal')
        self.status_text.insert(tk.END, mensagem + "\n")
        self.status_text.configure(state='disabled')
        self.status_text.see(tk.END)

    def iniciar_conexao(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Erro", "Digite o IP do Fire TV Stick")
            return
        self.atualizar_status_conexao("yellow", "Conectando...")
        self.atualizar_status("Iniciando conexão com o Fire TV...")
        threading.Thread(target=self.conectar_thread, args=(ip,), daemon=True).start()

    def conectar_thread(self, ip):
        self.device = conectar_firetv(ip, self.atualizar_status)
        if self.device:
            try:
                nome_disp = self.device.get_properties().get("ro.product.model", "Fire TV")
            except Exception:
                nome_disp = "Fire TV"
            self.atualizar_status_conexao("green", f"{nome_disp} ({ip})")
            salvar_ip(ip)
        else:
            self.atualizar_status_conexao("red", "Desconectado")

    def varrer_rede(self):
        base_ip = self.ip_entry.get().strip().rsplit('.', 1)[0]
        if not base_ip:
            messagebox.showerror("Erro", "Digite parte do IP base (ex: 192.168.0)")
            return
        self.atualizar_status(f"Iniciando varredura: {base_ip}.0/24")
        threading.Thread(target=self.scan_lan, args=(base_ip,), daemon=True).start()

    def scan_lan(self, base_ip):
        encontrados = []
        for i in range(1, 255):
            ip = f"{base_ip}.{i}"
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.3)
                result = sock.connect_ex((ip, FIRE_TV_PORT))
                sock.close()
                if result == 0:
                    encontrados.append(ip)
                    self.atualizar_status(f"Dispositivo encontrado: {ip}")
            except:
                pass

        if encontrados:
            escolhido = simpledialog.askstring("Escolha IP", f"Dispositivos encontrados:\n" + "\n".join(encontrados) + "\n\nDigite o IP desejado:")
            if escolhido and escolhido.strip() in encontrados:
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, escolhido.strip())
                self.iniciar_conexao()
        else:
            self.atualizar_status("Nenhum dispositivo com ADB encontrado na rede.")

    def enviar_texto(self):
        texto = self.text_entry.get().strip()
        if texto:
            enviar_texto(self.device, texto, self.atualizar_status)

    def capturar_tela(self):
        capturar_tela(self.device, self.atualizar_status, self.exibir_imagem)

    def exibir_imagem(self, caminho):
        try:
            janela = Toplevel(self.root)
            janela.title("Captura de Tela")
            imagem = Image.open(caminho)
            imagem = imagem.resize((imagem.width // 2, imagem.height // 2))
            foto = ImageTk.PhotoImage(imagem)
            lbl = Label(janela, image=foto)
            lbl.image = foto
            lbl.pack()
        except Exception as e:
            self.atualizar_status(f"Erro ao exibir imagem: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = FireTVGUI(root)
    root.mainloop()
