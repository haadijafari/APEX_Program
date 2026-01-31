/* backend/static/js/admin_tasks.js */

(function() {
    // 1. IDEMPOTENCY GUARD
    if (window.HAS_ADMIN_TASKS_JS_LOADED) return;
    window.HAS_ADMIN_TASKS_JS_LOADED = true;

/**
 * ==========================================
 * MODULE: SCHEDULE VISIBILITY CONTROLLER
 * Handles showing/hiding the 'weekdays' field
 * based on the frequency selection.
 * ==========================================
 */
class ScheduleVisibilityController {
    constructor() {
        // Support both Inline (OneToOne) and Standard form IDs
        this.freqSelect = document.getElementById('id_schedule-0-frequency') || document.getElementById('id_frequency');
        this.weekdaysField = document.querySelector('.field-weekdays');

        if (this.freqSelect && this.weekdaysField) {
            this.init();
        }
    }

    init() {
        // Initial check
        this.toggle();

        // Bind listener
        this.freqSelect.addEventListener('change', () => this.toggle());
    }

    toggle() {
        if (this.freqSelect.value === 'WEEKLY') {
            // Revert to default display (block/flex)
            this.weekdaysField.style.display = '';
        } else {
            // Hide completely
            this.weekdaysField.style.display = 'none';
        }
    }
}

/**
 * ==========================================
 * MODULE: XP PREVIEW CONTROLLER
 * Real-time calculation of Rank and XP split
 * based on task parameters.
 * ==========================================
 */
class XPPreviewController {
    constructor() {
        // --- Configuration ---
        this.RANK_XP = {
            "E": 15, "D": 35, "C": 75, "B": 150,
            "A": 350, "S": 700, "SS": 1200, "Monarch": 1500
        };

        // --- DOM Elements ---
        this.dom = {
            // Stats
            primary: document.getElementById('id_primary_stat'),
            secondary: document.getElementById('id_secondary_stat'),
            manualRank: document.getElementById('id_manual_rank'),

            // Scoring Inputs
            duration: document.getElementById('id_duration_minutes'),
            effort: document.getElementById('id_effort_level'),
            impact: document.getElementById('id_impact_level'),
            fear: document.getElementById('id_fear_factor'),

            // Outputs
            previewSpan: document.getElementById('xp-distribution-preview'),
            computedRankRow: document.getElementById('computed-rank-preview')
        };

        // Only initialize if critical elements exist
        if (this.dom.primary) {
            this.initValueDisplays();
            this.bindEvents();
            this.calculate(); // Initial run
        }
    }

    initValueDisplays() {
        this.attachValueDisplay(this.dom.effort, "/10");
        this.attachValueDisplay(this.dom.impact, "/5");
        this.attachValueDisplay(this.dom.fear, "x");
    }

    attachValueDisplay(inputElement, unit = "") {
        if (!inputElement || inputElement.type !== 'range') return;

        // Prevent duplicates
        if (inputElement.nextElementSibling && inputElement.nextElementSibling.classList.contains('range-value')) return;

        // Create UI
        const displaySpan = document.createElement('span');
        displaySpan.className = 'range-value';
        Object.assign(displaySpan.style, {
            marginLeft: '10px',
            fontWeight: 'bold',
            minWidth: '30px',
            display: 'inline-block'
        });

        // Insert & Bind
        inputElement.parentNode.insertBefore(displaySpan, inputElement.nextSibling);
        
        const update = () => displaySpan.textContent = `${inputElement.value}${unit}`;
        inputElement.addEventListener('input', update);
        update();
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

    calculate() {
        if (!this.dom.previewSpan) return;

        // 1. Calculate Score
        const duration = parseInt(this.dom.duration?.value || 15);
        const effort = parseInt(this.dom.effort?.value || 1);
        const impact = parseInt(this.dom.impact?.value || 1);
        const fear = parseFloat(this.dom.fear?.value || 1.0);

        const durationScore = Math.min(duration, 240); // Cap at 4 hours
        // Formula: ((Duration * 0.25) + (Effort * 1.5) + (Impact^3)) * FearFactor
        const baseScore = (durationScore * 0.25) + (effort * 1.5) + (Math.pow(impact, 3));
        const totalScore = baseScore * fear;

        // 2. Determine Computed Rank
        let computedRank = "E";
        if (totalScore > 280) computedRank = "Monarch";
        else if (totalScore > 250) computedRank = "SS";
        else if (totalScore > 180) computedRank = "S";
        else if (totalScore > 120) computedRank = "A";
        else if (totalScore > 75) computedRank = "B";
        else if (totalScore > 45) computedRank = "C";
        else if (totalScore > 20) computedRank = "D";

        // Update UI for Computed Rank
        if (this.dom.computedRankRow) {
            this.dom.computedRankRow.textContent = `${computedRank}-Rank (Score: ${totalScore.toFixed(1)})`;
        }

        // 3. Determine Final Rank (Manual overrides Computed)
        const manualRank = this.dom.manualRank?.value;
        const finalRank = manualRank || computedRank;
        const totalXP = this.RANK_XP[finalRank] || 15;

        // 4. Calculate Split
        const pStat = this.dom.primary?.value || 'STR';
        const sStat = this.dom.secondary?.value;
        let outputText = "";

        if (!sStat || sStat === pStat) {
            // Case 1: 100% Primary
            outputText = `${pStat}: ${totalXP} XP`;
        } else {
            // Case 2: 60/40 Split
            const pAmount = Math.floor(totalXP * 0.60);
            const sAmount = totalXP - pAmount; 
            outputText = `${pStat}: ${pAmount} XP, ${sStat}: ${sAmount} XP`;
        }

        // 5. Render Output
        this.dom.previewSpan.textContent = outputText;
        this.dom.previewSpan.style.color = manualRank ? "#d35400" : "#27ae60"; // Orange if manual, Green if auto
    }
}

/**
 * ==========================================
 * BOOTSTRAPPER
 * ==========================================
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Admin Tasks JS Initialized");
    
    new ScheduleVisibilityController();
    new XPPreviewController();
});

})();
