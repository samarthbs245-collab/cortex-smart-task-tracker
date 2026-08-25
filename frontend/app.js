const API_URL = "https://cortex-rgzd.onrender.com";


// ============================================================
// ELEMENTS
// ============================================================

const loginSection = document.getElementById("login-section");
const registerSection = document.getElementById("register-section");

const showRegisterButton = document.getElementById("show-register");
const showLoginButton = document.getElementById("show-login");

const loginForm = document.getElementById("login-form");
const registerForm = document.getElementById("register-form");


// ============================================================
// CHECK ELEMENTS
// ============================================================

if (
    !loginSection ||
    !registerSection ||
    !showRegisterButton ||
    !showLoginButton ||
    !loginForm ||
    !registerForm
) {
    console.error(
        "CORTEX: Required authentication elements were not found."
    );
}


// ============================================================
// SWITCH TO REGISTER
// ============================================================

showRegisterButton.addEventListener("click", () => {

    loginSection.classList.add("hidden");

    registerSection.classList.remove("hidden");

    // Clear previous messages
    const loginMessage =
        document.getElementById("login-message");

    const registerMessage =
        document.getElementById("register-message");

    if (loginMessage) {
        loginMessage.textContent = "";
    }

    if (registerMessage) {
        registerMessage.textContent = "";
    }

});


// ============================================================
// SWITCH TO LOGIN
// ============================================================

showLoginButton.addEventListener("click", () => {

    registerSection.classList.add("hidden");

    loginSection.classList.remove("hidden");

    // Clear previous messages
    const loginMessage =
        document.getElementById("login-message");

    const registerMessage =
        document.getElementById("register-message");

    if (loginMessage) {
        loginMessage.textContent = "";
    }

    if (registerMessage) {
        registerMessage.textContent = "";
    }

});


// ============================================================
// EMAIL VALIDATION
// ============================================================

function isValidEmail(email) {

    const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

    return emailPattern.test(email);
}


// ============================================================
// SHOW MESSAGE
// ============================================================

function showMessage(element, message, type) {

    if (!element) {
        return;
    }

    element.textContent = message;

    if (type === "success") {

        element.style.color = "#34d399";

    } else {

        element.style.color = "#fb7185";

    }
}


// ============================================================
// LOGIN
// ============================================================

loginForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        // ----------------------------------------------------
        // Get values
        // ----------------------------------------------------

        const email =
            document
                .getElementById("login-email")
                .value
                .trim();


        const password =
            document
                .getElementById("login-password")
                .value;


        const emailError =
            document.getElementById(
                "login-email-error"
            );


        const message =
            document.getElementById(
                "login-message"
            );


        // ----------------------------------------------------
        // Clear old messages
        // ----------------------------------------------------

        emailError.textContent = "";

        message.textContent = "";


        // ----------------------------------------------------
        // Validate email
        // ----------------------------------------------------

        if (!isValidEmail(email)) {

            emailError.textContent =
                "Invalid email address. Please enter a valid email.";

            return;
        }


        // ----------------------------------------------------
        // Validate password
        // ----------------------------------------------------

        if (!password) {

            showMessage(
                message,
                "Please enter your password.",
                "error"
            );

            return;
        }


        // ----------------------------------------------------
        // Loading state
        // ----------------------------------------------------

        const button =
            loginForm.querySelector(
                ".primary-button"
            );


        const originalButtonText =
            button.innerHTML;


        button.disabled = true;

        button.style.opacity = "0.7";

        button.innerHTML =
            "<span>Signing in...</span>";


        try {

            // ------------------------------------------------
            // Send login request
            // ------------------------------------------------

            const response =
                await fetch(
                    `${API_URL}/api/auth/login`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({
                            email: email,
                            password: password
                        })
                    }
                );


            const data =
                await response.json();


            // ------------------------------------------------
            // Login failed
            // ------------------------------------------------

            if (!response.ok) {

                if (response.status === 401) {

                    showMessage(
                        message,
                        "Incorrect email or password.",
                        "error"
                    );

                } else if (
                    response.status === 422
                ) {

                    showMessage(
                        message,
                        "Please enter valid login information.",
                        "error"
                    );

                } else {

                    showMessage(
                        message,
                        data.detail ||
                            "Login failed. Please try again.",
                        "error"
                    );
                }

                return;
            }


            // ------------------------------------------------
            // Make sure token exists
            // ------------------------------------------------

            if (!data.access_token) {

                showMessage(
                    message,
                    "Login succeeded, but no access token was received.",
                    "error"
                );

                return;
            }


            // ------------------------------------------------
            // Save JWT
            // ------------------------------------------------

            localStorage.setItem(
                "access_token",
                data.access_token
            );


            // ------------------------------------------------
            // Login successful
            // ------------------------------------------------

            showMessage(
                message,
                "Login successful. Welcome to CORTEX!",
                "success"
            );


            console.log(
                "CORTEX login successful."
            );


            // ------------------------------------------------
            // Redirect to dashboard
            // ------------------------------------------------

            setTimeout(() => {

                window.location.href =
                    "dashboard.html";

            }, 700);


        } catch (error) {

            console.error(
                "CORTEX login error:",
                error
            );


            showMessage(
                message,
                "Unable to connect to the CORTEX server.",
                "error"
            );


        } finally {

            button.disabled = false;

            button.style.opacity = "1";

            button.innerHTML =
                originalButtonText;
        }

    }
);


