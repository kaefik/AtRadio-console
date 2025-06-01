import curses


def get_input(stdscr, prompt, y, x):
    curses.echo()
    stdscr.addstr(y, x, prompt)
    stdscr.refresh()
    input_str = stdscr.getstr(y, x + len(prompt)).decode('utf-8')
    curses.noecho()
    return input_str


def text_field(stdscr, y, x, width, initial_text="", russian=False):
    """
    если нажали Esc, то возвращается None, иначе возвращается строка
    russian: если True, разрешает ввод русских букв
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
        elif 32 <= key <= 126:  # Стандартные печатные символы ASCII
            text.insert(cursor_pos, chr(key))
            cursor_pos += 1
        elif russian and key >= 1024:  # Русские символы в curses (обычно >= 1024)
            print(f"{key=}")
            try:
                char = chr(key)
                # Проверяем, что это действительно русская буква (может потребоваться уточнение)
                if char.isalpha():
                    text.insert(cursor_pos, char)
                    cursor_pos += 1
            except ValueError:
                pass
    
    curses.curs_set(0)  # Скрываем курсор
    return "".join(text)


def text_field_unicode(stdscr, y, x, width, initial_text="", russian=False):
    """
    Версия с использованием get_wch() для лучшей поддержки Unicode
    """
    text = list(initial_text)
    cursor_pos = len(text)
    curses.curs_set(1)
    
    while True:
        # Отрисовываем текущий текст
        stdscr.addstr(y, x, " " * width)
        display_text = "".join(text)[:width]
        try:
            stdscr.addstr(y, x, display_text)
        except curses.error:
            pass
        
        stdscr.move(y, x + min(cursor_pos, width-1))
        
        try:
            # Используем get_wch() для Unicode символов
            if hasattr(stdscr, 'get_wch'):
                key = stdscr.get_wch()
            else:
                key = stdscr.getch()
        except curses.error:
            continue
        
        # Обработка специальных клавиш (числовые коды)
        if isinstance(key, int):
            if key in (curses.KEY_ENTER, 10, 13):
                break
            elif key == 27:  # ESC
                return None
            elif key in [curses.KEY_BACKSPACE, 127, 8]:
                if cursor_pos > 0:
                    text.pop(cursor_pos-1)
                    cursor_pos -= 1
            elif key == curses.KEY_DC:
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
            elif 32 <= key <= 126:
                text.insert(cursor_pos, chr(key))
                cursor_pos += 1
        else:
            # Обработка Unicode символов и специальных клавиш как строк
            if isinstance(key, str):
                # Проверяем специальные клавиши, которые могут прийти как строки
                if key == '\n' or key == '\r':  # Enter как строка
                    break
                elif key == '\x1b':  # ESC как строка
                    return None
                elif key == '\x7f' or key == '\b':  # Backspace как строка
                    if cursor_pos > 0:
                        text.pop(cursor_pos-1)
                        cursor_pos -= 1
                elif len(key) == 1:
                    # Обычные символы
                    if not russian:
                        # Только ASCII символы
                        if 32 <= ord(key) <= 126:
                            text.insert(cursor_pos, key)
                            cursor_pos += 1
                    else:
                        # Разрешаем кириллицу и другие символы
                        if (32 <= ord(key) <= 126 or  # ASCII печатные
                            'а' <= key <= 'я' or 'А' <= key <= 'Я' or 
                            key in 'ёЁ' or 
                            (key.isalnum() and ord(key) > 127)):  # Другие Unicode буквы
                            text.insert(cursor_pos, key)
                            cursor_pos += 1
    
    curses.curs_set(0)
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


def show_confirmation(stdscr, message, options=["Да", "Нет"], default=0):
    """
    Универсальная функция подтверждения с выбором вариантов.
    
    Параметры:
    - stdscr: главное окно curses
    - message: сообщение для подтверждения
    - options: список вариантов ответа (по умолчанию ["Да", "Нет"])
    - default: индекс выбранного по умолчанию варианта
    
    Возвращает:
    - Индекс выбранного варианта или None, если отмена (ESC)
    """
    h, w = stdscr.getmaxyx()
    win_width = 50
    win_height = 5
    confirm_win = curses.newwin(win_height, win_width, h//2-2, w//2-25)
    confirm_win.keypad(True)
    
    current_choice = default
    result = None
    
    while True:
        confirm_win.border()
        # Центрируем сообщение
        msg_x = max(2, (win_width - len(message)) // 2)
        confirm_win.addstr(1, msg_x, message[:win_width-4])  # Обрезаем слишком длинные сообщения
        
        # Собираем варианты с подсветкой текущего выбора
        options_text = []
        for i, option in enumerate(options):
            if i == current_choice:
                options_text.append(f"[{option}]")
            else:
                options_text.append(f" {option} ")
        
        # Собираем все варианты в одну строку с пробелами между ними
        options_line = "   ".join(options_text)
        # Вычисляем позицию для центрирования
        options_x = max(0, (win_width - len(options_line)) // 2)
        
        confirm_win.addstr(3, options_x, options_line, curses.A_BOLD)
        confirm_win.refresh()
        
        key = confirm_win.getch()
        
        if key in [ord('\t')]:
            current_choice = (current_choice + 1) % len(options)
        elif key in [curses.KEY_LEFT, curses.KEY_RIGHT]:
            if key == curses.KEY_LEFT:
                current_choice = max(0, current_choice - 1)
            else:
                current_choice = min(len(options)-1, current_choice + 1)
        elif key in [ord('\n'), ord('\r')]:
            result = current_choice
            break
        elif key == 27:  # ESC - отмена
            result = None
            break
        elif len(options) == 2 and key in [ord('y'), ord('Y'), ord('д'), ord('Д')]:
            result = 0
            break
        elif len(options) == 2 and key in [ord('n'), ord('N'), ord('т'), ord('Т')]:
            result = 1
            break
        elif key >= ord('1') and key <= ord(str(len(options))):
            choice = key - ord('1')
            if choice < len(options):
                result = choice
                break
    
    confirm_win.clear()
    confirm_win.refresh()
    del confirm_win
    return result