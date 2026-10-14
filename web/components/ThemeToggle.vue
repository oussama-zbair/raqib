<script setup lang="ts">
// Dark/light theme toggle. Persisted in a cookie so it survives reloads and SSR.
const theme = useCookie<"dark" | "light">("raqib_theme", {
  default: () => "dark",
  maxAge: 60 * 60 * 24 * 365,
  sameSite: "lax",
});

function apply(t: "dark" | "light") {
  if (import.meta.client) {
    document.documentElement.setAttribute("data-theme", t);
  }
}

onMounted(() => apply(theme.value));

function toggle() {
  theme.value = theme.value === "dark" ? "light" : "dark";
  apply(theme.value);
}
</script>

<template>
  <button
    class="theme-toggle"
    :aria-label="theme === 'dark' ? 'Passer en mode clair' : 'Passer en mode sombre'"
    :title="theme === 'dark' ? 'Mode clair' : 'Mode sombre'"
    @click="toggle"
  >
    <!-- Sun (shown in dark mode = click to go light) -->
    <svg v-if="theme === 'dark'" viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <circle cx="12" cy="12" r="4.5" stroke="currentColor" stroke-width="2" />
      <path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"
        stroke="currentColor" stroke-width="2" stroke-linecap="round" />
    </svg>
    <!-- Moon (shown in light mode = click to go dark) -->
    <svg v-else viewBox="0 0 24 24" width="18" height="18" fill="none" aria-hidden="true">
      <path d="M20 14.5A8 8 0 1 1 9.5 4a6.5 6.5 0 0 0 10.5 10.5Z"
        stroke="currentColor" stroke-width="2" stroke-linejoin="round" />
    </svg>
  </button>
</template>

<style scoped>
.theme-toggle {
  width: 38px; height: 38px; border-radius: 10px;
  display: grid; place-items: center;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  cursor: pointer;
  transition: all 0.15s ease;
}
.theme-toggle:hover { background: var(--surface-2); color: var(--brand); transform: translateY(-1px); }
</style>
