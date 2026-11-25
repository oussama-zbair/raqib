<script setup lang="ts">
// The portal's four stages; the ones already published for this concours are filled.
const props = defineProps<{ done: string[] }>();
const { t } = useI18n();
const reached = computed(() => STAGES.map((s) => props.done.includes(s)));
</script>

<template>
  <ol class="stl">
    <li v-for="(s, i) in STAGES" :key="s" class="stl-step" :class="{ on: reached[i] }">
      <span class="stl-dot"></span>
      <span class="stl-label">{{ t(`stage.${s}`) }}</span>
    </li>
  </ol>
</template>
