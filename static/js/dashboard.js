document.addEventListener("DOMContentLoaded", function () {
    // Chart 1: Sales by Item
    const salesByItemCtx = document.getElementById("salesByItemChart").getContext("2d");
    new Chart(salesByItemCtx, {
        type: "bar",
        data: {
            labels: {{ sales_by_item.labels | tojson }},
            datasets: [{
                label: "Sales by Item",
                data: {{ sales_by_item.values | tojson }},
                backgroundColor: "rgba(75, 192, 192, 0.6)",
                borderColor: "rgba(75, 192, 192, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 2: Quantity Sold Over Time
    const quantityOverTimeCtx = document.getElementById("quantityOverTimeChart").getContext("2d");
    new Chart(quantityOverTimeCtx, {
        type: "line",
        data: {
            labels: {{ quantity_sold_over_time.labels | tojson }},
            datasets: [{
                label: "Quantity Sold Over Time",
                data: {{ quantity_sold_over_time.values | tojson }},
                backgroundColor: "rgba(153, 102, 255, 0.6)",
                borderColor: "rgba(153, 102, 255, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });

    // Chart 3: Top-Selling Items
    const topSellingItemsCtx = document.getElementById("topSellingItemsChart").getContext("2d");
    new Chart(topSellingItemsCtx, {
        type: "bar",
        data: {
            labels: {{ top_selling_items.labels | tojson }},
            datasets: [{
                label: "Top Selling Items",
                data: {{ top_selling_items.values | tojson }},
                backgroundColor: "rgba(255, 159, 64, 0.6)",
                borderColor: "rgba(255, 159, 64, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 4: Sales Distribution
    const salesDistributionCtx = document.getElementById("salesDistributionChart").getContext("2d");
    new Chart(salesDistributionCtx, {
        type: "pie",
        data: {
            labels: {{ sales_distribution.labels | tojson }},
            datasets: [{
                label: "Sales Distribution",
                data: {{ sales_distribution.values | tojson }},
                backgroundColor: [
                    "rgba(255, 99, 132, 0.6)",
                    "rgba(54, 162, 235, 0.6)",
                    "rgba(255, 206, 86, 0.6)",
                    "rgba(75, 192, 192, 0.6)"
                ]
            }]
        }
    });

    // Chart 5: Daily Sales Performance
    const dailyPerformanceCtx = document.getElementById("dailyPerformanceChart").getContext("2d");
    new Chart(dailyPerformanceCtx, {
        type: "line",
        data: {
            labels: {{ daily_sales_performance.labels | tojson }},
            datasets: [{
                label: "Daily Revenue",
                data: {{ daily_sales_performance.values | tojson }},
                backgroundColor: "rgba(255, 205, 86, 0.6)",
                borderColor: "rgba(255, 205, 86, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });
});
