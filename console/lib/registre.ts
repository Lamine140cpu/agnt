/**
 * Le registre des entreprises. Une frontière, comme les autres.
 *
 * POURQUOI CETTE FRONTIÈRE EXISTE. La cheffe ne doit jamais écrire un fait
 * sur le client sans source. Le registre est la meilleure source qui soit :
 * publique, opposable, et surtout — elle ne dépend pas de ce que le client
 * se rappelle. Un dirigeant qui dit « on a une vingtaine de camions » se
 * trompe de bonne foi ; le registre, non.
 *
 * CE FICHIER A ÉTÉ ÉCRIT À L'AVEUGLE, PUIS CORRIGÉ SUR PIÈCES. Le réseau de
 * l'environnement refusait ce domaine (503 au proxy) : la forme des champs
 * venait de la documentation, pas d'une réponse observée. L'appel passe
 * depuis le 25/08/2026 et la confrontation a montré trois choses que la
 * documentation ne disait pas, et qui auraient toutes fini sur la page d'un
 * client :
 *
 *   1. `nature_juridique` rend un CODE INSEE, pas un libellé. Le site aurait
 *      annoncé « société 5710 » au lieu de « SAS ».
 *   2. `siege.adresse` rend des CAPITALES sans ponctuation :
 *      « 45 RUE JEAN CHARCOT 93600 AULNAY-SOUS-BOIS ».
 *   3. `dirigeants` EXISTE. Le fichier affirmait que le directeur de la
 *      publication faisait partie de « ce que le registre ne saura jamais ».
 *      C'était vrai le jour où personne n'avait vu la réponse ; c'est faux
 *      depuis. Le représentant légal s'y lit, et c'est précisément lui que
 *      la LCEN désigne par défaut.
 *
 * La leçon vaut plus que les trois correctifs : une frontière décrite d'après
 * sa documentation n'est pas une frontière éprouvée. Tant qu'une réponse
 * réelle n'a pas été regardée, tout ce qui en est déduit est une hypothèse.
 */

export interface FaitRegistre {
  cle: string;
  valeur: string;
  source: string;
}

export interface Etablissement {
  faits: FaitRegistre[];
  /** Ce que le registre NE dit PAS, et qu'il faudra demander au client. */
  ouvertes: string[];
  brut: unknown;
}

export interface Registre {
  chercher(siren: string): Promise<Etablissement | null>;
}

const SOURCE = "recherche-entreprises.api.gouv.fr";

/**
 * Ce que le registre ne saura jamais, quoi qu'il arrive.
 *
 * Deux d'entre elles sont des obligations légales — sans elles, le site
 * n'est pas en règle. Les autres sont des faits que seul le client détient.
 * Elles ne sont pas des trous à combler : elles sont posées comme questions,
 * et la page n'affirme rien à leur sujet tant qu'elles sont ouvertes.
 *
 * `directeur_publication` N'Y EST PLUS : le registre le donne. Il reste
 * posé en question ouverte au cas par cas, quand le dirigeant est une
 * personne morale ou qu'aucune qualité ne désigne un représentant légal.
 */
export const HORS_REGISTRE = [
  "hebergeur",
  "courriel",
  "horaires",
  "assurance",
];

/**
 * Les catégories juridiques INSEE, réduites à ce qu'une PME peut être.
 *
 * DÉLIBÉRÉMENT INCOMPLÈTE, et c'est le point : un code absent de cette table
 * ne devient PAS un fait. Publier « société 5710 » serait une contrevérité
 * d'apparence sourcée — la pire espèce, puisqu'elle porte le nom du registre.
 * Un code inconnu pose donc une question ouverte, comme n'importe quel trou.
 */
const FORMES: Record<string, string> = {
  "1000": "entrepreneur individuel",
  "5202": "SNC",
  "5306": "société en commandite simple",
  "5410": "SARL",
  "5415": "SARL",
  "5426": "SARL",
  "5498": "SARL",
  "5499": "SARL",
  "5505": "SA",
  "5510": "SA",
  "5515": "SA",
  "5599": "SA",
  "5710": "SAS",
  "5720": "SASU",
  "5785": "société d'exercice libéral par actions simplifiée",
  "6540": "SCI",
  "6588": "société civile de moyens",
};

/**
 * Les qualités qui font d'un dirigeant le REPRÉSENTANT LÉGAL, par ordre de
 * préséance. C'est lui que la LCEN désigne comme directeur de la publication
 * à défaut de désignation expresse.
 *
 * L'ordre compte : Trans Gold a deux dirigeants, un directeur général et un
 * président. C'est le président qui représente la SAS.
 */
const REPRESENTANTS = [
  /président/i,
  /g[ée]rant/i,
  /directeur\s+g[ée]n[ée]ral/i,
];

