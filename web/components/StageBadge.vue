<script setup lang="ts">
const props = defineProps<{ stage: string }>();
const { t } = useI18n();
const cls = computed(() => props.stage.toLowerCase());
const icon: Record<string, string> = { AVIS: "🟢", CONVOQUES: "📋", CONVOQUES_ORAL: "🎤", RESULTATS: "🏆" };
</script>

<template>
  <span class="badge stage-badge" :class="cls">{{ icon[stage] ?? "" }} {{ t(`stage.${stage}`) }}</span>
</template>
