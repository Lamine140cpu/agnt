/**
 * Le retour du lien de connexion.
 *
 * Supabase renvoie ici avec un code à usage unique ; on l'échange contre une
 * session, et le cookie est posé au passage. Sans cette route, le lien
 * envoyé par courriel tombe en 404 — personne ne peut entrer, et c'est
 * exactement ce qui manquait.
 */
import { NextResponse, type NextRequest } from "next/server";
import { clientServeur } from "@/lib/supabase/serveur";

export async function GET(req: NextRequest) {
  const url = new URL(req.url);
  const code = url.searchParams.get("code");
  const vers = url.searchParams.get("vers") ?? "/";

  if (!code) {
    return NextResponse.redirect(new URL("/connexion?souci=lien-sans-code", url));
  }

  const sb = await clientServeur();
  const { error } = await sb.auth.exchangeCodeForSession(code);
  if (error) {
    // Un lien périmé ou déjà utilisé n'est pas une panne : c'est le cas
    // ordinaire quand on clique deux fois. On le dit sans dramatiser.
    return NextResponse.redirect(
      new URL(`/connexion?souci=${encodeURIComponent(error.message)}`, url));
  }

  // `vers` vient de l'URL : on n'accepte qu'un chemin interne. Une
  // redirection ouverte transformerait ce lien de connexion en tremplin
  // vers n'importe quel site.
  const sur = vers.startsWith("/") && !vers.startsWith("//") ? vers : "/";
  return NextResponse.redirect(new URL(sur, url));
}
