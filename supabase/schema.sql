create table public.boss_worldcup_results (
  game_id uuid primary key,
  winner_id bigint not null references public.boss_worldcup_items(id) on delete restrict,
  created_at timestamptz not null default now()
);
comment on table public.boss_worldcup_results is '게임별 최종 우승 기록. 같은 game_id는 한 번만 저장.';
comment on column public.boss_worldcup_results.game_id is '게임 시작 시 생성한 UUID. 재시도에도 동일한 값을 사용.';
comment on column public.boss_worldcup_results.winner_id is 'boss_worldcup_items.id를 참조하는 우승 후보';
create index boss_worldcup_results_winner_id_idx on public.boss_worldcup_results(winner_id);
alter table public.boss_worldcup_results enable row level security;
revoke all on public.boss_worldcup_results from public, anon, authenticated;
grant select, insert on public.boss_worldcup_results to service_role;
create policy results_server_only on public.boss_worldcup_results for all to service_role using (true) with check (true);

create view public.boss_worldcup_rankings with (security_invoker = true) as
select i.id as winner_id, i.content, count(r.game_id) as win_count,
  coalesce(round(100.0 * count(r.game_id) / nullif(sum(count(r.game_id)) over (), 0), 2), 0) as win_percentage
from public.boss_worldcup_items i
left join public.boss_worldcup_results r on r.winner_id = i.id
group by i.id, i.content;
comment on view public.boss_worldcup_rankings is '후보별 우승 횟수 및 전체 완료 게임 대비 우승 비율. win_count DESC로 정렬.';
revoke all on public.boss_worldcup_rankings from public, anon, authenticated;
grant select on public.boss_worldcup_rankings to service_role;
grant select on public.boss_worldcup_items to service_role;
