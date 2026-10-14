<template>
  <!-- Story: noisy scattered sources (left) -> Raqib's eye filters -> one clean alert (right) -->
  <svg viewBox="0 0 560 460" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Raqib filtre le bruit des sources et vous alerte">
    <defs>
      <linearGradient id="hgGreen" x1="0" y1="0" x2="1" y2="1">
        <stop stop-color="#5EEAD4" /><stop offset="1" stop-color="#2563EB" />
      </linearGradient>
      <radialGradient id="hgEye" cx="0.5" cy="0.45" r="0.6">
        <stop stop-color="#F8CE6B" /><stop offset="1" stop-color="#F4B740" />
      </radialGradient>
      <filter id="hgGlow" x="-50%" y="-50%" width="200%" height="200%">
        <feGaussianBlur stdDeviation="8" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
      </filter>
    </defs>

    <!-- noisy source nodes on the left -->
    <g opacity="0.9">
      <g v-for="(n, i) in noise" :key="i">
        <line :x1="n.x + 22" :y1="n.y + 14" x2="248" y2="230" stroke="#26324d" stroke-width="1.5" stroke-dasharray="3 4" />
        <rect :x="n.x" :y="n.y" width="86" height="30" rx="8" fill="#16233b" stroke="#26324d" />
        <circle :cx="n.x + 14" :cy="n.y + 15" r="5" :fill="n.c" />
        <rect :x="n.x + 26" :y="n.y + 9" width="48" height="4" rx="2" fill="#3a4a68" />
        <rect :x="n.x + 26" :y="n.y + 18" width="34" height="4" rx="2" fill="#2c3a56" />
      </g>
    </g>

    <!-- Raqib eye (khatam star) in the center as the filter -->
    <g transform="translate(248 230)" filter="url(#hgGlow)">
      <g fill="url(#hgGreen)">
        <rect x="-58" y="-58" width="116" height="116" rx="14" />
        <rect x="-58" y="-58" width="116" height="116" rx="14" transform="rotate(45)" />
      </g>
      <path d="M -52 0 C -24 -30, 24 -30, 52 0 C 24 30, -24 30, -52 0 Z" fill="#0B1220" />
      <path d="M -44 0 C -20 -25, 20 -25, 44 0 C 20 25, -20 25, -44 0 Z" fill="#E8EDF7" />
      <circle class="rq-scan" cx="0" cy="0" r="20" fill="url(#hgEye)" />
      <circle cx="0" cy="0" r="9" fill="#0B1220" />
      <circle cx="5" cy="-5" r="3.4" fill="#E8EDF7" opacity="0.9" />
    </g>

    <!-- single clean beam to the alert -->
    <path d="M 306 230 C 360 230, 380 180, 430 150" stroke="url(#hgGreen)" stroke-width="3" fill="none" />
    <path d="M 306 230 C 360 230, 380 280, 430 310" stroke="#26324d" stroke-width="2" fill="none" stroke-dasharray="4 5" />

    <!-- the alert card (the one that matters) -->
    <g transform="translate(400 96)">
      <rect x="0" y="0" width="150" height="108" rx="12" fill="#14233a" stroke="#22d3a8" />
      <rect x="0" y="0" width="4" height="108" rx="2" fill="#f43f5e" />
      <circle cx="20" cy="20" r="7" fill="#f43f5e" />
      <rect x="34" y="15" width="96" height="6" rx="3" fill="#F4B740" />
      <rect x="14" y="40" width="120" height="5" rx="2.5" fill="#3a4a68" />
      <rect x="14" y="54" width="104" height="5" rx="2.5" fill="#3a4a68" />
      <rect x="14" y="68" width="70" height="5" rx="2.5" fill="#2c3a56" />
      <rect x="14" y="86" width="60" height="12" rx="6" fill="rgba(34,211,168,0.25)" stroke="#22d3a8" />
    </g>

    <!-- rejected/off-target node (dimmed, X) -->
    <g transform="translate(408 300)" opacity="0.55">
      <rect x="0" y="0" width="150" height="60" rx="12" fill="#101a2c" stroke="#26324d" />
      <path d="M 18 22 l 16 16 M 34 22 l -16 16" stroke="#D64545" stroke-width="2.4" stroke-linecap="round" />
      <rect x="48" y="22" width="86" height="5" rx="2.5" fill="#2c3a56" />
      <rect x="48" y="34" width="60" height="5" rx="2.5" fill="#22304a" />
    </g>
  </svg>
</template>

<script setup lang="ts">
// Scattered noisy sources feeding into the eye.
const noise = [
  { x: 6, y: 40, c: "#F4B740" },
  { x: 0, y: 110, c: "#3aa0ff" },
  { x: 14, y: 182, c: "#D64545" },
  { x: 4, y: 258, c: "#34d399" },
  { x: 22, y: 330, c: "#F4B740" },
  { x: 96, y: 80, c: "#3aa0ff" },
  { x: 104, y: 300, c: "#D64545" },
];
</script>
