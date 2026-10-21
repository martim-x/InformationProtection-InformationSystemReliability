#!/usr/bin/env python3
"""
Лабораторная работа № 5: Избыточное кодирование данных в информационных
системах. Итеративные коды (код произведения, прямоугольный код).

Идея кода: информационные биты раскладываются в матрицу k1 на k2, после чего
считаются проверочные символы:
  Xh  - контрольные биты по строкам (по одному на строку, всего k1);
  Xv  - контрольные биты по столбцам (по одному на столбец, всего k2);
  Xhv - бит общей четности (паритет паритетов), один.
Отсюда r = k1 + k2 + 1 при трех группах паритетов и r = k1 + k2 при двух.

Практическое задание (пункты 1-6):
  1. Записать информационное слово Xk в матрицу k1 на k2.
  2. Вычислить проверочные биты по двум и по трем направлениям.
  3. Собрать кодовое слово Xn = Xk + Xh + Xv + Xhv.
  4. Внести ошибку кратности i > 0 в случайные символы Xn, получив Yn.
  5. Найти ошибочные символы по группам паритетов и получить исправленное
     слово Yn'.
  6. Оценить количественно корректирующую способность: отношение числа слов,
     в которых кратность определена верно (N2) и в которых все ошибки
     исправлены (N3), к общему числу слов с ошибками (N1).

Значения по умолчанию соответствуют варианту 1 таблицы 5.2:
k = 16, матрица 4 на 4, три группы паритетов.
"""

import argparse
import random
import sys


# --------------------------------------------------------------------------
# Формирование паритетов
# --------------------------------------------------------------------------
def build_matrix(xk: str, k1: int, k2: int) -> list:
    """
    Раскладывает информационное слово Xk в матрицу k1 на k2 построчно.

    Args:
        xk: информационное слово (строка из '0' и '1').
        k1: число строк матрицы.
        k2: число столбцов матрицы.

    Returns:
        Матрица - список списков, элементы равны 0 или 1.
    """
    return [[int(xk[i * k2 + j]) for j in range(k2)] for i in range(k1)]


def calc_xh(matrix: list) -> str:
    """
    Считает контрольные биты по строкам (Xh): контрольный бит строки равен
    сумме её информационных битов по модулю 2. Такой бит позволяет найти
    ошибочную строку, но не ошибочный бит внутри неё.

    Args:
        matrix: матрица информационных битов.

    Returns:
        Строка из k1 контрольных битов по строкам.
    """
    xh = []
    for row in matrix:
        xh.append(sum(row) % 2)
    return ''.join(str(bit) for bit in xh)


def calc_xv(matrix: list) -> str:
    """
    Считает контрольные биты по столбцам (Xv): контрольный бит столбца равен
    сумме его информационных битов по модулю 2. Вместе с Xh он однозначно
    указывает на ошибочный бит при одиночной ошибке в данных.

    Args:
        matrix: матрица информационных битов.

    Returns:
        Строка из k2 контрольных битов по столбцам.
    """
    k1 = len(matrix)
    k2 = len(matrix[0])
    xv = []
    for j in range(k2):
        col_sum = 0
        for i in range(k1):
            col_sum = col_sum + matrix[i][j]
        xv.append(col_sum % 2)
    return ''.join(str(bit) for bit in xv)


def calc_xhv(xk: str, xh: str, xv: str) -> str:
    """
    Считает бит общей четности Xhv как сумму по модулю 2 всех информационных
    битов и всех паритетов Xh и Xv. Нужен, чтобы отличать ошибочный бит данных
    от ошибочного бита паритета.

    Args:
        xk: информационное слово.
        xh: контрольные биты по строкам.
        xv: контрольные биты по столбцам.

    Returns:
        Один символ '0' или '1'.
    """
    total = 0
    for symbol in xk:
        total = total ^ int(symbol)
    for symbol in xh:
        total = total ^ int(symbol)
    for symbol in xv:
        total = total ^ int(symbol)
    return str(total)


def build_codeword(xk: str, xh: str, xv: str, xhv: str) -> str:
    """
    Собирает кодовое слово: к информационному слову присоединяются паритеты
    в порядке «сверху вниз» (Xh), «справа налево» (Xv) и общая четность (Xhv).

    Args:
        xk: информационное слово.
        xh: контрольные биты по строкам.
        xv: контрольные биты по столбцам.
        xhv: бит общей четности ('' если он не используется).

    Returns:
        Кодовое слово Xn.
    """
    return xk + xh + xv + xhv


