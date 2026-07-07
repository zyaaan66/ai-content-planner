/**
 * main.js — shared client-side behavior:
 * theme toggle, sidebar mobile drawer, toast auto-dismiss, AI generation UX.
 */

document.addEventListener("DOMContentLoaded", () => {
  initThemeToggle();
  initMobileSidebar();
  initToastDismiss();
  initSearchDebounce();
});

function initThemeToggle() {
  const toggle = document.getElementById("theme-toggle");
  if (!toggle) return;

  toggle.addEventListener("click", async () => {
    document.documentElement.classList.toggle("light");
    try {
      await fetch("/api/toggle-theme", { method: "POST" });
    } catch (err) {
      console.error("Theme toggle failed:", err);
    }
  });
}

function initMobileSidebar() {
  const openBtn = document.getElementById("sidebar-open");
  const closeBtn = document.getElementById("sidebar-close");
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebar-overlay");

  if (!sidebar) return;

  const open = () => {
    sidebar.classList.remove("-translate-x-full");
    overlay?.classList.remove("hidden");
  };
  const close = () => {
    sidebar.classList.add("-translate-x-full");
    overlay?.classList.add("hidden");
  };

  openBtn?.addEventListener("click", open);
  closeBtn?.addEventListener("click", close);
  overlay?.addEventListener("click", close);
}

function initToastDismiss() {
  document.querySelectorAll(".toast").forEach((toast) => {
    setTimeout(() => toast.remove(), 4500);
  });
}

function initSearchDebounce() {
  const input = document.getElementById("history-search");
  if (!input) return;
  let timer;
  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => input.form.requestSubmit(), 450);
  });
}

/**
 * Called from planner.html to regenerate content inline via /api/generate
 * without a full page reload. Shows a skeleton loader while waiting.
 */
async function regenerateContent(contentType, promptInput, outputElId, btnEl) {
  const outputEl = document.getElementById(outputElId);
  if (!outputEl) return;

  const originalBtnText = btnEl ? btnEl.innerHTML : "";
  if (btnEl) {
    btnEl.disabled = true;
    btnEl.innerHTML = `<span class="inline-block h-4 w-4 border-2 border-white/40 border-t-white rounded-full animate-spin"></span>`;
  }
  outputEl.innerHTML = `
    <div class="space-y-2">
      <div class="skeleton h-4 w-full"></div>
      <div class="skeleton h-4 w-5/6"></div>
      <div class="skeleton h-4 w-3/4"></div>
    </div>`;

  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content_type: contentType, prompt_input: promptInput }),
    });
    const data = await res.json();

    if (!res.ok) {
      outputEl.innerHTML = `<p class="text-[var(--danger)] text-sm">${escapeHtml(data.error || "Generation failed.")}</p>`;
      return;
    }
    outputEl.innerText = data.result;
  } catch (err) {
    outputEl.innerHTML = `<p class="text-[var(--danger)] text-sm">Network error. Please try again.</p>`;
  } finally {
    if (btnEl) {
      btnEl.disabled = false;
      btnEl.innerHTML = originalBtnText;
    }
  }
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
