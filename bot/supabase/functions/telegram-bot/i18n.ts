// Bilingual (FR / AR) message catalog for the Raqib bot.
// Usage: t(locale, "menu.title") or t(locale, "welcome.hi", { name: "Amine" }).

export type Locale = "fr" | "ar";

type Dict = Record<string, string>;

const FR: Dict = {
  // --- welcome / start ---
  "welcome.caption":
    "👁️ <b>Raqib · رقيب</b>\nVotre veilleur des concours publics marocains.",
  "welcome.intro":
    "👋 Bienvenue sur <b>Raqib</b> !\n\n" +
    "Je surveille les portails officiels, les ministères et les canaux communautaires, " +
    "et je vous alerte :\n" +
    "1️⃣ dès qu'un <b>nouveau concours</b> correspond à votre profil (à temps pour déposer),\n" +
    "2️⃣ puis dès que votre <b>CIN</b> apparaît sur une liste de <b>convoqués</b>.\n\n" +
    "Commençons par configurer votre profil.",
  "welcome.back": "👋 Content de vous revoir ! Que souhaitez-vous faire ?",

  // --- main menu ---
  "menu.title": "🏠 <b>Menu principal</b>\nQue souhaitez-vous faire ?",
  "menu.profile": "👤 Mon profil",
  "menu.tracked": "📌 Mes concours suivis",
  "menu.settings": "⚙️ Paramètres",
  "menu.help": "❓ Aide",
  "menu.language": "🌐 Langue",
  "menu.admin": "🛠️ Administration",
  "menu.back": "⬅️ Retour au menu",

  // --- onboarding ---
  "onb.askNameFr": "🖊 Quel est votre <b>nom complet</b> (en français) ?",
  "onb.askNameAr": "🖊 Votre nom complet <b>en arabe</b> ? (ou tapez « - » pour ignorer)",
  "onb.askCin": "🪪 Votre <b>CIN</b> (ex : AB123456) ? Elle sera chiffrée et jamais partagée.",
  "onb.askGrade": "🎯 Choisissez votre <b>grade cible</b> :",
  "onb.askSpecialty": "🧩 Choisissez votre/vos <b>spécialité(s)</b>, puis Terminer :",
  "onb.done": "✅ <b>Profil configuré !</b>",
  "onb.finish": "➡️ Terminer",

  // --- profile ---
  "profile.title": "👤 <b>Votre profil</b>",
  "profile.nameFr": "Nom (FR)",
  "profile.nameAr": "Nom (AR)",
  "profile.cin": "CIN",
  "profile.grades": "Grades",
  "profile.specialties": "Spécialités",
  "profile.editName": "✏️ Modifier le nom",
  "profile.editCin": "✏️ Modifier la CIN",
  "profile.editGrades": "✏️ Modifier les grades",
  "profile.editSpecialties": "✏️ Modifier les spécialités",
  "profile.none": "—",

  // --- settings ---
  "settings.title": "⚙️ <b>Paramètres</b>",
  "settings.language": "🌐 Langue : {value}",
  "settings.offTarget": "🔎 Inclure hors-profil : {value}",
  "settings.offTargetHint":
    "Inclure Technicien / génie civil, etc. (par défaut : non)",
  "settings.pause": "⏸️ Alertes : {value}",
  "settings.paused": "en pause",
  "settings.active": "actives",
  "settings.quiet": "🌙 Heures silencieuses : {value}",
  "settings.quietOff": "désactivées",
  "settings.setQuiet": "🌙 Définir les heures silencieuses",
  "settings.deleteData": "🗑️ Supprimer mes données",
  "settings.on": "activé",
  "settings.off": "désactivé",
  "settings.saved": "✅ Enregistré.",
  "settings.pausedMsg": "⏸️ Vos alertes sont en pause. Réactivez-les quand vous voulez.",
  "settings.resumedMsg": "▶️ Vos alertes sont réactivées.",
  "settings.quietPrompt":
    "🌙 Envoyez la plage d'heures silencieuses au format <code>22-7</code> " +
    "(pas de notifications entre 22h et 7h). Envoyez <code>off</code> pour désactiver.",
  "settings.quietSet": "🌙 Heures silencieuses : {value}",
  "settings.deleteConfirm":
    "⚠️ Cela supprimera définitivement votre profil, votre CIN chiffrée et vos suivis. Confirmer ?",
  "settings.deleteYes": "🗑️ Oui, tout supprimer",
  "settings.deleteNo": "Annuler",
  "settings.deleted": "🗑️ Vos données ont été supprimées. Tapez /start pour recommencer.",

  // --- language ---
  "lang.title": "🌐 Choisissez votre langue :",
  "lang.set": "✅ Langue définie : Français",

  // --- tracked ---
  "tracked.title": "📌 <b>Vos concours suivis</b>",
  "tracked.empty": "Vous ne suivez aucun concours pour l'instant.",
  "tracked.state.APPLIED": "Dossier déposé",
  "tracked.state.EN_ATTENTE_CONVOCATION": "En attente de convocation",
  "tracked.state.CONVOQUE": "Convoqué ✅",
  "tracked.state.RESULTAT": "Résultats disponibles",
  "tracked.added": "📌 Ajouté à votre suivi. Je vous alerte dès la convocation ou les résultats.",

  // --- help ---
  "help.title": "❓ <b>Aide — Raqib</b>",
  "help.body":
    "Raqib surveille les concours publics et vous alerte à temps.\n\n" +
    "• /menu — menu principal\n" +
    "• /profil — voir / modifier votre profil\n" +
    "• /parametres — langue, pause, heures silencieuses…\n" +
    "• /mes_concours — vos concours suivis\n" +
    "• /langue — changer de langue\n\n" +
    "🔒 Votre CIN est chiffrée et n'est jamais partagée.",

  // --- admin ---
  "admin.title": "🛠️ <b>Administration</b>",
  "admin.denied": "⛔ Accès réservé au propriétaire.",
  "admin.stats": "📊 Statistiques",
  "admin.broadcast": "📣 Diffuser un message",
  "admin.statsBody":
    "👥 Utilisateurs : <b>{users}</b>\n" +
    "✅ Profils complets : <b>{profiles}</b>\n" +
    "📚 Concours : <b>{competitions}</b>\n" +
    "📌 Suivis actifs : <b>{tracked}</b>\n" +
    "🔌 Sources saines : <b>{sources}</b>",
  "admin.broadcastPrompt": "📣 Envoyez le message à diffuser à tous les utilisateurs :",
  "admin.broadcastSent": "📣 Message diffusé à {count} utilisateur(s).",

  // --- misc ---
  "common.unknown": "Utilisez /menu pour voir les options disponibles.",
  "common.cancelled": "Annulé.",
};

