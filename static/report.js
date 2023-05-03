const reportDataTag = document.getElementById('report-data');
const reportData = JSON.parse(reportDataTag.textContent);

const uniqueReportDates = [...new Set(reportData.map(entry => entry.report_date))];

const reportDateSelect = document.getElementById('report-date-select');
uniqueReportDates.forEach(date => {
    const option = document.createElement('option');
    option.value = date;
    option.textContent = date;
    reportDateSelect.appendChild(option);
});

reportDateSelect.addEventListener('change', () => {
    const selectedDate = reportDateSelect.value;
    window.location.href = `/report_tickets?report_date=${selectedDate}`;
});
