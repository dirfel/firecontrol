import json
import os

CONFIG_PATH = "config.json"

def carregar_ip():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("ultimo_ip", "")
        except:
            return ""
    return ""

def salvar_ip(ip):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump({"ultimo_ip": ip}, f)
