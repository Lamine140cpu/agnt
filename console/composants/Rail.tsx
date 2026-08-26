/**
 * L'état du contrat, en permanence sous les yeux.
 *
 * Les questions ouvertes sont AUSSI VISIBLES que les faits vérifiés, et
 * c'est délibéré : un trou signalé est le produit, pas un défaut. Les
 * masquer donnerait l'impression d'une page complète, qui est exactement
 * l'impression qu'on refuse de donner.
 */
import type { Fait } from "@/lib/contrat";

export default function Rail({ faits }: { faits: Fait[] }) {
  const vus = faits.filter((f) => f.valeur != null);
  const ouverts = faits.filter((f) => f.valeur == null);

  return (
    <aside className="rail">
      <div className="bloc">
        <div className="bloc-tete">
          <span className="eti">Faits vérifiés</span><b>{vus.length}</b>
        </div>
        {vus.length === 0 ? <p className="rien">rien encore</p> : vus.map((f) => (
          <div className="fait" key={f.cle}>
            <div className="k">{f.cle}</div>
            <div className="v">
              <span>{f.valeur}</span>
              <em className={`src ${f.origine}`}>{f.origine}</em>
            </div>
          </div>
        ))}
      </div>

      <div className="bloc">
        <div className="bloc-tete">
          <span className="eti">Questions ouvertes</span><b>{ouverts.length}</b>
        </div>
        {ouverts.length === 0 ? <p className="rien">rien encore</p> : ouverts.map((f) => (
          <div className="ouvert" key={f.cle}><i /><span>{f.cle.replace(/_/g, " ")}</span></div>
        ))}
      </div>
    </aside>
  );
}
