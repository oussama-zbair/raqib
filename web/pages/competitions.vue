<script setup lang="ts">
const configured = isSupabaseConfigured();
const supabase = useSupabase();

const { data: rows } = await useAsyncData("competitions", async () => {
  if (!supabase) return [];
  const { data } = await supabase
    .from("competitions")
    .select(
      "id,administration,grade,specialty,stage,deadline,post_count,early_signal,title_fr,title_ar,submission_link",
    )
    .order("first_seen_at", { ascending: false })
    .limit(100);
  return data ?? [];
});

function title(c: any): string {
  return c.title_fr || c.title_ar || c.administration || "Concours";
}
</script>

<template>
  <div class="container" style="padding-top: 40px">
    <h1 class="page-title">{{ $t("nav.competitions") }}</h1>
    <p class="page-sub">Les 100 concours canoniques les plus récents (dédupliqués, toutes sources).</p>

    <NotConfigured v-if="!configured" />
    <div v-else class="card" style="padding: 0; overflow: hidden">
      <table v-if="rows && rows.length">
        <thead>
          <tr>
            <th>Concours</th>
            <th>Grade</th>
            <th>Spécialité</th>
            <th>Étape</th>
            <th>Postes</th>
            <th>Date limite</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="c in rows" :key="c.id">
            <td>
              <a v-if="c.submission_link" :href="c.submission_link" target="_blank" rel="noopener">
                {{ title(c) }}
              </a>
              <span v-else>{{ title(c) }}</span>
              <span v-if="c.early_signal" class="badge early" style="margin-left: 8px">⚡ précoce</span>
              <div style="color: var(--muted); font-size: 12px; margin-top: 2px">{{ c.administration }}</div>
            </td>
            <td>{{ c.grade ?? "—" }}</td>
            <td>{{ c.specialty ?? "—" }}</td>
            <td><StageBadge :stage="c.stage" /></td>
            <td>{{ c.post_count ?? "—" }}</td>
            <td>{{ c.deadline ?? "—" }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="empty">Aucun concours pour l'instant. Lancez le job d'ingestion.</div>
    </div>
  </div>
</template>
