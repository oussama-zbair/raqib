<script setup lang="ts">
// Small on-brand line-icon set used by problem cards and flow steps.
defineProps<{ name: string }>();
</script>

<template>
  <svg class="ic" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <template v-if="name === 'ai'">
      <path d="M19 8a5 5 0 0 0-5 5v10a5 5 0 0 0 5 5" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" />
      <path d="M29 8a5 5 0 0 1 5 5v10a5 5 0 0 1-5 5" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" />
      <path d="M19 16h10M19 24h10M24 8v24" stroke="#12987C" stroke-width="2" stroke-linecap="round" opacity="0.6" />
      <path d="M36 12l1.2 3 3 1.2-3 1.2-1.2 3-1.2-3-3-1.2 3-1.2Z" fill="#F4B740" />
    </template>
    <template v-else-if="name === 'calendar'">
      <rect x="9" y="11" width="30" height="28" rx="4" stroke="#F4B740" stroke-width="2.4" />
      <path d="M9 19h30M17 8v6M31 8v6" stroke="#F4B740" stroke-width="2.4" stroke-linecap="round" />
      <path d="M20 28l8 8M28 28l-8 8" stroke="#D64545" stroke-width="2.6" stroke-linecap="round" />
    </template>
    <template v-else-if="name === 'scatter'">
      <circle cx="12" cy="12" r="4" stroke="#F4B740" stroke-width="2.4" />
      <circle cx="36" cy="16" r="4" stroke="#3aa0ff" stroke-width="2.4" />
      <circle cx="16" cy="36" r="4" stroke="#D64545" stroke-width="2.4" />
      <circle cx="34" cy="34" r="4" stroke="#34d399" stroke-width="2.4" />
      <path d="M16 14l16 3M14 16l4 16M20 36l12-3" stroke="#3a4a68" stroke-width="1.8" stroke-dasharray="2 3" />
    </template>
    <template v-else-if="name === 'mask'">
      <path d="M8 18c8-8 24-8 32 0-8 10-24 10-32 0Z" stroke="#F4B740" stroke-width="2.4" />
      <circle cx="24" cy="18" r="4" fill="#D64545" />
      <path d="M12 30l24 8M14 38l20-10" stroke="#3a4a68" stroke-width="1.8" />
    </template>
    <template v-else-if="name === 'pdf'">
      <rect x="12" y="8" width="24" height="32" rx="3" stroke="#12987C" stroke-width="2.4" />
      <path d="M18 20h12M18 26h12M18 32h8" stroke="#3a4a68" stroke-width="2" stroke-linecap="round" />
      <circle cx="34" cy="36" r="8" fill="#0B1220" stroke="#F4B740" stroke-width="2.4" />
      <path d="M31 36l2 2 4-4" stroke="#F4B740" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" />
    </template>
    <template v-else-if="name === 'clock'">
      <circle cx="24" cy="24" r="16" stroke="#D64545" stroke-width="2.4" />
      <path d="M24 15v9l6 4" stroke="#F4B740" stroke-width="2.4" stroke-linecap="round" />
    </template>
    <template v-else-if="name === 'profile'">
      <circle cx="24" cy="17" r="7" stroke="#12987C" stroke-width="2.4" />
      <path d="M12 38c2-7 8-10 12-10s10 3 12 10" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" />
    </template>
    <template v-else-if="name === 'ingest'">
      <path d="M24 8v18m0 0l-6-6m6 6l6-6" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
      <path d="M10 30v8h28v-8" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" />
    </template>
    <template v-else-if="name === 'match'">
      <path d="M10 24h10l4-8 6 16 4-8h4" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    </template>
    <template v-else-if="name === 'digest'">
      <rect x="10" y="12" width="28" height="24" rx="3" stroke="#12987C" stroke-width="2.4" />
      <path d="M10 16l14 9 14-9" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    </template>
    <template v-else-if="name === 'monitor'">
      <path d="M8 24c6-8 26-8 32 0-6 8-26 8-32 0Z" stroke="#12987C" stroke-width="2.4" />
      <circle cx="24" cy="24" r="5" fill="#F4B740" />
    </template>
    <template v-else-if="name === 'shield'">
      <path d="M24 8l14 5v9c0 9-6 15-14 18-8-3-14-9-14-18v-9l14-5Z" stroke="#12987C" stroke-width="2.4" stroke-linejoin="round" />
      <path d="M18 24l4 4 8-8" stroke="#F4B740" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" />
    </template>
    <template v-else-if="name === 'free'">
      <circle cx="24" cy="24" r="16" stroke="#12987C" stroke-width="2.4" />
      <path d="M20 18h6a4 4 0 0 1 0 8h-6m0-8v14" stroke="#F4B740" stroke-width="2.4" stroke-linecap="round" />
      <path d="M14 28h20" stroke="#F4B740" stroke-width="2.4" stroke-linecap="round" />
    </template>
    <template v-else-if="name === 'users'">
      <circle cx="18" cy="18" r="6" stroke="#12987C" stroke-width="2.4" />
      <circle cx="33" cy="20" r="5" stroke="#F4B740" stroke-width="2.2" />
      <path d="M8 36c1.5-6 6-8 10-8s8.5 2 10 8" stroke="#12987C" stroke-width="2.4" stroke-linecap="round" />
    </template>
  </svg>
</template>
