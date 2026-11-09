"""Лабораторная работа №9 – сжатие/распаковка данных на основе статистических
методов (код Хаффмана).

Строится таблица частот символов сообщения, по ней – префиксное двоичное
дерево Хаффмана, затем выполняется прямое (в битовую строку) и обратное
(по дереву) преобразования. Эффективность сравнивается с равномерным
кодом ASCII.

Запуск:
    python3 lab9/app/main.py freq      # частоты символов сообщения
    python3 lab9/app/main.py codes     # коды Хаффмана и длина в битах
    python3 lab9/app/main.py codec     # кодирование и декодирование
    python3 lab9/app/main.py compare   # эффективность: ASCII, Хаффман, Шеннон – Фано
"""
import math
import sys
from collections import Counter

NAME = "Тимофей"
SURNAME = "Марушко"
MESSAGE = NAME + " " + SURNAME

# частоты букв русского языка (таблица из справочных материалов, без пробела)
RUS_FREQ = {
    "о": 0.1097, "е": 0.0845, "а": 0.0801, "и": 0.0735, "н": 0.0670,
    "т": 0.0626, "с": 0.0547, "р": 0.0473, "в": 0.0454, "л": 0.0440,
    "к": 0.0349, "м": 0.0321, "д": 0.0298, "п": 0.0281, "у": 0.0262,
    "я": 0.0201, "ы": 0.0190, "ь": 0.0174, "г": 0.0170, "з": 0.0165,
    "б": 0.0159, "ч": 0.0144, "й": 0.0121, "х": 0.0097, "ж": 0.0094,
    "ш": 0.0073, "ю": 0.0064, "ц": 0.0048, "щ": 0.0036, "э": 0.0032,
    "ф": 0.0026, "ъ": 0.0004, "ё": 0.0004, " ": 0.1750,
}


class Node:
    __slots__ = ("symbol", "weight", "left", "right")

    def __init__(self, symbol=None, weight=0, left=None, right=None):
        self.symbol = symbol
        self.weight = weight
        self.left = left
        self.right = right


def build_tree(weights):
    """Дерево Хаффмана по словарю «символ -> вес»."""
    nodes = [Node(s, w) for s, w in sorted(weights.items())]
    if len(nodes) == 1:
        return Node(None, nodes[0].weight, nodes[0], None)
    while len(nodes) > 1:
        nodes.sort(key=lambda n: (n.weight, str(n.symbol)))
        left, right = nodes.pop(0), nodes.pop(0)
        nodes.append(Node(None, left.weight + right.weight, left, right))
    return nodes[0]


def build_codes(tree):
    """Префиксные коды: обход дерева, левая ветвь – 0, правая – 1."""
    codes = {}

    def walk(node, prefix):
        if node.symbol is not None:
            codes[node.symbol] = prefix or "0"
            return
        if node.left is not None:
            walk(node.left, prefix + "0")
        if node.right is not None:
            walk(node.right, prefix + "1")

    walk(tree, "")
    return codes


def encode(text, codes):
    return "".join(codes[c] for c in text)


def decode(bits, tree):
    out = []
    node = tree
    for bit in bits:
        node = node.left if bit == "0" else node.right
        if node is None:
            raise ValueError("некорректный код")
        if node.symbol is not None:
            out.append(node.symbol)
            node = tree
    return "".join(out)


def entropy(weights):
    total = sum(weights.values())
    return -sum((w / total) * math.log2(w / total) for w in weights.values())


def shannon_fano(weights):
    """Коды Шеннона – Фано для сравнения эффективности."""
    items = sorted(weights.items(), key=lambda kv: (-kv[1], kv[0]))
    codes = {s: "" for s, _ in items}

    def split(group):
        if len(group) < 2:
            return
        total = sum(w for _, w in group)
        acc = 0
        cut = 1
        for i in range(len(group)):
            acc += group[i][1]
            if acc >= total / 2:
                cut = i + 1
                break
        for s, _ in group[:cut]:
            codes[s] += "0"
        for s, _ in group[cut:]:
            codes[s] += "1"
        split(group[:cut])
        split(group[cut:])

    split(items)
    return codes


