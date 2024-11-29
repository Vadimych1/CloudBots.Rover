def _sorted_binary_search(arr: list, value: int):
    a = arr.copy()
    index = 0

    while len(a) > 1:
        mid = len(a) // 2
        if a[mid] < value:
            a = a[mid:]
            index += mid
        else:
            a = a[:mid]
            index -= mid
    
    return index

def binary_search(arr: list, value: int):
    a = arr.copy()
    a.sort()
    return _sorted_binary_search(a, value)