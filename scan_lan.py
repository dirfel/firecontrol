import socket
import time

def scan_lan_com_cancelamento(base_ip, porta, cancelar_flag, status_callback, progresso_callback):
    encontrados = []
    tempos = []
    total = 254
    for i in range(1, 255):
        if cancelar_flag:
            status_callback("Varredura cancelada pelo usuário.")
            break
        ip = f"{base_ip}.{i}"
        start_ip = time.time()
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, porta))
            sock.close()
            if result == 0:
                encontrados.append(ip)
                status_callback(f"Dispositivo encontrado: {ip}")
        except Exception:
            pass
        tempo_ip = time.time() - start_ip
        tempos.append(tempo_ip)
        progresso = i
        # Calcula tempo restante estimado
        media_tempo = sum(tempos) / len(tempos) if tempos else 0
        restante = media_tempo * (total - i)
        mins, secs = divmod(int(restante), 60)
        tempo_str = f"Estimativa restante: {mins}m {secs}s"
        progresso_callback(progresso, tempo_str)
    return encontrados
