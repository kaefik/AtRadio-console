import subprocess
import signal
import sys
import time

# URL радиостанции
RADIO_URL = "http://retro.volna.top/Retro"

def main():
    # Запуск VLC в фоне без интерфейса
    vlc_process = subprocess.Popen(
        ["vlc\\vlc", "--intf", "dummy", RADIO_URL],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    print(f"Радио запущено (PID: {vlc_process.pid}). Нажмите Ctrl+C для остановки.")
    
    try:
        # Бесконечное ожидание (прерывается по Ctrl+C)
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nОстановка радио...")
    finally:
        # Гарантированное завершение VLC при выходе
        vlc_process.terminate()
        vlc_process.wait()
        print("VLC остановлен.")

if __name__ == "__main__":
    main()