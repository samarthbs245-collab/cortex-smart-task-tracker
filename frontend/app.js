// ============================================================
// CORTEX AI FRONTEND APPLICATION
// ============================================================

const API_URL =
"https://cortex-rgzd.onrender.com";

const $ =
(id) => document.getElementById(id);


// ============================================================
// CORTEX AI SPLASH SCREEN
// Brain + Infinity Logo
// ============================================================

window.addEventListener(
"DOMContentLoaded",
() => {

const splash =
$("cortex-splash");

if (!splash) {
return;
}

const progress =
splash.querySelector(
".loader-progress"
);

const percent =
$("loading-percent");

let current = 0;

const timer =
setInterval(
() => {

current +=
Math.floor(
Math.random() * 8
) + 4;

if (current >= 100) {

current = 100;

clearInterval(timer);
}

if (progress) {

progress.style.width =
`${current}%`;
}

if (percent) {

percent.textContent =
`${current}%`;
}

},
100
);


// Automatically close splash
// after initialization.

setTimeout(
() => {

clearInterval(timer);

if (progress) {

progress.style.width =
"100%";
}

if (percent) {

percent.textContent =
"100%";
}

splash.classList.add(
"splash-hidden"
);

},
1900
);

}
);


// ============================================================
// CORTEX AI THINKING LOADER
// ============================================================

function showCortexAILoader(
container
) {

if (!container) {
return;
}


container.innerHTML = `

<div class="cortex-ai-loader">

<img
src="assets/cortex-brain-infinity-logo.png"
alt="CORTEX AI"
>

<span>
CORTEX AI is thinking...
</span>

</div>

`;
}


// ============================================================
// HIDE CORTEX AI LOADER
// ============================================================

function hideCortexAILoader(
container
) {

if (!container) {
return;
}


const loader =
container.querySelector(
".cortex-ai-loader"
);


if (loader) {

loader.remove();

}

}


// ============================================================
// APPROVED EMAIL PROVIDERS
// ============================================================

const APPROVED_EMAIL_DOMAINS =
new Set([

"gmail.com",
"outlook.com",
"hotmail.com",
"live.com",
"yahoo.com",
"icloud.com",
"proton.me",
"protonmail.com"

]);


// ============================================================
// EMAIL VALIDATION
// ============================================================

function isValidEmail(
email
) {

if (
typeof email !==
"string"
) {

return false;

}


const normalized =
email
.trim()
.toLowerCase();


if (!normalized) {

return false;

}


// Basic email structure

const parts =
normalized.split("@");


if (
parts.length !== 2
) {

return false;

}


const local =
parts[0];

const domain =
parts[1];


// Local part validation

if (
!local ||
local.length > 64
) {

return false;

}


// Domain validation

if (
!domain ||
domain.length > 255
) {

return false;

}


// Prevent obvious malformed emails

if (
local.startsWith(".") ||
local.endsWith(".") ||
local.includes("..")
) {

return false;

}


if (
domain.startsWith(".") ||
domain.endsWith(".") ||
domain.includes("..")
) {

return false;

}


// Allowed characters

const emailPattern =
/^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$/;


if (
!emailPattern.test(
normalized
)
) {

return false;

}


// CORTEX approved providers

if (
!APPROVED_EMAIL_DOMAINS.has(
domain
)
) {

return false;

}


return true;

}

// ============================================================
// EMAIL ERROR MESSAGE
// ============================================================

function getEmailError(value) {

const email =
String(value || "")
.trim()
.toLowerCase();

if (!email) {
return "Email address is required.";
}

if (/\s/.test(email)) {
return "Email address cannot contain spaces.";
}

if (
(email.match(/@/g) || []).length !== 1
) {
return "Enter a valid email address.";
}

const [
local,
domain,
] =
email.split("@");

if (!local || !domain) {
return "Enter a valid email address.";
}

if (
local.startsWith(".") ||
local.endsWith(".") ||
local.includes("..")
) {
return "Enter a valid email address.";
}

if (
!APPROVED_EMAIL_DOMAINS.has(domain)
) {
return (
"Please use Gmail, Outlook, Yahoo, iCloud or Proton."
);
}

return "";

}


