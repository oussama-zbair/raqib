<script setup lang="ts">
const configured = isSupabaseConfigured();
const supabase = useSupabase();

const { data: rows } = await useAsyncData("sources", async () => {
  if (!supabase) return [];
  const { data } = await supabase
    .from("announcement_sources")
    .select("id,name,type,url,enabled,last_run_at,last_status")
    .order("type", { ascending: true });
  return data ?? [];
});

function isOk(status: string | null): boolean {
  return (status ?? "").startsWith("OK");
}
function fmt(ts: string | null): string {
  return ts ? new Date(ts).toLocaleString("fr-FR") : "jamais";
}
</script>

<template>
  <div class="container" style="padding-top: 40px">
    <h1 class="page-title">{{ $t("nav.sources") }}</h1>
    <p class="page-sub">État de santé des portails, ministères et agrégateurs surveillés.</p>

    <NotConfigured v-if="!configured" />
    <div v-else class="card" style="padding: 0; overflow: hidden">
      <table v-if="rows && rows.length">
        <thead>
          <tr>
            <th>Source</th>
            <th>Type</th>
            <th>Dernière exécution</th>
            <th>Statut</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="s in rows" :key="s.id">
            <td>
              <a :href="s.url" target="_blank" rel="noopener">{{ s.name }}</a>
              <span v-if="!s.enabled" class="badge" style="margin-left: 8px">désactivée</span>
            </td>
            <td>{{ s.type }}</td>
            <td>{{ fmt(s.last_run_at) }}</td>
            <td>
              <span class="badge" :class="isOk(s.last_status) ? 'ok' : 'err'">
                <span class="dot" :class="isOk(s.last_status) ? 'ok' : 'err'"></span>
                {{ s.last_status ?? "en attente" }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">Aucune source configurée.</div>
    </div>
  </div>
</template>