def split_received(yn: str, k1: int, k2: int, n_groups: int) -> tuple:
    """
    Разделяет принятое слово на информационную часть и принятые паритеты:
    Yh, Yv, Yhv нужны декодеру для сравнения с пересчитанными значениями.

    Args:
        yn: принятое слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).

    Returns:
        Кортеж (yk, yh, yv, yhv), где yhv равен '' при двух группах.
    """
    k = k1 * k2
    yk = yn[:k]
    yh = yn[k:k + k1]
    yv = yn[k + k1:k + k1 + k2]
    if n_groups == 3:
        yhv = yn[k + k1 + k2]
    else:
        yhv = ''
    return yk, yh, yv, yhv


# --------------------------------------------------------------------------
# Пункт 4. Внесение ошибок в кодовое слово
# --------------------------------------------------------------------------
def inject_errors(xn: str, weight: int, rng: random.Random) -> tuple:
    """
    Инвертирует кратность случайно выбранных символов кодового слова.
    Ошибки распределяются по всем символам слова (данные и паритеты) равновероятно.

    Args:
        xn: исходное кодовое слово.
        weight: число вносимых ошибок i > 0.
        rng: генератор случайных чисел (для воспроизводимости).

    Returns:
        Кортеж (yn, позиции), где позиции отсортированы по возрастанию,
        нумерация - с 1, как принято в тексте практикума.
    """
    n = len(xn)
    positions = sorted(rng.sample(range(n), weight))
    yn = list(xn)
    for position in positions:
        yn[position] = '1' if yn[position] == '0' else '0'
    return ''.join(yn), [position + 1 for position in positions]


# --------------------------------------------------------------------------
# Пункт 5. Декодирование: синдром и исправление
# --------------------------------------------------------------------------
def calc_syndrome(yn: str, k1: int, k2: int, n_groups: int) -> tuple:
    """
    Пересчитывает паритеты принятого слова по его информационной части и
    сравнивает их с принятыми. Ненулевое расхождение означает наличие ошибки.

    Args:
        yn: принятое слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).

    Returns:
        Кортеж (S, yk, yh, yv, yhv, yh_prime, yv_prime,
        yhv_prime). Синдром S - строка из k1 + k2 + (n_groups - 2) символов;
        при двух группах это k1 + k2 символов.
    """
    yk, yh, yv, yhv = split_received(yn, k1, k2, n_groups)
    matrix = build_matrix(yk, k1, k2)
    yh_prime = calc_xh(matrix)
    yv_prime = calc_xv(matrix)
    syndrome = ''
    for received, recomputed in zip(yh, yh_prime):
        syndrome = syndrome + str(int(received) ^ int(recomputed))
    for received, recomputed in zip(yv, yv_prime):
        syndrome = syndrome + str(int(received) ^ int(recomputed))
    yhv_prime = ''
    if n_groups == 3:
        yhv_prime = calc_xhv(yk, yh_prime, yv_prime)
        syndrome = syndrome + str(int(yhv) ^ int(yhv_prime))
    return (syndrome, yk, yh, yv, yhv, yh_prime, yv_prime,
            yhv_prime)


def build_syndrome_table(k1: int, k2: int, n_groups: int) -> dict:
    """
    Заранее вычисляет синдром одиночной ошибки в каждом символе слова и
    связывает его с номером этого символа.

    Код линеен, поэтому синдром не зависит от того, какое именно слово принято:
    достаточно инвертировать символ в слове из одних нулей. Декодер затем
    выбирает вариант минимального веса - так исправляется любая одиночная
    ошибка, а неоднозначные синдромы остаются неисправленными.

    Args:
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).

    Returns:
        Словарь: синдром -> номер символа (нумерация с 1).
    """
    n = k1 * k2 + k1 + k2 + (n_groups - 2)
    zeros = '0' * n
    table = {}
    for position in range(n):
        word = list(zeros)
        word[position] = '1'
        syndrome = calc_syndrome(''.join(word), k1, k2, n_groups)[0]
        table[syndrome] = position + 1
    return table


