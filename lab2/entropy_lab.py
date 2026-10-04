import collections
import math

BASE = "."
INPUT = f"{BASE}/input"
OUTPUT = f"{BASE}/output"

# Алфавиты, по которым фильтруется текст документа.
ALPHABETS = {
    "latin": set("abcdefghijklmnopqrstuvwxyz"),
    "cyrillic": set("абвгдеёжзийклмнопрстуфхцчшщъыьэюя"),
}


def log2_0(x):
    """Вклад символа p·log2(p) в энтропию; 0 при p <= 0."""
    return 0.0 if x <= 0 else -x * math.log2(x)


def counter_of(path, alphabet):
    """Задание 'а': частости символов документа."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read().lower()
    return collections.Counter(ch for ch in text if ch in ALPHABETS[alphabet])


def shannon(counter):
    """Задание 'а': энтропия Шеннона (2.1)."""
    total = sum(counter.values())
    return sum(log2_0(v / total) for v in counter.values()), total


def hartley(n):
    """Задание 'а': энтропия Хартли H = log2 N (2.2)."""
    return math.log2(n) if n else 0.0


def redundancy(hs, n):
    """Задание 'а': избыточность алфавита R = 1 - H_Шеннона / H_Хартли."""
    return 1.0 - hs / hartley(n) if hartley(n) else 0.0


def binary_entropy(p1):
    """Задание 'б': энтропия бинарного алфавита (2.4)."""
    return log2_0(p1) + log2_0(1 - p1)


def channel_entropy(p):
    """Задание 'г': условная энтропия ДСК H(Y|X) (2.6)."""
    return log2_0(p) + log2_0(1 - p)


def encode_bits(text, enc):
    """Задание 'б': сообщение -> двоичная строка (8 бит на байт)."""
    return "".join(f"{x:08b}" for x in text.encode(enc))


def save_md(counter, path, label):
    """Задание 'а': гистограмма частот -> markdown-таблица."""
    total = sum(counter.values())
    ordered = counter.most_common()
    maxf = ordered[0][1]
    rows = []
    for ch, cnt in ordered:
        bar = "#" * max(1, round(40 * cnt / maxf))
        rows.append(f"| `{ch}` | {cnt} | {cnt / total:.6f} | {bar} |")
    table = (
        f"# Гистограмма частот символов — {label}\n\n"
        f"Всего символов алфавита в документе: {total}\n\n"
        "| Символ | Частота | Вероятность | Гистограмма |\n"
        "|---|---:|---:|---|\n" + "\n".join(rows) + "\n"
    )
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(table)


def alphabet_analysis(label, path, alphabet):
    """Задание 'а': анализ алфавита документа + гистограмма."""
    counter = counter_of(path, alphabet)
    hs, total = shannon(counter)
    hh = hartley(len(counter))
    print(f"== {label} (N={len(counter)}, символов={total}) ==")
    print(
        f"  Энтропия Шеннона: {hs:.4f}  |  Хартли: {hh:.4f}  |  Избыточность: {redundancy(hs, len(counter)):.4f}"
    )
    print(
        "  Топ-10 символов: "
        + ", ".join(f"{ch}({cnt / total:.3f})" for ch, cnt in counter.most_common(10))
    )
    save_md(counter, f"{OUTPUT}/freq_{alphabet}.md", label)
    return hs


# --- Данные: собственные ФИО в трёх вариантах записи/кодировки ---
fio_lat = "Marushko Timofey Fyodorovich"
fio_cyr = "Марушко Тимофей Фёдорович"


if __name__ == "__main__":
    print("ЛАБОРАТОРНАЯ РАБОТА No2 — ЭЛЕМЕНТЫ ТЕОРИИ ИНФОРМАЦИИ\n")

    # Задание 'а': энтропия алфавитов для двух входных документов (книг).
    print("а) ЭНТРОПИЯ АЛФАВИТОВ ВХОДНЫХ ДОКУМЕНТОВ")
    h_lat = alphabet_analysis("Латиница", f"{INPUT}/latin.txt", "latin")
    h_cyr = alphabet_analysis("Кириллица", f"{INPUT}/cyrillic.txt", "cyrillic")
    print()

    # Задание 'б': энтропия бинарного алфавита 8-битных кодов ФИО.
    print("б) ЭНТРОПИЯ БИНАРНОГО АЛФАВИТА КОДОВ ФИО")
    for name, text, enc in [
        ("ASCII", fio_lat, "ascii"),
        ("WIN1251", fio_cyr, "cp1251"),
        ("UTF-8", fio_cyr, "utf-8"),
    ]:
        bits = encode_bits(text, enc)
        p1 = bits.count("1") / len(bits)
        print(
            f"  {name:<8} n={len(bits):>3} бит  p(1)={p1:.6f}  H(A2)={binary_entropy(p1):.6f}"
        )
    print()

    # Задание 'в': количество информации в сообщении I(Xk) = H·k (2.3).
    print("в) КОЛИЧЕСТВО ИНФОРМАЦИИ В СООБЩЕНИИ ФИО")
    for label, text, h in [
        ("По алфавиту латиницы", fio_lat, h_lat),
        ("По алфавиту кириллицы", fio_cyr, h_cyr),
    ]:
        print(f"  {label:<24} k={len(text):>2}  I={h * len(text):.4f} бит")
    for name, text, enc in [("ASCII", fio_lat, "ascii"), ("WIN1251", fio_cyr, "cp1251")]:
        bits = encode_bits(text, enc)
        p1 = bits.count("1") / len(bits)
        print(
            f"  В кодах {name:<7} n={len(bits):>3}  I={binary_entropy(p1) * len(bits):.4f} бит"
        )
    print()

    # Задание 'г': ДСК, эффективная энтропия He = 1 - H(Y|X) (2.5, 2.6).
    print("г) ПЕРЕДАЧА ПО ДСК (формулы 2.5, 2.6)")
    for name, text, enc in [("ASCII", fio_lat, "ascii"), ("WIN1251", fio_cyr, "cp1251")]:
        n = len(encode_bits(text, enc))
        print(f"  {name}, n={n} бит:")
        for p in [0.1, 0.5, 1.0]:
            hch = channel_entropy(p)
            print(
                f"    p={p:<4} H(Y|X)={hch:.6f}  He={1 - hch:.6f}  I(Yk)={n * (1 - hch):.4f}  потери={n * hch:.4f}"
            )
