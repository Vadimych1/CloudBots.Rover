# Robot & miniros package
miniros - пакет, основанный на принципах ROS. Выполняет ту-же функцию, что и ROS - передача данных между нодами. Для использования пакета:
- в консоли Windows/PowerShell
```
./build @REM or ./build.bat
```
- на Linux
```
sh ./build.sh
```

# Использование
Для передачи данных в miniros существуют пакеты. Базовый класс для пакетов находится в `miniros.source.Packet`. Также, miniros предоставляет набор встроенных пакетов в `miniros.builtin_datatypes`.

Класс Node расположен в miniros.source, там же есть класс Server, но он вам не понадобится: для запуска главного сервера достаточно написать:
```
python -m miniros
```

Примеры написания нодов и их использования можно найти в папке examples репозитория.
Для теста пакета попробуйте запустить `example_node_publisher.py` и `example_node_listener.py` (последовательно).

# Система пакетов
Хотя код и можно писать в обычных python-файлах и запускать, лучше делать это с помощью системы пакетов.
Чтобы увидеть использование системы пакетов, введите в консоль:
```
python -m miniros --help
```

Выведутся все доступные команды.

# Tools
В папке Tools можно найти несколько полезных файлов:
1. miniros.bat - если добавить его в переменную PATH на Windows, можно запускать miniros без python -m:
```
miniros ...
```
2. miniros.sh - то же, что и miniros.bat, но для Linux-систем, и для использования нужно:
```bash
source miniros.sh
```
Для того, чтобы каждый раз не писать source miniros.sh:
```bash
echo "source path/to/miniros.sh" >> ~/.bashrc
```