def decode(yn: str, xn: str, k1: int, k2: int, n_groups: int,
           table: dict) -> tuple:
    """
    Определяет наличие ошибок и исправляет одиночную.

    Нулевой синдром означает, что расхождений нет; при этом ошибка может быть
    и есть, но она необнаруживаема. Ненулевой синдром, присутствующий в таблице
    одиночных ошибок, исправляется инверсией указанного символа. Остальные
    (более тяжелые) синдромы только обнаруживаются: восстановить исходное слово
    по ним невозможно, так как им соответствуют несколько вариантов ошибок.

    Args:
        yn: принятое слово.
        xn: исходное кодовое слово (нужно только для проверки результата).
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).
        table: таблица синдромов одиночных ошибок.

    Returns:
        Кортеж (S, yn_fixed, detected, positions, correct).
    """
    syndrome = calc_syndrome(yn, k1, k2, n_groups)[0]
    positions = []
    if set(syndrome) != {'0'}:
        detected = True
        if syndrome in table:
            positions = [table[syndrome]]
    else:
        detected = False
    yn_fixed = list(yn)
    for position in positions:
        yn_fixed[position - 1] = '1' if yn_fixed[position - 1] == '0' else '0'
    yn_fixed = ''.join(yn_fixed)
    return syndrome, yn_fixed, detected, positions, yn_fixed == xn


def describe_position(position: int, k1: int, k2: int) -> str:
    """
    Даёт символическое имя символа кодового слова по его номеру: бит данных с
    координатами (строка, столбец), один из паритетов или бит общей четности.

    Args:
        position: номер символа в слове, нумерация с 1.
        k1: число строк матрицы.
        k2: число столбцов матрицы.

    Returns:
        Текстовое описание символа.
    """
    k = k1 * k2
    if position <= k:
        row = (position - 1) // k2 + 1
        col = (position - 1) % k2 + 1
        return "бит данных Xk[%d][%d]" % (row, col)
    if position <= k + k1:
        return "паритет Xh[%d]" % (position - k)
    if position <= k + k1 + k2:
        return "паритет Xv[%d]" % (position - k - k1)
    return "паритет Xhv"


# --------------------------------------------------------------------------
# Пункт 6. Измерение корректирующей способности
# --------------------------------------------------------------------------
def measure_dmin(k1: int, k2: int, n_groups: int) -> int:
    """
    Определяет минимальное кодовое расстояние dmin перебором всех
    информационных слов: dmin равно наименьшему весу ненулевого кодового слова.

    Перебор всех 2^k слов возможен только при небольшом k, поэтому при больших
    матрицах возвращается -1, а в отчете печатается значение по конструкции.

    Args:
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).

    Returns:
        Измеренное значение dmin либо -1, если перебор слишком велик.
    """
    k = k1 * k2
    if k > 20:
        return -1
    # Начальное значение берём с запасом: длина любого кодового слова равна n.
    best = k + k1 + k2 + 1
    for value in range(1, 1 << k):
        xk = format(value, '0{}b'.format(k))
        matrix = build_matrix(xk, k1, k2)
        xh = calc_xh(matrix)
        xv = calc_xv(matrix)
        xn_full = xk + xh + xv
        if n_groups == 3:
            xn_full = xn_full + calc_xhv(xk, xh, xv)
        weight = xn_full.count('1')
        if weight < best:
            best = weight
    return best


def run_analysis(xn: str, k1: int, k2: int, n_groups: int,
                 weights: list, trials: int,
                 rng: random.Random) -> dict:
    """
    Моделирует ошибки заданной кратности и считает три доли:
    N2 / N1 - доля случаев, в которых кратность ошибки определена верно,
    N3 / N1 - доля случаев, в которых все ошибки исправлены и Yn' равно Xn,
    доля случаев с ненулевым синдромом (простота обнаружения).

    Args:
        xn: исходное кодовое слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        n_groups: число групп паритетов (2 или 3).
        weights: список кратностей ошибок.
        trials: число слов с ошибками для каждой кратности.
        rng: генератор случайных чисел.

    Returns:
        Словарь: кратность -> (N1, N2, N3, обнаружено).
    """
    table = build_syndrome_table(k1, k2, n_groups)
    results = {}
    for weight in weights:
        n1 = 0
        n2 = 0
        n3 = 0
        detected_count = 0
        for _ in range(trials):
            yn = inject_errors(xn, weight, rng)[0]
            syndrome, yn_fixed, detected, positions, correct = decode(
                yn, xn, k1, k2, n_groups, table)
            n1 = n1 + 1
            if detected:
                detected_count = detected_count + 1
                # Кратность определена верно, если декодер нашел ошибку и
                # указал столько символов, сколько их было на самом деле.
                if len(positions) == weight:
                    n2 = n2 + 1
            if correct:
                n3 = n3 + 1
        results[weight] = (n1, n2, n3, detected_count)
    return results


def percent(numerator: int, denominator: int) -> float:
    """Возвращает отношение двух чисел в процентах."""
    if denominator == 0:
        return 0.0
    return 100.0 * numerator / denominator


