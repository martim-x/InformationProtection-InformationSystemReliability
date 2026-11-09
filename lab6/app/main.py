"""Лабораторная работа №6 – циклические коды.

Циклический (n,k)-код над GF(2) с порождающим полиномом
G(x) степени r = n - k. Кодирование систематическое через деление,
синдромное декодирование одиночной ошибки.
"""
import random


def poly_mod(a, b):
    """Деление полиномов над GF(2): возвращает остаток a mod b."""
    deg_b = b.bit_length() - 1
    while a.bit_length() - 1 >= deg_b and a:
        sh = (a.bit_length() - 1) - deg_b
        a ^= b << sh
    return a


def encode(xk, g, r):
    """Систематическое кодирование: Xn = Xk*x^r + (Xk*x^r mod G)."""
    shifted = xk << r
    rem = poly_mod(shifted, g)
    return shifted | rem, rem


def syndrome(yn, g):
    return poly_mod(yn, g)


def build_error_vector(n, pos):
    return 1 << (n - 1 - pos)


def main():
    # вариант 1: r=4, G(x)=x^4+x+1  -> 0b10011
    r = 4
    g = (1 << 4) | (1 << 1) | 1  # x^4 + x + 1
    # информационное слово: 1011 (k=4, n=8)
    xk = 0b1011
    n = 4 + r
    xn, rem = encode(xk, g, r)
    print("r =", r, "n =", n, "k =", n - r)
    print("G(x) =", bin(g))
    print("Xk =", format(xk, '04b'))
    print("Xr =", format(rem, '04b'))
    print("Xn =", format(xn, '08b'))
    # проверка делимости
    print("Xn mod G =", bin(syndrome(xn, g)))
    # одиночная ошибка
    pos = 2  # позиция с 0
    yn = xn ^ build_error_vector(n, pos)
    s = syndrome(yn, g)
    print("Yn =", format(yn, '08b'), "ошибка в позиции", pos)
    print("синдром =", format(s, '04b'))
    # таблица синдромов одиночных ошибок
    print("\nТаблица синдромов (одиночные ошибки):")
    for i in range(n):
        e = build_error_vector(n, i)
        print("  позиция", i, "-> синдром", format(syndrome(e, g), '04b'))
    # исправление
    # находим позицию по синдрому
    mist = None
    for i in range(n):
        if syndrome(build_error_vector(n, i), g) == s:
            mist = i
            break
    if mist is not None:
        xn_rec = yn ^ build_error_vector(n, mist)
        print("исправлена позиция", mist, "->", format(xn_rec, '08b'),
              "совпадает:", xn_rec == xn)
    # 2 ошибки
    yn2 = xn ^ build_error_vector(n, 0) ^ build_error_vector(n, 3)
    s2 = syndrome(yn2, g)
    print("\n2 ошибки: синдром =", format(s2, '04b'),
          "(не нулевой, но однозначной локализации нет)")
    # перебор dmin
    # минимальный вес ненулевого кодового слова
    minw = n + 1
    for m in range(1, 1 << (n - r)):
        xk_ = m
        xn_, _ = encode(xk_, g, r)
        if xn_:
            w = bin(xn_).count('1')
            if w < minw:
                minw = w
    print("dmin (минимальный вес ненулевого слова) =", minw)


if __name__ == "__main__":
    main()
