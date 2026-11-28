<div align="center">

<img src="web/public/logo.png" width="104" alt="Raqib" />

# Raqib · رقيب

**Tous les concours publics marocains, dès leur publication**
*كل مباريات التوظيف العمومي بالمغرب، فور صدورها*

[![Chaîne Telegram](https://img.shields.io/badge/Telegram-%40RaqibEmploi-229ED9?logo=telegram&logoColor=white)](https://t.me/RaqibEmploi)
[![Chaîne WhatsApp](https://img.shields.io/badge/WhatsApp-Raqib-25D366?logo=whatsapp&logoColor=white)](https://whatsapp.com/channel/0029VbEJN8rIXnlxFgLlea1w)
[![Site](https://img.shields.io/badge/Site-raqib--emploi.pages.dev-2563EB)](https://raqib-emploi.pages.dev)
[![CI](https://github.com/oussama-zbair/raqib/actions/workflows/ci.yml/badge.svg)](https://github.com/oussama-zbair/raqib/actions/workflows/ci.yml)
![License](https://img.shields.io/badge/license-MIT-2563EB)

</div>

---

## 🎯 Le problème

Au Maroc, le plus dur dans un concours public est souvent l'information, pas l'examen.
Les annonces sont éparpillées entre le portail officiel, les sites des ministères et des
dizaines de canaux Telegram. Après l'inscription, personne ne prévient quand la liste des
convoqués à l'écrit ou à l'oral est publiée, et on a souvent 48–72h pour la trouver.

## 👁️ Ce que fait Raqib aujourd'hui

Raqib lit le portail officiel **emploi-public.ma** toutes les 30 minutes et publie
chaque étape de chaque concours, pour tous les domaines et toutes les administrations
(services de l'État, collectivités territoriales, établissements et entreprises publics) :

| Étape | Publication |
|---|---|
| 🟢 Annonce | administration, grade, spécialités, postes, date limite, date de l'écrit, lien officiel |
| 📋 Convocation à l'écrit | en réponse à l'annonce d'origine, avec la liste officielle |
| 🎤 Convocation à l'oral | dans le même fil |
| 🏆 Résultats | dans le même fil : un concours se suit du début à la fin |

Sur trois canaux :

- **📢 Chaîne Telegram [@RaqibEmploi](https://t.me/RaqibEmploi)** : chaque publication en direct,
  avec le logo de l'administration (ou les armoiries du Royaume) et des hashtags par domaine,
  étape et ville.
- **🟢 Chaîne [WhatsApp](https://whatsapp.com/channel/0029VbEJN8rIXnlxFgLlea1w)** : pour ceux qui n'ont pas
  Telegram. Trois fois par jour (09:00, 15:00, 21:00), le bot prépare des cartes prêtes à publier.
- **🌐 Site [raqib-emploi.pages.dev](https://raqib-emploi.pages.dev)** : les concours ouverts avec recherche
  et filtres par métier, échelle, domaine et ville, les jours restants et la frise des étapes.

Le bot **[@RaqibMaBot](https://t.me/RaqibMaBot)** accueille les nouveaux membres (accès après avoir rejoint
la chaîne) et modère le groupe de discussion (liens supprimés, insultes : avertissement, puis
24h de silence, puis exclusion).

Gratuit, sans publicité, sans aucune donnée personnelle collectée.

## ⚙️ Fonctionnement

```
Cloudflare Worker (cron */30)          ← l'horloge, à l'heure
   └─► démarre le workflow GitHub "publish"
          └─► GitHub Actions (machine Linux neuve)
                1. lit emploi-public.ma (annonces, convocations, résultats)
                2. compare avec state/posted.json (la mémoire)
                3. publie le nouveau sur Telegram
                4. prépare les cartes WhatsApp (3 fois par jour)
                5. écrit state/public.json pour le site
                6. commite state/ dans le dépôt
Site (Cloudflare Pages)  ← le navigateur lit state/public.json directement sur GitHub
```

**Choix techniques**

- **Pas de base de données** : un seul écrivain, quelques milliers d'entrées par an, aucune donnée
  utilisateur. Un fichier JSON dans Git suffit, ne coûte rien et garde tout l'historique.
- **Une seule identité par concours** : sur le portail, l'annonce, les listes et les résultats partagent
  le même identifiant. Pages FR et AR, toutes étapes : une seule clé, donc aucun doublon.
- **Jamais deux fois** : la mémoire est enregistrée après chaque envoi, une seule exécution à la fois,
  et l'envoi réel n'est possible que depuis GitHub Actions.
- **Jamais bloqué** : une publication refusée par Telegram est sautée, réessayée trois fois puis
  abandonnée. Chaque étape du job a son propre filet de sécurité.
- **Aucune convocation manquée** : les listes ne sont pas triées par date sur le portail. Raqib combine
  les dernières mises à jour de l'accueil, les premières pages et le suivi d'environ 370 concours actifs.
- **Heure du Maroc officielle** : règles IANA (`Africa/Casablanca`) mises à jour à chaque exécution,
  avec une variable `MOROCCO_UTC_OFFSET` en secours.
- **Collecte respectueuse** : uniquement les pages autorisées par robots.txt, User-Agent identifié,
  faible fréquence, lien vers la source officielle. Les sites qui bloquent les robots ne sont pas
  contournés.

## 🛠️ Stack technique

| Composant | Technologie |
|---|---|
| Collecte, publication, cartes | Python 3.11 · httpx · BeautifulSoup · Pillow |
| Planification | Cloudflare Workers (cron) + GitHub Actions |
| Bot et modération | Cloudflare Worker (JavaScript) · KV |
| Site | Nuxt 3 (Vue) · FR / AR · RTL · Cloudflare Pages |
| Données | `state/*.json` dans le dépôt |
| Tests | pytest (fixtures : pages réelles du portail) · node:test |

```
backend/        Python : scrapers, déduplication, cartes, publication, résumé WhatsApp
  app/jobs/       publish_channel.py (le job), posted_state.py (la mémoire), whatsapp_digest.py
  app/scrapers/   emploi_public.py (source officielle, 4 étapes)
  app/notify/     channel.py (cartes Telegram, images)
  tests/          tests hors ligne sur des pages réelles
web/            Nuxt : site bilingue (accueil, concours, sources)
state/          posted.json · public.json · last_run.json (écrits par le job)
.github/        publish.yml (le job) · ci.yml (tests à chaque push)
bot/, db/       ancienne conception (bot Supabase, schéma SQL) gardée pour l'assistant à venir
```

Le Worker (bot, modération, horloge) est déployé séparément sur Cloudflare.

## 🩺 Santé du service

- `state/last_run.json` : dernière exécution, état de chaque source, publications, erreurs éventuelles.
- Onglet **Actions** : chaque exécution du job (toutes les 30 minutes) et les tests CI.
- Page [Sources](https://raqib-emploi.pages.dev/sources) du site.

## 🚀 La suite

L'assistant personnel, en préparation :

- **Profil** dans le bot : grade, spécialité, ville.
- **Alertes ciblées** en message privé, uniquement pour votre profil.
- **Votre nom dans les listes** : recherche de votre CIN ou de votre nom (FR/AR) dans chaque liste
  de convoqués, avec centre, salle et n° de table. Le CIN sera chiffré au repos. Cette fonction
  attend l'accord du portail, qui interdit le téléchargement automatisé des PDF.
- **Coach IA** : éligibilité, format des épreuves, QCM d'entraînement, oral blanc.
- Alerte quand une source tombe, déploiement automatique du site, sources officielles
  supplémentaires (uniquement celles qui autorisent la collecte).

## ⚖️ Avertissement

Projet indépendant, non affilié à l'administration. Les données sont publiques et proviennent du
portail officiel [emploi-public.ma](https://www.emploi-public.ma). Vérifiez toujours l'annonce officielle
avant de candidater.

---

<div align="center">

🛠 Développé par **[Oussama Zbair](https://oussamazbair.engineer)** · [@ousamz](https://t.me/ousamz)

[@RaqibEmploi](https://t.me/RaqibEmploi) · [WhatsApp](https://whatsapp.com/channel/0029VbEJN8rIXnlxFgLlea1w) · [raqib-emploi.pages.dev](https://raqib-emploi.pages.dev)

</div>
