/**
 * Le flux de la cheffe.
 *
 * LE PROBLÈME QUE CETTE ROUTE RÉSOUT. Le garde-fou a besoin du texte
 * ENTIER pour juger — une invention peut tomber au dernier mot. Mais un chat
 * qui attend la fin pour afficher quoi que ce soit ne ressemble à rien.
 *
 * On fait donc les deux : le texte ruisselle normalement, et à la fin il est
 * relu. S'il déborde, on envoie un événement `refus` et le client RETIRE le
 * message sous les yeux de l'utilisateur, en disant ce qui a été retiré.
 *
 * Ce n'est pas un pis-aller : c'est le moment le plus honnête du produit. Un
 * modèle qui se corrige en public vaut mieux qu'un modèle qui n'a jamais
 * l'air de se tromper — et le second n'existe pas.
 */
import { NextRequest } from "next/server";
import type Anthropic from "@anthropic-ai/sdk";
import { clientServeur, clientService } from "@/lib/supabase/serveur";
import { flux, SansCle } from "@/lib/cheffe";
import { inventions, faitsDeclares, type Fait } from "@/lib/contrat";
import { Reel, HORS_REGISTRE } from "@/lib/registre";

export const runtime = "nodejs";
export const maxDuration = 300;

const enc = new TextEncoder();
const evt = (type: string, d: unknown) =>
  enc.encode(`data: ${JSON.stringify({ type, ...(d as object) })}\n\n`);

export async function POST(req: NextRequest) {
  const sb = await clientServeur();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return new Response("non connecté", { status: 401 });

  const { projet, texte } = (await req.json()) as { projet: string; texte: string };
  if (!projet || !texte?.trim()) return new Response("requête vide", { status: 400 });

  // La politique de ligne fait le contrôle d'accès : si le projet n'est pas
  // le sien, la requête ne rend rien. Pas de vérification à la main ici —
  // une deuxième règle finirait par diverger de la première.
  const { data: p } = await sb.from("projets")
    .select("id, nom, cle, etat, contrat").eq("id", projet).single();
  if (!p) return new Response("projet introuvable", { status: 404 });

  const { data: faitsBase } = await sb.from("faits")
    .select("cle, valeur, origine, source, releve_le").eq("projet", projet);
  const faits = (faitsBase ?? []) as Fait[];

  const { data: histo } = await sb.from("messages")
    .select("role, texte").eq("projet", projet)
    .in("role", ["client", "cheffe"]).order("id").limit(60);

  await sb.from("messages").insert({ projet, role: "client", texte });

  const messages: Anthropic.MessageParam[] = [
    ...(histo ?? []).map((m) => ({
      role: (m.role === "client" ? "user" : "assistant") as "user" | "assistant",
      content: m.texte,
    })),
    { role: "user", content: texte },
  ];

  const contexte = [
    `Projet « ${p.nom} » (clé ${p.cle}), étape : ${p.etat}.`,
    "",
    "FAITS DÉJÀ DÉCLARÉS — les seuls que tu aies le droit d'écrire :",
    ...(faits.filter((f) => f.valeur != null).map(
      (f) => `  ${f.cle} = ${f.valeur}  [${f.origine} · ${f.source}]`)),
    faits.some((f) => f.valeur != null) ? "" : "  (aucun pour l'instant)",
    "QUESTIONS OUVERTES — ne les comble pas, ne les contourne pas :",
    ...(faits.filter((f) => f.valeur == null).map((f) => `  ${f.cle}`)),
  ].join("\n");

  const corps = new ReadableStream({
    async start(ctrl) {
      const dire = (t: string, d: unknown) => ctrl.enqueue(evt(t, d));
      let accumule = "";

      try {
        const s = flux(messages, contexte);

        s.on("text", (delta) => {
          accumule += delta;
          dire("texte", { delta });
        });

        const rep = await s.finalMessage();

        if (rep.stop_reason === "refusal") {
          dire("erreur", {
            message: "Le modèle a décliné la demande, et le repli aussi.",
          });
          ctrl.close();
          return;
        }

        /* --------------------------------------------- les outils */
        for (const bloc of rep.content) {
          if (bloc.type !== "tool_use") continue;
          const res = await outil(bloc, projet, sb);
          dire("outil", { nom: bloc.name, resultat: res });
        }

        /* ------------------------------- LA RELECTURE, à la toute fin */
        const relus = await sb.from("faits")
          .select("cle, valeur, origine, source").eq("projet", projet);
        const permis = faitsDeclares((relus.data ?? []) as Fait[], [p.nom]);
        const trouves = inventions(accumule, permis);

        if (trouves.length) {
          // On n'enregistre PAS le message : il ne doit pas revenir dans
          // l'historique du prochain tour, sinon le modèle le reprendrait
          // comme un fait acquis.
          dire("refus", {
            trouves,
            message:
              trouves.length === 1
                ? "Je retire ce message : il avance un fait que je ne peux pas justifier."
                : `Je retire ce message : il avance ${trouves.length} faits que je ne peux pas justifier.`,
          });
          // Le TEXTE retiré est gardé dans `meta`, pas seulement son résumé.
          // Sans lui, rouvrir le projet demain montrerait une ligne de
          // journal sèche au lieu de la phrase barrée — et on perdrait
          // justement ce qui rend le garde-fou visible.
          await sb.from("messages").insert({
            projet, role: "journal",
            texte: `garde-fou : message retiré — ${trouves
              .map((t) => `${t.quoi} « ${t.extrait} »`).join(", ")}`,
            meta: { trouves, retire: accumule },
          });
        } else if (accumule.trim()) {
          await sb.from("messages").insert({
            projet, role: "cheffe", texte: accumule,
          });
        }

        dire("fin", { jetons: rep.usage?.output_tokens ?? null });
      } catch (e) {
        dire("erreur", {
          message: e instanceof SansCle ? e.message
            : e instanceof Error ? e.message : "erreur inconnue",
          sansCle: e instanceof SansCle,
        });
      } finally {
        ctrl.close();
      }
    },
  });

  return new Response(corps, {
    headers: {
      "content-type": "text/event-stream; charset=utf-8",
      "cache-control": "no-cache, no-transform",
      connection: "keep-alive",
    },
  });
}

