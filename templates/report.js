const reportData = {{ report_data|tojson|safe }};

const uniqueReportDates = [...new Set(reportData.map(entry => entry.report_date))];

const reportDateSelect = document.getElementById('report-date-select');
uniqueReportDates.forEach(date => {
    const option = document.createElement('option');
    option.value = date;
    option.textContent = date;
    reportDateSelect.appendChild(option);
});

function displayData(selectedDate) {
    const tableBody = document.querySelector('table tbody');
    tableBody.innerHTML = '';

    const filteredData = selectedDate === 'all'
        ? reportData
        : reportData.filter(entry => entry.report_date === selectedDate);

    filteredData.forEach(entry => {
        const row = tableBody.insertRow();

        for (const key in entry) {
            if (key !== 'report_date') {
                const cell = row.insertCell();
                cell.textContent = entry[key];
            }
        }
    });
}

reportDateSelect.addEventListener('change', () => {
    displayData(reportDateSelect.value);
});

displayData('all');
