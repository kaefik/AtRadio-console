# TODO AtRadio console

##  PLAN

- работа с избранными станциями, запуск по горячим клавишам (определить механику)
- F1 - помощь (нужно ли?)
- add при закрытии терминала в windows-linux завершался запущенное проигрывание станции
- корретно не работает управление громкостью воспроизведения в windows
- по клавишам влево вправо перемещаться по вкладкам (категориям станций), первая вкладка All 
- перевести изменение громкости на asincio

## DONE

- добавление, редактирование и удаление радиостанций (done)
- сохранение  и загрузка радиостанций ( done  сохранение)
- автозапуск воспроизведения станций (нужно ли?) - возможно стоит реализовать в виде возможности через командную строку (done)
- add управление функциями программы с помощью функциональных клавиш:  
    - '+' - добавить станцию в список (done)
    - '-' - удалить станцию из списка (done)
    - F4 - редактирование текущей станции (done)
    - F10 - выход (done)
    - F5 - загрузка станций из файла (done)
    - F2 - сохранение станций в файл (done)
    - F3 - режим перемещения станций по списку: (done)
         при нажатии на F3  текущую станцию можно переместить клавишами вверх и вниз по списку, если нажать на Esc выходим из этого режима (done)
- в режиме проигрывания и потом перемещаешь текущую станцию некорректно отображается после перемещения какая станция проигрывается (done)
- в режиме проигрывания и потом перемещаешь станцию которая НЕ играет и путь проходит через играющую станцию, то резко на списке станций меняется то что проигрывается (done)
- регулирование громкости воспроизведения (done)
- когда вводим по русски не вводится в элемент text_field
- не прокручивается список станций когда выходит за переделы страницы после оптимизации перерисовки экрана
- проверка url  на корректность при добавлении и редактировании  url  станции
- вывести функции частичной перерисовки в отдельный модуль




