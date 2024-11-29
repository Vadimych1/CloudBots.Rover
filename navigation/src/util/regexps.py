# import regex
import re

_raw_MAP_TILE_REGEX = r"https:\/\/pano.maps.yandex.net\/[a-z0-9A-Z]+\/[0-9][0-9]?.[0-9][0-9]?.[0-9][0-9]?+"
MAP_TILE_REGEX = re.compile(_raw_MAP_TILE_REGEX)

_raw_ADDRESS = r"([A-Za-zа-яА-Я]{3,}(, |,)[A-Za-zа-яА-Я ]{3,}(, |,)[0-9\-]{2,}( |\.|,|)+)"
_raw_ADDRESS_WITHOUT_TOWN = r"((улиц.?|проспект.?|площад.?|пл(\.?)|пр(\.?)|ул(\.?)) [a-zA-Zа-яА-Я ]{2,}.(дом|здание|)( [0-9\-абвгдabcdef ]{0,})( ?(корпус|к|к\.)?[0-9абвгдеabcdef]+)?)"
ADDRESS = re.compile(_raw_ADDRESS)
ADDRESS_WITHOUT_TOWN = re.compile(_raw_ADDRESS_WITHOUT_TOWN)

def get_addresses_from_text(text: str):
    text = text.lower()

    a = ["".join(x) for x in ADDRESS.findall(text)]
    b = ["".join(x) for x in ADDRESS_WITHOUT_TOWN.findall(text)]
    return [*a, *b]

# text = """
# Москва - мой любимый город. Вчера я побывал на улице игоря думенко, 12к1.
# Сейчас я нахожусь на площади ленина. Это моя любимая площадь, ведь на площади ленина убили сталина.
# """
# addrs = get_addresses_from_text(text)
# print(addrs)