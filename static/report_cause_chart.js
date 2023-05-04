const chartDataTag = document.getElementById('report-data-tag');
const chartData = JSON.parse(chartDataTag.textContent);

let causeCount = {};
chartData.forEach(entry => {
    const cause = entry.cause;
    causeCount[cause] = (causeCount[cause] || 0) + 1;
});

const ctx = document.getElementById('chart').getContext('2d');
const chart = new Chart(ctx, {
    type: 'pie',
    data: {
        labels: Object.keys(causeCount),
        datasets: [{
            data: Object.values(causeCount),
            backgroundColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                // добавьте другие цвета для фона, если необходимо
            ],
            borderColor: [
                '#FF6384',
                '#36A2EB',
                '#FFCE56',
                '#4BC0C0',
                '#9966FF',
                '#FF9F40',
                // добавьте другие цвета для границы, если необходимо
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const total = context.dataset.data.reduce((a, b) => a + b);
                        const value = context.raw;
                        const percentage = ((value / total) * 100).toFixed(2);
                        return `${value} (${percentage}%)`;
                    }
                }
            },
            legend: {
                position: 'right', // положение легенды: 'top', 'right', 'bottom' или 'left'
                labels: {
                    boxWidth: 20, // ширина блока метки
                    padding: 10, // отступ между метками
                }
            }
        },
        layout: {
            padding: {
                left: 0,
                right: 0,
                top: 0,
                bottom: 0
            }
        },
    }
});

// Функция для сортировки легенды
function sortLegend() {
    const dataset = chart.data.datasets[0];
    const labels = chart.data.labels;
    const data = dataset.data;

    const dataArray = labels.map((label, index) => ({
        label: label,
        data: data[index],
        backgroundColor: dataset.backgroundColor[index],
        borderColor: dataset.borderColor[index]
    }));

    dataArray.sort((a, b) => b.data - a.data);

    labels.length = 0;
    data.length = 0;
    dataset.backgroundColor.length = 0;
    dataset.borderColor.length = 0;

    dataArray.forEach(item => {
        labels.push(item.label);
        data.push(item.data);
        dataset.backgroundColor.push(item.backgroundColor);
        dataset.borderColor.push(item.borderColor);
    });

    chart.update();
}

// Вызовите функцию сортировки легенды после создания графика
sortLegend();
