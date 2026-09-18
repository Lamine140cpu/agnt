/**
 * La frontière Stripe.
 *
 * DEUX RÈGLES, ET ELLES SE PAYENT CHER QUAND ON LES OUBLIE.
 *
 * 1. LE PLAN N'EST JAMAIS ÉCRIT DEPUIS LE NAVIGATEUR. Il ne change que
 *    lorsque Stripe le dit, par un événement signé. Une page de retour
 *    « paiement réussi » n'est pas une preuve de paiement : c'est une URL,
 *    et n'importe qui peut l'ouvrir.
 *
 * 2. LES DROITS SE LISENT EN BASE, PAS ICI. La fonction `droits(plan)` de
 *    la migration est la seule à les définir. Les recopier en TypeScript
 *    donnerait deux vérités qui finiraient par autoriser des choses
 *    différentes — et c'est toujours l'application qui autorise ce que la
 *    base refuse, ou l'inverse, au pire moment.
 *
 * CE QUI N'EST PAS ÉPROUVÉ : tout ce fichier. Il n'y avait pas de clé Stripe
 * dans l'environnement où il a été écrit. À éprouver dans cet ordre, en mode
 * test : une session de paiement, puis l'événement reçu par le crochet, puis
 * une résiliation. Le crochet AVANT toute mise en production : un plan qui ne
 * redescend jamais est un client qui garde un accès qu'il ne paye plus.
 */
import Stripe from "stripe";

export const PLANS = {
  atelier: {
    nom: "Atelier",
    prix: process.env.NEXT_PUBLIC_STRIPE_PRIX_ATELIER,
    dit: "Cinq sites, publication comprise.",
  },
  studio: {
    nom: "Studio",
    prix: process.env.NEXT_PUBLIC_STRIPE_PRIX_STUDIO,
    dit: "Cinquante sites, et la file prioritaire.",
  },
} as const;

export type Plan = keyof typeof PLANS | "essai";

export class SansStripe extends Error {
  constructor() {
    super("STRIPE_SECRET_KEY absente — la facturation est hors service.");
    this.name = "SansStripe";
  }
}

export function stripe() {
  const cle = process.env.STRIPE_SECRET_KEY;
  if (!cle) throw new SansStripe();
  return new Stripe(cle);
}

/**
 * Retrouve le plan d'après ce que Stripe dit de l'abonnement.
 *
 * On lit le PRIX, jamais un libellé : un nom de produit se change dans le
 * tableau de bord d'un clic, et le jour où quelqu'un renomme « Atelier » en
 * « Atelier 2026 », un code qui compare des noms ouvre ou ferme les droits
 * de tout le monde.
 */
export function planDuPrix(prixId: string | undefined): Plan {
  if (!prixId) return "essai";
  if (prixId === PLANS.studio.prix) return "studio";
  if (prixId === PLANS.atelier.prix) return "atelier";
  // Un prix inconnu ne donne pas de droits. Se rabattre sur le plan le plus
  // généreux « pour ne pas gêner le client » serait offrir l'accès à toute
  // personne capable de créer un prix.
  return "essai";
}

/** Les états d'abonnement qui donnent effectivement accès. */
export const VIVANT = new Set(["active", "trialing", "past_due"]);
// `past_due` est dedans à dessein : la carte a été refusée mais Stripe
// réessaie encore. Couper l'accès au premier échec ferait perdre un client
// pour une carte expirée.
