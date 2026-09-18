"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { clientNavigateur } from "@/lib/supabase/navigateur";

/** Connexion par lien envoyé au courriel : pas de mot de passe à stocker,
 *  donc pas de mot de passe à laisser fuir. */
export default function Connexion() {
  const [courriel, setCourriel] = useState("");
  const [etat, setEtat] = useState<"repos" | "envoi" | "envoye">("repos");
  const [souci, setSouci] = useState<string | null>(null);
  const router = useRouter();

  /**
   * LES JETONS DANS LE FRAGMENT.
   *
   * Supabase a deux façons de renvoyer une session : un code en paramètre
   * (`?code=`), que le serveur peut échanger, et les jetons dans le
   * FRAGMENT (`#access_token=…`), que le serveur ne voit jamais — un
   * fragment ne quitte pas le navigateur.
   *
   * Le client de cette page demande la première, mais la seconde arrive
   * quand même : lien fabriqué côté administration, réglage de projet
   * différent, certains clients de messagerie. Trouvé en parcourant
   * l'application pour de vrai — on atterrissait sur « lien-sans-code »
   * avec sa session dans la barre d'adresse.
   */
  useEffect(() => {
    const f = new URLSearchParams(location.hash.slice(1));

    // L'ÉCHEC AUSSI REVIENT DANS LE FRAGMENT. Un lien périmé renvoie
    // `#error=access_denied&error_code=otp_expired`, que le serveur ne voit
    // pas davantage. Sans ces trois lignes, l'utilisateur retombe sur un
    // formulaire muet et ne sait pas que son lien a expiré — il le
    // recliquerait indéfiniment.
    const echec = f.get("error_description") || f.get("error");
    if (echec) {
      setSouci(f.get("error_code") === "otp_expired"
        ? "Ce lien a expiré ou a déjà servi. Demandez-en un nouveau."
        : echec.replace(/\+/g, " "));
      history.replaceState(null, "", location.pathname);
      return;
    }

    const acces = f.get("access_token");
    const rafraichir = f.get("refresh_token");
    if (!acces || !rafraichir) return;
    setEtat("envoi");
    clientNavigateur().auth
      .setSession({ access_token: acces, refresh_token: rafraichir })
      .then(({ error }) => {
        if (error) { setSouci(error.message); setEtat("repos"); return; }
        // On efface le fragment avant de partir : il porte des jetons, et
        // ils n'ont rien à faire dans l'historique du navigateur.
        history.replaceState(null, "", location.pathname);
        router.replace("/");
        router.refresh();
      });
  }, [router]);

  async function envoyer(e: React.FormEvent) {
    e.preventDefault();
    setEtat("envoi"); setSouci(null);
    const { error } = await clientNavigateur().auth.signInWithOtp({
      email: courriel.trim(),
      options: { emailRedirectTo: `${location.origin}/api/auth/retour` },
    });
    if (error) { setSouci(error.message); setEtat("repos"); }
    else setEtat("envoye");
  }

  return (
    <div className="seuil">
      <form className="seuil-boite" onSubmit={envoyer}>
        <div className="logo">UM</div>
        <h1>Ultra Motion</h1>
        <p>Des sites d&rsquo;une page où un film défile au rythme du défilement.
          Rien n&rsquo;y est écrit sur votre entreprise sans sa source.</p>

        {etat === "envoye" ? (
          <p className="avis">Lien envoyé à {courriel}. Il ouvre la console.</p>
        ) : (
          <>
            <div className="champ">
              <label className="eti" htmlFor="courriel">Courriel</label>
              <input id="courriel" type="email" required autoComplete="email"
                     value={courriel} onChange={(e) => setCourriel(e.target.value)} />
            </div>
            <button className="gros-bouton" disabled={etat === "envoi"}>
              {etat === "envoi" ? "Envoi…" : "Recevoir le lien"}
            </button>
          </>
        )}
        {souci && <p className="avis mauvais">{souci}</p>}
      </form>
    </div>
  );
}