# --------------------------------------------------------------------------
# Вывод на экран
# --------------------------------------------------------------------------
def show_matrix(matrix: list) -> None:
    """
    Печатает матрицу информационных битов с нумерацией строк и столбцов,
    чтобы было видно, в какой строке и в каком столбце находится ошибочный бит.
    """
    k2 = len(matrix[0])
    header = "     " + " ".join("%3d" % (j + 1) for j in range(k2))
    print(header + "   <- номера столбцов")
    for i, row in enumerate(matrix):
        line = " ".join("%3d" % bit for bit in row)
        print("%3d  %s   <- строка %d" % (i + 1, line, i + 1))


def show_parameters(k1: int, k2: int, n_groups: int, trials: int,
                    weights: list, seed: int) -> None:
    """Печатает параметры варианта и характеристики кода."""
    k = k1 * k2
    r = k1 + k2 + n_groups - 2
    print("=" * 72)
    print("ЛАБОРАТОРНАЯ РАБОТА № 5. ИТЕРАТИВНЫЕ КОДЫ (КОД ПРОИЗВЕДЕНИЯ)")
    print("=" * 72)
    print("Параметры варианта 1 (таблица 5.2):")
    print("  длина информационного слова k = %d бит" % k)
    print("  разбиение матрицы: k1 = %d строк, k2 = %d столбцов (%d x %d = %d)"
          % (k1, k2, k1, k2, k))
    print("  число измерений z = 2, число групп паритетов = %d" % n_groups)
    if n_groups == 2:
        print("  группы паритетов: Xh (строки) и Xv (столбцы), r = k1 + k2 = %d" % r)
    else:
        print("  группы паритетов: Xh, Xv и Xhv (общая четность), "
              "r = k1 + k2 + 1 = %d" % r)
    print("  длина кодового слова n = k + r = %d бит" % (k + r))
    print("  статистика: кратности %s, повторов для каждой кратности = %d"
          % (", ".join(str(w) for w in weights), trials))
    print("  зерно генератора случайных чисел = %d (повторяемый результат)" % seed)


def show_practicum_check() -> None:
    """
    Проверяет на данных из практикума (Xk = 011101111, матрица 3 на 3), что
    расчет паритетов и сборка кодового слова дают Xh = 001, Xv = 001, Xhv = 1
    и Xn = 0111011110010011.
    """
    print("\n" + "=" * 72)
    print("ПРОВЕРКА НА ДАННЫХ ИЗ ПРАКТИКУМА (матрица 3 x 3)")
    print("=" * 72)
    xk = "011101111"
    matrix = build_matrix(xk, 3, 3)
    print("Xk = %s" % xk)
    show_matrix(matrix)
    xh = calc_xh(matrix)
    xv = calc_xv(matrix)
    xhv = calc_xhv(xk, xh, xv)
    xn = build_codeword(xk, xh, xv, xhv)
    print("Xh  = %s   (по строкам)" % xh)
    print("Xv  = %s   (по столбцам)" % xv)
    print("Xhv = %s   (паритет паритетов)" % xhv)
    print("Xn  = %s   (%d бит)" % (xn, len(xn)))
    expected_xn = "0111011110010011"
    print("Ожидалось по практикуму: Xh = 001, Xv = 001, Xhv = 1, Xn = %s"
          % expected_xn)
    matches = (xh == "001" and xv == "001" and xhv == "1" and xn == expected_xn)
    print("Результат проверки: %s" % ("СОВПАДАЕТ" if matches else "НЕ СОВПАДАЕТ"))


def show_encoding(xk: str, k1: int, k2: int) -> tuple:
    """
    Печатает пункты 1-3: разбиение на матрицу, паритеты по двум и по трем
    направлениям и собранное кодовое слово.

    Args:
        xk: информационное слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.

    Returns:
        Кортеж (xn_two, xn_three).
    """
    print("\n" + "=" * 72)
    print("ПУНКТЫ 1-3. РАЗБИЕНИЕ НА МАТРИЦУ, ПАРИТЕТЫ, КОДОВОЕ СЛОВО")
    print("=" * 72)
    matrix = build_matrix(xk, k1, k2)
    print("Пункт 1. Информационное слово в матрице %d x %d:" % (k1, k2))
    print("Xk = %s (%d бит)" % (xk, len(xk)))
    show_matrix(matrix)

    print("\nПункт 2 а). Паритеты по двум направлениям (две группы):")
    xh = calc_xh(matrix)
    xv = calc_xv(matrix)
    for i, bit in enumerate(xh):
        row_sum = sum(matrix[i])
        print("  Xh[%d] = %d %% 2 = %s   (сумма битов строки %d = %d)"
              % (i + 1, row_sum, bit, i + 1, row_sum))
    for j in range(k2):
        col_sum = sum(matrix[i][j] for i in range(k1))
        print("  Xv[%d] = %d %% 2 = %s   (сумма битов столбца %d = %d)"
              % (j + 1, col_sum, xv[j], j + 1, col_sum))

    print("\nПункт 2 б). Плюс паритет паритетов (три группы):")
    xhv = calc_xhv(xk, xh, xv)
    print("  Xhv = сумма по модулю 2 всех битов Xk, Xh и Xv = %s" % xhv)

    xn_two = build_codeword(xk, xh, xv, '')
    xn_three = build_codeword(xk, xh, xv, xhv)
    print("\nПункт 3. Кодовые слова (порядок: Xk, Xh, Xv, Xhv):")
    print("  две группы: r = %d, Xn = %s" % (k1 + k2, xn_two))
    print("  три группы: r = %d, Xn = %s" % (k1 + k2 + 1, xn_three))
    return xn_two, xn_three


