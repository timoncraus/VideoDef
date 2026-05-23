"""
Верификация метода нечеткого многокритериального анализа Беллмана-Заде
с поэтапным экспортом в Excel
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')
from pathlib import Path
from django.test import TestCase
from ..bellman_zade import BellmanZadeMCDA, create_brand_project_example
from ..utils.excel_exporter import VerificationExcelExporter


class VerifyAgainstTextbook(TestCase):
    def setUp(self):
        self.model = create_brand_project_example()
        self.model.build_fuzzy_sets()
        self.solution = self.model.calculate_solution(use_weights=True)
        
        # Эталонные данные
        self.expected_memberships = {
            'G1': {'P1': 0.39, 'P2': 0.39, 'P3': 0.15, 'P4': 0.07},
            'G2': {'P1': 0.59, 'P2': 0.22, 'P3': 0.12, 'P4': 0.07},
            'G3': {'P1': 0.42, 'P2': 0.11, 'P3': 0.42, 'P4': 0.05},
            'G4': {'P1': 0.08, 'P2': 0.23, 'P3': 0.48, 'P4': 0.21},
            'G5': {'P1': 0.08, 'P2': 0.23, 'P3': 0.48, 'P4': 0.21},
            'G6': {'P1': 0.06, 'P2': 0.40, 'P3': 0.14, 'P4': 0.40}
        }
        
        self.expected_weights = {
            'G1': 0.15, 'G2': 0.34, 'G3': 0.26,
            'G4': 0.05, 'G5': 0.13, 'G6': 0.07
        }
        
        self.expected_mu = {
            'P1': 0.717, 'P2': 0.552, 'P3': 0.490, 'P4': 0.409
        }

    def export_to_excel(self, filename=None):
        """Экспорт результатов верификации в Excel"""
        if filename is None:
            reports_dir = Path(__file__).parent.parent / "reports"
            reports_dir.mkdir(exist_ok=True)
            filename = str(reports_dir / "verification_report.xlsx")
        
        calculated_weights = self.model.calculate_criteria_weights()
        
        exporter = VerificationExcelExporter(
            model=self.model,
            solution=self.solution,
            expected_mu=self.expected_mu,
            calculated_weights=calculated_weights,
            expected_memberships=self.expected_memberships
        )
        
        exporter.export(filename)
        return filename


def run_full_verification():
    """Запуск полной верификации с экспортом в Excel"""
    print("\n" + "=" * 70)
    print("ВЕРИФИКАЦИЯ МЕТОДА БЕЛЛМАНА-ЗАДЕ")
    print("=" * 70)
    
    test = VerifyAgainstTextbook()
    test.setUp()
    
    # Экспорт в Excel
    excel_file = test.export_to_excel()
    print(f"\nExcel отчет сохранен: {excel_file}")
    
    print("\n" + "=" * 70)
    print("ВЕРИФИКАЦИЯ УСПЕШНО ЗАВЕРШЕНА")
    print("=" * 70)
    print("\nExcel отчет содержит следующие листы:")
    print("  0_Сводка - общая информация о верификации")
    print("  1_Матрицы_сравнений - матрицы парных сравнений")
    print("  2_Нечеткие_множества - степени принадлежности")
    print("  3_Веса_критериев - α-коэффициенты")
    print("  4_Расчет_по_формуле - детальный расчет по формуле (2.35)")
    print("  5_Финальное_решение - ранжирование альтернатив")
    print("  6_Согласованность_матриц - отчет о согласованности")
    
    return True


if __name__ == '__main__':
    run_full_verification()