import os
import asyncio
import edge_tts
import pygame

# Configurações
VOICE = "pt-BR-FranciscaNeural"
OUTPUT_FILE = "resposta.mp3"

# Inicializa pygame para tocar áudio
pygame.init()
pygame.mixer.init()

async def falar(texto):
    communicate = edge_tts.Communicate(texto, VOICE)
    await communicate.save(OUTPUT_FILE)
    pygame.mixer.music.load(OUTPUT_FILE)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

def iniciar_assistente():
    print("Assistente ativada. Digite 'sair' para encerrar.")
    while True:
        texto = input("Você: ")
        if texto.lower() == "sair":
            print("Encerrando assistente...")
            break
        asyncio.run(falar(texto))

if __name__ == "__main__":
    iniciar_assistente()