def show_decoding(xn: str, k1: int, k2: int, n_groups: int,
                  rng: random.Random) -> None:
    """
    Печатает пункты 4-5 на примере одиночной ошибки: показывает принятое слово,
    пересчитанные паритеты, синдром, найденные строку и столбец и результат
    исправления.
    """
    print("\n" + "=" * 72)
    print("ПУНКТЫ 4-5. ОДИНОЧНАЯ ОШИБКА: ВНЕСЕНИЕ, ПОИСК И ИСПРАВЛЕНИЕ")
    print("=" * 72)
    print("Вариант кода: %d группы паритетов, длина слова n = %d"
          % (n_groups, len(xn)))
    table = build_syndrome_table(k1, k2, n_groups)
    yn, positions = inject_errors(xn, 1, rng)
    position = positions[0]
    print("Пункт 4. Ошибка кратности i = 1 внесена в символ %d (%s)."
          % (position, describe_position(position, k1, k2)))
    print("  Xn = %s" % xn)
    print("  Yn = %s" % yn)
    print("            ^  <- ошибочный символ")

    syndrome, yk, yh, yv, yhv, yh_p, yv_p, yhv_p = calc_syndrome(yn, k1, k2, n_groups)
    print("\nПункт 5. Пересчет паритетов по принятой информационной части:")
    print("  Yk              = %s" % yk)
    print("  Yh  (принятые)  = %s" % yh)
    print("  Yh' (пересчет)  = %s" % yh_p)
    print("  Yv  (принятые)  = %s" % yv)
    print("  Yv' (пересчет)  = %s" % yv_p)
    if n_groups == 3:
        print("  Yhv (принятый)  = %s" % yhv)
        print("  Yhv'(пересчет)  = %s" % yhv_p)
    print("  Синдром S = Yh+Yh' + Yv+Yv' + Yhv+Yhv' = %s" % syndrome)
    broken_rows = [i + 1 for i in range(k1) if syndrome[i] == '1']
    broken_cols = [j + 1 for j in range(k2) if syndrome[k1 + j] == '1']
    print("  Строки с нарушенной четностью: %s" % (broken_rows if broken_rows else "нет"))
    print("  Столбцы с нарушенной четностью: %s" % (broken_cols if broken_cols else "нет"))
    print("  Ошибка в матрице найдена по пересечению строки и столбца.")

    s_fixed, yn_fixed, detected, found_positions, correct = decode(
        yn, xn, k1, k2, n_groups, table)
    print("  Позиция ошибочного символа по синдрому: %s (%s)"
          % (found_positions, describe_position(found_positions[0], k1, k2)))
    print("  Yn' = %s" % yn_fixed)
    print("  Yn' == Xn: %s" % correct)

    # Вторая одиночная ошибка - в паритете Xh: строка определяется, столбец
    # нет, и ошибку в паритете декодер исправляет по самому факту одиночности.
    parity_position = k1 * k2 + 1
    yn2 = list(xn)
    yn2[parity_position - 1] = '1' if yn2[parity_position - 1] == '0' else '0'
    yn2 = ''.join(yn2)
    syndrome2 = calc_syndrome(yn2, k1, k2, n_groups)[0]
    s2_fixed, yn2_fixed, detected2, found2, correct2 = decode(
        yn2, xn, k1, k2, n_groups, table)
    print("\n  Для сравнения: та же операция, но ошибка в символе %d (%s)."
          % (parity_position, describe_position(parity_position, k1, k2)))
    print("    Yn  = %s" % yn2)
    print("    S   = %s  (нарушена только строка 1, столбцы целы)" % syndrome2)
    print("    Найденный символ: %s, Yn' == Xn: %s"
          % (describe_position(found2[0], k1, k2), correct2))


