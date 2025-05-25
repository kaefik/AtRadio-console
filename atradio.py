import subprocess
import signal
import sys
import time
import platform
import curses
import csv
from curses import wrapper


def load_stations(filename):
    stations = []
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            stations.append((row['Name'], row['URL']))
    return stations

def play_station(radio_url):
    vlc_prg = ""
    os_name = platform.system()

    vlc_prg = "vlc.exe" if os_name == "Windows" else "vlc"

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
            [vlc_prg, "--intf", "dummy", radio_url],
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


def main(stdscr):
    curses.curs_set(0)  # Скрываем курсор
    stations = load_stations('data/ru_radio_stations_tatar.csv')
    current_row = 0
    offset = 0  # Смещение для прокрутки списка

    while True:
        try:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Проверяем минимальный размер терминала
            if h < 5 or w < 40:
                stdscr.addstr(0, 0, "Terminal too small! Please resize.", curses.A_BOLD)
                stdscr.refresh()
                stdscr.getch()
                continue

            # Рассчитываем сколько станций можем показать
            max_display = h - 3  # -3 для заголовка и статусной строки

            # Корректируем смещение, чтобы текущая строка была видна
            if current_row < offset:
                offset = current_row
            elif current_row >= offset + max_display:
                offset = current_row - max_display + 1

            # Отображаем заголовок
            title = "Татарские радиостанции (Enter - играть, q - выход)"
            title_x = max(0, w//2 - len(title)//2)
            stdscr.addstr(0, title_x, title)

            # Отображаем видимую часть списка станций
            for idx in range(offset, min(offset + max_display, len(stations))):
                name, url = stations[idx]
                x = max(0, w//2 - len(name)//2)
                y = idx - offset + 2  # +2 чтобы оставить место для заголовка
                
                try:
                    if idx == current_row:
                        stdscr.attron(curses.color_pair(1))
                        stdscr.addstr(y, x, name)
                        stdscr.attroff(curses.color_pair(1))
                    else:
                        stdscr.addstr(y, x, name)
                except curses.error:
                    pass

            # Показываем подсказку внизу экрана
            status = f"Выбрано: {stations[current_row][0]} [{current_row + 1}/{len(stations)}]"
            url_display = stations[current_row][1]
            
            # Обрезаем URL, если он слишком длинный
            max_url_len = w - len(status) - 2
            if max_url_len > 0 and len(url_display) > max_url_len:
                url_display = url_display[:max_url_len-3] + "..."
            
            try:
                stdscr.addstr(h-1, 0, status)
                stdscr.addstr(h-1, len(status)+1, url_display, curses.A_DIM)
            except curses.error:
                pass

            key = stdscr.getch()

            if key == curses.KEY_UP and current_row > 0:
                current_row -= 1
            elif key == curses.KEY_DOWN and current_row < len(stations)-1:
                current_row += 1
            elif key == curses.KEY_ENTER or key in [10, 13]:
                curses.endwin()
                play_station(stations[current_row][1])
                # Возвращаемся в curses режим
                stdscr = curses.initscr()
                curses.noecho()
                curses.cbreak()
                curses.curs_set(0)
                curses.start_color()
                curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            elif key == ord('q'):
                break

        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    try:
        # Инициализация curses
        curses.initscr()
        curses.noecho()
        curses.cbreak()
        curses.start_color()
        curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
        
        curses.wrapper(main)
    finally:
        # Всегда завершаем curses правильно
        curses.endwin()
   