const root = document.documentElement;
const themeToggle = document.getElementById("themeToggle");
const togglePassword = document.getElementById("togglePassword");
const password = document.getElementById("password");
const form = document.getElementById("loginForm");
const email = document.getElementById("email");
const role = document.getElementById("role");
const submitBtn = document.getElementById("submitBtn");
const formMessage = document.getElementById("formMessage");

let theme = "light";

function updateThemeIcon() {
  themeToggle.innerHTML =
    theme === "dark"
      ? `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="5"></circle><path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42"></path></svg>`
      : `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
}

function applyTheme() {
  root.setAttribute("data-theme", theme);
  updateThemeIcon();
}

applyTheme();

themeToggle.addEventListener("click", () => {
  theme = theme === "dark" ? "light" : "dark";
  applyTheme();
});

togglePassword.addEventListener("click", () => {
  const isHidden = password.type === "password";
  password.type = isHidden ? "text" : "password";
  togglePassword.textContent = isHidden ? "Hide" : "Show";
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.textContent = "";
  formMessage.className = "message";

  const emailValue = email.value.trim();
  const roleValue = role.value.trim();
  const passwordValue = password.value.trim();

  if (!emailValue || !roleValue || !passwordValue) {
    formMessage.textContent = "Please complete all fields before signing in.";
    return;
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(emailValue)) {
    formMessage.textContent = "Please enter a valid work email address.";
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = "Signing in...";

  try {
    const response = await fetch("/api/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: emailValue,
        password: passwordValue,
        role: roleValue,
      }),
    });

    const data = await response.json();

    if (data.success) {
      const roleLabel = role.options[role.selectedIndex].text.toLowerCase();
      formMessage.textContent = `Login successful. Redirecting as ${roleLabel}...`;
      formMessage.classList.add("success");
      setTimeout(() => {
        window.location.href = "/";
      }, 800);
      return;
    } else {
      formMessage.textContent = data.error || "Login failed. Please check your credentials.";
    }
  } catch (err) {
    formMessage.textContent = "Unable to reach the server. Please try again.";
  }

  submitBtn.disabled = false;
  submitBtn.textContent = "Sign in";
});