const API_URL = "http://127.0.0.1:8000";

const token = localStorage.getItem("access_token");

// ============================================================
// AUTH CHECK
// ============================================================

if (!token) {
    window.location.href = "index.html";
}


// ============================================================
// ELEMENTS
// ============================================================

const navItems =
    document.querySelectorAll(".nav-item");

const sections = {
    overview:
        document.getElementById("overview-section"),

    tasks:
        document.getElementById("tasks-section"),

    ai:
        document.getElementById("ai-section"),

    profile:
        document.getElementById("profile-section")
};


const logoutButton =
    document.getElementById("logout-button");

const taskModal =
    document.getElementById("task-modal");

const closeModalButton =
    document.getElementById("close-modal");

const addTaskButton =
    document.getElementById("add-task-button");

const createTaskButton =
    document.getElementById("create-task-button");

const taskForm =
    document.getElementById("task-form");


// ============================================================
// TASK DATA
// ============================================================

let tasks = [];


// ============================================================
// NAVIGATION
// ============================================================

navItems.forEach((item) => {

    item.addEventListener("click", () => {

        const sectionName =
            item.dataset.section;

        navItems.forEach((nav) => {
            nav.classList.remove("active");
        });

        item.classList.add("active");

        Object.values(sections).forEach(
            (section) => {

                if (section) {
                    section.classList.add("hidden");
                }

            }
        );

        if (sections[sectionName]) {
            sections[sectionName]
                .classList.remove("hidden");
        }

        // Load tasks whenever My Tasks is opened
        if (sectionName === "tasks") {
            loadTasks();
        }

    });

});


// ============================================================
// LOGOUT
// ============================================================

if (logoutButton) {

    logoutButton.addEventListener(
        "click",
        () => {

            localStorage.removeItem(
                "access_token"
            );

            window.location.href =
                "index.html";
        }
    );

}


// ============================================================
// TASK MODAL
// ============================================================

function openTaskModal() {

    if (!taskModal) {
        return;
    }

    taskModal.classList.remove("hidden");

}


function closeTaskModal() {

    if (!taskModal) {
        return;
    }

    taskModal.classList.add("hidden");

}


if (addTaskButton) {

    addTaskButton.addEventListener(
        "click",
        openTaskModal
    );

}


if (createTaskButton) {

    createTaskButton.addEventListener(
        "click",
        openTaskModal
    );

}


if (closeModalButton) {

    closeModalButton.addEventListener(
        "click",
        closeTaskModal
    );

}


if (taskModal) {

    taskModal.addEventListener(
        "click",
        (event) => {

            if (event.target === taskModal) {
                closeTaskModal();
            }

        }
    );

}


// ============================================================
// API HEADERS
// ============================================================

function getHeaders() {

    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };

}


// ============================================================
// LOAD TASKS
// ============================================================

async function loadTasks() {

    try {

        console.log("Loading CORTEX tasks...");

        const response = await fetch(
            `${API_URL}/api/tasks`,
            {
                method: "GET",
                headers: getHeaders()
            }
        );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Task loading failed:",
                errorText
            );

            return;
        }


        tasks = await response.json();

        console.log(
            "Tasks loaded:",
            tasks
        );


        renderTasks();

        updateTaskStatistics();

    }

    catch (error) {

        console.error(
            "CORTEX task loading error:",
            error
        );

    }

}


// ============================================================
// CREATE TASK
// ============================================================

