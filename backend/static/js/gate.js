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
});