def show_rectangle(xk: str, k1: int, k2: int, title: str) -> None:
    """
    Строит слово с ошибкой в четырех вершинах прямоугольника и печатает его
    вместе с паритетами и синдромом.

    Args:
        xk: информационное слово.
        k1: число строк матрицы.
        k2: число столбцов матрицы.
        title: подпись к примеру.
    """
    print("\n%s" % title)
    matrix = build_matrix(xk, k1, k2)
    corners = [(0, 0), (0, 1), (1, 0), (1, 1)]
    for row, col in corners:
        matrix[row][col] ^= 1
    yk = ''.join(str(bit) for row in matrix for bit in row)
    marks = [' '] * len(yk)
    for row, col in corners:
        marks[row * k2 + col] = '^'
    xh = calc_xh(build_matrix(xk, k1, k2))
    xv = calc_xv(build_matrix(xk, k1, k2))
    yh = calc_xh(matrix)
    yv = calc_xv(matrix)
    xn = build_codeword(xk, xh, xv, '')
    yn = build_codeword(yk, yh, yv, '')
    print("Xn = %s" % xn)
    print("Yn = %s" % yn)
    print("    %s   <- четыре ошибочных бита" % ''.join(marks))
    print("Xh = %s, Yh = %s  -> разность = %s"
          % (xh, yh, ''.join(str(int(a) ^ int(b)) for a, b in zip(xh, yh))))
    print("Xv = %s, Yv = %s  -> разность = %s"
          % (xv, yv, ''.join(str(int(a) ^ int(b)) for a, b in zip(xv, yv))))
    syndrome = calc_syndrome(yn, k1, k2, 2)[0]
    print("Синдром кода без Xhv: S = %s = %s | %s (горизонтальные | вертикальные)"
          % (syndrome, syndrome[:k1], syndrome[k1:]))
    print("Yn == Xn: %s" % (yn == xn))
    yn_with_parity = build_codeword(yk, yh, yv, calc_xhv(yk, yh, yv))
    syndrome_with_parity = calc_syndrome(yn_with_parity, k1, k2, 3)[0]
    print("То же слово с паритетом Xhv: S = %s = %s | %s | %s"
          % (syndrome_with_parity, syndrome_with_parity[:k1],
             syndrome_with_parity[k1:k1 + k2], syndrome_with_parity[k1 + k2:]))


def show_undetectable_error(xk: str, k1: int, k2: int) -> None:
    """
    Печатает пункт 5 (проверка): ошибка в четырех вершинах прямоугольника
    (две строки на два столбца) не нарушает четность ни по строкам, ни по
    столбцам, поэтому синдром равен нулю и ошибка не обнаруживается.
    """
    print("\n" + "=" * 72)
    print("НЕОБНАРУЖИВАЕМАЯ ОШИБКА: ПРЯМОУГОЛЬНИК ИЗ ЧЕТЫРЕХ БИТ")
    print("=" * 72)
    print("Ошибка в вершинах (1,1), (1,2), (2,1), (2,2): в каждой из двух строк")
    print("и в каждом из двух столбцов инвертировано ровно два бита, поэтому")
    print("четность не нарушается ни по одному направлению.")

    show_rectangle(
        "011101111", 3, 3,
        "Пример 1: матрица 3 x 3 (данные практикума).")
    show_rectangle(
        xk, k1, k2,
        "Пример 2: рабочая матрица %d x %d." % (k1, k2))

    print("\nВывод: все биты синдрома нулевые (S = 000...0), все паритеты совпали,")
    print("а слово передано с ошибкой. Это НЕОБНАРУЖИВАЕМАЯ ошибка: декодер считает")
    print("слово верным, и исправить ее невозможно.")
    print("Общий бит четности Xhv здесь не помогает: в прямоугольнике четыре бита,")
    print("значит общая четность не нарушается и синдром остается нулевым.")


