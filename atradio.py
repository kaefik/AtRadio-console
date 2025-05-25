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


def main(stdscr):
    curses.curs_set(0)  # Скрываем курсор
    stations = load_stations('data/ru_radio_stations_tatar.csv')
    current_row = 0
    offset = 0
    vlc_process = None
    playing_index = -1  # Индекс проигрываемой станции (-1 - ничего не играет)


    vlc_prg = ""
    os_name = platform.system()
    vlc_prg = "vlc.exe" if os_name == "Windows" else "vlc"
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

            max_display = h - 4  # -4 для заголовка, статуса и строки состояния

            # Корректируем смещение для прокрутки
            if current_row < offset:
                offset = current_row
            elif current_row >= offset + max_display:
                offset = current_row - max_display + 1

            # Отображаем заголовок
            title = "Список радиостанций"
            sub_title = "(Enter - играть, ESC - остановить, q - выход)"
            title_x = max(0, w//2 - len(title)//2)
            stdscr.addstr(0, title_x, title)
            sub_title_x = max(0, w//2 - len(sub_title)//2)
            stdscr.addstr(1, sub_title_x, sub_title)

            # Отображаем список станций
            for idx in range(offset, min(offset + max_display, len(stations))):
                name, url = stations[idx]
                x = max(0, w//2 - len(name)//2)
                y = idx - offset + 3
                
                try:
                    if idx == current_row:
                        attr = curses.color_pair(1)
                    elif idx == playing_index:
                        attr = curses.color_pair(2) | curses.A_BOLD
                    else:
                        attr = curses.A_NORMAL

                    stdscr.attron(attr)
                    stdscr.addstr(y, x, name)
                    stdscr.attroff(attr)
                    
                    # Добавляем значок проигрывания
                    if idx == playing_index:
                        stdscr.addstr(y, x-2, "▶ ")
                except curses.error:
                    pass

            # Строка состояния проигрывания
            status_line = h-2
            if playing_index >= 0:
                status_text = f"Сейчас играет: {stations[playing_index][0]}"
                stdscr.addstr(status_line, 0, status_text, curses.color_pair(2))
            else:
                stdscr.addstr(status_line, 0, "Готов к проигрыванию", curses.A_DIM)

            # Статусная строка (информация о выбранной станции)
            status = f"Выбрано: {stations[current_row][0]} [{current_row + 1}/{len(stations)}]"
            url_display = stations[current_row][1]
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
                # Останавливаем предыдущее проигрывание, если есть
                if vlc_process and vlc_process.poll() is None:
                    vlc_process.terminate()
                    vlc_process.wait()
                
                # Запускаем новую станцию
                playing_index = current_row
                vlc_process = subprocess.Popen(
                    [vlc_prg, "--intf", "dummy", stations[current_row][1]],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            elif key == 27:  # ESC - остановить проигрывание
                if vlc_process and vlc_process.poll() is None:
                    vlc_process.terminate()
                    vlc_process.wait()
                    playing_index = -1
            elif key == ord('q'):
                if playing_index >= 0:  # Если что-то играет - только остановить
                    if vlc_process and vlc_process.poll() is None:
                        vlc_process.terminate()
                        vlc_process.wait()
                    playing_index = -1
                break

        except KeyboardInterrupt:
            if vlc_process and vlc_process.poll() is None:
                vlc_process.terminate()
                vlc_process.wait()
            break

# if __name__ == "__main__":
#     try:
#         # Инициализация curses с дополнительными цветами
#         curses.wrapper(main)
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         try:
#             curses.endwin()
#         except:
#             pass


if __name__ == "__main__":

    # Инициализация curses
    curses.initscr()
    curses.noecho()
    curses.cbreak()
    curses.start_color()        
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Для выделения
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Для играющей станции
    
    curses.wrapper(main)
    
   