<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
const route = useRoute();
const router = useRouter();
const { data, pending, error } = useRaqibData();
const { date, ago } = useFormat();

// ---- filters (kept in the address bar so a filtered view can be shared) -------------
const tab = ref<"open" | "updates">(route.query.tab === "updates" ? "updates" : "open");
const q = ref(String(route.query.q ?? ""));
const family = ref(String(route.query.metier ?? ""));
const scale = ref(String(route.query.echelle ?? ""));
const field = ref(String(route.query.domaine ?? ""));
const city = ref(String(route.query.ville ?? ""));
const soon = ref(route.query.bientot === "1");
const sort = ref<"deadline" | "newest" | "posts">(
  (["deadline", "newest", "posts"].includes(String(route.query.tri)) ? route.query.tri : "deadline") as any,
);
const showAllFamilies = ref(false);

watch([tab, q, family, scale, field, city, soon, sort], () => {
  const query: Record<string, string> = {};
  if (tab.value !== "open") query.tab = tab.value;
  if (q.value) query.q = q.value;
  if (family.value) query.metier = family.value;
  if (scale.value) query.echelle = scale.value;
  if (field.value) query.domaine = field.value;
  if (city.value) query.ville = city.value;
  if (soon.value) query.bientot = "1";
  if (sort.value !== "deadline") query.tri = sort.value;
  router.replace({ query });
});

const activeCount = computed(
  () => [q.value, family.value, scale.value, field.value, city.value, soon.value].filter(Boolean).length,
);
function reset() {
  q.value = family.value = scale.value = field.value = city.value = "";
  soon.value = false;
}

// ---- data ---------------------------------------------------------------------------
function norm(s: string | null | undefined): string {
  return (s ?? "")
    .toLowerCase()
    .normalize("NFKD")
    .replace(/[\u0300-\u036f\u064b-\u065f\u0670\u0640]/g, "")
    .replace(/[أإآ]/g, "ا")
    .replace(/ى/g, "ي");
}
function matchesText(c: Concours | StageUpdate): boolean {
  const words = norm(q.value).split(/\s+/).filter(Boolean);
  if (!words.length) return true;
  const hay = norm([c.administration, c.grade, c.title, (c as any).specialty, c.city, (c as any).code].join(" "));
  return words.every((w) => hay.includes(w));
}

const open = computed(() =>
  (data.value?.concours ?? []).filter((c) => (daysUntil(c.deadline) ?? 0) >= 0),
);

