// ============================================================
// CORTEX DASHBOARD ENGINE
// ============================================================

const API_URL = "https://cortex-rgzd.onrender.com";

const token = localStorage.getItem("access_token");

if (!token) {
    window.location.href = "index.html";
}


// ============================================================
// GLOBAL STATE
// ============================================================

const $ = (id) => document.getElementById(id);

let tasks = [];
let currentUser = null;
let currentView = "dashboard";
let calendarDate = new Date();

const PRIORITY_ORDER = {
    urgent: 4,
    high: 3,
    medium: 2,
    low: 1,
};

const STATUS_ORDER = [
    "todo",
    "in_progress",
    "done",
];


// ============================================================
// HELPERS
// ============================================================

function escapeHTML(value = "") {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


function authHeaders(json = true) {
    const headers = {
        Authorization: `Bearer ${token}`,
    };

    if (json) {
        headers["Content-Type"] = "application/json";
    }

    return headers;
}


async function parseResponse(response) {
    const text = await response.text();

    if (!text) {
        return {};
    }

    try {
        return JSON.parse(text);
    } catch {
        return {
            detail: text,
        };
    }
}


async function api(path, options = {}) {
    const response = await fetch(
        `${API_URL}${path}`,
        {
            ...options,
            headers: {
                ...authHeaders(
                    options.body !== undefined
                ),
                ...(options.headers || {}),
            },
        }
    );

    const data = await parseResponse(response);

    if (response.status === 401) {
        localStorage.removeItem("access_token");
        window.location.href = "index.html";
        throw new Error("Your session has expired.");
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            "Something went wrong."
        );
    }

    return data;
}


function showToast(text, type = "normal") {
    const container = $("toast-container");

    if (!container) {
        return;
    }

    const toast = document.createElement("div");

    toast.className = `toast ${type}`;
    toast.textContent = text;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3200);
}


function formatDate(value) {
    if (!value) {
        return "No deadline";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return "No deadline";
    }

    return date.toLocaleString(
        "en-IN",
        {
            day: "numeric",
            month: "short",
            hour: "numeric",
            minute: "2-digit",
        }
    );
}


function isOverdue(task) {
    if (
        !task.due_date ||
        task.status === "done"
    ) {
        return false;
    }

    return new Date(task.due_date) < new Date();
}


function isDueToday(task) {
    if (!task.due_date) {
        return false;
    }

    const date = new Date(task.due_date);
    const now = new Date();

    return (
        date.getFullYear() === now.getFullYear() &&
        date.getMonth() === now.getMonth() &&
        date.getDate() === now.getDate()
    );
}


function statusLabel(status) {
    const labels = {
        todo: "To do",
        in_progress: "In progress",
        done: "Completed",
    };

    return labels[status] || status;
}


function nextStatus(status) {
    if (status === "todo") {
        return "in_progress";
    }

    if (status === "in_progress") {
        return "done";
    }

    return "todo";
}


function priorityBadge(priority) {
    const value = priority || "medium";

    return `
        <span class="task-badge ${escapeHTML(value)}">
            ${escapeHTML(value.toUpperCase())}
        </span>
    `;
}


// ============================================================
// PROFILE
// ============================================================

async function loadProfile() {

    currentUser = await api("/api/auth/me");

    const firstName =
        currentUser.name
            .trim()
            .split(/\s+/)[0];

    $("page-title").textContent =
        `Good ${getGreeting()}, ${firstName}`;

    $("sidebar-name").textContent =
        currentUser.name;

    $("sidebar-email").textContent =
        currentUser.email;

    const initial =
        currentUser.name
            .charAt(0)
            .toUpperCase();

    $("sidebar-avatar").textContent =
        initial;

    $("top-avatar").textContent =
        initial;


    // PROFILE PAGE

    $("profile-avatar").textContent =
        initial;

    $("profile-name").textContent =
        currentUser.name;

    $("profile-email").textContent =
        currentUser.email;

    $("profile-name-detail").textContent =
        currentUser.name;

    $("profile-email-detail").textContent =
        currentUser.email;


    const currentTheme =
        currentUser.theme ||
        localStorage.getItem("cortex_theme") ||
        "dark";

    $("profile-theme").textContent =
        currentTheme === "light"
            ? "Light"
            : "Dark";

    $("profile-theme-side").textContent =
        currentTheme === "light"
            ? "Light"
            : "Dark";


    applyTheme(currentTheme);
}


function getGreeting() {
    const hour = new Date().getHours();

    if (hour < 12) {
        return "morning";
    }

    if (hour < 18) {
        return "afternoon";
    }

    return "evening";
}


// ============================================================
// THEME
// ============================================================

function applyTheme(theme) {
    const isLight = theme === "light";

    document.body.classList.toggle(
        "light-theme",
        isLight
    );

    localStorage.setItem(
        "cortex_theme",
        theme
    );

    const label = $("theme-label");
    const icon = $("theme-icon");

    if (label) {
        label.textContent =
            isLight
                ? "Dark mode"
                : "Light mode";
    }

    if (icon) {
        icon.textContent =
            isLight
                ? "☾"
                : "☼";
    }
}


async function toggleTheme() {
    const light =
        document.body.classList.contains(
            "light-theme"
        );

    const next =
        light
            ? "dark"
            : "light";

    applyTheme(next);

    try {
        await api(
            "/api/auth/me",
            {
                method: "PUT",
                body: JSON.stringify({
                    theme: next,
                }),
            }
        );
    } catch (error) {
        console.warn(
            "Theme preference could not be saved:",
            error
        );
    }
}


// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {
    const search =
        $("task-search")?.value.trim() || "";

    const status =
        $("status-filter")?.value || "all";

    const priority =
        $("priority-filter")?.value || "all";

    const due =
        $("due-filter")?.value || "all";

    const sort =
        $("sort-filter")?.value || "newest";

    const query = new URLSearchParams();

    if (search) {
        query.set("search", search);
    }

    if (status !== "all") {
        query.set("status", status);
    }

    if (priority !== "all") {
        query.set("priority", priority);
    }

    if (due !== "all") {
        query.set("due", due);
    }

    query.set("sort", sort);

    tasks = await api(
        `/api/tasks?${query.toString()}`
    );

    renderTaskList();
    renderFocusTasks();
    renderRecentTasks();
    renderBoard();
    renderCalendar();

    await loadStats();
    await loadReminders();
}

// ============================================================
// IMPORT CSV
// ============================================================

async function importCSV(files) {
    if (!files || !files.length) {
        return;
    }

    const formData = new FormData();

    for (const file of files) {
        formData.append("files", file);
    }

    try {
        showToast("Importing CSV...", "normal");

        const response = await fetch(
            `${API_URL}/api/tasks/import-csv`,
            {
                method: "POST",
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                body: formData,
            }
        );

        const data = await parseResponse(response);

        if (response.status === 401) {
            localStorage.removeItem("access_token");
            window.location.href = "index.html";
            return;
        }

        if (!response.ok) {
            throw new Error(
                data.detail ||
                data.message ||
                "CSV import failed."
            );
        }

        showToast(
            `CSV imported successfully — ${data.total_imported} tasks added.`,
            "success"
        );

        // Refresh dashboard tasks
        await loadTasks();

    } catch (error) {
        console.error("CSV import failed:", error);

        showToast(
            error.message || "CSV import failed.",
            "error"
        );
    }
}



// ============================================================
// STATISTICS
// ============================================================

async function loadStats() {
    const stats =
        await api("/api/tasks/stats");

    $("stat-total").textContent =
        stats.total;

    $("stat-completed").textContent =
        stats.completed;

    $("stat-progress").textContent =
        stats.in_progress;

    $("stat-overdue").textContent =
        stats.overdue;

    $("stat-urgent").textContent =
        stats.urgent;

    $("stat-completion-rate").textContent =
        `${stats.completion_rate}% completion rate`;
}


// ============================================================
// TASK CARD
// ============================================================

function taskCard(task) {
    const overdue = isOverdue(task);
    const dueToday = isDueToday(task);

    const dueText =
        overdue
            ? "Overdue"
            : dueToday
                ? "Due today"
                : task.due_date
                    ? `Due ${formatDate(task.due_date)}`
                    : "No deadline";

    const subtaskCount =
        Array.isArray(task.subtasks)
            ? task.subtasks.length
            : 0;

    const completedSubtasks =
        Array.isArray(task.subtasks)
            ? task.subtasks.filter(
                item => item.completed
            ).length
            : 0;

    const completeButton =
        task.status !== "done"
            ? `
                <button
                    class="mini-action complete-action"
                    data-task-action="complete"
                    data-task-id="${task.id}"
                >
                    ✓ Complete
                </button>
            `
            : `
                <span class="task-completed-label">
                    ✓ Completed
                </span>
            `;

    return `
        <article
            class="task-card"
            data-task-id="${task.id}"
        >

            <div class="task-card-top">

                <div>

                    <div class="task-card-title">
                        ${escapeHTML(task.title)}
                    </div>

                    <div class="task-card-description">
                        ${escapeHTML(
                            task.description ||
                            "No description"
                        )}
                    </div>

                </div>

                ${priorityBadge(task.priority)}

            </div>


            <div class="task-meta">

                <span class="meta-pill">
                    ${escapeHTML(
                        statusLabel(task.status)
                    )}
                </span>

                <span class="meta-pill ${
                    overdue ? "overdue-pill" : ""
                }">
                    ${escapeHTML(dueText)}
                </span>

                ${
                    subtaskCount
                        ? `
                            <span class="meta-pill">
                                ✓ ${completedSubtasks}/${subtaskCount}
                            </span>
                        `
                        : ""
                }

            </div>


            ${
                task.ai_reason
                    ? `
                        <div class="task-ai-note">
                            ✦ ${escapeHTML(
                                task.ai_reason
                            )}
                        </div>
                    `
                    : ""
            }


            <div class="task-card-actions">

                <div class="task-status-actions">

                    <button
                        class="mini-action status-action ${
                            task.status === "todo"
                                ? "active-status"
                                : ""
                        }"
                        data-task-action="set-status"
                        data-status="todo"
                        data-task-id="${task.id}"
                    >
                        To do
                    </button>

                    <button
                        class="mini-action status-action ${
                            task.status === "in_progress"
                                ? "active-status"
                                : ""
                        }"
                        data-task-action="set-status"
                        data-status="in_progress"
                        data-task-id="${task.id}"
                    >
                        In progress
                    </button>

                    <button
                        class="mini-action status-action ${
                            task.status === "done"
                                ? "active-status"
                                : ""
                        }"
                        data-task-action="set-status"
                        data-status="done"
                        data-task-id="${task.id}"
                    >
                        Completed
                    </button>

                </div>

                <button
                    class="mini-action"
                    data-task-action="ai"
                    data-task-id="${task.id}"
                >
                    ✦ AI
                </button>

                <button
                    class="mini-action danger-action"
                    data-task-action="delete"
                    data-task-id="${task.id}"
                >
                    Delete
                </button>

            </div>

        </article>
    `;
}


