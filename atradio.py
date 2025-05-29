import subprocess
import signal
import sys
import time
import platform
import curses
import csv
from curses import wrapper
import os
from datetime import datetime
import click
import telnetlib
from ui.ui_interface import text_field, select_file_from_list, get_input, show_confirmation


def set_vlc_volume(volume: int):
    try:
        tn = telnetlib.Telnet("localhost", 5000)
        tn.write(f"volume {volume}\n".encode())  # Устанавливаем громкость
        tn.write("quit\n".encode())  # Закрываем соединение
        tn.close()
    except ConnectionRefusedError:
        print("❌ VLC не отвечает. Убедитесь, что запущен с --rc-host")

def load_stations(filename):
    stations = []
    with open(filename, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            stations.append((row['Name'], row['URL']))
    return stations


def save_stations(filename, stations):
    with open(filename, mode='w', encoding='utf-8', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Name', 'URL'])  # Заголовки
        for name, url in stations:
            writer.writerow([name, url])


def vlc_open(vlc_prg, name_station:str):
    # запуск процесса vlc
    return subprocess.Popen(
        [vlc_prg, "--intf", "dummy", "--rc-host", "localhost:5000", name_station],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def main(stdscr, autoplay):

    # Инициализация цветов (перенесено внутрь main)
    curses.start_color()
    curses.use_default_colors()
    
    # Упрощенная цветовая схема для лучшей совместимости
    try:
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Выделенный элемент
        curses.init_pair(2, curses.COLOR_GREEN, -1)  # Играющая станция
    except:
        # Если цвета не поддерживаются, используем атрибуты
        pass
    
    curses.curs_set(0)  # Скрываем курсор
    stations_file = 'data/ru_radio_stations_tatar.csv'
    stations = load_stations(stations_file)
    current_row = 0
    offset = 0
    vlc_process = None
    playing_index = -1  # Индекс проигрываемой станции (-1 - ничего не играет)
    move_mode = False  # Флаг режима перемещения
    moving_index = -1  # Индекс перемещаемой станции
    original_stations = ""
    original_stations_index = -1
    move_mode_playing = False # перемещение станции по спику которая проигрывается
    current_volume = 100  #   громкость воспроизведения

    vlc_prg = ""
    os_name = platform.system()
    vlc_prg = "C:\\Program Files (x86)\\VideoLAN\VLC\\vlc.exe" if os_name == "Windows" else "vlc"
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
    else:
        if not os.path.isfile(vlc_prg):
            print("❌ VLC не установлен! Установите его:")
            print("Скачайте по адресу https://www.videolan.org/vlc/")
            sys.exit(1)

    stdscr.keypad(True)

    if autoplay > -1 and autoplay<len(stations):
        playing_index = autoplay
        # Запускаем  автоматическое проигрывание станции
        vlc_process = vlc_open(vlc_prg, stations[playing_index][1])

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

            max_display = h - 6  # -4 для заголовка, статуса и строки состояния

            # Корректируем смещение для прокрутки
            if current_row < offset:
                offset = current_row
            elif current_row >= offset + max_display:
                offset = current_row - max_display + 1

            # Отображаем заголовок
            title = "Список радиостанций"
            sub_title = "(Enter - играть, ESC - остановить, q - выход)"
            title_x = max(0, w//2 - len(title)//2)
            stdscr.addstr(0, title_x, title, curses.A_BOLD)
            sub_title_x = max(0, w//2 - len(sub_title)//2)
            stdscr.addstr(1, sub_title_x, sub_title, curses.A_DIM)

            # Отображаем список станций
            for idx in range(offset, min(offset + max_display, len(stations))):
                name, url = stations[idx]
                x = max(0, w//2 - len(name)//2)
                y = idx - offset + 3
                
                try:
                    if idx == current_row:
                        # Выделенный элемент
                        if move_mode:
                            # В режиме перемещения - особое выделение
                            try:
                                stdscr.addstr(y, x, name, curses.color_pair(1) | curses.A_BLINK)
                            except:
                                stdscr.addstr(y, x, name, curses.A_REVERSE | curses.A_BLINK)
                        else:
                            try:
                                stdscr.addstr(y, x, name, curses.color_pair(1))
                            except:
                                stdscr.addstr(y, x, name, curses.A_REVERSE)
                    elif idx == playing_index:
                        # Играющая станция - жирный или цвет
                        try:
                            stdscr.addstr(y, x, name, curses.color_pair(2) | curses.A_BOLD)
                        except:
                            stdscr.addstr(y, x, name, curses.A_BOLD)
                    else:
                        stdscr.addstr(y, x, name)

                    # Добавляем значок проигрывания
                    if idx == playing_index:
                        try:
                            stdscr.addstr(y, x-2, "▶ ")
                        except:
                            pass
                except curses.error:
                    pass

            # Строка состояния проигрывания
            status_line = h-3
            if playing_index >= 0:
                if move_mode_playing:
                    status_text = f"Сейчас играет: {stations[moving_index][0]} ->  громкость {current_volume} из 512"
                else:
                    if not move_mode:
                        status_text = f"Сейчас играет: {stations[playing_index][0]} ->  громкость {current_volume} из 512"

                try:
                    stdscr.addstr(status_line, 0, status_text, curses.color_pair(2) | curses.A_BOLD)
                except:
                    stdscr.addstr(status_line, 0, status_text, curses.A_BOLD)
            else:
                stdscr.addstr(status_line, 0, "Готов к проигрыванию", curses.A_DIM)

            # Статусная строка (информация о выбранной станции)
            status = f"Выбрано: {stations[current_row][0]} [{current_row + 1}/{len(stations)}]"
            url_display = stations[current_row][1]
            max_url_len = w - len(status) - 2
            if max_url_len > 0 and len(url_display) > max_url_len:
                url_display = url_display[:max_url_len-3] + "..."
            
            try:
                stdscr.addstr(h-2, 0, status)
                stdscr.addstr(h-2, len(status)+1, url_display, curses.A_DIM)
            except curses.error:
                pass
            

            # Строка подсказки функц клавиш
            help_line = " Ins: добавить | Del: удалить | F2: сохранить |F3: переместить | F4: изменить | F5: загрузить |F10: выход "
            help_line_f3 = " ↑: переместить вверх |  ↓: переместить вниз | Enter: закрепить перемешение  | Esc: отмена перемещения"
            title_x = max(0, w//2 - len(help_line)//2)
            try:
                if move_mode:
                    stdscr.addstr(h-1, title_x, help_line_f3)                
                else:
                    stdscr.addstr(h-1, title_x, help_line)                
            except curses.error:
                pass

            key = stdscr.getch()

             # В режиме перемещения обрабатываем клавиши вверх/вниз
            if move_mode:
                if key == curses.KEY_UP and moving_index > 0:
                    # Перемещаем станцию вверх
                    stations[moving_index], stations[moving_index-1] = stations[moving_index-1], stations[moving_index]
                    moving_index -= 1
                    current_row = moving_index
                    if playing_index == moving_index: # когда перемещем станцию выше проигрывающую
                        playing_index += 1
                elif key == curses.KEY_DOWN and moving_index < len(stations)-1:
                    # Перемещаем станцию вниз
                    stations[moving_index], stations[moving_index+1] = stations[moving_index+1], stations[moving_index]
                    moving_index += 1
                    current_row = moving_index
                    if playing_index == moving_index: # когда перемещем станцию ниже проигрывающую
                        playing_index -= 1
                elif key in [curses.KEY_ENTER, 10, 13]:
                    # Сохраняем изменения по Enter
                    save_stations(stations_file, stations)
                    if move_mode_playing:
                        playing_index = moving_index
                    move_mode = False
                    moving_index = -1
                    move_mode_playing = False                    
                elif key == 27:  # ESC - отмена изменений
                    # Восстанавливаем исходный порядок
                    stations = original_stations.copy()
                    # playing_index = original_stations_index
                    current_row = moving_index  # Возвращаем курсор на исходную позицию
                    move_mode = False
                    moving_index = -1
                    move_mode_playing = False
            else:
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
                    vlc_process = vlc_open(vlc_prg, stations[current_row][1])
                elif key == 27:  # ESC - остановить проигрывание
                    if vlc_process and vlc_process.poll() is None:
                        vlc_process.terminate()
                        vlc_process.wait()
                        playing_index = -1
                elif key in [ord('q'), 274]:
                    if playing_index >= 0:  # Если что-то играет - только остановить
                        if vlc_process and vlc_process.poll() is None:
                            vlc_process.terminate()
                            vlc_process.wait()
                        playing_index = -1
                    break
                elif key == 331:
                    # Добавление новой станции Ins
                    stdscr.clear()
                    h, w = stdscr.getmaxyx()
                    
                    # Получаем название станции
                    name_prompt = "Название станции: "
                    name_y = h//2 - 1
                    name_x = w//2 - len(name_prompt)//2
                    stdscr.addstr(name_y, name_x, name_prompt)
                    name = text_field(stdscr, name_y, name_x+len(name_prompt), 50, "")
                    
                    if name:
                        # Получаем URL станции
                        url_prompt = "URL станции: "
                        url_y = h//2 + 1
                        url_x = w//2 - len(url_prompt)//2
                        stdscr.addstr(url_y, url_x, url_prompt)
                        url = text_field(stdscr, url_y, url_x+len(url_prompt), 50, "")
                        
                        if url:
                            # Добавляем новую станцию
                            stations.append((name, url))
                            save_stations(stations_file, stations)
                            
                            # Обновляем текущую строку
                            current_row = len(stations) - 1
                elif key == 330:
                # Удаление текущей станции с подтверждением Del
                    if len(stations) > 0:
                        choice = show_confirmation(stdscr, f"Удалить станцию: {stations[current_row][0]}?")
                        if choice == 0:  # Да
                            # Останавливаем воспроизведение, если удаляем играющую станцию
                            if playing_index == current_row:
                                if vlc_process and vlc_process.poll() is None:
                                    vlc_process.terminate()
                                    vlc_process.wait()
                                playing_index = -1
                            
                            # Удаляем станцию
                            del stations[current_row]
                            save_stations(stations_file, stations)
                            
                            # Корректируем позицию курсора
                            if current_row >= len(stations):
                                current_row = max(0, len(stations) - 1)
                            # Корректируем индекс играющей станции
                            if playing_index > current_row:
                                playing_index -= 1

                        stdscr.touchwin()
                        stdscr.refresh()
                elif key == 267: 
                    # Вход в режим перемещения станции F3
                    move_mode = True                    
                    moving_index = current_row
                    original_stations = stations.copy()  # Сохраняем исходный порядок
                    if playing_index == current_row:
                        print("перемещаем то что проигрывается")
                        move_mode_playing = True
                    
                elif key == curses.KEY_F4:
                    # Редактирование текущей станции
                    if len(stations) > 0:
                        stdscr.clear()
                        h, w = stdscr.getmaxyx()
                        editing = True
                        edit_step = 1  # 1 - редактирование названия, 2 - редактирование URL
                        
                        # Сохраняем оригинальные значения на случай отмены
                        original_name, original_url = stations[current_row]
                        new_name, new_url = original_name, original_url

                        # Шаг 1: Редактирование названия
                        prompt = "Редактирование названия (Enter - подтвердить, Esc - отмена):"
                        stdscr.addstr(h//2 - 2, w//2 - len(prompt)//2, prompt)                        
                        width= len(new_name) if len(new_name)>50 else 50
                        new_name =text_field(stdscr, h//2, w//2 - len(new_name)//2, width, new_name)

                        # Шаг 2: Редактирование URL
                        stdscr.clear()
                        prompt = "Редактирование URL (Enter - подтвердить, Esc - отмена):"
                        stdscr.addstr(h//2 - 2, w//2 - len(prompt)//2, prompt)
                        #stdscr.addstr(h//2, w//2 - len(new_url)//2, new_url, curses.A_BOLD)
                        width= len(new_url) if len(new_url)>50 else 50
                        new_url = text_field(stdscr, h//2, w//2 - len(new_url)//2, width, new_url)

                        if new_name and new_url:
                            # Сохраняем изменения
                            stations[current_row] = (new_name, new_url)
                            save_stations(stations_file, stations)
                elif key == curses.KEY_F2: 
                    # сохранение станций в файл
                    stdscr.clear()
                    current_date = datetime.now().strftime("%Y%m%d")
                    prompt = "Введите имя файла для сохранения станций:"
                    stdscr.addstr(h//2 - 2, w//2 - len(prompt)//2, prompt)                
                    filename = f"{current_date}-radio_stations"
                    width = 50
                    new_filename = text_field(stdscr, h//2, w//2 - len(filename)//2, width, filename)
                    if new_filename and len(new_filename)>0:                        
                        filename = f"{new_filename}.csv"
                        save_stations(filename, stations)

                elif key == curses.KEY_F5:  # Загрузка станций из файла
                    # Получаем список CSV файлов в текущей директории
                    files = [f for f in os.listdir() if f.endswith('.csv')]
                    if files:
                        selected_file = select_file_from_list(stdscr, files)
                        if selected_file:
                            try:
                                new_stations = load_stations(selected_file)
                                stations = new_stations
                                save_stations(stations_file, stations)  # Сохраняем в основной файл
                                current_row = 0  # Сбрасываем позицию курсора
                                playing_index = -1  # Сбрасываем воспроизведение
                                if vlc_process and vlc_process.poll() is None:
                                    vlc_process.terminate()
                                    vlc_process.wait()
                            except Exception as e:
                                # Показываем сообщение об ошибке
                                h, w = stdscr.getmaxyx()
                                error_msg = f"Ошибка загрузки файла: {str(e)}"
                                stdscr.addstr(h-1, 0, error_msg, curses.A_BOLD | curses.color_pair(1))
                                stdscr.getch()
                    else:
                        h, w = stdscr.getmaxyx()
                        error_msg = "Нет CSV файлов в текущей директории"
                        stdscr.addstr(h-1, 0, error_msg, curses.A_BOLD | curses.color_pair(1))
                        stdscr.getch()
                elif key == ord("+"):
                    if playing_index >= 0:
                        current_volume = min(current_volume + 10, 512)  # +10%
                        set_vlc_volume(current_volume)
                elif key == ord("-"):
                    if playing_index >= 0:
                        current_volume = max(current_volume - 10, 0)  # -10%
                        set_vlc_volume(current_volume)

        except KeyboardInterrupt:
            if vlc_process and vlc_process.poll() is None:
                vlc_process.terminate()
                vlc_process.wait()
            break

@click.command()
@click.option('--autoplay', default=-1, help='Автопроигрывание номера заданной станции нумерация от 0')
def _main(autoplay):
    try:
        stdscr = curses.initscr()
        main(stdscr=stdscr, autoplay=autoplay)
    finally:
        curses.endwin()

if __name__ == "__main__":
    _main()