type Key = "family" | "scale" | "field" | "city" | "soon";
function passes(c: Concours, skip?: Key): boolean {
  if (!matchesText(c)) return false;
  if (skip !== "family" && family.value && c.family !== family.value) return false;
  if (skip !== "scale" && scale.value && String(c.scale ?? "") !== scale.value) return false;
  if (skip !== "field" && field.value && !c.tags.includes(field.value)) return false;
  if (skip !== "city" && city.value && c.city !== city.value) return false;
  if (skip !== "soon" && soon.value && (daysUntil(c.deadline) ?? 99) > 7) return false;
  return true;
}
// Each option shows how many results it would give with the other filters kept.
function facet(skip: Key, pick: (c: Concours) => (string | null | undefined)[]) {
  const counts = new Map<string, number>();
  for (const c of open.value) {
    if (!passes(c, skip)) continue;
    for (const v of pick(c)) if (v) counts.set(v, (counts.get(v) ?? 0) + 1);
  }
  return [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
}
const families = computed(() => facet("family", (c) => [c.family]));
const scales = computed(() =>
  facet("scale", (c) => [c.scale ? String(c.scale) : null]).sort((a, b) => +a[0] - +b[0]),
);
const fields = computed(() => facet("field", (c) => c.tags));
const cities = computed(() => facet("city", (c) => [c.city]));
const visibleFamilies = computed(() => (showAllFamilies.value ? families.value : families.value.slice(0, 10)));

const shownOpen = computed(() => {
  const list = open.value.filter((c) => passes(c));
  if (sort.value === "newest") return list.sort((a, b) => (b.posted_at ?? "").localeCompare(a.posted_at ?? ""));
  if (sort.value === "posts") return list.sort((a, b) => (b.posts ?? 0) - (a.posts ?? 0));
  return list.sort((a, b) => (a.deadline ?? "9999").localeCompare(b.deadline ?? "9999"));
});
const shownUpdates = computed(() => (data.value?.updates ?? []).filter((u) => matchesText(u)));

const closingThisWeek = computed(() => open.value.filter((c) => (daysUntil(c.deadline) ?? 99) <= 7).length);

// ---- card helpers -------------------------------------------------------------------
function urgency(iso: string | null): "urgent" | "soon" | "ok" {
  const d = daysUntil(iso) ?? 99;
  return d <= 3 ? "urgent" : d <= 7 ? "soon" : "ok";
}
function deadlineLabel(iso: string | null): string {
  const d = daysUntil(iso);
  if (d === null) return "";
  if (d === 0) return t("competitions.today");
  return t("competitions.daysLeft", { n: d });
}
function isNew(iso: string | null): boolean {
  return !!iso && Date.now() - new Date(iso).getTime() < 36 * 3600 * 1000;
}
function specs(s: string | null): { shown: string[]; more: number } {
  const all = (s ?? "").split(" / ").map((x) => x.trim()).filter(Boolean);
  return { shown: all.slice(0, 3), more: Math.max(0, all.length - 3) };
}
function onImgError(e: Event) {
  (e.target as HTMLImageElement).src = "/morocco.png";
}
const copied = ref("");
async function share(c: Concours) {
  const text = `${c.title ?? c.grade ?? ""} · ${c.administration ?? ""}`;
  const url = c.url ?? (config.public.channelUrl as string);
  try {
    if (navigator.share) {
      await navigator.share({ title: text, text, url });
      return;
    }
    await navigator.clipboard.writeText(`${text}\n${url}`);
    copied.value = c.id;
    setTimeout(() => (copied.value = ""), 2000);
  } catch {
    /* share sheet closed */
  }
}
</script>

<template>
  <div class="container cx-page">
    <!-- header -->
    <div class="cx-hero">
      <div>
        <h1 class="page-title">{{ t("competitions.title") }}</h1>
        <p class="page-sub">{{ t("competitions.subtitle") }}</p>
      </div>
      <div v-if="data" class="cx-kpis">
        <div class="cx-kpi"><b>{{ open.length }}</b><span>{{ t("competitions.kpiOpen") }}</span></div>
        <div class="cx-kpi warn"><b>{{ closingThisWeek }}</b><span>{{ t("competitions.kpiClosing") }}</span></div>
        <div class="cx-kpi"><b>{{ data.updates.length }}</b><span>{{ t("competitions.kpiUpdates") }}</span></div>
      </div>
    </div>

    <!-- tabs -->
    <div class="cx-toolbar">
      <div class="cx-tabs" role="tablist">
        <button role="tab" :aria-selected="tab === 'open'" :class="{ on: tab === 'open' }" @click="tab = 'open'">
          🟢 {{ t("competitions.tabOpen") }}
        </button>
        <button role="tab" :aria-selected="tab === 'updates'" :class="{ on: tab === 'updates' }" @click="tab = 'updates'">
          📋 {{ t("competitions.tabUpdates") }}
        </button>
      </div>
      <a :href="config.public.channelUrl as string" target="_blank" rel="noopener" class="btn btn-ghost cx-follow">
        ✈️ {{ t("competitions.follow") }}
      </a>
    </div>

    <!-- search -->
    <div class="cx-search">
      <span class="cx-search-icon" aria-hidden="true">🔎</span>
      <input v-model="q" type="search" :placeholder="t('competitions.search')" :aria-label="t('competitions.search')" />
      <button v-if="q" class="cx-clear" :aria-label="t('competitions.reset')" @click="q = ''">✕</button>
    </div>

    <!-- filters -->
    <div v-if="tab === 'open' && data" class="cx-panel">
      <div class="cx-row">
        <span class="cx-label">💼 {{ t("competitions.job") }}</span>
        <div class="cx-chips">
          <button class="chip" :class="{ on: !family }" @click="family = ''">{{ t("competitions.all") }}</button>
          <button
            v-for="[f, n] in visibleFamilies"
            :key="f"
            class="chip"
            :class="{ on: family === f }"
            @click="family = family === f ? '' : f"
          >
            {{ f }} <span class="chip-n">{{ n }}</span>
          </button>
          <button v-if="families.length > 10" class="chip chip-more" @click="showAllFamilies = !showAllFamilies">
            {{ showAllFamilies ? t("competitions.less") : t("competitions.more", { n: families.length - 10 }) }}
          </button>
        </div>
      </div>

      <div v-if="scales.length" class="cx-row">
        <span class="cx-label">📊 {{ t("competitions.scale") }}</span>
        <div class="cx-chips">
          <button class="chip" :class="{ on: !scale }" @click="scale = ''">{{ t("competitions.all") }}</button>
          <button
            v-for="[s, n] in scales"
            :key="s"
            class="chip"
            :class="{ on: scale === s }"
            @click="scale = scale === s ? '' : s"
          >
            {{ t("competitions.scaleN", { n: s }) }} <span class="chip-n">{{ n }}</span>
          </button>
        </div>
      </div>

      <div class="cx-row cx-row-selects">
        <select v-model="field" class="cx-select" :aria-label="t('competitions.allFields')">
          <option value="">🏷 {{ t("competitions.allFields") }}</option>
          <option v-for="[f, n] in fields" :key="f" :value="f">#{{ f }} ({{ n }})</option>
        </select>
        <select v-model="city" class="cx-select" :aria-label="t('competitions.allCities')">
          <option value="">📍 {{ t("competitions.allCities") }}</option>
          <option v-for="[c, n] in cities" :key="c" :value="c">{{ c }} ({{ n }})</option>
        </select>
        <select v-model="sort" class="cx-select" :aria-label="t('competitions.sort')">
          <option value="deadline">↕ {{ t("competitions.sortDeadline") }}</option>
          <option value="newest">↕ {{ t("competitions.sortNewest") }}</option>
          <option value="posts">↕ {{ t("competitions.sortPosts") }}</option>
        </select>
        <label class="cx-switch">
          <input v-model="soon" type="checkbox" />
          <span class="cx-switch-ui"></span>
          ⏳ {{ t("competitions.closingSoon") }}
        </label>
      </div>
    </div>

    <!-- states -->
    <div v-if="pending && !data" class="cx-grid">
      <div v-for="i in 6" :key="i" class="cx-card cx-skeleton"></div>
    </div>
    <div v-else-if="error" class="empty">{{ t("competitions.error") }}</div>

    <template v-else-if="data">
      <div class="cx-meta">
        <span>{{ t("competitions.count", tab === "open" ? shownOpen.length : shownUpdates.length) }}</span>
        <span>· {{ t("competitions.updatedAt", { when: ago(data.updated_at) }) }}</span>
        <button v-if="activeCount" class="cx-reset" @click="reset">✕ {{ t("competitions.reset") }} ({{ activeCount }})</button>
      </div>

      <!-- open concours -->
      <div v-if="tab === 'open'" class="cx-grid">
        <article v-for="c in shownOpen" :key="c.id" class="cx-card" :class="`u-${urgency(c.deadline)}`">
          <div class="cx-top">
            <img :src="c.logo || '/morocco.png'" alt="" class="cx-logo" loading="lazy" @error="onImgError" />
            <div class="cx-top-text">
              <p class="cx-admin">{{ c.administration }}</p>
              <h3 class="cx-title">{{ c.title || c.grade }}</h3>
              <p v-if="c.grade && c.grade !== c.title" class="cx-grade">{{ c.grade }}</p>
            </div>
            <span v-if="isNew(c.posted_at)" class="cx-new">{{ t("competitions.new") }}</span>
          </div>

          <div class="cx-pills">
            <span v-if="c.posts" class="pill">👥 {{ t("competitions.posts", c.posts) }}</span>
            <span v-if="c.scale" class="pill">📊 {{ t("competitions.scaleN", { n: c.scale }) }}</span>
            <span v-if="c.city" class="pill">📍 {{ c.city }}</span>
          </div>

          <p v-if="c.specialty" class="cx-spec">
            🎓 {{ specs(c.specialty).shown.join(" · ") }}
            <span v-if="specs(c.specialty).more" class="cx-more">+{{ specs(c.specialty).more }}</span>
          </p>

          <div class="cx-dates">
            <div class="cx-date">
              <span class="k">⏳ {{ t("competitions.deadline") }}</span>
              <span class="v">{{ date(c.deadline) }}</span>
              <span class="cx-left" :class="urgency(c.deadline)">{{ deadlineLabel(c.deadline) }}</span>
            </div>
            <div class="cx-date">
              <span class="k">📝 {{ t("competitions.exam") }}</span>
              <span class="v">{{ c.exam_date ? date(c.exam_date) : t("competitions.examTbd") }}</span>
            </div>
          </div>

          <StageTimeline :done="c.stages" />

          <footer class="cx-foot">
            <span class="cx-tags"><span v-for="tg in c.tags" :key="tg">#{{ tg }}</span></span>
            <div class="cx-actions">
              <button class="btn btn-ghost cx-icon" :title="t('competitions.share')" @click="share(c)">
                {{ copied === c.id ? "✓" : "📤" }}
              </button>
              <a v-if="c.url" :href="c.url" target="_blank" rel="noopener" class="btn btn-primary cx-btn">
                {{ t("competitions.official") }} ↗
              </a>
            </div>
          </footer>
        </article>
      </div>

      <!-- convocations and results -->
      <div v-else class="cx-grid">
        <article v-for="u in shownUpdates" :key="u.id + u.stage" class="cx-card" :class="`s-${u.stage.toLowerCase()}`">
          <div class="cx-top">
            <img :src="u.logo || '/morocco.png'" alt="" class="cx-logo" loading="lazy" @error="onImgError" />
            <div class="cx-top-text">
              <StageBadge :stage="u.stage" />
              <p class="cx-admin" style="margin-top: 8px">{{ u.administration }}</p>
              <h3 class="cx-title">{{ u.title || u.grade }}</h3>
            </div>
            <span v-if="isNew(u.posted_at)" class="cx-new">{{ t("competitions.new") }}</span>
          </div>
          <div class="cx-pills">
            <span v-if="u.exam_date" class="pill">📅 {{ date(u.exam_date) }}</span>
            <span v-if="u.city" class="pill">📍 {{ u.city }}</span>
            <span class="pill">🕒 {{ ago(u.posted_at) }}</span>
          </div>
          <footer class="cx-foot">
            <span></span>
            <a :href="u.pdf || u.url || '#'" target="_blank" rel="noopener" class="btn btn-primary cx-btn">
              📄 {{ t("competitions.pdf") }} ↗
            </a>
          </footer>
        </article>
      </div>

      <div v-if="(tab === 'open' ? shownOpen : shownUpdates).length === 0" class="empty cx-empty">
        <p>{{ t("competitions.empty") }}</p>
        <button v-if="activeCount" class="btn btn-ghost" @click="reset">{{ t("competitions.reset") }}</button>
      </div>
    </template>
  </div>
</template>