// ============================================================
// REGISTRATION
// ============================================================

registerForm.addEventListener(
    "submit",
    async (event) => {

        event.preventDefault();


        // ----------------------------------------------------
        // Get values
        // ----------------------------------------------------

        const name =
            document
                .getElementById("register-name")
                .value
                .trim();


        const email =
            document
                .getElementById("register-email")
                .value
                .trim();


        const password =
            document
                .getElementById("register-password")
                .value;


        const age =
            Number(
                document
                    .getElementById("register-age")
                    .value
            );


        const hoursInput =
            document
                .getElementById("register-hours")
                .value;


        const availableHours =
            hoursInput === ""
                ? null
                : Number(hoursInput);


        const goal =
            document
                .getElementById("register-goal")
                .value;


        const emailError =
            document.getElementById(
                "register-email-error"
            );


        const message =
            document.getElementById(
                "register-message"
            );


        // ----------------------------------------------------
        // Clear old messages
        // ----------------------------------------------------

        emailError.textContent = "";

        message.textContent = "";


        // ----------------------------------------------------
        // Validate name
        // ----------------------------------------------------

        if (name.length < 2) {

            showMessage(
                message,
                "Please enter your full name.",
                "error"
            );

            return;
        }


        // ----------------------------------------------------
        // Validate email
        // ----------------------------------------------------

        if (!isValidEmail(email)) {

            emailError.textContent =
                "Invalid email address. Please enter a valid email.";

            return;
        }


        // ----------------------------------------------------
        // Validate password
        // ----------------------------------------------------

        if (password.length < 8) {

            showMessage(
                message,
                "Password must contain at least 8 characters.",
                "error"
            );

            return;
        }


        // ----------------------------------------------------
        // Validate age
        // ----------------------------------------------------

        if (
            !Number.isInteger(age) ||
            age < 13 ||
            age > 120
        ) {

            showMessage(
                message,
                "Please enter a valid age between 13 and 120.",
                "error"
            );

            return;
        }


        // ----------------------------------------------------
        // Validate available hours
        // ----------------------------------------------------

        if (
            availableHours !== null &&
            (
                Number.isNaN(availableHours) ||
                availableHours < 0 ||
                availableHours > 24
            )
        ) {

            showMessage(
                message,
                "Available hours must be between 0 and 24.",
                "error"
            );

            return;
        }


        // ----------------------------------------------------
        // Loading state
        // ----------------------------------------------------

        const button =
            registerForm.querySelector(
                ".primary-button"
            );


        const originalButtonText =
            button.innerHTML;


        button.disabled = true;

        button.style.opacity = "0.7";

        button.innerHTML =
            "<span>Creating your CORTEX...</span>";


        try {

            // ------------------------------------------------
            // Send registration request
            // ------------------------------------------------

            const response =
                await fetch(
                    `${API_URL}/api/auth/register`,
                    {
                        method: "POST",

                        headers: {
                            "Content-Type":
                                "application/json"
                        },

                        body: JSON.stringify({

                            name: name,

                            email: email,

                            password: password,

                            age: age,

                            goal:
                                goal === ""
                                    ? null
                                    : goal,

                            available_hours:
                                availableHours

                        })
                    }
                );


            const data =
                await response.json();


            // ------------------------------------------------
            // Registration failed
            // ------------------------------------------------

            if (!response.ok) {

                if (
                    response.status === 409
                ) {

                    showMessage(
                        message,
                        "An account with this email already exists.",
                        "error"
                    );

                } else if (
                    response.status === 422
                ) {

                    showMessage(
                        message,
                        "Please check your information. Make sure your email and age are valid.",
                        "error"
                    );

                } else {

                    showMessage(
                        message,
                        data.detail ||
                            "Registration failed. Please try again.",
                        "error"
                    );
                }

                return;
            }


            // ------------------------------------------------
            // Registration successful
            // ------------------------------------------------

            showMessage(
                message,
                "Account created successfully! Redirecting to sign in...",
                "success"
            );


            // ------------------------------------------------
            // Move to login
            // ------------------------------------------------

            setTimeout(() => {

                registerSection.classList.add(
                    "hidden"
                );

                loginSection.classList.remove(
                    "hidden"
                );


                // Put registered email
                // into login field

                document.getElementById(
                    "login-email"
                ).value = email;


                // Clear registration form

                registerForm.reset();


                // Focus password

                document.getElementById(
                    "login-password"
                ).focus();


                // Clear success message

                message.textContent = "";

            }, 1200);


        } catch (error) {

            console.error(
                "CORTEX registration error:",
                error
            );


            showMessage(
                message,
                "Unable to connect to the CORTEX server.",
                "error"
            );


        } finally {

            button.disabled = false;

            button.style.opacity = "1";

            button.innerHTML =
                originalButtonText;
        }

    }
);


// ============================================================
// EXISTING LOGIN SESSION
// ============================================================

window.addEventListener(
    "load",
    () => {

        const token =
            localStorage.getItem(
                "access_token"
            );


        if (token) {

            console.log(
                "Existing CORTEX session detected."
            );

            /*
             * We intentionally don't automatically
             * redirect here yet.
             *
             * The dashboard will handle authentication
             * when opened.
             */
        }

    }
);