// ============================================================
// PASSWORD VALIDATION
// ============================================================

function isValidPassword(
password
) {

if (
typeof password !==
"string"
) {

return false;

}


if (
password.length < 8
) {

return false;

}


if (
password.length > 128
) {

return false;

}


const hasUpper =
/[A-Z]/.test(password);

const hasLower =
/[a-z]/.test(password);

const hasNumber =
/[0-9]/.test(password);

const hasSpecial =
/[^A-Za-z0-9]/.test(password);


return (
hasUpper &&
hasLower &&
hasNumber &&
hasSpecial
);

}


// ============================================================
// PASSWORD STRENGTH
// ============================================================

function getPasswordStrength(
password
) {

if (!password) {

return {
score: 0,
text:
"Use 8+ characters with uppercase, lowercase, number and symbol."
};

}


let score = 0;


if (
password.length >= 8
) {

score++;

}


if (
password.length >= 12
) {

score++;

}


if (
/[A-Z]/.test(password)
) {

score++;

}


if (
/[a-z]/.test(password)
) {

score++;

}


if (
/[0-9]/.test(password)
) {

score++;

}


if (
/[^A-Za-z0-9]/.test(password)
) {

score++;

}


let text =
"Weak";


if (score >= 5) {

text =
"Strong";

} else if (score >= 3) {

text =
"Medium";

}


return {
score,
text
};

}


function passwordStrength(
password
) {

const result =
getPasswordStrength(
password
);

let percentage =
0;

if (result.score <= 2) {
percentage = 30;
} else if (result.score <= 4) {
percentage = 65;
} else {
percentage = 100;
}

return {
level: result.text,
percentage,
};

}

// ============================================================
// DISPLAY MESSAGE
// ============================================================

function message(
element,
message,
type = "error"
) {

if (!element) {

return;

}


element.textContent =
message;


element.classList.remove(
"error",
"success"
);


if (type) {

element.classList.add(
type
);

}

}


// ============================================================
// BUTTON LOADING
// ============================================================

function setButtonLoading(
button,
loading,
loadingText = "Please wait..."
) {

if (!button) {

return;

}


if (loading) {

if (
!button.dataset.originalText
) {

button.dataset.originalText =
button.innerHTML;

}


button.disabled =
true;


button.innerHTML = `

<span
class="button-spinner"
></span>

${loadingText}

`;

} else {

button.disabled =
false;


if (
button.dataset.originalText
) {

button.innerHTML =
button.dataset.originalText;

delete button.dataset.originalText;

}

}

}


// ============================================================
// API RESPONSE HELPER
// ============================================================

async function readJSON(
response
) {

const text =
await response.text();

try {

return text
? JSON.parse(text)
: {};

} catch {

return {
detail:
text ||
"Unexpected server response.",
};

}

}

// ============================================================
// PASSWORD VISIBILITY
// ============================================================

document.addEventListener(
"click",
(event) => {

const button =
event.target.closest(
"[data-toggle-password]"
);


if (!button) {

return;

}


const inputId =
button.dataset.togglePassword;


const input =
$(inputId);


if (!input) {

return;

}


if (
input.type ===
"password"
) {

input.type =
"text";

} else {

input.type =
"password";

}

}
);


// ============================================================
// PASSWORD STRENGTH UI
// ============================================================

document.addEventListener(
"input",
(event) => {

if (
event.target.id !==
"register-password"
) {

return;

}


const password =
event.target.value;


const strength =
getPasswordStrength(
password
);


const bar =
$("password-strength-bar");


const text =
$("password-strength-text");


if (bar) {

const percentage =
Math.min(
100,
strength.score * 16.67
);


bar.style.width =
`${percentage}%`;

}


if (text) {

if (!password) {

text.textContent =
"Use 8+ characters with uppercase, lowercase, number and symbol.";

} else {

text.textContent =
strength.text;

}

}

}
);


// ============================================================
// EMAIL FIELD VALIDATION
// ============================================================

