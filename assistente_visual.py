import os
import time
import json
import queue
import threading
import asyncio
import edge_tts
import pygame
import sounddevice as sd
import keyboard
from vosk import Model, KaldiRecognizer
from colorama import Fore, Style, init
import subprocess
from datetime import datetime
import pytz # Certifique-se de que 'pip install pytz' foi executado
import webbrowser # Nova importação para abrir URLs

# --- Inicialização do Colorama ---
init(autoreset=True) # Inicializa Colorama para resetar cores automaticamente no terminal

# --- Configurações de Voz (Edge TTS) ---
# Você pode mudar para "pt-BR-BrendaNeural" ou "en-US-JennyNeural"
VOICE = "pt-BR-FranciscaNeural" 
OUTPUT_FILE = "astra_resposta_audio.mp3"

# Inicializa pygame para tocar áudio
pygame.init()
pygame.mixer.init()

# --- Configurações de Reconhecimento de Voz (Vosk) ---
MODEL_PATH = "model" # Pasta onde o modelo Vosk está
if not os.path.exists(MODEL_PATH):
    print(f"{Fore.RED}Erro: Pasta '{MODEL_PATH}' do modelo Vosk não encontrada!{Style.RESET_ALL}")
    print("Por favor, baixe e extraia o modelo vosk-model-small-pt-0.3.zip")
    print("em uma pasta chamada 'model' no mesmo diretório do script.")
    exit()

try:
    vosk_model = Model(MODEL_PATH)
    vosk_recognizer = KaldiRecognizer(vosk_model, 16000) # 16000 é a taxa de amostragem padrão
except Exception as e:
    print(f"{Fore.RED}Erro ao carregar o modelo Vosk: {e}{Style.RESET_ALL}")
    print("Verifique se o modelo está completo e na pasta 'model'.")
    exit()

audio_queue = queue.Queue() # Fila para armazenar os dados de áudio do microfone

def callback_audio(indata, frames, time_, status):
    """Callback para sounddevice que coloca os dados de áudio na fila."""
    if status:
        print(status, flush=True) 
    audio_queue.put(bytes(indata))

def ouvir_comando_vosk():
    """Ouve o microfone e reconhece o comando usando Vosk."""
    global estado_assistente
    estado_assistente = "ouvindo"
    
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback_audio):
        
        # Limpa a fila antes de começar a ouvir para evitar áudio antigo
        with audio_queue.mutex:
            audio_queue.queue.clear() 
        
        start_time = time.time()
        timeout = 5 # Tempo máximo para ouvir (em segundos)
        
        # Desenha a interface "ouvindo" antes de começar a ouvir
        desenhar_interface("Status: Ouvindo...") 

        print(f"{Fore.GREEN}>> Diga algo para a ASTRA... (ou aperte F10 novamente para cancelar){Style.RESET_ALL}")

        while True:
            # Verifica se F10 foi pressionado novamente para cancelar
            if keyboard.is_pressed("F10") and (time.time() - start_time > 1): # Pequeno delay para evitar duplo clique
                print(f"{Fore.YELLOW}Escuta cancelada.{Style.RESET_ALL}")
                return ""

            try:
                data = audio_queue.get(timeout=timeout) # Pega dados da fila com timeout
                if vosk_recognizer.AcceptWaveform(data):
                    resultado = json.loads(vosk_recognizer.Result())
                    comando = resultado.get("text", "")
                    if comando:
                        print(f"{Fore.CYAN}Você disse:{Style.RESET_ALL} {comando}")
                        return comando
            except queue.Empty:
                print(f"{Fore.YELLOW}Tempo esgotado para o comando. Tente novamente.{Style.RESET_ALL}")
                return ""
            except Exception as e:
                print(f"{Fore.RED}Erro durante o reconhecimento de voz: {e}{Style.RESET_ALL}")
                return ""
    return ""

# --- Funções de Voz e Áudio ---
async def falar_astra(texto):
    """Gera e toca o áudio da ASTRA."""
    global estado_assistente
    estado_assistente = "falando"
    
    print(f"{Fore.CYAN}ASTRA:{Style.RESET_ALL} {texto}")
    
    communicate = edge_tts.Communicate(text=texto, voice=VOICE)
    await communicate.save(OUTPUT_FILE)
    
    pygame.mixer.music.load(OUTPUT_FILE)
    pygame.mixer.music.play()
    
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)
    
    # Garante que o Pygame libere o arquivo antes de tentar removê-lo
    pygame.mixer.music.stop()   
    pygame.mixer.music.unload() 
    
    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)
    
    estado_assistente = "ocioso" # Volta para ocioso após falar

