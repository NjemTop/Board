const reportDataTag = document.getElementById('report-data-tag');
const reportData = JSON.parse(reportDataTag.textContent);

function displayData(reportDate) {
    const tableBody = document.querySelector('#report-table tbody');
    tableBody.innerHTML = '';

    const filteredData = reportDate === 'all' ? reportData : reportData.filter(entry => entry.creation_date === reportDate);

    filteredData.forEach(entry => {
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
}

reportDateSelect.addEventListener('change', () => {
    const selectedDate = reportDateSelect.value;
    displayData(selectedDate);
});

displayData('all');