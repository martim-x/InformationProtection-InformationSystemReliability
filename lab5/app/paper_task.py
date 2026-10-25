#!/usr/bin/env python3
"""Разбор задания с листка (вариант 6): итеративный код, k = 36, матрица 6 x 6.

Код содержит две группы паритетов (строки Xh и столбцы Xv), поэтому
d = 3: исправляется одна ошибка, обнаруживаются две.

Запуск без аргументов воспроизводит оба случая с листка:
    python3 lab5/app/paper_task.py
"""

import argparse


def par(bits):
    """Паритет (сумма по модулю 2) последовательности '0'/'1'."""
    return sum(b == "1" for b in bits) % 2


def to_matrix(xk, k1, k2):
    return [xk[i * k2:(i + 1) * k2] for i in range(k1)]


def encode(xk, k1, k2):
    """Возвращает (строки матрицы, Xh, Xv)."""
    rows = to_matrix(xk, k1, k2)
    xh = "".join(str(par(r)) for r in rows)
    xv = "".join(str(par([rows[i][j] for i in range(k1)])) for j in range(k2))
    return rows, xh, xv


def inject(xk, positions):
    """Инвертирует биты в указанных (1-базных) позициях информационного слова."""
    bits = list(xk)
    for p in positions:
        bits[p - 1] = "1" if bits[p - 1] == "0" else "0"
    return "".join(bits)


def syndrome(yk, xh, xv, k1, k2):
    """Синдром принятого информационного слова: (Sh по строкам, Sv по столбцам)."""
    rows = to_matrix(yk, k1, k2)
    sh = "".join(str(par(rows[i]) ^ int(xh[i])) for i in range(k1))
    sv = "".join(
        str(par([rows[i][j] for i in range(k1)]) ^ int(xv[j])) for j in range(k2)
    )
    return sh, sv


def decode(yk, xh, xv, k1, k2):
    """Локализация и исправление. Возвращает (исправленное слово или None, Sh, Sv)."""
    sh, sv = syndrome(yk, xh, xv, k1, k2)
    if sh.count("1") == 1 and sv.count("1") == 1:
        pos = sh.index("1") * k2 + sv.index("1") + 1
        return inject(yk, [pos]), sh, sv
    return None, sh, sv


def report_case(title, xk, xh, xv, k1, k2, positions):
    print(f"\n=== {title}: ошибки в позициях {', '.join(map(str, positions))} ===")
    yk = inject(xk, positions)
    rows = to_matrix(yk, k1, k2)
    print("Принятые данные Yn:")
    for i, r in enumerate(rows, 1):
        print(f"  строка {i}: {r}")
    fixed, sh, sv = decode(yk, xh, xv, k1, k2)
    broken_rows = [i + 1 for i, c in enumerate(sh) if c == "1"]
    broken_cols = [j + 1 for j, c in enumerate(sv) if c == "1"]
    print(f"  Sh = {sh}  (нарушены строки: {broken_rows or 'нет'})")
    print(f"  Sv = {sv}  (нарушены столбцы: {broken_cols or 'нет'})")
    if fixed is None:
        print("  итог: ошибка ОБНАРУЖЕНА, но местоположение не определено – исправление невозможно")
        return
    pos = sh.index("1") * k2 + sv.index("1") + 1
    print(f"  пересечение: строка {broken_rows[0]}, столбец {broken_cols[0]} -> позиция {pos}")
    print(f"  Yn' = Xk: {fixed == xk}")


def main():
    ap = argparse.ArgumentParser(description="Итеративный код: кодирование и декодирование")
    ap.add_argument("--xk", default="101111001010000010111000100101110011",
                    help="информационное слово (по умолчанию – вариант с листка)")
    ap.add_argument("--k1", type=int, default=6)
    ap.add_argument("--k2", type=int, default=6)
    ap.add_argument("--errors", default="8;10,22",
                    help="позиции ошибок через ';' для разных случаев, внутри случая – через ','")
    args = ap.parse_args()

    xk, k1, k2 = args.xk, args.k1, args.k2
    if len(xk) != k1 * k2:
        raise SystemExit(f"длина Xk {len(xk)} не равна k1*k2 = {k1 * k2}")

    rows, xh, xv = encode(xk, k1, k2)
    print(f"Xk = {xk}  (k = {len(xk)}, матрица {k1} x {k2})")
    for i, r in enumerate(rows, 1):
        print(f"  строка {i}: {r}   Xh[{i}] = {xh[i - 1]}")
    print(f"  Xv = {xv}")
    print(f"Xh = {xh}")
    print(f"Xn = Xk|Xh|Xv = {xk}{xh}{xv}  (n = {len(xk) + len(xh) + len(xv)})")

    for part in args.errors.split(";"):
        positions = [int(p) for p in part.replace(" ", "").split(",") if p]
        report_case("Случай", xk, xh, xv, k1, k2, positions)

    # сколько пар позиций дают такой же синдром, как у последнего случая
    last = [int(p) for p in args.errors.split(";")[-1].replace(" ", "").split(",") if p]
    target = syndrome(inject(xk, last), xh, xv, k1, k2)
    twins = []
    for a in range(1, len(xk) + 1):
        for b in range(a + 1, len(xk) + 1):
            if syndrome(inject(xk, [a, b]), xh, xv, k1, k2) == target:
                twins.append((a, b))
    print(f"\nПар позиций с тем же синдромом {target}: {len(twins)} -> {twins}")


if __name__ == "__main__":
    main()
