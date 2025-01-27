document.addEventListener("DOMContentLoaded", function () {
    // Debugging data passed from Flask
    console.log(totalSalesData, salesByItemData, quantitySoldOverTimeData, topSellingItemsData, salesDistributionData, dailySalesPerformanceData);

    // Chart 1: Total Sales
    const totalSalesdataCtx = document.getElementById("totalSales").getContext("2d");
    new Chart(totalSalesdataCtx, {
        type: "bar",
        data: {
            labels: totalSalesData.labels,
            datasets: [{
                label: "Total Sales by Manager",
                data: totalSalesData.values,
                backgroundColor: [ 
                    'rgba(0, 51, 102, 0.9)',
                        'rgba(0, 128, 255, 0.8)',  // Deep Navy Blue (Completed)
                'rgba(0, 76, 153, 0.8)',  // Medium Blue (Cancelled)
                'rgba(0, 102, 204, 0.8)', // Sky Blue (Pending)
                'rgba(51, 153, 255, 0.7)', // Light Blue (Processing)
                 // Bright Blue (Optional)
                'rgba(0, 204, 255, 0.7)'   // Cyan (Optional)
            ],
            borderColor: [
            'rgba(0, 51, 102, 1)',
                'rgba(0, 128, 255, 1)',    // Deep Navy Blue
                'rgba(0, 76, 153, 1)',    // Medium Blue
                'rgba(0, 102, 204, 1)',   // Sky Blue
                'rgba(51, 153, 255, 1)',  // Light Blue
                   // Bright Blue
                'rgba(0, 204, 255, 1)'    // Cyan
            ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Chart 2: Sales by Item
    const salesByItemCtx = document.getElementById("salesByItemChart").getContext("2d");
    new Chart(salesByItemCtx, {
        type: "bar",
        data: {
            labels: salesByItemData.labels,
            datasets: [{
                label: "Sales by Item",
                data: salesByItemData.values,
                backgroundColor: "rgba(0, 102, 204, 0.8)",
                borderColor: "rgba(0, 102, 204, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 3: Quantity Sold Over Time
    const quantityOverTimeCtx = document.getElementById("quantityOverTimeChart").getContext("2d");
    new Chart(quantityOverTimeCtx, {
        type: "line",
        data: {
            labels: quantitySoldOverTimeData.labels,
            datasets: [{
                label: "Quantity Sold Over Time",
                data: quantitySoldOverTimeData.values,
                backgroundColor: "rgba(0, 204, 255, 0.7)",
                borderColor: "rgba(0, 204, 255, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });

    // Chart 4: Top-Selling Items
    const topSellingItemsCtx = document.getElementById("topSellingItemsChart").getContext("2d");
    new Chart(topSellingItemsCtx, {
        type: "bar",
        data: {
            labels: topSellingItemsData.labels,
            datasets: [{
                label: "Top Selling Items",
                data: topSellingItemsData.values,
                backgroundColor: "rgba(0, 76, 153, 0.8)",
                borderColor: "rgba(0, 76, 153, 1)",
                borderWidth: 1
            }]
        }
    });

    // Chart 5: Sales Distribution
    const salesDistributionCtx = document.getElementById("salesDistributionChart").getContext("2d");
    new Chart(salesDistributionCtx, {
        type: "pie",
        data: {
            labels: salesDistributionData.labels,
            datasets: [{
                label: "Sales Distribution",
                data: salesDistributionData.values,
                backgroundColor: [ 
                    'rgba(0, 51, 102, 0.9)',
                        'rgba(0, 128, 255, 0.8)',  // Deep Navy Blue (Completed)
                'rgba(0, 76, 153, 0.8)',  // Medium Blue (Cancelled)
                'rgba(0, 102, 204, 0.8)', // Sky Blue (Pending)
                'rgba(51, 153, 255, 0.7)', // Light Blue (Processing)
                 // Bright Blue (Optional)
                'rgba(0, 204, 255, 0.7)'   // Cyan (Optional)
            ]
            }]
        }
    });

    // Chart 6: Daily Sales Performance
    const dailyPerformanceCtx = document.getElementById("dailyPerformanceChart").getContext("2d");
    new Chart(dailyPerformanceCtx, {
        type: "line",
        data: {
            labels: dailySalesPerformanceData.labels,
            datasets: [{
                label: "Daily Revenue",
                data: dailySalesPerformanceData.values,
                backgroundColor: "rgba(51, 153, 255, 0.7)",
                borderColor: "rgba(51, 153, 255, 1)",
                borderWidth: 2,
                fill: true
            }]
        }
    });
});
