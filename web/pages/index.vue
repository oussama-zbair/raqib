<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
useReveal();

const botUrl = config.public.telegramBotUrl as string;

const problems = ["missed", "fragmented", "misleading", "silent", "window"];
const problemIcons: Record<string, string> = {
  missed: "calendar",
  fragmented: "scatter",
  misleading: "mask",
  silent: "pdf",
  window: "clock",
};

const steps = ["onboard", "ingest", "match", "digest", "monitor"];
const stepIcons: Record<string, string> = {
  onboard: "profile",
  ingest: "ingest",
  match: "match",
  digest: "digest",
  monitor: "monitor",
};

const builtPoints = ["shared", "free", "privacy"];
const builtIcons: Record<string, string> = {
  shared: "users",
  free: "free",
  privacy: "shield",
};

const aiPoints = ["extract", "bilingual", "fallback"];
const aiIcons: Record<string, string> = {
  extract: "ai",
  bilingual: "match",
  fallback: "shield",
};

const convocationRows = [
  { k: "admin", v: "adminValue" },
  { k: "post", v: "postValue" },
  { k: "candidate", v: "candidateValue" },
  { k: "centre", v: "centreValue" },
  { k: "room", v: "roomValue" },
  { k: "table", v: "tableValue" },
  { k: "date", v: "dateValue" },
];

const centralSources = [{ logo: "emploi", label: "emploi-public.ma" }];
const ministrySources = [
  { logo: "finances", label: "Finances" },
  { logo: "justice", label: "Justice" },
  { logo: "interieur", label: "Intérieur" },
  { logo: "ocp", label: "OCP" },
  { logo: "cdg", label: "CDG" },
  { logo: "oncf", label: "ONCF" },
  { logo: "barid", label: "Barid Al-Maghrib" },
  { logo: "anp", label: "ANP" },
];
const communitySources = [
  { logo: "telegram", label: "Telegram" },
  { logo: "aggregator", label: "Alwadifa-Maroc" },
  { logo: "aggregator", label: "Wadifa9" },
];
</script>

