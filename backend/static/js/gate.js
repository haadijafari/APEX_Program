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
        if (diffMins < 0) diffMins += (24 * 60); 

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
    // 5. AUTO SAVE LOGIC
    // ==========================================
    const form = document.getElementById('dayPageForm');
    const statusIndicator = document.getElementById('save-status');

    function saveData() {
        if (!form) return;

        if (statusIndicator) {
            statusIndicator.textContent = "Saving...";
            statusIndicator.className = "small fw-bold text-uppercase text-secondary"; 
        }
        
        const formData = new FormData(form);
        const url = form.dataset.autosaveUrl || "/gate/autosave/";
        
        let csrfToken = "";
        const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfInput) csrfToken = csrfInput.value;

        fetch(url, { 
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                if (statusIndicator) {
                    statusIndicator.textContent = "Saved";
                    statusIndicator.className = "small fw-bold text-uppercase text-success";
                    setTimeout(() => { 
                        if (statusIndicator.textContent === "Saved") {
                            statusIndicator.textContent = ""; 
                        }
                    }, 2000);
                }
            } else {
                console.error("Save errors:", data.errors);
                if (statusIndicator) {
                    statusIndicator.textContent = "Error";
                    statusIndicator.className = "small fw-bold text-uppercase text-danger";
                }
            }
        })
        .catch(err => {
            console.error("Network error:", err);
            if (statusIndicator) statusIndicator.textContent = "Offline";
        });
    }

    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    if (form) {
        const debouncedSave = debounce(saveData, 1000);

        form.addEventListener('input', (e) => {
            if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
                debouncedSave();
            }
        });

        form.addEventListener('change', (e) => {
            if (e.target.type === 'radio' || e.target.tagName === 'SELECT' || e.target.type === 'time') {
                saveData();
            }
        });
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
            emojiInput.value = event.detail.unicode; 
            popover.style.display = 'none'; 
            saveData(); 
            setTimeout(updateMoodVisuals, 50);
        });

        document.addEventListener('click', (e) => {
            // If click is NOT on the slot AND NOT on the popup, close it
            if (!moodSlot.contains(e.target) && !popover.contains(e.target)) {
                popover.style.display = 'none';
            }
        });
    }

    // ==========================================
    // 3. SCORE BAR VISUALS
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
    }
});


function toggleRoutineItem(itemId) {
    const url = `/routine/toggle/${itemId}/`;
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
        console.log(`Item ${data.item_id} status: ${data.status}`);
    })
    .catch(error => {
        console.error('Error toggling routine item:', error);
        const checkbox = document.getElementById(`item${itemId}`);
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
