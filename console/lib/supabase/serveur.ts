import { createServerClient } from "@supabase/ssr";
import { cookies } from "next/headers";
import { createClient } from "@supabase/supabase-js";

/** Le client du serveur, AVEC la session de l'utilisateur : les politiques
 *  de ligne s'appliquent, et c'est voulu. */
export async function clientServeur() {
  const jar = await cookies();
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        getAll: () => jar.getAll(),
        setAll: (liste) => {
          try {
            liste.forEach(({ name, value, options }) => jar.set(name, value, options));
          } catch {
            // Appelé depuis un composant serveur : le rafraîchissement de
            // session est fait par le middleware, on peut ignorer.
          }
        },
      },
    },
  );
}

/**
 * LE CLIENT DE SERVICE — il contourne toutes les politiques de ligne.
 *
 * Il n'a que deux usages légitimes : poser une tâche dans la file, et
 * encaisser un événement Stripe. Partout ailleurs, utiliser `clientServeur`.
 * Une requête utilisateur servie par cette clé, c'est chaque compte qui voit
 * les projets de tous les autres.
 */
export function clientService() {
  const cle = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!cle) throw new Error("SUPABASE_SERVICE_ROLE_KEY absente");
  return createClient(process.env.NEXT_PUBLIC_SUPABASE_URL!, cle, {
    auth: { persistSession: false, autoRefreshToken: false },
  });
}
