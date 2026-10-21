import os

from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from entropy_lab import INPUT, OUTPUT, counter_of

# Пары (лист в Excel, файл документа, ключ алфавита, подпись).
SEQUENCES = [
    ("Латиница", f"{INPUT}/latin.txt", "latin", "Латиница"),
    (
        "Кириллица",
        f"{INPUT}/cyrillic.txt",
        "cyrillic",
        "Кириллица",
    ),
]


def build_workbook(seq_name, path, alphabet, chart_title, out_path):
    """Формирует книгу Excel с таблицей частот и гистограммой."""
    counter = counter_of(path, alphabet).most_common()
    total = sum(cnt for _, cnt in counter)

    wb = Workbook()
    ws = wb.active
    ws.title = seq_name

    header = ["Символ", "Частота", "Вероятность"]
    ws.append(header)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = PatternFill("solid", fgColor="D9E1F2")
        cell.alignment = Alignment(horizontal="center")
    for ch, cnt in counter:
        ws.append([ch, cnt, cnt / total])

    row_count = len(counter) + 1
    ws.freeze_panes = "A2"
    ws.column_dimensions["A"].width = 10
    ws.column_dimensions["B"].width = 12
    ws.column_dimensions["C"].width = 14
    for row in ws.iter_rows(min_row=2, min_col=2, max_row=row_count, max_col=2):
        for cell in row:
            cell.number_format = "0"
    for row in ws.iter_rows(min_row=2, min_col=3, max_row=row_count, max_col=3):
        for cell in row:
            cell.number_format = "0.000000"

    chart = BarChart()
    chart.type = "col"
    chart.style = 10
    chart.title = f"Гистограмма частот символов — {chart_title}"
    chart.y_axis.title = "Вероятность"
    chart.x_axis.title = "Символ"

    data = Reference(ws, min_col=3, min_row=1, max_row=row_count)
    cats = Reference(ws, min_col=1, min_row=2, max_row=row_count)
    chart.add_data(data, titles_from_data=True)
    chart.set_categories(cats)
    chart.dLbls = DataLabelList()
    chart.dLbls.showVal = True
    chart.legend = None
    chart.width = 24
    chart.height = 12

    ws.add_chart(chart, f"E2")
    wb.save(out_path)
    return out_path


def main():
    os.makedirs(OUTPUT, exist_ok=True)
    for seq_name, path, alphabet, label in SEQUENCES:
        out_path = f"{OUTPUT}/freq_{alphabet}.xlsx"
        build_workbook(seq_name, path, alphabet, label, out_path)
        print(f"OK: {out_path}")


if __name__ == "__main__":
    main()
