(function() {
    // 1. IDEMPOTENCY GUARD: Prevent double-loading
    if (window.HAS_GATE_JS_LOADED) {
        console.warn("⚠️ Gate.js attempted to load a second time. Skipping.");
        return;
    }
    window.HAS_GATE_JS_LOADED = true;

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

    static get headers() {
        return {
            "X-CSRFToken": this.getCookie('csrftoken'),
            "X-Requested-With": "XMLHttpRequest"
        };
    }

    static async autoSave(formElement) {
        const url = formElement.dataset.autosaveUrl || "/gate/autosave/";
        const formData = new FormData(formElement);
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": this.getCookie('csrftoken') },
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error("AutoSave Failed:", error);
            throw error;
        }
    }

    static async toggleTaskStatus(taskId) {
        const url = `/task/toggle/${taskId}/`; 
        
        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: this.headers,
            });
            return await response.json();
        } catch (error) {
            console.error("Task Toggle Failed:", error);
            throw error;
        }
    }

    static async createTask(formData) {
        const url = "/task/add/"; // Ensure this matches your urls.py
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": this.getCookie('csrftoken') }, // No Content-Type for FormData
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error("Create Task Failed:", error);
            throw error;
        }
    }

    static async archiveTask(taskId) {
        const url = `/task/${taskId}/archive/`;
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: this.headers
            });
            return await response.json();
        } catch (error) {
            console.error("Archive Task Failed:", error);
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
        let totalMinutes = 0;

        // 1. Calculate Night Sleep (Only if BOTH values are present)
        if (this.dom.sleep.value && this.dom.wake.value) {
            const [sH, sM] = this.dom.sleep.value.split(':').map(Number);
            const [wH, wM] = this.dom.wake.value.split(':').map(Number);

            let nightMins = ((wH * 60) + wM) - ((sH * 60) + sM);
            // Handle crossing midnight (e.g. 23:00 to 07:00)
            if (nightMins < 0) nightMins += (24 * 60);
            
            totalMinutes += nightMins;
        }

        // 2. Add Nap Time (Always add if present)
        const napHours = this.dom.nap ? (parseFloat(this.dom.nap.value) || 0) : 0;
        totalMinutes += (napHours * 60);

        // 3. Handle Empty State
        // If total is 0 and inputs are empty, show "--"
        if (totalMinutes === 0 && !this.dom.sleep.value && !this.dom.wake.value && !napHours) {
            this.dom.display.value = "--";
            return;
        }

        // 4. Format and Display
        const hours = Math.floor(totalMinutes / 60);
        const minutes = Math.round(totalMinutes % 60);
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
        
        if (!this.form) return;

        // State for locking
        this.isSaving = false;
        this.pendingSave = false;

        // Store the specific status element that requested the save
        this.pendingStatusEl = null;

        // Debounce passing arguments correctly
        this.debouncedSave = this.debounce((statusEl) => this.performSave(statusEl), 1000);
        
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
        // Helper to find the correct status element based on the event target
        const getStatusElement = (target) => {
            const section = target.closest('.js-autosave-section');
            // Fallback to global ID if section not found or section has no status
            return (section && section.querySelector('.js-section-status')) 
                   || document.getElementById('global-save-status')
                   || document.getElementById('save-status'); // Legacy fallback
        };

        // Text Inputs: Debounce
        this.form.addEventListener('input', (e) => {
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                const statusEl = getStatusElement(e.target);
                this.debouncedSave(statusEl);
            }
        });

        // Choices: Immediate
        this.form.addEventListener('change', (e) => {
            if (['radio', 'checkbox'].includes(e.target.type) || e.target.tagName === 'SELECT' || e.target.type === 'time') {
                const statusEl = getStatusElement(e.target);
                this.performSave(statusEl);
            }
        });
    }

    async performSave(statusEl) {
        // LOCK CHECK: If already saving, queue a retry and exit
        if (this.isSaving) {
            this.pendingSave = true;
            // Update the pending status element so the retry highlights the latest edit
            if (statusEl) this.pendingStatusEl = statusEl;
            return;
        }

        // SET LOCK
        this.isSaving = true;

        // Use the passed element, or if coming from pending queue, use the stored one
        const currentStatusEl = statusEl || this.pendingStatusEl;
        this.pendingStatusEl = null; // Reset pending target

        this.updateStatus(currentStatusEl, "Saving...", "text-secondary");

        try {
            const data = await GateAPI.autoSave(this.form);
            if (data.status === 'success') {
                this.updateStatus(currentStatusEl, "Saved", "text-success");

                // Sync backend IDs to frontend to prevent duplicates on next save
                if (data.new_ids) {
                    Object.entries(data.new_ids).forEach(([inputName, newId]) => {
                        const idInput = this.form.querySelector(`input[name="${inputName}"]`);
                        if (idInput) {
                            idInput.value = newId;
                        }
                    });
                }

                // Update INITIAL_FORMS Counters
                // This tells Django that these rows are now "Existing" records,
                // preventing it from creating duplicates on the next save.
                ['pos', 'neg'].forEach(prefix => {
                    const initialInput = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
                    if (initialInput) {
                        // Count how many rows now have a valid database ID
                        const validIds = Array.from(
                            this.form.querySelectorAll(`input[name^="${prefix}-"][name$="-id"]`)
                        ).filter(input => input.value !== "").length;
                        
                        initialInput.value = validIds;
                    }
                });

                setTimeout(() => this.updateStatus(currentStatusEl, "", ""), 2000);
            } else {
                this.updateStatus(currentStatusEl, "Error", "text-danger");
            }
        } catch (error) {
            console.error(error);
            this.updateStatus(currentStatusEl, "Offline", "text-danger");
        } finally {
            // RELEASE LOCK & HANDLE QUEUE
            this.isSaving = false;
            
            if (this.pendingSave) {
                this.pendingSave = false;
                // Recursive call to handle the edits made while we were saving
                this.performSave(this.pendingStatusEl); 
            }
        }
    }

    updateStatus(element, text, colorClass) {
        if (!element) return;
        element.textContent = text;
        element.className = `js-section-status small fw-bold text-uppercase transition-all ${colorClass}`;
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
            
            // Fix: Pass status element for immediate save
            const statusEl = slot.closest('.js-autosave-section')?.querySelector('.js-section-status');
            this.performSave(statusEl); 
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
                
                // Fix: Pass status element for immediate save
                const statusEl = row.closest('.js-autosave-section')?.querySelector('.js-section-status');
                this.performSave(statusEl);
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
 * UI MODULE: TASK MANAGER (NEW)
 * Handles Creation, Archive, and Rendering
 * ==========================================
 */
class TaskManager {
    constructor() {
        this.dom = {
            list: document.getElementById('gate-task-list'),
            form: document.getElementById('gate-add-task-form'),
            modalEl: document.getElementById('taskModal'),
        };

        // Initialize Bootstrap Modal Wrapper
        if (this.dom.modalEl) {
            this.modal = new bootstrap.Modal(this.dom.modalEl);
            this.initCreator();
        }

        // Initialize Archive Listeners
        if (this.dom.list) {
            this.initArchiver();
        }
    }

    // --- Task Creation ---
    initCreator() {
        const saveBtn = this.dom.modalEl.querySelector('.btn-primary');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.handleCreate());
        }
    }

    async handleCreate() {
        // Sync TinyMCE if present
        if (typeof tinymce !== 'undefined') tinymce.triggerSave();

        const formData = new FormData(this.dom.form);
        
        try {
            const data = await GateAPI.createTask(formData);
            
            if (data.status === 'success') {
                this.appendTaskToUI(data.task);
                this.dom.form.reset();
                this.modal.hide();
            } else {
                alert('Error creating task: ' + JSON.stringify(data.errors));
            }
        } catch (error) {
            console.error(error);
            alert('Failed to create task. See console.');
        }
    }

    appendTaskToUI(task) {
        if (!this.dom.list) return;

        // Remove "No active tasks" message if it exists
        const emptyMsg = this.dom.list.querySelector('.text-center');
        if (emptyMsg) emptyMsg.remove();

        const html = `
            <div class="list-group-item d-flex justify-content-between align-items-center task-item" id="task-row-${task.id}">
                <div class="d-flex align-items-center">
                    <input class="form-check-input me-2" 
                           type="checkbox" 
                           onclick="toggleTask(${task.id})">
                    <div class="ms-2">
                        <div class="fw-bold">${task.title}</div>
                        <small class="text-muted badge bg-dark">${task.rank}</small>
                    </div>
                </div>
                <button class="btn btn-link text-danger p-0 delete-task-btn" data-task-id="${task.id}">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `;
        
        // Append at top or bottom? User preference. Usually top for new things.
        this.dom.list.insertAdjacentHTML('afterbegin', html);
    }

    // --- Task Archiving ---
    initArchiver() {
        this.dom.list.addEventListener('click', async (e) => {
            const btn = e.target.closest('.delete-task-btn');
            if (!btn) return;

            const taskId = btn.dataset.taskId;
            if (confirm("Are you sure you want to remove this task?")) {
                await this.handleArchive(taskId);
            }
        });
    }

    async handleArchive(taskId) {
        try {
            const data = await GateAPI.archiveTask(taskId);
            if (data.status === 'success') {
                const row = document.getElementById(`task-row-${taskId}`);
                if (row) row.remove();
            }
        } catch (error) {
            console.error(error);
        }
    }
}

/**
 * ==========================================
 * BOOTSTRAPPER
 * ==========================================
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Gate.js Initialized");

    new SleepModule();
    new DailyLogForm('dayPageForm');
    new TaskManager();

    // Global helper for Checkboxes (Routines & Tasks)
    // Must be explicitly attached to window to be accessible by HTML onclick=""
    window.toggleTask = async function(itemId) {
        try {
            const data = await GateAPI.toggleTaskStatus(itemId);
            console.log(`Task ${itemId}: ${data.status}`);
            
            // Optional: Visually strike-through if needed, 
            // though CSS often handles this via :checked sibling selectors if structured correctly.
        } catch {
            // Revert checkbox on failure
            const cb = document.querySelector(`input[onclick="toggleTask(${itemId})"]`);
            if (cb) cb.checked = !cb.checked;
        }
    };
});

})(); // End IIFE