# --- Interface ASCII Animada (Símbolos e Expressões) ---

# Carinhas para as expressões (ajustadas para serem "grandes" com espaços)
EMOJI_OCIO = ["  (owo)  ", "  (^w^)  ", "  (-w-)  "] # Padding para centralizar no retângulo
EMOJI_OUVINDO = ["  >.<  ", "  o.o  "] # Padding para centralizar no hexágono
EMOJI_PROCESSANDO = ["  ...  ", "  o.O  "] # Padding para centralizar no hexágono
EMOJI_FALANDO = ["  ^.^  ", "  o.o  "] # Padding para centralizar no círculo
EMOJI_ERRO = ["  >.<  ", "  X.X  "] # Padding para centralizar no triângulo

# Quadros de animação do símbolo (Formas geométricas com expressões)
# A forma base determina o estado principal.
    
# RETÂNGULO (Ocioso / Dormindo) - Substitui o quadrado
ASCII_FRAMES_OCIOSO = [
    f"{Fore.WHITE}╔═══════════════════════════╗{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║         {Fore.CYAN}{EMOJI_OCIO[0]}{Fore.WHITE}         ║{Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}╚═══════════════════════════╝{Style.RESET_ALL}",

    f"{Fore.WHITE}╔═══════════════════════════╗{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║         {Fore.CYAN}{EMOJI_OCIO[1]}{Fore.WHITE}         ║{Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}╚═══════════════════════════╝{Style.RESET_ALL}",

    f"{Fore.WHITE}╔═══════════════════════════╗{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║         {Fore.CYAN}{EMOJI_OCIO[2]}{Fore.WHITE}         ║{Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}║                           ║{Style.RESET_ALL}\n"
    f"{Fore.WHITE}╚═══════════════════════════╝{Style.RESET_ALL}",
]

# HEXÁGONO (Processando / Pensando) - Com emoji centrado
ASCII_FRAMES_PENSANDO = [
    f"{Fore.YELLOW}           _____          {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}           /     \\          {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}          /       \\         {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}    ,----(         )----.   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  \\        /     \\        / {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   \\      / {EMOJI_PROCESSANDO[0]} \\      /  {Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.YELLOW}    )----(         )----(   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  \\        /     \\        / {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   \\      /       \      /  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}    `----(         )----'   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}          \\       /         {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}           \\_____/          {Style.RESET_ALL}",

    f"{Fore.YELLOW}           _____          {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}           /     \\          {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}          /       \\         {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}    ,----(         )----.   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  \\        /     \\        / {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   \\      / {EMOJI_PROCESSANDO[1]} \\      /  {Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.YELLOW}    )----(         )----(   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}  \        /     \        / {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}   \      /       \      /  {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}    `----(         )----'   {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}          \\       /         {Style.RESET_ALL}\n"
    f"{Fore.YELLOW}           \\_____/          {Style.RESET_ALL}",
]

# HEXÁGONO (Ouvindo) - Usando variação com EMOJI_OUVINDO
ASCII_FRAMES_OUVINDO = [
    f"{Fore.GREEN}           _____          {Style.RESET_ALL}\n"
    f"{Fore.GREEN}           /     \\          {Style.RESET_ALL}\n"
    f"{Fore.GREEN}          /       \\         {Style.RESET_ALL}\n"
    f"{Fore.GREEN}    ,----(         )----.   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  \\        /     \\        / {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   \\      / {EMOJI_OUVINDO[0]} \\      /  {Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.GREEN}    )----(         )----(   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  \        /     \        / {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   \      /       \      /  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}    `----(         )----'   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}          \\       /         {Style.RESET_ALL}\n"
    f"{Fore.GREEN}           \\_____/          {Style.RESET_ALL}",

    f"{Fore.GREEN}           _____          {Style.RESET_ALL}\n"
    f"{Fore.GREEN}           /     \\          {Style.RESET_ALL}\n"
    f"{Fore.GREEN}          /       \\         {Style.RESET_ALL}\n"
    f"{Fore.GREEN}    ,----(         )----.   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  \\        /     \\        / {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   \\      / {EMOJI_OUVINDO[1]} \\      /  {Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.GREEN}    )----(         )----(   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   /      \\       /      \\  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  /        \\_____/        \\ {Style.RESET_ALL}\n"
    f"{Fore.GREEN}  \        /     \        / {Style.RESET_ALL}\n"
    f"{Fore.GREEN}   \      /       \      /  {Style.RESET_ALL}\n"
    f"{Fore.GREEN}    `----(         )----'   {Style.RESET_ALL}\n"
    f"{Fore.GREEN}          \\       /         {Style.RESET_ALL}\n"
    f"{Fore.GREEN}           \\_____/          {Style.RESET_ALL}",
]


