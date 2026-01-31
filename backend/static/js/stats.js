/* backend/static/js/stats.js */

(function() {
    // 1. IDEMPOTENCY GUARD: Prevent double-loading
    if (window.HAS_STATS_JS_LOADED) return;
    window.HAS_STATS_JS_LOADED = true;

/**
 * ==========================================
 * STATS VISUALIZATION MODULE
 * Handles the configuration and rendering of the
 * Player Stats Radar Chart using Chart.js.
 * ==========================================
 */
class StatsChartRenderer {
    
    /**
     * Renders or re-renders the Radar Chart.
     * * @param {Array<string>} labels - Array of stat names (e.g. ['STR', 'INT'])
     * @param {Array<number>} dataValues - Array of stat values
     * @returns {Object|null} The Chart.js instance or null if container missing
     */
    static render(labels, dataValues) {
        const ctx = document.getElementById('statsChart');
        
        // Safety check: if chart container doesn't exist, stop
        if (!ctx) return null;

        // 1. Styles & Theme Config
        const styles = getComputedStyle(document.documentElement);
        const primaryColor = styles.getPropertyValue('--apex-primary').trim() || '#0d6efd';
        const primaryRgb = styles.getPropertyValue('--apex-primary-rgb').trim() || '13, 110, 253';

        // 2. Calculate Scale (Max Stat + 1 for breathing room)
        const maxLevel = Math.max(...dataValues);
        const scaleMax = maxLevel + 1;

        // 3. Cleanup Previous Instance
        if (window.apexStatsChart) {
            window.apexStatsChart.destroy();
        }

        // 4. Initialize Chart
        window.apexStatsChart = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Player Stats',
                    data: dataValues,
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
                        suggestedMax: scaleMax
                    }
                },
                plugins: {
                    legend: { display: false }
                },
                maintainAspectRatio: false 
            }
        });

        // [CRITICAL] Return the instance so index.js can control it
        return window.apexStatsChart;
    }
}

/**
 * ==========================================
 * EXPORTS
 * Expose the render function globally so 
 * index.js can utilize it.
 * ==========================================
 */
window.renderStatsChart = StatsChartRenderer.render;

// Optional: Log initialization for debugging consistency
console.log("🚀 Stats.js Loaded");

})();
