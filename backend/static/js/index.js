/**
 * backend/static/js/index.js
 * Handles charts and habit toggling for the gate index page.
 */

// Define chart variable in outer scope so toggleHabit can access it
let habitCountChart;

/**
 * Toggle Habit Status
 * This function is called globally by the onclick attributes in the HTML table.
 */
window.toggleHabit = function(habitId, dateStr, cellElement, dayIndex) {
    const config = window.apexPageData;
    if (!config) {
        console.error("Apex page data is missing. Ensure the config script is loaded.");
        return;
    }

    const url = `/habit/toggle/${habitId}/${dateStr}/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': config.csrfToken,
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        // 1. Update Grid Icon
        const iconSpan = cellElement.querySelector('.status-icon');
        if (data.status === 'added') {
            iconSpan.innerHTML = '<span class="text-system">●</span>';
        } else if (data.status === 'removed') {
            iconSpan.innerHTML = '<span class="text-secondary opacity-25">·</span>';
        }

        // 2. Update Bar Chart
        if (habitCountChart && typeof dayIndex !== 'undefined') {
            // Update the specific bar's data
            habitCountChart.data.datasets[0].data[dayIndex] = data.daily_count;

            // Update the tooltip titles for this day in the global config
            if (data.daily_titles) {
                config.habitTitlesData[dayIndex] = data.daily_titles;
            }

            habitCountChart.update();
        }
    })
    .catch(error => {
        console.error('Error toggling habit:', error);
    });
};

// --- Chart Initialization ---
document.addEventListener('DOMContentLoaded', function() {
    const config = window.apexPageData;
    if (!config) return;

    // 1. Render Existing Radar
    // Ensure renderStatsChart is available (loaded from stats.js)
    if (typeof renderStatsChart === 'function') {
        renderStatsChart(config.statLabels, config.statValues);
    }

    const styles = getComputedStyle(document.documentElement);
    const primaryColor = styles.getPropertyValue('--apex-primary').trim() || '#0d6efd';
    const primaryRgb = styles.getPropertyValue('--apex-primary-rgb').trim() || '13, 110, 253';
    
    // 2. Render Sleep Chart
    const sleepChartCanvas = document.getElementById('sleepChart');
    if (sleepChartCanvas) {
        new Chart(sleepChartCanvas, {
            type: 'line',
            data: {
                labels: config.monthDays,
                datasets: [{
                    label: 'Sleep Duration (hrs)',
                    data: config.sleepData,
                    borderColor: primaryColor,
                    backgroundColor: `rgba(${primaryRgb}, 0.1)`,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 2,
                    pointHoverRadius: 5
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        grid: { color: '#333' },
                        suggestedMax: 10
                    },
                    x: { 
                        grid: { display: false },
                        ticks: {
                            autoSkip: false, // Forces all labels (days) to show
                            maxRotation: 0   // Prevents tilting
                        }
                    }
                },
                plugins: { legend: { display: false } } 
            }
        });
    }

    // 3. Render Habit Count Chart
    const habitChartCanvas = document.getElementById('habitCountChart');
    if (habitChartCanvas) {
        habitCountChart = new Chart(habitChartCanvas, {
            type: 'bar',
            data: {
                labels: config.monthDays,
                datasets: [{
                    label: 'Habits Completed',
                    data: config.habitCountsData,
                    backgroundColor: primaryColor,
                    borderRadius: 2,
                    barPercentage: 0.6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        grid: { color: '#333' },
                        ticks: { stepSize: 1 },
                        max: config.totalActiveHabits,
                    },
                    x: {
                        grid: { display: false },
                        ticks: {
                            autoSkip: false,
                            maxRotation: 0
                        }
                    }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: function(context) {
                                const titles = config.habitTitlesData[context.dataIndex];
                                if (titles && titles.length > 0) {
                                    return titles;
                                }
                                return [];
                            }
                        }
                    }
                }
            }
        });
    }
});
