import subprocess
import signal
import sys
import time
import platform

# URL радиостанции
RADIO_URL = "http://retro.volna.top/Retro"

def main():

    vlc_prg = ""
    os_name = platform.system()

    if os_name == "Windows":
        vlc_prg = "vlc\\vlc.exe"  # Обычно VLC в Windows имеет расширение .exe
    elif os_name == "Linux" or os_name == "Darwin":
        vlc_prg = "vlc"
    else:
        print(f"❌ Неизвестная ОС: {os_name}")
        sys.exit(1)

    try:
        # Проверяем, есть ли VLC в системе (только для Linux/macOS)
        if os_name != "Windows":
            check_installed = subprocess.run(
                ["which", vlc_prg],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            if check_installed.returncode != 0:
                print("❌ VLC не установлен! Установите его:")
                if os_name == "Linux":
                    print("  sudo apt install vlc  # для Debian/Ubuntu")
                    print("  sudo dnf install vlc  # для Fedora")
                elif os_name == "Darwin":
                    print("  brew install vlc      # через Homebrew")
                sys.exit(1)

        # Запуск VLC в фоне
        vlc_process = subprocess.Popen(
            [vlc_prg, "--intf", "dummy", RADIO_URL],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Проверяем, не завершился ли процесс сразу (ошибка запуска)
        if vlc_process.poll() is not None:
            stderr_output = vlc_process.stderr.read().decode("utf-8")
            print(f"❌ Ошибка запуска VLC:\n{stderr_output}")
            sys.exit(1)

        print("✅ VLC успешно запущен в фоновом режиме!")
        # Дальнейший код (ожидание, завершение и т. д.)

    except FileNotFoundError:
        print("❌ VLC не найден! Убедитесь, что он установлен и добавлен в PATH.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Неизвестная ошибка: {e}")
        sys.exit(1)
    
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