<template>
  <div>
    <!-- HERO -->
    <section class="container hero">
      <div class="hero-grid">
        <div>
          <span class="badge-pill">{{ t("hero.badge") }}</span>
          <h1>{{ t("hero.title") }}</h1>
          <p class="lead">{{ t("hero.subtitle") }}</p>
          <p class="tagline">{{ t("hero.tagline") }}</p>
          <div class="cta-row">
            <a :href="botUrl" target="_blank" rel="noopener" class="btn btn-primary">
              ✈️ {{ t("hero.ctaPrimary") }}
            </a>
            <a href="#flow" class="btn btn-ghost">{{ t("hero.ctaSecondary") }}</a>
          </div>
          <p class="trust">✓ {{ t("hero.trust") }}</p>
        </div>
        <div class="hero-art">
          <HeroArt />
        </div>
      </div>
    </section>

    <!-- PROBLEM -->
    <section class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">Raqib</span>
        <h2>{{ t("problem.title") }}</h2>
        <p>{{ t("problem.subtitle") }}</p>
      </div>
      <div class="card-grid">
        <div v-for="(p, i) in problems" :key="p" class="pcard reveal" :style="{ '--i': i }">
          <div class="ic-chip"><Icon :name="problemIcons[p]" /></div>
          <h3>{{ t(`problem.cards.${p}.title`) }}</h3>
          <p>{{ t(`problem.cards.${p}.text`) }}</p>
        </div>
      </div>
    </section>

    <!-- FLOW -->
    <section id="flow" class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">Workflow</span>
        <h2>{{ t("flow.title") }}</h2>
        <p>{{ t("flow.subtitle") }}</p>
      </div>
      <div class="stage-labels reveal">
        <span class="stage-tag stage-primary">{{ t("flow.stage1") }}</span>
        <span class="stage-tag stage-secondary">{{ t("flow.stage2") }}</span>
      </div>
      <div class="steps">
        <div
          v-for="(s, i) in steps"
          :key="s"
          class="step reveal"
          :class="{ 'step-secondary': s === 'monitor' }"
          :style="{ '--i': i }"
        >
          <div class="num">{{ i + 1 }}</div>
          <Icon :name="stepIcons[s]" />
          <h3>{{ t(`flow.steps.${s}.title`) }}</h3>
          <p>{{ t(`flow.steps.${s}.text`) }}</p>
        </div>
      </div>
    </section>

    <!-- CONVOCATION MOCK -->
    <section class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">★</span>
        <h2>{{ t("convocation.title") }}</h2>
        <p>{{ t("convocation.subtitle") }}</p>
      </div>
      <div class="tg-wrap">
        <div class="tg-phone reveal">
          <div class="tg-header">
            <div class="tg-avatar"><img src="/favicon.svg" alt="Raqib" /></div>
            <div>
              <div class="tg-name">Raqib · رقيب</div>
              <div class="tg-status">bot</div>
            </div>
          </div>
          <div class="tg-chat">
            <!-- STAGE 1: new concours alert with track button -->
            <div class="tg-msg">
              <div class="tg-bubble tg-bubble--new">
                <div class="alert-head alert-head--new">🎯 {{ t("convocation.newTitle") }}</div>
                <div class="tg-row"><span class="k">{{ t("convocation.admin") }} :</span><span class="v">{{ t("convocation.newAdminValue") }}</span></div>
                <div class="tg-row"><span class="k">{{ t("convocation.newPost") }} :</span><span class="v">{{ t("convocation.newPostValue") }}</span></div>
                <div class="tg-row"><span class="k">{{ t("convocation.newSeats") }} :</span><span class="v">{{ t("convocation.newSeatsValue") }}</span></div>
                <div class="tg-row"><span class="k">{{ t("convocation.newDeadline") }} :</span><span class="v">{{ t("convocation.newDeadlineValue") }}</span></div>
                <div class="tg-buttons">
                  <button class="tg-btn tg-btn--accent">{{ t("convocation.newTrack") }}</button>
                  <button class="tg-btn">{{ t("convocation.newApply") }}</button>
                </div>
                <div class="tg-time">09:02 <span class="tg-tick">✓✓</span></div>
              </div>
            </div>

            <!-- user tapped Suivre -> system note -->
            <div class="tg-note">{{ t("convocation.trackedBadge") }}</div>

            <!-- STAGE 2: convocation found -->
            <div class="tg-msg">
              <div class="tg-bubble tg-bubble--alert">
                <div class="alert-head">🚨 {{ t("convocation.alertTitle") }}</div>
                <div v-for="row in convocationRows" :key="row.k" class="tg-row">
                  <span class="k">{{ t(`convocation.${row.k}`) }} :</span>
                  <span class="v">{{ t(`convocation.${row.v}`) }}</span>
                </div>
                <div class="tg-buttons">
                  <button class="tg-btn tg-btn--accent">📄 {{ t("convocation.download") }}</button>
                </div>
                <div class="tg-time">08:14 <span class="tg-tick">✓✓</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="reveal tg-side">
          <div class="pcard">
            <div class="ic-chip"><Icon name="digest" /></div>
            <h3>{{ t("flow.steps.digest.title") }}</h3>
            <p>{{ t("flow.steps.digest.text") }}</p>
          </div>
          <div class="pcard">
            <div class="ic-chip"><Icon name="monitor" /></div>
            <h3>{{ t("flow.steps.monitor.title") }}</h3>
            <p>{{ t("flow.steps.monitor.text") }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- SOURCES -->
    <section class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">Coverage</span>
        <h2>{{ t("sources.title") }}</h2>
        <p>{{ t("sources.subtitle") }}</p>
      </div>
      <div class="src-groups">
        <div class="src-group reveal">
          <div class="src-group-head"><span class="dot ok"></span>{{ t("sources.central") }}</div>
          <div class="src-logos">
            <div v-for="s in centralSources" :key="s.label" class="src-tile">
              <BrandLogo :name="s.logo" />
              <span>{{ s.label }}</span>
            </div>
          </div>
        </div>

        <div class="src-group reveal" style="--i: 1">
          <div class="src-group-head"><span class="dot ok"></span>{{ t("sources.ministries") }}</div>
          <div class="src-logos">
            <div v-for="s in ministrySources" :key="s.label" class="src-tile">
              <BrandLogo :name="s.logo" />
              <span>{{ s.label }}</span>
            </div>
          </div>
        </div>

        <div class="src-group reveal" style="--i: 2">
          <div class="src-group-head"><span class="dot ok"></span>{{ t("sources.community") }}</div>
          <div class="src-logos">
            <div v-for="s in communitySources" :key="s.label" class="src-tile">
              <BrandLogo :name="s.logo" />
              <span>{{ s.label }}</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- AI -->
    <section class="container section">
      <div class="ai-band reveal">
        <div class="ai-head">
          <span class="badge-pill">{{ t("ai.badge") }}</span>
          <h2>{{ t("ai.title") }}</h2>
          <p>{{ t("ai.subtitle") }}</p>
        </div>
        <div class="built-grid" style="margin-top: 28px">
          <div v-for="(p, i) in aiPoints" :key="p" class="pcard reveal" :style="{ '--i': i }">
            <div class="ic-chip"><Icon :name="aiIcons[p]" /></div>
            <h3>{{ t(`ai.points.${p}.title`) }}</h3>
            <p>{{ t(`ai.points.${p}.text`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- BUILT / ZERO-COST -->
    <section class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">Open source</span>
        <h2>{{ t("built.title") }}</h2>
        <p>{{ t("built.subtitle") }}</p>
      </div>
      <div class="built-grid">
        <div v-for="(b, i) in builtPoints" :key="b" class="pcard reveal" :style="{ '--i': i }">
          <div class="ic-chip"><Icon :name="builtIcons[b]" /></div>
          <h3>{{ t(`built.points.${b}.title`) }}</h3>
          <p>{{ t(`built.points.${b}.text`) }}</p>
        </div>
      </div>
    </section>

    <SiteFooter />
  </div>
</template>