# CÍRCULO (Falando) - Com emoji centrado
ASCII_FRAMES_FALANDO = [
    f"{Fore.BLUE}                   ooo OOO OOO ooo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}               oOO                 OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}           oOO                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}        oOO                               OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}      oOO                                   OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}    oOO                                       OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}   oOO                                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}  oOO                                           OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                {EMOJI_FALANDO[0]}                OOo{Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}  oOO                                           OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}   oOO                                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}    oOO                                       OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}      oOO                                   OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}        oO                                OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}           oOO                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}               oOO                 OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}                   ooo OOO OOO ooo{Style.RESET_ALL}",

    f"{Fore.BLUE}                   ooo OOO OOO ooo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}               oOO                 OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}           oOO                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}        oOO                               OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}      oOO                                   OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}    oOO                                       OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}   oOO                                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}  oOO                                           OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                {EMOJI_FALANDO[1]}                OOo{Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE} oOO                                             OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}  oOO                                           OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}   oOO                                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}    oOO                                       OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}      oOO                                   OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}        oO                                OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}           oOO                         OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}               oOO                 OOo{Style.RESET_ALL}\n"
    f"{Fore.BLUE}                   ooo OOO OOO ooo{Style.RESET_ALL}",
]

# TRIÂNGULO (Erro / Não Entendeu) - Versão simplificada para emoji
# Ajustado para garantir alinhamento e centralização da carinha
ASCII_FRAME_ERRO = (
    f"{Fore.RED}                 /\\                 {Style.RESET_ALL}\n"
    f"{Fore.RED}                /  \\                {Style.RESET_ALL}\n"
    f"{Fore.RED}               /    \\               {Style.RESET_ALL}\n"
    f"{Fore.RED}              / {EMOJI_ERRO[0]} \\              {Style.RESET_ALL}\n" # Centered emoji
    f"{Fore.RED}             /        \\             {Style.RESET_ALL}\n"
    f"{Fore.RED}            /__________\\            {Style.RESET_ALL}"
)


# Estado global da assistente para controlar a animação
estado_assistente = "ocioso" 
frame_idx = 0 

def desenhar_interface(mensagem_status=""):
    """
    Desenha o símbolo ASCII e as informações de status no terminal.
    """
    global frame_idx
    os.system('cls' if os.name == 'nt' else 'clear') 

    # Título da ASTRA
    print(f"{Fore.MAGENTA}{Style.BRIGHT}")
    print("   .--.      .--. ")
    print("  /    \\    /    \\")
    print(" |  A  S  T  R  A  |")
    print("  \\____/    \\____/")
    print(f"{Style.RESET_ALL}\n")

    # Define o frame do símbolo com base no estado e na animação
    simbolo_ascii = ""
    if estado_assistente == "ocioso":
        simbolo_ascii = ASCII_FRAMES_OCIOSO[frame_idx % len(ASCII_FRAMES_OCIOSO)]
        frame_idx = (frame_idx + 1) % len(ASCII_FRAMES_OCIOSO)
    elif estado_assistente == "ouvindo":
        simbolo_ascii = ASCII_FRAMES_OUVINDO[frame_idx % len(ASCII_FRAMES_OUVINDO)]
        frame_idx = (frame_idx + 1) % len(ASCII_FRAMES_OUVINDO)
    elif estado_assistente == "processando":
        simbolo_ascii = ASCII_FRAMES_PENSANDO[frame_idx % len(ASCII_FRAMES_PENSANDO)]
        frame_idx = (frame_idx + 1) % len(ASCII_FRAMES_PENSANDO)
    elif estado_assistente == "falando":
        simbolo_ascii = ASCII_FRAMES_FALANDO[frame_idx % len(ASCII_FRAMES_FALANDO)]
        frame_idx = (frame_idx + 1) % len(ASCII_FRAMES_FALANDO)
    elif estado_assistente == "erro":
        simbolo_ascii = ASCII_FRAME_ERRO
        # Para o erro, não queremos animação contínua no símbolo, apenas o X.X
    else: # Fallback para ocioso
        simbolo_ascii = ASCII_FRAMES_OCIOSO[frame_idx % len(ASCII_FRAMES_OCIOSO)]
        frame_idx = (frame_idx + 1) % len(ASCII_FRAMES_OCIOSO)

    print(simbolo_ascii)
    print("\n")
    
    # Exibe a mensagem de status
    print(f"{Fore.WHITE}{mensagem_status}{Style.RESET_ALL}")


