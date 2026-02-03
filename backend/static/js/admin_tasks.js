/* backend/static/js/admin_tasks.js */
(function() {
    'use strict';

    // 1. IDEMPOTENCY GUARD
    if (window.HAS_ADMIN_TASKS_JS_LOADED) return;
    window.HAS_ADMIN_TASKS_JS_LOADED = true;

    /**
     * ==========================================
     * MODULE: SCHEDULE VISIBILITY CONTROLLER
     * Handles UI logic for Weekly vs Daily tasks.
     * ==========================================
     */
    class ScheduleVisibilityController {
        constructor() {
            this.freqSelect = document.getElementById('id_schedule-0-frequency') || document.getElementById('id_frequency');
            this.weekdaysField = document.querySelector('.field-weekdays');

            if (this.freqSelect && this.weekdaysField) {
                this.init();
            }
        }

        init() {
            this.toggle(); // Initial state
            this.freqSelect.addEventListener('change', () => this.toggle());
        }

        toggle() {
            // Only show weekdays selector if frequency is WEEKLY
            const isWeekly = this.freqSelect.value === 'WEEKLY';
            this.weekdaysField.style.display = isWeekly ? '' : 'none';
        }
    }

    /**
     * ==========================================
     * MODULE: XP PREVIEW CONTROLLER
     * Calculates Task Rank and XP in real-time.
     * ==========================================
     */
    class XPPreviewController {
        // Configuration: XP Tables and Scoring Weights
        static CONFIG = {
            RANK_XP: {
                "E": 15, "D": 35, "C": 75, "B": 150,
                "A": 350, "S": 700, "SS": 1200, "Monarch": 1500
            },
            THRESHOLDS: {
                "Monarch": 280, "SS": 250, "S": 180, "A": 120,
                "B": 75, "C": 45, "D": 20
            },
            WEIGHTS: {
                DURATION: 0.25,
                EFFORT: 1.5,
                IMPACT_POW: 3
            },
            MAX_DURATION_MINS: 240
        };

        constructor() {
            // --- DOM Elements ---
            this.dom = {
                // Inputs
                primary: document.getElementById('id_primary_stat'),
                secondary: document.getElementById('id_secondary_stat'),
                manualRank: document.getElementById('id_manual_rank'),
                duration: document.getElementById('id_duration_minutes'),
                effort: document.getElementById('id_effort_level'),
                impact: document.getElementById('id_impact_level'),
                fear: document.getElementById('id_fear_factor'),

                // Outputs
                previewSpan: document.getElementById('xp-distribution-preview'),
                computedRankRow: document.getElementById('computed-rank-preview')
            };

            // Initialize only if primary fields exist (e.g. on Add/Change page)
            if (this.dom.primary) {
                this.initValueDisplays();
                this.bindEvents();
                this.calculate(); 
            }
        }

        /**
         * Adds visual feedback numbers next to range sliders
         */
        initValueDisplays() {
            this.attachValueDisplay(this.dom.effort, "/10");
            this.attachValueDisplay(this.dom.impact, "/5");
            this.attachValueDisplay(this.dom.fear, "x");
        }

        attachValueDisplay(inputElement, unit = "") {
            if (!inputElement || inputElement.type !== 'range') return;
            if (inputElement.nextElementSibling?.classList.contains('range-value')) return;

            const displaySpan = document.createElement('span');
            displaySpan.className = 'range-value';
            displaySpan.style.cssText = 'margin-left: 10px; font-weight: bold; min-width: 30px; display: inline-block;';

            const update = () => displaySpan.textContent = `${inputElement.value}${unit}`;
            inputElement.addEventListener('input', update);
            update(); // Initial set
            inputElement.parentNode.insertBefore(displaySpan, inputElement.nextSibling);
        }

        bindEvents() {
            const inputs = [
                this.dom.primary, this.dom.secondary, this.dom.manualRank,
                this.dom.duration, this.dom.effort, this.dom.impact, this.dom.fear
            ];

            inputs.forEach(input => {
                if (input) {
                    input.addEventListener('change', () => this.calculate());
                    input.addEventListener('keyup', () => this.calculate());
                }
            });
        }

        /**
         * Main Logic: Calculates score based on inputs and updates DOM.
         */
        calculate() {
            if (!this.dom.previewSpan) return;

            const cfg = XPPreviewController.CONFIG;

            // 1. Get Values
            const duration = parseInt(this.dom.duration?.value || 15);
            const effort = parseInt(this.dom.effort?.value || 1);
            const impact = parseInt(this.dom.impact?.value || 1);
            const fear = parseFloat(this.dom.fear?.value || 1.0);

            // 2. Compute Score
            // Formula: ((Duration * 0.25) + (Effort * 1.5) + (Impact^3)) * FearFactor
            const cappedDuration = Math.min(duration, cfg.MAX_DURATION_MINS);
            const baseScore = (cappedDuration * cfg.WEIGHTS.DURATION) + 
                              (effort * cfg.WEIGHTS.EFFORT) + 
                              (Math.pow(impact, cfg.WEIGHTS.IMPACT_POW));
            
            const totalScore = baseScore * fear;

            // 3. Determine Rank from Score
            let computedRank = "E";
            for (const [rank, threshold] of Object.entries(cfg.THRESHOLDS)) {
                if (totalScore > threshold) {
                    computedRank = rank;
                    break; // Found highest matching rank (assuming object iteration order or manual sort)
                }
            }

            // Update Rank Preview UI
            if (this.dom.computedRankRow) {
                this.dom.computedRankRow.textContent = `${computedRank}-Rank (Score: ${totalScore.toFixed(1)})`;
            }

            // 4. Calculate Final XP (Manual override takes precedence)
            const finalRank = this.dom.manualRank?.value || computedRank;
            const totalXP = cfg.RANK_XP[finalRank] || 15;

            // 5. XP Split (Primary vs Secondary)
            const pStat = this.dom.primary?.value || 'STR';
            const sStat = this.dom.secondary?.value;
            let outputText = "";

            if (!sStat || sStat === pStat) {
                outputText = `${pStat}: ${totalXP} XP`;
            } else {
                // 60/40 Split
                const pAmount = Math.floor(totalXP * 0.60);
                const sAmount = totalXP - pAmount; 
                outputText = `${pStat}: ${pAmount} XP, ${sStat}: ${sAmount} XP`;
            }

            this.dom.previewSpan.textContent = outputText;
            // Visual cue: Orange if overridden manually, Green if automatic
            this.dom.previewSpan.style.color = this.dom.manualRank?.value ? "#d35400" : "#27ae60"; 
        }
    }

    // Initialize
    document.addEventListener('DOMContentLoaded', () => {
        new ScheduleVisibilityController();
        new XPPreviewController();
    });

})();
