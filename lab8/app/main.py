"""Лабораторная работа №8 – сжатие/распаковка данных методом Барроуза – Уилера.

Прямое преобразование: все циклические сдвиги блока сортируются, в выходной
поток записывается последний столбец матрицы сдвигов и номер строки, в которой
оказался исходный блок. Обратное преобразование восстанавливает блок по
последнему столбцу и номеру строки.

Запуск:
    python3 lab8/app/main.py blocks   # три блока: имя, фамилия, слово варианта
    python3 lab8/app/main.py matrix   # матрица сдвигов для короткого слова
    python3 lab8/app/main.py ascii    # 3 символа -> двоичный код -> BWT
    python3 lab8/app/main.py timing   # время прямого/обратного преобразований
"""
import random
import sys
import time

NAME = "Тимофей"
SURNAME = "Марушко"
VARIANT_WORD = "летоисчисление"      # вариант 1


def rotations(block):
    """Все циклические сдвиги блока."""
    return [block[i:] + block[:i] for i in range(len(block))]


def bwt(block):
    """Прямое преобразование: (последний столбец, номер исходной строки)."""
    table = sorted(rotations(block))
    last = "".join(row[-1] for row in table)
    return last, table.index(block)


def inverse_bwt(last, index):
    """Обратное преобразование по последнему столбцу и номеру строки."""
    n = len(last)
    table = [""] * n
    for _ in range(n):
        table = sorted(last[i] + table[i] for i in range(n))
    return table[index]


def to_bits(text):
    return "".join(format(byte, "08b") for byte in text.encode("utf-8"))


def from_bits(bits):
    data = bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))
    return data.decode("utf-8")


def show_blocks():
    print("Прямое и обратное преобразование трёх блоков (вариант 1)")
    for title, block in (("имя", NAME), ("фамилия", SURNAME),
                         ("слово варианта", VARIANT_WORD)):
        last, idx = bwt(block)
        back = inverse_bwt(last, idx)
        print()
        print("  {}: {}".format(title, block))
        print("    длина блока        : {} символов".format(len(block)))
        print("    последний столбец L: {}".format(last))
        print("    номер строки I     : {}".format(idx))
        print("    восстановлено      : {}".format(back))
        print("    совпадает          : {}".format(back == block))


def show_matrix():
    word = "молоко"
    table = sorted(rotations(word))
    print("Матрица циклических сдвигов для слова «{}»:".format(word))
    print("   №   сдвиг      последний символ")
    for i, row in enumerate(table, 1):
        mark = " <-- исходный" if row == word else ""
        print("  {:2d}   {}   {}{}".format(i, row, row[-1], mark))
    last, idx = bwt(word)
    print()
    print("L = {}   I = {}".format(last, idx))
    print("Обратное преобразование: {}".format(inverse_bwt(last, idx)))


def show_ascii():
    text = VARIANT_WORD[:3]
    bits = to_bits(text)
    last, idx = bwt(bits)
    back = inverse_bwt(last, idx)
    print("Первые три символа варианта: «{}»".format(text))
    print("  коды ASCII : {}".format(" ".join(str(ord(c)) for c in text)))
    print("  двоичный код ({} бит): {}".format(len(bits), bits))
    print("  L ({} бит): {}".format(len(last), last))
    print("  I = {}".format(idx))
    print("  восстановлено: {}".format(from_bits(back) if back == bits else "ошибка"))
    print("  совпадает с исходными битами: {}".format(back == bits))


def show_timing(lengths=(100, 200, 400, 800, 1600), repeats=5):
    random.seed(8)
    alphabet = "абвгдежзийклмнопрстуфхцчшщыьэюя "
    print("Зависимость времени преобразований от длины блока")
    print("(среднее по {} повторам)".format(repeats))
    print()
    print("  длина | прямое, мс | обратное, мс | восстановлено")
    print("  ------+------------+--------------+--------------")
    for n in lengths:
        block = "".join(random.choice(alphabet) for _ in range(n))
        t0 = time.perf_counter()
        for _ in range(repeats):
            last, idx = bwt(block)
        t1 = time.perf_counter()
        for _ in range(repeats):
            back = inverse_bwt(last, idx)
        t2 = time.perf_counter()
        print("  {:5d} | {:10.2f} | {:12.2f} | {}".format(
            n, 1000 * (t1 - t0) / repeats, 1000 * (t2 - t1) / repeats,
            back == block))


MODES = ("blocks", "matrix", "ascii", "timing", "all")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in MODES:
        raise SystemExit(__doc__)
    if mode in ("all", "blocks"):
        show_blocks()
        print()
    if mode in ("all", "matrix"):
        show_matrix()
        print()
    if mode in ("all", "ascii"):
        show_ascii()
        print()
    if mode in ("all", "timing"):
        show_timing()


if __name__ == "__main__":
    main()
