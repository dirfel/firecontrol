# 🔥 Controle Fire TV Stick via ADB com Interface Gráfica

Este projeto permite controlar seu dispositivo **Amazon Fire TV Stick** através do **ADB (Android Debug Bridge)** usando uma interface gráfica feita em **Tkinter** com **Python**. Ele suporta controle remoto, envio de texto, captura de tela, varredura automática de dispositivos na rede, e muito mais.

## 🚀 Recursos

- Controle remoto completo com botões (cima, baixo, OK, etc.)
- Envio de texto à TV
- Captura de tela com visualização integrada
- Varredura da LAN para encontrar dispositivos Fire TV
- Indicação visual de status (conectado, desconectado, conectando)
- Barra de progresso com tempo estimado na varredura
- Persistência do último IP conectado

---

## 📦 Requisitos

- Windows 10 ou superior
- Python 3.9 ou superior
- Dispositivo Fire TV com **depuração ADB ativada**
- Ambos os dispositivos (PC e Fire TV) conectados na mesma rede Wi-Fi

---

## 🛠️ Como instalar e executar

### 1. Clone o repositório:

```bash
git clone https://github.com/dirfel/firecontrol.git
cd firecontrol
```

### 2. Crie e ative um ambiente virtual (venv):

```bash
# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Instale as dependências:

```bash
pip install -r requirements.txt
```

### 4. Execute o programa:

```bash
python main.py
```

---

## 📺 Como ativar a depuração ADB na Fire TV

1. Vá para **Configurações > Meu Fire TV > Opções do desenvolvedor**
2. Ative **Depuração ADB**
3. Anote o IP do Fire TV (está em **Configurações > Rede**)
4. Ao se conectar pela primeira vez, a TV mostrará um aviso pedindo permissão. Aceite.

---

## 🧪 Estrutura do projeto

```
firetv-control-gui/
├── main.py
├── adb_utils.py
├── config.py
├── firetv_gui.py
├── gui.py
├── scan_lan.py
├── comandos.json       # (opcional) comandos personalizados
├── requirements.txt
└── README.md
```

---

## ❗ Observações

- A biblioteca `pure-python-adb` não requer instalação do ADB externo.
- Se quiser adicionar **comandos personalizados**, edite o arquivo `comandos.json`.

---

## 📃 Licença

Este projeto está sob a licença MIT. Sinta-se à vontade para usar e modificar conforme necessário.

---

## ✨ Créditos

Desenvolvido por [Dirfel](https://github.com/dirfel).
