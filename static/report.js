// Устанавливаем daterangepicker
const reportDateRange = document.getElementById('report-date-range');
$(reportDateRange).daterangepicker({
    locale: {
        format: 'YYYY-MM-DD'
    },
    opens: 'right'
});

function displayDataByDateRange(startDate, endDate) {
    // Запрашиваем данные с сервера с переданными параметрами даты
    fetch(`/api/report/${startDate.format('YYYY-MM-DD')}/${endDate.format('YYYY-MM-DD')}`)
        .then(response => response.json())
        .then(data => {
            // Отображаем отфильтрованные данные
            displayData(data);
        });
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

function updateChartData(filteredData) {
    let causeCount = {};

    filteredData.forEach(entry => {
        const cause = entry.cause;
        causeCount[cause] = (causeCount[cause] || 0) + 1;
    });

    chart.data.labels = Object.keys(causeCount);
    chart.data.datasets[0].data = Object.values(causeCount);
    chart.update();
}

// Изначально показываем данные за текущую неделю
const thisMonday = moment().startOf('week').add(1, 'days'); // Начало текущей недели, понедельник
const today = moment(); // Сегодняшний день

$(reportDateRange).data('daterangepicker').setStartDate(thisMonday);
$(reportDateRange).data('daterangepicker').setEndDate(today);
displayDataByDateRange(thisMonday, today);
