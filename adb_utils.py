import os
import time
from ppadb.client import Client as AdbClient

client = AdbClient(host="127.0.0.1", port=5037)

def conectar_firetv(ip, log_func):
    try:
        log_func(f"Tentando conectar ao dispositivo {ip}...")
        os.system(f"adb connect {ip}")
        time.sleep(1)
        devices = client.devices()
        for device in devices:
            if device.serial == ip + ":5555":
                if device.get_state() == "device":
                    log_func("Dispositivo conectado com sucesso.")
                    return device
                elif device.get_state() == "unauthorized":
                    log_func("Dispositivo não autorizado. Confirme no Fire TV.")
                    return None
        log_func("Dispositivo não encontrado ou não autorizado.")
    except Exception as e:
        log_func(f"Erro na conexão: {e}")
    return None

def desconectar_firetv(ip):
    os.system(f"adb disconnect {ip}")

def enviar_comando(device, comando, comandos_map, log_func):
    if not device:
        log_func("Dispositivo não conectado.")
        return
    if comando in comandos_map:
        try:
            device.shell(comandos_map[comando])
            log_func(f"Comando '{comando}' enviado.")
        except Exception as e:
            log_func(f"Erro ao enviar comando: {e}")
    else:
        log_func(f"Comando '{comando}' não encontrado no mapa.")

def enviar_texto(device, texto, log_func):
    if not device:
        log_func("Dispositivo não conectado.")
        return
    try:
        for c in texto:
            if c == ' ':
                device.shell("input keyevent 62")
            else:
                device.shell(f'input text \"{c}\"')
                time.sleep(0.1)
        log_func(f"Texto enviado: {texto}")
    except Exception as e:
        log_func(f"Erro ao enviar texto: {e}")

def capturar_tela(device, atualizar_status, callback_imagem):
    try:
        atualizar_status("Capturando tela...")
        remote_path = "/sdcard/screenshot.png"
        local_path = "screenshot.png"  # caminho local onde salvar

        device.shell(f"screencap -p {remote_path}")
        device.pull(remote_path, local_path)
        atualizar_status(f"Tela capturada salva em {local_path}")
        callback_imagem(local_path)
    except Exception as e:
        atualizar_status(f"Erro na captura de tela: {e}")