async function createTask(event) {

    event.preventDefault();

    try {

        // --------------------------------------------
        // Find form fields
        // --------------------------------------------

        const titleInput =
            taskForm.querySelector(
                '[name="title"], #task-title, #title'
            );

        const descriptionInput =
            taskForm.querySelector(
                '[name="description"], #task-description, #description'
            );

        const priorityInput =
            taskForm.querySelector(
                '[name="priority"], #task-priority, #priority'
            );

        const dueDateInput =
            taskForm.querySelector(
                '[name="due_date"], [name="dueDate"], #task-due-date, #due-date'
            );


        // --------------------------------------------
        // Get values
        // --------------------------------------------

        const title =
            titleInput
                ? titleInput.value.trim()
                : "";

        const description =
            descriptionInput
                ? descriptionInput.value.trim()
                : "";

        const priority =
            priorityInput
                ? priorityInput.value
                : "medium";

        const dueDate =
            dueDateInput
                ? dueDateInput.value
                : "";


        // --------------------------------------------
        // Validate title
        // --------------------------------------------

        if (!title) {

            alert(
                "Please enter a task title."
            );

            return;
        }


        // --------------------------------------------
        // Prepare request
        // --------------------------------------------

        const taskData = {

            title: title,

            description:
                description || null,

            priority:
                priority || "medium",

            due_date:
                dueDate
                    ? new Date(dueDate).toISOString()
                    : null

        };


        console.log(
            "Creating task:",
            taskData
        );


        // --------------------------------------------
        // Send to FastAPI
        // --------------------------------------------

        const response = await fetch(
            `${API_URL}/api/tasks`,
            {
                method: "POST",

                headers:
                    getHeaders(),

                body:
                    JSON.stringify(taskData)
            }
        );


        // --------------------------------------------
        // Handle error
        // --------------------------------------------

        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Task creation failed:",
                errorText
            );

            alert(
                "Unable to create task.\n\n" +
                errorText
            );

            return;
        }


        // --------------------------------------------
        // Successful creation
        // --------------------------------------------

        const newTask =
            await response.json();


        console.log(
            "Task created:",
            newTask
        );


        // Add task locally
        tasks.unshift(newTask);


        // Clear form
        taskForm.reset();


        // Close modal
        closeTaskModal();


        // Update dashboard
        renderTasks();

        updateTaskStatistics();


        alert(
            "Task created successfully!"
        );

    }

    catch (error) {

        console.error(
            "CORTEX task creation error:",
            error
        );

        alert(
            "Unable to connect to the CORTEX server."
        );

    }

}


// ============================================================
// FORM SUBMIT
// ============================================================

if (taskForm) {

    taskForm.addEventListener(
        "submit",
        createTask
    );

}


// ============================================================
// FIND TASK CONTAINER
// ============================================================

function getTaskContainer() {

    let container =
        document.getElementById("tasks-list");


    if (!container) {

        container =
            document.getElementById("task-list");

    }


    if (!container) {

        container =
            document.querySelector(".tasks-list");

    }


    if (!container) {

        container =
            document.querySelector(".task-list");

    }


    if (!container) {

        console.warn(
            "CORTEX: Task list container not found."
        );

        return null;

    }


    return container;

}


// ============================================================
// RENDER TASKS
// ============================================================

function renderTasks() {

    const container =
        getTaskContainer();


    if (!container) {
        return;
    }


    container.innerHTML = "";


    if (!tasks.length) {

        container.innerHTML = `
            <div class="cortex-empty-state">
                <div style="font-size: 36px; margin-bottom: 12px;">
                    ✦
                </div>

                <h3>No tasks yet</h3>

                <p>
                    Create your first task and let CORTEX
                    organize your workspace.
                </p>
            </div>
        `;

        return;
    }


    tasks.forEach((task) => {

        const taskElement =
            document.createElement("div");


        taskElement.className =
            "cortex-task-card";


        const completed =
            task.status === "completed";


        taskElement.innerHTML = `

            <div class="cortex-task-main">

                <div class="cortex-task-check">

                    <input
                        type="checkbox"
                        class="task-complete-checkbox"
                        data-id="${task.id}"
                        ${completed ? "checked" : ""}
                    >

                </div>


                <div class="cortex-task-content">

                    <h3
                        class="${completed ? "task-completed" : ""}"
                    >
                        ${escapeHtml(task.title)}
                    </h3>


                    ${
                        task.description
                            ? `
                                <p>
                                    ${escapeHtml(
                                        task.description
                                    )}
                                </p>
                              `
                            : ""
                    }


                    <div class="cortex-task-meta">

                        <span class="task-priority ${getPriorityClass(task.priority)}">
                            ${escapeHtml(
                                task.priority || "medium"
                            )}
                        </span>


                        ${
                            task.due_date
                                ? `
                                    <span>
                                        Due:
                                        ${formatDate(
                                            task.due_date
                                        )}
                                    </span>
                                  `
                                : ""
                        }

                    </div>

                </div>


                <div class="cortex-task-actions">

                    <button
                        type="button"
                        class="task-delete-button"
                        data-id="${task.id}"
                        title="Delete task"
                    >
                        Delete
                    </button>

                </div>

            </div>
        `;


        container.appendChild(
            taskElement
        );

    });


    // --------------------------------------------
    // Complete buttons
    // --------------------------------------------

    container
        .querySelectorAll(
            ".task-complete-checkbox"
        )
        .forEach((checkbox) => {

            checkbox.addEventListener(
                "change",
                async () => {

                    const taskId =
                        Number(
                            checkbox.dataset.id
                        );

                    await toggleTask(
                        taskId,
                        checkbox.checked
                    );

                }
            );

        });


    // --------------------------------------------
    // Delete buttons
    // --------------------------------------------

    container
        .querySelectorAll(
            ".task-delete-button"
        )
        .forEach((button) => {

            button.addEventListener(
                "click",
                async () => {

                    const taskId =
                        Number(
                            button.dataset.id
                        );

                    await deleteTask(
                        taskId
                    );

                }
            );

        });

}


