import curses

# функции перерисовки частей интерфейса UI

def draw_header(stdscr, title, sub_title):
    h, w = stdscr.getmaxyx()
    title_x = max(0, w//2 - len(title)//2)
    stdscr.addstr(0, title_x, title, curses.A_BOLD)
    sub_title_x = max(0, w//2 - len(sub_title)//2)
    stdscr.addstr(1, sub_title_x, sub_title, curses.A_DIM)

def draw_stations_list(stdscr, stations, current_row, offset, playing_index, move_mode, max_display):
    h, w = stdscr.getmaxyx()
    for idx in range(offset, min(offset + max_display, len(stations))):
        name, url = stations[idx]
        x = max(0, w//2 - len(name)//2)
        y = idx - offset + 3
        
        try:
            if idx == current_row:
                if move_mode:
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
                try:
                    stdscr.addstr(y, x, name, curses.color_pair(2) | curses.A_BOLD)
                except:
                    stdscr.addstr(y, x, name, curses.A_BOLD)
            else:
                stdscr.addstr(y, x, name)

            if idx == playing_index:
                try:
                    stdscr.addstr(y, x-2, "▶ ")
                except:
                    pass
        except curses.error:
            pass

def draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index):
    h, w = stdscr.getmaxyx()
    
    # Инициализируем status_text значением по умолчанию
    status_text = "Готов к проигрыванию"
    
    # Строка состояния проигрывания
    status_line = h-3
    if playing_index >= 0:
        if move_mode_playing:
            status_text = f"Сейчас играет: {stations[moving_index][0]} -> громкость {current_volume} из 512"
        else:
            if not move_mode:
                status_text = f"Сейчас играет: {stations[playing_index][0]} -> громкость {current_volume} из 512"

    try:
        stdscr.addstr(status_line, 0, status_text, curses.color_pair(2) | curses.A_BOLD)
    except:
        try:
            stdscr.addstr(status_line, 0, status_text, curses.A_BOLD)
        except:
            pass

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
def draw_help_line(stdscr, move_mode):
    h, w = stdscr.getmaxyx()
    help_line = " Ins: добавить | Del: удалить | F2: сохранить |F3: переместить | F4: изменить | F5: загрузить |F10: выход "
    help_line_f3 = " ↑: переместить вверх | ↓: переместить вниз | Enter: закрепить перемешение | Esc: отмена перемещения"
    title_x = max(0, w//2 - len(help_line)//2)
    try:
        if move_mode:
            stdscr.addstr(h-1, title_x, help_line_f3)                
        else:
            stdscr.addstr(h-1, title_x, help_line)                
    except curses.error:
        pass

def full_redraw(stdscr, stations, current_row, offset, playing_index, move_mode, move_mode_playing, current_volume, moving_index):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    
    # Проверяем минимальный размер терминала
    if h < 5 or w < 40:
        stdscr.addstr(0, 0, "Terminal too small! Please resize.", curses.A_BOLD)
        stdscr.refresh()
        return False
    
    max_display = h - 6
    
    draw_header(stdscr, "Список радиостанций", "(Enter - играть, ESC - остановить, q - выход)")
    draw_stations_list(stdscr, stations, current_row, offset, playing_index, move_mode, max_display)
    draw_status_lines(stdscr, stations, current_row, playing_index, current_volume, move_mode, move_mode_playing, moving_index)
    draw_help_line(stdscr, move_mode)
    
    stdscr.refresh()
    return True

# END функции перерисовки частей интерфейса UI