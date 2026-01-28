/* backend/static/js/gate.js */

/**
 * GATE MODULE
 * Handles the interactivity for the Daily Log (Gate) page.
 * Includes: Sleep Calculator, Emoji Picker, Energy Bar Visuals, and Auto-Save.
 */

// ==========================================
// 1. IDEMPOTENCY GUARD
// ==========================================
// Prevents the script from running twice if injected multiple times by Django/Tools.
if (window.HAS_GATE_JS_LOADED) {
    console.warn("⚠️ Gate.js attempted to load a second time. Skipping.");
} else {
    window.HAS_GATE_JS_LOADED = true;

    document.addEventListener('DOMContentLoaded', () => {
        initGate();
    });
}

/**
 * Main Initialization Function
 * bootstraps all sub-modules safely.
 */
function initGate() {
    console.log("🚀 Gate.js Initialized");

    // Initialize Sub-Modules
    initSleepCalculator();
    initEmojiPicker();
    initScoreBar();
    initAutoSave();
}


// ==========================================
// 2. SHARED UTILITIES
// ==========================================

/**
 * Debounce helper to limit how often a function runs (e.g., for auto-save).
 * @param {Function} func - The function to debounce
 * @param {number} wait - Time in ms to wait before running
 */
function debounce(func, wait) {
    let timeout;
    return function(...args) {
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(this, args), wait);
    };
}

/**
 * Safe wrapper to retrieve CSRF token from cookies.
 */
function getCookie(name) {
    if (!document.cookie) return null;
    const xsrfCookies = document.cookie.split(';')
        .map(c => c.trim())
        .filter(c => c.startsWith(name + '='));

    if (xsrfCookies.length === 0) return null;
    return decodeURIComponent(xsrfCookies[0].substring(name.length + 1));
}


// ==========================================
// 3. SLEEP CALCULATOR MODULE
// ==========================================
function initSleepCalculator() {
    const sleepInput = document.getElementById('id_sleep_time');
    const wakeInput = document.getElementById('id_wake_up_time');
    const napInput = document.getElementById('id_nap_duration');
    const durationDisplay = document.getElementById('sleepDuration');

    // Exit if elements are missing
    if (!sleepInput || !wakeInput || !durationDisplay) return;

    function calculateDuration() {
        if (!sleepInput.value || !wakeInput.value) {
            durationDisplay.value = "--";
            return;
        }

        // Parse Times (HH:MM)
        const [sleepH, sleepM] = sleepInput.value.split(':').map(Number);
        const [wakeH, wakeM] = wakeInput.value.split(':').map(Number);

        const sleepTotalMins = (sleepH * 60) + sleepM;
        const wakeTotalMins = (wakeH * 60) + wakeM;

        // Calculate Difference (handle crossing midnight)
        let diffMins = wakeTotalMins - sleepTotalMins;
        if (diffMins < 0) diffMins += (24 * 60);

        // Add Nap Time
        const napHours = napInput ? (parseFloat(napInput.value) || 0) : 0;
        diffMins += (napHours * 60);

        // Format Output
        const finalHours = Math.floor(diffMins / 60);
        const finalMinutes = Math.round(diffMins % 60);

        durationDisplay.value = `${finalHours} hr ${finalMinutes} min`;
    }

    // Attach Listeners
    sleepInput.addEventListener('change', calculateDuration);
    wakeInput.addEventListener('change', calculateDuration);
    if (napInput) napInput.addEventListener('input', calculateDuration);

    // Initial calculation on load
    calculateDuration();
}


// ==========================================
// 4. EMOJI PICKER MODULE
// ==========================================
function initEmojiPicker() {
    const elements = {
        input: document.getElementById('mood-picker-input'),
        slot: document.getElementById('mood-slot-container'),
        popover: document.getElementById('emoji-popover'),
        picker: document.querySelector('emoji-picker')
    };

    // Safety Check: Ensure all parts of the picker exist
    if (!elements.input || !elements.slot || !elements.popover || !elements.picker) {
        return; 
    }

    // Set Data Source (Local JSON for speed)
    elements.picker.dataSource = '/static/vendor/emoji-picker/data.json';

    // 1. Toggle Popover on Slot Click
    elements.slot.addEventListener('click', (e) => {
        // Prevent closing if clicking *inside* the popover itself (while it's open)
        if (elements.popover.contains(e.target)) return;

        e.preventDefault();
        e.stopPropagation();

        const isVisible = elements.popover.style.display === 'block';
        elements.popover.style.display = isVisible ? 'none' : 'block';
    });

    // 2. Handle Emoji Selection
    elements.picker.addEventListener('emoji-click', (event) => {
        // Update hidden input
        elements.input.value = event.detail.unicode;
        
        // Hide popover
        elements.popover.style.display = 'none';

        // Trigger updates
        triggerAutoSave(); // Save new mood immediately
        updateMoodVisuals(); // Update glow effect
    });

    // 3. Close when clicking outside
    document.addEventListener('click', (e) => {
        const isClickInside = elements.slot.contains(e.target) || elements.popover.contains(e.target);
        if (!isClickInside) {
            elements.popover.style.display = 'none';
        }
    });

    // Initial Visual Check
    updateMoodVisuals();
}

