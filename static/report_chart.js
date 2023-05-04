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
                'rgba(255, 99, 132, 0.2)',
                'rgba(54, 162, 235, 0.2)',
                'rgba(255, 206, 86, 0.2)',
                'rgba(75, 192, 192, 0.2)',
                'rgba(153, 102, 255, 0.2)',
                'rgba(255, 159, 64, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)',
                'rgba(54, 162, 235, 1)',
                'rgba(255, 206, 86, 1)',
                'rgba(75, 192, 192, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    boxWidth: 20,
                    padding: 10,
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
