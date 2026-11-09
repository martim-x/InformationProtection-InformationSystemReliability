"""Лабораторная работа №10 – сжатие/распаковка данных методом Лемпеля – Зива.

Реализован LZ77 со скользящим окном: словарь длиной n1 и буфер просмотра
длиной n2. Выход – последовательность троек (p, q, c): смещение p от текущей
позиции назад, длина совпадения q и следующий символ c.

Запуск:
    python3 lab10/app/main.py demo      # пошаговое сжатие короткой строки
    python3 lab10/app/main.py text      # сжатие/распаковка текста в несколько КБ
    python3 lab10/app/main.py windows   # зависимость от размеров окон n1, n2
"""
import math
import sys
import time

SAMPLE = ("Метод Лемпеля – Зива заменяет повторяющиеся последовательности "
          "ссылками на словарь. Словарь хранит уже обработанные символы, "
          "буфер просмотра – ещё не обработанные. ")


def lz77_encode(text, n1, n2):
    """Прямое преобразование: список троек (смещение, длина, следующий символ)."""
    tokens = []
    i = 0
    n = len(text)
    while i < n:
        start = max(0, i - n1)
        best_len, best_off = 0, 0
        for j in range(start, i):
            length = 0
            while (length < n2 and i + length < n and text[j + length] == text[i + length]):
                length += 1
            if length > best_len:
                best_len, best_off = length, i - j
        if best_len > 0:
            nxt = text[i + best_len] if i + best_len < n else ""
            tokens.append((best_off, best_len, nxt))
            i += best_len + (1 if nxt else 0)
        else:
            tokens.append((0, 0, text[i]))
            i += 1
    return tokens


def lz77_decode(tokens):
    """Обратное преобразование по списку троек."""
    out = []
    for off, length, nxt in tokens:
        if length:
            start = len(out) - off
            for k in range(length):
                out.append(out[start + k])
        if nxt:
            out.append(nxt)
    return "".join(out)


def token_bits(n1, n2):
    """Бит на тройку: смещение + длина + символ."""
    return math.ceil(math.log2(n1)) + math.ceil(math.log2(n2)) + 8


def show_demo():
    text = "молоко молоко"
    n1, n2 = 32, 16
    tokens = lz77_encode(text, n1, n2)
    print("Пошаговое сжатие строки «{}» (n1 = {}, n2 = {})".format(text, n1, n2))
    print()
    print("   № | p | q | c | что закодировано")
    pos = 0
    for i, (off, length, nxt) in enumerate(tokens, 1):
        got = text[pos:pos + length] + (nxt or "")
        print("  {:2d} | {} | {} | {!r:4} | {!r}".format(i, off, length, nxt, got))
        pos += length + (1 if nxt else 0)
    print()
    print("Троек: {} | исходно {} символов | восстановлено: {!r}".format(
        len(tokens), len(text), lz77_decode(tokens)))
    print("Совпадает с исходной строкой: {}".format(lz77_decode(tokens) == text))


def show_text():
    text = SAMPLE * 20
    n1, n2 = 64, 32
    t0 = time.perf_counter()
    tokens = lz77_encode(text, n1, n2)
    t1 = time.perf_counter()
    back = lz77_decode(tokens)
    t2 = time.perf_counter()
    bits = token_bits(n1, n2)
    packed = len(tokens) * bits
    print("Сжатие текста объёмом несколько килобайт")
    print("  размер исходного текста : {} символов ({} байт)".format(
        len(text), len(text.encode("utf-8"))))
    print("  окон: словарь n1 = {}, буфер n2 = {}".format(n1, n2))
    print("  получено троек         : {}".format(len(tokens)))
    print("  бит на тройку          : {}".format(bits))
    print("  объём сжатых данных    : {} бит = {} байт".format(packed, packed // 8))
    print("  коэффициент сжатия     : {:.2f}".format(len(text.encode("utf-8")) / (packed / 8)))
    print("  время сжатия           : {:.1f} мс".format(1000 * (t1 - t0)))
    print("  время распаковки       : {:.1f} мс".format(1000 * (t2 - t1)))
    print("  распаковка совпала     : {}".format(back == text))


def show_windows():
    text = SAMPLE * 20
    print("Зависимость сжатия от размеров окон (текст {} символов)".format(len(text)))
    print()
    print("   n1   |  n2  | троек | бит/тройку | сжатие | время, мс")
    print("  ------+------+-------+------------+--------+----------")
    for n1 in (16, 32, 64, 128, 256):
        for n2 in (8, 16, 32):
            t0 = time.perf_counter()
            tokens = lz77_encode(text, n1, n2)
            t1 = time.perf_counter()
            bits = token_bits(n1, n2)
            packed = len(tokens) * bits / 8
            print("  {:5d} | {:4d} | {:5d} | {:10d} | {:6.2f} | {:9.1f}".format(
                n1, n2, len(tokens), bits, len(text.encode("utf-8")) / packed,
                1000 * (t1 - t0)))


MODES = ("demo", "text", "windows", "all")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in MODES:
        raise SystemExit(__doc__)
    if mode in ("all", "demo"):
        show_demo()
        print()
    if mode in ("all", "text"):
        show_text()
        print()
    if mode in ("all", "windows"):
        show_windows()


if __name__ == "__main__":
    main()