// ============================================================
// TASK LIST
// ============================================================

function renderTaskList() {
    const root = $("task-list");

    if (!root) {
        return;
    }

    if (!tasks.length) {
        root.innerHTML = `
            <div class="empty-state">
                <div>✓</div>
                <strong>No tasks found</strong>
                <span>
                    Create a task or change your filters.
                </span>
            </div>
        `;

        return;
    }

    root.innerHTML =
        tasks.map(taskCard).join("");

    attachTaskActions();
}


// ============================================================
// TODAY'S FOCUS
// ============================================================

function renderFocusTasks() {
    const root = $("focus-task-list");

    if (!root) {
        return;
    }

    const focus =
        [...tasks]
            .filter(
                task =>
                    task.status !== "done"
            )
            .sort(
                (a, b) => {

                    const p =
                        PRIORITY_ORDER[b.priority] -
                        PRIORITY_ORDER[a.priority];

                    if (p !== 0) {
                        return p;
                    }

                    return (
                        new Date(
                            a.due_date ||
                            "2999-12-31"
                        ) -
                        new Date(
                            b.due_date ||
                            "2999-12-31"
                        )
                    );
                }
            )
            .slice(0, 5);

    if (!focus.length) {
        root.innerHTML = `
            <div class="empty-state">
                <div>✦</div>
                <strong>Your workspace is clear.</strong>
                <span>
                    Create something new and let CORTEX
                    help you prioritize it.
                </span>
            </div>
        `;

        return;
    }

    root.innerHTML =
        focus
            .map(task => {
                return `
                    <div class="focus-task-item">

                        <button
                            class="task-check"
                            data-task-action="complete"
                            data-task-id="${task.id}"
                            title="Mark completed"
                        >
                            ✓
                        </button>

                        <div class="task-item-copy">

                            <strong>
                                ${escapeHTML(task.title)}
                            </strong>

                            <span>
                                ${escapeHTML(
                                    statusLabel(task.status)
                                )}
                                ·
                                ${
                                    task.due_date
                                        ? escapeHTML(
                                            formatDate(
                                                task.due_date
                                            )
                                        )
                                        : "No deadline"
                                }
                            </span>

                        </div>

                        ${priorityBadge(task.priority)}

                    </div>
                `;
            })
            .join("");

    attachTaskActions();
}


// ============================================================
// RECENT TASKS
// ============================================================

function renderRecentTasks() {
    const root = $("recent-task-list");

    if (!root) {
        return;
    }

    const recent =
        [...tasks]
            .sort(
                (a, b) =>
                    new Date(b.created_at) -
                    new Date(a.created_at)
            )
            .slice(0, 6);

    if (!recent.length) {
        root.innerHTML = `
            <div class="empty-state">
                <div>✓</div>
                <span>
                    Your task activity will appear here.
                </span>
            </div>
        `;

        return;
    }

    root.innerHTML =
        recent
            .map(task => {
                return `
                    <div class="recent-task-item">

                        <div class="task-item-copy">

                            <strong>
                                ${escapeHTML(task.title)}
                            </strong>

                            <span>
                                ${escapeHTML(
                                    statusLabel(task.status)
                                )}
                                ·
                                ${
                                    task.due_date
                                        ? escapeHTML(
                                            formatDate(
                                                task.due_date
                                            )
                                        )
                                        : "No deadline"
                                }
                            </span>

                        </div>

                        ${priorityBadge(task.priority)}

                    </div>
                `;
            })
            .join("");
}


// ============================================================
// BOARD
// ============================================================

function renderBoard() {
    const columns = {
        todo: $("board-todo"),
        in_progress: $("board-progress"),
        done: $("board-done"),
    };

    if (
        !columns.todo ||
        !columns.in_progress ||
        !columns.done
    ) {
        return;
    }

    Object.values(columns).forEach(
        column => {
            column.innerHTML = "";
        }
    );

    STATUS_ORDER.forEach(status => {
        const column = columns[status];

        const matching =
            tasks.filter(
                task =>
                    task.status === status
            );

        matching.forEach(task => {
            const card =
                document.createElement("div");

            card.className =
                "board-task-card";

            card.draggable = true;

            card.dataset.taskId =
                task.id;

            card.innerHTML = `
                <div class="task-card-title">
                    ${escapeHTML(task.title)}
                </div>

                <div class="task-meta">
                    ${priorityBadge(task.priority)}
                </div>

                <div class="task-card-description">
                    ${
                        task.due_date
                            ? escapeHTML(
                                formatDate(task.due_date)
                            )
                            : "No deadline"
                    }
                </div>

                ${
                    task.status !== "done"
                        ? `
                            <button
                                class="mini-action complete-board-action"
                                data-task-id="${task.id}"
                            >
                                ✓ Complete
                            </button>
                        `
                        : `
                            <div class="task-completed-label">
                                ✓ Completed
                            </div>
                        `
                }
            `;

            card.addEventListener(
                "dragstart",
                event => {
                    event.dataTransfer.setData(
                        "text/plain",
                        String(task.id)
                    );
                }
            );

            const completeButton =
                card.querySelector(
                    ".complete-board-action"
                );

            completeButton?.addEventListener(
                "click",
                async event => {
                    event.stopPropagation();

                    await completeTask(
                        task.id
                    );
                }
            );

            column.appendChild(card);
        });
    });

    $("board-todo-count").textContent =
        tasks.filter(
            task =>
                task.status === "todo"
        ).length;

    $("board-progress-count").textContent =
        tasks.filter(
            task =>
                task.status === "in_progress"
        ).length;

    $("board-done-count").textContent =
        tasks.filter(
            task =>
                task.status === "done"
        ).length;

    setupBoardDrop(
        columns.todo,
        "todo"
    );

    setupBoardDrop(
        columns.in_progress,
        "in_progress"
    );

    setupBoardDrop(
        columns.done,
        "done"
    );
}


