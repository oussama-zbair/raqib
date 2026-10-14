<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
const botUrl = config.public.telegramBotUrl as string;
const githubUrl = config.public.githubUrl as string;
const year = new Date().getFullYear();
</script>

<template>
  <footer class="site-footer">
    <div class="footer-inner">
      <div>
        <div class="brand" style="margin-bottom: 12px">
          <span class="logo"><img src="/logo-mark.svg" alt="Raqib" /></span>
          <span>Raqib <span class="ar">رقيب</span></span>
        </div>
        <p style="color: var(--muted); margin: 0; max-width: 320px; line-height: 1.6">
          {{ t("footer.tagline") }}
        </p>
        <p class="footer-privacy">🔒 {{ t("footer.privacyNote") }}</p>
      </div>

      <div>
        <h5>{{ t("footer.product") }}</h5>
        <a :href="botUrl" target="_blank" rel="noopener">✈️ {{ t("nav.openBot") }}</a>
        <NuxtLink to="/competitions">{{ t("nav.competitions") }}</NuxtLink>
        <NuxtLink to="/sources">{{ t("footer.status") }}</NuxtLink>
      </div>

      <div>
        <h5>{{ t("footer.resources") }}</h5>
        <a :href="githubUrl" target="_blank" rel="noopener">{{ t("footer.github") }}</a>
        <NuxtLink to="/sources">{{ t("footer.status") }}</NuxtLink>
      </div>
    </div>
    <div class="footer-bottom">© {{ year }} Raqib · رقيب — {{ t("footer.rights") }}</div>
  </footer>
</template>
