/** Ouvre une session de paiement. Ne change AUCUN droit : seul le crochet
 *  le fait, après un événement signé par Stripe. */
import { NextRequest, NextResponse } from "next/server";
import { clientServeur } from "@/lib/supabase/serveur";
import { stripe, PLANS, SansStripe, type Plan } from "@/lib/paiement";

export async function POST(req: NextRequest) {
  const sb = await clientServeur();
  const { data: { user } } = await sb.auth.getUser();
  if (!user) return new NextResponse("non connecté", { status: 401 });

  const { plan } = (await req.json()) as { plan: Plan };
  const choisi = PLANS[plan as keyof typeof PLANS];
  if (!choisi?.prix) return new NextResponse("plan inconnu", { status: 400 });

  try {
    const s = stripe();
    const { data: compte } = await sb.from("comptes")
      .select("client_stripe, courriel").eq("id", user.id).single();

    // On réutilise le client Stripe existant : en créer un par paiement
    // éparpille l'historique d'un même client sur plusieurs fiches, et plus
    // personne ne sait ensuite ce qu'il a payé.
    let client = compte?.client_stripe ?? undefined;
    if (!client) {
      const c = await s.customers.create({
        email: compte?.courriel ?? user.email,
        metadata: { compte: user.id },
      });
      client = c.id;
      await sb.from("comptes").update({ client_stripe: client }).eq("id", user.id);
    }

    const base = process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000";
    const session = await s.checkout.sessions.create({
      mode: "subscription",
      customer: client,
      line_items: [{ price: choisi.prix, quantity: 1 }],
      // `compte` voyage jusqu'au crochet : sans lui, l'événement arrive sans
      // qu'on sache à qui l'attribuer.
      subscription_data: { metadata: { compte: user.id } },
      success_url: `${base}/?paiement=ok`,
      cancel_url: `${base}/?paiement=annule`,
    });

    return NextResponse.json({ url: session.url });
  } catch (e) {
    if (e instanceof SansStripe) {
      return NextResponse.json({ erreur: e.message }, { status: 503 });
    }
    throw e;
  }
}
