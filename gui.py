import tkinter as tk
from tkinter import messagebox, simpledialog, Toplevel, Label, ttk
from PIL import Image, ImageTk
import threading
import socket
import os
import json
import time

from adb_utils import conectar_firetv, desconectar_firetv, enviar_comando, enviar_texto, capturar_tela
from config import carregar_ip, salvar_ip

FIRE_TV_PORT = 5555

class FireTVGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Controle Fire TV Stick")
        self.root.configure(bg="#1e1e1e")
        self.device = None
        self.device_ip = None
        self.comandos_map = self.carregar_comandos()

        self.status_frame = tk.Frame(root, bg="#1e1e1e")
        self.status_frame.pack(pady=(5, 0))
        self.status_color = tk.Label(self.status_frame, width=2, height=1, bg="red")
        self.status_color.pack(side=tk.LEFT)
        self.status_label = tk.Label(self.status_frame, text="Desconectado", bg="#1e1e1e", fg="white")
        self.status_label.pack(side=tk.LEFT, padx=5)

        self.progress = ttk.Progressbar(self.status_frame, mode="determinate", length=150)
        self.progress.pack(side=tk.LEFT, padx=10)
        self.progress['value'] = 0

        self.tempo_restante_label = tk.Label(self.status_frame, text="", bg="#1e1e1e", fg="white")
        self.tempo_restante_label.pack(side=tk.LEFT)

        self.ip_frame = tk.Frame(root, bg="#1e1e1e")
        self.ip_frame.pack(pady=5)

        tk.Label(self.ip_frame, text="IP do Fire TV:", fg="white", bg="#1e1e1e").pack(side=tk.LEFT)
        self.ip_entry = tk.Entry(self.ip_frame, width=20)
        self.ip_entry.pack(side=tk.LEFT, padx=5)
        self.btn_conectar = tk.Button(self.ip_frame, text="Conectar", command=self.iniciar_conexao)
        self.btn_conectar.pack(side=tk.LEFT)
        self.btn_desconectar = tk.Button(self.ip_frame, text="Desconectar", command=self.desconectar)
        self.btn_desconectar.pack(side=tk.LEFT)
        self.btn_scan = tk.Button(self.ip_frame, text="Escanear LAN", command=self.varrer_rede)
        self.btn_scan.pack(side=tk.LEFT)
        self.btn_cancelar = tk.Button(self.ip_frame, text="Cancelar Varredura", command=self.cancelar_scan)
        self.btn_cancelar.pack(side=tk.LEFT, padx=5)
        self.btn_cancelar.pack_forget()  # escondido inicialmente

        self.dpad_frame = tk.Frame(root, bg="#1e1e1e")
        self.dpad_frame.pack(pady=10)
        self._add_dpad_button(row=0, column=1, text="↑")
        self._add_dpad_button(row=1, column=0, text="←")
        self._add_dpad_button(row=1, column=1, text="OK")
        self._add_dpad_button(row=1, column=2, text="→")
        self._add_dpad_button(row=2, column=1, text="↓")

        self.extra_frame = tk.Frame(root, bg="#1e1e1e")
        self.extra_frame.pack(pady=5)
        for i, nome in enumerate(["Voltar", "Home", "Menu", "Play/Pause"]):
            b = tk.Button(self.extra_frame, text=nome, width=10,
                          command=lambda c=nome: threading.Thread(target=enviar_comando, args=(self.device, c, self.comandos_map, self.atualizar_status), daemon=True).start())
            b.grid(row=0, column=i, padx=3)

        for i, nome in enumerate(["Configurações", "Netflix", "YouTube", "Prime Video"]):
            b = tk.Button(self.extra_frame, text=nome, width=10,
                          command=lambda c=nome: threading.Thread(target=enviar_comando, args=(self.device, c, self.comandos_map, self.atualizar_status), daemon=True).start())
            b.grid(row=1, column=i, padx=3)

        self.text_entry = tk.Entry(root, width=50)
        self.text_entry.pack(pady=5)
        tk.Button(root, text="Enviar Texto", command=lambda: threading.Thread(target=self.enviar_texto, daemon=True).start()).pack()

        tk.Button(root, text="Capturar Tela", command=lambda: threading.Thread(target=self.capturar_tela, daemon=True).start()).pack(pady=5)

        self.status_text = tk.Text(root, height=6, width=60, state='disabled', bg="#2d2d2d", fg="white")
        self.status_text.pack(pady=10)

        ultimo_ip = carregar_ip()
        self.ip_entry.insert(0, ultimo_ip)
        self.atualizar_botoes_status(conectado=False)
        self.cancelar_varredura = False

    def carregar_comandos(self):
        if os.path.exists("comandos.json"):
            with open("comandos.json", "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def _add_dpad_button(self, row, column, text):
        b = tk.Button(self.dpad_frame, text=text, width=5, height=2, font=("Arial", 14),
                      command=lambda: threading.Thread(target=enviar_comando, args=(self.device, text, self.comandos_map, self.atualizar_status), daemon=True).start())
        b.grid(row=row, column=column, padx=5, pady=5)

    def atualizar_status(self, mensagem):
        self.status_text.configure(state='normal')
        self.status_text.insert(tk.END, mensagem + "\n")
        self.status_text.configure(state='disabled')
        self.status_text.see(tk.END)

    def atualizar_indicador(self, cor, texto):
        self.status_color.configure(bg=cor)
        self.status_label.configure(text=texto)

    def atualizar_botoes_status(self, conectado):
        if conectado:
            self.btn_conectar.pack_forget()
            self.btn_scan.pack_forget()
            self.btn_desconectar.pack(side=tk.LEFT)
            self.btn_cancelar.pack_forget()
        else:
            self.btn_desconectar.pack_forget()
            self.btn_cancelar.pack_forget()
            self.btn_conectar.pack(side=tk.LEFT)
            self.btn_scan.pack(side=tk.LEFT)

    def iniciar_conexao(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            messagebox.showerror("Erro", "Digite o IP do Fire TV Stick")
            return
        self.atualizar_status("Iniciando conexão...")
        self.atualizar_indicador("yellow", "Conectando...")
        self.atualizar_botoes_status(conectado=False)
        threading.Thread(target=self.conectar_thread, args=(ip,), daemon=True).start()

    def conectar_thread(self, ip):
        self.device = conectar_firetv(ip, self.atualizar_status)
        if self.device:
            self.device_ip = ip
            salvar_ip(ip)
            self.atualizar_indicador("green", f"Conectado ({ip})")
            self.atualizar_botoes_status(conectado=True)
        else:
            self.atualizar_indicador("red", "Desconectado")
            self.atualizar_botoes_status(conectado=False)

    def desconectar(self):
        if self.device_ip:
            desconectar_firetv(self.device_ip)
            self.device = None
            self.device_ip = None
            self.atualizar_status("Desconectado manualmente.")
            self.atualizar_indicador("red", "Desconectado")
            self.atualizar_botoes_status(conectado=False)

    def varrer_rede(self):
        base_ip = self.ip_entry.get().strip().rsplit('.', 1)[0]
        if not base_ip:
            messagebox.showerror("Erro", "Digite parte do IP base (ex: 192.168.0)")
            return
        self.atualizar_status(f"Iniciando varredura: {base_ip}.0/24")
        self.atualizar_indicador("yellow", "Varredura em andamento...")
        self.atualizar_botoes_status(conectado=False)
        self.btn_scan.config(state="disabled")
        self.btn_conectar.config(state="disabled")
        self.cancelar_varredura = False
        self.progress['maximum'] = 254
        self.progress['value'] = 0
        self.tempo_restante_label.config(text="Estimativa: calculando...")
        self.btn_cancelar.pack(side=tk.LEFT, padx=5)
        threading.Thread(target=self.scan_lan, args=(base_ip,), daemon=True).start()

    def cancelar_scan(self):
        self.cancelar_varredura = True
        self.atualizar_status("Cancelando varredura...")
        self.btn_cancelar.config(state="disabled")

    def scan_lan(self, base_ip):
        encontrados = []
        tempos = []
        total = 254
        for i in range(1, 255):
            if self.cancelar_varredura:
                break
            ip = f"{base_ip}.{i}"
            start_ip = time.time()
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
            tempo_ip = time.time() - start_ip
            tempos.append(tempo_ip)
            progresso = i
            self.root.after(0, lambda p=progresso: self.progress.step(1))
            # Atualiza tempo estimado restante
            media_tempo = sum(tempos)/len(tempos) if tempos else 0
            restante = media_tempo * (total - i)
            mins, secs = divmod(int(restante), 60)
            tempo_str = f"Estimativa restante: {mins}m {secs}s"
            self.root.after(0, lambda t=tempo_str: self.tempo_restante_label.config(text=t))

        self.root.after(0, self.finalizar_scan, encontrados)

    def finalizar_scan(self, encontrados):
        self.progress['value'] = 0
        self.tempo_restante_label.config(text="")
        self.btn_cancelar.pack_forget()
        self.btn_cancelar.config(state="normal")
        self.btn_scan.config(state="normal")
        self.btn_conectar.config(state="normal")
        self.atualizar_indicador("red", "Desconectado")

        if encontrados:
            janela = Toplevel(self.root)
            janela.title("Escolha IP")
            tk.Label(janela, text="Dispositivos encontrados:").pack(padx=10, pady=5)
            combo = ttk.Combobox(janela, values=encontrados, state="readonly", width=30)
            combo.pack(padx=10, pady=5)
            combo.current(0)

            def confirmar():
                ip_escolhido = combo.get()
                if ip_escolhido:
                    self.ip_entry.delete(0, tk.END)
                    self.ip_entry.insert(0, ip_escolhido)
                    janela.destroy()
                    self.iniciar_conexao()
            btn_ok = tk.Button(janela, text="Conectar", command=confirmar)
            btn_ok.pack(pady=10)
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
