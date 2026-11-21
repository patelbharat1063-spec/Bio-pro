-- Lifetime student performance analytics for Advanced NEET Pro
-- Safe additive migration: preserves all existing attempts and question records.
alter table public.neet_questions
  add column if not exists subtopic_name text;

create or replace function public.neet_staff_student_attempt_history(
  p_student_user_id uuid,
  p_limit integer default 500,
  p_offset integer default 0
)
returns table (
  id uuid,
  exam_title text,
  subject text,
  total_questions integer,
  attempted_count integer,
  correct_count integer,
  score integer,
  accuracy numeric,
  weak_topics jsonb,
  question_results jsonb,
  completed_at timestamptz
)
language plpgsql
stable
security definer
set search_path = ''
as $function$
begin
  if auth.uid() is null or not exists (
    select 1
    from public.neet_profiles p
    where p.user_id = auth.uid()
      and lower(coalesce(p.role, '')) in ('admin', 'teacher')
      and lower(coalesce(p.approval_status, 'approved')) = 'approved'
  ) then
    raise exception 'Approved Teacher or Admin access required';
  end if;

  if not exists (
    select 1
    from public.neet_profiles p
    where p.user_id = p_student_user_id
      and lower(coalesce(p.role, 'student')) = 'student'
  ) then
    raise exception 'Student account not found';
  end if;

  return query
  select a.id, a.exam_title, a.subject, a.total_questions,
         a.attempted_count, a.correct_count, a.score, a.accuracy,
         a.weak_topics, a.question_results, a.completed_at
  from public.neet_student_attempts a
  where a.user_id = p_student_user_id
  order by a.completed_at desc, a.id
  limit greatest(1, least(coalesce(p_limit, 500), 1000))
  offset greatest(0, coalesce(p_offset, 0));
end;
$function$;

revoke all on function public.neet_staff_student_attempt_history(uuid, integer, integer) from public;
grant execute on function public.neet_staff_student_attempt_history(uuid, integer, integer) to authenticated;
