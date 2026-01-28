/**
 * backend/static/js/index.js
 * Handles charts and habit toggling for the gate index page.
 */

(function() {
    // Define chart variable in local scope so it's accessible to toggleHabit and init
    // wrapped in an IIFE to prevent "Identifier already declared" errors.
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
            // 1. Update Grid Icon using Backend HTML
            const iconSpan = cellElement.querySelector('.status-icon');
            if (data.icon_html) {
                iconSpan.innerHTML = data.icon_html;
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

            // 3. Update Player Card ===
            const elLevel = document.getElementById('player-level');
            const elXPText = document.getElementById('player-xp-text');
            const elXPBar = document.getElementById('player-xp-bar');

            if (elLevel) elLevel.textContent = data.new_level;
            if (elXPText) elXPText.textContent = `${data.new_xp_current} / ${data.new_xp_required}`;
            if (elXPBar) elXPBar.style.width = `${data.new_xp_percent}%`;

            // === 4. Update Stats Radar Chart ===
            if (window.apexStatsChart) {
                // Update the data array
                window.apexStatsChart.data.datasets[0].data = data.new_stats;
                
                // Optional: Dynamic Scaling (if stats grew, increase the chart scale)
                const newMax = Math.max(...data.new_stats);
                window.apexStatsChart.options.scales.r.suggestedMax = newMax + 1;
                
                window.apexStatsChart.update();
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

        // 4. Habit Tracker Crosshair Effect
        const table = document.querySelector('.habit-tracker-table');
        if (table) {
            table.addEventListener('mouseover', function(e) {
                const cell = e.target.closest('td');
                if (!cell) return;

                // Clear previous highlights
                table.querySelectorAll('.habit-crosshair-active').forEach(el => el.classList.remove('habit-crosshair-active'));

                const colIndex = cell.cellIndex;
                // Skip Habit Title column (index 0)
                if (colIndex === 0) return;

                // Highlight Row
                const row = cell.parentElement;
                row.querySelectorAll('td').forEach(td => td.classList.add('habit-crosshair-active'));

                // Highlight Column
                const colSelector = `td:nth-child(${colIndex + 1}), th:nth-child(${colIndex + 1})`;
                table.querySelectorAll(colSelector).forEach(el => el.classList.add('habit-crosshair-active'));
            });

            table.addEventListener('mouseleave', function() {
                table.querySelectorAll('.habit-crosshair-active').forEach(el => el.classList.remove('habit-crosshair-active'));
            });
        }
    });

})();