function setupBoardDrop(
    column,
    targetStatus
) {
    if (!column) {
        return;
    }

    column.ondragover = event => {
        event.preventDefault();

        column.style.borderColor =
            "rgba(139,92,246,.45)";
    };

    column.ondragleave = () => {
        column.style.borderColor = "";
    };

    column.ondrop = async event => {
        event.preventDefault();

        column.style.borderColor = "";

        const taskId =
            event.dataTransfer.getData(
                "text/plain"
            );

        if (!taskId) {
            return;
        }

        try {
            await api(
                `/api/tasks/${taskId}`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        status: targetStatus,
                    }),
                }
            );

            showToast(
                targetStatus === "done"
                    ? "Task completed ✓"
                    : "Task moved successfully.",
                "success"
            );

            await loadTasks();

        } catch (error) {
            showToast(
                error.message,
                "error"
            );
        }
    };
}


// ============================================================
// CALENDAR
// ============================================================

function renderCalendar() {
    const root = $("calendar-grid");
    const monthLabel = $("calendar-month");

    if (!root || !monthLabel) {
        return;
    }

    const year =
        calendarDate.getFullYear();

    const month =
        calendarDate.getMonth();

    monthLabel.textContent =
        calendarDate.toLocaleDateString(
            "en-IN",
            {
                month: "long",
                year: "numeric",
            }
        );

    const firstDay =
        new Date(
            year,
            month,
            1
        ).getDay();

    const lastDate =
        new Date(
            year,
            month + 1,
            0
        ).getDate();

    let html = "";

    for (
        let i = 0;
        i < firstDay;
        i++
    ) {
        html += `
            <div class="calendar-day"></div>
        `;
    }

    for (
        let day = 1;
        day <= lastDate;
        day++
    ) {
        const dayTasks =
            tasks.filter(task => {
                if (!task.due_date) {
                    return false;
                }

                const date =
                    new Date(task.due_date);

                return (
                    date.getFullYear() === year &&
                    date.getMonth() === month &&
                    date.getDate() === day
                );
            });

        html += `
            <div class="calendar-day">

                <div class="calendar-day-date">
                    ${day}
                </div>

                ${
                    dayTasks.length
                        ? dayTasks
                            .map(
                                task => `
                                    <div class="calendar-day-task">
                                        ${escapeHTML(
                                            task.title
                                        )}
                                    </div>
                                `
                            )
                            .join("")
                        : `
                            <div
                                style="
                                    margin-top:16px;
                                    color:#607089;
                                    font-size:9px;
                                "
                            >
                                No tasks
                            </div>
                        `
                }

            </div>
        `;
    }

    root.innerHTML = html;
}


// ============================================================
// REMINDERS
// ============================================================

async function loadReminders() {
    const root = $("reminder-list");

    if (!root) {
        return;
    }

    try {
        const reminders =
            await api(
                "/api/tasks/reminders"
            );

        if (!reminders.length) {
            root.innerHTML = `
                <div class="empty-state compact">
                    <div>◷</div>
                    <span>
                        No urgent deadlines right now.
                    </span>
                </div>
            `;

            $("notification-count")
                ?.classList.add("hidden");

            renderNotifications([]);

            return;
        }

        root.innerHTML =
            reminders
                .slice(0, 5)
                .map(
                    item => `
                        <div class="reminder-item ${
                            item.type === "overdue"
                                ? "overdue"
                                : ""
                        }">

                            <div class="reminder-icon">
                                ${
                                    item.type === "overdue"
                                        ? "!"
                                        : "◷"
                                }
                            </div>

                            <div class="reminder-copy">

                                <strong>
                                    ${escapeHTML(item.title)}
                                </strong>

                                <span>
                                    ${
                                        item.type === "overdue"
                                            ? "Overdue"
                                            : "Due soon"
                                    }
                                    ·
                                    ${escapeHTML(
                                        formatDate(
                                            item.due_date
                                        )
                                    )}
                                </span>

                            </div>

                        </div>
                    `
                )
                .join("");

        $("notification-count").textContent =
            reminders.length;

        $("notification-count")
            ?.classList.remove("hidden");

        renderNotifications(reminders);

    } catch (error) {
        console.warn(
            "Reminder loading failed:",
            error
        );
    }
}


function renderNotifications(reminders) {
    const root = $("notification-list");

    if (!root) {
        return;
    }

    root.innerHTML =
        reminders.length
            ? reminders
                .map(
                    item => `
                        <div class="notification-item">

                            <strong>
                                ${
                                    item.type === "overdue"
                                        ? "⚠ Task overdue"
                                        : "◷ Deadline approaching"
                                }
                            </strong>

                            <span>
                                ${escapeHTML(item.title)}
                                ·
                                ${escapeHTML(
                                    formatDate(
                                        item.due_date
                                    )
                                )}
                            </span>

                        </div>
                    `
                )
                .join("")
            : `
                <div class="empty-state compact">
                    <span>
                        Nothing needs your attention.
                    </span>
                </div>
            `;
}


