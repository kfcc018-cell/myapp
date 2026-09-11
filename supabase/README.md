# Supabase 스키마

프로젝트: `uvkdwnedqxgczeterdef` (`test project`)

`schema.sql`은 이미 적용된 `create_boss_worldcup_results_and_rankings` 마이그레이션의 참조 사본입니다. 재실행하지 마세요. 기존 `boss_worldcup_items`의 id/content를 사용합니다.

- `boss_worldcup_results`: game_id(UUID PK), winner_id(후보 FK), created_at(timestamptz)
- `boss_worldcup_rankings`: winner_id, content, win_count, win_percentage
- 기존 RLS와 서버 전용 권한을 유지합니다. 앱은 서버의 Supabase secret key로 접근합니다.

```sql
select * from public.boss_worldcup_rankings order by win_count desc, winner_id;
```
