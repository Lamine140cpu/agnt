/**
 * Le crochet Stripe : LE SEUL endroit qui change un plan.
 *
 * La signature est vérifiée avant toute chose. Sans elle, l'URL de ce
 * crochet suffirait à s'offrir n'importe quel plan — il n'y a rien d'autre
 * à deviner qu'une adresse.
 */
import { NextRequest, NextResponse } from "next/server";
import type Stripe from "stripe";
import { clientService } from "@/lib/supabase/serveur";
import { stripe, planDuPrix, VIVANT } from "@/lib/paiement";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  const secret = process.env.STRIPE_WEBHOOK_SECRET;
  const signature = req.headers.get("stripe-signature");
  if (!secret || !signature) {
    return new NextResponse("crochet non configuré", { status: 503 });
  }

  const brut = await req.text();
  let e: Stripe.Event;
  try {
    e = stripe().webhooks.constructEvent(brut, signature, secret);
  } catch (err) {
    // Une signature invalide n'est pas une erreur de service : c'est une
    // requête qu'on refuse.
    return new NextResponse(
      `signature refusée : ${err instanceof Error ? err.message : ""}`,
      { status: 400 });
  }

  const svc = clientService();

  if (e.type === "customer.subscription.created" ||
      e.type === "customer.subscription.updated" ||
      e.type === "customer.subscription.deleted") {
    const ab = e.data.object as Stripe.Subscription;
    const compte = ab.metadata?.compte;
    if (!compte) return NextResponse.json({ ignore: "abonnement sans compte" });

    const prix = ab.items?.data?.[0]?.price?.id;
    const vivant = e.type !== "customer.subscription.deleted" && VIVANT.has(ab.status);
    const plan = vivant ? planDuPrix(prix) : "essai";
    const fin = (ab as unknown as { current_period_end?: number }).current_period_end;

    await svc.from("comptes").update({
      abonnement_stripe: ab.id,
      plan,
      plan_jusqu_a: fin ? new Date(fin * 1000).toISOString() : null,
    }).eq("id", compte);

    return NextResponse.json({ compte, plan, etat: ab.status });
  }

  // Tout le reste est reçu et ignoré explicitement. Répondre 200 est ce qui
  // empêche Stripe de rejouer indéfiniment des événements dont on n'a que
  // faire.
  return NextResponse.json({ recu: e.type });
}
