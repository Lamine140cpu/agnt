-- =====================================================================
--  Ultra Motion — le socle
--
--  UNE RÈGLE TRAVERSE CE FICHIER : le contrat est la source de vérité, et
--  chaque valeur y porte son origine. La base ne stocke donc pas « le
--  téléphone du client » mais « le téléphone, et d'où il vient ». Un fait
--  sans source ne peut pas exister : la contrainte l'interdit.
--
--  Les politiques de ligne sont écrites ICI, en même temps que les tables.
--  Ajoutées après coup, elles laissent toujours une table découverte.
-- =====================================================================

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------- comptes

create table public.comptes (
  id           uuid primary key references auth.users(id) on delete cascade,
  courriel     text not null,
  nom          text,
  -- La facturation vit ici, pas dans une table à part : un compte a un
  -- plan, et c'est tout ce dont l'application a besoin de savoir.
  client_stripe        text unique,
  abonnement_stripe    text unique,
  plan         text not null default 'essai'
               check (plan in ('essai', 'atelier', 'studio')),
  plan_jusqu_a timestamptz,
  cree_le      timestamptz not null default now()
);
comment on column public.comptes.plan is
  'essai : un site, sans publication. atelier / studio : voir droits().';

alter table public.comptes enable row level security;

create policy "on lit son compte" on public.comptes
  for select using (auth.uid() = id);
create policy "on modifie son compte" on public.comptes
  for update using (auth.uid() = id) with check (auth.uid() = id);
-- Aucune politique d'insertion ni de suppression : la ligne est créée par
-- le déclencheur ci-dessous, et un compte ne se supprime que par la
-- suppression de l'utilisateur.

create or replace function public.compte_a_la_creation()
returns trigger language plpgsql security definer set search_path = '' as $$
begin
  insert into public.comptes (id, courriel, nom)
  values (new.id, new.email, new.raw_user_meta_data->>'name');
  return new;
end $$;

create trigger creer_compte
  after insert on auth.users
  for each row execute function public.compte_a_la_creation();

-- ---------------------------------------------------------------- projets

create table public.projets (
  id        uuid primary key default gen_random_uuid(),
  compte    uuid not null references public.comptes(id) on delete cascade,
  nom       text not null,
  -- L'identifiant du dossier servi : minuscules, sans accent, sans espace.
  cle       text not null check (cle ~ '^[a-z0-9][a-z0-9-]{1,38}[a-z0-9]$'),
  etat      text not null default 'parler'
            check (etat in ('parler','contrat','ecrire','filmer','decouper',
                            'construire','controler','pret','publie')),
  -- LE CONTRAT. Tout le reste en découle. Il est ici en entier plutôt
  -- qu'éclaté en colonnes : le moteur le lit tel quel, et une colonne
  -- oubliée serait un champ que le contrôleur ne verrait jamais.
  contrat   jsonb not null default '{}'::jsonb,
  publie_le timestamptz,
  url       text,
  cree_le   timestamptz not null default now(),
  maj_le    timestamptz not null default now(),
  unique (compte, cle)
);

create index projets_compte_idx on public.projets (compte, maj_le desc);

alter table public.projets enable row level security;

create policy "on voit ses projets" on public.projets
  for select using (auth.uid() = compte);
create policy "on crée ses projets" on public.projets
  for insert with check (auth.uid() = compte);
create policy "on modifie ses projets" on public.projets
  for update using (auth.uid() = compte) with check (auth.uid() = compte);
create policy "on supprime ses projets" on public.projets
  for delete using (auth.uid() = compte);

-- --------------------------------------------------------------- messages

create table public.messages (
  id      bigserial primary key,
  projet  uuid not null references public.projets(id) on delete cascade,
  role    text not null check (role in ('client','cheffe','journal')),
  -- 'journal' porte ce que le MOTEUR a fait, pas ce qui a été dit. Les
  -- mélanger ferait passer une mesure pour une opinion.
  texte   text not null,
  meta    jsonb not null default '{}'::jsonb,
  cree_le timestamptz not null default now()
);

create index messages_projet_idx on public.messages (projet, id);

alter table public.messages enable row level security;

-- On passe par le projet : une politique qui referait le lien à la main
-- finirait par diverger de celle des projets.
create policy "on lit les messages de ses projets" on public.messages
  for select using (exists (
    select 1 from public.projets p
    where p.id = messages.projet and p.compte = auth.uid()));
create policy "on écrit dans ses projets" on public.messages
  for insert with check (exists (
    select 1 from public.projets p
    where p.id = messages.projet and p.compte = auth.uid()));