def show_properties(k1: int, k2: int) -> None:
    """
    Печатает измеренное минимальное кодовое расстояние и объясняет, чем
    измеренные значения отличаются от формул, приведенных в теории.
    """
    print("\n" + "=" * 72)
    print("МИНИМАЛЬНОЕ КОДОВОЕ РАССТОЯНИЕ (измерено перебором слов Xk)")
    print("=" * 72)
    for n_groups in (2, 3):
        dmin = measure_dmin(k1, k2, n_groups)
        # По формулам (8) и (9) лекции: t_и = (d-1)/2 при нечётном d
        # и (d-2)/2 при чётном; t_о = (d-1)/2 при нечётном и d/2 при чётном.
        if dmin % 2:
            t_fix, t_det = (dmin - 1) // 2, (dmin - 1) // 2
        else:
            t_fix, t_det = (dmin - 2) // 2, dmin // 2
        if dmin < 0:
            print("  %d группы паритетов: перебор 2^k слов слишком велик." % n_groups)
            continue
        print("  %d группы паритетов: dmin = %d  ->  исправляет %d ошибку, "
              "обнаруживает до %d (по формулам (8) и (9))"
              % (n_groups, dmin, t_fix, t_det))
    print("\nПояснение к теории. В теории указано: без Xhv dmin = 2 * 2 = 4,")
    print("с Xhv dmin = 4 + 1 = 5. Формула произведения dmin = d1 * d2 верна для")
    print("произведения двух кодов простой четности, где на каждую строку и на")
    print("каждый столбец приходится по k2 (k1) проверочных битов. В данной")
    print("конструкции на всю строку добавлен ровно один бит Xh и на весь столбец")
    print("один бит Xv, поэтому одиночная ошибка в данных меняет сразу три бита")
    print("кодового слова (сам бит данных, Xh и Xv):")
    print("  - без общего бита четности Xhv вес такого слова равен 3, dmin = 3;")
    print("  - с общим битом четности Xhv вес дополняется до 4, dmin = 4.")
    print("Исправляется при этом одна ошибка в обоих случаях, а общий бит четности")
    print("нужен для того, чтобы отличать ошибку в данных от ошибки в паритете.")


def show_statistics(results: dict, n_groups: int) -> None:
    """
    Печатает сводную таблицу пункта 6: по каждой кратности сколько слов
    сгенерировано, сколько раз кратность определена верно, сколько раз все
    ошибки исправлены и сколько раз ошибка была обнаружена вовсе.
    """
    print("\n" + "=" * 72)
    print("ПУНКТ 6. АНАЛИЗ КОРРЕКТИРУЮЩЕЙ СПОСОБНОСТИ (%d группы паритетов)"
          % n_groups)
    print("=" * 72)
    print("Для каждой кратности i сгенерировано N1 слов с ошибками.")
    print("N2 - кратность определена верно (найдено нужное число символов).")
    print("N3 - все ошибки исправлены, то есть Yn' равно Xn.")
    print("Отношения N2/N1 и N3/N1 - количественная оценка корректирующей")
    print("способности кода.\n")
    header = "%-9s %8s %8s %11s %8s %11s %12s %11s" % (
        "кратность", "N1", "N2", "N2/N1, %", "N3", "N3/N1, %",
        "обнаружено", "доля, %")
    print(header)
    print("-" * len(header))
    for weight in sorted(results):
        n1, n2, n3, detected_count = results[weight]
        print("%-9d %8d %8d %11.2f %8d %11.2f %12d %11.2f"
              % (weight, n1, n2, percent(n2, n1), n3, percent(n3, n1),
                 detected_count, percent(detected_count, n1)))


def show_conclusions(results_two: dict, results_three: dict) -> None:
    """
    Печатает выводы по результатам моделирования, подставляя измеренные доли
    необнаруженных ошибок.
    """
    undetected_two = (100.0 - percent(results_two[3][3], results_two[3][0])) if 3 in results_two else 0.0
    undetected_three = (100.0 - percent(results_three[3][3], results_three[3][0])) if 3 in results_three else 0.0
    print("\n" + "=" * 72)
    print("ВЫВОДЫ")
    print("=" * 72)
    print("1. Кратность i = 1: кратность и номер ошибочного символа определяются")
    print("   верно во всех случаях, слово исправляется полностью (100.00 %).")
    print("   Ошибочный бит данных находится как пересечение строки с нарушенной")
    print("   четностью и столбца с нарушенной четностью.")
    print("2. Кратность i = 2 и i = 3: ошибки обнаруживаются (ненулевой синдром),")
    print("   но ни кратность, ни все ошибочные символы определить нельзя: одному")
    print("   и тому же синдрому соответствует несколько наборов ошибок, поэтому")
    print("   доли N2/N1 и N3/N1 равны нулю. Это и означает t = 1.")
    print("3. Общий бит четности Xhv повышает обнаруживаемую кратность с 2 до 3:")
    print("   доля необнаруженных ошибок при i = 3 снижается с %.2f %% (две группы)"
          % undetected_two)
    print("   до %.2f %% (три группы)." % undetected_three)
    print("4. Кратность i = 4: часть наборов ошибок не обнаруживается вовсе - это")
    print("   четыре бита в вершинах прямоугольника (две строки на два столбца).")
    print("   Четность по строкам и по столбцам при этом не меняется.")
    print("5. Практикум требует отношения N2/N1 и N3/N1 к общему числу слов с")
    print("   ошибками; обе доли приведены в таблице пункта 6 и подтверждают")
    print("   свойства кода: исправляется одна ошибка, обнаруживаются все наборы")
    print("   ошибок не выше предела, заданного dmin, а необнаруживаемые комбинации")
    print("   связаны с прямоугольником из четырех бит.")


