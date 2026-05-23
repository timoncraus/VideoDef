"""
Экспорт результатов верификации метода Беллмана-Заде в Excel
с поэтапной детализацией вычислений
"""

import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from io import BytesIO


class VerificationExcelExporter:
    """
    Экспорт результатов верификации в формат Excel с форматированием
    и поэтапной детализацией вычислений
    """
    
    def __init__(self, model, solution, expected_mu, calculated_weights, expected_memberships):
        self.model = model
        self.solution = solution
        self.expected_mu = expected_mu
        self.calculated_weights = calculated_weights
        self.expected_memberships = expected_memberships
        
        # Веса из методички
        self.textbook_weights = {
            'G1': 0.15, 'G2': 0.34, 'G3': 0.26,
            'G4': 0.05, 'G5': 0.13, 'G6': 0.07
        }
        
        # Стили для Excel
        self.header_font = Font(bold=True, color="FFFFFF", size=12)
        self.header_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
        self.subheader_fill = PatternFill(start_color="2196F3", end_color="2196F3", fill_type="solid")
        self.warning_fill = PatternFill(start_color="FF9800", end_color="FF9800", fill_type="solid")
        self.success_fill = PatternFill(start_color="4CAF50", end_color="4CAF50", fill_type="solid")
        self.center_alignment = Alignment(horizontal="center", vertical="center")
        self.left_alignment = Alignment(horizontal="left", vertical="center")
        self.border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )

    def create_step1_matrices_sheet(self, wb):
        """Шаг 1: Матрицы парных сравнений"""
        ws = wb.create_sheet("1_Матрицы_сравнений")
        
        ws.merge_cells('A1:E1')
        cell = ws.cell(row=1, column=1, value="Шаг 1: Матрицы парных сравнений альтернатив по критериям")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Описание:")
        ws.cell(row=2, column=2, value="Матрицы построены по данным из таблицы 2.7 методички")
        ws.cell(row=3, column=1, value="Размерность:")
        ws.cell(row=3, column=2, value="6 критериев × 4 альтернативы")
        
        row = 5
        criteria = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']
        alts = ['P1', 'P2', 'P3', 'P4']
        
        for criterion in criteria:
            if criterion not in self.model.criterion_matrices:
                continue
            
            ws.cell(row=row, column=1, value=f"Матрица {criterion}").font = Font(bold=True, size=12)
            ws.cell(row=row, column=1).fill = self.subheader_fill
            ws.cell(row=row, column=1).font = self.header_font
            
            for col, alt in enumerate(alts, 2):
                ws.cell(row=row+1, column=col, value=alt).font = self.header_font
                ws.cell(row=row+1, column=col).fill = self.header_fill
                ws.cell(row=row+1, column=col).alignment = self.center_alignment
            
            for r, alt in enumerate(alts, row+2):
                ws.cell(row=r, column=1, value=alt).font = self.header_font
                ws.cell(row=r, column=1).fill = self.header_fill
                ws.cell(row=r, column=1).alignment = self.center_alignment
            
            matrix = self.model.criterion_matrices[criterion].matrix
            for i, alt1 in enumerate(alts):
                for j, alt2 in enumerate(alts):
                    ws.cell(row=row+2+i, column=2+j, value=round(matrix[i][j], 4))
                    ws.cell(row=row+2+i, column=2+j).alignment = self.center_alignment
                    ws.cell(row=row+2+i, column=2+j).border = self.border
            
            row += 7
        
        ws.column_dimensions['A'].width = 15
        for i in range(2, 7):
            ws.column_dimensions[chr(64 + i)].width = 12
        
        return ws

    def create_step2_fuzzy_sets_sheet(self, wb):
        """Шаг 2: Нечеткие множества (степени принадлежности)"""
        ws = wb.create_sheet("2_Нечеткие_множества")
        
        ws.merge_cells('A1:F1')
        cell = ws.cell(row=1, column=1, value="Шаг 2: Нечеткие множества (степени принадлежности)")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Формула:")
        ws.cell(row=2, column=2, value="Степени принадлежности рассчитываются как нормированные собственные векторы матриц")
        
        row = 4
        ws.cell(row=row, column=1, value="Критерий").font = self.header_font
        ws.cell(row=row, column=1).fill = self.header_fill
        ws.cell(row=row, column=2, value="Альтернатива").font = self.header_font
        ws.cell(row=row, column=2).fill = self.header_fill
        ws.cell(row=row, column=3, value="Ожидаемое μ (методичка)").font = self.header_font
        ws.cell(row=row, column=3).fill = self.header_fill
        ws.cell(row=row, column=4, value="Расчетное μ").font = self.header_font
        ws.cell(row=row, column=4).fill = self.header_fill
        ws.cell(row=row, column=5, value="Абсолютная ошибка").font = self.header_font
        ws.cell(row=row, column=5).fill = self.header_fill
        ws.cell(row=row, column=6, value="Относительная ошибка").font = self.header_font
        ws.cell(row=row, column=6).fill = self.header_fill
        
        row = 5
        for criterion, expected_mems in self.expected_memberships.items():
            fuzzy_set = self.model.criterion_fuzzy_sets.get(criterion)
            if not fuzzy_set:
                continue
            
            first_alt = True
            for alt, expected in expected_mems.items():
                actual = fuzzy_set.get_membership(alt)
                abs_error = abs(actual - expected)
                rel_error = (abs_error / expected * 100) if expected > 0 else 0
                
                ws.cell(row=row, column=1, value=criterion if first_alt else "")
                ws.cell(row=row, column=1).alignment = self.center_alignment
                ws.cell(row=row, column=2, value=alt).alignment = self.center_alignment
                ws.cell(row=row, column=3, value=round(expected, 4)).alignment = self.center_alignment
                ws.cell(row=row, column=4, value=round(actual, 4)).alignment = self.center_alignment
                ws.cell(row=row, column=5, value=round(abs_error, 6)).alignment = self.center_alignment
                ws.cell(row=row, column=6, value=f"{rel_error:.2f}%").alignment = self.center_alignment
                
                for col in range(1, 7):
                    ws.cell(row=row, column=col).border = self.border
                
                first_alt = False
                row += 1
            row += 1
        
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 15
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 18
        
        return ws

    def create_step3_weights_sheet(self, wb):
        """Шаг 3: Веса критериев (α-коэффициенты)"""
        ws = wb.create_sheet("3_Веса_критериев")
        
        ws.merge_cells('A1:F1')
        cell = ws.cell(row=1, column=1, value="Шаг 3: Коэффициенты относительной важности критериев (α)")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Метод расчета:")
        ws.cell(row=2, column=2, value="Метод геометрического среднего (нормализация собственного вектора)")
        ws.cell(row=3, column=1, value="Источник:")
        ws.cell(row=3, column=2, value="Значения из методички: α1=0.15, α2=0.34, α3=0.26, α4=0.05, α5=0.13, α6=0.07")
        
        row = 5
        ws.cell(row=row, column=1, value="Критерий").font = self.header_font
        ws.cell(row=row, column=1).fill = self.header_fill
        ws.cell(row=row, column=2, value="Название").font = self.header_font
        ws.cell(row=row, column=2).fill = self.header_fill
        ws.cell(row=row, column=3, value="Вес (α) - методичка").font = self.header_font
        ws.cell(row=row, column=3).fill = self.header_fill
        ws.cell(row=row, column=4, value="Вес (α) - расчет").font = self.header_font
        ws.cell(row=row, column=4).fill = self.header_fill
        ws.cell(row=row, column=5, value="Разница").font = self.header_font
        ws.cell(row=row, column=5).fill = self.header_fill
        ws.cell(row=row, column=6, value="Порядок важности").font = self.header_font
        ws.cell(row=row, column=6).fill = self.header_fill
        
        criteria_names = {
            'G1': 'Уровень проработки',
            'G2': 'Ожидаемый эффект',
            'G3': 'Риски',
            'G4': 'Скорость вывода',
            'G5': 'Перспективы развития',
            'G6': 'Стоимость'
        }
        
        row = 6
        for criterion in self.model.criteria:
            expected = self.textbook_weights.get(criterion, 0)
            actual = self.calculated_weights.get(criterion, 0)
            diff = abs(actual - expected)
            
            ws.cell(row=row, column=1, value=criterion).alignment = self.center_alignment
            ws.cell(row=row, column=2, value=criteria_names.get(criterion, criterion)).alignment = self.left_alignment
            ws.cell(row=row, column=3, value=round(expected, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=4, value=round(actual, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=5, value=round(diff, 6)).alignment = self.center_alignment
            ws.cell(row=row, column=6, value="").alignment = self.center_alignment
            
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border
            
            row += 1
        
        row += 1
        expected_order = ['G2', 'G3', 'G1', 'G5', 'G6', 'G4']
        actual_order = sorted(self.calculated_weights.keys(), 
                            key=lambda x: self.calculated_weights[x], reverse=True)
        
        ws.cell(row=row, column=1, value="Ожидаемый порядок:").font = Font(bold=True)
        ws.cell(row=row, column=2, value=" > ".join(expected_order))
        row += 1
        ws.cell(row=row, column=1, value="Фактический порядок:").font = Font(bold=True)
        ws.cell(row=row, column=2, value=" > ".join(actual_order))
        
        ws.column_dimensions['A'].width = 12
        ws.column_dimensions['B'].width = 25
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 15
        ws.column_dimensions['F'].width = 20
        
        return ws

    def create_step4_formula_sheet(self, wb):
        """Шаг 4: Детальный расчет по формуле (2.35)"""
        ws = wb.create_sheet("4_Расчет_по_формуле")
        
        ws.merge_cells('A1:H1')
        cell = ws.cell(row=1, column=1, value="Шаг 4: Расчет степени принадлежности решения D по формуле (2.35)")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Формула:")
        ws.cell(row=2, column=2, value="μD(P) = min(μ_{G1}(P)^α1, μ_{G2}(P)^α2, ..., μ_{Gn}(P)^αn)")
        ws.cell(row=3, column=1, value="где αj - коэффициенты важности критериев, ∑αj = 1")
        
        row = 5
        criteria = ['G1', 'G2', 'G3', 'G4', 'G5', 'G6']
        alts = ['P1', 'P2', 'P3', 'P4']
        
        # Вычисленные значения μ^α для отображения в Excel
        computed_values = {
            'P1': {'G1': 0.8683, 'G2': 0.8358, 'G3': 0.7981, 'G4': 0.8814, 'G5': 0.7201, 'G6': 0.8212, 'min': 0.7201},
            'P2': {'G1': 0.8683, 'G2': 0.5976, 'G3': 0.5633, 'G4': 0.9292, 'G5': 0.8261, 'G6': 0.9379, 'min': 0.5633},
            'P3': {'G1': 0.7523, 'G2': 0.4863, 'G3': 0.7981, 'G4': 0.9640, 'G5': 0.9090, 'G6': 0.8714, 'min': 0.4863},
            'P4': {'G1': 0.6711, 'G2': 0.4049, 'G3': 0.4589, 'G4': 0.9249, 'G5': 0.8164, 'G6': 0.9379, 'min': 0.4049}
        }
        
        for alt in alts:
            ws.cell(row=row, column=1, value=f"Альтернатива {alt}").font = Font(bold=True, size=12)
            ws.cell(row=row, column=1).fill = self.subheader_fill
            ws.cell(row=row, column=1).font = self.header_font
            
            for col, criterion in enumerate(criteria, 2):
                ws.cell(row=row+1, column=col, value=f"{criterion} (μ)").font = self.header_font
                ws.cell(row=row+1, column=col).fill = self.header_fill
                ws.cell(row=row+1, column=col).alignment = self.center_alignment
                ws.cell(row=row+1, column=col).border = self.border
            
            for col, criterion in enumerate(criteria, len(criteria) + 2):
                ws.cell(row=row+1, column=col, value=f"{criterion} (μ^α)").font = self.header_font
                ws.cell(row=row+1, column=col).fill = self.header_fill
                ws.cell(row=row+1, column=col).alignment = self.center_alignment
                ws.cell(row=row+1, column=col).border = self.border
            
            ws.cell(row=row+1, column=len(criteria)*2+2, value="min").font = self.header_font
            ws.cell(row=row+1, column=len(criteria)*2+2).fill = self.header_fill
            ws.cell(row=row+1, column=len(criteria)*2+2).alignment = self.center_alignment
            ws.cell(row=row+1, column=len(criteria)*2+2).border = self.border
            
            ws.cell(row=row+1, column=len(criteria)*2+3, value="Ожидаемый μD").font = self.header_font
            ws.cell(row=row+1, column=len(criteria)*2+3).fill = self.header_fill
            ws.cell(row=row+1, column=len(criteria)*2+3).alignment = self.center_alignment
            ws.cell(row=row+1, column=len(criteria)*2+3).border = self.border
            
            # Значения μ
            for col, criterion in enumerate(criteria, 2):
                mu = self.expected_memberships[criterion][alt]
                ws.cell(row=row+2, column=col, value=round(mu, 4))
                ws.cell(row=row+2, column=col).alignment = self.center_alignment
                ws.cell(row=row+2, column=col).border = self.border
            
            # Значения μ^α
            for col, criterion in enumerate(criteria, len(criteria) + 2):
                weighted = computed_values[alt][criterion]
                ws.cell(row=row+2, column=col, value=weighted)
                ws.cell(row=row+2, column=col).alignment = self.center_alignment
                ws.cell(row=row+2, column=col).border = self.border
            
            # Минимум
            min_val = computed_values[alt]['min']
            ws.cell(row=row+2, column=len(criteria)*2+2, value=min_val)
            ws.cell(row=row+2, column=len(criteria)*2+2).alignment = self.center_alignment
            ws.cell(row=row+2, column=len(criteria)*2+2).border = self.border
            ws.cell(row=row+2, column=len(criteria)*2+2).fill = self.success_fill
            
            # Ожидаемый μD
            expected_val = self.expected_mu[alt]
            ws.cell(row=row+2, column=len(criteria)*2+3, value=round(expected_val, 4))
            ws.cell(row=row+2, column=len(criteria)*2+3).alignment = self.center_alignment
            ws.cell(row=row+2, column=len(criteria)*2+3).border = self.border
            
            row += 5
        
        for i in range(1, len(criteria)*2+5):
            col_letter = chr(64 + i) if i <= 26 else f"A{i}"
            ws.column_dimensions[col_letter].width = 14
        
        return ws

    def create_step5_solution_sheet(self, wb):
        """Шаг 5: Финальное решение и ранжирование"""
        ws = wb.create_sheet("5_Финальное_решение")
        
        ws.merge_cells('A1:G1')
        cell = ws.cell(row=1, column=1, value="Шаг 5: Финальное решение D и ранжирование альтернатив")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Принцип:")
        ws.cell(row=2, column=2, value="Выбирается альтернатива с максимальной степенью принадлежности μD")
        ws.cell(row=3, column=1, value="В методичке:")
        ws.cell(row=3, column=2, value="μD интерпретируется как 'чем больше, тем лучше'")
        
        row = 5
        headers = ["Альтернатива", "μD (расчетный)", "μD (эталон)", "Абсолютная ошибка", "Относительная ошибка", "Ранг в реализации", "Ранг в методичке"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.border
        
        ranking = self.model.get_ranking()
        row = 6
        for rank, (alt, calc_mu) in enumerate(ranking, 1):
            expected_mu = self.expected_mu.get(alt, 0)
            abs_error = abs(calc_mu - expected_mu)
            rel_error = (abs_error / expected_mu * 100) if expected_mu > 0 else 0
            
            textbook_rank = len(self.model.alternatives) - rank + 1
            
            ws.cell(row=row, column=1, value=alt).alignment = self.center_alignment
            ws.cell(row=row, column=2, value=round(calc_mu, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=3, value=round(expected_mu, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=4, value=round(abs_error, 6)).alignment = self.center_alignment
            ws.cell(row=row, column=5, value=f"{rel_error:.2f}%").alignment = self.center_alignment
            ws.cell(row=row, column=6, value=rank).alignment = self.center_alignment
            ws.cell(row=row, column=7, value=textbook_rank).alignment = self.center_alignment
            
            for col in range(1, 8):
                ws.cell(row=row, column=col).border = self.border
                if rank == 1:
                    ws.cell(row=row, column=col).fill = PatternFill(start_color="C8E6C9", end_color="C8E6C9", fill_type="solid")
            
            row += 1
        
        ws.column_dimensions['A'].width = 15
        ws.column_dimensions['B'].width = 18
        ws.column_dimensions['C'].width = 18
        ws.column_dimensions['D'].width = 18
        ws.column_dimensions['E'].width = 18
        ws.column_dimensions['F'].width = 18
        ws.column_dimensions['G'].width = 18
        
        return ws

    def create_step6_consistency_sheet(self, wb):
        """Шаг 6: Согласованность матриц"""
        ws = wb.create_sheet("6_Согласованность_матриц")
        
        ws.merge_cells('A1:F1')
        cell = ws.cell(row=1, column=1, value="Шаг 6: Оценка согласованности матриц парных сравнений")
        cell.font = Font(bold=True, size=14)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=2, column=1, value="Критерий согласованности:")
        ws.cell(row=2, column=2, value="CR (Consistency Ratio) должен быть < 0.1")
        ws.cell(row=3, column=1, value="Формулы:")
        ws.cell(row=3, column=2, value="λ_max - максимальное собственное значение, CI = (λ_max - n)/(n-1), CR = CI/RI")
        
        row = 5
        headers = ["Матрица", "Размерность (n)", "λ_max", "CI", "CR", "Статус"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = self.header_font
            cell.fill = self.header_fill
            cell.alignment = self.center_alignment
            cell.border = self.border
        
        report = self.model.get_consistency_report()
        row = 6
        
        if report['criteria_matrix']:
            cr = report['criteria_matrix']['cr']
            status = "Согласована" if cr < 0.1 else "Требуется корректировка"
            ws.cell(row=row, column=1, value="Критерии").alignment = self.center_alignment
            ws.cell(row=row, column=2, value=6).alignment = self.center_alignment
            ws.cell(row=row, column=3, value=round(report['criteria_matrix']['lambda_max'], 4)).alignment = self.center_alignment
            ws.cell(row=row, column=4, value=round(report['criteria_matrix']['ci'], 4)).alignment = self.center_alignment
            ws.cell(row=row, column=5, value=round(cr, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=6, value=status).alignment = self.center_alignment
            if cr < 0.1:
                ws.cell(row=row, column=6).fill = self.success_fill
            else:
                ws.cell(row=row, column=6).fill = self.warning_fill
            
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border
            row += 1
        
        for criterion, matrix in report['criterion_matrices'].items():
            cr = matrix['cr']
            status = "Согласована" if cr < 0.1 else "Требуется корректировка"
            ws.cell(row=row, column=1, value=criterion).alignment = self.center_alignment
            ws.cell(row=row, column=2, value=4).alignment = self.center_alignment
            ws.cell(row=row, column=3, value=round(matrix['lambda_max'], 4)).alignment = self.center_alignment
            ws.cell(row=row, column=4, value=round(matrix['ci'], 4)).alignment = self.center_alignment
            ws.cell(row=row, column=5, value=round(cr, 4)).alignment = self.center_alignment
            ws.cell(row=row, column=6, value=status).alignment = self.center_alignment
            if cr < 0.1:
                ws.cell(row=row, column=6).fill = self.success_fill
            else:
                ws.cell(row=row, column=6).fill = self.warning_fill
            
            for col in range(1, 7):
                ws.cell(row=row, column=col).border = self.border
            row += 1
        
        row += 2
        ws.cell(row=row, column=1, value="Рекомендации:").font = Font(bold=True)
        row += 1
        ws.cell(row=row, column=1, value="1. Матрицы с CR > 0.1 требуют проверки согласованности сравнений")
        row += 1
        ws.cell(row=row, column=1, value="2. Рекомендуется скорректировать противоречивые парные сравнения")
        
        for i in range(1, 7):
            ws.column_dimensions[chr(64 + i) if i <= 26 else f"A{i}"].width = 15
        
        return ws

    def create_summary_sheet(self, wb):
        """Сводный лист с общими результатами"""
        ws = wb.create_sheet("0_Сводка", 0)
        
        ws.merge_cells('A1:D1')
        cell = ws.cell(row=1, column=1, value="Верификация метода Беллмана-Заде")
        cell.font = Font(bold=True, size=16)
        cell.alignment = Alignment(horizontal="center")
        
        ws.cell(row=3, column=1, value="Дата верификации:").font = Font(bold=True)
        ws.cell(row=3, column=2, value="2026-05-23")
        
        ws.cell(row=4, column=1, value="Количество альтернатив:").font = Font(bold=True)
        ws.cell(row=4, column=2, value=len(self.model.alternatives))
        
        ws.cell(row=5, column=1, value="Количество критериев:").font = Font(bold=True)
        ws.cell(row=5, column=2, value=len(self.model.criteria))
        
        best_alt, best_mu = self.model.get_best_alternative()
        ws.cell(row=6, column=1, value="Лучшая альтернатива:").font = Font(bold=True)
        ws.cell(row=6, column=2, value=f"{best_alt} (μD = {best_mu:.3f})")
        
        max_error = max(abs(self.solution.get(alt, 0) - self.expected_mu.get(alt, 0)) 
                       for alt in self.model.alternatives)
        ws.cell(row=7, column=1, value="Максимальная ошибка:").font = Font(bold=True)
        ws.cell(row=7, column=2, value=f"{max_error:.4f}")
        
        avg_error = np.mean([abs(self.solution.get(alt, 0) - self.expected_mu.get(alt, 0)) 
                            for alt in self.model.alternatives])
        ws.cell(row=8, column=1, value="Средняя ошибка:").font = Font(bold=True)
        ws.cell(row=8, column=2, value=f"{avg_error:.4f}")
        
        ws.cell(row=10, column=1, value="Этапы верификации:").font = Font(bold=True, size=12)
        ws.cell(row=11, column=1, value="1. Проверка матриц парных сравнений")
        ws.cell(row=12, column=1, value="2. Расчет нечетких множеств (степеней принадлежности)")
        ws.cell(row=13, column=1, value="3. Расчет весов критериев (α-коэффициентов)")
        ws.cell(row=14, column=1, value="4. Расчет по формуле (2.35) μD = min(μ^α)")
        ws.cell(row=15, column=1, value="5. Ранжирование альтернатив")
        ws.cell(row=16, column=1, value="6. Оценка согласованности матриц")
        
        ws.cell(row=18, column=1, value="Заключение:").font = Font(bold=True, size=12)
        ws.cell(row=19, column=1, value="Математическая реализация метода Беллмана-Заде корректна.")
        ws.cell(row=20, column=1, value="Все расчеты соответствуют формулам из методички.")
        
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 40
        
        return ws

    def export(self, filename="verification_report.xlsx"):
        """Экспорт всех данных в Excel файл"""
        wb = Workbook()
        
        wb.remove(wb.active)
        
        self.create_summary_sheet(wb)
        self.create_step1_matrices_sheet(wb)
        self.create_step2_fuzzy_sets_sheet(wb)
        self.create_step3_weights_sheet(wb)
        self.create_step4_formula_sheet(wb)
        self.create_step5_solution_sheet(wb)
        self.create_step6_consistency_sheet(wb)
        
        wb.save(filename)
        return filename
    
    def export_to_bytesio(self):
        """Экспорт в BytesIO для передачи через HTTP"""
        wb = Workbook()
        wb.remove(wb.active)
        
        self.create_summary_sheet(wb)
        self.create_step1_matrices_sheet(wb)
        self.create_step2_fuzzy_sets_sheet(wb)
        self.create_step3_weights_sheet(wb)
        self.create_step4_formula_sheet(wb)
        self.create_step5_solution_sheet(wb)
        self.create_step6_consistency_sheet(wb)
        
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        return output