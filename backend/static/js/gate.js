/* backend/static/js/gate.js */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================
    // 1. SLEEP CALCULATOR
    // ==========================================
    const sleepInput = document.getElementById('id_sleep_time');
    const wakeInput = document.getElementById('id_wake_up_time');
    const napInput = document.getElementById('id_nap_duration');
    const durationDisplay = document.getElementById('sleepDuration');

    function calculateDuration() {
        // Safety check: Do elements exist?
        if (!sleepInput || !wakeInput || !durationDisplay) return;
        
        // If empty, show placeholder
        if (!sleepInput.value || !wakeInput.value) {
            durationDisplay.value = "--";
            return;
        }

        // Parse Hours and Minutes
        const [sleepH, sleepM] = sleepInput.value.split(':').map(Number);
        const [wakeH, wakeM] = wakeInput.value.split(':').map(Number);

        let sleepTotalMins = (sleepH * 60) + sleepM;
        let wakeTotalMins = (wakeH * 60) + wakeM;

        // Calculate difference
        let diffMins = wakeTotalMins - sleepTotalMins;
        
        // Handle midnight crossing (e.g., Sleep 23:00, Wake 07:00)
        if (diffMins < 0) {
            diffMins += (24 * 60); 
        }

        // Add Nap Time
        let napHours = napInput ? (parseFloat(napInput.value) || 0) : 0;
        let napMins = napHours * 60;

        let totalMins = diffMins + napMins;

        // Format Output (e.g., "8 hr 30 min")
        const finalHours = Math.floor(totalMins / 60);
        const finalMinutes = Math.round(totalMins % 60);

        durationDisplay.value = `${finalHours} hr ${finalMinutes} min`;
    }

    // Attach Event Listeners
    if (sleepInput && wakeInput) {
        sleepInput.addEventListener('change', calculateDuration);
        wakeInput.addEventListener('change', calculateDuration);
        if (napInput) napInput.addEventListener('input', calculateDuration);
        
        // Run once on load to populate fields if data exists
        calculateDuration();
    }


    // ==========================================
    // 2. EMOJI PICKER INTERACTION
    // ==========================================
    const emojiInput = document.getElementById('mood-picker-input');
    const moodSlot = document.getElementById('mood-slot-container'); 
    const popover = document.getElementById('emoji-popover');
    const picker = document.querySelector('emoji-picker');

    if (emojiInput && popover && picker && moodSlot) {

        picker.dataSource = '/static/vendor/emoji-picker/data.json';
        
        // Toggle Picker on SLOT Click
        moodSlot.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            const isVisible = popover.style.display === 'block';
            popover.style.display = isVisible ? 'none' : 'block';
        });

        // Handle Emoji Selection
        picker.addEventListener('emoji-click', (event) => {
            emojiInput.value = event.detail.unicode; // Fill input
            popover.style.display = 'none'; // Hide popup
        });

        // Close when clicking outside
        document.addEventListener('click', (e) => {
            // If click is NOT on the slot AND NOT on the popup, close it
            if (!moodSlot.contains(e.target) && !popover.contains(e.target)) {
                popover.style.display = 'none';
            }
        });
    }

    // ==========================================
    // 3. SCORE BAR VISUALS (Fill Effect)
    // ==========================================
    const scoreContainer = document.getElementById('score-container');
    
    function updateScoreVisuals() {
        if (!scoreContainer) return;
        
        // Find which radio is currently checked
        const checkedInput = scoreContainer.querySelector('input[type="radio"]:checked');
        const currentVal = checkedInput ? parseInt(checkedInput.value) : 0;

        // Loop through all labels and add/remove 'is-active' class
        const labels = scoreContainer.querySelectorAll('.score-label');
        labels.forEach(label => {
            const labelVal = parseInt(label.getAttribute('data-value'));
            if (labelVal <= currentVal) {
                label.classList.add('is-active');
            } else {
                label.classList.remove('is-active');
            }
        });
    }

    // Run on load (in case of validation error/reload)
    updateScoreVisuals();

    // Run on change
    if (scoreContainer) {
        scoreContainer.addEventListener('change', updateScoreVisuals);
    }

    // ==========================================
    // 4. MOOD SLOT VISUALS
    // ==========================================
    // Updates the border glow when an emoji is present
    const moodInput = document.getElementById('mood-picker-input');
    const moodSlotContainer = document.getElementById('mood-slot-container');

    function updateMoodVisuals() {
        if (moodInput && moodInput.value) {
            moodSlotContainer.classList.add('has-mood');
        } else if (moodSlotContainer) {
            moodSlotContainer.classList.remove('has-mood');
        }
    }

    if (moodInput) {
        // Run on load
        updateMoodVisuals();
        
        // We need to hook into the emoji picker click event we defined earlier
        const pickerElement = document.querySelector('emoji-picker');
        if (pickerElement) {
            pickerElement.addEventListener('emoji-click', () => {
                // Small delay to allow value to populate
                setTimeout(updateMoodVisuals, 50);
            });
        }
    }
});


// ==========================================
// 5. ROUTINE / TASK TOGGLING
// ==========================================
function toggleRoutineItem(taskId) {
    const url = `/routine/toggle/${taskId}/`;
    const csrftoken = getCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
    })
    .then(response => {
        if (!response.ok) throw new Error('Network response was not ok');
        return response.json();
    })
    .then(data => {
        console.log(`Task ${data.task_id} status: ${data.status}`);

        // --- Update Player Stats (XP, Level) ---
        // Checks if elements exist (e.g., if Player Card is present in layout)
        const elLevel = document.getElementById('player-level');
        const elXPText = document.getElementById('player-xp-text');
        const elXPBar = document.getElementById('player-xp-bar');

        if (elLevel && data.new_level) elLevel.textContent = data.new_level;
        if (elXPText && data.new_xp_current) elXPText.textContent = `${data.new_xp_current} / ${data.new_xp_required}`;
        if (elXPBar && data.new_xp_percent) elXPBar.style.width = `${data.new_xp_percent}%`;

        // --- Update Stats Radar Chart (if it exists on page) ---
        if (window.apexStatsChart && data.new_stats) {
            window.apexStatsChart.data.datasets[0].data = data.new_stats;
            const newMax = Math.max(...data.new_stats);
            window.apexStatsChart.options.scales.r.suggestedMax = newMax + 1;
            window.apexStatsChart.update();
        }
    })
    .catch(error => {
        console.error('Error toggling routine item:', error);
        // Revert Checkbox State on Error
        // Note: HTML ID is "task-123", not "item123"
        const checkbox = document.getElementById(`task-${taskId}`);
        if (checkbox) checkbox.checked = !checkbox.checked;
    });
}

// Helper to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

window.toggleTask = toggleRoutineItem;
