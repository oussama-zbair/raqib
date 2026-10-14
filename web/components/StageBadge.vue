<script setup lang="ts">
const props = defineProps<{ stage: string }>();
const labels: Record<string, string> = {
  AVIS: "Avis",
  CONVOQUES: "Convoqués",
  RESULTATS: "Résultats",
};
const cls = props.stage.toLowerCase();
</script>

<template>
  <span class="badge" :class="cls">{{ labels[stage] ?? stage }}</span>
</template>
