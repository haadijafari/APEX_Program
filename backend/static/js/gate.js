/* backend/static/js/gate.js */

/**
 * ==========================================
 * GATE API LAYER
 * Handles all server communication.
 * ==========================================
 */
class GateAPI {
    static getCookie(name) {
        if (!document.cookie) return null;
        const xsrfCookies = document.cookie.split(';')
            .map(c => c.trim())
            .filter(c => c.startsWith(name + '='));
        return xsrfCookies.length ? decodeURIComponent(xsrfCookies[0].substring(name.length + 1)) : null;
    }

    static async autoSave(formElement) {
        const url = formElement.dataset.autosaveUrl || "/gate/autosave/";
        const formData = new FormData(formElement);
        const csrfToken = formElement.querySelector('[name=csrfmiddlewaretoken]')?.value;

        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": csrfToken },
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error("AutoSave Failed:", error);
            throw error;
        }
    }

    static async toggleRoutine(itemId) {
        const url = `/routine/toggle/${itemId}/`;
        const csrfToken = this.getCookie('csrftoken');

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'Content-Type': 'application/json'
                },
            });
            return await response.json();
        } catch (error) {
            console.error("Routine Toggle Failed:", error);
            throw error;
        }
    }
}

/**
 * ==========================================
 * UI MODULE: SLEEP CALCULATOR
 * ==========================================
 */
class SleepModule {
    constructor() {
        this.dom = {
            sleep: document.getElementById('id_sleep_time'),
            wake: document.getElementById('id_wake_up_time'),
            nap: document.getElementById('id_nap_duration'),
            display: document.getElementById('sleepDuration')
        };
        
        if (this.dom.sleep && this.dom.wake) {
            this.initListeners();
            this.calculate();
        }
    }

    initListeners() {
        this.dom.sleep.addEventListener('change', () => this.calculate());
        this.dom.wake.addEventListener('change', () => this.calculate());
        if (this.dom.nap) this.dom.nap.addEventListener('input', () => this.calculate());
    }

    calculate() {
        if (!this.dom.sleep.value || !this.dom.wake.value) {
            this.dom.display.value = "--";
            return;
        }

        const [sH, sM] = this.dom.sleep.value.split(':').map(Number);
        const [wH, wM] = this.dom.wake.value.split(':').map(Number);

        let diffMins = ((wH * 60) + wM) - ((sH * 60) + sM);
        if (diffMins < 0) diffMins += (24 * 60);

        const napHours = this.dom.nap ? (parseFloat(this.dom.nap.value) || 0) : 0;
        diffMins += (napHours * 60);

        const hours = Math.floor(diffMins / 60);
        const minutes = Math.round(diffMins % 60);
        this.dom.display.value = `${hours} hr ${minutes} min`;
    }
}

/**
 * ==========================================
 * UI MODULE: DAILY LOG FORM
 * Handles AutoSave, Emoji Picking, and Dynamic Highlights
 * ==========================================
 */
class DailyLogForm {
    constructor(formId) {
        this.form = document.getElementById(formId);
        this.statusIndicator = document.getElementById('save-status');
        
        if (!this.form) return;

        this.debouncedSave = this.debounce(this.performSave.bind(this), 1000);
        this.initAutoSave();
        this.initEmojiPicker();
        this.initScoreBar();
        this.initDynamicRows();
    }

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // --- Auto Save Logic ---
    initAutoSave() {
        // Text Inputs: Debounce
        this.form.addEventListener('input', (e) => {
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) this.debouncedSave();
        });

