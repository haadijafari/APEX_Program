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
        const url = "/task/add/"; 
        
        try {
            const response = await fetch(url, {
                method: "POST",
                headers: { "X-CSRFToken": this.getCookie('csrftoken') }, 
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

        if (this.dom.sleep.value && this.dom.wake.value) {
            const [sH, sM] = this.dom.sleep.value.split(':').map(Number);
            const [wH, wM] = this.dom.wake.value.split(':').map(Number);

            let nightMins = ((wH * 60) + wM) - ((sH * 60) + sM);
            if (nightMins < 0) nightMins += (24 * 60);
            
            totalMinutes += nightMins;
        }

        const napHours = this.dom.nap ? (parseFloat(this.dom.nap.value) || 0) : 0;
        totalMinutes += (napHours * 60);

        if (totalMinutes === 0 && !this.dom.sleep.value && !this.dom.wake.value && !napHours) {
            this.dom.display.value = "--";
            return;
        }

        const hours = Math.floor(totalMinutes / 60);
        const minutes = Math.round(totalMinutes % 60);
        this.dom.display.value = `${hours} hr ${minutes} min`;
    }
}

/**
 * ==========================================
 * UI MODULE: DAILY LOG FORM
 * ==========================================
 */
class DailyLogForm {
    constructor(formId) {
        this.form = document.getElementById(formId);
        
        if (!this.form) return;

        this.isSaving = false;
        this.pendingSave = false;
        this.pendingStatusEl = null;

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

    initAutoSave() {
        const getStatusElement = (target) => {
            const section = target.closest('.js-autosave-section');
            return (section && section.querySelector('.js-section-status')) 
                   || document.getElementById('global-save-status')
                   || document.getElementById('save-status');
        };

        this.form.addEventListener('input', (e) => {
            if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                const statusEl = getStatusElement(e.target);
                this.debouncedSave(statusEl);
            }
        });

        this.form.addEventListener('change', (e) => {
            if (['radio', 'checkbox'].includes(e.target.type) || e.target.tagName === 'SELECT' || e.target.type === 'time') {
                const statusEl = getStatusElement(e.target);
                this.performSave(statusEl);
            }
        });
    }

    async performSave(statusEl) {
        if (this.isSaving) {
            this.pendingSave = true;
            if (statusEl) this.pendingStatusEl = statusEl;
            return;
        }

        this.isSaving = true;
        const currentStatusEl = statusEl || this.pendingStatusEl;
        this.pendingStatusEl = null;

        this.updateStatus(currentStatusEl, "Saving...", "text-secondary");

        try {
            const data = await GateAPI.autoSave(this.form);
            if (data.status === 'success') {
                this.updateStatus(currentStatusEl, "Saved", "text-success");

                if (data.new_ids) {
                    Object.entries(data.new_ids).forEach(([inputName, newId]) => {
                        const idInput = this.form.querySelector(`input[name="${inputName}"]`);
                        if (idInput) {
                            idInput.value = newId;
                        }
                    });
                }

                ['pos', 'neg'].forEach(prefix => {
                    const initialInput = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
                    if (initialInput) {
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
            this.isSaving = false;
            
            if (this.pendingSave) {
                this.pendingSave = false;
                this.performSave(this.pendingStatusEl); 
            }
        }
    }

    updateStatus(element, text, colorClass) {
        if (!element) return;
        element.textContent = text;
        element.className = `js-section-status small fw-bold text-uppercase transition-all ${colorClass}`;
    }

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

    initDynamicRows() {
        this.form.addEventListener('click', (e) => {
            const addBtn = e.target.closest('[data-add-row]');
            if (addBtn) this.addFormRow(addBtn.dataset.prefix);

            const delBtn = e.target.closest('.btn-delete-row');
            if (delBtn) {
                const row = delBtn.closest('.highlight-row');
                row.querySelector('input[name$="-DELETE"]').checked = true;
                row.style.display = 'none';
                
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
 * UI MODULE: TASK MANAGER
 * Handles Creation, Archive, and Rendering
 * ==========================================
 */
class TaskManager {
    constructor() {
        this.dom = {
            list: document.getElementById('pending-tasks-list'),
            form: document.getElementById('gate-add-task-form'),
            modalEl: document.getElementById('taskModal'),
        };

        if (this.dom.modalEl) {
            this.modal = new bootstrap.Modal(this.dom.modalEl);
            this.initCreator();
        }
    }

    initCreator() {
        const saveBtn = this.dom.modalEl.querySelector('.btn-primary');
        if (saveBtn) {
            saveBtn.addEventListener('click', () => this.handleCreate());
        }
    }

    async handleCreate() {
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
        const emptyMsg = this.dom.list.querySelector('.empty-msg');
        if (emptyMsg) emptyMsg.remove();

        // 1. Create a container first to easily access DOM elements
        const wrapper = document.createElement('div');
        
        // 2. Build HTML Structure
        wrapper.innerHTML = `
            <div class="list-group-item d-flex justify-content-between align-items-center task-item" id="task-row-${task.id}">
                <div class="d-flex align-items-center">
                    <input class="form-check-input me-2" 
                           type="checkbox" 
                           onclick="toggleTask(${task.id})">
                    <div class="ms-2">
                        <div class="fw-bold task-title">${task.title}</div>
                        <small class="text-muted badge bg-dark">${task.rank}-Rank</small>
                    </div>
                </div>
                <button class="btn btn-link text-danger p-0 delete-task-btn" onclick="archiveTask(${task.id})">
                    <i class="bi bi-x"></i>
                </button>
            </div>
        `;

        const row = wrapper.firstElementChild;
        
        // 3. Initialize Popover if description exists
        if (task.description) {
            const titleEl = row.querySelector('.task-title');
            new bootstrap.Popover(titleEl, {
                content: task.description,
                html: true,
                trigger: 'hover',
                placement: 'top'
            });
        }
        
        // 4. Append to list
        this.dom.list.insertAdjacentElement('beforeend', row);
    }
}

/**
 * ==========================================
 * BOOTSTRAPPER
 * ==========================================
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Gate.js Initialized");

    // Initialize Global Tooltips/Popovers (for server-rendered items)
    const popoverTriggerList = document.querySelectorAll('[data-bs-toggle="popover"]');
    [...popoverTriggerList].map(popoverTriggerEl => new bootstrap.Popover(popoverTriggerEl));

    new SleepModule();
    new DailyLogForm('dayPageForm');
    new TaskManager();

    // --- GLOBAL ACTIONS ---

    // 1. Toggle Task (Moves between Pending and Done)
    window.toggleTask = async function(itemId) {
        try {
            const data = await GateAPI.toggleTaskStatus(itemId);
            console.log(`Task ${itemId}: ${data.status}`);
            
            const row = document.getElementById(`task-row-${itemId}`);
            if (!row) return;

            const pendingList = document.getElementById('pending-tasks-list');
            const doneList = document.getElementById('done-tasks-list');
            const titleEl = row.querySelector('.fw-bold');

            // Logic for Standalone Tasks
            if (pendingList && doneList && (pendingList.contains(row) || doneList.contains(row))) {
                if (data.status === 'added') {
                    // Move to Done
                    doneList.appendChild(row);
                    if (titleEl) titleEl.classList.add('text-decoration-line-through');
                } else {
                    // Move to Pending
                    pendingList.appendChild(row);
                    if (titleEl) titleEl.classList.remove('text-decoration-line-through');
                }

                // Handle Empty State
                const emptyMsg = pendingList.querySelector('.empty-msg');
                const hasTasks = pendingList.querySelectorAll('.task-item').length > 0;
                
                if (!hasTasks && !emptyMsg) {
                    pendingList.insertAdjacentHTML('beforeend', '<div class="text-center text-muted py-3 empty-msg">No active tasks.</div>');
                } else if (hasTasks && emptyMsg) {
                    emptyMsg.remove();
                }
            }
            
        } catch (err) {
            console.error(err);
            // Revert checkbox
            const cb = document.querySelector(`input[onclick="toggleTask(${itemId})"]`);
            if (cb) cb.checked = !cb.checked;
        }
    };

    // 2. Archive Task
    window.archiveTask = async function(taskId) {
        if (!confirm("Are you sure you want to remove this task?")) return;
        
        try {
            const data = await GateAPI.archiveTask(taskId);
            if (data.status === 'success') {
                const row = document.getElementById(`task-row-${taskId}`);
                if (row) {
                    // Dispose popover before removing to avoid memory leaks
                    const titleEl = row.querySelector('[data-bs-toggle="popover"]');
                    if (titleEl) {
                        const popover = bootstrap.Popover.getInstance(titleEl);
                        if (popover) popover.dispose();
                    }
                    row.remove();
                }
            }
        } catch (error) {
            console.error(error);
        }
    };
});

})();
