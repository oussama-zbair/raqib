-- Migration 001 — bot settings columns
-- Safe to run on an existing Raqib database (idempotent).
-- Run in the Supabase SQL editor.

alter table users    add column if not exists is_owner    boolean  default false;
alter table profiles add column if not exists paused      boolean  default false;
alter table profiles add column if not exists quiet_start smallint;
alter table profiles add column if not exists quiet_end   smallint;

-- Optionally mark yourself as the bot owner (replace with your Telegram user id):
-- update users set is_owner = true where telegram_user_id = <YOUR_TELEGRAM_USER_ID>;
