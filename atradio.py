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
from ui.ui_interface import select_file_from_list, get_input, show_confirmation, text_field_unicode, get_valid_url
from ui.ui_app import *



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
    stations_file = 'data/radio_stations.csv'
    stations = load_stations(stations_file)
    current_row = 0
    offset = 0
    vlc_process = None
    playing_index = -1  # Индекс проигрываемой станции (-1 - ничего не играет)
    move_mode = False  # Флаг режима перемещения
    moving_index = -1  # Индекс перемещаемой станции
    original_stations = []
    move_mode_playing = False # перемещение станции по спику которая проигрывается
    current_volume = 100  #   громкость воспроизведения

    vlc_prg = ""
    os_name = platform.system()
    vlc_prg = "C:\\Program Files (x86)\\VideoLAN\\VLC\\vlc.exe" if os_name == "Windows" else "vlc"
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

    # Флаг, указывающий на необходимость полной перерисовки
    need_redraw = True
    
    while True:
        try:
            if need_redraw:
                if not full_redraw(stdscr, stations, current_row, offset, playing_index, move_mode, move_mode_playing, current_volume, moving_index):
                    continue
                need_redraw = False
            
            key = stdscr.getch()
            need_redraw = True  # По умолчанию считаем, что перерисовка нужна
            
            # В режиме перемещения обрабатываем клавиши вверх/вниз
            if move_mode:
                if key == curses.KEY_UP and moving_index > 0:
                    stations[moving_index], stations[moving_index-1] = stations[moving_index-1], stations[moving_index]
                    moving_index -= 1
                    current_row = moving_index
                    if playing_index == moving_index:
                        playing_index += 1
                    # Прокрутка вверх, если текущая строка выше видимой области
                    if current_row < offset:
                        offset = current_row
                        need_redraw = True
                elif key == curses.KEY_DOWN and moving_index < len(stations)-1:
                    stations[moving_index], stations[moving_index+1] = stations[moving_index+1], stations[moving_index]
                    moving_index += 1
                    current_row = moving_index
                    if playing_index == moving_index:
                        playing_index -= 1
                    # Прокрутка вниз, если текущая строка ниже видимой области
                    h, w = stdscr.getmaxyx()
                    max_display = h - 6
                    if current_row >= offset + max_display:
                        offset = current_row - max_display + 1
                        need_redraw = True
                elif key in [curses.KEY_ENTER, 10, 13]:
                    save_stations(stations_file, stations)
                    if move_mode_playing:
                        playing_index = moving_index
                    move_mode = False
                    moving_index = -1
                    move_mode_playing = False                    
                elif key == 27:
                    stations = original_stations.copy()
                    current_row = moving_index
                    move_mode = False
                    moving_index = -1
                    move_mode_playing = False
                else:
                    need_redraw = False  # Неизвестная клавиша в режиме перемещения
            else:
                if key == curses.KEY_UP and current_row > 0:
                    current_row -= 1
                    # Прокрутка вверх, если текущая строка выше видимой области
                    if current_row < offset:
                        offset = current_row
                        need_redraw = True
                        continue
                    # Частичная перерисовка только списка станций и строк состояния
                    h, w = stdscr.getmaxyx()
                    draw_stations_list(stdscr, stations, current_row, offset, playing_index, move_mode, h-6)
                    draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index)
                    need_redraw = False
                elif key == curses.KEY_DOWN and current_row < len(stations)-1:
                    current_row += 1
                    # Прокрутка вниз, если текущая строка ниже видимой области
                    h, w = stdscr.getmaxyx()
                    max_display = h - 6
                    if current_row >= offset + max_display:
                        offset = current_row - max_display + 1
                        need_redraw = True
                        continue
                    h, w = stdscr.getmaxyx()
                    draw_stations_list(stdscr, stations, current_row, offset, playing_index, move_mode, h-6)
                    draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index)
                    need_redraw = False
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
                    name = text_field_unicode(stdscr, name_y, name_x+len(name_prompt), 50, "", russian=True)
                    
                    if name and name.strip():
                        # Получаем URL станции
                        url_prompt = "URL станции: "
                        url_y = h//2 + 1
                        url_x = w//2 - len(url_prompt)//2
                        stdscr.addstr(url_y, url_x, url_prompt)
                        url = get_valid_url(stdscr, url_y, url_x + len(url_prompt), 50)
                        
                        if url and url.strip():
                            # Добавляем новую станцию
                            stations.append((name.strip(), url.strip()))
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
                elif key == 267: 
                    # Вход в режим перемещения станции F3
                    move_mode = True                    
                    moving_index = current_row
                    original_stations = stations.copy()  # Сохраняем исходный порядок
                    if playing_index == current_row:
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
                        new_name =text_field_unicode(stdscr, h//2, w//2 - len(new_name)//2, width, new_name, russian=True)

                        # Шаг 2: Редактирование URL
                        stdscr.clear()
                        prompt = "Редактирование URL (Enter - подтвердить, Esc - отмена):"
                        stdscr.addstr(h//2 - 2, w//2 - len(prompt)//2, prompt)
                        width= len(new_url) if len(new_url)>50 else 50
                        new_url = get_valid_url(stdscr, h//2, w//2 - len(new_url)//2, width, new_url)

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
                    new_filename = text_field_unicode(stdscr, h//2, w//2 - len(filename)//2, width, filename)
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
                        # Обновляем только строку состояния
                        h, w = stdscr.getmaxyx()
                        draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index)
                        need_redraw = False
                elif key == ord("-"):
                    if playing_index >= 0:
                        current_volume = max(current_volume - 10, 0)  # -10%
                        set_vlc_volume(current_volume)
                        # Обновляем только строку состояния
                        h, w = stdscr.getmaxyx()
                        draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index)
                        need_redraw = False
                else:
                    need_redraw = False  # Неизвестная клавиша - не перерисовываем

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