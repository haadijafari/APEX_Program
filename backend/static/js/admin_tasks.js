// ----------------- Dynamic Weekdays Field Visibility -----------------
// Show/hide the 'weekdays' field based on the selected frequency
document.addEventListener('DOMContentLoaded', function() {
    const freqSelect = document.getElementById('id_frequency');
    // Django admin wraps fields in rows with classes like "form-row field-weekdays"
    const weekdaysField = document.querySelector('.field-weekdays');

    function toggleWeekdays() {
        if (!freqSelect || !weekdaysField) return;

        if (freqSelect.value === 'WEEKLY') {
            // Make it visible
            weekdaysField.style.visibility = 'visible';
        } else {
            // Hide it, but KEEP the space it occupies (prevents height jump)
            weekdaysField.style.visibility = 'hidden';
        }
    }

    if (freqSelect) {
        // Run on page load (to handle existing data)
        toggleWeekdays();
        // Run whenever the user changes the dropdown
        freqSelect.addEventListener('change', toggleWeekdays);
    }
});


// ----------------- Dynamic XP Distribution Preview -----------------
document.addEventListener('DOMContentLoaded', function() {
    console.log("Apex Task Admin Loaded.");

    // --- Configuration ---
    const STAT_TYPES = {
        'STR': 'Strength',
        'DEX': 'Dexterity',
        'INT': 'Intelligence',
        'WIS': 'Wisdom',
        'CHA': 'Charisma',
        'CON': 'Constitution'
    };

    const RANK_XP = {
        "E": 15,
        "D": 35,
        "C": 75,
        "B": 150,
        "A": 350,
        "S": 700,
        "SS": 1200,
        "Monarch": 1500
    };

    // --- Selectors ---
    const inputPrimary = document.getElementById('id_primary_stat');
    const inputSecondary = document.getElementById('id_secondary_stat');
    const inputManualRank = document.getElementById('id_manual_rank');
    
    // Inputs affecting Score
    const inputDuration = document.getElementById('id_duration_minutes');
    const inputEffort = document.getElementById('id_effort_level');
    const inputImpact = document.getElementById('id_impact_level');
    const inputFear = document.getElementById('id_fear_factor');

    // Outputs
    const previewSpan = document.getElementById('xp-distribution-preview');
    // Unfold/Django readonly fields are often wrapped in specific classes. 
    // We try to find the read-only Computed Rank value to update it visually too.
    const computedRankRow = document.getElementById('computed-rank-preview');

    // --- Create Value Display for Sliders ---
    function addValueDisplay(inputElement, unit = "") {
        if (!inputElement || inputElement.type !== 'range') return;
        
        // Check if display already exists
        if (inputElement.nextElementSibling && inputElement.nextElementSibling.classList.contains('range-value')) {
            return;
        }

        // Create the span
        const displaySpan = document.createElement('span');
        displaySpan.className = 'range-value';
        displaySpan.style.marginLeft = '10px';
        displaySpan.style.fontWeight = 'bold';
        displaySpan.style.minWidth = '30px';
        displaySpan.style.display = 'inline-block';
        
        // Insert after input
        inputElement.parentNode.insertBefore(displaySpan, inputElement.nextSibling);

        // Update function
        const updateDisplay = () => {
            displaySpan.textContent = `${inputElement.value}${unit}`;
        };

        // Attach listeners
        inputElement.addEventListener('input', updateDisplay);
        updateDisplay(); // Init
    }

    // Initialize Displays
    addValueDisplay(inputEffort, "/10");
    addValueDisplay(inputImpact, "/5");
    addValueDisplay(inputFear, "x");

    // --- Logic ---

    function calculateRankAndXP() {
        if (!previewSpan) return;

        // 1. Calculate Score (Replicating Python Logic)
        const duration = parseInt(inputDuration?.value || 15);
        const effort = parseInt(inputEffort?.value || 1);
        const impact = parseInt(inputImpact?.value || 1);
        const fear = parseFloat(inputFear?.value || 1.0);

        const durationScore = Math.min(duration, 240); // Cap at 4 hours
        // Formula: ((Duration * 0.25) + (Effort * 1.5) + (Impact^3)) * FearFactor
        const baseScore = (durationScore * 0.25) + (effort * 1.5) + (Math.pow(impact, 3));
        const totalScore = baseScore * fear;

        // 2. Determine Computed Rank
        let computedRank = "E";
        if (totalScore <= 20) computedRank = "E";
        else if (totalScore <= 45) computedRank = "D";
        else if (totalScore <= 75) computedRank = "C";
        else if (totalScore <= 120) computedRank = "B";
        else if (totalScore <= 180) computedRank = "A";
        else if (totalScore <= 250) computedRank = "S";
        else if (totalScore <= 280) computedRank = "SS";
        else computedRank = "Monarch";

        // Update the Readonly Computed Rank UI (Visual only)
        if (computedRankRow) {
            computedRankRow.textContent = `${computedRank}-Rank (Score: ${totalScore.toFixed(1)})`;
        }

        // 3. Determine Final Rank (Manual overrides Computed)
        const manualRank = inputManualRank?.value;
        const finalRank = manualRank || computedRank;
        
        // 4. Get XP Reward
        const totalXP = RANK_XP[finalRank] || 15;

        // 5. Calculate Split
        const pStat = inputPrimary?.value || 'STR';
        const sStat = inputSecondary?.value;

        let outputText = "";

        if (!sStat || sStat === pStat) {
            // Case 1: 100% Primary
            outputText = `${pStat}: ${totalXP} XP`;
        } else {
            // Case 2: 60/40 Split
            const pAmount = Math.floor(totalXP * 0.60);
            const sAmount = totalXP - pAmount; // Remainder ensures no rounding loss
            outputText = `${pStat}: ${pAmount} XP, ${sStat}: ${sAmount} XP`;
        }

        // 6. Render
        previewSpan.textContent = outputText;
        
        // Optional: Color coding
        if (manualRank) {
            previewSpan.style.color = "#d35400"; // Orange if manual override
        } else {
            previewSpan.style.color = "#27ae60"; // Green if auto
        }
    }

    // --- Event Listeners ---
    const inputs = [
        inputPrimary, inputSecondary, inputManualRank,
        inputDuration, inputEffort, inputImpact, inputFear
    ];

    inputs.forEach(input => {
        if (input) {
            input.addEventListener('change', calculateRankAndXP);
            input.addEventListener('keyup', calculateRankAndXP); // For immediate feedback
        }
    });

    // Run once on load to set initial state
    calculateRankAndXP();
});