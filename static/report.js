const reportDataTag = document.getElementById('report-data-tag');
const reportData = JSON.parse(reportDataTag.textContent);

// Устанавливаем daterangepicker
const reportDateRange = document.getElementById('report-date-range');
$(reportDateRange).daterangepicker({
    locale: {
        format: 'DD-MM-YYYY'
    },
    opens: 'right'
});

function displayDataByDateRange(startDate, endDate) {
    const tableBody = document.querySelector('#report-table tbody');
    tableBody.innerHTML = '';

    const filteredData = reportData.filter(entry => {
        const entryDate = moment(entry.creation_date, 'DD-MM-YYYY');
        return entryDate.isBetween(startDate, endDate, undefined, '[]');
    });

    displayData(filteredData);
}

$(reportDateRange).on('apply.daterangepicker', function (ev, picker) {
    displayDataByDateRange(picker.startDate, picker.endDate);
});

// Функция для отображения данных
function displayData(data) {
    const tableBody = document.querySelector('#report-table tbody');
    tableBody.innerHTML = '';

    data.forEach(entry => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${entry.ticket_id}</td>
            <td>${entry.subject}</td>
            <td>${entry.creation_date}</td>
            <td>${entry.status}</td>
            <td>${entry.client_name}</td>
            <td>${entry.priority}</td>
            <td>${entry.assignee_name}</td>
            <td>${entry.updated_at}</td>
            <td>${entry.last_reply_at}</td>
            <td>${entry.sla}</td>
            <td>${entry.sla_time}</td>
            <td>${entry.response_time}</td>
            <td>${entry.cause}</td>
            <td>${entry.module_boardmaps}</td>
            <td>${entry.staff_message}</td>
        `;
        tableBody.appendChild(row);
    });

    // Обновляем график после фильтрации
    updateChartData(data);
}

// Изначально показываем данные за весь период
const startDate = moment.min(reportData.map(entry => moment(entry.creation_date, 'DD-MM-YYYY')));
const endDate = moment.max(reportData.map(entry => moment(entry.creation_date, 'DD-MM-YYYY')));
$(reportDateRange).data('daterangepicker').setStartDate(startDate);
$(reportDateRange).data('daterangepicker').setEndDate(endDate);
displayDataByDateRange(startDate, endDate);
