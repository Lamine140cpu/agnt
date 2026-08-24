/**
 * La fenêtre de projection.
 *
 * ELLE RESTE NOIRE TANT QU'IL N'Y A RIEN À MONTRER. C'est un choix, pas un
 * manque : afficher un brouillon plausible en attendant donnerait à voir une
 * page qui n'a pas été contrôlée, et personne ne saurait plus laquelle des
 * deux est la vraie.
 */
export default function Projection({ url, etat }: { url: string | null; etat: string }) {
  return (
    <div className="projo">
      <div className="ecran">
        {url ? (
          <iframe
            src={url}
            title="Le site en cours"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", border: 0 }}
            sandbox="allow-scripts allow-same-origin"
          />
        ) : (
          <div className="vide">
            <p className="gros">Rien à projeter</p>
            <p>
              {etat === "parler"
                ? "La fenêtre s'allume quand le contrat a de quoi écrire une page."
                : "La page est en cours de fabrication. Elle apparaîtra une fois contrôlée."}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
