// Starter list of insults to remove from the discussion group.
// Edit freely: add the words you see in the group, one string per entry.
// Entries can be written in any spelling, they are normalised the same way as messages
// (lowercase, no accents or Arabic diacritics, alef and ya variants merged, repeated
// letters collapsed). Entries with a space are matched as whole phrases.
// Do not add words that are also names or normal words (for example the surname of a
// public figure), a false positive deletes an innocent message.

export const BAD_WORDS = [
  // Arabic and Darija
  "زب", "زبي", "طبون", "قحبة", "كحبة", "شرموطة", "عاهرة", "منيوك", "منيك",
  "نيكمك", "نيك امك", "كسمك", "كسامك", "زامل", "ولد القحبة", "ولاد القحبة",
  "ابن الكلب", "ولد الكلب", "ولد الحرام", "ابن الحرام",
  // Darija written in latin letters
  "9a7ba", "9ahba", "qahba", "kahba", "zebi", "zamel", "nikmok", "nikomok",
  "kosomok", "ksomk", "mnayk", "mnaik", "ould l9a7ba", "wld l9a7ba",
  // French
  "putain", "pute", "salope", "connard", "connasse", "encule", "enculer",
  "nique", "niquer", "ntm", "fdp", "batard", "fils de pute", "va te faire foutre",
  // English
  "fuck", "fucker", "shit", "bitch", "asshole",
];
