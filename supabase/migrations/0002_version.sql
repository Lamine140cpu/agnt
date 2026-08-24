-- =====================================================================
--  La version publiée.
--
--  MESURÉ : Cloudflare, devant Supabase Storage, sert une copie périmée
--  après un renvoi — l'objet neuf faisait 115 355 octets, l'URL publique en
--  rendait 14, avec `cf-cache-status: EXPIRED`. Casser le cache à chaque
--  lecture reviendrait à ne plus en avoir du tout, sur onze cents images.
--
--  On publie donc sous un chemin VERSIONNÉ : `sites/<clé>/<version>/…`.
--  Rien ne peut être périmé si le chemin est neuf. Cette colonne dit
--  laquelle est servie.
-- =====================================================================

alter table public.projets
  add column if not exists version text;

comment on column public.projets.version is
  'Le préfixe de la version servie dans le seau. Nulle = jamais publié.';
