<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
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
        <NuxtLink to="/competitions">{{ t("nav.competitions") }}</NuxtLink>
        <NuxtLink to="/sources">{{ t("footer.status") }}</NuxtLink>
      </div>

      <div>
        <h5>{{ t("footer.community") }}</h5>
        <a :href="config.public.channelUrl as string" target="_blank" rel="noopener">📢 {{ t("footer.channel") }}</a>
        <a :href="config.public.whatsappUrl as string" target="_blank" rel="noopener">🟢 {{ t("footer.whatsapp") }}</a>
        <a :href="config.public.discussionUrl as string" target="_blank" rel="noopener">💬 {{ t("footer.discussion") }}</a>
        <a :href="config.public.telegramBotUrl as string" target="_blank" rel="noopener">🤖 {{ t("nav.openBot") }}</a>
      </div>
    </div>
    <div class="footer-bottom">
      © {{ year }} Raqib · رقيب · {{ t("footer.rights") }} ·
      🛠 {{ t("footer.madeBy") }}
      <a :href="config.public.ownerUrl as string" target="_blank" rel="noopener">Oussama Zbair</a>
    </div>
  </footer>
</template>
