/**
 * Le contrat, et le garde-fou qui l'oppose au texte produit.
 *
 * CE FICHIER EST UN JUMEAU. La même règle tourne en Python dans le moteur
 * (site/generateur/architecte.py). Elle est ici parce que la cheffe écrit
 * en DIRECT dans le chat : filtrer seulement au moment de construire la
 * page laisserait passer, à l'écran, une phrase que le moteur refusera
 * ensuite — et l'utilisateur aurait raison de ne plus rien y comprendre.
 *
 * Deux implémentations qui jugent la même chose divergent toujours. Les
 * deux répondent donc au MÊME questionnaire :
 *   site/generateur/vecteurs-faits.json
 * Ajouter un cas là-bas le rend obligatoire des deux côtés.
 *
 * CE QUE LE GARDE-FOU FAIT. Un modèle à qui on demande la page d'un
 * transporteur écrira « vingt ans d'expérience », « certifiés ISO 9001 » et
 * un numéro de téléphone. Tout sera crédible, tout sera faux, et meilleur
 * est le modèle plus c'est crédible. Ce n'est pas un défaut de
 * raisonnement : compléter est son métier. On ne le corrige donc pas en le
 * lui demandant gentiment — on vérifie.
 */

export type Origine = "registre" | "client" | "mesure" | "choix";

export interface Fait {
  cle: string;
  valeur: string | null;
  origine: Origine | null;
  source?: string | null;
  releve_le?: string | null;
}

export interface Invention {
  quoi: string;
  extrait: string;
}

/* ------------------------------------------------------- ce qui est un fait */

/** Chaque motif porte son nom : un refus doit dire CE QU'il a trouvé. */
const MOTIFS: [string, RegExp][] = [
  ["un courriel", /[\w.+-]+@[\w-]+\.[\w.]+/gi],
  ["un site", /\b(?:https?:\/\/|www\.)\S+/gi],
  ["un téléphone", /(?:\+33|\b0)[\s.\-]?[1-9](?:[\s.\-]?\d{2}){4}\b/gi],
  ["un identifiant", /\b\d[\d\s.\-]{7,}\d\b/gi],
  ["une année", /\b(?:19|20)\d{2}\b/gi],
  ["une certification", /\b(?:ISO|NF|AFNOR|QUALIMAT|IFS|BRC|OEA)[\s-]?\d*\b/gi],
  // Le séparateur de milliers fait partie du nombre : sans lui « 1 152 »
  // se lit « 1 » puis « 152 », et ni l'un ni l'autre ne se retrouve dans un
  // contrat qui déclare pourtant 1152.
  ["un chiffre", /\b\d{1,3}(?:[\s  ]\d{3})+\b|\b\d+(?:[.,]\d+)?\s*(?:%|€|km|kg|t\b|m²|h\b|\/\d+)?/gi],
];

const DENOMBRABLES =
  "ans?|années?|camions?|véhicules?|poids\\s+lourds?|salariés?|employés?|" +
  "collaborateurs?|chauffeurs?|conducteurs?|clients?|agences?|sites?|" +
  "entrepôts?|générations?|tonnes?|hectares?|artisans?|compagnons?|ateliers?";

/**
 * Les nombres écrits en toutes lettres comptent autant.
 *
 * « un » et « une » n'y sont pas, délibérément : ce sont d'abord des
 * articles. « un atelier » n'avance rien, et le garde-fou qui le refusait
 * rendait impossible d'écrire une phrase française — un garde-fou qu'on ne
 * peut pas satisfaire finit débranché.
 */
const LETTRES = new RegExp(
  "\\b(?:deux|trois|quatre|cinq|six|sept|huit|neuf|dix|onze|douze|quinze|" +
  "vingt|trente|quarante|cinquante|soixante|cent|mille|dizaine|douzaine|" +
  "vingtaine|trentaine|quarantaine|cinquantaine|centaine|millier)s?\\s+" +
  "(?:de\\s+|d['’])?(?:" + DENOMBRABLES + ")\\b", "gi");

/** Au singulier, devant une DURÉE seulement, l'article redevient un fait. */
const LETTRES_DUREE =
  /\b(?:un|une)\s+(?:demi-)?(?:an|année|génération|siècle|décennie)\b/gi;

