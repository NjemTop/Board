const reportDataTag = document.getElementById('report-data-tag');
const reportData = JSON.parse(reportDataTag.textContent);

Vue.component('date-picker', Vue2DatePicker);

const app = new Vue({
    el: '#app',
    data: {
        reportData: reportData,
        dateRange: '',
        selectedMonth: 'all',
        uniqueMonths: Array.from(new Set(reportData.map(entry => {
            const [day, month, year] = entry.report_date.split('-');
            return `${month}-${year}`;
        }))).sort(),
    },
    methods: {
        displayData(dateRange) {
            // сброс выбранного месяца
            this.selectedMonth = 'all';
    
            const tableBody = document.querySelector('#report-table tbody');
            tableBody.innerHTML = '';
    
            let filteredData;
            if (dateRange === '') {
                filteredData = reportData;
            } else {
                const [startDate, endDate] = dateRange.split(' ~ ').map(date => new Date(date.split('-').reverse().join('-')));
                filteredData = reportData.filter(entry => {
                    const entryDate = new Date(entry.report_date.split('-').reverse().join('-'));
                    return entryDate >= startDate && entryDate <= endDate;
                });
            }
    
            this.updateTable(filteredData);
            this.updateChartData(filteredData);
        },
        displayDataByMonth(selectedMonth) {
            // сброс выбранного диапазона дат
            this.dateRange = '';
    
            const tableBody = document.querySelector('#report-table tbody');
            tableBody.innerHTML = '';
    
            let filteredData;
            if (selectedMonth === 'all') {
                filteredData = reportData;
            } else {
                filteredData = reportData.filter(entry => {
                    const [day, month, year] = entry.report_date.split('-');
                    return `${month}-${year}` === selectedMonth;
                });
            }
    
            this.updateTable(filteredData);
            this.updateChartData(filteredData);
        },
        updateTable(filteredData) {
            const tableBody = document.querySelector('#report-table tbody');
            tableBody.innerHTML = '';
        
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
        },
    },
});