def show_freq():
    counts = Counter(MESSAGE)
    total = sum(counts.values())
    print("Сообщение: «{}» ({} символов, {} различных)".format(
        MESSAGE, len(MESSAGE), len(counts)))
    print()
    print("  символ | частота | вероятность")
    for sym, cnt in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        print("    {!r:5} | {:7d} | {:11.3f}".format(sym, cnt, cnt / total))
    print()
    print("Энтропия сообщения: {:.3f} бит/символ".format(entropy(counts)))


def show_codes():
    counts = Counter(MESSAGE)
    tree = build_tree(counts)
    codes = build_codes(tree)
    total_bits = sum(len(codes[c]) for c in MESSAGE)
    print("Коды Хаффмана для сообщения «{}»".format(MESSAGE))
    print()
    print("  символ | вес | код     | длина")
    for sym, cnt in sorted(counts.items(), key=lambda kv: (len(codes[kv[0]]), kv[0])):
        print("    {!r:5} | {:3d} | {:7} | {:5d}".format(
            sym, cnt, codes[sym], len(codes[sym])))
    print()
    print("Всего битов: {} на {} символов ({:.3f} бит/символ)".format(
        total_bits, len(MESSAGE), total_bits / len(MESSAGE)))


def show_codec():
    counts = Counter(MESSAGE)
    tree = build_tree(counts)
    codes = build_codes(tree)
    bits = encode(MESSAGE, codes)
    back = decode(bits, tree)
    print("Прямое и обратное преобразование")
    print("  исходное сообщение : «{}»".format(MESSAGE))
    print("  битовая строка ({} бит):".format(len(bits)))
    for i in range(0, len(bits), 60):
        print("    " + bits[i:i + 60])
    print("  декодировано       : «{}»".format(back))
    print("  совпадает          : {}".format(back == MESSAGE))


def show_compare():
    counts = Counter(MESSAGE)
    tree = build_tree(counts)
    codes = build_codes(tree)
    sf = shannon_fano(counts)
    n = len(MESSAGE)
    huffman_bits = sum(len(codes[c]) for c in MESSAGE)
    sf_bits = sum(len(sf[c]) for c in MESSAGE)
    ascii_bits = 8 * n
    print("Эффективность кодирования сообщения «{}»".format(MESSAGE))
    print()
    print("  метод            | бит | бит/символ | к ASCII, %")
    print("  -----------------+-----+------------+-----------")
    for title, b in (("ASCII (8 бит)", ascii_bits),
                     ("Хаффман (динам.)", huffman_bits),
                     ("Шеннон – Фано", sf_bits)):
        print("  {:<16} | {:3d} | {:10.3f} | {:9.1f}".format(
            title, b, b / n, 100.0 * b / ascii_bits))
    print()
    print("  энтропия         | {:3.1f} | {:10.3f} | {:9.1f}".format(
        entropy(counts) * n, entropy(counts), 100.0 * entropy(counts) / 8))

    # статическая таблица: коды строятся по частотам русского языка
    static_codes = build_codes(build_tree(RUS_FREQ))
    fits = [c for c in MESSAGE if c in static_codes]
    static_bits = sum(len(static_codes[c]) for c in fits) + 8 * (n - len(fits))
    print()
    print("Статическая таблица (частоты русского языка):")
    print("  кодов нашлось для {} из {} символов".format(len(fits), n))
    print("  длина сообщения по статической таблице: {} бит".format(static_bits))
    print("  по сравнению с ASCII: {:.1f} %".format(100.0 * static_bits / ascii_bits))


MODES = ("freq", "codes", "codec", "compare", "all")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in MODES:
        raise SystemExit(__doc__)
    if mode in ("all", "freq"):
        show_freq()
        print()
    if mode in ("all", "codes"):
        show_codes()
        print()
    if mode in ("all", "codec"):
        show_codec()
        print()
    if mode in ("all", "compare"):
        show_compare()


if __name__ == "__main__":
    main()
