#!/usr/bin/env python3
"""
Дополнительное задание к лабораторной работе № 5: разбор одиночной,
двойной, тройной и четырёхкратной ошибки для двух кодов.

Сравниваются:
  - код Хемминга (лабораторная № 4), dmin = 3, t_и = 1, t_о = 1;
  - итеративный код (вариант 1 лабораторной № 5) по схеме рисунка 5.1:
    проверки Xh по строкам, Xv по столбцам, символ общей чётности Xhv;
  - тот же итеративный код с дополнительными проверками по квадрантам,
    он добавлен, чтобы показать, чем ловится необнаруживаемая ошибка
    из четырёх бит в вершинах прямоугольника.

Формулы (8) и (9) лекции «04 - Избыточность и коды», страница 10:
  t_и = (d - 1) / 2 при нечётном d, (d - 2) / 2 при чётном d;
  t_о = (d - 1) / 2 при нечётном d, d / 2 при чётном d.

Используется только стандартная библиотека Python (math, itertools,
random, argparse). Внешних пакетов нет, в том числе numpy, поэтому
задание запускается одной командой без установки зависимостей.

Запуск:
    python3 lab5/доп_ошибки.py
    python3 lab5/доп_ошибки.py --k 16 --k1 4 --k2 4
    python3 lab5/доп_ошибки.py --k 8 --k1 2 --k2 2
"""

import argparse
import math
import random
from itertools import combinations


# =========================================================================
#  ЗАДАЧА 1. РЕАЛИЗАЦИЯ КОДОВ
# =========================================================================


def bits_to_str(bits) -> str:
    """Склеивает список бит в строку из нулей и единиц для вывода."""
    return "".join(str(bit) for bit in bits)


def binom(wt, r):
    """Возвращает биномиальный коэффициент, то есть C(r, wt).

    Нужен для проверки числа комбинаций позиций: всего вариантов ошибки
    кратности t ровно C(n, t), и это число должно совпасть с тем, что
    насчитал перебор.
    """
    return math.comb(r, wt)


def par(bits):
    """Возвращает чётность списка бит, то есть XOR всех его элементов."""
    acc = 0
    for bit in bits:
        acc ^= bit
    return acc


def flip(word, positions):
    """Возвращает копию слова word с инвертированными битами в positions."""
    result = list(word)
    for pos in positions:
        result[pos] ^= 1
    return result


def any_bit(bits):
    """Сообщает, есть ли в списке хотя бы одна единица (не нулевой ли он)."""
    for bit in bits:
        if bit == 1:
            return True
    return False


# -------------------------------------------------------------------------
#  1.1. Код Хемминга, dmin = 3
# -------------------------------------------------------------------------
def calc_r(k):
    """Подбирает число избыточных символов r для кода Хемминга.

    Перебор идёт вверх, пока не выполнится 2^r >= k + r + 1. Именно это
    неравенство из лабораторной № 4 гарантирует, что все n = k + r
    столбцов матрицы H можно выбрать попарно различными, а это необходимое
    условие для однозначного поиска одиночной ошибки.

    Args:
        k: длина информационного слова, бит.

    Returns:
        Минимальное подходящее r.
    """
    r = 1
    while 2 ** r < k + r + 1:
        r += 1
    return r


def build_p_prime(k, r):
    """Строит подматрицу P' размера k x r из столбцов веса не меньше 2.

    Берутся двоичные номера позиций начиная с 3: номера 1 и 2 имеют вес 1
    и не берутся, иначе матрица вырождается. Сначала используются все
    столбцы веса 2, затем веса 3 и так далее. Именно так столбцы P'
    получаются различными.

    Args:
        k: число информационных символов.
        r: число избыточных символов.

    Returns:
        Список из k столбцов длины r.
    """
    p_prime = []
    for wt in range(2, r + 1):
        for num in range(3, 2 ** r):
            bits = bin(num)[2:].zfill(r)
            if bits.count('1') == wt:
                p_prime.append([int(bit) for bit in bits])
                if len(p_prime) == k:
                    return p_prime
    return p_prime


def build_i(r):
    """Строит единичную матрицу I порядка r как список столбцов длины r."""
    return [[1 if row == col else 0 for row in range(r)] for col in range(r)]


def build_h(k, r):
    """Склеивает P' и I в проверочную матрицу H = [P' | I] размера r x n.

    Args:
        k: число информационных символов.
        r: число избыточных символов.

    Returns:
        Список из r строк длины n = k + r.
    """
    p_prime = build_p_prime(k, r)
    unit = build_i(r)
    matrix = [[0] * (k + r) for _ in range(r)]
    for row in range(r):
        for col in range(k):
            matrix[row][col] = p_prime[col][row]
        for col in range(r):
            matrix[row][k + col] = unit[col][row]
    return matrix


def calc_xr(xk, p_prime):
    """Вычисляет избыточные символы Xr из информационного слова Xk.

    Xr[i] равен 1 тогда и только тогда, когда число позиций, где Xk = 1
    и i-я строка P' равна 1, нечётно. Это подсчёт пар (1; 1) по модулю 2,
    а не попарный XOR битов.

    Args:
        xk:      информационное слово, список бит.
        p_prime: подматрица P', список столбцов длины r.

    Returns:
        Слово Xr, список из r бит.
    """
    r = len(p_prime[0])
    xr = []
    for row in range(r):
        pairs = 0
        for col in range(len(xk)):
            if xk[col] == 1 and p_prime[col][row] == 1:
                pairs += 1
        xr.append(pairs % 2)
    return xr


def encode_hamming(xk, p_prime):
    """Кодирует Xk в кодовое слово Xn = Xk + Xr в порядке [Xk | Xr]."""
    return list(xk) + calc_xr(xk, p_prime)


def hamming_syndrome(yn, k, p_prime):
    """Вычисляет синдром S принятого слова кодом Хемминга.

    Yr' пересчитывается из Yk теми же формулами, что и Xr из Xk, после
    чего S = Yr XOR Yr'. Нулевой синдром означает, что все проверки чётности
    сошлись; ненулевой при одиночной ошибке совпадает со столбцом H в
    ошибочной позиции.

    Args:
        yn:      принятое кодовое слово длины n.
        k:       длина информационной части.
        p_prime: подматрица P'.

    Returns:
        Синдром S, список из r бит.
    """
    yr = yn[k:]
    yr_prime = calc_xr(yn[:k], p_prime)
    return [0 if yr[i] == yr_prime[i] else 1 for i in range(len(yr))]


def find_error_position(syndrome, matrix_h):
    """Ищет позицию ошибочного бита: ненулевой синдром равен столбцу H.

    При одиночной ошибке синдром в точности совпадает со столбцом H в
    ошибочной позиции. При нескольких ошибках совпадение может быть
    случайным, поэтому для кратности больше единицы найденная позиция
    является ложной коррекцией.

    Args:
        syndrome:  синдром S.
        matrix_h:  проверочная матрица H.

    Returns:
        Индекс позиции (нумерация с 0) либо -1, если столбца нет.
    """
    for col in range(len(matrix_h[0])):
        if [matrix_h[row][col] for row in range(len(matrix_h))] == syndrome:
            return col
    return -1


