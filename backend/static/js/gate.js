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

    // Fetch Task Details
    static async getTaskDetails(taskId) {
        try {
            const response = await fetch(`/task/${taskId}/details/`, { headers: this.headers });
            return await response.json();
        } catch (error) {
            console.error("Get Task Details Failed:", error);
            throw error;
        }
    }

    // Update Task
    static async updateTask(taskId, formData) {
        try {
            const response = await fetch(`/task/${taskId}/update/`, {
                method: "POST",
                headers: { "X-CSRFToken": this.getCookie('csrftoken') },
                body: formData
            });
            return await response.json();
        } catch (error) {
            console.error("Update Task Failed:", error);
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
            saveBtn: document.getElementById('btn-save-task'),
            modalTitle: document.getElementById('taskModalTitle'),
            hiddenId: document.getElementById('task-id-hidden')
        };

        if (this.dom.modalEl) {
            // FIX: Use getOrCreateInstance to share the instance with Bootstrap's data-api
            this.modal = bootstrap.Modal.getOrCreateInstance(this.dom.modalEl);
            this.initSaver();
        }
    }

    initSaver() {
        if (this.dom.saveBtn) {
            // Remove any existing listeners to be safe (though constructor runs once)
            const newBtn = this.dom.saveBtn.cloneNode(true);
            this.dom.saveBtn.parentNode.replaceChild(newBtn, this.dom.saveBtn);
            this.dom.saveBtn = newBtn;
            
            this.dom.saveBtn.addEventListener('click', () => this.handleSave());
        }
    }

    resetForm() {
        if (!this.dom.form) return;
        
        this.dom.form.reset();
        if (this.dom.hiddenId) this.dom.hiddenId.value = '';
        if (this.dom.modalTitle) this.dom.modalTitle.textContent = "Initialize New Task";
        if (this.dom.saveBtn) this.dom.saveBtn.textContent = "Create Task";
        
        // Clear TinyMCE
        if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
            tinymce.activeEditor.setContent('');
        }
    }

    // --- Explicit Create Handler ---
    openCreator() {
        this.resetForm();
        this.modal.show();
    }

    // --- Explicit Edit Handler ---
    async openEditor(taskId) {
        try {
            // 1. Fetch Data
            const data = await GateAPI.getTaskDetails(taskId);
            
            if (data.status === 'success') {
                const task = data.task;
                
                // 2. Populate Hidden ID
                if (this.dom.hiddenId) this.dom.hiddenId.value = task.id;
                
                // 3. Populate Standard Fields
                const setVal = (name, val) => {
                    // Try by Name first (Standard Django)
                    let el = this.dom.form.querySelector(`[name="${name}"]`);
                    // Fallback to ID if name selector fails (Django defaults id="id_field")
                    if (!el) el = this.dom.form.querySelector(`#id_${name}`);
                    
                    if (el) {
                        el.value = (val === null || val === undefined) ? '' : val;
                    }
                };

                setVal('title', task.title);
                setVal('manual_rank', task.manual_rank);
                setVal('duration_minutes', task.duration_minutes);
                setVal('effort_level', task.effort_level);
                setVal('impact_level', task.impact_level);
                setVal('fear_factor', task.fear_factor);
                setVal('primary_stat', task.primary_stat);
                setVal('secondary_stat', task.secondary_stat);

                // 4. Populate TinyMCE (Description)
                if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                     tinymce.activeEditor.setContent(task.description || '');
                } else {
                     setVal('description', task.description);
                }

                // 5. Update Modal UI
                if (this.dom.modalTitle) this.dom.modalTitle.textContent = "Edit Task";
                if (this.dom.saveBtn) this.dom.saveBtn.textContent = "Update Task";

                // 6. Show Modal (Only after population is done)
                this.modal.show();
            }
        } catch (error) {
            console.error("Failed to open editor:", error);
            alert("Failed to load task details. Please try again.");
        }
    }

    async handleSave() {
        if (typeof tinymce !== 'undefined') tinymce.triggerSave();

        const formData = new FormData(this.dom.form);
        const taskId = this.dom.hiddenId ? this.dom.hiddenId.value : null;
        const isUpdate = !!taskId;
        
        try {
            let data;
            if (isUpdate) {
                data = await GateAPI.updateTask(taskId, formData);
            } else {
                data = await GateAPI.createTask(formData);
            }
            
            if (data.status === 'success') {
                if (isUpdate) {
                    this.updateTaskInUI(data.task);
                } else {
                    this.appendTaskToUI(data.task);
                }
                this.modal.hide();
                // Reset happens automatically on next openCreator call
            } else {
                alert('Error: ' + JSON.stringify(data.errors));
            }
        } catch (error) {
            console.error(error);
            alert('Failed to save task.');
        }
    }

    updateTaskInUI(task) {
        const row = document.getElementById(`task-row-${task.id}`);
        if (!row) return;

        const titleEl = row.querySelector('.fw-bold'); 
        if (titleEl) {
            titleEl.textContent = task.title;
            // Update Popover
            if (task.description) {
                const oldPop = bootstrap.Popover.getInstance(titleEl);
                if (oldPop) oldPop.dispose();
                titleEl.setAttribute('data-bs-content', task.description);
                new bootstrap.Popover(titleEl, {
                    content: task.description, html: true, trigger: 'hover', placement: 'top'
                });
            }
        }
        const rankEl = row.querySelector('.badge');
        if (rankEl) rankEl.textContent = `${task.rank}-Rank`;
    }

    appendTaskToUI(task) {
        if (!this.dom.list) return;
        const emptyMsg = this.dom.list.querySelector('.empty-msg');
        if (emptyMsg) emptyMsg.remove();

        const wrapper = document.createElement('div');
        wrapper.innerHTML = `
            <div class="list-group-item d-flex justify-content-between align-items-center task-item" id="task-row-${task.id}">
                <div class="d-flex align-items-center">
                    <input class="form-check-input me-2" type="checkbox" onclick="toggleTask(${task.id})">
                    <div class="ms-2" onclick="editTask(${task.id})" style="cursor: pointer;">
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
        if (task.description) {
            const titleEl = row.querySelector('.task-title');
            new bootstrap.Popover(titleEl, {
                content: task.description, html: true, trigger: 'hover', placement: 'top'
            });
        }
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

    const taskManager = new TaskManager();

    // 3. Edit Task Global Helper
    window.editTask = function(taskId) {
        taskManager.openEditor(taskId);
    };

    // 4. Create Task Global Helper
    window.initCreateTask = function() {
        taskManager.openCreator();
    };
});

})();
