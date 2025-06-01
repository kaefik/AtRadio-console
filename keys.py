import curses

def show_key(stdscr):
    stdscr.keypad(True)
    while True:
        key = stdscr.getch()
        stdscr.addstr(f"Код: {key}\n")
        stdscr.refresh()

curses.wrapper(show_key)