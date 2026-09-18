import { createServerClient } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";

/**
 * Le rafraîchissement de session, à chaque requête.
 *
 * SANS CE FICHIER, LA CONNEXION TIENT UNE HEURE PUIS LÂCHE. Le jeton
 * d'accès expire ; c'est le middleware qui le renouvelle et repose le
 * cookie. Un composant serveur ne peut pas le faire — il n'a pas le droit
 * d'écrire un cookie — d'où ce passage obligé.
 */
export async function middleware(req: NextRequest) {
  let reponse = NextResponse.next({ request: req });

  const sb = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => req.cookies.getAll(),
        setAll: (liste) => {
          liste.forEach(({ name, value }) => req.cookies.set(name, value));
          reponse = NextResponse.next({ request: req });
          liste.forEach(({ name, value, options }) =>
            reponse.cookies.set(name, value, options));
        },
      },
    },
  );

  // `getUser` vérifie le jeton auprès du serveur d'authentification. Se fier
  // à `getSession` ici reviendrait à croire un cookie sur parole.
  const { data: { user } } = await sb.auth.getUser();

  const chemin = req.nextUrl.pathname;
  // `/s/` sert les sites PUBLIÉS : ils sont faits pour être vus, y compris
  // par quelqu'un qui n'a pas de compte. Les protéger reviendrait à
  // publier une page que personne ne peut ouvrir.
  const ouvert = chemin.startsWith("/connexion") || chemin.startsWith("/api/auth")
              || chemin.startsWith("/s/");
  if (!user && !ouvert && !chemin.startsWith("/api/stripe/crochet")) {
    const vers = req.nextUrl.clone();
    vers.pathname = "/connexion";
    return NextResponse.redirect(vers);
  }
  return reponse;
}

export const config = {
  // Le crochet Stripe est exclu : il arrive sans session, signé par Stripe,
  // et le rediriger vers la page de connexion ferait manquer des paiements.
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|api/stripe/crochet|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)",
  ],
};