def parse_args() -> argparse.Namespace:
    """
    Разбирает параметры командной строки. Значения по умолчанию соответствуют
    варианту 1 таблицы 5.2, поэтому программа запускается без аргументов.
    """
    parser = argparse.ArgumentParser(
        description="Лабораторная работа № 5: итеративные коды (код произведения).")
    parser.add_argument("--k", type=int, default=16,
                        help="длина информационного слова, бит (по умолчанию 16)")
    parser.add_argument("--k1", type=int, default=4,
                        help="число строк матрицы (по умолчанию 4)")
    parser.add_argument("--k2", type=int, default=4,
                        help="число столбцов матрицы (по умолчанию 4)")
    parser.add_argument("--groups", type=int, choices=(2, 3), default=3,
                        help="число групп паритетов: 2 или 3 (по умолчанию 3)")
    parser.add_argument("--trials", type=int, default=2000,
                        help="слов с ошибками на каждую кратность (по умолчанию 2000)")
    parser.add_argument("--weights", type=int, nargs="+", default=[1, 2, 3, 4],
                        help="кратности ошибок (по умолчанию 1 2 3 4)")
    parser.add_argument("--seed", type=int, default=20261004,
                        help="зерно генератора случайных чисел (по умолчанию 20261004)")
    parser.add_argument("--xk", type=str, default="",
                        help="информационное слово задается явно; по умолчанию берётся из кода ASCII")
    return parser.parse_args()


def main() -> int:
    """
    Выполняет все шесть пунктов практического задания и печатает отчет.
    """
    args = parse_args()
    k1 = args.k1
    k2 = args.k2
    n_groups = args.groups
    trials = args.trials
    weights = args.weights
    seed = args.seed
    rng = random.Random(seed)
    n = k1 * k2 + k1 + k2 + n_groups - 2

    # Проверки параметров нужны, чтобы программа не падала с невнятной ошибкой.
    if k1 <= 0 or k2 <= 0:
        print("ОШИБКА: k1 и k2 должны быть положительными числами.")
        return 1
    if args.k != k1 * k2:
        print("ОШИБКА: размерности не согласованы: задано k = %d, а k1 * k2 = %d."
              % (args.k, k1 * k2))
        return 1
    if trials <= 0:
        print("ОШИБКА: число повторов должно быть положительным.")
        return 1
    for weight in weights:
        if weight < 1 or weight > n:
            print("ОШИБКА: кратность должна лежать в пределах от 1 до %d." % n)
            return 1

    if args.xk:
        xk = args.xk.strip()
    else:
        # Исходное сообщение: сумма кодов ASCII первой буквы имени (T) и
        # фамилии (M): T = 84, M = 77, сумма = 161. Остаток от деления на 2^k
        # нужен, чтобы при k меньше 8 бит слово осталось длины k.
        value = (ord('T') + ord('M')) % (1 << (k1 * k2))
        xk = format(value, '0{}b'.format(k1 * k2))
    if len(xk) != k1 * k2 or set(xk) - set('01'):
        print("ОШИБКА: Xk должно быть словом из %d нулей и единиц." % (k1 * k2))
        return 1

    show_parameters(k1, k2, n_groups, trials, weights, seed)
    show_practicum_check()
    xn_two, xn_three = show_encoding(xk, k1, k2)

    # Декодирование показываем на том варианте кода, который выбран в настройках.
    xn_active = xn_two if n_groups == 2 else xn_three
    show_decoding(xn_active, k1, k2, n_groups, rng)
    show_undetectable_error(xk, k1, k2)
    show_properties(k1, k2)

    results_two = {}
    results_three = {}
    for n_groups_variant in (2, 3):
        codeword = xn_two if n_groups_variant == 2 else xn_three
        results = run_analysis(codeword, k1, k2, n_groups_variant,
                               weights, trials, rng)
        show_statistics(results, n_groups_variant)
        if n_groups_variant == 2:
            results_two = results
        else:
            results_three = results

    show_conclusions(results_two, results_three)
    return 0


if __name__ == "__main__":
    sys.exit(main())
