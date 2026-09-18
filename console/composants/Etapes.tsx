const ETAPES = ["parler", "contrat", "ecrire", "filmer", "decouper",
                "construire", "controler"] as const;

export default function Etapes({ etat }: { etat: string }) {
  const i = Math.max(0, ETAPES.indexOf(etat as typeof ETAPES[number]));
  return (
    <div className="barre">
      {ETAPES.map((e, n) => (
        <div key={e} style={{ display: "contents" }}>
          <div className={`pas ${n < i ? "clos" : n === i ? "en" : ""}`}>
            <i /><span>{e}</span>
          </div>
          {n < ETAPES.length - 1 && <div className="tir" />}
        </div>
      ))}
    </div>
  );
}
