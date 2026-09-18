"use server";

import { redirect } from "next/navigation";
import { revalidatePath } from "next/cache";
import { clientServeur } from "@/lib/supabase/serveur";
import { cleDepuis } from "@/lib/cle";

/**
 * Crée un projet.
 *
 * LA LIMITE DU PLAN EST LUE DANS LA BASE, jamais recopiée ici. `droits()`
 * est écrite une fois dans la migration ; deux versions de la même règle
 * finiraient par autoriser des choses différentes — et ce serait toujours
 * l'application qui ouvre ce que la base ferme, au pire moment.
 */
export async function creerProjet(_precedent: unknown, form: FormData) {
  const nom = String(form.get("nom") ?? "").trim();
  if (nom.length < 2) return { souci: "Donnez un nom au projet." };

  const sb = await clientServeur();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) redirect("/connexion");

  const { data: compte } = await sb.from("comptes")
    .select("plan").eq("id", user.id).single();
  const plan = compte?.plan ?? "essai";

  const { data: droits } = await sb.rpc("droits", { p: plan });
  const { count } = await sb.from("projets")
    .select("id", { count: "exact", head: true });

  const plafond = (droits as { projets?: number } | null)?.projets ?? 1;
  if ((count ?? 0) >= plafond) {
    return {
      souci: plafond === 1
        ? "Le plan d'essai permet un seul site. Passez à Atelier pour en ouvrir d'autres."
        : `Votre plan permet ${plafond} sites, et vous en avez ${count}.`,
      plan,
    };
  }

  // La clé peut déjà être prise : on suffixe plutôt que de renvoyer une
  // erreur de contrainte, que l'utilisateur ne saurait pas quoi en faire.
  let cle = cleDepuis(nom);
  const { data: prises } = await sb.from("projets")
    .select("cle").like("cle", `${cle}%`);
  if (prises?.some((p) => p.cle === cle)) {
    cle = `${cle}-${(prises.length + 1)}`.slice(0, 40);
  }

  const { data, error } = await sb.from("projets")
    .insert({ compte: user.id, nom, cle }).select("id").single();

  if (error) return { souci: error.message };

  await sb.from("messages").insert({
    projet: data.id, role: "cheffe",
    texte: "Bonjour. Avant d'écrire quoi que ce soit, je veux savoir de quoi " +
           "on parle : quel est le métier, et à qui il s'adresse ?\n\n" +
           "Ensuite je vous demanderai le SIREN — j'interroge le registre " +
           "plutôt que votre mémoire, parce que ce que j'y trouve, je peux " +
           "l'écrire dans la page et le prouver.",
  });

  revalidatePath("/console", "layout");
  redirect(`/console/${data.id}`);
}
