"""Лабораторная работа №7 – перемежение/деперемежение данных.

Блоковый перемежитель/деперемежитель совместно с циклическим (7,3)-кодом
с порождающим полиномом G(x) = x^4 + x^2 + x + 1 (0b10111).

Схема тракта: информационное слово Xk разбивается на слова по k = 3 бита,
каждое кодируется систематически в кодовое слово длиной n = 7. Кодовые слова
группируются в блоки по m штук, записываются строками матрицы m x n и
передаются по столбцам (перемежение). В канал вносится пакет ошибок заданной
длины; после деперемежения пакет разносится по разным кодовым словам блока
и исправляется синдромным декодером.

Запуск:
    python3 lab7/app/main.py            # полный прогон
    python3 lab7/app/main.py code       # параметры кода и кодовые слова
    python3 lab7/app/main.py syndromes  # таблица синдромов
    python3 lab7/app/main.py matrix     # матрица перемежения
    python3 lab7/app/main.py plain      # передача без перемежения
    python3 lab7/app/main.py shuffle    # передача с перемежением
    python3 lab7/app/main.py experiment # влияние глубины перемежения
"""
import random
import sys

# --- параметры кода (задание с листка) -------------------------------------
R = 4                          # степень порождающего полинома: n - k
K = 3                          # длина информационного слова, бит
N = K + R                      # длина кодового слова, бит
G = (1 << 4) | (1 << 2) | (1 << 1) | 1       # x^4 + x^2 + x + 1
XK = "101100111101001000011110100111110111"  # 36 бит = 12 слов по 3 бита
BURST_START = 7                # первая позиция пакета ошибок (1-based)
BURST_LEN = 6                  # биты 7..12 включительно
DEPTH = 12                     # штатное число строк матрицы перемежения

SYNDROMES = None


def poly_mod(a, b):
    """Остаток от деления полиномов над GF(2): a mod b."""
    deg_b = b.bit_length() - 1
    while a and a.bit_length() - 1 >= deg_b:
        a ^= b << ((a.bit_length() - 1) - deg_b)
    return a


def encode(info):
    """Систематическое кодирование: Xn = Xk*x^r + (Xk*x^r mod G)."""
    shifted = info << R
    return shifted | poly_mod(shifted, G)


def syndrome(word):
    return poly_mod(word, G)


def syndrome_table():
    """Синдром одиночной ошибки -> номер бита от младшего разряда."""
    global SYNDROMES
    if SYNDROMES is None:
        SYNDROMES = {syndrome(1 << i): i for i in range(N)}
    return SYNDROMES


def decode(word):
    """Синдромное декодирование: (слово | None, число исправленных бит)."""
    s = syndrome(word)
    if s == 0:
        return word, 0
    if s in syndrome_table():
        return word ^ (1 << syndrome_table()[s]), 1
    return None, 0


def info_words(bits):
    return [bits[i:i + K] for i in range(0, len(bits), K)]


def encode_stream(bits):
    return [encode(int(w, 2)) for w in info_words(bits)]


def bits_of(codes):
    return "".join(format(c, "0{}b".format(N)) for c in codes)


def interleave(codes, depth):
    """Записать блок из depth кодовых слов строками и прочитать по столбцам."""
    rows = codes[:depth]
    out = []
    for col in range(N):
        for row in rows:
            out.append((row >> (N - 1 - col)) & 1)
    return out


def deinterleave(bits, depth):
    """Принять поток по столбцам матрицы depth x N, вернуть кодовые слова."""
    rows = [0] * depth
    t = 0
    for col in range(N):
        for r in range(depth):
            rows[r] = (rows[r] << 1) | bits[t]
            t += 1
    return rows


def transmit(codes, depth):
    """Разбить кодовые слова на блоки по depth и перемежить каждый блок."""
    bits = []
    for i in range(0, len(codes), depth):
        bits += interleave(codes[i:i + depth], min(depth, len(codes) - i))
    return bits


def receive(bits, depth, count):
    """Деперемежение всех блоков и синдромное декодирование."""
    words, fixed, refused = [], 0, 0
    per = N * depth
    for i, start in enumerate(range(0, len(bits), per)):
        rows = min(depth, count - i * depth)
        for code in deinterleave(bits[start:start + N * rows], rows):
            done, nfix = decode(code)
            if done is None:
                refused += 1
                words.append("?" * K)
            else:
                fixed += nfix
                words.append(format(done >> R, "0{}b".format(K)))
    return "".join(words), fixed, refused


def receive_plain(bits):
    """Приём без перемежения: поток сразу делится на кодовые слова."""
    words, fixed, refused = [], 0, 0
    for start in range(0, len(bits), N):
        done, nfix = decode(int("".join(map(str, bits[start:start + N])), 2))
        if done is None:
            refused += 1
            words.append("?" * K)
        else:
            fixed += nfix
            words.append(format(done >> R, "0{}b".format(K)))
    return "".join(words), fixed, refused


def apply_burst(bits, start, length):
    """Инвертировать биты в позициях start..start+length-1 (0-based)."""
    out = list(bits)
    for t in range(start, start + length):
        out[t] ^= 1
    return out


