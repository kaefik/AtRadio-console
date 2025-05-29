import curses


def get_input(stdscr, prompt, y, x):
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    input_str = stdscr.getstr(y, x + len(prompt)).decode('utf-8')
    curses.noecho()
    return input_str


def text_field(stdscr, y, x, width, initial_text=""):
    """
    если нажали  Esc, то возвращается None,  иначе возвращается строка
    """
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
            return None
            break
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
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


def select_file_from_list(stdscr, files):
    """Функция для выбора файла из списка"""
    current_row = 0
    offset = 0
    
    while True:
        stdscr.clear()
        h, w = stdscr.getmaxyx()
        max_display = h - 4
        
        # Корректируем смещение для прокрутки
        if current_row < offset:
            offset = current_row
        elif current_row >= offset + max_display:
            offset = current_row - max_display + 1

        # Отображаем заголовок
        title = "Выберите файл для загрузки (Enter - выбрать, ESC - отмена)"
        stdscr.addstr(0, w//2 - len(title)//2, title, curses.A_BOLD)
        
        # Отображаем список файлов
        for idx in range(offset, min(offset + max_display, len(files))):
            filename = files[idx]
            y = idx - offset + 2
            try:
                if idx == current_row:
                    stdscr.addstr(y, w//2 - len(filename)//2, filename, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, w//2 - len(filename)//2, filename)
            except curses.error:
                pass

        key = stdscr.getch()
        
        if key == curses.KEY_UP and current_row > 0:
            current_row -= 1
        elif key == curses.KEY_DOWN and current_row < len(files)-1:
            current_row += 1
        elif key in [curses.KEY_ENTER, 10, 13]:  # Enter - выбрать
            return files[current_row]
        elif key == 27:  # ESC - отмена
            return None