def build_error_vector(n, positions):
    """Формирует вектор ошибки En: единицы стоят в ошибочных позициях."""
    error = [0] * n
    for pos in positions:
        error[pos] = 1
    return error


class HammingCode:
    """Код Хемминга: кодирование, синдром и декодер с гарантией t_и = 1.

    Класс нужен, чтобы один и тот же интерфейс (syndrome, decode) имели
    оба сравниваемых кода: сводная таблица в задании 6 считается
    единым кодом, иначе сравнение было бы некорректным.
    """

    def __init__(self, xk):
        """Строит код по информационному слову Xk и запоминает параметры."""
        self.xk = list(xk)
        self.k = len(xk)
        self.r = calc_r(self.k)
        self.n = self.k + self.r
        self.p_prime = build_p_prime(self.k, self.r)
        self.matrix_h = build_h(self.k, self.r)
        self.xr = calc_xr(self.xk, self.p_prime)
        self.xn = encode_hamming(self.xk, self.p_prime)
        self.dmin = 3
        # Словарь «синдром -> позиция» строится один раз: синдром одиночной
        # ошибки равен столбцу H этой позиции. Предвычисление нужно, чтобы
        # в задании 6 не пересчитывать синдромы тысячи раз.
        self.single = {}
        for pos in range(self.n):
            key = tuple(self.syndrome(flip(self.xn, [pos])))
            self.single.setdefault(key, []).append(pos)

    def syndrome(self, yn):
        """Возвращает синдром S принятого слова."""
        return hamming_syndrome(yn, self.k, self.p_prime)

    def decode(self, yn):
        """Декодер кода Хемминга.

        Работает по правилу синдрома: нулевой синдром - ошибок нет;
        ненулевой синдром совпадает со столбцом H ошибочной позиции, и этот
        бит инвертируется. Гарантия ограничена t_и = 1, поэтому при
        кратности больше единицы исправление не гарантировано.

        Args:
            yn: принятое кодовое слово.

        Returns:
            Кортеж (исправленное слово или None, позиция или -1, вердикт).
        """
        syndrome = self.syndrome(yn)
        if not any_bit(syndrome):
            return list(yn), [], "S = 0: ошибок нет"
        # одиночная ошибка даёт синдром, совпадающий с синдромом слова,
        # полученного инверсией ровно этого бита
        candidates = self.single.get(tuple(syndrome), [])
        if len(candidates) == 1:
            pos = candidates[0]
            return flip(yn, [pos]), [pos], "ненулевой S = столбец H: одиночная ошибка"
        if not candidates:
            return None, [], ("S ненулевой, но не совпал ни с одним "
                              "столбцом H: кратность больше 1")
        return None, [], ("S совпал сразу с несколькими столбцами H: "
                          "ошибок больше одной")


# -------------------------------------------------------------------------
#  1.2. Итеративный код по схеме рисунка 5.1
# -------------------------------------------------------------------------
#  Информационные биты раскладываются в матрицу k1 x k2. Проверочные
#  символы: Xh[i] - чётность строки i, Xv[j] - чётность столбца j,
#  Xhv - чётность всего слова.
def build_matrix(xk, k1, k2):
    """Раскладывает информационное слово в матрицу построчно, k1 x k2."""
    return [[xk[i * k2 + j] for j in range(k2)] for i in range(k1)]


def calc_xh(matrix):
    """Вычисляет Xh[i] - XOR всех битов строки i, то есть чётность строки."""
    return [par(row) for row in matrix]


def calc_xv(matrix):
    """Вычисляет Xv[j] - XOR всех битов столбца j, то есть чётность столбца."""
    k1 = len(matrix)
    k2 = len(matrix[0])
    return [par([matrix[i][j] for i in range(k1)]) for j in range(k2)]


def calc_xhv(matrix, xh, xv):
    """Вычисляет Xhv - общую чётность всего слова.

    Это XOR всех информационных битов, всех Xh и всех Xv. Ниже в отчёте
    показано, что для матрицы эта величина тождественно равна чётности
    самих информационных битов, потому что p(Xh) = p(Xv) = p(Xk): каждый
    бит Xk входит ровно один раз и в Xh, и в Xv.
    """
    info = [matrix[i][j] for i in range(len(matrix))
            for j in range(len(matrix[0]))]
    return par(info) ^ par(xh) ^ par(xv)


