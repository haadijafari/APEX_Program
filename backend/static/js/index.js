/* backend/static/js/index.js */

/**
 * ==========================================
 * INDEX API LAYER
 * ==========================================
 */
class IndexAPI {
    static async toggleHabit(habitId, dateStr, csrfToken) {
        const url = `/habit/toggle/${habitId}/${dateStr}/`;
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'Content-Type': 'application/json'
            },
        });
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    }
}

/**
 * ==========================================
 * CHART MANAGER
 * Wraps Chart.js logic to keep the main view clean.
 * ==========================================
 */
class DashboardCharts {
    constructor(config) {
        this.config = config;
        this.charts = {
            stats: null,
            sleep: null,
            habits: null
        };
        this.styles = getComputedStyle(document.documentElement);
        this.primaryColor = this.styles.getPropertyValue('--apex-primary').trim() || '#0d6efd';
        
        this.initStatsChart();
        this.initSleepChart();
        this.initHabitChart();
    }

    initStatsChart() {
        // Relies on global renderStatsChart from stats.js
        if (typeof renderStatsChart === 'function') {
            this.charts.stats = renderStatsChart(this.config.statLabels, this.config.statValues);
            // Store reference globally if needed by stats.js, or capture the return
            window.apexStatsChart = this.charts.stats; 
        }
    }

    initSleepChart() {
        const ctx = document.getElementById('sleepChart');
        if (!ctx) return;

        this.charts.sleep = new Chart(ctx, {
            type: 'line',
            data: {
                labels: this.config.monthDays,
                datasets: [{
                    label: 'Sleep Duration (hrs)',
                    data: this.config.sleepData,
                    borderColor: this.primaryColor,
                    backgroundColor: `rgba(${this.styles.getPropertyValue('--apex-primary-rgb')}, 0.1)`,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, grid: { color: '#333' } },
                    x: { grid: { display: false } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    initHabitChart() {
        const ctx = document.getElementById('habitCountChart');
        if (!ctx) return;

        this.charts.habits = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: this.config.monthDays,
                datasets: [{
                    label: 'Habits Completed',
                    data: this.config.habitCountsData,
                    backgroundColor: this.primaryColor,
                    borderRadius: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { 
                        beginAtZero: true, 
                        grid: { color: '#333' },
                        max: this.config.totalActiveHabits
                    },
                    x: { grid: { display: false } }
                },
                plugins: { 
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            afterLabel: (context) => {
                                const titles = this.config.habitTitlesData[context.dataIndex];
                                return titles && titles.length ? titles : [];
                            }
                        }
                    }
                }
            }
        });
    }

    updateStats(newValues) {
        if (!this.charts.stats) return;
        this.charts.stats.data.datasets[0].data = newValues;
        const newMax = Math.max(...newValues);
        this.charts.stats.options.scales.r.suggestedMax = newMax + 1;
        this.charts.stats.update();
    }

    updateHabitBar(dayIndex, newCount, newTitles) {
        if (!this.charts.habits) return;
        this.charts.habits.data.datasets[0].data[dayIndex] = newCount;
        if (newTitles) {
            this.config.habitTitlesData[dayIndex] = newTitles;
        }
        this.charts.habits.update();
    }
}

/**
 * ==========================================
 * HABIT GRID MANAGER
 * Handles interactions on the big calendar table.
 * ==========================================
 */
class HabitGrid {
    constructor(chartManager) {
        this.chartManager = chartManager;
        this.config = window.apexPageData;
        
        this.initCrosshair();
        
        // Bind the global toggle function expected by the HTML onclicks
        window.toggleHabit = this.handleToggle.bind(this);
    }

    async handleToggle(habitId, dateStr, cellElement, dayIndex) {
        if (!this.config) return;

        try {
            const data = await IndexAPI.toggleHabit(habitId, dateStr, this.config.csrfToken);

            // 1. Update Cell UI
            const iconSpan = cellElement.querySelector('.status-icon');
            if (iconSpan && data.icon_html) iconSpan.innerHTML = data.icon_html;

            // 2. Update Charts
            if (typeof dayIndex !== 'undefined') {
                this.chartManager.updateHabitBar(dayIndex, data.daily_count, data.daily_titles);
            }
            this.chartManager.updateStats(data.new_stats);

            // 3. Update Player Card
            this.updatePlayerCard(data);

        } catch (error) {
            console.error("Habit Toggle Failed:", error);
        }
    }

    updatePlayerCard(data) {
        const els = {
            level: document.getElementById('player-level'),
            xpText: document.getElementById('player-xp-text'),
            xpBar: document.getElementById('player-xp-bar')
        };

        if (els.level) els.level.textContent = data.new_level;
        if (els.xpText) els.xpText.textContent = `${data.new_xp_current} / ${data.new_xp_required}`;
        if (els.xpBar) els.xpBar.style.width = `${data.new_xp_percent}%`;
    }

    initCrosshair() {
        const table = document.querySelector('.habit-tracker-table');
        if (!table) return;

        table.addEventListener('mouseover', (e) => {
            const cell = e.target.closest('td');
            if (!cell || cell.cellIndex === 0) return;

            // Cleanup old
            table.querySelectorAll('.habit-crosshair-active').forEach(el => el.classList.remove('habit-crosshair-active'));

            // Highlight Row & Col
            cell.parentElement.querySelectorAll('td').forEach(td => td.classList.add('habit-crosshair-active'));
            const colIdx = cell.cellIndex + 1;
            table.querySelectorAll(`td:nth-child(${colIdx}), th:nth-child(${colIdx})`)
                 .forEach(el => el.classList.add('habit-crosshair-active'));
        });

        table.addEventListener('mouseleave', () => {
            table.querySelectorAll('.habit-crosshair-active').forEach(el => el.classList.remove('habit-crosshair-active'));
        });
    }
}

// Initialize on Load
document.addEventListener('DOMContentLoaded', () => {
    if (!window.apexPageData) return;
    
    console.log("🚀 Index.js Initialized (Refactored)");

    const dashboardCharts = new DashboardCharts(window.apexPageData);
    new HabitGrid(dashboardCharts);
});
