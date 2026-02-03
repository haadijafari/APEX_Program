/* backend/static/js/stats.js */
(function() {
    'use strict';
    
    if (window.HAS_STATS_JS_LOADED) return;
    window.HAS_STATS_JS_LOADED = true;

    /**
     * ==========================================
     * STATS VISUALIZATION MODULE
     * Renders the Radar Chart for Player Stats.
     * ==========================================
     */
    class StatsChartRenderer {
        
        /**
         * Renders (or re-renders) the Radar Chart.
         * @param {Array<string>} labels - Stat names (STR, AGI, etc)
         * @param {Array<number>} dataValues - Stat levels
         * @returns {Object|null} Chart.js instance
         */
        static render(labels, dataValues) {
            const ctx = document.getElementById('statsChart');
            if (!ctx) return null;

            // 1. Theme Extraction
            const styles = getComputedStyle(document.documentElement);
            const primaryColor = styles.getPropertyValue('--apex-primary').trim() || '#0d6efd';
            const primaryRgb = styles.getPropertyValue('--apex-primary-rgb').trim() || '13, 110, 253';

            // 2. Scale Calculation (Max + buffer)
            const scaleMax = Math.max(...dataValues) + 1;

            // 3. Clean Re-render
            if (window.apexStatsChart) {
                window.apexStatsChart.destroy();
            }

            // 4. Initialize
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
                    plugins: { legend: { display: false } },
                    maintainAspectRatio: false 
                }
            });

            return window.apexStatsChart;
        }
    }

    // Export globally for index.js usage
    window.renderStatsChart = StatsChartRenderer.render;

})();
