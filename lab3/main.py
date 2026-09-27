#!/usr/bin/env python3
"""
Лабораторная работа №3: Элементы теории информации.
Информативность данных в различных кодировках.

Задачи:
1. Конвертация произвольного документа в base64 и обратно (своя реализация).
2. Частотный анализ, энтропия Хартли и Шеннона, избыточность алфавитов.
3. XOR двух буферов (фамилия и имя) в ASCII и base64. Проверка a XOR b XOR b.
4. Сравнение со стандартными функциями Python.
"""

# Таблица символов base64 (стандартный алфавит)
BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def base64_encode(data: bytes) -> str:
    """
    Кодирует байты в base64 (своя реализация без стандартной библиотеки).
    
    Args:
        data: Входные байты для кодирования.
        
    Returns:
        Строка в формате base64.
    """
    if not data:
        return ""
    
    result = []
    # Обрабатываем по 3 байта (24 бита) за раз
    for i in range(0, len(data), 3):
        chunk = data[i:i+3]
        # Дополняем нулями до 3 байт если нужно
        pad_len = 3 - len(chunk)
        if pad_len:
            chunk += b'\x00' * pad_len
        
        # 24 бита -> 4 группы по 6 бит
        b24 = (chunk[0] << 16) | (chunk[1] << 8) | chunk[2]
        
        indices = [
            (b24 >> 18) & 0x3F,
            (b24 >> 12) & 0x3F,
            (b24 >> 6) & 0x3F,
            b24 & 0x3F,
        ]
        
        for idx in indices:
            result.append(BASE64_ALPHABET[idx])
        
        # Заменяем последние символы на '=' для padding
        if pad_len == 1:
            result[-1] = '='
        elif pad_len == 2:
            result[-1] = '='
            result[-2] = '='
    
    return ''.join(result)


def base64_decode(encoded: str) -> bytes:
    """
    Декодирует base64 строку в байты (своя реализация).
    
    Args:
        encoded: Строка в формате base64.
        
    Returns:
        Декодированные байты.
    """
    if not encoded:
        return b""
    
    # Убираем padding и считаем его
    pad_count = encoded.count('=')
    encoded = encoded.rstrip('=')
    
    # Создаем обратный словарь индексов
    rev_alphabet = {ch: i for i, ch in enumerate(BASE64_ALPHABET)}
    
    result = bytearray()
    # Обрабатываем по 4 символа (24 бита)
    for i in range(0, len(encoded), 4):
        chunk = encoded[i:i+4]
        # Дополняем нулями если нужно
        if len(chunk) < 4:
            chunk += 'A' * (4 - len(chunk))
        
        indices = [rev_alphabet.get(ch, 0) for ch in chunk]
        
        b24 = (indices[0] << 18) | (indices[1] << 12) | (indices[2] << 6) | indices[3]
        
        result.append((b24 >> 16) & 0xFF)
        if len(chunk) > 2 or pad_count < 2:
            result.append((b24 >> 8) & 0xFF)
        if len(chunk) > 3 or pad_count < 1:
            result.append(b24 & 0xFF)
    
    # Убираем padding байты
    if pad_count:
        result = result[:-pad_count]
    
    return bytes(result)


def frequency_analysis(data: bytes) -> dict[int, int]:
    """
    Строит частотное распределение байтов в данных.
    
    Args:
        data: Входные байты.
        
    Returns:
        Словарь {байт: частота}.
    """
    freq = {}
    for b in data:
        freq[b] = freq.get(b, 0) + 1
    return freq


def hartley_entropy(alphabet_size: int) -> float:
    """
    Энтропия Хартли: H = log2(N), где N - мощность алфавита.
    
    Args:
        alphabet_size: Количество уникальных символов в алфавите.
        
    Returns:
        Энтропия Хартли в битах.
    """
    import math
    if alphabet_size <= 1:
        return 0.0
    return math.log2(alphabet_size)


def shannon_entropy(freq: dict[int, int], total: int) -> float:
    """
    Энтропия Шеннона: H = -Σ p(x) * log2(p(x)).
    
    Args:
        freq: Частотное распределение.
        total: Общее количество символов.
        
    Returns:
        Энтропия Шеннона в битах на символ.
    """
    import math
    if total == 0:
        return 0.0
    
    entropy = 0.0
    for count in freq.values():
        if count > 0:
            p = count / total
            entropy -= p * math.log2(p)
    return entropy


def redundancy(hartley: float, shannon: float) -> float:
    """
    Избыточность алфавита: R = (H_hartley - H_shannon) / H_hartley * 100%.
    
    Args:
        hartley: Энтропия Хартли.
        shannon: Энтропия Шеннона.
        
    Returns:
        Избыточность в процентах.
    """
    if hartley == 0:
        return 0.0
    return (hartley - shannon) / hartley * 100.0


def xor_buffers(a: bytes, b: bytes) -> bytes:
    """
    XOR двух буферов одинаковой длины (меньший дополняется нулями).
    
    Args:
        a: Первый буфер.
        b: Второй буфер.
        
    Returns:
        Результат побтового XOR.
    """
    max_len = max(len(a), len(b))
    a_padded = a.ljust(max_len, b'\x00')
    b_padded = b.ljust(max_len, b'\x00')
    
    return bytes(x ^ y for x, y in zip(a_padded, b_padded))


def analyze_data(name: str, data: bytes) -> dict:
    """
    Полный анализ данных: частота, энтропии, избыточность.
    
    Args:
        name: Имя набора данных для вывода.
        data: Байты для анализа.
        
    Returns:
        Словарь с результатами анализа.
    """
    freq = frequency_analysis(data)
    alphabet_size = len(freq)
    total = len(data)
    
    h_hartley = hartley_entropy(alphabet_size)
    h_shannon = shannon_entropy(freq, total)
    red = redundancy(h_hartley, h_shannon)
    
    return {
        'name': name,
        'size': total,
        'alphabet_size': alphabet_size,
        'hartley': h_hartley,
        'shannon': h_shannon,
        'redundancy': red,
        'frequency': freq,
    }


