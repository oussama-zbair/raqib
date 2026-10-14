<script setup lang="ts">
const { t, locale, locales } = useI18n();
const config = useRuntimeConfig();
const botUrl = config.public.telegramBotUrl as string;

// Theme cookie, read on the server so the correct theme is set before paint (no flash).
const theme = useCookie<"dark" | "light">("raqib_theme", { default: () => "dark" });

// Set <html lang>, dir (RTL for Arabic), and data-theme.
const currentDir = computed(() => {
  const l = (locales.value as any[]).find((x) => x.code === locale.value);
  return l?.dir ?? "ltr";
});
useHead({
  htmlAttrs: {
    lang: computed(() => locale.value),
    dir: currentDir,
    "data-theme": computed(() => theme.value),
  },
});
</script>

<template>
  <div>
    <header class="topbar">
      <NuxtLink to="/" class="brand" style="text-decoration: none; color: inherit">
        <span class="logo"><img src="/logo-mark.svg" alt="Raqib" /></span>
        <span>Raqib <span class="ar">رقيب</span></span>
      </NuxtLink>
      <nav class="nav">
        <NuxtLink to="/">{{ t("nav.home") }}</NuxtLink>
        <NuxtLink to="/competitions">{{ t("nav.competitions") }}</NuxtLink>
        <NuxtLink to="/sources">{{ t("nav.sources") }}</NuxtLink>
      </nav>
      <div style="display: flex; align-items: center; gap: 10px">
        <LangToggle />
        <ThemeToggle />
        <a :href="botUrl" target="_blank" rel="noopener" class="btn btn-primary" style="padding: 8px 16px; font-size: 14px">
          ✈️ {{ t("nav.openBot") }}
        </a>
      </div>
    </header>
    <main>
      <NuxtPage />
    </main>
  </div>
</template>
