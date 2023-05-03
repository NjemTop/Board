const data = [
    "Доработка",
    "Консультация",
    "Консультация",
    // ... (другие элементы массива)
    "В работе",
  ];
  
  const categories = {};
  data.forEach((item) => {
    categories[item] = (categories[item] || 0) + 1;
  });
  
  const labels = Object.keys(categories);
  const chartData = labels.map((label) => categories[label]);
  
  const ctx = document.getElementById("myChart").getContext("2d");
  const myChart = new Chart(ctx, {
    type: "pie",
    data: {
      labels: labels,
      datasets: [
        {
          data: chartData,
          backgroundColor: [
            // Укажите цвета для каждой категории (количество цветов должно совпадать с количеством категорий)
            "rgba(255, 99, 132, 0.2)",
            "rgba(54, 162, 235, 0.2)",
            "rgba(255, 206, 86, 0.2)",
            // ... (другие цвета)
          ],
          borderColor: [
            // Укажите цвета границ для каждой категории (количество цветов должно совпадать с количеством категорий)
            "rgba(255, 99, 132, 1)",
            "rgba(54, 162, 235, 1)",
            "rgba(255, 206, 86, 1)",
            // ... (другие цвета)
          ],
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "top",
        },
      },
    },
  });
  