function attachEmailValidation(
inputId,
errorId
) {

const input =
$(inputId);


const error =
$(errorId);


if (!input) {

return;

}


input.addEventListener(
"input",
() => {

const value =
input.value.trim();


if (!value) {

if (error) {

error.textContent =
"";

}

input.setCustomValidity(
""
);

return;

}


if (
!isValidEmail(
value
)
) {

input.setCustomValidity(
"Please enter a valid Gmail or approved email address."
);


if (error) {

error.textContent =
"Please enter a valid Gmail or approved email address.";

}

} else {

input.setCustomValidity(
""
);


if (error) {

error.textContent =
"";

}

}

}
);

}


// Attach to all relevant email inputs.

attachEmailValidation(
"login-email",
"login-email-error"
);


attachEmailValidation(
"register-email",
"register-email-error"
);


attachEmailValidation(
"forgot-email",
"forgot-email-error"
);
function setupEmailValidation(
inputId,
errorId
) {

const input =
$(inputId);

const error =
$(errorId);

if (!input) {
return;
}

input.addEventListener(
"input",
() => {

const value =
input.value
.trim()
.toLowerCase();

if (!value) {

if (error) {
error.textContent = "";
}

input.setCustomValidity("");

return;
}

const valid =
isValidEmail(value);

if (!valid) {

const errorText =
getEmailError(value);

if (error) {
error.textContent =
errorText;
}

input.setCustomValidity(
errorText
);

} else {

if (error) {
error.textContent = "";
}

input.setCustomValidity("");

}

}
);

}

setupEmailValidation(
"login-email",
"login-email-error"
);

setupEmailValidation(
"register-email",
"register-email-error"
);

setupEmailValidation(
"forgot-email",
"forgot-email-error"
);


// ============================================================
// AUTH SECTIONS
// ============================================================

const loginSection =
$("login-section");

const registerSection =
$("register-section");

const forgotSection =
$("forgot-section");


function show(section) {

[
loginSection,
registerSection,
forgotSection,
].forEach(
(item) => {

item?.classList.add(
"hidden"
);

}
);


section?.classList.remove(
"hidden"
);

}


// ============================================================
// NAVIGATION
// ============================================================

$("show-register")
?.addEventListener(
"click",
() =>
show(
registerSection
)
);


$("show-login")
?.addEventListener(
"click",
() =>
show(
loginSection
)
);


$("forgot-password-button")
?.addEventListener(
"click",
() =>
show(
forgotSection
)
);


$("back-login-from-forgot")
?.addEventListener(
"click",
() =>
show(
loginSection
)
);


// ============================================================
// LOGIN
// ============================================================

$("login-form")
?.addEventListener(
"submit",
async (event) => {

event.preventDefault();


const email =
$("login-email")
?.value
.trim()
.toLowerCase();


const password =
$("login-password")
?.value ||
"";


const msg =
$("login-message");


const emailError =
$("login-email-error");


if (emailError) {

emailError.textContent =
"";

}


// ------------------------------------------------
// EMAIL VALIDATION
// ------------------------------------------------

if (
!isValidEmail(
email
)
) {

if (emailError) {

emailError.textContent =
getEmailError(
email
);

}

return;

}


// ------------------------------------------------
// PASSWORD VALIDATION
// ------------------------------------------------

if (!password) {

message(
msg,
"Please enter your password."
);

return;

}


const button =
event.submitter;


setButtonLoading(
button,
true,
"Signing in..."
);


try {

const response =
await fetch(
`${API_URL}/api/auth/login`,
{
method:
"POST",

headers: {
"Content-Type":
"application/json",
},

body:
JSON.stringify({
email,
password,
}),

}
);


const data =
await readJSON(
response
);


// ------------------------------------------------
// LOGIN ERROR
// ------------------------------------------------

if (!response.ok) {

message(
msg,
data.detail ||
"Login failed."
);

return;

}


// ------------------------------------------------
// SAVE TOKEN
// ------------------------------------------------

if (
data.access_token
) {

localStorage.setItem(
"access_token",
data.access_token
);

}


// ------------------------------------------------
// SUCCESS
// ------------------------------------------------

message(
msg,
"Login successful. Opening CORTEX...",
true
);


setTimeout(
() => {

window.location.href =
"dashboard.html";

},
500
);


} catch (error) {

console.error(
"CORTEX login error:",
error
);


message(
msg,
"Unable to connect to the CORTEX server."
);


} finally {

setButtonLoading(
button,
false
);

}

}
);


