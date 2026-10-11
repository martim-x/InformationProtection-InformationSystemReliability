import random
from itertools import combinations


# --------------------------------------------------------------------------
# Задание 4.2 (п. 2). Определение числа избыточных символов r
# --------------------------------------------------------------------------
def calc_r(k: int) -> int:
    """
    Вычисляет число избыточных символов r по неравенству 2^r >= n + 1,
    где n = k + r (л. 4.1.2, формула 4.5).

    Args:
        k: Длина информационного слова, бит.

    Returns:
        Минимальное подходящее значение r.
    """
    r = 1
    while 2**r < k + r + 1:
        r = r + 1
    return r


# --------------------------------------------------------------------------
# Листинг 4.1. Бином Ньютона: подсчёт числа комбинаций заданного веса
# --------------------------------------------------------------------------
def fact(n: int) -> int:
    """Возвращает факториал натурального числа n (рекурсивно, листинг 4.1)."""
    if n <= 1:
        return 1
    return fact(n - 1) * n


def binom(wt: int, r: int) -> int:
    """
    Возвращает число сочетаний из r по wt — количество двоичных
    комбинаций длины r с весом wt (листинг 4.1).

    Args:
        wt: Вес столбца (число единиц).
        r:  Длина двоичной комбинации.

    Returns:
        Значение биномиального коэффициента.
    """
    return fact(r) // (fact(wt) * fact(r - wt))


# --------------------------------------------------------------------------
# Задание 4.2 (п. 2). Построение подматрицы P' (алгоритм листинга 4.2)
# --------------------------------------------------------------------------
def build_p_prime(k: int, r: int) -> list[list[int]]:
    """
    Строит подматрицу P' размера k x r: перебирает натуральные числа от 3,
    переводит их в двоичную систему (дополняя до r разрядов) и берёт первые
    k чисел с весом не меньше 2. Нулевой и единичный векторы не используются.

    Args:
        k: Число информационных символов.
        r: Число избыточных символов.

    Returns:
        Матрица P' — список из k столбцов длины r.
    """
    p_prime = []  # список столбцов P'

    for wt in range(2, r + 1):
        # все числа с текущим весом wt, в порядке возрастания
        for num in range(3, 2**r):
            bits = bin(num)[2:].zfill(r)
            if bits.count("1") == wt:
                p_prime.append([int(bit) for bit in bits])
                if len(p_prime) == k:
                    return p_prime

        # комбинации веса wt исчерпаны — увеличиваем вес (листинг 4.2)
    return p_prime


# --------------------------------------------------------------------------
# Задание 4.2 (п. 2). Построение единичной матрицы I (листинг 4.3)
# --------------------------------------------------------------------------
def build_i(r: int) -> list[list[int]]:
    """
    Строит единичную матрицу I порядка r (r x r).

    Args:
        r: Порядок единичной матрицы.

    Returns:
        Матрица I — список из r столбцов длины r.
    """
    return [[1 if row == col else 0 for row in range(r)] for col in range(r)]


