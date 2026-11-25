<script setup lang="ts">
const { t } = useI18n();
const config = useRuntimeConfig();
useReveal();
const { data } = useRaqibData();
const { ago } = useFormat();

const channelUrl = config.public.channelUrl as string;

const problems = ["missed", "fragmented", "misleading", "silent", "window"];
const problemIcons: Record<string, string> = {
  missed: "calendar", fragmented: "scatter", misleading: "mask", silent: "pdf", window: "clock",
};

const nowPoints = ["annonces", "convocations", "resultats", "official"];
const nowIcons: Record<string, string> = {
  annonces: "digest", convocations: "pdf", resultats: "match", official: "shield",
};

const futurePoints = ["profile", "alerts", "cin", "coach"];
const futureIcons: Record<string, string> = {
  profile: "profile", alerts: "digest", cin: "monitor", coach: "ai",
};

const builtPoints = ["shared", "free", "privacy"];
const builtIcons: Record<string, string> = { shared: "users", free: "free", privacy: "shield" };

const convocationRows = [
  { k: "admin", v: "adminValue" },
  { k: "post", v: "postValue" },
  { k: "candidate", v: "candidateValue" },
  { k: "centre", v: "centreValue" },
  { k: "room", v: "roomValue" },
  { k: "table", v: "tableValue" },
  { k: "date", v: "dateValue" },
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
            <a :href="channelUrl" target="_blank" rel="noopener" class="btn btn-primary">
              ✈️ {{ t("hero.ctaPrimary") }}
            </a>
            <NuxtLink to="/competitions" class="btn btn-ghost">{{ t("hero.ctaSecondary") }}</NuxtLink>
          </div>
          <p class="trust">
            <span class="dot ok"></span>
            <template v-if="data">{{ t("hero.live", { open: data.stats.open, when: ago(data.updated_at) }) }}</template>
            <template v-else>{{ t("hero.liveLoading") }}</template>
          </p>
        </div>
        <div class="hero-art">
          <HeroArt />
        </div>
      </div>
    </section>

    <section class="container">
      <p class="positioning reveal">{{ t("hero.positioning") }}</p>
    </section>

    <!-- PROBLEM -->
    <section class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">Raqib</span>
        <h2>{{ t("problem.title") }}</h2>
        <p>{{ t("problem.subtitle") }}</p>
      </div>
      <div class="timeline">
        <div class="timeline-spine"></div>
        <div v-for="(p, i) in problems" :key="p" class="tl-item reveal" :style="{ '--i': i }">
          <div class="tl-node"><Icon :name="problemIcons[p]" /></div>
          <div class="tl-card">
            <span class="tl-step">{{ String(i + 1).padStart(2, "0") }}</span>
            <h3>{{ t(`problem.cards.${p}.title`) }}</h3>
            <p>{{ t(`problem.cards.${p}.text`) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- AVAILABLE NOW: the channel -->
    <section id="now" class="container section">
      <div class="section-head reveal">
        <span class="eyebrow">{{ t("now.eyebrow") }}</span>
        <h2>{{ t("now.title") }}</h2>
        <p>{{ t("now.subtitle") }}</p>
      </div>
      <div class="tg-wrap">
        <div class="tg-phone reveal">
          <div class="tg-header">
            <div class="tg-avatar"><img src="/favicon.svg" alt="Raqib" /></div>
            <div>
              <div class="tg-name">Raqib | Concours &amp; Emploi Public</div>
              <div class="tg-status">@RaqibEmploi</div>
            </div>
          </div>
          <div class="tg-chat" dir="rtl">
            <div class="tg-msg">
              <div class="tg-bubble tg-bubble--new">
                <div class="alert-head alert-head--new">🟢 {{ t("journey.demoNew") }}</div>
                <div class="tg-row"><span class="v">🏛 {{ t("journey.demoAdmin") }}</span></div>
                <div class="tg-row"><span class="v">💼 {{ t("journey.demoGrade") }}</span></div>
                <div class="tg-row"><span class="v">👥 {{ t("journey.demoPosts") }}</span></div>
                <div class="tg-row"><span class="v">⏳ {{ t("journey.demoDeadline") }}</span></div>
                <div class="tg-row"><span class="v demo-tags">#صحة #مباراة #الرباط</span></div>
                <div class="tg-buttons">
                  <button class="tg-btn tg-btn--accent">{{ t("journey.demoDetails") }}</button>
                  <button class="tg-btn">{{ t("journey.demoShare") }}</button>
                </div>
                <div class="tg-time">09:02</div>
              </div>
            </div>
            <div class="tg-msg">
              <div class="tg-bubble tg-bubble--alert">
                <div class="alert-head">📋 {{ t("journey.demoConv") }}</div>
                <div class="tg-row"><span class="v">🏛 {{ t("journey.demoAdmin") }}</span></div>
                <div class="tg-row"><span class="v">📅 {{ t("journey.demoExam") }}</span></div>
                <div class="tg-buttons">
                  <button class="tg-btn tg-btn--accent">{{ t("journey.demoList") }}</button>
                </div>
                <div class="tg-time">08:14</div>
              </div>
            </div>
          </div>
        </div>
        <div class="tg-side">
          <div v-for="(p, i) in nowPoints" :key="p" class="pcard reveal" :style="{ '--i': i }">
            <div class="ic-chip"><Icon :name="nowIcons[p]" /></div>
            <h3>{{ t(`now.points.${p}.title`) }}</h3>
            <p>{{ t(`now.points.${p}.text`) }}</p>
          </div>
        </div>
      </div>

      <div class="section-head reveal" style="margin-top: 56px">
        <h2 style="font-size: 26px">{{ t("journey.title") }}</h2>
        <p>{{ t("journey.subtitle") }}</p>
      </div>
      <div class="journey reveal">
        <div v-for="s in STAGES" :key="s" class="journey-step">
          <StageBadge :stage="s" />
        </div>
      </div>
      <div class="cta-row" style="justify-content: center; margin-top: 28px">
        <a :href="channelUrl" target="_blank" rel="noopener" class="btn btn-primary">✈️ {{ t("hero.ctaPrimary") }}</a>
      </div>
    </section>

    <!-- SOURCES -->
    <section class="container section">
      <div class="section-head reveal">
        <h2>{{ t("sources.title") }}</h2>
        <p>{{ t("sources.subtitle") }}</p>
      </div>
      <div class="src-groups">
        <div class="src-group reveal">
          <div class="src-group-head"><span class="dot ok"></span>{{ t("sources.live") }}</div>
          <div class="src-logos">
            <div class="src-tile"><BrandLogo name="emploi" /><span>emploi-public.ma</span></div>
          </div>
          <p class="src-note">{{ t("sources.liveText") }}</p>
        </div>
        <div class="src-group reveal" style="--i: 1">
          <div class="src-group-head"><span class="dot"></span>{{ t("sources.soon") }}</div>
          <p class="src-note">{{ t("sources.soonText") }}</p>
        </div>
      </div>
    </section>

    <!-- FUTURE: the personal assistant -->
    <section class="container section">
      <div class="ai-band reveal">
        <div class="ai-head">
          <span class="badge-pill">✨ {{ t("future.badge") }}</span>
          <h2>{{ t("future.title") }}</h2>
          <p>{{ t("future.subtitle") }}</p>
        </div>
        <div class="built-grid future-grid" style="margin-top: 28px">
          <div v-for="(p, i) in futurePoints" :key="p" class="pcard reveal" :style="{ '--i': i }">
            <div class="ic-chip"><Icon :name="futureIcons[p]" /></div>
            <h3>{{ t(`future.points.${p}.title`) }} <span class="soon-tag">{{ t("future.badge") }}</span></h3>
            <p>{{ t(`future.points.${p}.text`) }}</p>
          </div>
        </div>

        <div class="section-head" style="margin-top: 40px">
          <h3 style="margin: 0 0 6px">{{ t("future.previewTitle") }}</h3>
          <p>{{ t("future.previewSubtitle") }}</p>
        </div>
        <div class="tg-wrap preview-wrap">
          <div class="tg-phone">
            <div class="tg-header">
              <div class="tg-avatar"><img src="/favicon.svg" alt="Raqib" /></div>
              <div>
                <div class="tg-name">Raqib · رقيب</div>
                <div class="tg-status">bot · {{ t("future.badge") }}</div>
              </div>
            </div>
            <div class="tg-chat">
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
                </div>
              </div>
              <div class="tg-note">{{ t("convocation.trackedBadge") }}</div>
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
                </div>
              </div>
            </div>
          </div>
        </div>
        <p class="ai-note">{{ t("future.note") }}</p>
      </div>
    </section>

    <!-- BUILT -->
    <section class="container section">
      <div class="section-head reveal">
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