// ============================================================
// REGISTER
// ============================================================

$("register-form")
?.addEventListener(
"submit",
async (event) => {

event.preventDefault();


const name =
$("register-name")
?.value
.trim();


const email =
$("register-email")
?.value
.trim()
.toLowerCase();


const password =
$("register-password")
?.value ||
"";


const ageValue =
$("register-age")
?.value;


const hoursValue =
$("register-hours")
?.value;


const goal =
$("register-goal")
?.value ||
"";


const msg =
$("register-message");


const emailError =
$("register-email-error");


if (msg) {

msg.textContent =
"";

msg.classList.remove(
"error",
"success"
);

}


if (emailError) {

emailError.textContent =
"";

}


// ------------------------------------------------
// NAME VALIDATION
// ------------------------------------------------

if (
!name ||
name.length < 2
) {

message(
msg,
"Please enter your valid full name."
);

return;

}


// ------------------------------------------------
// EMAIL VALIDATION
// ------------------------------------------------

if (
!isValidEmail(
email
)
) {

const errorText =
getEmailError(
email
);


if (emailError) {

emailError.textContent =
errorText;

}


message(
msg,
errorText
);


return;

}


// ------------------------------------------------
// PASSWORD VALIDATION
// ------------------------------------------------

if (
!isValidPassword(
password
)
) {

message(
msg,
"Password must contain at least 8 characters, including uppercase, lowercase, number and special character."
);


return;

}


// ------------------------------------------------
// AGE VALIDATION
// ------------------------------------------------

const age =
Number(
ageValue
);


if (
!Number.isFinite(age) ||
age < 13 ||
age > 120
) {

message(
msg,
"Please enter a valid age between 13 and 120."
);


return;

}


// ------------------------------------------------
// HOURS VALIDATION
// ------------------------------------------------

let hours =
Number(
hoursValue
);


if (
hoursValue === "" ||
hoursValue === null ||
hoursValue === undefined
) {

hours = 0;

}


if (
!Number.isFinite(hours) ||
hours < 0 ||
hours > 24
) {

message(
msg,
"Please enter valid hours between 0 and 24."
);


return;

}


// ------------------------------------------------
// GOAL VALIDATION
// ------------------------------------------------

if (!goal) {

message(
msg,
"Please select your primary focus."
);


return;

}


const button =
event.submitter;


setButtonLoading(
button,
true,
"Creating account..."
);


try {

// ------------------------------------------------
// REGISTER REQUEST
// ------------------------------------------------

const response =
await fetch(
`${API_URL}/api/auth/register`,
{
method:
"POST",

headers: {
"Content-Type":
"application/json",
},

body:
JSON.stringify({

name:
name,

email:
email,

password:
password,

age:
age,

hours_per_day:
hours,

goal:
goal,

}),

}
);


const data =
await readJSON(
response
);


// ------------------------------------------------
// REGISTRATION ERROR
// ------------------------------------------------

if (!response.ok) {

let errorText =
data?.detail ||
data?.message ||
"Registration failed.";


if (
Array.isArray(
errorText
)
) {

errorText =
errorText
.map(
(item) =>
item?.msg ||
"Invalid input."
)
.join(
" "
);

}


message(
msg,
errorText
);


return;

}


// ------------------------------------------------
// SUCCESS
// ------------------------------------------------

message(
msg,
"Account created successfully. You can now sign in.",
true
);





} catch (error) {

console.error(
"CORTEX registration error:",
error
);


message(
msg,
"Unable to connect to the CORTEX server."
);


} finally {

setButtonLoading(
button,
false
);

}

}
);