/**
 * Un nombre nu ne se juge pas, son unité si. « 45 chauffeurs » passait
 * parce que 45 figure dans « 45 rue Jean Charcot ». On cherche donc le
 * nombre AVEC ce qu'il compte : « 45 rue » est déclaré, « 45 chauffeurs »
 * ne l'est pas.
 *
 * UNE ANNÉE N'EST PAS UN COMPTE. « © 2026 Atelier Martin » se lisait
 * « 2026 ateliers » — un millésime suivi du nom de la marque. Les années
 * sont donc exclues ici ; elles restent jugées par le motif « une année ».
 * Ce qui subsiste comme angle mort : « 1998 clients » passerait si 1998
 * était déjà déclaré comme date de création. On l'accepte — un faux positif
 * sur chaque bas de page ferait débrancher le garde-fou, ce qui coûterait
 * bien plus cher.
 */
const CHIFFRE_UNITE = new RegExp(
  "\\b(?!(?:19|20)\\d{2}\\b)\\d+\\s+(?:de\\s+|d['’])?(?:" + DENOMBRABLES + ")\\b",
  "gi");

/** Ce qui ressemble à un chiffre sans en être un. */
const INNOCENTS = /^(?:un|une|des|de|d|le|la|les)$/i;

const nu = (s: string) =>
  s.normalize("NFD").replace(/\p{Mn}/gu, "").toLowerCase();

/* ------------------------------------------------------ ce qui est autorisé */

/**
 * Tout ce que le contrat autorise à écrire. Rien de plus.
 *
 * Une valeur nulle n'entre pas : un fait sans source est une question
 * ouverte, pas une permission. L'année en cours entre, elle : c'est la
 * mention de copyright du bas de page, un fait sur aujourd'hui et non sur
 * le client — la déclarer dans chaque contrat obligerait à la corriger le
 * 1er janvier, ce qui est exactement la constante qui se périme en silence.
 */
export function faitsDeclares(faits: Fait[], extra: string[] = []): Set<string> {
  const permis = new Set<string>([String(new Date().getFullYear())]);
  for (const f of faits) if (f.valeur != null) permis.add(nu(String(f.valeur)));
  for (const e of extra) if (e) permis.add(nu(e));
  return permis;
}

function autorise(trouve: string, permis: Set<string>): boolean {
  const t = nu(trouve).trim();
  if (!t || INNOCENTS.test(t)) return true;
  const chiffres = t.replace(/[^\p{L}\p{N}]/gu, "");
  for (const p of permis) {
    if (p.includes(t)) return true;
    if (chiffres && p.replace(/[^\p{L}\p{N}]/gu, "").includes(chiffres)) return true;
  }
  return false;
}

/**
 * Les faits présents dans le texte et absents du contrat.
 * Vide = le texte n'avance rien qu'on ne puisse justifier.
 */
export function inventions(texte: string, permis: Set<string>): Invention[] {
  const trouves: Invention[] = [];
  const passer = (quoi: string, motif: RegExp) => {
    for (const m of texte.matchAll(motif)) {
      const brut = m[0].trim();
      if (!autorise(brut, permis)) trouves.push({ quoi, extrait: brut });
    }
  };
  for (const [quoi, motif] of MOTIFS) passer(quoi, motif);
  passer("une quantité", CHIFFRE_UNITE);
  passer("une quantité", LETTRES);
  passer("une durée", LETTRES_DUREE);

  // Un même intrus répété ne compte qu'une fois.
  const vus = new Set<string>();
  return trouves.filter(({ extrait }) => {
    const k = nu(extrait);
    if (vus.has(k)) return false;
    vus.add(k);
    return true;
  });
}

/* ------------------------------------------------------------- le verdict */

export class Refus extends Error {
  // Déclarée à part plutôt qu'en propriété de constructeur : le dépouillage
  // de types de Node refuse cette forme-là, et les épreuves tournent sans
  // étape de compilation.
  trouves: Invention[];
  constructor(message: string, trouves: Invention[] = []) {
    super(message);
    this.name = "Refus";
    this.trouves = trouves;
  }
}

/**
 * Passe un texte au garde-fou. Lève si le texte avance un fait non déclaré.
 * Ne CORRIGE jamais : corriger reviendrait à ne plus savoir ce que le
 * modèle a réellement écrit, et le contrôle deviendrait une politesse.
 */
export function verifierTexte(texte: string, faits: Fait[], extra: string[] = []) {
  const trouves = inventions(texte, faitsDeclares(faits, extra));
  if (trouves.length) {
    throw new Refus(
      `${trouves.length} fait(s) non déclaré(s) : ` +
      trouves.map((t) => `${t.quoi} « ${t.extrait} »`).join(", "),
      trouves,
    );
  }
}

/** Les clés dont la valeur manque encore : les questions ouvertes. */
export const questionsOuvertes = (faits: Fait[]) =>
  faits.filter((f) => f.valeur == null).map((f) => f.cle);
