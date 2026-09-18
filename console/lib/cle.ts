/**
 * La clé d'un projet : c'est le nom du dossier servi, donc il n'a droit
 * ni aux accents, ni aux majuscules, ni aux espaces.
 *
 * La contrainte de la base l'impose déjà (`^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$`).
 * On la fabrique ici pour que l'utilisateur n'ait pas à la deviner — pas
 * pour remplacer le contrôle, qui reste en base où personne ne peut le
 * contourner.
 */
export function cleDepuis(nom: string): string {
  const c = nom
    .normalize("NFD").replace(/\p{Mn}/gu, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 40)
    .replace(/-+$/, "");
  // Un nom entièrement non latin (« 工房 ») donnerait une clé vide, que la
  // base refuserait sans rien expliquer. On retombe sur quelque chose de
  // valide plutôt que d'exposer une erreur de contrainte.
  return c.length >= 3 ? c : `site-${Date.now().toString(36).slice(-6)}`;
}