# --- вывод по частям (используется для скриншотов) -------------------------

def show_code(codes):
    print("Код: (n, k) = ({}, {}), r = {}".format(N, K, R))
    print("G(x) = x^4 + x^2 + x + 1 = (x + 1)(x^3 + x^2 + 1), 0b{:05b}".format(G))
    print("G(x) делит x^7 + 1 -> n = 7, dmin = 4, t_испр = 1")
    print("Xk = {} ({} бит = {} слов по {} бита)".format(XK, len(XK), len(codes), K))
    print()
    print("Кодовые слова Xn = Xk*x^r + (Xk*x^r mod G):")
    print("   №   Xk   Xr   Xn      Xn mod G")
    for i, (w, c) in enumerate(zip(info_words(XK), codes), 1):
        print("  {:2d}   {}  {}  {}  {}".format(
            i, w, format(c & ((1 << R) - 1), "04b"),
            format(c, "0{}b".format(N)), format(syndrome(c), "04b")))
    print()
    print("Поток на входе перемежителя ({} бит):".format(len(codes) * N))
    print("  " + bits_of(codes))


def show_syndromes():
    print("Таблица синдромов одиночных ошибок S = E(x) mod G(x):")
    print("  позиция  E(x)    S       позиция  E(x)    S")
    half = (N + 1) // 2
    for i in range(half):
        left = "     {:>2d}    x^{}   {}      ".format(
            i + 1, N - 1 - i, format(syndrome(1 << (N - 1 - i)), "04b"))
        j = i + half
        right = "   {:>2d}    x^{}   {}".format(
            j + 1, N - 1 - j, format(syndrome(1 << (N - 1 - j)), "04b")) if j < N else ""
        print(left + right)
    print()
    print("Все {} синдромов различны -> код исправляет любую одиночную ошибку".format(N))


def show_matrix(codes):
    m = len(codes)
    print("Матрица перемежения {} x {} (строки – кодовые слова):".format(m, N))
    print("         " + "  ".join("c{}".format(c + 1) for c in range(N)))
    for i, c in enumerate(codes, 1):
        print("   w{:<3d}   ".format(i) + "   ".join(format(c, "0{}b".format(N))))
    print()
    print("Запись – по строкам, передача – по столбцам:")
    print("c1 (w1..w{}), затем c2 (w1..w{}) и так далее.".format(m, m))
    shuf = transmit(codes, m)
    line = "".join(map(str, shuf))
    print("Поток после перемежения ({} бит):".format(len(line)))
    for i in range(0, len(line), 42):
        print("  " + line[i:i + 42])


def show_plain(codes):
    plain = bits_of(codes)
    damaged = apply_burst([int(b) for b in plain], BURST_START - 1, BURST_LEN)
    print("Передача без перемежения")
    print("  передано : " + plain)
    print("  принято  : " + "".join(map(str, damaged)))
    print("  ошибки в битах {}-{} ({} бит подряд)".format(
        BURST_START, BURST_START + BURST_LEN - 1, BURST_LEN))
    rec, fixed, refused = receive_plain(damaged)
    print("  декодер  : исправлено одиночных ошибок {}, отказов {}".format(fixed, refused))
    print("  получено : " + " ".join(info_words(rec)))
    print("  было     : " + " ".join(info_words(XK)))
    print("  совпадает с Xk: {}".format(rec == XK))


