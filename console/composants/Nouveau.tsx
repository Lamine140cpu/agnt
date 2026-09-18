"use client";

import { useActionState } from "react";
import { creerProjet } from "@/app/console/actions";

/** Le formulaire d'ouverture d'un projet. Rien de plus qu'un nom : tout le
 *  reste vient de la conversation, et lui demander dix champs d'avance
 *  serait exactement le formulaire qu'on remplace. */
export default function Nouveau() {
  const [etat, action, enCours] = useActionState(creerProjet, null);

  return (
    <section className="chat">
      <div className="fil">
        <div className="fil-dedans">
          <div className="tour">
            <div className="nom"><i /> cheffe</div>
            <div className="corps">
              <p>Donnez un nom à ce site &mdash; celui de l&rsquo;entreprise fait
                l&rsquo;affaire. On peut le changer ensuite.</p>
            </div>
          </div>

          <form action={action} className="champ" style={{ gap: 12 }}>
            <input name="nom" required minLength={2} maxLength={80}
                   placeholder="Atelier Vaillant" aria-label="Nom du site"
                   autoFocus disabled={enCours} />
            <button className="gros-bouton" disabled={enCours}>
              {enCours ? "Ouverture…" : "Ouvrir le projet"}
            </button>
            {etat?.souci && <p className="avis mauvais">{etat.souci}</p>}
          </form>
        </div>
      </div>
    </section>
  );
}
