"use client";

import { useState } from "react";
import { clientNavigateur } from "@/lib/supabase/navigateur";

/** Connexion par lien envoyé au courriel : pas de mot de passe à stocker,
 *  donc pas de mot de passe à laisser fuir. */
export default function Connexion() {
  const [courriel, setCourriel] = useState("");
  const [etat, setEtat] = useState<"repos" | "envoi" | "envoye">("repos");
  const [souci, setSouci] = useState<string | null>(null);

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
