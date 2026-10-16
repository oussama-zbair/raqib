<div align="center">

<img src="web/public/logo.png" width="104" alt="Raqib" />

# Raqib · رقيب

**Votre veilleur des concours publics marocains**
*رقيبك في المباريات العمومية · Your public-exam watchman*

[![Ouvrir le bot](https://img.shields.io/badge/Telegram-%40RaqibMaBot-229ED9?logo=telegram&logoColor=white)](https://t.me/RaqibMaBot)
![License](https://img.shields.io/badge/license-MIT-2563EB)
![FR](https://img.shields.io/badge/Fran%C3%A7ais-FR-22D3A8)
![AR](https://img.shields.io/badge/%D8%A7%D9%84%D8%B9%D8%B1%D8%A8%D9%8A%D8%A9-AR-2563EB)

</div>

---

## 🎯 Le problème

Au Maroc, le plus dur dans un concours public n'est souvent pas l'examen — c'est
l'information. Les annonces sont éparpillées sur `emploi-public.ma`, des dizaines de
canaux Telegram, et les portails de chaque ministère. On manque un concours parce qu'on
apprend son existence **après le délai de dépôt**. Et après l'inscription, aucune
notification : l'administration met en ligne un PDF scanné de *candidats convoqués*, et si
on ne repère pas son **CIN** dans les 48–72h, on perd sa chance.

## 👁️ La solution

**Raqib** (رقيب, « le veilleur ») surveille en continu tous les portails, filtre selon
votre profil exact (grade + spécialité, en FR et AR), et vous alerte sur Telegram :

1. **Dès qu'un nouveau concours** correspond à votre profil — à temps pour déposer.
2. **Dès que votre CIN ou votre nom (FR/AR) apparaît** sur une liste de convoqués —
   avec centre, salle et n° de table extraits automatiquement.

Le tout **gratuitement**, bilingue, dans un simple bot Telegram.

👉 **[Commencer sur @RaqibMaBot](https://t.me/RaqibMaBot)**

## ✨ Fonctionnalités

- 🔔 **Alertes ciblées** — uniquement les concours qui matchent votre grade et votre spécialité
- 🌍 **Bilingue FR / AR** — interface et correspondance dans les deux langues
- 🤖 **IA intégrée** — un modèle d'IA lit les PDF scannés et le texte non structuré que l'analyse classique rate
- 📄 **Détection CIN & nom** — recherche automatique de votre CIN ou de votre nom (FR/AR) dans les listes de convoqués
- 📌 **Suivi en un clic** — suivez un concours et laissez Raqib surveiller sa convocation
- 🔒 **CIN chiffré** — votre numéro est chiffré au repos, déchiffré uniquement le temps de la recherche

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Bot Telegram | TypeScript · Supabase Edge Function |
| Collecte & analyse | Python · GitHub Actions (cron) |
| Site vitrine | Nuxt (Vue 3) · Cloudflare Pages |
| Base de données | Supabase (PostgreSQL) |
| IA (fallback) | Google Gemini |

```
backend/   Python — scrapers, matching bilingue, moteur PDF, notifications, cron
bot/       TypeScript — bot Telegram (Supabase Edge Function)
web/       Nuxt — site vitrine bilingue (FR/AR)
db/        SQL — schéma Supabase
```

## 🔒 Confidentialité

Le CIN est une donnée sensible. Il est **chiffré au repos** (Fernet) et déchiffré
**uniquement en mémoire** le temps de rechercher votre nom dans un PDF de convocation.
Il n'est jamais exposé publiquement.

---

<div align="center">

Fait avec ❤️ pour les candidats marocains · [@RaqibMaBot](https://t.me/RaqibMaBot)

</div>
