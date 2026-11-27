// Nuxt config: Raqib public site (landing, concours, source status).
// Static site on Cloudflare Pages. Data comes from state/public.json (see runtimeConfig).

export default defineNuxtConfig({
  compatibilityDate: "2025-01-01",
  // Devtools off: it added ~7s to dev startup (NUXT_B8014) and isn't needed. Re-enable
  // temporarily with `devtools: { enabled: true }` if you want the in-browser panel.
  devtools: { enabled: false },
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
      // Written by the publish job after every run (every 30 minutes). Read in the browser,
      // so the site is always current without a rebuild, a server or a database.
      dataUrl:
        process.env.NUXT_PUBLIC_DATA_URL ??
        "https://raw.githubusercontent.com/oussama-zbair/raqib/main/state/public.json",
      channelUrl: process.env.NUXT_PUBLIC_CHANNEL_URL ?? "https://t.me/RaqibEmploi",
      discussionUrl: process.env.NUXT_PUBLIC_DISCUSSION_URL ?? "https://t.me/RaqibDiscussion",
      whatsappUrl:
        process.env.NUXT_PUBLIC_WHATSAPP_URL ??
        "https://whatsapp.com/channel/0029VbEJN8rIXnlxFgLlea1w",
      telegramBotUrl: process.env.NUXT_PUBLIC_TELEGRAM_BOT_URL ?? "https://t.me/RaqibMaBot",
      ownerUrl: process.env.NUXT_PUBLIC_OWNER_URL ?? "https://oussamazbair.engineer",
    },
  },

  nitro: {
    preset: "cloudflare-pages",
    prerender: { routes: ["/", "/competitions", "/sources"], crawlLinks: true },
  },

  app: {
    head: {
      title: "Raqib · رقيب · Tous les concours publics au Maroc",
      meta: [
        { charset: "utf-8" },
        { name: "viewport", content: "width=device-width, initial-scale=1" },
        {
          name: "description",
          content:
            "Raqib publie chaque concours public marocain dès sa sortie : annonces, convocations écrit et oral, résultats. Source officielle emploi-public.ma, mise à jour toutes les 30 minutes.",
        },
        { name: "theme-color", content: "#2563EB" },
        // Open Graph / social
        { property: "og:title", content: "Raqib · Tous les concours publics au Maroc" },
        {
          property: "og:description",
          content:
            "Annonces, convocations et résultats des concours publics marocains, dès leur publication.",
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
