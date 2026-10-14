// Nuxt config — Raqib public site (landing + read-only status).
// Deployed to Cloudflare Pages. Uses the Supabase ANON key + RLS so it can only read
// non-sensitive columns (never CIN).

export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  devtools: { enabled: true },
  modules: ["@nuxtjs/i18n"],
  css: ["~/assets/css/main.css"],

  i18n: {
    strategy: "no_prefix", // language chosen via toggle, persisted in a cookie
    bundle: { optimizeTranslationDirective: false }, // silence v10 deprecation warning
    defaultLocale: "fr",
    detectBrowserLanguage: {
      useCookie: true,
      cookieKey: "raqib_lang",
      redirectOn: "root",
      fallbackLocale: "fr",
    },
    locales: [
      { code: "fr", name: "Français", language: "fr-FR", dir: "ltr", file: "fr.json" },
      { code: "ar", name: "العربية", language: "ar-MA", dir: "rtl", file: "ar.json" },
    ],
  },

  runtimeConfig: {
    public: {
      supabaseUrl: process.env.NUXT_PUBLIC_SUPABASE_URL ?? "",
      supabaseAnonKey: process.env.NUXT_PUBLIC_SUPABASE_ANON_KEY ?? "",
      telegramBotUrl: process.env.NUXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/RaqibBot",
      githubUrl: process.env.NUXT_PUBLIC_GITHUB_URL ?? "https://github.com/oussama-zbair/raqib",
    },
  },

  nitro: {
    preset: "cloudflare-pages",
  },

  app: {
    head: {
      title: "Raqib — رقيب · Veilleur des concours publics",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Raqib (رقيب) surveille les concours publics marocains et vous alerte dès qu'une nouvelle opportunité correspond à votre profil — à temps pour déposer votre dossier. Puis il suit votre convocation.",
        },
        { name: "theme-color", content: "#0E7C66" },
        // Open Graph / social
        { property: "og:title", content: "Raqib — votre veilleur des concours publics" },
        {
          property: "og:description",
          content:
            "Ne manquez plus jamais un concours. Raqib repère chaque nouvelle opportunité à temps pour déposer, puis surveille votre convocation.",
        },
        { property: "og:type", content: "website" },
        { property: "og:image", content: "/og.png" },
        { name: "twitter:card", content: "summary_large_image" },
      ],
      link: [
        { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
        { rel: "preconnect", href: "https://fonts.googleapis.com" },
        { rel: "preconnect", href: "https://fonts.gstatic.com", crossorigin: "" },
        {
          rel: "stylesheet",
          href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Cairo:wght@400;600;700;800&display=swap",
        },
      ],
    },
  },
});
