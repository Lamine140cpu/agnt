import { createBrowserClient } from "@supabase/ssr";

/** Le client du navigateur. Il ne voit que ce que les politiques de ligne
 *  laissent voir — c'est pour ça que la clé anonyme peut être publique. */
export const clientNavigateur = () =>
  createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
  );