/* ------------------------------------------------------------ les outils */

type SB = Awaited<ReturnType<typeof clientServeur>>;

async function outil(bloc: Anthropic.ToolUseBlock, projet: string, sb: SB) {
  const e = bloc.input as Record<string, unknown>;

  if (bloc.name === "chercher_registre") {
    const r = await new Reel().chercher(String(e.siren));
    if (!r) return { trouve: false };
    // On écrit les faits ici plutôt que de les rendre au modèle en lui
    // demandant de les reposer : un aller-retour de plus, c'est une
    // occasion de plus qu'un chiffre change en chemin.
    await sb.from("faits").upsert(
      r.faits.map((f) => ({
        projet, cle: f.cle, valeur: f.valeur,
        origine: "registre", source: f.source,
        releve_le: new Date().toISOString(),
      })), { onConflict: "projet,cle" });
    await sb.from("faits").upsert(
      r.ouvertes.map((cle) => ({ projet, cle, valeur: null, origine: null, source: null })),
      { onConflict: "projet,cle", ignoreDuplicates: true });
    return { trouve: true, faits: r.faits.length, ouvertes: r.ouvertes.length };
  }

  if (bloc.name === "poser_faits") {
    const liste = (e.faits ?? []) as Fait[];
    // La contrainte de la base refuserait de toute façon un fait sans
    // source. On le dit ici pour que le message soit lisible.
    const sans = liste.filter((f) => f.valeur != null && !f.source);
    if (sans.length) {
      return { refuse: true, motif: `sans source : ${sans.map((f) => f.cle).join(", ")}` };
    }
    await sb.from("faits").upsert(
      liste.map((f) => ({
        projet, cle: f.cle, valeur: f.valeur, origine: f.origine, source: f.source,
        releve_le: f.origine === "registre" ? new Date().toISOString() : null,
      })), { onConflict: "projet,cle" });
    return { poses: liste.length };
  }

  if (bloc.name === "ouvrir_questions") {
    const cles = ((e.cles ?? []) as string[]).filter(Boolean);
    await sb.from("faits").upsert(
      cles.map((cle) => ({ projet, cle, valeur: null, origine: null, source: null })),
      { onConflict: "projet,cle", ignoreDuplicates: true });
    return { ouvertes: cles.length };
  }

  if (bloc.name === "lancer") {
    // La file est posée avec la clé de service : personne ne met une tâche
    // en file depuis le navigateur, sinon n'importe qui pourrait faire
    // tourner le moteur autant qu'il veut.
    const quoi = String(e.quoi);
    const svc = clientService();
    const { data } = await svc.from("taches")
      .insert({ projet, quoi, charge: {} }).select("id").single();
    await sb.from("projets").update({ etat: quoi }).eq("id", projet);
    return { tache: data?.id ?? null, quoi };
  }

  return { inconnu: bloc.name };
}

export { HORS_REGISTRE };
