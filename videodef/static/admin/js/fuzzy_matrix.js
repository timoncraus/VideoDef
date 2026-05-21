// static/admin/js/fuzzy_matrix.js - исправленная версия

function calculateCriteriaWeights() {
    // Собираем все сравнения
    const comparisons = {};
    document.querySelectorAll('[name^="criteria_comp_"]').forEach(select => {
        const name = select.name;
        let value = select.value;
        
        // Преобразуем значение в число
        if (value.includes('/')) {
            const [num, den] = value.split('/');
            value = parseFloat(num) / parseFloat(den);
        } else {
            value = parseFloat(value);
        }
        comparisons[name] = value;
    });
    
    console.log('Отправляемые сравнения:', comparisons);
    
    // Отправляем AJAX запрос для расчета
    fetch('/resumes/api/calculate-criteria-weights/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({comparisons: comparisons})
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Response error:', text);
                throw new Error(`HTTP ${response.status}: ${text}`);
            });
        }
        return response.json();
    })
    .then(data => {
        const resultDiv = document.getElementById('criteria-weights-result');
        if (data.error) {
            resultDiv.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
            return;
        }
        
        if (data.weights) {
            let html = '<h4>📊 Результаты расчета весов критериев (α-коэффициенты):</h4>';
            html += '<table class="weights-table">';
            html += '<tr><th>Критерий</th><th>Вес (α)</th><th>Важность</th></tr>';
            
            const sorted = Object.entries(data.weights).sort((a, b) => b[1] - a[1]);
            for (const [criterion, weight] of sorted) {
                const percent = (weight * 100).toFixed(1);
                let importance = '';
                if (weight > 0.3) importance = '🔥 Высокая';
                else if (weight > 0.2) importance = '⭐ Средняя';
                else importance = '📉 Низкая';
                
                html += `<tr>
                    <td><strong>${getCriterionName(criterion)}</strong></td>
                    <td><strong>${weight.toFixed(4)}</strong> (${percent}%)</td>
                    <td>${importance}</td>
                </tr>`;
            }
            html += '</table>';
            
            const crColor = data.cr < 0.1 ? '#4CAF50' : '#f44336';
            const crStatus = data.cr < 0.1 ? '✓ Согласована' : '✗ НЕ согласована (требуется корректировка)';
            html += `<div style="margin-top: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                <strong>Индекс согласованности (CR):</strong> 
                <span style="color: ${crColor}; font-weight: bold;">${data.cr.toFixed(4)}</span> - ${crStatus}
            </div>`;
            
            resultDiv.innerHTML = html;
            resultDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const resultDiv = document.getElementById('criteria-weights-result');
        resultDiv.innerHTML = `<div class="error">Ошибка при расчете: ${error.message}</div>`;
    });
}

function calculateAlternativesWeights(criterion) {
    const comparisons = {};
    document.querySelectorAll(`[name^="alt_comp_${criterion}_"]`).forEach(select => {
        const name = select.name;
        let value = select.value;
        if (value.includes('/')) {
            const [num, den] = value.split('/');
            value = parseFloat(num) / parseFloat(den);
        } else {
            value = parseFloat(value);
        }
        comparisons[name] = value;
    });
    
    console.log(`Отправляемые сравнения для критерия ${criterion}:`, comparisons);
    
    fetch('/resumes/api/calculate-alternatives-weights/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({criterion: criterion, comparisons: comparisons})
    })
    .then(response => {
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Response error:', text);
                throw new Error(`HTTP ${response.status}`);
            });
        }
        return response.json();
    })
    .then(data => {
        const resultDiv = document.getElementById(`alternatives-weights-result-${criterion}`);
        if (data.error) {
            resultDiv.innerHTML = `<div class="error">Ошибка: ${data.error}</div>`;
            return;
        }
        
        if (data.weights) {
            let html = '<h4>📊 Нечеткое множество G (степени принадлежности):</h4>';
            html += '<table class="weights-table">';
            html += '<tr><th>Преподаватель</th><th>Степень принадлежности</th><th>Рейтинг</th></tr>';
            
            const sorted = Object.entries(data.weights).sort((a, b) => b[1] - a[1]);
            for (const [name, weight] of sorted) {
                const percent = (weight * 100).toFixed(1);
                let barColor = '#4CAF50';
                if (weight < 0.3) barColor = '#f44336';
                else if (weight < 0.5) barColor = '#FF9800';
                
                html += `<tr>
                    <td>${name}</td>
                    <td>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <div style="flex: 1; background: #e0e0e0; height: 20px; border-radius: 10px; overflow: hidden;">
                                <div style="width: ${percent}%; background: ${barColor}; height: 100%;"></div>
                            </div>
                            <span><strong>${percent}%</strong></span>
                        </div>
                    </td>
                    <td>${getRankIcon(weight)}</td>
                </tr>`;
            }
            html += '</table>';
            
            if (data.consistency) {
                const crColor = data.consistency.cr < 0.1 ? '#4CAF50' : '#f44336';
                html += `<div style="margin-top: 10px; font-size: 12px; color: #666;">
                    CR = <span style="color: ${crColor}">${data.consistency.cr.toFixed(4)}</span>
                    ${data.consistency.cr < 0.1 ? '✓' : '✗'}
                </div>`;
            }
            
            resultDiv.innerHTML = html;
            resultDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const resultDiv = document.getElementById(`alternatives-weights-result-${criterion}`);
        resultDiv.innerHTML = `<div class="error">Ошибка при расчете: ${error.message}</div>`;
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getCriterionName(criterion) {
    const names = {
        'price': '💰 Цена занятия',
        'distance': '📍 Расстояние',
        'experience': '⏳ Опыт работы',
        'rating': '⭐ Рейтинг',
        'education': '🎓 Образование'
    };
    return names[criterion] || criterion;
}

function getRankIcon(weight) {
    if (weight >= 0.8) return '🏆 Отлично';
    if (weight >= 0.6) return '👍 Хорошо';
    if (weight >= 0.4) return '👌 Средне';
    if (weight >= 0.2) return '⚠️ Ниже среднего';
    return '❌ Плохо';
}