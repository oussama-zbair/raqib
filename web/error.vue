<script setup lang="ts">
import type { NuxtError } from "#app";

defineProps<{ error: NuxtError }>();
const { t } = useI18n();
</script>

<template>
  <div class="error-page">
    <div>
      <div class="logo" style="width: 64px; height: 64px; margin: 0 auto 20px">
        <img src="/logo.svg" alt="Raqib" style="width: 64px; height: 64px" />
      </div>
      <div class="code">{{ error?.statusCode || 404 }}</div>
      <h1 style="margin: 12px 0 8px">{{ t("error.title") }}</h1>
      <p style="color: var(--muted); margin: 0 0 24px">{{ t("error.text") }}</p>
      <a href="/" class="btn btn-primary">{{ t("error.back") }}</a>
    </div>
  </div>
</template>