def loop_animacao():
    """
    Loop em uma thread separada para manter a animação da interface rodando.
    """
    while True:
        # A animação só deve desenhar se o estado não for 'digitando' (input)
        if estado_assistente != "digitando": 
            desenhar_interface(f"Status: {estado_assistente.capitalize()}...")
        
        if estado_assistente == "ocioso":
            time.sleep(0.8) # Quadrado "dormindo" mais lento
        elif estado_assistente == "ouvindo":
            time.sleep(0.4) # Hexágono ouvindo mais rápido
        elif estado_assistente == "processando":
            time.sleep(0.4) # Hexágono pensando mais rápido
        elif estado_assistente == "falando":
            time.sleep(0.5) # Círculo falando
        elif estado_assistente == "erro":
            time.sleep(2) # Triângulo de erro fica mais tempo
        else:
            time.sleep(0.1) # Default para outros estados

# --- Funções de Ação e Lógica ---
def executar_comando(comando):
    """
    Processa e executa o comando dado à ASTRA.
    """
    global estado_assistente
    comando = comando.lower()

    # --- Comandos de Sites ---
    if "abrir youtube" in comando or "youtube" in comando:
        asyncio.run(falar_astra("Abrindo o YouTube para você."))
        webbrowser.open("https://www.youtube.com") 
        return True
    
    elif "abrir gmail" in comando:
        asyncio.run(falar_astra("Abrindo o Gmail."))
        webbrowser.open("https://mail.google.com")
        return True

    elif "abrir google docs" in comando or "abrir documentos google" in comando:
        asyncio.run(falar_astra("Abrindo o Google Docs."))
        webbrowser.open("https://docs.google.com")
        return True

    elif "abrir youtube music" in comando or "abrir música do youtube" in comando:
        asyncio.run(falar_astra("Abrindo o YouTube Music."))
        webbrowser.open("https://music.youtube.com")
        return True
    
    elif "abrir google drive" in comando or "abrir drive" in comando:
        asyncio.run(falar_astra("Abrindo o Google Drive."))
        webbrowser.open("https://drive.google.com")
        return True

    elif "abrir calendário google" in comando or "abrir calendário" in comando:
        asyncio.run(falar_astra("Abrindo o Calendário Google."))
        webbrowser.open("https://calendar.google.com")
        return True

    # --- Comandos de Aplicativos ---
    elif "abrir discord" in comando:
        asyncio.run(falar_astra("Abrindo o Discord."))
        try:
            # Tenta abrir pelo nome do executável (se estiver no PATH)
            subprocess.Popen(["discord.exe"]) 
        except FileNotFoundError:
            asyncio.run(falar_astra("Não encontrei o Discord. Certifique-se de que ele está instalado e no seu PATH."))
        return True

    elif "abrir spotify" in comando:
        asyncio.run(falar_astra("Abrindo o Spotify."))
        try:
            subprocess.Popen(["spotify.exe"])
        except FileNotFoundError:
            asyncio.run(falar_astra("Não encontrei o Spotify. Certifique-se de que ele está instalado e no seu PATH."))
        return True
    
    elif "abrir steam" in comando:
        asyncio.run(falar_astra("Abrindo o Steam."))
        try:
            subprocess.Popen(["steam.exe"])
        except FileNotFoundError:
            asyncio.run(falar_astra("Não encontrei o Steam. Certifique-se de que ele está instalado e no seu PATH."))
        return True

    elif "abrir bloco de notas" in comando:
        asyncio.run(falar_astra("Abrindo o Bloco de Notas."))
        try:
            os.system("notepad.exe") # Comando universal para Bloco de Notas no Windows
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir o Bloco de Notas. Erro: {e}"))
        return True

    elif "abrir blender" in comando:
        asyncio.run(falar_astra("Abrindo o Blender."))
        try:
            os.system("start blender") 
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir o Blender. Erro: {e}"))
        return True
    
    elif "abrir prompt de comando" in comando or "abrir cmd" in comando:
        asyncio.run(falar_astra("Abrindo o Prompt de Comando."))
        try:
            subprocess.Popen("start \"\" cmd", shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE)
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir o Prompt de Comando. Erro: {e}"))
        return True

    # --- Comandos de Pastas ---
    elif "abrir downloads" in comando:
        asyncio.run(falar_astra("Abrindo a pasta de Downloads."))
        try:
            os.startfile(os.path.join(os.path.expanduser("~"), "Downloads"))
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir a pasta de Downloads. Erro: {e}"))
        return True

    elif "abrir documentos" in comando:
        asyncio.run(falar_astra("Abrindo a pasta de Documentos."))
        try:
            os.startfile(os.path.join(os.path.expanduser("~"), "Documents"))
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir a pasta de Documentos. Erro: {e}"))
        return True
    
    elif "abrir imagens" in comando:
        asyncio.run(falar_astra("Abrindo a pasta de Imagens."))
        try:
            os.startfile(os.path.join(os.path.expanduser("~"), "Pictures"))
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir a pasta de Imagens. Erro: {e}"))
        return True

    elif "abrir vídeos" in comando:
        asyncio.run(falar_astra("Abrindo a pasta de Vídeos."))
        try:
            os.startfile(os.path.join(os.path.expanduser("~"), "Videos"))
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir a pasta de Vídeos. Erro: {e}"))
        return True

    elif "abrir pasta de projetos" in comando:
        asyncio.run(falar_astra("Abrindo sua pasta de projetos."))
        # !!! ATENÇÃO: VOCÊ PRECISA MUDAR ESTE CAMINHO PARA O SEU CAMINHO REAL !!!
        PROJECTS_FOLDER = "C:\\Seu\\Caminho\\Para\\Projetos" 
        try:
            if os.path.exists(PROJECTS_FOLDER):
                os.startfile(PROJECTS_FOLDER)
            else:
                asyncio.run(falar_astra(f"A pasta de projetos '{PROJECTS_FOLDER}' não foi encontrada. Por favor, configure o caminho correto no código."))
        except Exception as e:
            asyncio.run(falar_astra(f"Não consegui abrir a pasta de projetos. Erro: {e}"))
        return True

    # --- Outros Comandos ---
    elif "que horas são" in comando or "horas agora" in comando:
        try:
            timezone = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(timezone) 
        except Exception: 
            now = datetime.now() 
            
        hora = now.strftime("%H:%M")
        asyncio.run(falar_astra(f"Agora são {hora}"))
        return True

    elif "sair" in comando or "desligar assistente" in comando or "tchau astra" in comando:
        asyncio.run(falar_astra("Encerrando ASTRA. Até mais!"))
        return False 

    else:
        asyncio.run(falar_astra("Desculpe, ainda não sei fazer isso."))
        estado_assistente = "erro" 
        time.sleep(1) 
        return True 


