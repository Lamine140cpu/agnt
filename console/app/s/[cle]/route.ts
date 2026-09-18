/**
 * Sert la page d'un site publié.
 *
 * DEUX DÉCOUVERTES ONT DICTÉ CE FICHIER, et ni l'une ni l'autre n'était
 * prévue :
 *
 * 1. Supabase Storage STOCKE bien le fichier en `text/html`, mais le SERT en
 *    `text/plain` avec `nosniff` — il refuse d'héberger des pages arbitraires
 *    sur son domaine. Mesuré : le CSS ressort en `text/css`, le JSON en
 *    `application/json`, une image en `image/jpeg`, et seul le HTML est
 *    dégradé. Un navigateur afficherait le code source au lieu de la page.
 *    D'où le partage : LA PAGE VIENT D'ICI, LES IMAGES DU STOCKAGE. Faire
 *    transiter onze cents images par l'application serait absurde, et elles,
 *    le stockage les sert correctement.
 *
 * 2. Cloudflare, devant le stockage, sert une copie périmée après un renvoi :
 *    l'objet neuf faisait 115 355 octets, l'URL publique en rendait 14. D'où
 *    la publication sous un chemin VERSIONNÉ, et cette route qui lit dans la
 *    base quelle version est servie.
 *
 * La balise `<base>` fait le raccord : la page est servie à /s/<clé>, mais
 * ses chemins relatifs doivent pointer vers le stockage. Sans elle, ils se
 * résoudraient en /s/assets/… et la toile resterait noire.
 */
import { type NextRequest } from "next/server";
import { clientService } from "@/lib/supabase/serveur";

export const runtime = "nodejs";

const BASE = process.env.NEXT_PUBLIC_SUPABASE_URL;
const SEAU = "sites";

export async function GET(
  _req: NextRequest,
  { params }: { params: Promise<{ cle: string }> },
) {
  const { cle } = await params;
  // La clé sert à construire une URL : on n'accepte que ce que la contrainte
  // de la base accepte déjà, sinon un `../` la ferait sortir du seau.
  if (!/^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$/.test(cle)) {
    return new Response("clé invalide", { status: 400 });
  }

  // Lecture par la clé de service : un site publié est fait pour être vu par
  // quelqu'un qui n'a pas de compte, donc les politiques de ligne ne peuvent
  // pas répondre ici.
  const { data } = await clientService()
    .from("projets").select("version").eq("cle", cle).not("version", "is", null)
    .order("publie_le", { ascending: false }).limit(1).maybeSingle();

  if (!data?.version) {
    return new Response("ce site n'est pas publié", { status: 404 });
  }

  const racine = `${BASE}/storage/v1/object/public/${SEAU}/${cle}/${data.version}/`;
  const r = await fetch(racine + "index.html", { cache: "no-store" });
  if (!r.ok) {
    return new Response("la version enregistrée est introuvable", { status: 502 });
  }

  let html = await r.text();
  if (!html.includes("<base ")) {
    html = html.replace(/<head([^>]*)>/i, (m) => `${m}\n<base href="${racine}">`);
  }

  return new Response(html, {
    headers: {
      "content-type": "text/html; charset=utf-8",
      // Le chemin étant versionné, la page peut se garder longtemps : c'est
      // la ligne en base qui change quand on republie, pas ce contenu-ci.
      "cache-control": "public, max-age=300, stale-while-revalidate=3600",
    },
  });
}
