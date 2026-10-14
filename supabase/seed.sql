-- Seed data will be added with the first domain slice.
-- Supabase Auth users should be created through Auth, not this file.
-- The backend uses the Supabase service-role client for private resume uploads.
insert into storage.buckets (id, name, public)
values ('resumes', 'resumes', false)
on conflict (id) do update set public = false;
