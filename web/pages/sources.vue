<script setup lang="ts">
const { t } = useI18n();
const { data, pending, error } = useRaqibData();
const { ago } = useFormat();

function ok(status: string): boolean {
  return status.toLowerCase().startsWith("ok");
}
</script>

<template>
  <div class="container" style="padding-top: 40px">
    <h1 class="page-title">{{ t("status.title") }}</h1>
    <p class="page-sub">{{ t("status.subtitle") }}</p>

    <div v-if="pending && !data" class="empty">{{ t("competitions.loading") }}</div>
    <div v-else-if="error" class="empty">{{ t("competitions.error") }}</div>

    <template v-else-if="data">
      <div class="sx-stats">
        <div class="sx-stat"><b>{{ data.stats.open }}</b><span>{{ t("status.open") }}</span></div>
        <div class="sx-stat"><b>{{ data.stats.posted_total }}</b><span>{{ t("status.posted") }}</span></div>
        <div class="sx-stat"><b>{{ data.stats.stage_posts_total }}</b><span>{{ t("status.stagePosts") }}</span></div>
        <div class="sx-stat"><b>{{ data.stats.followed }}</b><span>{{ t("status.followed") }}</span></div>
      </div>

      <div class="card" style="padding: 0; overflow: hidden; margin-top: 20px">
        <table>
          <thead>
            <tr>
              <th>{{ t("status.source") }}</th>
              <th>{{ t("status.lastRun") }}</th>
              <th>{{ t("status.state") }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="s in data.sources" :key="s.name">
              <td>
                <a :href="s.url" target="_blank" rel="noopener">{{ s.name }}</a>
                <div style="color: var(--muted); font-size: 12px; margin-top: 2px">{{ t("sources.liveText") }}</div>
              </td>
              <td>{{ ago(data.updated_at) }}</td>
              <td>
                <span class="badge" :class="ok(s.status) ? 'ok' : 'err'">
                  <span class="dot" :class="ok(s.status) ? 'ok' : 'err'"></span>
                  {{ ok(s.status) ? t("status.ok") : t("status.failed") }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="card" style="margin-top: 20px">
        <h3 style="margin: 0 0 6px">{{ t("status.soonTitle") }}</h3>
        <p style="margin: 0; color: var(--muted)">{{ t("sources.soonText") }} {{ t("status.soonText") }}</p>
      </div>
    </template>
  </div>
</template>