def print_analysis(analysis: dict) -> None:
    """Выводит результаты анализа в читаемом виде."""
    print(f"\n=== {analysis['name']} ===")
    print(f"Размер: {analysis['size']} байт")
    print(f"Мощность алфавита: {analysis['alphabet_size']}")
    print(f"Энтропия Хартли: {analysis['hartley']:.4f} бит/символ")
    print(f"Энтропия Шеннона: {analysis['shannon']:.4f} бит/символ")
    print(f"Избыточность: {analysis['redundancy']:.2f}%")


def main():
    """Основная функция демонстрации лабораторной работы."""
    # Тестовые данные: фамилия и имя (как в задании 3)
    surname = "Иванов".encode('utf-8')
    name = "Петр".encode('utf-8')
    test_doc = "Это тестовый документ для лабораторной работы №3. Содержит кириллицу и цифры 123.".encode('utf-8')
    
    print("=" * 60)
    print("ЛАБОРАТОРНАЯ РАБОТА №3: ЭЛЕМЕНТЫ ТЕОРИИ ИНФОРМАЦИИ")
    print("=" * 60)
    
    # --- Задание 1: base64 кодирование/декодирование ---
    print("\n--- ЗАДАНИЕ 1: Base64 кодирование/декодирование ---")
    
    # Своя реализация
    encoded_custom = base64_encode(test_doc)
    decoded_custom = base64_decode(encoded_custom)
    
    # Стандартная библиотека для сравнения
    import base64
    encoded_std = base64.b64encode(test_doc).decode('ascii')
    decoded_std = base64.b64decode(encoded_std)
    
    print(f"Исходный документ ({len(test_doc)} байт): {test_doc[:50]}...")
    print(f"Своя реализация:  {encoded_custom}")
    print(f"Стандартная lib:  {encoded_std}")
    print(f"Кодирование совпадает: {encoded_custom == encoded_std}")
    print(f"Декодирование совпадает: {decoded_custom == test_doc and decoded_std == test_doc}")
    
    # --- Задание 2: Энтропийный анализ ---
    print("\n--- ЗАДАНИЕ 2: Энтропийный анализ алфавитов ---")
    
    # Анализ исходного документа
    orig_analysis = analyze_data("Исходный документ (UTF-8)", test_doc)
    print_analysis(orig_analysis)
    
    # Анализ base64 версии
    b64_bytes = encoded_custom.encode('ascii')
    b64_analysis = analyze_data("Base64 документ (ASCII)", b64_bytes)
    print_analysis(b64_analysis)
    
    # Анализ фамилии и имени
    surname_analysis = analyze_data("Фамилия (UTF-8)", surname)
    name_analysis = analyze_data("Имя (UTF-8)", name)
    print_analysis(surname_analysis)
    print_analysis(name_analysis)
    
    # --- Задание 3: XOR операций ---
    print("\n--- ЗАДАНИЕ 3: XOR операций ---")
    
    # XOR в ASCII (UTF-8 байты)
    xor_ascii = xor_buffers(surname, name)
    print(f"Фамилия (hex): {surname.hex()}")
    print(f"Имя (hex):     {name.hex()}")
    print(f"XOR (hex):     {xor_ascii.hex()}")
    
    # XOR в base64
    surname_b64 = base64_encode(surname).encode('ascii')
    name_b64 = base64_encode(name).encode('ascii')
    xor_b64 = xor_buffers(surname_b64, name_b64)
    print(f"Фамилия base64: {surname_b64.decode()}")
    print(f"Имя base64:     {name_b64.decode()}")
    print(f"XOR base64(hex): {xor_b64.hex()}")
    
    # Проверка a XOR b XOR b = a
    xor_check = xor_buffers(xor_ascii, name)
    print(f"\nПроверка a XOR b XOR b = a:")
    print(f"a XOR b XOR b (hex): {xor_check.hex()}")
    print(f"Исходная a (hex):    {surname.hex()}")
    print(f"Результат верный: {xor_check == surname}")
    
    # То же для base64
    xor_check_b64 = xor_buffers(xor_b64, name_b64)
    print(f"\nДля base64: a XOR b XOR b = a: {xor_check_b64 == surname_b64}")
    
    # --- Задание 4: Сравнение со стандартными функциями ---
    print("\n--- ЗАДАНИЕ 4: Сравнение со стандартными функциями ---")
    
    # Base64
    test_data = b"Test data for comparison"
    custom_enc = base64_encode(test_data)
    std_enc = base64.b64encode(test_data).decode('ascii')
    print(f"Base64 кодирование совпадает: {custom_enc == std_enc}")
    
    custom_dec = base64_decode(custom_enc)
    std_dec = base64.b64decode(std_enc)
    print(f"Base64 декодирование совпадает: {custom_dec == std_dec == test_data}")
    
    # XOR
    a = b"hello"
    b = b"world"
    custom_xor = xor_buffers(a, b)
    std_xor = bytes(x ^ y for x, y in zip(a.ljust(max(len(a), len(b)), b'\x00'), 
                                           b.ljust(max(len(a), len(b)), b'\x00')))
    print(f"XOR совпадает: {custom_xor == std_xor}")
    
    print("\n" + "=" * 60)
    print("РАБОТА ЗАВЕРШЕНА УСПЕШНО")
    print("=" * 60)


if __name__ == "__main__":
    main()