// ============================================================
// CREATE TASK
// ============================================================

async function createTask(event) {
    event.preventDefault();

    const title =
        $("task-title-input")
            .value
            .trim();

    const description =
        $("task-description-input")
            .value
            .trim();

    const priority =
        $("task-priority-input")
            .value;

    const status =
        $("task-status-input")
            .value;

    const dueValue =
        $("task-due-input")
            .value;

    const message =
        $("task-form-message");

    if (!title) {
        message.textContent =
            "Task title is required.";

        message.className =
            "form-message error";

        return;
    }

    try {
        const subtasks =
            getGeneratedSubtasks();

        await api(
            "/api/tasks",
            {
                method: "POST",
                body: JSON.stringify({
                    title,
                    description:
                        description || null,
                    priority,
                    status,
                    due_date:
                        dueValue
                            ? new Date(
                                dueValue
                            ).toISOString()
                            : null,
                    subtasks:
                        subtasks.map(
                            item => ({
                                title: item,
                            })
                        ),
                }),
            }
        );

        closeTaskModal();

        showToast(
            "Task created successfully.",
            "success"
        );

        await loadTasks();

    } catch (error) {
        message.textContent =
            error.message;

        message.className =
            "form-message error";
    }
}


function closeTaskModal() {
    $("task-modal")
        ?.classList.add("hidden");

    $("task-form")
        ?.reset();

    $("generated-subtasks")
        .innerHTML = "";

    $("task-ai-suggestion")
        .textContent =
        "Let CORTEX analyze this task.";

    $("task-form-message")
        .textContent = "";
}


// ============================================================
// COMPLETE TASK ✅
// ============================================================

async function completeTask(id) {
    try {

        await api(
            `/api/tasks/${id}/complete`,
            {
                method: "POST",
            }
        );

        showToast(
            "Task completed successfully ✓",
            "success"
        );

        await loadTasks();

    } catch (error) {

        showToast(
            error.message ||
            "Unable to complete task.",
            "error"
        );
    }
}


// ============================================================
// SET TASK STATUS
// ============================================================

async function setTaskStatus(id, status) {

    const validStatuses = [
        "todo",
        "in_progress",
        "done",
    ];

    if (!validStatuses.includes(status)) {
        showToast(
            "Invalid task status.",
            "error"
        );
        return;
    }

    const task =
        tasks.find(
            item =>
                String(item.id) ===
                String(id)
        );

    if (!task) {
        return;
    }

    if (task.status === status) {
        return;
    }

    try {

        if (status === "done") {

            await api(
                `/api/tasks/${id}/complete`,
                {
                    method: "POST",
                }
            );

            showToast(
                "Task completed successfully ✓",
                "success"
            );

        } else {

            await api(
                `/api/tasks/${id}`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        status: status,
                    }),
                }
            );

            showToast(
                `Task moved to ${statusLabel(status)}.`,
                "success"
            );
        }

        await loadTasks();

    } catch (error) {

        showToast(
            error.message ||
            "Unable to update task status.",
            "error"
        );
    }
}


// ============================================================

// DELETE TASK
// ============================================================

async function deleteTask(id) {
    const confirmDelete = await showConfirmModal(
        "Delete task",
        "Are you sure you want to delete this task permanently?"
    );

    if (!confirmDelete) {
        return;
    }

    await api(
        `/api/tasks/${id}`,
        {
            method: "DELETE",
        }
    );

    showToast(
        "Task deleted.",
        "success"
    );

    await loadTasks();
}

// ============================================================
// CLEAR ALL TASKS
// ============================================================

async function clearAllTasks() {
    if (!tasks.length) {
        showToast(
            "There are no tasks to clear.",
            "normal"
        );
        return;
    }

    const confirmed = await showConfirmModal(
        "Clear all tasks",
        `Are you sure you want to delete all ${tasks.length} tasks permanently?`
    );

    if (!confirmed) {
        return;
    }

    try {
        await api(
            "/api/tasks/clear-all",
            {
                method: "DELETE",
            }
        );

        tasks = [];

        renderTaskList();
        renderFocusTasks();
        renderRecentTasks();
        renderBoard();
        renderCalendar();

        showToast(
            "All tasks cleared successfully.",
            "success"
        );

        await loadStats();
        await loadReminders();

    } catch (error) {
        console.error(
            "Clear all tasks failed:",
            error
        );

        showToast(
            error.message ||
            "Unable to clear all tasks.",
            "error"
        );
    }
}

// ============================================================
// TASK ACTIONS
// ============================================================

function attachTaskActions() {

    document
        .querySelectorAll(
            "[data-task-action]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                async event => {

                    event.stopPropagation();

                    const id =
                        button.dataset.taskId;

                    const action =
                        button.dataset.taskAction;

                    try {

                        if (
                            action === "complete"
                        ) {

                            await completeTask(id);

                        } else if (
                            action === "set-status"
                        ) {

                            await setTaskStatus(
                                id,
                                button.dataset.status
                            );

                        } else if (
                            action === "delete"
                        ) {

                            await deleteTask(id);

                        } else if (
                            action === "ai"
                        ) {

                            await openTaskAI(id);
                        }

                    } catch (error) {

                        showToast(
                            error.message,
                            "error"
                        );
                    }
                }
            );
        });
}


// ============================================================
// AI TASK ANALYSIS
// ============================================================

