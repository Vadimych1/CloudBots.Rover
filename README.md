# Robot & miniros package
miniros - пакет, основанный на принципах ROS. Выполняет ту-же функцию, что и ROS - передача данных между нодами. Для использования пакета:
- в консоли Windows/PowerShell
```
./build
```
- на Linux: для начала сделайте ./build на Windows-машине, перенесите файл miniros/dist/miniros-...-none-any.whl на Linux-машину и установите его с помощью:
```sh
pip3 install miniros-...-none-any.whl
```

# Использование
Для передачи данных в miniros существуют пакеты. Базовый класс для пакетов находится в `miniros.source.Packet`. Также, miniros предоставляет набор встроенных пакетов в `miniros.builtin_datatypes`.

Класс Node расположен в miniros.source, там же есть класс Server, но он вам не понадобится: для запуска главного сервера достаточно написать:
```
python -m miniros
```

Примеры написания нодов и их использования можно найти в папке examples репозитория.
Для теста пакета попробуйте запустить `example_node_publisher.py` и `example_node_listener.py` (последовательно).