"""Лабораторная работа №11 – сжатие/распаковка данных арифметическим методом.

Сообщение отображается на отрезок [0; 1): каждый символ сужает рабочий отрезок
пропорционально своей частоте. Кодом служит любое число из итогового отрезка,
для его записи нужно ceil(-log2(w)) бит, где w – ширина отрезка.

Вычисления выполняются точной рациональной арифметикой (fractions.Fraction),
поэтому результат не зависит от разрядности машины.

Запуск:
    python3 lab11/app/main.py moloko    # пример «молоко» из методички
    python3 lab11/app/main.py variant   # задания варианта 1 (две части)
    python3 lab11/app/main.py overflow  # оценка переполнения при длинных текстах
    python3 lab11/app/main.py compare   # сравнение с Хаффманом
"""
import math
import sys
from collections import Counter
from fractions import Fraction

WORD = "летоисчисление"                       # вариант 1, часть 1
SECOND = "времяпрепровождение"                # вариант 1, часть 2 (строка 2)
CONCAT = WORD + SECOND                        # конкатенация 1–2


def model(text):
    """Таблица частот и кумулятивные границы символов на [0; 1)."""
    counts = Counter(text)
    total = sum(counts.values())
    bounds, low = {}, Fraction(0)
    for sym in sorted(counts):
        width = Fraction(counts[sym], total)
        bounds[sym] = (low, low + width, counts[sym])
        low += width
    return bounds


def bits_needed(width):
    """Минимальное число бит для записи числа из отрезка шириной width."""
    inv = 1 / width
    k = inv.numerator.bit_length() - inv.denominator.bit_length()
    while Fraction(2) ** k < inv:
        k += 1
    while k > 0 and Fraction(2) ** (k - 1) >= inv:
        k -= 1
    return k


def encode(text, bounds):
    """Прямое преобразование: итоговый отрезок и требуемое число бит."""
    low, width = Fraction(0), Fraction(1)
    for sym in text:
        s_low, s_high, _ = bounds[sym]
        low += width * s_low
        width *= s_high - s_low
    return low, low + width, bits_needed(width)


def decode(low, high, bounds, length):
    """Обратное преобразование по числу из итогового отрезка."""
    by_low = sorted(bounds.items(), key=lambda kv: kv[1][0])
    value = (low + high) / 2
    cur_low, cur_width = Fraction(0), Fraction(1)
    out = []
    for _ in range(length):
        r = (value - cur_low) / cur_width
        for sym, (s_low, s_high, _) in by_low:
            if s_low <= r < s_high:
                out.append(sym)
                cur_low += cur_width * s_low
                cur_width *= s_high - s_low
                break
        else:
            out.append("?")
    return "".join(out)


def huffman_bits(text):
    """Длина сообщения кодом Хаффмана – для сравнения."""
    counts = Counter(text)
    weights = sorted(counts.values())
    total = 0
    while len(weights) > 1:
        a, b = weights.pop(0), weights.pop(0)
        total += a + b
        weights.append(a + b)
        weights.sort()
    return total if total else 0


def show_moloko():
    text = "молоко"
    bounds = model(text)
    print("Пример методички: сообщение «{}»".format(text))
    print()
    print("  символ | частота | p        | отрезок")
    for sym, (lo, hi, cnt) in sorted(bounds.items(), key=lambda kv: kv[1][0]):
        print("    {!r:4} | {:7d} | {:.4f}   | [{:.4f}; {:.4f})".format(
            sym, cnt, float(hi - lo), float(lo), float(hi)))
    low, high, bits = encode(text, bounds)
    print()
    print("  итоговый отрезок : [{:.15f}; {:.15f})".format(float(low), float(high)))
    print("  ширина отрезка   : {:.3e}".format(float(high - low)))
    print("  нужно бит        : {}".format(bits))
    print("  декодировано     : «{}»".format(decode(low, high, bounds, len(text))))
    print("  совпадает        : {}".format(decode(low, high, bounds, len(text)) == text))


def show_variant():
    print("Задание варианта 1")
    for title, text in (("часть 1", WORD), ("часть 2 (конкатенация 1–2)", CONCAT)):
        bounds = model(text)
        low, high, bits = encode(text, bounds)
        back = decode(low, high, bounds, len(text))
        ascii_bits = 8 * len(text)
        print()
        print("  {}: «{}»".format(title, text))
        print("    символов            : {}".format(len(text)))
        print("    отрезок             : [{:.15f}; {:.15f})".format(float(low), float(high)))
        print("    ширина              : {:.3e}".format(float(high - low)))
        print("    арифметический код  : {} бит ({:.2f} бит/символ)".format(
            bits, bits / len(text)))
        print("    ASCII               : {} бит ({:.2f} бит/символ)".format(
            ascii_bits, 8.0))
        print("    выигрыш к ASCII     : {:.1f} %".format(100.0 * bits / ascii_bits))
        print("    декодировано        : совпадает = {}".format(back == text))


def show_overflow():
    print("Оценка переполнения при увеличении длины сообщения")
    print("(сообщение – повтор слова «{}»)".format(WORD))
    bounds = model(WORD)
    widths = sorted(float(b - a) for a, b, _ in bounds.values())
    p_min = widths[0]
    print()
    print("  повтор | символов | ширина отрезка | нужно бит | бит/символ")
    print("  -------+----------+----------------+-----------+-----------")
    for k in (1, 2, 4, 8, 16, 32, 64, 128):
        text = WORD * k
        low, high, bits = encode(text, bounds)
        w = float(high - low) if float(high - low) > 0 else None
        print("  {:6d} | {:8d} | {:14} | {:9d} | {:9.3f}".format(
            k, len(text), "{:.3e}".format(w) if w else "< 1e-308", bits,
            bits / len(text)))
    print()
    print("  минимальная вероятность символа p_min = {:.4f}".format(p_min))
    n64 = math.ceil(64 / -math.log2(p_min))
    print("  64-битная арифметика теряет точность примерно после {} символов".format(n64))
    print("  -> нужна реорганизация (перенормировка) или длинная арифметика")


def show_compare():
    print("Сравнение арифметического метода с вероятностными")
    print()
    print("  сообщение                 | арифм., бит | Хаффман, бит | ASCII, бит")
    print("  --------------------------+-------------+--------------+-----------")
    for text in (WORD, CONCAT):
        bounds = model(text)
        _, _, bits = encode(text, bounds)
        print("  {:<25} | {:11d} | {:12d} | {:9d}".format(
            text[:25], bits, huffman_bits(text), 8 * len(text)))
    print()
    print("  арифметический код не требует кратности вероятностей степеням 1/2,")
    print("  поэтому он ближе к энтропии, чем префиксные коды")


MODES = ("moloko", "variant", "overflow", "compare", "all")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in MODES:
        raise SystemExit(__doc__)
    if mode in ("all", "moloko"):
        show_moloko()
        print()
    if mode in ("all", "variant"):
        show_variant()
        print()
    if mode in ("all", "overflow"):
        show_overflow()
        print()
    if mode in ("all", "compare"):
        show_compare()


if __name__ == "__main__":
    main()