async function analyzeCurrentTask() {

    const title =
        $("task-title-input")
            .value
            .trim();

    const description =
        $("task-description-input")
            .value
            .trim();

    if (!title) {
        $("task-ai-suggestion")
            .textContent =
            "Enter a task title first.";

        return;
    }

    const button =
        $("analyze-task-button");

    button.disabled = true;
    button.textContent = "Thinking...";

    try {

        const result =
            await api(
                "/api/ai/analyze-task",
                {
                    method: "POST",
                    body: JSON.stringify({
                        title,
                        description:
                            description ||
                            null,
                    }),
                }
            );

        if (
            result.priority &&
            $("task-priority-input")
        ) {
            $("task-priority-input")
                .value =
                result.priority;
        }

        $("task-ai-suggestion")
            .textContent =
            result.reason ||
            "CORTEX analyzed your task.";

        renderGeneratedSubtasks(
            result.subtasks || []
        );

    } catch (error) {

        $("task-ai-suggestion")
            .textContent =
            error.message;

    } finally {

        button.disabled = false;
        button.textContent = "Analyze";
    }
}


function renderGeneratedSubtasks(
    subtasks
) {

    const root =
        $("generated-subtasks");

    if (!root) {
        return;
    }

    if (
        !Array.isArray(subtasks) ||
        !subtasks.length
    ) {
        root.innerHTML = "";
        return;
    }

    root.innerHTML = `
        <div
            style="
                margin-bottom:8px;
                color:#a99bf6;
                font-size:10px;
                font-weight:700;
            "
        >
            ✦ Suggested subtasks
        </div>

        ${
            subtasks
                .map(
                    item => `
                        <div
                            class="generated-subtask-row"
                            data-subtask="${escapeHTML(item)}"
                        >
                            <span>✓</span>
                            ${escapeHTML(item)}
                        </div>
                    `
                )
                .join("")
        }
    `;
}


function getGeneratedSubtasks() {
    return [
        ...document.querySelectorAll(
            "[data-subtask]"
        ),
    ].map(
        element =>
            element.dataset.subtask
    );
}


// ============================================================
// TASK AI
// ============================================================

async function openTaskAI(id) {

    const task =
        tasks.find(
            item =>
                String(item.id) ===
                String(id)
        );

    if (!task) {
        return;
    }

    try {

        const result =
            await api(
                "/api/ai/analyze-task",
                {
                    method: "POST",
                    body: JSON.stringify({
                        title: task.title,
                        description:
                            task.description ||
                            null,
                    }),
                }
            );

        let text =
            `CORTEX suggestion: ${
                (
                    result.priority ||
                    task.priority ||
                    "medium"
                ).toUpperCase()
            }`;

        if (result.reason) {
            text +=
                `\n\n${result.reason}`;
        }

        if (
            Array.isArray(
                result.subtasks
            ) &&
            result.subtasks.length
        ) {

            text +=
                "\n\nSuggested subtasks:\n";

            text +=
                result.subtasks
                    .map(
                        item =>
                            `• ${item}`
                    )
                    .join("\n");
        }

        showToast(
            text,
            "normal"
        );

    } catch (error) {

        showToast(
            error.message,
            "error"
        );
    }
}


// ============================================================
// AI CHAT
// ============================================================

