function renderStatsChart(labels, dataValues) {
    const ctx = document.getElementById('statsChart');
    
    // Safety check: if chart doesn't exist on page, stop
    if (!ctx) return;

    //Get the colors dynamically from CSS variables
    const styles = getComputedStyle(document.documentElement);
    const primaryColor = styles.getPropertyValue('--apex-primary').trim();
    const primaryRgb = styles.getPropertyValue('--apex-primary-rgb').trim();

    new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels, // Received from arguments
            datasets: [{
                label: 'Player Stats',
                data: dataValues, // Received from arguments
                fill: true,
                backgroundColor: `rgba(${primaryRgb}, 0.2)`,
                borderColor: primaryColor,
                pointBackgroundColor: primaryColor,
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: primaryColor
            }]
        },
        options: {
            scales: {
                r: {
                    angleLines: { color: '#333' },
                    grid: { color: '#333' },
                    pointLabels: { 
                        color: '#aaa',
                        font: { size: 11 }
                    },
                    ticks: { display: false, backdropColor: 'transparent' },
                    suggestedMin: 0,
                    suggestedMax: 20 // Keeps the chart looking good even with low stats
                }
            },
            plugins: {
                legend: { display: false }
            },
            maintainAspectRatio: false 
        }
    });
}