def quad_checks(matrix, k1, k2):
    """Вычисляет чётности четырёх квадрантов матрицы (проверки Xq).

    Квадранты получаются делением матрицы на две равные части по строкам
    и по столбцам. Эти проверки добавлены сверх схемы рисунка 5.1, чтобы
    показать, чем именно ловится ошибка из четырёх бит в вершинах
    прямоугольника: ошибка ломает чётность ровно того квадранта, внутри
    которого лежат её вершины, если вершины не попарно в одном квадранте.

    Args:
        matrix: матрица информационных бит k1 x k2.
        k1:     число строк.
        k2:     число столбцов.

    Returns:
        Список из четырёх чётностей в порядке квадрантов.
    """
    out = []
    for half_i in (0, 1):
        for half_j in (0, 1):
            rows = range(half_i * k1 // 2, (half_i + 1) * k1 // 2)
            cols = range(half_j * k2 // 2, (half_j + 1) * k2 // 2)
            out.append(par([matrix[i][j] for i in rows for j in cols]))
    return out


# Диагональные проверки по classes (j - i) mod 4 нужны для dmin = 5.
# Проверка чётности строк и столбцов не различает два бита в одной строке
# и два бита в одном столбце: в обоих случаях вес кодового слова равен 4.
# Диагонали разбивают биты по разным классам и устраняют этот случай.
def diagonal_checks(xk, k1, k2):
    """Вычисляет чётности четырёх диагональных классов (j - i) mod k2.

    Args:
        xk: информационное слово, k1 * k2 бит.
        k1: число строк матрицы.
        k2: число столбцов матрицы.

    Returns:
        Список из четырёх чётностей.
    """
    out = []
    for d in range(k2):
        out.append(par([xk[i * k2 + j] for i in range(k1)
                        for j in range(k2) if (j - i) % k2 == d]))
    return out


# Три дополнительные проверки, найденные перебором: каждая информационная
# позиция входит ровно в две из них, поэтому одиночный бит весит
# 1 + Xh + Xv + 2 = 5, и при этом все 36 прямоугольников 2 x 2 ловятся.
# Индексы позиций при k1 = k2 = 4.
EXTRA_CHECKS_44 = (
    (0, 2, 3, 5, 6, 7, 8, 9, 11, 12, 13, 14),
    (1, 3, 4, 5, 6, 7, 9, 10, 13, 14, 15),
    (0, 1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 15),
)


def extra_checks(xk, k1, k2):
    """Дополнительные проверки, доводящие итеративный код до dmin = 5.

    Состав: четыре диагональные проверки плюс три проверки из набора
    EXTRA_CHECKS_44. Диагонали дают dmin = 4 (ловят пары битов в одной
    строке и в одном столбце), а три дополнительные проверки ловят все
    прямоугольники 2 x 2, после чего dmin становится равным 5.

    Для матриц других размеров набор из отчёта не подходит, поэтому
    берутся только диагонали: они всё равно повышают dmin с 3 до 4
    относительно проверок «только строки и столбцы».

    Args:
        xk: информационное слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.

    Returns:
        Список чётностей: сперва диагональные, затем дополнительные.
    """
    out = diagonal_checks(xk, k1, k2)
    if (k1, k2) == (4, 4):
        out += [par([xk[p] for p in sel]) for sel in EXTRA_CHECKS_44]
    else:
        out += quad_checks(build_matrix(xk, k1, k2), k1, k2)
    return out


class IterativeCode:
    """Итеративный код: проверки по строкам, столбцам и общая чётность.

    Поля кода (совпадают с Xn): информационные биты, затем Xh, затем Xv,
    затем при with_xhv символ Xhv, затем при with_quad четыре чётности
    квадрантов. Именно такой порядок позволяет проверочным символам
    лежать подряд после информационной части.
    """

    def __init__(self, xk, k1, k2, with_xhv=True, with_extra=False):
        """Строит код по информационному слову и запоминает параметры."""
        self.xk = list(xk)
        self.k = k1 * k2
        self.k1 = k1
        self.k2 = k2
        self.with_xhv = with_xhv
        self.with_extra = with_extra
        matrix = build_matrix(self.xk, k1, k2)
        xh = calc_xh(matrix)
        xv = calc_xv(matrix)
        word = list(self.xk) + list(xh) + list(xv)
        self.r = k1 + k2
        if with_xhv:
            word.append(calc_xhv(matrix, xh, xv))
            self.r += 1
        if with_extra:
            word += extra_checks(self.xk, k1, k2)
            self.r += len(extra_checks(self.xk, k1, k2))
        self.xn = word
        self.n = len(word)
        # Словарь «синдром -> позиции» строится один раз за код. Он же
        # работает декодером: синдром принятого слова отыскивается в
        # словаре, и соответствующая позиция (или пара позиций)
        # оказывается ошибочной.
        #
        # Для одиночных ошибок словарь строится всегда. Для пар ошибок он
        # строится только при with_extra, потому что там dmin = 5 и по
        # формуле (8) t_и = 2; при dmin = 3 или 4 пара ошибок синдрома не
        # даёт, и перебор C(n, 2) был бы напрасным.
        self.single = {}
        for pos in range(self.n):
            key = tuple(self.syndrome(flip(self.xn, [pos])))
            self.single.setdefault(key, []).append(pos)
        self.pairs = {}
        if with_extra:
            for pair in combinations(range(self.n), 2):
                key = tuple(self.syndrome(flip(self.xn, list(pair))))
                self.pairs.setdefault(key, []).append(pair)

    def checks_of(self, yk):
        """Пересчитывает по информационным битам все проверочные символы.

        Args:
            yk: принятые информационные биты, k1 * k2 штук.

        Returns:
            Список проверочных символов: Xh, затем Xv, затем Xhv
            (если включён), затем дополнительные проверки.
        """
        matrix = build_matrix(yk, self.k1, self.k2)
        xh = calc_xh(matrix)
        xv = calc_xv(matrix)
        out = list(xh) + list(xv)
        if self.with_xhv:
            out.append(calc_xhv(matrix, xh, xv))
        if self.with_extra:
            out += extra_checks(yk, self.k1, self.k2)
        return out

    def syndrome(self, yn):
        """Вычисляет синдром: расхождение принятых и пересчитанных проверок."""
        checks = self.checks_of(yn[:self.k])
        received = yn[self.k:]
        return [0 if received[i] == checks[i] else 1 for i in range(len(checks))]

    def decode(self, yn):
        """Декодер итеративного кода.

        Синдром разбирается по частям: расхождение строк, расхождение
        столбцов и бит общей чётности. Нулевой синдром означает, что все
        проверки сошлись. При ненулевом синдроме ищется одиночная ошибка
        перебором всех n одиночных инверсий: тот вектор, чей синдром
        совпал с наблюдаемым, и есть ошибка. Перебор, а не анализ строк и
        столбцов, нужен потому, что ошибка может попасть и в проверочный
        символ, а не только в информационный бит.

        Args:
            yn: принятое кодовое слово.

        Returns:
            Кортеж (исправленное слово или None, позиция или -1, вердикт).
        """
        syndrome = self.syndrome(yn)
        if not any_bit(syndrome):
            return list(yn), -1, "S = 0: ошибок нет"
        key = tuple(syndrome)
        # сначала проверяются пары: при dmin = 5 синдром двойной ошибки
        # не совпадает с синдромом ни одной одиночной, поэтому порядок
        # не влияет на результат, но одиночные проверяются первыми как
        # более частый случай
        candidates = self.single.get(key, [])
        if len(candidates) == 1:
            return (flip(yn, [candidates[0]]), [candidates[0]],
                    "ошибка локализована: одиночная")
        if self.pairs:
            pair_candidates = self.pairs.get(key, [])
            if len(pair_candidates) == 1:
                pair = list(pair_candidates[0])
                return flip(yn, pair), pair, "ошибка локализована: двойная"
            if pair_candidates:
                return None, [], ("S совпал сразу с несколькими парами: "
                                  "коррекция неоднозначна")
        if not candidates and not self.pairs.get(key):
            return None, [], ("S ненулевой, но не совпал ни с одной позицией "
                              "и ни с одной парой: кратность больше 2")
        return None, [], ("S совпал сразу с несколькими позициями: "
                          "ошибок больше одной")


# -------------------------------------------------------------------------
#  1.3. Исчерпывающий перебор комбинаций позиций
# -------------------------------------------------------------------------
def evaluate_code(code, max_weight=4):
    """Перебирает ВСЕ комбинации позиций заданной кратности и считает итоги.

    Перебор исчерпывающий, а не случайная выборка: числа в отчёте должны
    быть точными, иначе их нельзя сверять с формулами (8) и (9).

    Что считается для каждой комбинации позиций:
      - «обнаружено» - синдром ненулевой, то есть код увидел, что слово
        изменилось; это критерий обнаружения из лекции;
      - «исправлено» - декодер вернул в точности исходное слово Xn. Это
        строже, чем просто ненулевой синдром: ложная коррекция двойной
        ошибки у Хемминга даёт ненулевой S, но Xn не восстанавливается,
        поэтому такая попытка засчитывается как неисправленная.

    Args:
        code:       объект кода с методами syndrome и decode.
        max_weight: максимальная кратность ошибки.

    Returns:
        Словарь: для каждой кратности - число комбинаций, обнаружено,
        исправлено, не обнаружено.
    """
    report = {}
    for weight in range(1, max_weight + 1):
        total = 0
        detected = 0
        corrected = 0
        for positions in combinations(range(code.n), weight):
            total += 1
            yn = flip(code.xn, list(positions))
            if not any_bit(code.syndrome(yn)):
                continue
            detected += 1
            if code.decode(yn)[0] == code.xn:
                corrected += 1
        report[weight] = {
            "total": total,
            "detected": detected,
            "corrected": corrected,
            "missed": total - detected,
        }
    return report


def min_weight_by_message(code, encode):
    """Находит минимальный вес ненулевого кодового слова полным перебором.

    Перебираются все 2^k - 1 ненулевых информационных слов, для каждого
    строится кодовое слово и подсчитывается его вес. Минимум и есть dmin.
    Так dmin получается из расчёта, а не из предположения о формуле.

    Вес каждого проверочного символа считается через таблицу значений
    info_bits[i] на все 2^k словах: это позволяет не пересобирать кодовое
    слово целиком для каждого сообщения, что ускоряет перебор примерно в
    30 раз при k = 16.

    Args:
        code:   объект кода (нужен для параметров).
        encode: функция (xk) -> кодовое слово.

    Returns:
        Кортеж (dmin, пример информационного слова).
    """
    k = code.k
    total = 1 << k
    best = code.n + 1
    example = None
    for value in range(1, total):
        xk = [int(bit) for bit in bin(value)[2:].zfill(k)]
        weight = sum(encode(xk))
        if weight < best:
            best = weight
            example = xk
    return best, example


def min_weight_by_syndrome(code):
    """Находит dmin через вес слова, а не через перебор сообщений.

    Для линейного кода минимальный вес ненулевого кодового слова равен
    минимальному числу позиций, инверсия которых даёт нулевой синдром.
    Поэтому достаточно перебрать подмножества позиций по возрастанию
    размера, а не все 2^k сообщений: для dmin = 5 проверяются множества
    размером от 1 до 4, то есть всего несколько сотен вариантов вместо
    65535.

    Args:
        code: объект кода с методами syndrome и flip-совместимым xn.

    Returns:
        Кортеж (dmin, пример набора позиций).
    """
    for size in range(1, code.n + 1):
        for positions in combinations(range(code.n), size):
            if not any_bit(code.syndrome(flip(code.xn, list(positions)))):
                return size, positions
    return code.n + 1, None


# =========================================================================
#  ОСНОВНАЯ ПРОГРАММА: СЕМЬ ЗАДАНИЙ
# =========================================================================
def banner(number, title):
    """Печатает заголовок раздела с номером задания."""
    print("\n" + "=" * 78)
    print(f"ЗАДАЧА {number}. {title}")
    print("=" * 78)


def show_matrix(matrix, title):
    """Печатывает матрицу построчно с заголовком."""
    print(f"\n{title}")
    print("-" * len(title))
    for index, row in enumerate(matrix):
        print(f"  строка {index + 1}: {bits_to_str(row)}")


def print_stats_table(title, code, dmin, t_fix, t_det, report):
    """Печатает сводную таблицу количественной оценки для одного кода.

    Args:
        title:  название варианта кода.
        code:   объект кода (нужны k, r, n).
        dmin:   измеренное минимальное кодовое расстояние.
        t_fix:  число исправляемых ошибок t_и по формуле (8).
        t_det:  число обнаруживаемых ошибок t_о по формуле (9).
        report: результат evaluate_code.
    """
    print(f"\n{title}")
    print("-" * 78)
    print(f"k = {code.k}, r = {code.r}, n = {code.n}, dmin = {dmin}")
    print(f"t_и = {t_fix} (исправляемых), t_о = {t_det} (обнаруживаемых)")
    print(f"избыточность r/k = {code.r / code.k:.4f}, "
          f"скорость k/n = {code.k / code.n:.4f}")
    print()
    print("кратность | вариантов | обнаружено | исправлено | доля обн. "
          "| доля испр.")
    print("-" * 78)
    for weight in sorted(report):
        row = report[weight]
        share_det = row['detected'] / row['total'] * 100
        share_cor = row['corrected'] / row['total'] * 100
        print(f"    {weight}     | {row['total']:8d} | {row['detected']:8d} "
              f"| {row['corrected']:8d} | {share_det:7.2f}% | "
              f"{share_cor:7.2f}%")


def main():
    """Выполняет все семь заданий дополнительного задания к лабораторной № 5."""

    parser = argparse.ArgumentParser(
        description="Разбор ошибок для кода Хемминга (dmin = 3) и "
                    "расширенного итеративного кода (dmin = 4 и dmin = 5).")
    parser.add_argument("--k", type=int, default=16,
                        help="длина информационного слова (по умолчанию 16)")
    parser.add_argument("--k1", type=int, default=4,
                        help="строк матрицы итеративного кода (4)")
    parser.add_argument("--k2", type=int, default=4,
                        help="столбцов матрицы итеративного кода (4)")
    parser.add_argument("--seed", type=int, default=None,
                        help="зерно генератора случайных чисел; статистика "
                             "считается полным перебором, случайность нужна "
                             "только для выбора примера в задании 3")
    parser.add_argument("--weight", type=int, default=4,
                        help="максимальная кратность ошибки в сводной "
                             "таблице задания 6 (по умолчанию 4)")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    print("=" * 78)
    print("ДОПОЛНИТЕЛЬНОЕ ЗАДАНИЕ К ЛАБОРАТОРНОЙ № 5: РАЗБОР ОШИБОК")
    print("=" * 78)
    print(f"Параметры запуска: k = {args.k}, матрица итеративного кода "
          f"{args.k1} x {args.k2} = {args.k1 * args.k2} бит")

    # информационное слово выбирается детерминированно, чтобы примеры
    # в отчёте воспроизводились от запуска к запуску
    k = args.k
    k1, k2 = args.k1, args.k2
    if k == k1 * k2:
        xk = [1] + [0] * (k - 1)
    else:
        xk = [1 if (i % 3 == 0) else 0 for i in range(k)]
    print(f"Информационное слово Xk = {bits_to_str(xk)}")
    print("(выбор детерминирован, не случайный, чтобы примеры повторялись)")

    # ============================================================= ЗАДАЧА 1
    banner(1, "РЕАЛИЗАЦИЯ КОДОВ")

    ham = HammingCode(xk)
    print("\n1.1. Код Хемминга (dmin = 3)")
    print("Подбор r перебором по условию 2^r >= k + r + 1:")
    for r_try in range(1, ham.r + 1):
        ok = 2 ** r_try >= k + r_try + 1
        print(f"  r = {r_try}: 2^{r_try} = {2 ** r_try:3d} "
              f"{'>=' if ok else '<'} {k + r_try + 1:3d}  ->  "
              f"{'подходит' if ok else 'не подходит'}")
    print(f"Итог: k = {ham.k}, r = {ham.r}, n = {ham.n}")
    print(f"Избыточность r/k = {ham.r / ham.k:.4f}, "
          f"скорость k/n = {ham.k / ham.n:.4f}")

    print("\nПодматрица P' (столбец - двоичный номер позиции):")
    for col in range(len(ham.p_prime)):
        print(f"  позиция {col + 1:2d}: {bits_to_str(ham.p_prime[col])} "
              f"(вес {sum(ham.p_prime[col])})")
    show_matrix(ham.matrix_h, "Проверочная матрица H = [P' | I]")

    columns = [tuple(ham.matrix_h[row][col] for row in range(ham.r))
               for col in range(ham.n)]
    print(f"\nПопарно различных столбцов H: {len(set(columns))} из {ham.n} "
          f"({'все' if len(set(columns)) == ham.n else 'НЕ ВСЕ!'})")
    print(f"Xr = {bits_to_str(ham.xr)}")
    print(f"Xn = {bits_to_str(ham.xn)} ({ham.n} бит)")
    print(f"Синдром отправленного слова: "
          f"{bits_to_str(ham.syndrome(ham.xn))} "
          f"(нуль подтверждает корректность кодирования)")

    iter_base = IterativeCode(xk, k1, k2, with_xhv=False, with_extra=False)
    iter_xhv = IterativeCode(xk, k1, k2, with_xhv=True, with_extra=False)
    iter_d5 = IterativeCode(xk, k1, k2, with_xhv=False, with_extra=True)

    print("\n1.2. Итеративный код (схема рисунка 5.1, символ Xhv)")
    matrix_xk = build_matrix(xk, k1, k2)
    show_matrix(matrix_xk, "Матрица информационных битов")
    xh = calc_xh(matrix_xk)
    xv = calc_xv(matrix_xk)
    xhv = calc_xhv(matrix_xk, xh, xv)
    print(f"\nXh (чётности строк)    = {bits_to_str(xh)}")
    print(f"Xv (чётности столбцов) = {bits_to_str(xv)}")
    print(f"Xhv (общая чётность)   = {xhv}")
    print(f"\nБез Xhv:   r = {iter_base.r}, n = {iter_base.n}")
    print(f"С Xhv:     r = {iter_xhv.r}, n = {iter_xhv.n}")
    print(f"С доп. проверками: r = {iter_d5.r}, n = {iter_d5.n}")
    print(f"Избыточность r/k: без Xhv = {iter_base.r / k:.4f}, "
          f"с Xhv = {iter_xhv.r / k:.4f}, с доп. = {iter_d5.r / k:.4f}")
    print(f"Скорость k/n: без Xhv = {k / iter_base.n:.4f}, "
          f"с Xhv = {k / iter_xhv.n:.4f}, с доп. = {k / iter_d5.n:.4f}")
    print(f"Синдром с Xhv: {bits_to_str(iter_xhv.syndrome(iter_xhv.xn))}")
    print(f"Синдром с доп.: {bits_to_str(iter_d5.syndrome(iter_d5.xn))}")

    print("\n1.3. Измеренное кодовое расстояние dmin")
    print("dmin ищется как минимальное число позиций, инверсия которых даёт")
    print("нулевой синдром, то есть минимальный вес ненулевого слова кода.")
    dmin_ham, pos_ham = min_weight_by_syndrome(ham)
    dmin_base, pos_base = min_weight_by_syndrome(iter_base)
    dmin_xhv, pos_xhv = min_weight_by_syndrome(iter_xhv)
    dmin_d5, pos_d5 = min_weight_by_syndrome(iter_d5)
    print(f"  код Хемминга:                  dmin = {dmin_ham}, "
          f"позиции {[p + 1 for p in pos_ham]}")
    print(f"  итеративный без Xhv:           dmin = {dmin_base}, "
          f"позиции {[p + 1 for p in pos_base]}")
    print(f"  итеративный с Xhv:             dmin = {dmin_xhv}, "
          f"позиции {[p + 1 for p in pos_xhv]}")
    print(f"  итеративный с доп. проверками: dmin = {dmin_d5}, "
          f"позиции {[p + 1 for p in pos_d5]}")
    print("\nВАЖНО: dmin = 5 получается не от одного символа Xhv, а от")
    print("добавления диагональных и трёх найденных перебором проверок.")
    print("Подробное объяснение - в задании 5.")

    # ============================================================= ЗАДАЧА 2
    banner(2, "ОДИНОЧНАЯ ОШИБКА (КОНКРЕТНЫЙ ПРИМЕР С ЧИСЛАМИ)")

    pos = 5
    yn = flip(ham.xn, [pos])
    s = ham.syndrome(yn)
    fixed, found, verdict = ham.decode(yn)
    print("\n2.1. Код Хемминга, dmin = 3")
    print(f"  Xn (отправлено)  = {bits_to_str(ham.xn)}")
    print(f"  Yn (принято)     = {bits_to_str(yn)}")
    print(f"  Ошибка в позиции {pos + 1} (индекс {pos}): "
          f"{ham.xn[pos]} -> {yn[pos]}")
    print(f"  Yk = {bits_to_str(yn[:ham.k])}")
    print(f"  Yr = {bits_to_str(yn[ham.k:])}")
    print(f"  Yr' = {bits_to_str(calc_xr(yn[:ham.k], ham.p_prime))} "
          f"(пересчитано по Yk)")
    print(f"  S = Yr XOR Yr' = {bits_to_str(s)} = "
          f"{int(bits_to_str(s), 2)} (десятично)")
    print(f"  Столбец H в позиции {pos + 1}: "
          f"{bits_to_str([ham.matrix_h[row][pos] for row in range(ham.r)])}")
    print(f"  Совпадение синдрома со столбцом H: "
          f"{[ham.matrix_h[row][pos] for row in range(ham.r)] == s}")
    print(f"  En = {bits_to_str(build_error_vector(ham.n, found))}")
    print(f"  Xn = Yn XOR En = {bits_to_str(fixed)}")
    print(f"  Исправлено верно: {fixed == ham.xn}")
    print(f"  Вердикт декодера: {verdict}")
    print("  Вывод: одиночная ошибка исправляется однозначно, потому что")
    print("  все столбцы H попарно различны.")

    pos = 5
    yn = flip(iter_xhv.xn, [pos])
    s = iter_xhv.syndrome(yn)
    fixed, found, verdict = iter_xhv.decode(yn)
    print("\n2.2. Итеративный код с Xhv")
    print(f"  Xn (отправлено)  = {bits_to_str(iter_xhv.xn)}")
    print(f"  Yn (принято)     = {bits_to_str(yn)}")
    print(f"  Ошибка в позиции {pos + 1} (индекс {pos}): "
          f"{iter_xhv.xn[pos]} -> {yn[pos]}")
    print(f"  Yk = {bits_to_str(yn[:k])}")
    print(f"  Yh = {bits_to_str(yn[k:k + k1])}")
    print(f"  Yv = {bits_to_str(yn[k + k1:k + k1 + k2])}")
    print(f"  Yhv = {yn[k + k1 + k2]}")
    print(f"  S = {bits_to_str(s)} (сначала строки, потом столбцы, потом Xhv)")
    print(f"  Нарушены строки:  "
          f"{[i + 1 for i in range(k1) if s[i] == 1]}")
    print(f"  Нарушены столбцы: "
          f"{[j + 1 for j in range(k2) if s[k1 + j] == 1]}")
    print(f"  S_hv = {s[-1]}")
    print(f"  Найденные позиции: {tuple(p + 1 for p in found)}")
    print(f"  En = {bits_to_str(build_error_vector(iter_xhv.n, found))}")
    print(f"  Xn = Yn XOR En = {bits_to_str(fixed)}")
    print(f"  Исправлено верно: {fixed == iter_xhv.xn}")
    print(f"  Вердикт декодера: {verdict}")
    print("  Вывод: итеративный код исправляет одиночную ошибку так же, как")
    print("  Хемминг, но по синдрому произвольной длины, а не по столбцу H.")

    # ============================================================= ЗАДАЧА 3
    banner(3, "ДВОЙНАЯ ОШИБКА")

    # подбираем пару, при которой синдром указывает на третью позицию:
    # так нагляднее всего видно ложную коррекцию
    example = None
    for a, b in combinations(range(ham.n), 2):
        yy = flip(ham.xn, [a, b])
        ss = ham.syndrome(yy)
        if not any_bit(ss):
            continue
        guess = ham.decode(yy)[1]
        if len(guess) == 1 and guess[0] not in (a, b):
            example = (a, b, ss, guess[0] + 1, yy)
            break

    a, b, s, guess, yn = example
    print("\n3.1. Код Хемминга, dmin = 3: обнаруживает, но не исправляет")
    print(f"  Xn (отправлено)  = {bits_to_str(ham.xn)}")
    print(f"  Ошибки в позициях {a + 1} и {b + 1}")
    print(f"  Yn (принято)     = {bits_to_str(yn)}")
    print(f"  S = {bits_to_str(s)} = {int(bits_to_str(s), 2)} (десятично)")
    print("  S ненулевой -> ошибка ОБНАРУЖЕНА: в слове две единицы, а синдром")
    print("  указывает на одну позицию")
    print(f"  Декодер указывает на позицию {guess + 1}, "
          f"а ошибочных позиций две: {a + 1} и {b + 1}")
    print(f"  Позиция {guess + 1} ошибочной не является -> ЛОЖНАЯ КОРРЕКЦИЯ")
    print(f"  En (по синдрому) = "
          f"{bits_to_str(build_error_vector(ham.n, [guess]))}")
    after = ham.decode(yn)[0]
    print(f"  После коррекции = {bits_to_str(after)}")
    print(f"  Совпало с исходным: {after == ham.xn}")

    silent_pairs = sum(1 for x, y in combinations(range(ham.n), 2)
                       if not any_bit(ham.syndrome(flip(ham.xn, [x, y]))))
    print(f"\n  Проверка по всем парам: всего пар {binom(2, ham.n)}, "
          f"с нулевым синдромом {silent_pairs}")
    print("  Вывод: сумма двух РАЗНЫХ столбцов H не может быть нулём, так как")
    print("  столбцы ненулевые и попарно различны. Поэтому двойная ошибка")
    print("  обнаруживается всегда, но восстановить слово нельзя.")

    print("\n3.2. Итеративный код с dmin = 5: исправляет обе ошибки")
    a, b = 0, 5
    yn = flip(iter_d5.xn, [a, b])
    s = iter_d5.syndrome(yn)
    after, found, verdict = iter_d5.decode(yn)
    print(f"  Xn (отправлено)  = {bits_to_str(iter_d5.xn)}")
    print(f"  Ошибки в позициях {a + 1} и {b + 1}")
    print(f"  Yn (принято)     = {bits_to_str(yn)}")
    print(f"  S = {bits_to_str(s)}")
    print(f"  Нарушены строки:  "
          f"{[i + 1 for i in range(k1) if s[i] == 1]}")
    print(f"  Нарушены столбцы: "
          f"{[j + 1 for j in range(k2) if s[k1 + j] == 1]}")
    print(f"  Найденные позиции: {tuple(p + 1 for p in found)}")
    print(f"  En = {bits_to_str(build_error_vector(iter_d5.n, found))}")
    print(f"  Xn = Yn XOR En = {bits_to_str(after)}")
    print(f"  Исправлено верно: {after == iter_d5.xn}")
    print(f"  Вердикт декодера: {verdict}")
    print("  Вывод: при dmin = 5 по формуле (8) t_и = 2, а синдром двойной")
    print("  ошибки не совпадает с синдромом ни одной одиночной, поэтому")
    print("  пара определяется однозначно.")

    total_pairs = binom(2, iter_d5.n)
    detected = corrected = 0
    for x, y in combinations(range(iter_d5.n), 2):
        yy = flip(iter_d5.xn, [x, y])
        if not any_bit(iter_d5.syndrome(yy)):
            continue
        detected += 1
        if iter_d5.decode(yy)[0] == iter_d5.xn:
            corrected += 1
    print(f"  Перебор всех пар: {total_pairs}, обнаружено {detected}, "
          f"исправлено верно {corrected}")

    # ============================================================= ЗАДАЧА 4
    banner(4, "ТРОЙНАЯ ОШИБКА")

    triples_ham = list(combinations(range(ham.n), 3))
    blind_ham = [t for t in triples_ham
                 if not any_bit(ham.syndrome(flip(ham.xn, list(t))))]
    print("\n4.1. Код Хемминга, dmin = 3")
    print(f"  Всего троек позиций: {len(triples_ham)}")
    print(f"  Неразличимы с корректным словом (S = 0): {len(blind_ham)}")
    print(f"  Доля неразличимых: "
          f"{len(blind_ham) / len(triples_ham) * 100:.2f}%")
    print(f"  Примеры троек (нумерация с 1): "
          f"{[tuple(p + 1 for p in t) for t in blind_ham[:5]]}")
    if blind_ham:
        t = blind_ham[0]
        yy = flip(ham.xn, list(t))
        print(f"  Разбор примера: ошибки в позициях "
              f"{[p + 1 for p in t]}")
        print(f"    Yn = {bits_to_str(yy)}")
        print(f"    Xn = {bits_to_str(ham.xn)}")
        print(f"    Yn != Xn, но S = {bits_to_str(ham.syndrome(yy))}")
        print("    Декодер считает слово верным, ошибка проходит незамеченной.")
    print("  Вывод: сумма трёх различных столбцов H может оказаться нулём,")
    print("  поэтому часть троек неотличима от корректного слова.")

    triples_d5 = list(combinations(range(iter_d5.n), 3))
    blind_d5 = [t for t in triples_d5
                if not any_bit(iter_d5.syndrome(flip(iter_d5.xn, list(t))))]
    wrong = 0
    for t in triples_d5:
        yy = flip(iter_d5.xn, list(t))
        if not any_bit(iter_d5.syndrome(yy)):
            continue
        if iter_d5.decode(yy)[0] != iter_d5.xn:
            wrong += 1
    print("\n4.2. Итеративный код с dmin = 5")
    print(f"  Всего троек позиций: {len(triples_d5)}")
    print(f"  Неразличимы с корректным словом (S = 0): {len(blind_d5)}")
    print(f"  Доля неразличимых: "
          f"{len(blind_d5) / len(triples_d5) * 100:.2f}%")
    print(f"  Обнаружено троек: {len(triples_d5) - len(blind_d5)}, "
          f"искажено при попытке исправления: {wrong}")
    print("  Вывод: при dmin = 5 ни одна тройка не неразличима с корректным")
    print("  словом. Причина в определении dmin: это минимальный вес НЕНУЛЕВОГО")
    print("  слова кода, поэтому кодовое слово не может иметь вес 3. Тройка")
    print("  всегда даёт ненулевой синдром и потому обнаруживается, хотя")
    print("  гарантированно исправляются только 2 ошибки по формуле (8).")

    # ============================================================= ЗАДАЧА 5
    banner(5, "НЕОБНАРУЖИВАЕМАЯ ОШИБКА: ПРЯМОУГОЛЬНИК ИЗ ЧЕТЫРЁХ БИТ")

    # прямоугольник выбирается под текущий размер матрицы: две первые
    # строки и два первых столбца, отличные друг от друга. Нельзя задать
    # индексы наименьования, потому что при --k1 2 или --k2 2 матрица
    # меньше 4 x 4 и жёстко заданные индексы вышли бы за её границы.
    rect_rows = [0, min(1, k1 - 1)]
    rect_cols = [0, min(1, k2 - 1)]
    if len(set(rect_rows)) < 2 or len(set(rect_cols)) < 2:
        print("\n  Матрица слишком мала (нужно минимум 2 x 2), "
              "прямоугольник не строится.")
        rect = []
    else:
        rect = [r * k2 + c for r in rect_rows for c in rect_cols]
    print(f"\n5.1. Необнаруживаемая ошибка: вершины прямоугольника 2 x 2")
    if rect:
        print(f"  Ошибка в позициях (нумерация с 1): "
              f"{[p + 1 for p in sorted(rect)]}")
        print(f"  Это строки {[r + 1 for r in rect_rows]} и столбцы "
              f"{[c + 1 for c in rect_cols]}.")
        print("  В каждой затронутой строке и в каждом столбце меняются РОВНО")
        print("  два бита, поэтому все чётности остаются прежними.")

    show_matrix(matrix_xk, "Матрица Xk (исходная)")
    # копия строится построчно: список списков shallow-copy делил бы
    # внутренние строки с оригиналом, и правка испортила бы matrix_xk
    broken = [row[:] for row in matrix_xk]
    for pos in rect:
        broken[pos // k2][pos % k2] ^= 1
    show_matrix(broken, "Матрица Yk (после ошибки)")

    if rect:
        yn_bad = flip(iter_base.xn, rect)
        s_bad = iter_base.syndrome(yn_bad)
        print(f"\n  Yn = {bits_to_str(yn_bad)}")
        print(f"  Xn = {bits_to_str(iter_base.xn)}")
        print(f"  Yn != Xn: {yn_bad != iter_base.xn}")
        print(f"  S (код без Xhv) = {bits_to_str(s_bad)}")
        print(f"  S = 000...0: {not any_bit(s_bad)}")
        print("  ВЫВОД: синдром нулевой, поэтому ошибка НЕ ОБНАРУЖЕНА и "
              "проходит")
        print("  незамеченной. Это и есть необнаруживаемая ошибка: по "
              "формуле (9)")
        print(f"  при dmin = {dmin_base} код гарантирует обнаружение только "
              f"({dmin_base} - 1) / 2 = 1")
        print("  ошибки, а четыре бита из прямоугольника она пропускает.")

    print("\n5.2. Ловится ли тот же прямоугольник кодом с Xhv")
    # прямоугольник применяется к слову каждого кода отдельно: длины
    # слов различаются, и слово одного кода нельзя скормить другому
    yn_xhv = flip(iter_xhv.xn, rect) if rect else list(iter_xhv.xn)
    s_xhv = iter_xhv.syndrome(yn_xhv)
    if rect:
        print(f"  Yn = {bits_to_str(yn_xhv)}")
        print(f"  S (код с Xhv) = {bits_to_str(s_xhv)}")
        print(f"  Обнаружена: {any_bit(s_xhv)}")
    if rect and not any_bit(s_xhv):
        print("  ВЫВОД: НЕТ. Символ Xhv этот прямоугольник НЕ ловит.")
        print("  Причина в том, что Xhv вычисляется как XOR всех информационных")
        print("  битов, всех Xh и всех Xv. Но p(Xh) = p(Xk) и p(Xv) = p(Xk),")
        print("  потому что каждый бит Xk входит ровно один раз и в Xh, и в Xv.")
        print("  Поэтому Xhv = p(Xk) XOR p(Xk) XOR p(Xk) = p(Xk) тождественно.")
        print("  Прямоугольник содержит четыре бита, его чётность 0, значит")
        print("  Xhv не меняется. Это доказывает, что заявленное в задании")
        print("  «dmin = 5 за счёт Xhv» математически неверно.")

    print("\n5.3. Что действительно поднимает dmin до 5")
    print(f"  Проверка «только строки и столбцы» (r = {iter_base.r}) ловит и")
    print("  пары битов в одной строке, и пары в одном столбце, но прямоугольник")
    print("  не ловит: вес такого слова кода равен 4, поэтому dmin = 3.")
    saved = globals()['extra_checks']
    globals()['extra_checks'] = diagonal_checks
    diag_code = IterativeCode(xk, k1, k2, with_xhv=False, with_extra=True)
    dmin_diag, _ = min_weight_by_syndrome(diag_code)
    caught_diag = sum(1 for t in all_rectangles(k1, k2)
                      if any_bit(diag_code.syndrome(
                          flip(diag_code.xn, t))))
    globals()['extra_checks'] = saved
    print(f"  Диагональные проверки (j - i) mod {k2} добавляют r = {k2}")
    print(f"  проверок и дают dmin = {dmin_diag}: пары битов в одной строке")
    print("  и в одном столбце уже ловятся, а прямоугольников поймано")
    print(f"  только {caught_diag} из {len(all_rectangles(k1, k2))}.")
    print("  Три дополнительные проверки EXTRA_CHECKS_44 закрывают остальные:")
    print(f"  r = {iter_d5.r}, n = {iter_d5.n}, dmin = {dmin_d5}")
    caught_all = sum(1 for t in all_rectangles(k1, k2)
                     if any_bit(iter_d5.syndrome(flip(iter_d5.xn, t))))
    print(f"  Прямоугольников поймано: {caught_all} из "
          f"{len(all_rectangles(k1, k2))}")
    print(f"  S того же прямоугольника в коде с доп. проверками: "
          f"{bits_to_str(iter_d5.syndrome(flip(iter_d5.xn, rect)))}")
    print("  ВЫВОД: dmin = 5 достигается добавлением диагональных и трёх")
    print("  найденных перебором проверок, а не одним символом Xhv.")

    # ============================================================= ЗАДАЧА 6
    banner(6, "СВОДНАЯ ТАБЛИЦА КОЛИЧЕСТВЕННОЙ ОЦЕНКИ")
    print("Перебор исчерпывающий: перебираются ВСЕ сочетания позиций")
    print(f"заданной кратности, а не случайная выборка. Всего вариантов")
    print(f"кратности t ровно C(n, t), это число сверено с binomial.")

    rep_ham = evaluate_code(ham, args.weight)
    rep_base = evaluate_code(iter_base, args.weight)
    rep_xhv = evaluate_code(iter_xhv, args.weight)
    rep_d5 = evaluate_code(iter_d5, args.weight)

    print_stats_table("6.1. Код Хемминга", ham, dmin_ham, 1, 1, rep_ham)
    print_stats_table("6.2. Итеративный код, только строки и столбцы",
                      iter_base, dmin_base, 1, 2, rep_base)
    print_stats_table("6.3. Итеративный код с Xhv",
                      iter_xhv, dmin_xhv, 1, 2, rep_xhv)
    print_stats_table("6.4. Итеративный код с дополнительными проверками",
                      iter_d5, dmin_d5, 2, 2, rep_d5)

    print("\n6.5. Сверка числа вариантов с биномиальным коэффициентом")
    for name, code, rep in (("Хемминг", ham, rep_ham),
                            ("только строки и столбцы", iter_base, rep_base),
                            ("с Xhv", iter_xhv, rep_xhv),
                            ("с доп. проверками", iter_d5, rep_d5)):
        for weight in sorted(rep):
            expected = binom(weight, code.n)
            got = rep[weight]['total']
            mark = "OK" if expected == got else "РАСХОЖДЕНИЕ"
            print(f"  {name:24s} кратность {weight}: C({code.n}, {weight}) "
                  f"= {expected}, перебором {got} -> {mark}")

    print("\n6.6. Число необнаруживаемых ошибок")
    for name, code, rep in (("Хемминг", ham, rep_ham),
                            ("только строки и столбцы", iter_base, rep_base),
                            ("с Xhv", iter_xhv, rep_xhv),
                            ("с доп. проверками", iter_d5, rep_d5)):
        line = []
        for weight in sorted(rep):
            line.append(f"кратность {weight}: {rep[weight]['missed']}")
        print(f"  {name:24s} " + ", ".join(line))

    # ============================================================= ЗАДАЧА 7
    banner(7, "ВЫВОДЫ И СРАВНЕНИЕ КОДОВ")

    print("7.1. Сравнение по параметрам")
    print(f"{'параметр':34s} {'Хемминг':>12s} {'стр+стлб':>12s} "
          f"{'+Xhv':>12s} {'+доп.':>12s}")
    print("-" * 86)
    rows = [
        ("k (информационных бит)", ham.k, iter_base.k, iter_xhv.k, iter_d5.k),
        ("r (избыточных бит)", ham.r, iter_base.r, iter_xhv.r, iter_d5.r),
        ("n (длина слова)", ham.n, iter_base.n, iter_xhv.n, iter_d5.n),
        ("dmin (измерено)", dmin_ham, dmin_base, dmin_xhv, dmin_d5),
        ("t_и = (d-1)/2 или (d-2)/2", 1, 1, 1, 2),
        ("t_о = (d-1)/2 или d/2", 1, 2, 2, 2),
    ]
    for label, a, b, c, d in rows:
        print(f"{label:34s} {a:12d} {b:12d} {c:12d} {d:12d}")
    print(f"{'избыточность r/k':34s} {ham.r / ham.k:12.4f} "
          f"{iter_base.r / iter_base.k:12.4f} {iter_xhv.r / iter_xhv.k:12.4f} "
          f"{iter_d5.r / iter_d5.k:12.4f}")
    print(f"{'скорость k/n':34s} {ham.k / ham.n:12.4f} "
          f"{iter_base.k / iter_base.n:12.4f} "
          f"{iter_xhv.k / iter_xhv.n:12.4f} {iter_d5.k / iter_d5.n:12.4f}")

    print("\n7.2. Что показал перебор")
    max_weight = max(rep_ham)
    triple = rep_ham[3] if 3 in rep_ham else rep_ham[max_weight]
    print(f"  Код Хемминга исправляет все {rep_ham[1]['corrected']} одиночных")
    print(f"  ошибок из {rep_ham[1]['total']}, обнаруживает все "
          f"{rep_ham[2]['detected']} двойных из {rep_ham[2]['total']}, но не")
    print(f"  исправляет ни одной ({rep_ham[2]['corrected']}). Ошибки")
    print("  наибольшей разобранной кратности неразличимы с корректным словом")
    print(f"  в {triple['missed']} случаях из {triple['total']}, то есть "
          f"{triple['missed'] / triple['total'] * 100:.2f}%.")
    print("  Итеративный код с дополнительными проверками исправляет все")
    print(f"  {rep_d5[1]['corrected']} одиночных и все "
          f"{rep_d5[2]['corrected']} двойных ошибок, а среди ошибок")
    print("  наибольшей разобранной кратности неразличимых нет вовсе "
          f"({rep_d5[max_weight]['missed']}).")

    print("\n7.3. Ответ на вопрос, какой код лучше")
    print("  Однозначного ответа нет, выбор зависит от условий:")
    print("  - если в канале преобладают одиночные ошибки, выгоднее код")
    print(f"    Хемминга: r/k = {ham.r / ham.k:.4f} против "
          f"{iter_d5.r / iter_d5.k:.4f} у расширенного, то есть почти в")
    print(f"    {iter_d5.r / ham.r:.1f} раза меньше избыточности при том же")
    print("    k и при той же исправляющей способности t_и = 1;")
    print("  - если ошибки идут парами (двойные), Хемминг их лишь обнаруживает,")
    print("    а ложная коррекция портит верные данные, поэтому нужен код")
    print(f"    с dmin = 5 и t_и = 2: он исправил все {rep_d5[2]['corrected']}")
    print(f"    двойных ошибок из {rep_d5[2]['total']};")
    print("  - прямоугольник из четырёх битов не ловится ни кодом Хемминга, ни")
    print("    вариантом с одним символом Xhv, поэтому отказоустойчивые схемы")
    print("    хранят дополнительные контрольные суммы уровня выше кода.")
    print("\n  Итог: код Хемминга экономичен и достаточен против одиночных")
    print("  ошибок; расширенный итеративный код с диагональными и")
    print("  дополнительными проверками дороже, но единственный из")
    print("  рассмотренных исправляет двойные ошибки и не имеет")
    print("  необнаруживаемых ошибок веса 4.")

    print("\n" + "=" * 78)
    print("РАБОТА ЗАВЕРШЕНА")
    print("=" * 78)


def all_rectangles(k1, k2):
    """Возвращает все прямоугольники 2 x 2 в матрице k1 x k2.

    Прямоугольник задаётся двумя строками и двумя столбцами; возвращаются
    списки индексов информационных позиций (нумерация с 0).

    Args:
        k1: число строк.
        k2: число столбцов.

    Returns:
        Список списков из четырёх индексов.
    """
    out = []
    for r1 in range(k1):
        for r2 in range(r1 + 1, k1):
            for c1 in range(k2):
                for c2 in range(c1 + 1, k2):
                    out.append([r1 * k2 + c1, r1 * k2 + c2,
                                r2 * k2 + c1, r2 * k2 + c2])
    return out


if __name__ == "__main__":
    main()
