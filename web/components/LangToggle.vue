<script setup lang="ts">
const { locale, setLocale } = useI18n();
</script>

<template>
  <div class="lang-toggle" role="group" aria-label="Language">
    <button
      class="lang-btn"
      :class="{ active: locale === 'fr' }"
      :aria-pressed="locale === 'fr'"
      @click="setLocale('fr')"
    >
      <FlagFR />
      <span class="code">FR</span>
    </button>
    <button
      class="lang-btn"
      :class="{ active: locale === 'ar' }"
      :aria-pressed="locale === 'ar'"
      @click="setLocale('ar')"
    >
      <FlagMA />
      <span class="code">AR</span>
    </button>
  </div>
</template>

<style scoped>
.lang-toggle {
  display: inline-flex;
  gap: 2px;
  padding: 3px;
  border: 1px solid var(--border);
  border-radius: 999px;
  background: var(--surface);
}
.lang-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 5px 11px;
  border: 0;
  background: transparent;
  color: var(--muted);
  border-radius: 999px;
  cursor: pointer;
  font-weight: 700;
  font-size: 13px;
  transition: all 0.15s ease;
}
.lang-btn:hover { color: var(--text); }
.lang-btn.active {
  background: linear-gradient(135deg, var(--brand), var(--brand-2));
  color: #fff;
}
.lang-btn :deep(.flag-svg) {
  border-radius: 3px;
  display: block;
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.15);
}
</style>