/** « 45 RUE JEAN CHARCOT 93600 AULNAY-SOUS-BOIS » -> lisible. */
export function _adresse(brut: string): string {
  const petits = new Set([
    "de", "du", "des", "le", "la", "les", "sur", "sous", "en", "aux", "au",
    "et", "lès", "l", "d",
  ]);
  const mot = (m: string, i: number) => {
    const b = m.toLowerCase();
    if (i > 0 && petits.has(b)) return b;
    return b.charAt(0).toUpperCase() + b.slice(1);
  };
  const casse = (s: string) =>
    s
      .split(" ")
      .map((m, i) =>
        m
          .split("-")
          .map((p, j) => mot(p, i + j))
          .join("-"),
      )
      .join(" ");

  // Le type de voie reste en bas de casse : « 45 rue Jean Charcot », pas
  // « 45 Rue Jean Charcot ». C'est l'usage de l'adresse française.
  const VOIES =
    /^(\d+\s*(?:bis|ter|quater)?\s+)(rue|avenue|boulevard|impasse|allée|place|chemin|route|quai|cours|square|passage|voie|zone|rond-point)\b/i;

  const m = brut.trim().match(/^(.*?)\s+(\d{5})\s+(.*)$/);
  if (!m) return casse(brut.trim()).replace(VOIES, (_, n, v) => n + v.toLowerCase());
  const voie = casse(m[1]).replace(VOIES, (_, n, v) => n + v.toLowerCase());
  return `${voie}, ${m[2]} ${casse(m[3])}`;
}

/** Le représentant légal, s'il s'en trouve un qui soit une personne. */
export function _representant(
  dirigeants: unknown,
): { nom: string; qualite: string } | null {
  if (!Array.isArray(dirigeants)) return null;
  const gens = dirigeants.filter(
    (d): d is Record<string, unknown> =>
      !!d &&
      typeof d === "object" &&
      (d as Record<string, unknown>).type_dirigeant !== "personne morale" &&
      typeof (d as Record<string, unknown>).nom === "string",
  );
  for (const motif of REPRESENTANTS) {
    const un = gens.find((d) => motif.test(String(d.qualite ?? "")));
    if (!un) continue;
    const prenoms = String(un.prenoms ?? "").trim().split(/\s+/)[0] ?? "";
    const nom = String(un.nom ?? "").trim();
    if (!nom) continue;
    const jolie = (s: string) =>
      s
        .toLowerCase()
        .split(/([\s-])/)
        .map((p) => (/[\s-]/.test(p) ? p : p.charAt(0).toUpperCase() + p.slice(1)))
        .join("");
    return {
      nom: [jolie(prenoms), jolie(nom)].filter(Boolean).join(" "),
      qualite: String(un.qualite ?? "").trim(),
    };
  }
  return null;
}

/** Convertit une réponse du registre en faits sourcés. */
export function enFaits(r: Record<string, unknown>): Etablissement {
  const siege = (r.siege ?? {}) as Record<string, unknown>;
  const ouvertes = [...HORS_REGISTRE, "effectif"];

  const forme = FORMES[String(r.nature_juridique ?? "")];
  if (!forme && r.nature_juridique != null) ouvertes.push("forme_juridique");

  const rep = _representant(r.dirigeants);
  if (!rep) ouvertes.push("directeur_publication");

  const adresse =
    typeof siege.adresse === "string" ? _adresse(siege.adresse) : null;

  const brut: [string, unknown][] = [
    ["raison_sociale", r.nom_complet ?? r.nom_raison_sociale],
    ["siren", r.siren],
    ["siret_siege", siege.siret],
    ["forme_juridique", forme ?? null],
    ["code_ape", r.activite_principale],
    ["immatriculation", r.date_creation],
    ["siege", adresse],
    ["directeur_publication", rep ? rep.nom : null],
  ];
  const faits = brut
    .filter(([, v]) => v != null && String(v).trim() !== "")
    .map(([cle, v]) => ({ cle, valeur: String(v).trim(), source: SOURCE }));

  // L'effectif n'est PAS repris. Le registre ne donne qu'une TRANCHE
  // (« 10 à 19 salariés »), et une tranche écrite comme un nombre sur une
  // page devient un mensonge précis. On la laisse en question ouverte.
  return { faits, ouvertes, brut: r };
}

export class Reel implements Registre {
  // Champ déclaré à part, pas en propriété de constructeur : le mode
  // « strip-only » de Node refuse `constructor(private base …)`, et c'est
  // sous ce mode que tournent les épreuves.
  private base: string;
  constructor(base = "https://recherche-entreprises.api.gouv.fr") {
    this.base = base;
  }

  async chercher(siren: string): Promise<Etablissement | null> {
    const q = siren.replace(/\D/g, "");
    if (q.length !== 9) throw new Error(`« ${siren} » n'est pas un SIREN (9 chiffres)`);
    const r = await fetch(`${this.base}/search?q=${q}&per_page=1`, {
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(12_000),
    });
    if (!r.ok) throw new Error(`le registre a répondu ${r.status}`);
    const d = (await r.json()) as { results?: Record<string, unknown>[] };
    const un = d.results?.[0];
    if (!un || String(un.siren) !== q) return null;
    return enFaits(un);
  }
}

/** Sert des réponses écrites d'avance. Éprouve tout ce qui suit l'appel. */
export class Rejeu implements Registre {
  private reponses: Record<string, Record<string, unknown>>;
  constructor(reponses: Record<string, Record<string, unknown>>) {
    this.reponses = reponses;
  }
  async chercher(siren: string) {
    const un = this.reponses[siren.replace(/\D/g, "")];
    return un ? enFaits(un) : null;
  }
}
