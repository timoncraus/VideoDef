# resume/admin.py

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.db import models
from django import forms
from .models import (
    Resume, ViolationType, TeacherReview, 
    FuzzyComparisonSettings, ExpertMatrixSettings
)
from .bellman_zade import ComparisonMatrix, SaatyScale


@admin.register(FuzzyComparisonSettings)
class FuzzyComparisonSettingsAdmin(admin.ModelAdmin):
    """Админ для настройки парных сравнений - только критерии"""
    
    fieldsets = (
        ('📊 Настройка метода Беллмана-Заде', {
            'fields': ('use_expert_comparisons',),
            'description': 'Включите эту опцию для использования ручных экспертных сравнений'
        }),
        ('🎯 Матрица парных сравнений КРИТЕРИЕВ', {
            'fields': ('criteria_matrix_html',),
            'description': 'Заполните матрицу парных сравнений для определения важности критериев (по шкале Саати 1-9)',
            'classes': ('wide',)
        }),
    )
    
    # ИСПРАВЛЕНО: readonly_fields должен быть кортежем
    readonly_fields = ('criteria_matrix_html',)
    
    class Media:
        css = {
            'all': ('admin/css/fuzzy_matrix.css',)
        }
        js = ('admin/js/fuzzy_matrix.js',)
    
    def criteria_matrix_html(self, obj):
        """Генерация HTML для матрицы критериев"""
        criteria = ['price', 'distance', 'experience', 'rating', 'education']
        criteria_names = {
            'price': '💰 Цена занятия',
            'distance': '📍 Расстояние',
            'experience': '⏳ Опыт работы',
            'rating': '⭐ Рейтинг',
            'education': '🎓 Образование'
        }
        
        # Загружаем сохраненные сравнения
        saved_comparisons = {}
        if obj and obj.criteria_comparisons:
            import json
            try:
                saved = json.loads(obj.criteria_comparisons)
                for comp in saved:
                    key = f"{comp['criterion1']}_{comp['criterion2']}"
                    saved_comparisons[key] = comp.get('value', 1)
            except:
                pass
        
        html = '''
        <div class="matrix-container">
            <h4>Шкала Саати для сравнений:</h4>
            <table class="saaty-scale">
                <tr><td>1</td><td>- Одинаковая важность</td></tr>
                <tr><td>2</td><td>- Почти слабое преимущество</td></tr>
                <tr><td>3</td><td>- Слабое преимущество</td></tr>
                <tr><td>4</td><td>- Почти существенное преимущество</td></tr>
                <tr><td>5</td><td>- Существенное преимущество</td></tr>
                <tr><td>6</td><td>- Почти сильное преимущество</td></tr>
                <tr><td>7</td><td>- Явное преимущество</td></tr>
                <tr><td>8</td><td>- Очень сильное преимущество</td></tr>
                <tr><td>9</td><td>- Абсолютное преимущество</td></tr>
            </table>
            
            <table class="matrix-table">
                <thead>
                    <tr>
                        <th>Критерий A</th>
                        <th>Сравнение</th>
                        <th>Критерий B</th>
                        <th>Значение (1/9 - 9)</th>
                    </tr>
                </thead>
                <tbody>
        '''
        
        for i, crit1 in enumerate(criteria):
            for j, crit2 in enumerate(criteria):
                if i < j:
                    key = f"{crit1}_{crit2}"
                    current_value = saved_comparisons.get(key, 1)
                    html += f'''
                        <tr>
                            <td><strong>{criteria_names.get(crit1, crit1)}</strong></td>
                            <td>по сравнению с</td>
                            <td><strong>{criteria_names.get(crit2, crit2)}</strong></td>
                            <td>
                                <select name="criteria_comp_{crit1}_{crit2}" class="saaty-select" 
                                        onchange="updateCriteriaMatrix()">
                                    <option value="1/9" {('selected' if current_value == 1/9 else '')}>1/9 - Абсолютно хуже</option>
                                    <option value="1/8" {('selected' if current_value == 1/8 else '')}>1/8 - Очень сильно хуже</option>
                                    <option value="1/7" {('selected' if current_value == 1/7 else '')}>1/7 - Явно хуже</option>
                                    <option value="1/6" {('selected' if current_value == 1/6 else '')}>1/6</option>
                                    <option value="1/5" {('selected' if current_value == 1/5 else '')}>1/5 - Существенно хуже</option>
                                    <option value="1/4" {('selected' if current_value == 1/4 else '')}>1/4</option>
                                    <option value="1/3" {('selected' if current_value == 1/3 else '')}>1/3 - Слабо хуже</option>
                                    <option value="1/2" {('selected' if current_value == 1/2 else '')}>1/2</option>
                                    <option value="1" {('selected' if current_value == 1 else '')}>1 - Равны</option>
                                    <option value="2" {('selected' if current_value == 2 else '')}>2</option>
                                    <option value="3" {('selected' if current_value == 3 else '')}>3 - Слабо лучше</option>
                                    <option value="4" {('selected' if current_value == 4 else '')}>4</option>
                                    <option value="5" {('selected' if current_value == 5 else '')}>5 - Существенно лучше</option>
                                    <option value="6" {('selected' if current_value == 6 else '')}>6</option>
                                    <option value="7" {('selected' if current_value == 7 else '')}>7 - Явно лучше</option>
                                    <option value="8" {('selected' if current_value == 8 else '')}>8</option>
                                    <option value="9" {('selected' if current_value == 9 else '')}>9 - Абсолютно лучше</option>
                                </select>
                            </td>
                        </tr>
                    '''
        
        html += '''
                </tbody>
             </table>
            <button type="button" class="button" onclick="calculateCriteriaWeights()">📊 Рассчитать веса критериев</button>
            <div id="criteria-weights-result" class="calculation-result"></div>
        </div>
        '''
        
        return format_html(html)
    
    def save_model(self, request, obj, form, change):
        """Сохранение настроек из POST-запроса"""
        import json
        
        # Собираем сравнения критериев
        criteria_comparisons = []
        for key, value in request.POST.items():
            if key.startswith('criteria_comp_'):
                parts = key.split('_')
                if len(parts) >= 4:
                    # Преобразуем строковое значение в число
                    if '/' in value:
                        num, den = value.split('/')
                        value_num = float(num) / float(den)
                    else:
                        value_num = float(value)
                    
                    criteria_comparisons.append({
                        'criterion1': parts[2],
                        'criterion2': parts[3],
                        'linguistic_value': value,
                        'value': value_num
                    })
        
        obj.criteria_comparisons = json.dumps(criteria_comparisons, ensure_ascii=False)
        obj.use_expert_comparisons = request.POST.get('use_expert_comparisons') == 'on'
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем кастомный JS/CSS для матриц"""
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = True
        return super().changeform_view(request, object_id, form_url, extra_context)


# ИСПРАВЛЕН ResumeAdmin - убрано поле rating
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'experience_years', 'created_at']
    list_filter = ['status', 'violation_types']
    search_fields = ['user__username', 'user__profile__first_name', 'user__profile__last_name']


@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']



@admin.register(TeacherReview)
class TeacherReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'teacher', 'parent', 'rating', 'created_at']
    list_filter = ['rating']
    search_fields = ['teacher__username', 'parent__username', 'comment']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher__profile', 'parent__profile')