function formatAIResponse(text) {

    if (!text) {
        return "";
    }

    let html = escapeHTML(text.trim());

    // Bold: **text**
    html = html.replace(
        /\*\*(.*?)\*\*/g,
        "<strong>$1</strong>"
    );

    // Inline code: `code`
    html = html.replace(
        /`([^`]+)`/g,
        "<code>$1</code>"
    );

    // Headings
    html = html.replace(
        /^### (.*?)$/gm,
        "<h4>$1</h4>"
    );

    html = html.replace(
        /^## (.*?)$/gm,
        "<h3>$1</h3>"
    );

    // Bullet points
    html = html.replace(
        /^[-•]\s+(.*?)$/gm,
        '<div class="ai-list-item"><span>•</span><div>$1</div></div>'
    );

    // Numbered points
    html = html.replace(
        /^(\d+)\.\s+(.*?)$/gm,
        '<div class="ai-number-item"><span>$1.</span><div>$2</div></div>'
    );

    // Paragraph spacing
    html = html.replace(
        /\n{2,}/g,
        '<div class="ai-response-gap"></div>'
    );

    // Line breaks
    html = html.replace(
        /\n/g,
        "<br>"
    );

    return html;
}


function appendAIMessage(
    text,
    type = "assistant"
) {

    const root = $("ai-messages");

    if (!root) {
        return null;
    }

    const wrapper =
        document.createElement("div");

    wrapper.className =
        `ai-message ${
            type === "user"
                ? "user"
                : "assistant"
        }`;

    const avatar =
        type === "user"
            ? (
                currentUser?.name
                    ?.charAt(0)
                    ?.toUpperCase() || "U"
            )
            : "✦";

    wrapper.innerHTML = `

        <div class="message-avatar">
            ${avatar}
        </div>

        <div class="message-content">

            <div class="message-meta">

                <span class="message-name">
                    ${
                        type === "user"
                            ? "You"
                            : "CORTEX"
                    }
                </span>

            </div>

            <div class="message-bubble">

                <div class="ai-response">
                    ${
                        text
                            ? formatAIResponse(text)
                            : ""
                    }
                </div>

            </div>

        </div>
    `;

    root.appendChild(wrapper);

    root.scrollTop =
        root.scrollHeight;

    return wrapper.querySelector(
        ".ai-response"
    );
}


async function sendAIMessage(message) {

    const clean =
        message.trim();

    if (!clean) {
        return;
    }


    // USER MESSAGE

    appendAIMessage(
        clean,
        "user"
    );


    // CORTEX THINKING

    const responseTarget =
        appendAIMessage(
            "",
            "assistant"
        );


    if (responseTarget) {

        responseTarget.innerHTML = `

            <div class="cortex-thinking">

                <span></span>
                <span></span>
                <span></span>

                <em>
                    CORTEX is thinking
                </em>

            </div>
        `;
    }


    try {

        const result =
            await api(
                "/api/ai/assistant",
                {
                    method: "POST",

                    body: JSON.stringify({
                        message: clean,
                    }),
                }
            );


        const answer =
            result.answer ||
            "I don't have a useful answer yet.";


        if (responseTarget) {

            responseTarget.innerHTML =
                formatAIResponse(answer);

        }


    } catch (error) {

        if (responseTarget) {

            responseTarget.innerHTML = `
                <span class="ai-error">
                    ${escapeHTML(error.message)}
                </span>
            `;

        }

    }


    const root =
        $("ai-messages");

    if (root) {

        root.scrollTop =
            root.scrollHeight;

    }
}


function runQuickAI(action) {

    const prompts = {

        plan:
            "Plan my day using my current tasks. Give me the top 3 actions and explain why they should be done in that order.",

        prioritize:
            "Prioritize my current tasks. Tell me which task deserves attention first and why.",

        overdue:
            "Which of my current tasks are overdue or at risk? Give me practical next actions.",

        workload:
            "Analyze my current workload and tell me whether it looks manageable. Suggest a realistic plan.",
    };

    sendAIMessage(
        prompts[action] || action
    );
}



// ============================================================
// VIEW SWITCHING
// ============================================================

function switchView(view) {

    currentView = view;

    const views = [
        "dashboard",
        "tasks",
        "board",
        "calendar",
        "ai",
        "profile",
    ];

    views.forEach(name => {

        const section =
            $(`${name}-view`);

        if (!section) {
            return;
        }

        section.classList.toggle(
            "active-view",
            name === view
        );
    });

    document
        .querySelectorAll(
            ".nav-item[data-view]"
        )
        .forEach(button => {

            button.classList.toggle(
                "active",
                button.dataset.view === view
            );
        });

    if (view === "board") {
        renderBoard();
    }

    if (view === "calendar") {
        renderCalendar();
    }
}


// ============================================================
// MOBILE SIDEBAR
// ============================================================

function toggleMobileSidebar(open) {

    const sidebar =
        $("sidebar");

    const overlay =
        $("sidebar-overlay");

    sidebar?.classList.toggle(
        "mobile-open",
        open
    );

    overlay?.classList.toggle(
        "mobile-open",
        open
    );
}


// ============================================================
// TASK MODAL
// ============================================================

function openTaskModal() {

    $("task-modal")
        ?.classList.remove(
            "hidden"
        );

    setTimeout(
        () => {
            $("task-title-input")
                ?.focus();
        },
        50
    );
}


// ============================================================
// INITIAL EVENTS
// ============================================================

document.addEventListener(
    "DOMContentLoaded",
    async () => {

        // ----------------------------------------------------
        // CORTEX DATE + TIME PICKER
        // ----------------------------------------------------

        const dueInput = document.getElementById(
            "task-due-input"
        );

        if (dueInput && typeof flatpickr !== "undefined") {
            flatpickr(dueInput, {
                enableTime: true,
                dateFormat: "Y-m-d H:i",
                altInput: true,
                altFormat: "d M Y • h:i K",
                time_24hr: false,
                minuteIncrement: 5,
                allowInput: false
            });
        }

        // ----------------------------------------------------
        // NAVIGATION
        // ----------------------------------------------------

        document
            .querySelectorAll(
                ".nav-item[data-view]"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () => {

                        switchView(
                            button.dataset.view
                        );

                        toggleMobileSidebar(
                            false
                        );
                    }
                );
            });

        // ----------------------------------------------------
        // TOP PROFILE AVATAR
        // ----------------------------------------------------

        $("top-avatar")
            ?.addEventListener(
                "click",
                () => {
                    switchView("profile");
                }
            );

        // ----------------------------------------------------
        // THEME
        // ----------------------------------------------------

        $("toggle-theme")
            ?.addEventListener(
                "click",
                toggleTheme
            );


        // ----------------------------------------------------
        // LOGOUT
        // ----------------------------------------------------

        $("logout-button")
            ?.addEventListener(
                "click",
                () => {

                    localStorage.removeItem(
                        "access_token"
                    );

                    window.location.href =
                        "index.html";
                }
            );


        // ----------------------------------------------------
        // MOBILE MENU
        // ----------------------------------------------------

        $("mobile-menu")
            ?.addEventListener(
                "click",
                () =>
                    toggleMobileSidebar(true)
            );

        $("sidebar-overlay")
            ?.addEventListener(
                "click",
                () =>
                    toggleMobileSidebar(false)
            );


        // ----------------------------------------------------
        // NEW TASK
        // ----------------------------------------------------

        $("quick-add-task")
            ?.addEventListener(
                "click",
                openTaskModal
            );

        $("hero-new-task")
            ?.addEventListener(
                "click",
                openTaskModal
            );

        $("tasks-new-button")
            ?.addEventListener(
                "click",
                openTaskModal
            );

        $("board-new-button")
            ?.addEventListener(
                "click",
                openTaskModal
            );


        // ----------------------------------------------------
        // IMPORT CSV
        // ----------------------------------------------------

        $("import-csv-button")
            ?.addEventListener(
                "click",
                () => {
                    $("csv-file-input")?.click();
                }
            );

        $("clear-all-tasks-button")
            ?.addEventListener(
                "click",
                clearAllTasks
            );
    
        $("import-csv-modal-button")
            ?.addEventListener(
                "click",
                () => {
                    $("csv-file-input")?.click();
                }
            );    

        $("csv-file-input")
            ?.addEventListener(
                "change",
                async event => {
                    const files = event.target.files;

                    if (!files || !files.length) {
                        return;
                    }

                    await importCSV(files);

                    // Allow selecting the same file again
                    event.target.value = "";
                }
            );    

        // ----------------------------------------------------
        // CLOSE MODAL
        // ----------------------------------------------------

        document
            .querySelectorAll(
                "[data-close-modal]"
            )
            .forEach(element => {

                element.addEventListener(
                    "click",
                    closeTaskModal
                );
            });


        // ----------------------------------------------------
        // TASK FORM
        // ----------------------------------------------------

        $("task-form")
            ?.addEventListener(
                "submit",
                createTask
            );


        $("analyze-task-button")
            ?.addEventListener(
                "click",
                analyzeCurrentTask
            );


        // ----------------------------------------------------
        // FILTERS
        // ----------------------------------------------------

        $("task-search")
            ?.addEventListener(
                "input",
                loadTasks
            );

        [
            "status-filter",
            "priority-filter",
            "due-filter",
            "sort-filter",
        ].forEach(id => {

            $(id)?.addEventListener(
                "change",
                loadTasks
            );
        });


        // ----------------------------------------------------
        // DASHBOARD ACTIONS
        // ----------------------------------------------------

        $("hero-ai-button")
            ?.addEventListener(
                "click",
                () =>
                    switchView("ai")
            );


        $("plan-day-button")
            ?.addEventListener(
                "click",
                () => {

                    switchView("ai");

                    runQuickAI("plan");
                }
            );


        $("view-all-tasks")
            ?.addEventListener(
                "click",
                () =>
                    switchView("tasks")
            );


        // ----------------------------------------------------
        // NOTIFICATIONS
        // ----------------------------------------------------

        $("notification-button")
            ?.addEventListener(
                "click",
                () => {

                    $("notification-panel")
                        ?.classList.toggle(
                            "hidden"
                        );
                }
            );


        $("close-notifications")
            ?.addEventListener(
                "click",
                () => {

                    $("notification-panel")
                        ?.classList.add(
                            "hidden"
                        );
                }
            );


        $("refresh-reminders")
            ?.addEventListener(
                "click",
                loadReminders
            );


        // ----------------------------------------------------
        // AI FORM
        // ----------------------------------------------------

        $("ai-form")
            ?.addEventListener(
                "submit",
                event => {

                    event.preventDefault();

                    const input =
                        $("ai-input");

                    const text =
                        input.value.trim();

                    if (!text) {
                        return;
                    }

                    input.value = "";

                    sendAIMessage(text);
                }
            );


        document
            .querySelectorAll(
                ".ai-suggestion"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () =>
                        sendAIMessage(
                            button.dataset.aiPrompt
                        )
                );
            });


        document
            .querySelectorAll(
                ".ai-action-card"
            )
            .forEach(button => {

                button.addEventListener(
                    "click",
                    () =>
                        runQuickAI(
                            button.dataset.aiAction
                        )
                );
            });


        // ----------------------------------------------------
        // CALENDAR
        // ----------------------------------------------------

        $("calendar-prev")
            ?.addEventListener(
                "click",
                () => {

                    calendarDate =
                        new Date(
                            calendarDate.getFullYear(),
                            calendarDate.getMonth() - 1,
                            1
                        );

                    renderCalendar();
                }
            );


        $("calendar-next")
            ?.addEventListener(
                "click",
                () => {

                    calendarDate =
                        new Date(
                            calendarDate.getFullYear(),
                            calendarDate.getMonth() + 1,
                            1
                        );

                    renderCalendar();
                }
            );


        $("calendar-today")
            ?.addEventListener(
                "click",
                () => {

                    calendarDate =
                        new Date();

                    renderCalendar();
                }
            );


        // ----------------------------------------------------
        // KEYBOARD SHORTCUTS
        // ----------------------------------------------------

        document.addEventListener(
            "keydown",
            event => {

                const tag =
                    document.activeElement
                        ?.tagName
                        ?.toLowerCase();

                if (
                    tag === "input" ||
                    tag === "textarea" ||
                    tag === "select"
                ) {
                    return;
                }

                if (
                    event.key === "n" ||
                    event.key === "N"
                ) {

                    event.preventDefault();

                    openTaskModal();
                }

                if (event.key === "/") {

                    event.preventDefault();

                    switchView("tasks");

                    setTimeout(
                        () =>
                            $("task-search")
                                ?.focus(),
                        50
                    );
                }

                if (event.key === "Escape") {

                    closeTaskModal();

                    $("notification-panel")
                        ?.classList.add(
                            "hidden"
                        );
                }
            }
        );


        // ----------------------------------------------------
        // LOAD APP
        // ----------------------------------------------------

        try {

            await loadProfile();
            await loadTasks();

        } catch (error) {

            console.error(
                "CORTEX initialization failed:",
                error
            );

            showToast(
                error.message ||
                "Unable to load CORTEX.",
                "error"
            );
        }
    }
);
