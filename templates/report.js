
// Получить данные отчета из Flask-приложения
const reportData = {{ report_data|tojson|safe }};

// Получить уникальные даты отчетов
const uniqueReportDates = [...new Set(reportData.map(entry => entry.report_date))];

// Добавить уникальные даты отчетов в выпадающий список
const reportDateSelect = document.getElementById('report-date-select');
uniqueReportDates.forEach(date => {
    const option = document.createElement('option');
    option.value = date;
    option.textContent = date;
    reportDateSelect.appendChild(option);
});

// Функция для отображения отфильтрованных данных
function displayData(selectedDate) {
    const tableBody = document.querySelector('table tbody');
    tableBody.innerHTML = '';
    
    const filteredData = selectedDate === 'all'
        ? reportData
        : reportData.filter(entry => entry.report_date === selectedDate);
        
    filteredData.forEach(entry => {
        const row = tableBody.insertRow();
        
        // Добавьте ячейки таблицы для каждого столбца, кроме 'report_date'
        for (const key in entry) {
            if (key !== 'report_date') {
                const cell = row.insertCell();
                cell.textContent = entry[key];
            }
        }
    });
}

// Обновить данные таблицы при изменении значения выпадающего списка
reportDateSelect.addEventListener('change', () => {
    displayData(reportDateSelect.value);
});

// Отобразить все данные по умолчанию
displayData('all');