// ============================================================
// TOGGLE TASK COMPLETE
// ============================================================

async function toggleTask(
    taskId,
    completed
) {

    try {

        const response =
            await fetch(
                `${API_URL}/api/tasks/${taskId}`,
                {
                    method: "PUT",

                    headers:
                        getHeaders(),

                    body:
                        JSON.stringify({
                            status:
                                completed
                                    ? "completed"
                                    : "todo"
                        })
                }
            );


        if (!response.ok) {

            console.error(
                "Unable to update task."
            );

            return;

        }


        const updatedTask =
            await response.json();


        tasks =
            tasks.map(
                (task) =>
                    task.id === taskId
                        ? updatedTask
                        : task
            );


        renderTasks();

        updateTaskStatistics();

    }

    catch (error) {

        console.error(
            "Task update error:",
            error
        );

    }

}


// ============================================================
// DELETE TASK
// ============================================================

async function deleteTask(
    taskId
) {

    const confirmed =
        confirm(
            "Delete this task?"
        );


    if (!confirmed) {
        return;
    }


    try {

        const response =
            await fetch(
                `${API_URL}/api/tasks/${taskId}`,
                {
                    method: "DELETE",

                    headers:
                        getHeaders()
                }
            );


        if (!response.ok) {

            const errorText =
                await response.text();

            console.error(
                "Delete failed:",
                errorText
            );

            alert(
                "Unable to delete task."
            );

            return;

        }


        tasks =
            tasks.filter(
                (task) =>
                    task.id !== taskId
            );


        renderTasks();

        updateTaskStatistics();

    }

    catch (error) {

        console.error(
            "Task delete error:",
            error
        );

    }

}


// ============================================================
// SEARCH TASKS
// ============================================================

function setupTaskSearch() {

    const searchInput =
        document.querySelector(
            "#task-search, #search-tasks, input[placeholder*='Search tasks']"
        );


    if (!searchInput) {
        return;
    }


    searchInput.addEventListener(
        "input",
        () => {

            const search =
                searchInput.value
                    .trim()
                    .toLowerCase();


            const filteredTasks =
                tasks.filter(
                    (task) =>
                        task.title
                            .toLowerCase()
                            .includes(search)
                        ||
                        (
                            task.description || ""
                        )
                            .toLowerCase()
                            .includes(search)
                );


            renderFilteredTasks(
                filteredTasks
            );

        }
    );

}


// ============================================================
// RENDER FILTERED TASKS
// ============================================================

function renderFilteredTasks(
    filteredTasks
) {

    const originalTasks =
        tasks;


    tasks =
        filteredTasks;

    renderTasks();

    tasks =
        originalTasks;

}


// ============================================================
// STATISTICS
// ============================================================

function updateTaskStatistics() {

    const total =
        tasks.length;


    const completed =
        tasks.filter(
            (task) =>
                task.status === "completed"
        ).length;


    const pending =
        total - completed;


    const totalElement =
        document.getElementById(
            "total-tasks"
        );


    const completedElement =
        document.getElementById(
            "completed-tasks"
        );


    const pendingElement =
        document.getElementById(
            "pending-tasks"
        );


    if (totalElement) {
        totalElement.textContent =
            total;
    }


    if (completedElement) {
        completedElement.textContent =
            completed;
    }


    if (pendingElement) {
        pendingElement.textContent =
            pending;
    }

}


// ============================================================
// HELPERS
// ============================================================

function escapeHtml(value) {

    if (value === null ||
        value === undefined) {

        return "";

    }


    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");

}


function formatDate(
    dateString
) {

    try {

        return new Date(
            dateString
        ).toLocaleDateString(
            "en-IN",
            {
                day: "numeric",
                month: "short",
                year: "numeric"
            }
        );

    }

    catch {

        return dateString;

    }

}


function getPriorityClass(
    priority
) {

    const value =
        String(
            priority || "medium"
        ).toLowerCase();


    if (value === "high") {
        return "priority-high";
    }


    if (value === "low") {
        return "priority-low";
    }


    return "priority-medium";

}


// ============================================================
// INITIALIZATION
// ============================================================

async function initializeDashboard() {

    console.log(
        "CORTEX dashboard initialized."
    );


    // Load saved tasks from PostgreSQL
    await loadTasks();


    // Enable task search
    setupTaskSearch();


    updateTaskStatistics();

}


initializeDashboard();