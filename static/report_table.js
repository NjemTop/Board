Vue.component('vue-good-table', VueGoodTable.VueGoodTable);

new Vue({
    el: '#app',
    data: {
        columns: [
            { label: 'ID', field: 'id' },
            { label: 'Дата создания', field: 'creation_date' },
            { label: 'Тема тикета', field: 'subject' },
            { label: 'Статус', field: 'status' },
            { label: 'Название клиента', field: 'client_name' },
            { label: 'Приоритет', field: 'priority' },
            { label: 'Исполнитель', field: 'assignee_name' },
            { label: 'Дата обновления', field: 'updated_at' },
            { label: 'Дата последнего ответа клиенту', field: 'last_reply_at' },
            { label: 'SLA', field: 'sla' },
            { label: 'Общее время SLA', field: 'sla_time' },
            { label: 'Среднее время ответа', field: 'response_time' },
            { label: 'Причина возникновения', field: 'cause' },
            { label: 'Модуль BoardMaps', field: 'module_boardmaps' },
            { label: 'Сообщений от саппорта', field: 'staff_message' },
        ],
        rows: [],
    },
    mounted() {
        this.fetchData();
    },
    methods: {
        fetchData(start_date, end_date) {
            fetch('/api/report', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_date: start_date,
                    end_date: end_date,
                }),
            })
                .then((response) => response.json())
                .then((data) => {
                    this.rows = data;
                });
        },        
    },
});

export default app;