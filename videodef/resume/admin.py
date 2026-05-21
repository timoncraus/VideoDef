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


class CriteriaComparisonInline(admin.TabularInline):
    """Инлайн для сравнения критериев"""
    model = FuzzyComparisonSettings
    can_delete = False
    verbose_name = "Сравнение критериев"
    verbose_name_plural = "Сравнения критериев"
    
    def get_formset(self, request, obj=None, **kwargs):
        class CriteriaComparisonFormset(forms.BaseInlineFormSet):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                # Динамическое создание полей для сравнений
                pass
        return CriteriaComparisonFormset


@admin.register(FuzzyComparisonSettings)
class FuzzyComparisonSettingsAdmin(admin.ModelAdmin):
    """Красивый админ для настройки парных сравнений"""
    
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
        ('📋 Матрицы парных сравнений АЛЬТЕРНАТИВ по критериям', {
            'fields': ('alternatives_matrices_html',),
            'description': 'Для каждого критерия заполните матрицу парных сравнений преподавателей',
            'classes': ('wide',)
        }),
        ('📈 Результаты расчета', {
            'fields': ('calculated_weights_html', 'consistency_report_html'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('criteria_matrix_html', 'alternatives_matrices_html', 
                      'calculated_weights_html', 'consistency_report_html')
    
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
    
    def alternatives_matrices_html(self, obj):
        """Генерация HTML для матриц альтернатив по каждому критерию"""
        from resume.models import Resume
        
        criteria = ['price', 'distance', 'experience', 'rating', 'education']
        criteria_names = {
            'price': '💰 Цена занятия',
            'distance': '📍 Расстояние',
            'experience': '⏳ Опыт работы',
            'rating': '⭐ Рейтинг',
            'education': '🎓 Образование'
        }
        
        # Получаем список преподавателей
        teachers = Resume.objects.filter(status='active').select_related('user__profile')
        teacher_choices = [(f"T_{t.id}", t.user.profile.get_full_name() or f"Преподаватель {t.id}") for t in teachers]
        
        # Загружаем сохраненные сравнения
        saved_comparisons = {}
        if obj and obj.alternative_comparisons:
            import json
            try:
                saved = json.loads(obj.alternative_comparisons)
                for criterion, comps in saved.items():
                    saved_comparisons[criterion] = {}
                    for comp in comps:
                        key = f"{comp['alt1']}_{comp['alt2']}"
                        saved_comparisons[criterion][key] = comp.get('value', 1)
            except:
                pass
        
        html = '<div class="alternatives-matrices">'
        
        for criterion in criteria:
            html += f'''
                <div class="criterion-matrix card">
                    <h3>{criteria_names.get(criterion, criterion)}</h3>
                    <table class="matrix-table">
                        <thead>
                            <tr>
                                <th>Преподаватель A</th>
                                <th>Сравнение</th>
                                <th>Преподаватель B</th>
                                <th>Значение (1/9 - 9)</th>
                            </tr>
                        </thead>
                        <tbody>
            '''
            
            for i, (alt1, name1) in enumerate(teacher_choices):
                for j, (alt2, name2) in enumerate(teacher_choices):
                    if i < j:
                        key = f"{alt1}_{alt2}"
                        current_value = saved_comparisons.get(criterion, {}).get(key, 1)
                        html += f'''
                            <tr>
                                <td>{name1}</td>
                                <td>по сравнению с</td>
                                <td>{name2}</td>
                                <td>
                                    <select name="alt_comp_{criterion}_{alt1}_{alt2}" class="saaty-select"
                                            onchange="updateAlternativesMatrix('{criterion}')">
                                        <option value="1/9" {('selected' if current_value == 1/9 else '')}>1/9</option>
                                        <option value="1/8" {('selected' if current_value == 1/8 else '')}>1/8</option>
                                        <option value="1/7" {('selected' if current_value == 1/7 else '')}>1/7</option>
                                        <option value="1/6" {('selected' if current_value == 1/6 else '')}>1/6</option>
                                        <option value="1/5" {('selected' if current_value == 1/5 else '')}>1/5</option>
                                        <option value="1/4" {('selected' if current_value == 1/4 else '')}>1/4</option>
                                        <option value="1/3" {('selected' if current_value == 1/3 else '')}>1/3</option>
                                        <option value="1/2" {('selected' if current_value == 1/2 else '')}>1/2</option>
                                        <option value="1" {('selected' if current_value == 1 else '')}>1 - Равны</option>
                                        <option value="2" {('selected' if current_value == 2 else '')}>2</option>
                                        <option value="3" {('selected' if current_value == 3 else '')}>3</option>
                                        <option value="4" {('selected' if current_value == 4 else '')}>4</option>
                                        <option value="5" {('selected' if current_value == 5 else '')}>5</option>
                                        <option value="6" {('selected' if current_value == 6 else '')}>6</option>
                                        <option value="7" {('selected' if current_value == 7 else '')}>7</option>
                                        <option value="8" {('selected' if current_value == 8 else '')}>8</option>
                                        <option value="9" {('selected' if current_value == 9 else '')}>9</option>
                                    </select>
                                </td>
                            </tr>
                        '''
            
            html += '''
                        </tbody>
                    </table>
                    <button type="button" class="button" onclick="calculateAlternativesWeights('{}')">📊 Рассчитать нечеткие множества</button>
                    <div id="alternatives-weights-result-{}" class="calculation-result"></div>
                </div>
            '''.format(criterion, criterion)
        
        html += '</div>'
        return format_html(html)
    
    def calculated_weights_html(self, obj):
        """Отображение рассчитанных весов"""
        if not obj or not obj.criteria_weights:
            return format_html('<p class="text-muted">Нажмите "Рассчитать" для получения весов критериев</p>')
        
        import json
        try:
            weights = json.loads(obj.criteria_weights)
            html = '<table class="weights-table"><tr><th>Критерий</th><th>Вес (α)</th></tr>'
            for criterion, weight in weights.items():
                html += f'<tr><td>{criterion}</td><td><strong>{weight:.4f}</strong></td></tr>'
            html += '</table>'
            return format_html(html)
        except:
            return format_html('<p class="text-danger">Ошибка загрузки весов</p>')
    
    def consistency_report_html(self, obj):
        """Отображение отчета о согласованности"""
        if not obj:
            return format_html('<p class="text-muted">Нет данных</p>')
        
        # Здесь можно добавить расчет CR из сохраненных данных
        return format_html('''
            <div class="consistency-info">
                <p>Индекс согласованности (CR) должен быть &lt; 0.1 для согласованной матрицы</p>
                <button type="button" class="button" onclick="checkConsistency()">✓ Проверить согласованность</button>
                <div id="consistency-result"></div>
            </div>
        ''')
    
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
        
        # Собираем сравнения альтернатив
        alternative_comparisons = {}
        for key, value in request.POST.items():
            if key.startswith('alt_comp_'):
                parts = key.split('_')
                if len(parts) >= 5:
                    criterion = parts[2]
                    alt1 = parts[3]
                    alt2 = parts[4]
                    
                    if '/' in value:
                        num, den = value.split('/')
                        value_num = float(num) / float(den)
                    else:
                        value_num = float(value)
                    
                    if criterion not in alternative_comparisons:
                        alternative_comparisons[criterion] = []
                    alternative_comparisons[criterion].append({
                        'alt1': alt1,
                        'alt2': alt2,
                        'linguistic_value': value,
                        'value': value_num
                    })
        
        obj.criteria_comparisons = json.dumps(criteria_comparisons, ensure_ascii=False)
        obj.alternative_comparisons = json.dumps(alternative_comparisons, ensure_ascii=False)
        obj.use_expert_comparisons = request.POST.get('use_expert_comparisons') == 'on'
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        """Добавляем кастомный JS/CSS для матриц"""
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = True
        return super().changeform_view(request, object_id, form_url, extra_context)


# Регистрируем остальные модели
@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'experience_years', 'rating', 'created_at']
    list_filter = ['status', 'violation_types']
    search_fields = ['user__username', 'user__profile__first_name', 'user__profile__last_name']


@admin.register(ViolationType)
class ViolationTypeAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']


@admin.register(TeacherReview)
class TeacherReviewAdmin(admin.ModelAdmin):
    list_display = ['id', 'teacher', 'parent', 'rating', 'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating']
    actions = ['approve_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Одобрить выбранные отзывы"