/**
 * Updates the CSS class of the mood slot based on whether an emoji is selected.
 * Adds 'has-mood' class for glowing effects.
 */
function updateMoodVisuals() {
    const input = document.getElementById('mood-picker-input');
    const slot = document.getElementById('mood-slot-container');
    
    if (input && slot) {
        if (input.value) slot.classList.add('has-mood');
        else slot.classList.remove('has-mood');
    }
}


// ==========================================
// 5. SCORE BAR MODULE (Energy Meter)
// ==========================================
function initScoreBar() {
    const container = document.getElementById('score-container');
    if (!container) return;

    function renderVisuals() {
        const checkedInput = container.querySelector('input[type="radio"]:checked');
        const currentVal = checkedInput ? parseInt(checkedInput.value) : 0;
        const labels = container.querySelectorAll('.score-label');

        labels.forEach(label => {
            const labelVal = parseInt(label.getAttribute('data-value'));
            // Highlight all bars up to the selected value
            if (labelVal <= currentVal) {
                label.classList.add('is-active');
            } else {
                label.classList.remove('is-active');
            }
        });
    }

    // Init & Listener
    renderVisuals();
    container.addEventListener('change', renderVisuals);
}


// ==========================================
// 6. AUTO-SAVE MODULE
// ==========================================

// Expose trigger globally so other modules (like Emoji) can call it
let triggerAutoSave = () => {}; 

function initAutoSave() {
    const form = document.getElementById('dayPageForm');
    const statusIndicator = document.getElementById('save-status');

    if (!form) return;

    /**
     * Performs the actual AJAX save
     */
    function saveData() {
        // UI: Saving...
        if (statusIndicator) {
            statusIndicator.textContent = "Saving...";
            statusIndicator.className = "small fw-bold text-uppercase text-secondary";
        }

        const formData = new FormData(form);
        const url = form.dataset.autosaveUrl || "/gate/autosave/";
        
        // Fetch CSRF Token safely
        const csrfInput = form.querySelector('[name=csrfmiddlewaretoken]');
        const csrfToken = csrfInput ? csrfInput.value : "";

        fetch(url, {
            method: "POST",
            headers: { "X-CSRFToken": csrfToken },
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                // UI: Saved
                if (statusIndicator) {
                    statusIndicator.textContent = "Saved";
                    statusIndicator.className = "small fw-bold text-uppercase text-success";
                    setTimeout(() => {
                        if (statusIndicator.textContent === "Saved") statusIndicator.textContent = "";
                    }, 2000);
                }
            } else {
                console.error("Auto-Save Error:", data.errors);
                if (statusIndicator) {
                    statusIndicator.textContent = "Error";
                    statusIndicator.className = "small fw-bold text-uppercase text-danger";
                }
            }
        })
        .catch(err => {
            console.error("Auto-Save Network Error:", err);
            if (statusIndicator) statusIndicator.textContent = "Offline";
        });
    }

    // Create Debounced Version (Wait 1s after typing stops)
    const debouncedSave = debounce(saveData, 1000);
    
    // Assign to global trigger (for immediate saves like Radio buttons)
    triggerAutoSave = saveData;

    // Attach Listeners
    // 1. Text Inputs: Debounce to prevent spamming
    form.addEventListener('input', (e) => {
        if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
            debouncedSave();
        }
    });

    // 2. Choice Inputs: Save Immediately
    form.addEventListener('change', (e) => {
        if (e.target.type === 'radio' || e.target.tagName === 'SELECT' || e.target.type === 'time') {
            saveData();
        }
    });
}


// ==========================================
// 7. GLOBAL UTILITIES (External Access)
// ==========================================

// Used by the Routine Checkboxes in the Sidebar
window.toggleTask = function(itemId) {
    const url = `/routine/toggle/${itemId}/`;
    const csrftoken = getCookie('csrftoken');

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'Content-Type': 'application/json'
        },
    })
    .then(res => res.json())
    .then(data => console.log(`Routine Item ${data.item_id}: ${data.status}`))
    .catch(error => {
        console.error('Routine Toggle Error:', error);
        // Revert checkbox visual on failure
        const checkbox = document.getElementById(`item${itemId}`);
        if (checkbox) checkbox.checked = !checkbox.checked;
    });
};
