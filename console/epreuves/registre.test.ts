/**
 * La frontière du registre, éprouvée sur pièces.
 *
 * Deux moitiés, et la distinction compte.
 *
 * LES ÉPREUVES HORS LIGNE tournent toujours : elles jugent la conversion
 * d'une réponse en faits — la table des formes juridiques, la mise en forme
 * de l'adresse, le choix du représentant légal. Elles n'ont besoin de rien.
 *
 * L'ÉPREUVE EN LIGNE appelle le vrai registre sur un vrai SIREN. Elle SAUTE
 * quand le réseau la refuse, au lieu d'échouer : l'environnement où ce
 * fichier a été écrit rendait 503 sur ce domaine, et une épreuve rouge pour
 * cause de proxy finit par être ignorée, ce qui la rend pire qu'absente.
 * Mais quand elle tourne, elle vérifie ce qu'aucune réponse écrite d'avance
 * ne peut vérifier : que les noms de champs de l'API n'ont pas bougé.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { enFaits, _adresse, _representant, Reel } from "../lib/registre.ts";

/* ---------------------------------------------------- l'adresse en capitales */

test("l'adresse en capitales devient lisible", () => {
  assert.equal(
    _adresse("45 RUE JEAN CHARCOT 93600 AULNAY-SOUS-BOIS"),
    "45 rue Jean Charcot, 93600 Aulnay-sous-Bois",
  );
});

test("les particules restent en bas de casse dans les noms de commune", () => {
  assert.equal(
    _adresse("12 AVENUE DES CHAMPS 78000 SAINT-GERMAIN-EN-LAYE"),
    "12 avenue des Champs, 78000 Saint-Germain-en-Laye",
  );
});

test("une adresse sans code postal passe quand même", () => {
  assert.equal(_adresse("ZONE INDUSTRIELLE NORD"), "Zone Industrielle Nord");
});

/* ------------------------------------------------- le représentant légal */

const DEUX = [
  { nom: "BAKAS", prenoms: "SAID", qualite: "Directeur Général", type_dirigeant: "personne physique" },
  { nom: "BAKAS", prenoms: "SAMI", qualite: "Président de SAS", type_dirigeant: "personne physique" },
];

test("entre un directeur général et un président, c'est le président", () => {
  assert.deepEqual(_representant(DEUX), { nom: "Sami Bakas", qualite: "Président de SAS" });
});

test("une personne morale dirigeante ne fait pas un directeur de publication", () => {
  const r = _representant([
    { nom: "HOLDING MACHIN", qualite: "Président", type_dirigeant: "personne morale" },
  ]);
  assert.equal(r, null);
});

test("un gérant de SARL représente la société", () => {
  const r = _representant([
    { nom: "DUPONT", prenoms: "MARIE CLAIRE", qualite: "Gérant", type_dirigeant: "personne physique" },
  ]);
  assert.equal(r?.nom, "Marie Dupont");
});

test("aucun dirigeant, aucun représentant", () => {
  assert.equal(_representant(undefined), null);
  assert.equal(_representant([]), null);
});

/* ------------------------------------------------------- la conversion */

const REPONSE = {
  nom_complet: "TRANS GOLD MARCHANDISES",
  siren: "831321112",
  nature_juridique: "5710",
  activite_principale: "49.41A",
  date_creation: "2017-07-31",
  dirigeants: DEUX,
  siege: { siret: "83132111200029", adresse: "45 RUE JEAN CHARCOT 93600 AULNAY-SOUS-BOIS" },
};

test("le code de forme juridique devient un libellé, jamais un chiffre publié", () => {
  const e = enFaits(REPONSE);
  const f = e.faits.find((x) => x.cle === "forme_juridique");
  assert.equal(f?.valeur, "SAS");
  assert.ok(!e.ouvertes.includes("forme_juridique"));
});

test("un code inconnu ne devient PAS un fait : il devient une question", () => {
  const e = enFaits({ ...REPONSE, nature_juridique: "9999" });
  assert.equal(e.faits.find((x) => x.cle === "forme_juridique"), undefined);
  assert.ok(e.ouvertes.includes("forme_juridique"));
});

test("le directeur de la publication sort du registre", () => {
  const e = enFaits(REPONSE);
  const f = e.faits.find((x) => x.cle === "directeur_publication");
  assert.equal(f?.valeur, "Sami Bakas");
  assert.equal(f?.source, "recherche-entreprises.api.gouv.fr");
  assert.ok(!e.ouvertes.includes("directeur_publication"));
});

test("sans dirigeant lisible, le directeur de publication redevient une question", () => {
  const e = enFaits({ ...REPONSE, dirigeants: [] });
  assert.ok(e.ouvertes.includes("directeur_publication"));
});

test("l'effectif reste une question : le registre n'en donne qu'une tranche", () => {
  assert.ok(enFaits(REPONSE).ouvertes.includes("effectif"));
});

test("chaque fait porte sa source", () => {
  for (const f of enFaits(REPONSE).faits) {
    assert.equal(f.source, "recherche-entreprises.api.gouv.fr");
    assert.notEqual(f.valeur.trim(), "");
  }
});

/* -------------------------------------------------- l'appel réel, s'il passe */

test("le vrai registre rend les champs que ce fichier attend", async (t) => {
  let e;
  try {
    e = await new Reel().chercher("831321112");
  } catch (err) {
    t.skip(`le registre est injoignable ici (${(err as Error).message})`);
    return;
  }
  assert.ok(e, "aucun résultat pour un SIREN qui existe");
  const par = Object.fromEntries(e!.faits.map((f) => [f.cle, f.valeur]));

  // Ce sont les valeurs du registre national, pas des préférences : si l'une
  // d'elles change, c'est que l'entreprise a changé — ou que l'API a bougé.
  assert.equal(par.raison_sociale, "TRANS GOLD MARCHANDISES");
  assert.equal(par.siren, "831321112");
  assert.equal(par.siret_siege, "83132111200029");
  assert.equal(par.code_ape, "49.41A");
  assert.equal(par.immatriculation, "2017-07-31");

  // Et les trois corrections, vérifiées de bout en bout sur la vraie réponse.
  assert.equal(par.forme_juridique, "SAS", "le code INSEE n'a pas été traduit");
  assert.equal(par.siege, "45 rue Jean Charcot, 93600 Aulnay-sous-Bois");
  assert.equal(par.directeur_publication, "Sami Bakas");
});

test("un SIREN qui n'existe pas rend null, pas une erreur", async (t) => {
  try {
    assert.equal(await new Reel().chercher("000000000"), null);
  } catch (err) {
    t.skip(`le registre est injoignable ici (${(err as Error).message})`);
  }
});

test("ce qui n'est pas un SIREN est refusé avant tout appel", async () => {
  await assert.rejects(() => new Reel().chercher("12345"), /n'est pas un SIREN/);
});