def block_interleave(bits, rows):
    """Блочный перемежитель по рис. 7.1 методички: биты пишутся строками
    таблицы из `rows` строк, читаются по столбцам."""
    bits = list(bits)
    cols = -(-len(bits) // rows)
    bits += ["0"] * (rows * cols - len(bits))
    out = []
    for c in range(cols):
        for r in range(rows):
            out.append(bits[r * cols + c])
    return "".join(out)


def show_primer():
    """Пример 7.1 методички: 5 блоков по 5 бит, таблица 5 x 5."""
    blocks = ["10101", "10011", "00110", "10001", "00001"]
    src = "".join(blocks)
    print("Пример из п. 7.1 методички: последовательность делится на блоки")
    print("по {} бит, каждый блок пишется в свою строку.".format(len(blocks[0])))
    print("         " + "  ".join("c{}".format(c + 1) for c in range(5)))
    for i, b in enumerate(blocks, 1):
        print("   стр{:2d}   ".format(i) + "   ".join(b))
    print()
    print("Входная последовательность : " + src)
    print("После перемежения (столбцы): " + block_interleave(src, len(blocks)))
    print("Глубина перемежения d = m - 1 = {} (второй символ станет шестым)".format(
        len(blocks) - 1))
    print()
    seq = "10111010011001100100"
    print("Контрольный вопрос 5: вход " + seq)
    for rows, cols in ((5, 4), (4, 5), (5, 5), (4, 4)):
        src2 = seq[:rows * cols] if len(seq) >= rows * cols else seq + "0" * (rows * cols - len(seq))
        print("   таблица {}x{}: {}".format(rows, cols, block_interleave(src2, rows)))


def show_shuffle(codes):
    m = len(codes)
    shuf = transmit(codes, m)
    damaged = apply_burst(shuf, BURST_START - 1, BURST_LEN)
    print("Передача с перемежением (матрица {} x {})".format(m, N))
    print("  передано : " + "".join(map(str, shuf)))
    print("  принято  : " + "".join(map(str, damaged)))
    print("  ошибки в битах {}-{} ({} бит подряд)".format(
        BURST_START, BURST_START + BURST_LEN - 1, BURST_LEN))
    rows = sorted({(t % m) + 1 for t in range(BURST_START - 1, BURST_START - 1 + BURST_LEN)})
    print("  пакет разнесён по словам w{}, в каждом одна ошибка".format(
        ", w".join(map(str, rows))))
    rec, fixed, refused = receive(damaged, m, m)
    print("  декодер  : исправлено одиночных ошибок {}, отказов {}".format(fixed, refused))
    print("  результат: " + rec)
    print("  совпадает с Xk: {}".format(rec == XK))


def experiment(trials=35, lengths=(3, 5, 6, 8), depth=DEPTH):
    """П. 2 задания методички: для каждой длины пакета 35 случайных ситуаций,
    сравнение переданной и восстановленной последовательностей без перемежения
    и с перемежением."""
    codes = encode_stream(XK)
    total = len(codes) * N
    print("Эксперимент по п. 2 задания: {} случайных положений пакета".format(trials))
    print("на каждую длину, сравнение без перемежения и с матрицей {} x {}".format(
        len(codes), N))
    print()

    def run(bits, is_plain):
        if is_plain:
            return receive_plain(bits)
        return receive(bits, depth, len(codes))

    print("  b | без перемежения      | с перемежением        | остаток")
    print("    | восст. ложн.  отказ  | восст. ложн.  отказ   | бит")
    print("  --+----------------------+-----------------------+--------")
    for b in lengths:
        stats = {}
        for is_plain in (True, False):
            full = false = fail = 0
            resid = 0.0
            for _ in range(trials):
                if is_plain:
                    src = [int(ch) for ch in bits_of(codes)]
                else:
                    src = transmit(codes, depth)
                start = random.randrange(0, total - b + 1)
                rec, _, refused = run(apply_burst(src, start, b), is_plain)
                if rec == XK:
                    full += 1
                else:
                    resid += sum(1 for x, y in zip(rec, XK) if x != y)
                    if refused:
                        fail += 1
                    else:
                        false += 1
            stats[is_plain] = (full, false, fail, resid / trials)
        free, fls, fl, _ = stats[True]
        shf, shf_false, shf_fail, shf_resid = stats[False]
        print("  {} | {:4d}   {:4d}   {:4d}   | {:4d}   {:4d}   {:4d}    | {:6.1f}".format(
            b, free, fls, fl, shf, shf_false, shf_fail, shf_resid))
    print()
    print("  восст. – сообщение совпало с Xk; ложн. – декодер «исправил»")
    print("  кратный пакет как одиночную ошибку; отказ – синдром не найден;")
    print("  остаток – среднее число неверных информационных битов на опыт.")


def depth_effect(trials=35, lengths=(3, 5, 6, 8), depths=(1, 2, 3, 4, 6, 12)):
    """Эффективность перемежения в зависимости от глубины (числа строк)."""
    codes = encode_stream(XK)
    print("Эффективность перемежения: {} случайных положений".format(trials))
    print("Доля полностью восстановленных сообщений, % (m = 1 – без перемежения)")
    header = "  b \\ m |" + "".join("{:>7d}".format(d) for d in depths)
    print(header)
    print("  " + "-" * (len(header) - 2))
    for b in lengths:
        row = []
        for d in depths:
            good = 0
            for _ in range(trials):
                shuf = transmit(codes, d)
                start = random.randrange(0, len(shuf) - b + 1)
                rec, _, _ = receive(apply_burst(shuf, start, b), d, len(codes))
                good += rec == XK
            row.append(100.0 * good / trials)
        print("  {:5d} |".format(b) + "".join("{:>6.0f}%".format(v) for v in row))
    print("  b – длина пакета ошибок, m – число строк матрицы")
    print("  dmin = 4 -> t_испр = 1, поэтому пакет исправляется при b <= m")


MODES = ("all", "code", "syndromes", "matrix", "primer", "plain", "shuffle",
         "experiment", "depth")


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "all"
    if mode not in MODES:
        raise SystemExit(__doc__)
    random.seed(7)
    codes = encode_stream(XK)
    if mode in ("all", "code"):
        show_code(codes)
        print()
    if mode in ("all", "syndromes"):
        show_syndromes()
        print()
    if mode in ("all", "primer"):
        show_primer()
        print()
    if mode in ("all", "matrix"):
        show_matrix(codes)
        print()
    if mode in ("all", "plain"):
        show_plain(codes)
        print()
    if mode in ("all", "shuffle"):
        show_shuffle(codes)
        print()
    if mode in ("all", "experiment"):
        experiment()
        print()
    if mode in ("all", "depth"):
        depth_effect()


if __name__ == "__main__":
    main()
