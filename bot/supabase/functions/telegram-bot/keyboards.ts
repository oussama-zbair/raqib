// Inline keyboard builders for the Raqib bot.

import type { InlineButton } from "./telegram.ts";
import { t, type Locale } from "./i18n.ts";
import { GRADE_OPTIONS, SPECIALTY_OPTIONS } from "./taxonomy.ts";
import type { ProfileRow } from "./db.ts";

export function mainMenu(locale: Locale, isOwner: boolean): InlineButton[][] {
  const rows: InlineButton[][] = [
    [{ text: t(locale, "menu.profile"), callback_data: "profile" }],
    [{ text: t(locale, "menu.tracked"), callback_data: "tracked" }],
    [{ text: t(locale, "menu.settings"), callback_data: "settings" }],
    [
      { text: t(locale, "menu.language"), callback_data: "language" },
      { text: t(locale, "menu.help"), callback_data: "help" },
    ],
  ];
  if (isOwner) rows.push([{ text: t(locale, "menu.admin"), callback_data: "admin" }]);
  return rows;
}

export function backRow(locale: Locale): InlineButton[] {
  return [{ text: t(locale, "menu.back"), callback_data: "menu" }];
}

export function gradeButtons(locale: Locale): InlineButton[][] {
  const rows = GRADE_OPTIONS.map((o) => [
    { text: o.labelFr, callback_data: `grade:${o.key}` },
  ]);
  return rows;
}

export function specialtyButtons(selected: string[]): InlineButton[][] {
  const rows = SPECIALTY_OPTIONS.map((o) => [{
    text: (selected.includes(o.key) ? "✅ " : "▫️ ") + o.labelFr,
    callback_data: `spec:${o.key}`,
  }]);
  return rows;
}

export function specialtyKeyboard(locale: Locale, selected: string[]): InlineButton[][] {
  const rows = specialtyButtons(selected);
  rows.push([{ text: t(locale, "onb.finish"), callback_data: "spec_done" }]);
  return rows;
}

export function profileMenu(locale: Locale): InlineButton[][] {
  return [
    [{ text: t(locale, "profile.editName"), callback_data: "edit_name" }],
    [{ text: t(locale, "profile.editCin"), callback_data: "edit_cin" }],
    [{ text: t(locale, "profile.editGrades"), callback_data: "edit_grades" }],
    [{ text: t(locale, "profile.editSpecialties"), callback_data: "edit_specialties" }],
    backRow(locale),
  ];
}

export function settingsMenu(locale: Locale, p: ProfileRow): InlineButton[][] {
  const quiet =
    p.quiet_start != null && p.quiet_end != null
      ? `${p.quiet_start}h–${p.quiet_end}h`
      : t(locale, "settings.quietOff");
  return [
    [{
      text: t(locale, "settings.offTarget", {
        value: p.include_off_target ? t(locale, "settings.on") : t(locale, "settings.off"),
      }),
      callback_data: "toggle_offtarget",
    }],
    [{
      text: t(locale, "settings.pause", {
        value: p.paused ? t(locale, "settings.paused") : t(locale, "settings.active"),
      }),
      callback_data: "toggle_pause",
    }],
    [{ text: t(locale, "settings.quiet", { value: quiet }), callback_data: "set_quiet" }],
    [{ text: t(locale, "menu.language"), callback_data: "language" }],
    [{ text: t(locale, "settings.deleteData"), callback_data: "delete_data" }],
    backRow(locale),
  ];
}

export function languageMenu(): InlineButton[][] {
  return [
    [{ text: "🇫🇷 Français", callback_data: "setlang:fr" }],
    [{ text: "🇲🇦 العربية", callback_data: "setlang:ar" }],
  ];
}

export function confirmDelete(locale: Locale): InlineButton[][] {
  return [
    [{ text: t(locale, "settings.deleteYes"), callback_data: "delete_confirm" }],
    [{ text: t(locale, "settings.deleteNo"), callback_data: "settings" }],
  ];
}

export function adminMenu(locale: Locale): InlineButton[][] {
  return [
    [{ text: t(locale, "admin.stats"), callback_data: "admin_stats" }],
    [{ text: t(locale, "admin.broadcast"), callback_data: "admin_broadcast" }],
    backRow(locale),
  ];
}