# --------------------------------------------------------------------------
# Задание 4.2 (п. 2). Проверочная матрица H = [P' | I]
# --------------------------------------------------------------------------
def build_h(k: int, r: int) -> list[list[int]]:
    """
    Склеивает подматрицу P' размера k x r и единичную матрицу I размера r x r
    в проверочную матрицу H = [P' | I] размера r x n (формула 4.4).

    Args:
        k: Число информационных символов.
        r: Число избыточных символов.

    Returns:
        Проверочная матрица H — список из r сток длины n = k + r.
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


# --------------------------------------------------------------------------
# Задание 4.2 (п. 3). Вычисление избыточных символов Xr
# --------------------------------------------------------------------------
def calc_xr(xk: list[int], p_prime: list[list[int]]) -> list[int]:
    """
    Вычисляет слово избыточных символов Xr: i-й символ равен 0, если
    количество пар (1;1) в позициях слова Xk и i-й строки P' чётно,
    иначе — 1.

    Args:
        xk:      Информационное слово, список бит.
        p_prime: Подматрица P' (список столбцов длины r).

    Returns:
        Слово Xr — список из r бит.
    """
    r = len(p_prime[0])
    xr = []
    for row in range(r):
        pairs = 0
        for col in range(len(xk)):
            if xk[col] == 1 and p_prime[col][row] == 1:
                pairs = pairs + 1
        xr.append(pairs % 2)
    return xr


# --------------------------------------------------------------------------
# Задание 4.2 (п. 5). Пересчёт избыточных символов принятого слова
# --------------------------------------------------------------------------
def calc_yr_from_yk(yk: list[int], p_prime: list[list[int]]) -> list[int]:
    """
    Вычисляет пересчитанные избыточные символы Yr' принятого слова Yk
    (теми же формулами, что и для Xr).

    Args:
        yk:      Принятое информационное слово, список бит.
        p_prime: Подматрица P'.

    Returns:
        Слово Yr' — список из r бит.
    """
    return calc_xr(yk, p_prime)


# --------------------------------------------------------------------------
# Задание 4.2 (п. 6). Вычисление синдрома (листинг 4.4)
# --------------------------------------------------------------------------
def calc_syndrome(yr: list[int], yr_prime: list[int]) -> list[int]:
    """
    Вычисляет синдром S как сумму по модулю 2 векторов Yr и Yr':
    i-й бит равен 0, если Yr[i] == Yr'[i], иначе — 1 (листинг 4.4).

    Args:
        yr:       Отправленные избыточные символы.
        yr_prime: Пересчитанные избыточные символы принятого слова.

    Returns:
        Синдром S — список из r бит.
    """
    return [0 if yr[i] == yr_prime[i] else 1 for i in range(len(yr))]


# --------------------------------------------------------------------------
# Задание 4.2 (п. 6). Вектор ошибки En (листинг 4.5)
# --------------------------------------------------------------------------
def build_error_vector(n: int, positions: list[int]) -> list[int]:
    """
    Формирует вектор ошибки En: единицы стоят в ошибочных позициях,
    остальные элементы равны нулю (листинг 4.5).

    Args:
        n:         Длина кодового слова.
        positions: Список ошибочных позиций (нумерация с 0).

    Returns:
        Вектор ошибки En — список из n бит.
    """
    error = [0] * n
    for pos in positions:
        error[pos] = 1
    return error


# --------------------------------------------------------------------------
# Задание 4.2 (п. 6). Определение номера ошибочного бита по синдрому
# --------------------------------------------------------------------------
def find_error_position(syndrome: list[int], matrix_h: list[list[int]]) -> int:
    """
    Ищет номер позиции ошибочного бита: ненулевой синдром равен сумме
    по модулю 2 тех столбцов матрицы H, в которых возникла ошибка.
    Для одиночной ошибки синдром в точности совпадает со столбцом H.

    Args:
        syndrome:  Синдром S.
        matrix_h:  Проверочная матрица H = [P' | I] (список строк длины n).

    Returns:
        Индекс ошибочного бита (нумерация с 0), либо -1 если не найден.
    """
    for col in range(len(matrix_h[0])):
        # столбец матрицы H — биты строк в позиции col
        column = [matrix_h[row][col] for row in range(len(matrix_h))]
        if column == syndrome:
            return col
    return -1


# --------------------------------------------------------------------------
# Задание 4.2 (п. 6). Исправление слова: Xn = Yn + En
# --------------------------------------------------------------------------
def correct_word(yn: list[int], error: list[int]) -> list[int]:
    """
    Исправляет принятое слово сложением по модулю 2 с вектором ошибки (4.7).

    Args:
        yn:    Принятое кодовое слово.
        error: Вектор ошибки En.

    Returns:
        Исправленное кодовое слово Xn.
    """
    return [yn[i] ^ error[i] for i in range(len(yn))]


# --------------------------------------------------------------------------
# Печать проверочной матрицы
# --------------------------------------------------------------------------
def print_matrix(matrix: list[list[int]], title: str) -> None:
    """Выводит матрицу построчно с заголовком."""
    print(f"\n{title}")
    print("-" * len(title))
    for index, row in enumerate(matrix):
        print(f"  строка {index + 1}: " + " ".join(str(bit) for bit in row))


def bits_to_str(bits: list[int]) -> str:
    """Преобразует список бит в строку из нулей и единиц."""
    return "".join(str(bit) for bit in bits)


# --------------------------------------------------------------------------
# Основная программа: выполняет задания 1-6 практического задания
# --------------------------------------------------------------------------
def main() -> None:
    """Выполняет лабораторную работу № 4: кодирование и коррекция ошибок."""
    print("=" * 62)
    print("ЛАБОРАТОРНАЯ РАБОТА № 4: КОД ХЕММИНГА")
    print("=" * 62)

    # --- Задание 1. Формирование информационного сообщения -----------------
    letter_name = ord("T")  # T — первая буква имени Тимофей
    letter_surname = ord("M")  # M — первая буква фамилии Марушко
    message_value = letter_name + letter_surname

    xk = [int(bit) for bit in bin(message_value)[2:].zfill(8)]

    print("\n--- ЗАДАНИЕ 1: информационное сообщение ---")
    print(f"ASCII 'T' (имя)     = {letter_name}  = {bin(letter_name)[2:].zfill(8)}")
    print(
        f"ASCII 'M' (фамилия) = {letter_surname}  = {bin(letter_surname)[2:].zfill(8)}"
    )
    print(f"Сумма кодов         = {message_value} = {bits_to_str(xk)}")
    print(f"Длина сообщения k   = {len(xk)} бит")

    k = len(xk)

    # --- Задание 2. Построение проверочной матрицы -------------------------
    r = calc_r(k)
    n = k + r
    p_prime = build_p_prime(k, r)
    matrix_h = build_h(k, r)

    print("\n--- ЗАДАНИЕ 2: параметры кода и матрица H ---")
    print(f"k = {k}, r = {r}, n = {n}")
    print(f"Проверка: 2^{r} = {2 ** r} >= n + 1 = {n + 1}  ->  " f"{2 ** r >= n + 1}")
    print(f"Относительная избыточность Rr = r/k = {r / k:.4f}")
    print(f"Скорость кода Rk = k/n = {k / n:.4f}")

    print("\nПодматрица P' (столбцы — номера позиций в двоичном виде):")
    for col in range(len(p_prime)):
        print(f"  позиция {col + 1:2d} (индекс {col}): " f"{bits_to_str(p_prime[col])}")

    print_matrix(matrix_h, "Проверочная матрица H = [P' | I]")

    # --- Задание 3. Вычисление избыточных символов -------------------------
    xr = calc_xr(xk, p_prime)
    xn = xk + xr

    print("\n--- ЗАДАНИЕ 3: избыточные символы ---")
    print(f"Xk = {bits_to_str(xk)}")
    print(f"Xr = {bits_to_str(xr)}")
    print(f"Xn = {bits_to_str(xn)}   ({n} бит)")

    # проверка свойства H * Xn^T = 0
    check = []
    for row in matrix_h:
        pairs = 0
        for col in range(n):
            if xn[col] == 1 and row[col] == 1:
                pairs = pairs + 1
        check.append(pairs % 2)
    print(
        f"Проверка H * Xn^T = {bits_to_str(check)} "
        f"(нулевой синдром подтверждает корректность кодирования)"
    )

    # --- Задание 4-6. Внесение ошибок и их исправление ---------------------
    print("\n--- ЗАДАНИЯ 4-6: моделирование ошибок ---")

    for error_count in (0, 1, 2):
        print(f"\n" + "*" * 62)
        print(f"ВАРИАНТ: количество ошибок = {error_count}")
        print("*" * 62)

        # Задание 4: случайные позиции ошибок
        positions = random.sample(range(n), error_count)
        yn = list(xn)
        for pos in positions:
            yn[pos] = yn[pos] ^ 1
        yk = yn[:k]
        yr = yn[k:]

        print(
            f"Позиции ошибок (нумерация с 1): "
            f"{[pos + 1 for pos in sorted(positions)]}"
        )
        print(f"Xn (отправлено)  = {bits_to_str(xn)}")
        print(f"Yn (принято)     = {bits_to_str(yn)}")
        print(f"  Yk = {bits_to_str(yk)}")
        print(f"  Yr = {bits_to_str(yr)}")

        # Задание 5: пересчёт избыточных символов
        yr_prime = calc_yr_from_yk(yk, p_prime)
        print(f"  Yr' = {bits_to_str(yr_prime)}   (пересчитано по (4.6))")

        # Задание 6: синдром и исправление
        syndrome = calc_syndrome(yr, yr_prime)
        syndrome_value = int(bits_to_str(syndrome), 2)
        print(f"Синдром S = {bits_to_str(syndrome)} = {syndrome_value}")

        # Нулевой синдром при двух ошибках — необнаруживаемая ошибка.
        # Проверяем реальное расхождение, а не доверяем синдрому.
        if syndrome_value == 0:
            if error_count == 0:
                print("Результат: S = 0, ошибок действительно нет — верно.")
            else:
                print("Результат: S = 0, но в слове есть ошибки!")
                print("Это НЕОБНАРУЖИВАЕМАЯ ошибка: сумма двух столбцов H")
                print("дала нулевой синдром. Декодер считает слово верным,")
                print("а Yn != Xn.")
                print(f"Yn = {bits_to_str(yn)}")
                print(f"Xn = {bits_to_str(xn)}")
            continue

        # одиночная ошибка — исправляется
        if error_count == 1:
            pos = find_error_position(syndrome, matrix_h)
            error_vector = build_error_vector(n, [pos])
            fixed = correct_word(yn, error_vector)

            print("Ненулевой синдром -> одиночная ошибка.")
            print(f"Ошибочный бит: позиция {pos + 1} (индекс {pos})")
            print(f"Вектор ошибки En = {bits_to_str(error_vector)}")
            print(f"Исправлено Xn = Yn + En = {bits_to_str(fixed)}")
            print(f"Верно: {fixed == xn}")
        else:
            # двойная ошибка — синдром указывает на ложную позицию
            pos = find_error_position(syndrome, matrix_h)
            real = sorted(p + 1 for p in positions)
            guessed = pos + 1
            if guessed in real:
                verdict = "один из двух битов угадан, второй остался"
            else:
                verdict = "указана позиция, где ошибки нет"
            print("Ненулевой синдром при двух ошибках -> ОШИБОЧНАЯ КОРРЕКЦИЯ.")
            print(f"Синдром указывает на позицию {guessed}; реальные ошибки: {real}")
            print(
                f"Итог: {verdict}. Слово после коррекции неверно: "
                f"{correct_word(yn, build_error_vector(n, [pos])) != xn}"
            )
            print(
                "Решение: расширенный код с dmin = 4 (общая чётность) "
                "обнаруживает двойную ошибку, но не исправляет."
            )

    # --- Задание 6. Исчерпывающий анализ по кратности ---------------------
    print("\n" + "=" * 62)
    print("ЗАДАНИЕ 6: СВОДНЫЙ АНАЛИЗ ПО КРАТНОСТИ ОШИБОК (все пары)")
    print("=" * 62)

    total = n * (n - 1) // 2
    detected = 0
    corrected = 0
    silent = 0
    for i in range(n):
        for j in range(i + 1, n):
            yn_t = list(xn)
            yn_t[i] ^= 1
            yn_t[j] ^= 1
            s = calc_syndrome(yn_t[k:], calc_yr_from_yk(yn_t[:k], p_prime))
            if not any(s):
                silent += 1
                continue
            detected += 1
            p = find_error_position(s, matrix_h)
            if correct_word(yn_t, build_error_vector(n, [p])) == xn:
                corrected += 1

    print(f"Всего пар позиций (двойная ошибка): {total}")
    print(f"Обнаружено ненулевым синдромом:      {detected}")
    print(f"Не обнаружено (S = 0):               {silent}")
    print(f"Из обнаруженных исправлено верно:    {corrected}")
    print(f"Доля обнаружения:  {detected / total:.4f}")
    print(f"Доля исправления:  {corrected / total:.4f}")

    # --- Задание 6. Тройные ошибки: часть неразличима ---------------------
    def syndrome_at(word: list[int], pos: int) -> list[int]:
        """Синдром слова word при инверсии бита в позиции pos."""
        probe = list(word)
        probe[pos] ^= 1
        return calc_syndrome(probe[k:], calc_yr_from_yk(probe[:k], p_prime))

    triples = list(combinations(range(n), 3))
    blind = []
    for a, b, c in triples:
        s = [
            syndrome_at(xn, a)[i] ^ syndrome_at(xn, b)[i] ^ syndrome_at(xn, c)[i]
            for i in range(r)
        ]
        if not any(s):
            blind.append((a, b, c))

    print(f"\nВсего троек позиций:                {len(triples)}")
    print(f"Не обнаружено (S = 0):             {len(blind)}")
    print(
        f"Примеры таких троек (позиции): "
        f"{[tuple(p + 1 for p in t) for t in blind[:5]]}"
    )

    print("\nВывод по dmin = 3 (t_и = 1, t_о = 1 по формулам (8) и (9)):")
    print("  1 ошибка  — обнаруживается и исправляется ВСЕГДА (n из n).")
    print("  2 ошибки  — обнаруживается ВСЕГДА: сумма двух РАЗНЫХ столбцов H")
    print("              не может быть нулём. Но исправить нельзя —")
    print("              синдром указывает на одну позицию, а ошибок две.")
    print("  3 ошибки  — часть троек неразличима с корректным словом:")
    print("              сумма трёх столбцов может дать нулевой синдром.")


if __name__ == "__main__":
    main()
