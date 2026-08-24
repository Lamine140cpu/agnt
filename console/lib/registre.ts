/**
 * Le registre des entreprises. Une frontière, comme les autres.
 *
 * POURQUOI CETTE FRONTIÈRE EXISTE. La cheffe ne doit jamais écrire un fait
 * sur le client sans source. Le registre est la meilleure source qui soit :
 * publique, opposable, et surtout — elle ne dépend pas de ce que le client
 * se rappelle. Un dirigeant qui dit « on a une vingtaine de camions » se
 * trompe de bonne foi ; le registre, non.
 *
 * CE QUI N'EST PAS ÉPROUVÉ : l'appel lui-même. Le réseau de l'environnement
 * où ce fichier a été écrit refuse ce domaine (503 au proxy), donc la forme
 * des champs vient de la documentation de l'API et non d'une réponse
 * observée. Le jour où l'appel passe, c'est `Reel.chercher()` qu'il faut
 * éprouver — sur UN SIREN — et corriger les noms de champs qui ne collent
 * pas avant d'en faire quoi que ce soit.
 *
 * Le mode rejeu permet d'éprouver tout ce qui vient après : la conversion en
 * faits, les origines, les questions ouvertes.
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
 */
export const HORS_REGISTRE = [
  "directeur_publication",
  "hebergeur",
  "courriel",
  "horaires",
  "assurance",
];

/** Convertit une réponse du registre en faits sourcés. */
export function enFaits(r: Record<string, unknown>): Etablissement {
  const siege = (r.siege ?? {}) as Record<string, unknown>;
  const brut: [string, unknown][] = [
    ["raison_sociale", r.nom_complet ?? r.nom_raison_sociale],
    ["siren", r.siren],
    ["siret_siege", siege.siret],
    ["forme_juridique", r.nature_juridique],
    ["code_ape", r.activite_principale],
    ["immatriculation", r.date_creation],
    ["siege", siege.adresse],
  ];
  const faits = brut
    .filter(([, v]) => v != null && String(v).trim() !== "")
    .map(([cle, v]) => ({ cle, valeur: String(v).trim(), source: SOURCE }));

  // L'effectif n'est PAS repris. Le registre ne donne qu'une TRANCHE
  // (« 10 à 19 salariés »), et une tranche écrite comme un nombre sur une
  // page devient un mensonge précis. On la laisse en question ouverte.
  return { faits, ouvertes: [...HORS_REGISTRE, "effectif"], brut: r };
}

export class Reel implements Registre {
  constructor(private base = "https://recherche-entreprises.api.gouv.fr") {}

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
  constructor(private reponses: Record<string, Record<string, unknown>>) {}
  async chercher(siren: string) {
    const un = this.reponses[siren.replace(/\D/g, "")];
    return un ? enFaits(un) : null;
  }
}