const AR: Dict = {
  "welcome.caption":
    "👁️ <b>رقيب · Raqib</b>\nرقيبك في المباريات العمومية بالمغرب.",
  "welcome.intro":
    "👋 مرحبًا بك في <b>رقيب</b> !\n\n" +
    "أراقب البوابات الرسمية والوزارات والقنوات المجتمعية، وأنبّهك:\n" +
    "1️⃣ فور صدور <b>مباراة جديدة</b> تناسب ملفك (في الوقت المناسب للترشيح)،\n" +
    "2️⃣ ثم فور ظهور <b>رقم بطاقتك الوطنية</b> في لائحة <b>المدعوين</b>.\n\n" +
    "لنبدأ بضبط ملفك الشخصي.",
  "welcome.back": "👋 سعيد بعودتك! ماذا تريد أن تفعل؟",

  "menu.title": "🏠 <b>القائمة الرئيسية</b>\nماذا تريد أن تفعل؟",
  "menu.profile": "👤 ملفي",
  "menu.tracked": "📌 مبارياتي المتابَعة",
  "menu.settings": "⚙️ الإعدادات",
  "menu.help": "❓ مساعدة",
  "menu.language": "🌐 اللغة",
  "menu.admin": "🛠️ الإدارة",
  "menu.back": "⬅️ العودة إلى القائمة",

  "onb.askNameFr": "🖊 ما اسمك الكامل (بالفرنسية)؟",
  "onb.askNameAr": "🖊 اسمك الكامل <b>بالعربية</b>؟ (أو اكتب « - » لتجاوزه)",
  "onb.askCin": "🪪 رقم بطاقتك الوطنية (مثال: AB123456)؟ سيُشفَّر ولن يُشارَك أبدًا.",
  "onb.askGrade": "🎯 اختر <b>الدرجة المستهدفة</b>:",
  "onb.askSpecialty": "🧩 اختر <b>تخصصك/تخصصاتك</b>، ثم أنهِ:",
  "onb.done": "✅ <b>تم ضبط ملفك!</b>",
  "onb.finish": "➡️ إنهاء",

  "profile.title": "👤 <b>ملفك الشخصي</b>",
  "profile.nameFr": "الاسم (فرنسية)",
  "profile.nameAr": "الاسم (عربية)",
  "profile.cin": "رقم البطاقة",
  "profile.grades": "الدرجات",
  "profile.specialties": "التخصصات",
  "profile.editName": "✏️ تعديل الاسم",
  "profile.editCin": "✏️ تعديل رقم البطاقة",
  "profile.editGrades": "✏️ تعديل الدرجات",
  "profile.editSpecialties": "✏️ تعديل التخصصات",
  "profile.none": "—",

  "settings.title": "⚙️ <b>الإعدادات</b>",
  "settings.language": "🌐 اللغة: {value}",
  "settings.offTarget": "🔎 تضمين خارج الملف: {value}",
  "settings.offTargetHint": "تضمين تقني / هندسة مدنية… (افتراضيًا: لا)",
  "settings.pause": "⏸️ التنبيهات: {value}",
  "settings.paused": "متوقفة",
  "settings.active": "نشطة",
  "settings.quiet": "🌙 ساعات الهدوء: {value}",
  "settings.quietOff": "معطّلة",
  "settings.setQuiet": "🌙 تحديد ساعات الهدوء",
  "settings.deleteData": "🗑️ حذف بياناتي",
  "settings.on": "مفعّل",
  "settings.off": "معطّل",
  "settings.saved": "✅ تم الحفظ.",
  "settings.pausedMsg": "⏸️ تم إيقاف تنبيهاتك مؤقتًا. أعد تفعيلها متى شئت.",
  "settings.resumedMsg": "▶️ تمت إعادة تفعيل تنبيهاتك.",
  "settings.quietPrompt":
    "🌙 أرسل نطاق ساعات الهدوء بالشكل <code>22-7</code> " +
    "(لا إشعارات بين 22 و7). أرسل <code>off</code> للتعطيل.",
  "settings.quietSet": "🌙 ساعات الهدوء: {value}",
  "settings.deleteConfirm":
    "⚠️ سيؤدي هذا إلى حذف ملفك ورقم بطاقتك المشفّر ومتابعاتك نهائيًا. هل تؤكد؟",
  "settings.deleteYes": "🗑️ نعم، احذف كل شيء",
  "settings.deleteNo": "إلغاء",
  "settings.deleted": "🗑️ تم حذف بياناتك. اكتب /start للبدء من جديد.",

  "lang.title": "🌐 اختر لغتك:",
  "lang.set": "✅ تم تعيين اللغة: العربية",

  "tracked.title": "📌 <b>مبارياتك المتابَعة</b>",
  "tracked.empty": "لا تتابع أي مباراة حاليًا.",
  "tracked.state.APPLIED": "تم إيداع الملف",
  "tracked.state.EN_ATTENTE_CONVOCATION": "في انتظار الاستدعاء",
  "tracked.state.CONVOQUE": "مدعو ✅",
  "tracked.state.RESULTAT": "النتائج متاحة",
  "tracked.added": "📌 تمت الإضافة إلى متابعتك. سأنبّهك فور صدور الاستدعاء أو النتائج.",

  "help.title": "❓ <b>مساعدة — رقيب</b>",
  "help.body":
    "رقيب يراقب المباريات العمومية وينبّهك في الوقت المناسب.\n\n" +
    "• /menu — القائمة الرئيسية\n" +
    "• /profil — عرض / تعديل ملفك\n" +
    "• /parametres — اللغة، الإيقاف، ساعات الهدوء…\n" +
    "• /mes_concours — مبارياتك المتابَعة\n" +
    "• /langue — تغيير اللغة\n\n" +
    "🔒 رقم بطاقتك مشفّر ولا يُشارَك أبدًا.",

  "admin.title": "🛠️ <b>الإدارة</b>",
  "admin.denied": "⛔ الوصول مخصص للمالك.",
  "admin.stats": "📊 الإحصائيات",
  "admin.broadcast": "📣 بث رسالة",
  "admin.statsBody":
    "👥 المستخدمون: <b>{users}</b>\n" +
    "✅ الملفات المكتملة: <b>{profiles}</b>\n" +
    "📚 المباريات: <b>{competitions}</b>\n" +
    "📌 المتابعات النشطة: <b>{tracked}</b>\n" +
    "🔌 المصادر السليمة: <b>{sources}</b>",
  "admin.broadcastPrompt": "📣 أرسل الرسالة المراد بثّها لجميع المستخدمين:",
  "admin.broadcastSent": "📣 تم بث الرسالة إلى {count} مستخدم.",

  "common.unknown": "استخدم /menu لعرض الخيارات المتاحة.",
  "common.cancelled": "أُلغي.",
};

const CATALOG: Record<Locale, Dict> = { fr: FR, ar: AR };

export function t(locale: Locale, key: string, vars?: Record<string, string | number>): string {
  const dict = CATALOG[locale] ?? FR;
  let s = dict[key] ?? FR[key] ?? key;
  if (vars) {
    for (const [k, v] of Object.entries(vars)) {
      s = s.replaceAll(`{${k}}`, String(v));
    }
  }
  return s;
}

export function normalizeLocale(v: string | null | undefined): Locale {
  return v === "ar" ? "ar" : "fr";
}
