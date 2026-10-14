<script setup lang="ts">
// Simplified, recognizable brand marks for the sources we monitor.
// These are original stylized SVGs (not official assets) used to represent each source.
defineProps<{ name: string }>();
</script>

<template>
  <svg class="brand-logo" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <!-- Telegram -->
    <template v-if="name === 'telegram'">
      <circle cx="24" cy="24" r="22" fill="#229ED9" />
      <path d="M11 23.5l24-9.2c1.1-.4 2 .3 1.7 1.9l-3.4 16.2c-.3 1.3-1.1 1.6-2.2 1L25 29l-2.9 2.8c-.3.3-.6.6-1.2.6l.4-6 11-9.9c.5-.4-.1-.6-.7-.2L18 22.6l-5.8-1.8c-1.3-.4-1.3-1.3.2-1.9Z" fill="#fff" />
    </template>

    <!-- emploi-public.ma (state service) -->
    <template v-else-if="name === 'emploi'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#0E7C66" />
      <path d="M16 30V19l8-5 8 5v11" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" />
      <path d="M20 30v-6h8v6" stroke="#F4B740" stroke-width="2.4" stroke-linejoin="round" />
      <path d="M13 30h22" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
    </template>

    <!-- Ministry of Finance -->
    <template v-else-if="name === 'finances'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#1f6feb" />
      <path d="M14 20l10-7 10 7" stroke="#fff" stroke-width="2.4" stroke-linejoin="round" />
      <path d="M16 20v10M24 20v10M32 20v10M13 32h22" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
    </template>

    <!-- Ministry of Justice -->
    <template v-else-if="name === 'justice'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#6b4bd6" />
      <path d="M24 12v22M15 34h18" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
      <path d="M14 16h20M14 16l-3 7h6l-3-7ZM34 16l-3 7h6l-3-7Z" stroke="#F4B740" stroke-width="2.2" stroke-linejoin="round" />
    </template>

    <!-- Ministry of Interior -->
    <template v-else-if="name === 'interieur'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#c1272d" />
      <path d="M24 12l12 4v7c0 8-6 12-12 14-6-2-12-6-12-14v-7l12-4Z" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" />
      <path d="M24 5.1l.98 2.5 2.67.02-2.16 1.58.82 2.55L24 10.2l-2.31 1.55.82-2.55L20.35 7.6l2.67-.02Z" fill="#F4B740" transform="translate(0 12) scale(1)" />
    </template>

    <!-- OCP -->
    <template v-else-if="name === 'ocp'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#00953b" />
      <text x="24" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="14" font-weight="800" fill="#fff">OCP</text>
    </template>

    <!-- CDG -->
    <template v-else-if="name === 'cdg'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#003b71" />
      <text x="24" y="30" text-anchor="middle" font-family="Inter, sans-serif" font-size="13" font-weight="800" fill="#fff">CDG</text>
    </template>

    <!-- ONCF (rail) -->
    <template v-else-if="name === 'oncf'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#e2001a" />
      <rect x="15" y="13" width="18" height="16" rx="4" stroke="#fff" stroke-width="2.2" />
      <path d="M15 22h18" stroke="#fff" stroke-width="2.2" />
      <circle cx="19" cy="33" r="2" fill="#fff" /><circle cx="29" cy="33" r="2" fill="#fff" />
      <path d="M17 35l-2 3M31 35l2 3" stroke="#fff" stroke-width="2" stroke-linecap="round" />
    </template>

    <!-- Barid Al-Maghrib (post) -->
    <template v-else-if="name === 'barid'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#f6c400" />
      <rect x="12" y="16" width="24" height="16" rx="3" stroke="#003b71" stroke-width="2.4" />
      <path d="M12 18l12 8 12-8" stroke="#003b71" stroke-width="2.4" stroke-linejoin="round" />
    </template>

    <!-- ANP (ports) -->
    <template v-else-if="name === 'anp'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#0a6ca8" />
      <path d="M24 12v14M18 17h12M24 34c-5 0-9-4-9-8h18c0 4-4 8-9 8Z" stroke="#fff" stroke-width="2.2" stroke-linejoin="round" stroke-linecap="round" />
      <circle cx="24" cy="12" r="2.4" stroke="#fff" stroke-width="2.2" />
    </template>

    <!-- Alwadifa / aggregators (generic web feed) -->
    <template v-else-if="name === 'aggregator'">
      <rect x="4" y="4" width="40" height="40" rx="10" fill="#0E7C66" />
      <circle cx="16" cy="32" r="3" fill="#fff" />
      <path d="M14 20a14 14 0 0 1 14 14M14 14a20 20 0 0 1 20 20" stroke="#F4B740" stroke-width="2.6" stroke-linecap="round" fill="none" />
    </template>
  </svg>
</template>

<style scoped>
.brand-logo { width: 40px; height: 40px; display: block; }
</style>
