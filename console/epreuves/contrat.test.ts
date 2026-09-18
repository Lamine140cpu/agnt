/**
 * Le garde-fou des faits, éprouvé sur les vecteurs PARTAGÉS avec le moteur.
 *
 *     npm run verif
 *
 * Les cas ne sont pas écrits ici : ils vivent dans
 * site/generateur/vecteurs-faits.json, et architecte.py répond au même
 * questionnaire. C'est le seul moyen d'empêcher deux implémentations de la
 * même règle de diverger en silence — et une divergence ici voudrait dire
 * qu'on affiche dans le chat une phrase que le moteur refusera plus tard.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { faitsDeclares, inventions, verifierTexte, Refus, type Fait } from "../lib/contrat.ts";

const ici = dirname(fileURLToPath(import.meta.url));
const vecteurs = JSON.parse(readFileSync(
  join(ici, "..", "..", "site", "generateur", "vecteurs-faits.json"), "utf8"));

const faits = vecteurs.faits as Fait[];
const permis = faitsDeclares(faits);

for (const cas of vecteurs.cas) {
  test(`${cas.mord ? "refuse" : "laisse passer"} — ${cas.quoi}`, () => {
    const t = inventions(cas.texte, permis);
    const detail = t.map((x) => `${x.quoi}: « ${x.extrait} »`).join(", ") || "rien";
    assert.equal(t.length > 0, cas.mord,
      `« ${cas.texte} » -> ${detail}`);
    if (cas.mord && cas.extrait) {
      assert.ok(t.some((x) => x.extrait.includes(cas.extrait)),
        `attendu « ${cas.extrait} », trouvé ${detail}`);
    }
  });
}

test("une valeur nulle n'autorise rien", () => {
  // `effectif` est déclaré sans valeur : c'est une question ouverte, et une
  // question ouverte n'est pas une permission d'écrire un effectif.
  assert.throws(() => verifierTexte("Nous sommes 12 salariés.", faits), Refus);
});

test("verifierTexte laisse passer un texte honnête", () => {
  verifierTexte("On écoute la matière avant de la couper.", faits);
});

test("le refus nomme ce qu'il a trouvé", () => {
  try {
    verifierTexte("Vingt ans de métier, et 30 véhicules.", faits);
    assert.fail("aucun refus levé");
  } catch (e) {
    assert.ok(e instanceof Refus);
    assert.ok(e.trouves.length >= 2, `trouvé ${e.trouves.length}`);
    assert.match(e.message, /Vingt ans/);
  }
});

test("l'année en cours passe : c'est le copyright, pas un fait du client", () => {
  const an = String(new Date().getFullYear());
  assert.equal(inventions(`© ${an} Atelier Martin`, permis).length, 0);
});