-- ------------------------------------------------------------------ faits
--
--  LA TABLE QUI PORTE TOUTE LA DISCIPLINE DU PROJET.
--
--  Un fait sans origine n'entre pas : la contrainte le refuse. Et une
--  origine 'registre' exige de dire QUAND on a interrogé le registre —
--  une immatriculation lue il y a trois ans n'est plus une vérification,
--  c'est un souvenir.

create table public.faits (
  id      bigserial primary key,
  projet  uuid not null references public.projets(id) on delete cascade,
  cle     text not null,
  valeur  text,
  origine text check (origine in ('registre','client','mesure','choix')),
  source  text,
  releve_le timestamptz,
  cree_le timestamptz not null default now(),
  unique (projet, cle),

  -- Une valeur nulle est une QUESTION OUVERTE : elle a le droit de n'avoir
  -- ni origine ni source. Une valeur remplie, jamais.
  constraint fait_sourcé check (
    valeur is null or (origine is not null and source is not null)),

  -- Ce qui vient d'un registre doit dire quand il a été lu.
  constraint registre_daté check (
    origine is distinct from 'registre' or releve_le is not null)
);

create index faits_projet_idx on public.faits (projet, cle);

alter table public.faits enable row level security;

create policy "on lit les faits de ses projets" on public.faits
  for select using (exists (
    select 1 from public.projets p
    where p.id = faits.projet and p.compte = auth.uid()));
create policy "on écrit les faits de ses projets" on public.faits
  for all using (exists (
    select 1 from public.projets p
    where p.id = faits.projet and p.compte = auth.uid()))
  with check (exists (
    select 1 from public.projets p
    where p.id = faits.projet and p.compte = auth.uid()));

-- ------------------------------------------------------------------ tâches
--
--  La file que l'ouvrier Python dépile. Le moteur reste en Python : il
--  porte quarante contrôles éprouvés, une boucle de reprise et un
--  contrôleur. Le réécrire en TypeScript, ce serait repayer tous les
--  défauts déjà payés.

create table public.taches (
  id       bigserial primary key,
  projet   uuid not null references public.projets(id) on delete cascade,
  quoi     text not null
           check (quoi in ('filmer','construire','controler','publier')),
  etat     text not null default 'en-attente'
           check (etat in ('en-attente','en-cours','faite','refusee','erreur')),
  -- 'refusee' n'est PAS 'erreur'. Une barrière qui dit non a fonctionné ;
  -- les confondre ferait passer un contrôle réussi pour une panne.
  charge   jsonb not null default '{}'::jsonb,
  journal  jsonb not null default '[]'::jsonb,
  motif    text,
  essais   int not null default 0,
  pris_par text,
  pris_le  timestamptz,
  fini_le  timestamptz,
  cree_le  timestamptz not null default now()
);

create index taches_a_faire_idx on public.taches (etat, id)
  where etat = 'en-attente';
create index taches_projet_idx on public.taches (projet, id desc);

alter table public.taches enable row level security;

create policy "on suit les tâches de ses projets" on public.taches
  for select using (exists (
    select 1 from public.projets p
    where p.id = taches.projet and p.compte = auth.uid()));
-- Personne ne crée ni ne modifie une tâche depuis le navigateur : c'est le
-- serveur (clé de service) qui les pose, et l'ouvrier qui les prend.

-- Prise de tâche atomique : deux ouvriers qui démarrent ensemble ne
-- doivent pas prendre la même. `skip locked` est ce qui l'empêche.
create or replace function public.prendre_tache(nom_ouvrier text)
returns public.taches language plpgsql security definer set search_path = '' as $$
declare t public.taches;
begin
  select * into t from public.taches
   where etat = 'en-attente'
   order by id
   for update skip locked
   limit 1;
  if not found then return null; end if;
  update public.taches
     set etat = 'en-cours', pris_par = nom_ouvrier, pris_le = now(),
         essais = essais + 1
   where id = t.id
   returning * into t;
  return t;
end $$;

revoke all on function public.prendre_tache(text) from public, anon, authenticated;

-- ------------------------------------------------------------------ droits
--
--  Ce que chaque plan permet. Écrit en base plutôt qu'en TypeScript : le
--  serveur et l'ouvrier doivent lire la MÊME règle, sans quoi l'un des deux
--  finira par autoriser ce que l'autre refuse.

create or replace function public.droits(p text)
returns jsonb language sql immutable as $$
  select case p
    when 'studio'  then '{"projets": 50, "publier": true,  "films_par_mois": 30}'::jsonb
    when 'atelier' then '{"projets": 5,  "publier": true,  "films_par_mois": 5}'::jsonb
    else                '{"projets": 1,  "publier": false, "films_par_mois": 1}'::jsonb
  end $$;

create or replace function public.maj_le()
returns trigger language plpgsql as $$
begin new.maj_le = now(); return new; end $$;

create trigger projets_maj before update on public.projets
  for each row execute function public.maj_le();