        // Choices: Immediate
        this.form.addEventListener('change', (e) => {
            if (['radio', 'checkbox'].includes(e.target.type) || e.target.tagName === 'SELECT' || e.target.type === 'time') {
                this.performSave();
            }
        });
    }

    async performSave() {
        this.updateStatus("Saving...", "text-secondary");
        try {
            const data = await GateAPI.autoSave(this.form);
            if (data.status === 'success') {
                this.updateStatus("Saved", "text-success");
                setTimeout(() => this.updateStatus("", ""), 2000);
            } else {
                this.updateStatus("Error", "text-danger");
            }
        } catch {
            this.updateStatus("Offline", "text-danger");
        }
    }

    updateStatus(text, colorClass) {
        if (!this.statusIndicator) return;
        this.statusIndicator.textContent = text;
        this.statusIndicator.className = `small fw-bold text-uppercase ${colorClass}`;
    }

    // --- Emoji Picker ---
    initEmojiPicker() {
        const input = document.getElementById('mood-picker-input');
        const slot = document.getElementById('mood-slot-container');
        const popover = document.getElementById('emoji-popover');
        const picker = document.querySelector('emoji-picker');

        if (!input || !slot || !popover || !picker) return;

        picker.dataSource = '/static/vendor/emoji-picker/data.json';

        slot.addEventListener('click', (e) => {
            if (popover.contains(e.target)) return;
            e.preventDefault();
            popover.style.display = popover.style.display === 'block' ? 'none' : 'block';
        });

        picker.addEventListener('emoji-click', (e) => {
            input.value = e.detail.unicode;
            popover.style.display = 'none';
            slot.classList.add('has-mood');
            this.performSave(); // Immediate save
        });

        document.addEventListener('click', (e) => {
            if (!slot.contains(e.target) && !popover.contains(e.target)) {
                popover.style.display = 'none';
            }
        });

        if (input.value) slot.classList.add('has-mood');
    }

    // --- Score Bar ---
    initScoreBar() {
        const container = document.getElementById('score-container');
        if (!container) return;

        const updateVisuals = () => {
            const val = parseInt(container.querySelector('input:checked')?.value || 0);
            container.querySelectorAll('.score-label').forEach(lbl => {
                const lvl = parseInt(lbl.getAttribute('data-value'));
                lbl.classList.toggle('is-active', lvl <= val);
            });
        };
        
        container.addEventListener('change', updateVisuals);
        updateVisuals();
    }

    // --- Dynamic Highlights (Add/Delete Rows) ---
    initDynamicRows() {
        this.form.addEventListener('click', (e) => {
            const addBtn = e.target.closest('[data-add-row]');
            if (addBtn) this.addFormRow(addBtn.dataset.prefix);

            const delBtn = e.target.closest('.btn-delete-row');
            if (delBtn) {
                const row = delBtn.closest('.highlight-row');
                row.querySelector('input[name$="-DELETE"]').checked = true;
                row.style.display = 'none';
                this.performSave();
            }
        });
    }

    addFormRow(prefix) {
        const container = document.getElementById(`${prefix}-container`);
        const totalInput = document.getElementById(`id_${prefix}-TOTAL_FORMS`);
        const template = document.getElementById(`${prefix}-empty-form`);

        if (!container || !totalInput || !template) return;

        const count = parseInt(totalInput.value);
        const newHtml = template.innerHTML.replace(/__prefix__/g, count);
        container.insertAdjacentHTML('beforeend', newHtml);
        totalInput.value = count + 1;
        
        const inputs = container.querySelectorAll('input[type="text"]');
        if (inputs.length) inputs[inputs.length - 1].focus();
    }
}

/**
 * ==========================================
 * BOOTSTRAPPER
 * ==========================================
 */
document.addEventListener('DOMContentLoaded', () => {
    if (window.HAS_GATE_JS_LOADED) return;
    window.HAS_GATE_JS_LOADED = true;

    console.log("🚀 Gate.js Initialized (Refactored)");

    new SleepModule();
    new DailyLogForm('dayPageForm');

    // Global helper for the Sidebar Routines
    window.toggleTask = async function(itemId) {
        try {
            const data = await GateAPI.toggleRoutine(itemId);
            console.log(`Routine ${data.item_id}: ${data.status}`);
        } catch {
            // Revert checkbox on failure
            const cb = document.getElementById(`item${itemId}`);
            if (cb) cb.checked = !cb.checked;
        }
    };
});
