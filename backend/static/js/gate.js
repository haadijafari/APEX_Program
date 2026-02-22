(function() {
    'use strict';

    if (window.HAS_GATE_JS_LOADED) return;
    window.HAS_GATE_JS_LOADED = true;

    /**
     * ==========================================
     * GATE API LAYER
     * Centralized methods for server communication.
     * ==========================================
     */
    class GateAPI {
        // 1. Load Configuration
        static get config() {
            if (this._config) return this._config;
            const el = document.getElementById('gate-api-config');
            try {
                this._config = el ? JSON.parse(el.textContent) : {};
            } catch (e) {
                console.error("Failed to parse API config:", e);
                this._config = {};
            }
            return this._config;
        }

        // 2. Helper to Build URLs
        static getUrl(name, id = null) {
            let url = this.config[name];
            if (!url) {
                console.error(`URL for '${name}' not found in config.`);
                return '';
            }
            // Replace the dummy '0' ID with the actual ID
            if (id !== null) {
                url = url.replace('0', id);
            }
            return url;
        }

        static getCookie(name) {
            if (!document.cookie) return null;
            const cookie = document.cookie
                .split('; ')
                .find(row => row.startsWith(name + '='));
            return cookie ? decodeURIComponent(cookie.split('=')[1]) : null;
        }

        static get headers() {
            return {
                "X-CSRFToken": this.getCookie('csrftoken'),
                "X-Requested-With": "XMLHttpRequest"
            };
        }

        static async request(url, method = 'GET', body = null) {
            if (!url) throw new Error("Invalid API URL");
            
            const options = { method, headers: this.headers };
            if (body) options.body = body;

            try {
                const response = await fetch(url, options);
                return await response.json();
            } catch (error) {
                console.error(`API Error [${url}]:`, error);
                throw error;
            }
        }

        // --- Endpoints ---

        static autoSave(formElement) {
            // Keep existing data-attribute logic for autosave as it's specific to the form
            const url = formElement.dataset.autosaveUrl || "/gate/autosave/";
            return this.request(url, 'POST', new FormData(formElement));
        }

        static toggleTaskStatus(taskId) {
            const body = new FormData();
            
            // Check if we are viewing a specific date and append it
            if (this.config.targetDate) {
                body.append('target_date', this.config.targetDate);
            }
            
            return this.request(this.getUrl('taskToggle', taskId), 'POST', body);
        }

        static createTask(formData) {
            return this.request(this.getUrl('taskAdd'), 'POST', formData);
        }

        static getTaskDetails(taskId) {
            return this.request(this.getUrl('taskDetails', taskId), 'GET');
        }

        static updateTask(taskId, formData) {
            return this.request(this.getUrl('taskUpdate', taskId), 'POST', formData);
        }

        static archiveTask(taskId) {
            return this.request(this.getUrl('taskArchive', taskId), 'POST');
        }
    }

    /**
     * ==========================================
     * MODULE: SLEEP CALCULATOR
     * Computes sleep duration across midnight.
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
            }
        }

        initListeners() {
            // Recalculate on any change
            const inputs = [this.dom.sleep, this.dom.wake, this.dom.nap];
            inputs.forEach(el => {
                if(el) el.addEventListener(el.type === 'text' ? 'input' : 'change', () => this.calculate());
            });
            this.calculate(); // Initial check
        }

        calculate() {
            let totalMinutes = 0;

            // 1. Night Sleep Calculation
            if (this.dom.sleep.value && this.dom.wake.value) {
                const [sH, sM] = this.dom.sleep.value.split(':').map(Number);
                const [wH, wM] = this.dom.wake.value.split(':').map(Number);

                // Convert times to minutes from midnight
                const sleepMin = sH * 60 + sM;
                const wakeMin = wH * 60 + wM;

                let duration = wakeMin - sleepMin;
                // Handle crossing midnight (e.g. 23:00 to 07:00)
                if (duration < 0) duration += (24 * 60);
                
                totalMinutes += duration;
            }

            // 2. Nap Calculation
            const napHours = this.dom.nap ? (parseFloat(this.dom.nap.value) || 0) : 0;
            totalMinutes += (napHours * 60);

            // 3. Render
            if (totalMinutes === 0) {
                this.dom.display.value = "--";
            } else {
                const hours = Math.floor(totalMinutes / 60);
                const minutes = Math.round(totalMinutes % 60);
                this.dom.display.value = `${hours} hr ${minutes} min`;
            }
        }
    }

    /**
     * ==========================================
     * MODULE: DAILY LOG FORM
     * Auto-save, Emoji Picker, Dynamic Rows.
     * ==========================================
     */
    class DailyLogForm {
        constructor(formId) {
            this.form = document.getElementById(formId);
            if (!this.form) return;

            this.state = { isSaving: false, pendingSave: false, pendingStatusEl: null };
            
            // Debounce save for text inputs (wait 1s after typing stops)
            this.debouncedSave = this.debounce((statusEl) => this.performSave(statusEl), 1000);
            
            this.initAutoSave();
            this.initTinyMCE();
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
            // Identify where to show "Saving..." text
            const getStatusEl = (target) => {
                const section = target.closest('.js-autosave-section');
                return (section?.querySelector('.js-section-status')) || document.getElementById('global-save-status');
            };

            this.form.addEventListener('input', (e) => {
                if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) {
                    this.debouncedSave(getStatusEl(e.target));
                }
            });

            this.form.addEventListener('change', (e) => {
                // Immediate save for toggles/selects
                if (['radio', 'checkbox', 'select-one'].includes(e.target.type) || e.target.type === 'time') {
                    this.performSave(getStatusEl(e.target));
                }
            });
        }

        initTinyMCE() {
            // Check periodically if TinyMCE is initialized on the diary field
            const checkInterval = setInterval(() => {
                // 'id_diary' is the default ID Django gives to the field
                if (window.tinymce && window.tinymce.get('id_diary')) {
                    clearInterval(checkInterval);
                    const editor = window.tinymce.get('id_diary');

                    // Listen for typing or changes in the editor
                    editor.on('input change keyup', () => {
                        // Find the status element for the Diary section
                        // (We look for the closest section to the original textarea)
                        const textarea = document.getElementById('id_diary');
                        const statusEl = textarea.closest('.js-autosave-section')?.querySelector('.js-section-status');
                        
                        // Trigger the standard debounced save
                        this.debouncedSave(statusEl);
                    });
                }
            }, 500);
        }

        async performSave(statusEl) {
            // Ensure the underlying textarea is updated with the editor content
            if (window.tinymce) {
                window.tinymce.triggerSave();
            }
            
            if (this.state.isSaving) {
                this.state.pendingSave = true;
                if (statusEl) this.state.pendingStatusEl = statusEl;
                return;
            }

            this.state.isSaving = true;
            const targetStatusEl = statusEl || this.state.pendingStatusEl;
            this.state.pendingStatusEl = null;

            this.updateStatus(targetStatusEl, "Saving...", "text-secondary");

            try {
                const data = await GateAPI.autoSave(this.form);
                if (data.status === 'success') {
                    this.updateStatus(targetStatusEl, "Saved", "text-success");
                    this.handlePostSave(data); // Handle ID updates
                    setTimeout(() => this.updateStatus(targetStatusEl, "", ""), 2000);
                } else {
                    this.updateStatus(targetStatusEl, "Error", "text-danger");
                }
            } catch (error) {
                this.updateStatus(targetStatusEl, "Offline", "text-danger");
            } finally {
                this.state.isSaving = false;
                if (this.state.pendingSave) {
                    this.state.pendingSave = false;
                    this.performSave(this.state.pendingStatusEl);
                }
            }
        }

        handlePostSave(data) {
            // Update inputs with new database IDs (for newly created rows)
            if (data.new_ids) {
                Object.entries(data.new_ids).forEach(([name, id]) => {
                    const input = this.form.querySelector(`input[name="${name}"]`);
                    if (input) input.value = id;
                });
            }
            // Update Management Form counts
            ['pos', 'neg'].forEach(prefix => {
                const mgmtInput = document.getElementById(`id_${prefix}-INITIAL_FORMS`);
                if (mgmtInput) {
                     const count = this.form.querySelectorAll(`input[name^="${prefix}-"][name$="-id"][value]:not([value=""])`).length;
                     mgmtInput.value = count;
                }
            });
        }

        updateStatus(el, text, colorClass) {
            if (!el) return;
            el.textContent = text;
            el.className = `js-section-status small fw-bold text-uppercase transition-all ${colorClass}`;
        }

        initEmojiPicker() {
            const els = {
                input: document.getElementById('mood-picker-input'),
                slot: document.getElementById('mood-slot-container'),
                popover: document.getElementById('emoji-popover'),
                picker: document.querySelector('emoji-picker')
            };

            if (!els.input || !els.slot || !els.popover || !els.picker) return;

            els.picker.dataSource = '/static/vendor/emoji-picker/data.json'; 

            // Toggle logic
            els.slot.addEventListener('click', (e) => {
                if (els.popover.contains(e.target)) return;
                e.preventDefault();
                els.popover.style.display = els.popover.style.display === 'block' ? 'none' : 'block';
            });

            // Selection Logic
            els.picker.addEventListener('emoji-click', (e) => {
                els.input.value = e.detail.unicode;
                els.popover.style.display = 'none';
                els.slot.classList.add('has-mood');
                // Trigger Autosave
                const statusEl = els.slot.closest('.js-autosave-section')?.querySelector('.js-section-status');
                this.performSave(statusEl); 
            });

            // Outside Click Listener
            document.addEventListener('click', (e) => {
                if (!els.slot.contains(e.target) && !els.popover.contains(e.target)) {
                    els.popover.style.display = 'none';
                }
            });
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
            updateVisuals(); // Set initial state
        }

        initDynamicRows() {
            // Event Delegation for Add/Delete buttons
            this.form.addEventListener('click', (e) => {
                // Add Row
                const addBtn = e.target.closest('[data-add-row]');
                if (addBtn) this.addFormRow(addBtn.dataset.prefix);

                // Delete Row
                const delBtn = e.target.closest('.btn-delete-row');
                if (delBtn) {
                    const row = delBtn.closest('.highlight-row');
                    const deleteInput = row.querySelector('input[name$="-DELETE"]');
                    if (deleteInput) deleteInput.checked = true;
                    
                    row.style.display = 'none'; // Visual hide
                    
                    // Trigger Save
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
        }
    }

    /**
     * ==========================================
     * MODULE: TASK MANAGER
     * CRUD Operations for Tasks
     * ==========================================
     */
    class TaskManager {
        constructor() {
            this.dom = {
                listPending: document.getElementById('pending-tasks-list'),
                listDone: document.getElementById('done-tasks-list'),
                form: document.getElementById('gate-add-task-form'),
                modalEl: document.getElementById('taskModal'),
                saveBtn: document.getElementById('btn-save-task'),
                modalTitle: document.getElementById('taskModalTitle'),
                hiddenId: document.getElementById('task-id-hidden'),
                addBtn: document.getElementById('btn-open-create-task')
            };

            if (this.dom.modalEl) {
                this.modal = bootstrap.Modal.getOrCreateInstance(this.dom.modalEl);
                this.initSaver();
                this.initEventListeners();
            }
        }

        initSaver() {
            if (!this.dom.saveBtn) return;
            // Clean listener approach using clone is fine for simple buttons, 
            // alternatively use { once: true } or named functions.
            const newBtn = this.dom.saveBtn.cloneNode(true);
            this.dom.saveBtn.parentNode.replaceChild(newBtn, this.dom.saveBtn);
            this.dom.saveBtn = newBtn;
            
            this.dom.saveBtn.addEventListener('click', () => this.handleSave());
        }

        /**
         * Initialize Event Delegation
         * Listens for clicks/changes on the list containers instead of individual items.
         */
        initEventListeners() {
            // Listen for Modal Open to reset form
            if (this.dom.modalEl) {
                this.dom.modalEl.addEventListener('show.bs.modal', (event) => {
                    // Only reset if the trigger was the "Add" button, not an "Edit" click
                    if (event.relatedTarget && event.relatedTarget.id === 'btn-open-create-task') {
                        this.resetForm();
                    }
                });
            }

            // Bind Delegation to both lists
            [this.dom.listPending, this.dom.listDone].forEach(list => {
                if (!list) return;

                // Handle Clicks (Edit, Archive)
                list.addEventListener('click', (e) => {
                    // 1. Edit Click
                    const editTarget = e.target.closest('.js-task-edit');
                    if (editTarget) {
                        this.openEditor(editTarget.dataset.taskId);
                        return;
                    }

                    // 2. Archive Click
                    const archiveTarget = e.target.closest('.js-task-archive');
                    if (archiveTarget) {
                        this.handleArchive(archiveTarget.dataset.taskId);
                    }
                });

                // Handle Changes (Toggle Checkbox)
                list.addEventListener('change', (e) => {
                    const toggleTarget = e.target.closest('.js-task-toggle');
                    if (toggleTarget) {
                        this.handleToggle(toggleTarget.dataset.taskId, toggleTarget);
                    }
                });
            });
        }

        resetForm() {
            if (!this.dom.form) return;
            this.dom.form.reset();
            if (this.dom.hiddenId) this.dom.hiddenId.value = '';
            if (this.dom.modalTitle) this.dom.modalTitle.textContent = "Initialize New Task";
            if (this.dom.saveBtn) this.dom.saveBtn.textContent = "Create Task";
            
            // TinyMCE Reset
            if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                tinymce.activeEditor.setContent('');
            }
        }

        openCreator() {
            // Logic handled by modal event listener, but kept for manual calls if needed
            this.resetForm();
            this.modal.show();
        }

        async openEditor(taskId) {
            try {
                const data = await GateAPI.getTaskDetails(taskId);
                if (data.status === 'success') {
                    this.populateForm(data.task);
                    this.modal.show();
                }
            } catch (error) {
                alert("Failed to load task details.");
            }
        }

        populateForm(task) {
            // Helper to safe-set values
            const setVal = (name, val) => {
                let el = this.dom.form.querySelector(`[name="${name}"]`) || 
                         this.dom.form.querySelector(`#id_${name}`);
                if (el) el.value = (val ?? '');
            };

            if (this.dom.hiddenId) this.dom.hiddenId.value = task.id;
            setVal('title', task.title);
            setVal('manual_rank', task.manual_rank);
            setVal('duration_minutes', task.duration_minutes);
            setVal('effort_level', task.effort_level);
            setVal('impact_level', task.impact_level);
            setVal('fear_factor', task.fear_factor);
            setVal('primary_stat', task.primary_stat);
            setVal('secondary_stat', task.secondary_stat);

            if (typeof tinymce !== 'undefined' && tinymce.activeEditor) {
                 tinymce.activeEditor.setContent(task.description || '');
            } else {
                 setVal('description', task.description);
            }

            if (this.dom.modalTitle) this.dom.modalTitle.textContent = "Edit Task";
            if (this.dom.saveBtn) this.dom.saveBtn.textContent = "Update Task";
        }

        async handleSave() {
            if (typeof tinymce !== 'undefined') tinymce.triggerSave();

            const formData = new FormData(this.dom.form);
            const taskId = this.dom.hiddenId?.value;
            
            try {
                const data = taskId 
                    ? await GateAPI.updateTask(taskId, formData)
                    : await GateAPI.createTask(formData);
                
                if (data.status === 'success') {
                    taskId ? this.updateTaskInUI(data.task) : this.appendTaskToUI(data.task);
                    this.modal.hide();
                } else {
                    alert('Error: ' + JSON.stringify(data.errors));
                }
            } catch (error) {
                alert('Failed to save task.');
            }
        }

        async handleToggle(itemId, checkboxEl) {
            try {
                const data = await GateAPI.toggleTaskStatus(itemId);
                const row = document.getElementById(`task-row-${itemId}`);
                if (!row) return;

                // Determine movement
                const targetList = (data.status === 'added') ? this.dom.listDone : this.dom.listPending;
                const titleEl = row.querySelector('.fw-bold');

                if (targetList) {
                    targetList.appendChild(row);
                    titleEl?.classList.toggle('text-decoration-line-through', data.status === 'added');
                }
                
                this.updateEmptyState();

            } catch (err) {
                // Revert checkbox on failure
                if (checkboxEl) checkboxEl.checked = !checkboxEl.checked;
                console.error("Toggle failed", err);
            }
        }

        async handleArchive(taskId) {
            if (!confirm("Are you sure you want to remove this task?")) return;
            try {
                const data = await GateAPI.archiveTask(taskId);
                if (data.status === 'success') {
                    const row = document.getElementById(`task-row-${taskId}`);
                    // Dispose popover to prevent memory leaks
                    const titleEl = row?.querySelector('[data-bs-toggle="popover"]');
                    if (titleEl) bootstrap.Popover.getInstance(titleEl)?.dispose();
                    row?.remove();
                    this.updateEmptyState();
                }
            } catch (error) {
                console.error(error);
            }
        }

        updateEmptyState() {
            if (!this.dom.listPending) return;
            const hasTasks = this.dom.listPending.querySelectorAll('.task-item').length > 0;
            const emptyMsg = this.dom.listPending.querySelector('.empty-msg');
            
            if (!hasTasks && !emptyMsg) {
                this.dom.listPending.insertAdjacentHTML('beforeend', '<div class="text-center text-muted py-3 empty-msg">No active tasks.</div>');
            } else if (hasTasks && emptyMsg) {
                emptyMsg.remove();
            }
        }

        // --- UI Updates ---
        updateTaskInUI(task) {
            const row = document.getElementById(`task-row-${task.id}`);
            if (!row) return;

            const titleEl = row.querySelector('.fw-bold'); 
            const rankEl = row.querySelector('.badge');
            
            if (titleEl) {
                titleEl.textContent = task.title;
                // Re-init Popover
                const oldPop = bootstrap.Popover.getInstance(titleEl);
                if (oldPop) oldPop.dispose();
                if (task.description) {
                    titleEl.setAttribute('data-bs-content', task.description);
                    new bootstrap.Popover(titleEl, {
                        content: task.description, html: true, trigger: 'hover', placement: 'top'
                    });
                }
            }
            if (rankEl) rankEl.textContent = `${task.rank}-Rank`;
        }

        appendTaskToUI(task) {
            if (!this.dom.listPending) return;

            // 1. Get the Template
            const template = document.getElementById('task-row-template');
            if (!template) {
                console.error("Task template not found");
                return;
            }

            // 2. Clone the content
            const clone = template.content.cloneNode(true);
            const row = clone.querySelector('.task-item'); // Select the wrapper div

            // 3. Populate Data
            row.id = `task-row-${task.id}`;

            // Checkbox
            const checkbox = row.querySelector('.js-task-toggle');
            checkbox.dataset.taskId = task.id;

            // Title / Edit Container
            const editGroup = row.querySelector('.js-task-edit');
            editGroup.dataset.taskId = task.id;

            // Title Text & Popover
            const titleEl = row.querySelector('.task-title-text');
            titleEl.textContent = task.title;
            
            if (task.description) {
                // Set Bootstrap Popover attributes
                titleEl.setAttribute('data-bs-toggle', 'popover');
                titleEl.setAttribute('data-bs-trigger', 'hover');
                titleEl.setAttribute('data-bs-html', 'true');
                titleEl.setAttribute('data-bs-content', task.description);
                titleEl.setAttribute('data-bs-placement', 'top');
                
                // Initialize the Popover immediately
                new bootstrap.Popover(titleEl);
            }

            // Rank
            const rankEl = row.querySelector('.task-rank-text');
            rankEl.textContent = `${task.rank}-Rank`;

            // Archive Button
            const archiveBtn = row.querySelector('.js-task-archive');
            archiveBtn.dataset.taskId = task.id;

            // 4. Handle Empty State
            const emptyMsg = this.dom.listPending.querySelector('.empty-msg');
            if (emptyMsg) emptyMsg.remove();

            // 5. Append to List
            this.dom.listPending.appendChild(row);
        }
    }

    /**
     * ==========================================
     * MODULE: ROUTINE MANAGER
     * Handles toggling for routine subtasks.
     * ==========================================
     */
    class RoutineManager {
        constructor() {
            this.initListeners();
        }

        initListeners() {
            // Listen for changes on any element with the js-routine-toggle class
            document.addEventListener('change', (e) => {
                if (e.target.classList.contains('js-routine-toggle')) {
                    // Fallback to extracting ID from 'task-123' if data-task-id is missing
                    const taskId = e.target.dataset.taskId || e.target.id.replace('task-', '');
                    
                    if (!taskId || taskId === 'undefined') {
                        console.error("Could not determine task ID for:", e.target);
                        return;
                    }

                    this.handleToggle(taskId, e.target);
                }
            });
        }

        async handleToggle(taskId, checkboxEl) {
            try {
                await GateAPI.toggleTaskStatus(taskId);
            } catch (err) {
                // Revert checkbox visual state on failure
                checkboxEl.checked = !checkboxEl.checked;
                console.error("Routine toggle failed", err);
            }
        }
    }

    /**
     * ==========================================
     * INITIALIZATION
     * ==========================================
     */
    document.addEventListener('DOMContentLoaded', () => {
        console.log("🚀 Gate.js Initialized");

        // Init Bootstrap Popovers
        document.querySelectorAll('[data-bs-toggle="popover"]')
            .forEach(el => new bootstrap.Popover(el));

        // Init Modules
        new SleepModule();
        new DailyLogForm('dayPageForm');
        new TaskManager(); // Logic is now self-contained
        new RoutineManager();
    });

})();
