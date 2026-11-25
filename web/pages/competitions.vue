<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
const { data, pending, error } = useRaqibData();
const { date, ago } = useFormat();

const tab = ref<"open" | "updates">("open");
const q = ref("");
const field = ref("");
const city = ref("");

function norm(s: string | null | undefined): string {
  return (s ?? "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f\u064b-\u065f\u0670\u0640]/g, "")
    .replace(/[أإآ]/g, "ا");
}

const open = computed(() =>
  (data.value?.concours ?? []).filter((c) => (daysUntil(c.deadline) ?? 0) >= 0),
);
const fields = computed(() => [...new Set(open.value.flatMap((c) => c.tags))].sort());
const cities = computed(() =>
  [...new Set(open.value.map((c) => c.city).filter(Boolean) as string[])].sort(),
);

const shownOpen = computed(() => {
  const words = norm(q.value).split(/\s+/).filter(Boolean);
  return open.value
    .filter((c) => !field.value || c.tags.includes(field.value))
    .filter((c) => !city.value || c.city === city.value)
    .filter((c) => {
      const hay = norm([c.administration, c.grade, c.specialty, c.city, c.code].join(" "));
      return words.every((w) => hay.includes(w));
    })
    .sort((a, b) => (a.deadline ?? "9999").localeCompare(b.deadline ?? "9999"));
});

const shownUpdates = computed(() => {
  const words = norm(q.value).split(/\s+/).filter(Boolean);
  return (data.value?.updates ?? []).filter((u) => {
    const hay = norm([u.administration, u.grade, u.city].join(" "));
    return words.every((w) => hay.includes(w));
  });
});

function deadlineLabel(iso: string | null): string {
  const d = daysUntil(iso);
  if (d === null) return "";
  if (d < 0) return t("competitions.closed");
  if (d === 0) return t("competitions.today");
  return t("competitions.daysLeft", { n: d });
}
function urgent(iso: string | null): boolean {
  const d = daysUntil(iso);
  return d !== null && d >= 0 && d <= 3;
}
function onImgError(e: Event) {
  (e.target as HTMLImageElement).src = "/morocco.png";
}
</script>

<template>
  <div class="container" style="padding-top: 40px">
    <h1 class="page-title">{{ t("competitions.title") }}</h1>
    <p class="page-sub">{{ t("competitions.subtitle") }}</p>

    <div class="cx-toolbar">
      <div class="cx-tabs" role="tablist">
        <button :class="{ on: tab === 'open' }" @click="tab = 'open'">
          {{ t("competitions.tabOpen") }}
          <span v-if="data" class="cx-count">{{ open.length }}</span>
        </button>
        <button :class="{ on: tab === 'updates' }" @click="tab = 'updates'">
          {{ t("competitions.tabUpdates") }}
          <span v-if="data" class="cx-count">{{ data.updates.length }}</span>
        </button>
      </div>
      <a :href="config.public.channelUrl as string" target="_blank" rel="noopener" class="btn btn-ghost cx-follow">
        ✈️ {{ t("competitions.follow") }}
      </a>
    </div>

    <div class="cx-filters">
      <input v-model="q" type="search" class="cx-input" :placeholder="t('competitions.search')" />
      <template v-if="tab === 'open'">
        <select v-model="field" class="cx-select">
          <option value="">{{ t("competitions.allFields") }}</option>
          <option v-for="f in fields" :key="f" :value="f">#{{ f }}</option>
        </select>
        <select v-model="city" class="cx-select">
          <option value="">{{ t("competitions.allCities") }}</option>
          <option v-for="c in cities" :key="c" :value="c">{{ c }}</option>
        </select>
      </template>
    </div>

    <div v-if="pending && !data" class="empty">{{ t("competitions.loading") }}</div>
    <div v-else-if="error" class="empty">{{ t("competitions.error") }}</div>

    <template v-else-if="data">
      <p class="cx-meta">
        {{ t("competitions.count", tab === "open" ? shownOpen.length : shownUpdates.length) }}
        · {{ t("competitions.updatedAt", { when: ago(data.updated_at) }) }}
      </p>

      <!-- OPEN CONCOURS -->
      <div v-if="tab === 'open'" class="cx-grid">
        <article v-for="c in shownOpen" :key="c.id" class="cx-card">
          <header class="cx-head">
            <img :src="c.logo || '/morocco.png'" alt="" class="cx-logo" loading="lazy" @error="onImgError" />
            <div class="cx-head-text">
              <h3 class="cx-admin">{{ c.administration }}</h3>
              <p class="cx-grade">{{ c.grade }}</p>
            </div>
          </header>
          <p v-if="c.specialty" class="cx-spec">🎓 {{ c.specialty.split(" / ").slice(0, 4).join(" · ") }}</p>
          <div class="cx-facts">
            <span v-if="c.posts">👥 {{ t("competitions.posts", c.posts) }}</span>
            <span v-if="c.city">📍 {{ c.city }}</span>
          </div>
          <div class="cx-dates">
            <div>
              <span class="k">⏳ {{ t("competitions.deadline") }}</span>
              <span class="v">{{ date(c.deadline) }}</span>
              <span class="cx-left" :class="{ urgent: urgent(c.deadline) }">{{ deadlineLabel(c.deadline) }}</span>
            </div>
            <div>
              <span class="k">📝 {{ t("competitions.exam") }}</span>
              <span class="v">{{ c.exam_date ? date(c.exam_date) : t("competitions.examTbd") }}</span>
            </div>
          </div>
          <StageTimeline :done="c.stages" />
          <footer class="cx-foot">
            <span class="cx-tags"><span v-for="tg in c.tags" :key="tg">#{{ tg }}</span></span>
            <a v-if="c.url" :href="c.url" target="_blank" rel="noopener" class="btn btn-primary cx-btn">
              {{ t("competitions.official") }}
            </a>
          </footer>
        </article>
      </div>

      <!-- CONVOCATIONS AND RESULTS -->
      <div v-else class="cx-grid">
        <article v-for="u in shownUpdates" :key="u.id + u.stage" class="cx-card">
          <header class="cx-head">
            <img :src="u.logo || '/morocco.png'" alt="" class="cx-logo" loading="lazy" @error="onImgError" />
            <div class="cx-head-text">
              <StageBadge :stage="u.stage" />
              <h3 class="cx-admin" style="margin-top: 6px">{{ u.administration }}</h3>
              <p class="cx-grade">{{ u.grade }}</p>
            </div>
          </header>
          <div class="cx-facts">
            <span v-if="u.exam_date">📅 {{ date(u.exam_date) }}</span>
            <span v-if="u.city">📍 {{ u.city }}</span>
            <span>🕒 {{ ago(u.posted_at) }}</span>
          </div>
          <footer class="cx-foot">
            <span></span>
            <a :href="u.pdf || u.url || '#'" target="_blank" rel="noopener" class="btn btn-primary cx-btn">
              {{ t("competitions.pdf") }}
            </a>
          </footer>
        </article>
      </div>

      <div v-if="(tab === 'open' ? shownOpen : shownUpdates).length === 0" class="empty">
        {{ t("competitions.empty") }}
      </div>
    </template>
  </div>
</template>