# --- Loop Principal da Aplicação ---
def iniciar_astra():
    """
    Inicia a ASTRA, o loop de animação e o loop principal de comandos.
    """
    global estado_assistente

    # Inicia a thread de animação da interface
    animacao_thread = threading.Thread(target=loop_animacao, daemon=True)
    animacao_thread.start()

    # Saudação inicial da ASTRA
    asyncio.run(falar_astra("Olá! Eu sou ASTRA, sua assistente pessoal. Pressione F10 para me dar um comando de voz."))
    
    while True:
        estado_assistente = "ocioso" # ASTRA fica ociosa esperando F10
        desenhar_interface("Status: Pressione F10 para falar...") # Atualiza o status na tela
        
        # Espera o F10 ser pressionado
        keyboard.wait("F10") 
        time.sleep(0.2) # Pequeno atraso para evitar detecção dupla do F10

        # Captura o comando de voz
        comando = ouvir_comando_vosk()
        
        if comando:
            estado_assistente = "processando"
            desenhar_interface("Status: Processando...")
            time.sleep(0.5) # Simula um pequeno atraso no processamento
            
            if not executar_comando(comando):
                break # Sai do loop se o comando for de desligar

        estado_assistente = "ocioso" # Volta para ocioso após executar ou se não houver comando
        time.sleep(0.5) # Pequena pausa antes de voltar a esperar o F10


# --- Ponto de Entrada ---
if __name__ == "__main__":
    iniciar_astra()