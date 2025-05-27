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


def get_input(stdscr, prompt, y, x):
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    input_str = stdscr.getstr(y, x + len(prompt)).decode('utf-8')
    curses.noecho()
    return input_str


def text_field(stdscr, y, x, width, initial_text=""):
    text = list(initial_text)
    cursor_pos = len(text)
    curses.curs_set(1)  # Показываем курсор
    
    while True:
        # Отрисовываем текущий текст
        stdscr.addstr(y, x, " " * width)  # Очищаем область
        stdscr.addstr(y, x, "".join(text)[:width])
        
        # Устанавливаем курсор
        stdscr.move(y, x + min(cursor_pos, width-1))
        
        key = stdscr.getch()
        
        if key in (curses.KEY_ENTER, 10, 13):  # Enter - завершить
            break
        elif key == 27:  # ESC - отмена
            text = list(initial_text)
            break
        elif key == curses.KEY_BACKSPACE or key == 127:
            if cursor_pos > 0:
                text.pop(cursor_pos-1)
                cursor_pos -= 1
        elif key == curses.KEY_DC:  # Delete
            if cursor_pos < len(text):
                text.pop(cursor_pos)
        elif key == curses.KEY_LEFT:
            cursor_pos = max(0, cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            cursor_pos = min(len(text), cursor_pos + 1)
        elif key == curses.KEY_HOME:
            cursor_pos = 0
        elif key == curses.KEY_END:
            cursor_pos = len(text)
        elif 32 <= key <= 126:  # Печатные символы
            text.insert(cursor_pos, chr(key))
            cursor_pos += 1
    
    curses.curs_set(0)  # Скрываем курсор
    return "".join(text)


def main(stdscr):
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
                status_text = f"Сейчас играет: {stations[playing_index][0]}"
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
            help_line = "+:добавить | -: удалить | F3: переместить | F4: изменить | F10: выход "
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
                elif key == curses.KEY_DOWN and moving_index < len(stations)-1:
                    # Перемещаем станцию вниз
                    stations[moving_index], stations[moving_index+1] = stations[moving_index+1], stations[moving_index]
                    moving_index += 1
                    current_row = moving_index
                elif key in [curses.KEY_ENTER, 10, 13]:
                    # Сохраняем изменения по Enter
                    save_stations(stations_file, stations)
                    move_mode = False
                    moving_index = -1
                elif key == 27:  # ESC - отмена изменений
                    # Восстанавливаем исходный порядок
                    stations = original_stations.copy()
                    current_row = moving_index  # Возвращаем курсор на исходную позицию
                    move_mode = False
                    moving_index = -1
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
                elif key in [ord('q'), 274]:
                    if playing_index >= 0:  # Если что-то играет - только остановить
                        if vlc_process and vlc_process.poll() is None:
                            vlc_process.terminate()
                            vlc_process.wait()
                        playing_index = -1
                    break
                elif key == ord('+'):
                    # Добавление новой станции
                    stdscr.clear()
                    h, w = stdscr.getmaxyx()
                    
                    # Получаем название станции
                    name_prompt = "Название станции: "
                    name_y = h//2 - 1
                    name_x = w//2 - len(name_prompt)//2
                    name = get_input(stdscr, name_prompt, name_y, name_x)
                    
                    # Получаем URL станции
                    url_prompt = "URL станции: "
                    url_y = h//2 + 1
                    url_x = w//2 - len(url_prompt)//2
                    url = get_input(stdscr, url_prompt, url_y, url_x)
                    
                    # Добавляем новую станцию
                    stations.append((name, url))
                    save_stations(stations_file, stations)
                    
                    # Обновляем текущую строку
                    current_row = len(stations) - 1
                elif key == ord('-'):
                # Удаление текущей станции с подтверждением
                    if len(stations) > 0:
                        # Создаем окно подтверждения
                        confirm_win = curses.newwin(5, 50, h//2-2, w//2-25)
                        confirm_win.border()
                        confirm_win.addstr(1, 2, f"Удалить станцию: {stations[current_row][0]}?")
                        confirm_win.addstr(3, 10, "[Y] Да    [N] Нет", curses.A_BOLD)
                        confirm_win.refresh()
                        
                        # Ждем ответа пользователя
                        while True:
                            confirm_key = confirm_win.getch()
                            if confirm_key in [ord('y'), ord('Y')]:
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
                                break
                            elif confirm_key in [ord('n'), ord('N'), 27]:  # 27 - ESC
                                break
                        
                        # Закрываем окно подтверждения
                        confirm_win.clear()
                        confirm_win.refresh()
                        del confirm_win
                        stdscr.touchwin()
                        stdscr.refresh()
                elif key == 267:
                    # Вход/выход из режима перемещения
                    move_mode = not move_mode
                    if move_mode:
                        moving_index = current_row
                        original_stations = stations.copy()  # Сохраняем исходный порядок
                    else:
                        moving_index = -1
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
                    filename = new_url = text_field(stdscr, h//2, w//2 - len(filename)//2, width, filename)
                    if len(filename)>0:                        
                        filename = f"{filename}.csv"
                        save_stations(filename, stations)

        except KeyboardInterrupt:
            if vlc_process and vlc_process.poll() is None:
                vlc_process.terminate()
                vlc_process.wait()
            break


if __name__ == "__main__":
    wrapper(main)