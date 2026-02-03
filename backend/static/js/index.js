/* backend/static/js/index.js */
(function() {
    'use strict';
    
    if (window.HAS_INDEX_JS_LOADED) return;
    window.HAS_INDEX_JS_LOADED = true;

    // --- API Service ---
    class IndexAPI {
        static async toggleHabit(habitId, dateStr, csrfToken) {
            const response = await fetch(`/habit/toggle/${habitId}/${dateStr}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
            });
            if (!response.ok) throw new Error('Habit toggle failed');
            return await response.json();
        }
    }

    /**
     * ==========================================
     * CHART MANAGER
     * Wraps Chart.js instances for the Dashboard.
     * ==========================================
     */
    class DashboardCharts {
        constructor(config) {
            this.config = config;
            this.charts = { stats: null, sleep: null, habits: null };
            
            const styles = getComputedStyle(document.documentElement);
            this.theme = {
                primary: styles.getPropertyValue('--apex-primary').trim() || '#0d6efd',
                primaryRgb: styles.getPropertyValue('--apex-primary-rgb').trim()
            };

            this.initStatsChart();
            this.initSleepChart();
            this.initHabitChart();
        }

        initStatsChart() {
            // Relies on global renderStatsChart from stats.js
            if (typeof renderStatsChart === 'function') {
                this.charts.stats = renderStatsChart(this.config.statLabels, this.config.statValues);
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
                        borderColor: this.theme.primary,
                        backgroundColor: `rgba(${this.theme.primaryRgb}, 0.1)`,
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
                        backgroundColor: this.theme.primary,
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
                                afterLabel: (ctx) => {
                                    // Show titles of completed habits in tooltip
                                    const titles = this.config.habitTitlesData[ctx.dataIndex];
                                    return titles?.length ? titles : [];
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
            this.charts.stats.options.scales.r.suggestedMax = Math.max(...newValues) + 1;
            this.charts.stats.update();
        }

        updateHabitBar(dayIndex, newCount, newTitles) {
            if (!this.charts.habits) return;
            this.charts.habits.data.datasets[0].data[dayIndex] = newCount;
            if (newTitles) this.config.habitTitlesData[dayIndex] = newTitles;
            this.charts.habits.update();
        }
    }

    /**
     * ==========================================
     * HABIT GRID MANAGER
     * Handles calendar table interactions
     * ==========================================
     */
    class HabitGrid {
        constructor(chartManager) {
            this.chartManager = chartManager;
            this.config = window.apexPageData;
            
            this.initCrosshair();
            
            // Export interaction handler for HTML onclicks
            window.toggleHabit = this.handleToggle.bind(this);
        }

        async handleToggle(habitId, dateStr, cellElement, dayIndex) {
            if (!this.config) return;

            try {
                const data = await IndexAPI.toggleHabit(habitId, dateStr, this.config.csrfToken);

                // 1. Update Cell Icon
                const iconSpan = cellElement.querySelector('.status-icon');
                if (iconSpan && data.icon_html) iconSpan.innerHTML = data.icon_html;

                // 2. Update Charts & Stats
                if (dayIndex !== undefined) {
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
            const setTxt = (id, val) => {
                const el = document.getElementById(id);
                if (el) el.textContent = val;
            };
            
            setTxt('player-level', data.new_level);
            setTxt('player-xp-text', `${data.new_xp_current} / ${data.new_xp_required}`);
            
            const xpBar = document.getElementById('player-xp-bar');
            if (xpBar) xpBar.style.width = `${data.new_xp_percent}%`;
        }

        initCrosshair() {
            const table = document.querySelector('.habit-tracker-table');
            if (!table) return;

            // Highlight row and column on hover
            table.addEventListener('mouseover', (e) => {
                const cell = e.target.closest('td');
                if (!cell || cell.cellIndex === 0) return; // Ignore headers/first col

                // Reset previous
                table.querySelectorAll('.habit-crosshair-active')
                     .forEach(el => el.classList.remove('habit-crosshair-active'));

                // Highlight Row
                cell.parentElement.querySelectorAll('td')
                    .forEach(td => td.classList.add('habit-crosshair-active'));
                
                // Highlight Column
                const colIdx = cell.cellIndex + 1;
                table.querySelectorAll(`td:nth-child(${colIdx}), th:nth-child(${colIdx})`)
                     .forEach(el => el.classList.add('habit-crosshair-active'));
            });

            table.addEventListener('mouseleave', () => {
                table.querySelectorAll('.habit-crosshair-active')
                     .forEach(el => el.classList.remove('habit-crosshair-active'));
            });
        }
    }

    // Main Entry
    document.addEventListener('DOMContentLoaded', () => {
        if (window.apexPageData) {
            const charts = new DashboardCharts(window.apexPageData);
            new HabitGrid(charts);
        }
    });

})();
