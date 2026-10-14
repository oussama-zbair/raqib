<template>
  <div class="card" style="border-color: rgba(244, 183, 64, 0.4)">
    <div style="display: flex; align-items: flex-start; gap: 14px">
      <span style="font-size: 26px; line-height: 1">⚙️</span>
      <div>
        <h3 style="margin: 0 0 6px">Supabase non configuré</h3>
        <p style="margin: 0 0 10px; color: var(--muted)">
          Le tableau de bord a besoin des identifiants Supabase pour afficher les données.
          Créez un fichier <code>.env</code> dans <code>web/</code> :
        </p>
        <pre style="margin: 0; padding: 12px 14px; background: var(--bg); border: 1px solid var(--border); border-radius: 10px; overflow-x: auto"><code>NUXT_PUBLIC_SUPABASE_URL=https://VOTRE-PROJET.supabase.co
NUXT_PUBLIC_SUPABASE_ANON_KEY=votre-cle-anon</code></pre>
        <p style="margin: 10px 0 0; color: var(--muted); font-size: 13px">
          Puis relancez <code>npm run dev</code>. Les clés se trouvent dans
          Supabase → Project Settings → API.
        </p>
      </div>
    </div>
  </div>
</template>
