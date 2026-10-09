create extension if not exists pgcrypto;

create type public.recommendation_action as enum ('markdown','replenish','transfer','bundle','customer_campaign','donate','dispose','monitor');
create type public.recommendation_status as enum ('proposed','approved','rejected','executed','expired','cancelled');
create type public.movement_type as enum ('receipt','sale','waste','transfer_in','transfer_out','donation','return','adjustment','bundle_sale');
create type public.consent_status as enum ('unknown','granted','withdrawn');
create type public.food_disposition as enum ('pending_review','eligible_for_donation','donated','disposed','ineligible');

create table public.profiles (
 id uuid primary key references auth.users(id) on delete cascade,
 display_name text, role text not null default 'planner' check (role in ('admin','planner','store_manager','analyst','viewer')),
 created_at timestamptz not null default now()
);
create table public.stores (
 id uuid primary key default gen_random_uuid(), code text not null unique, name text not null, address text,
 latitude numeric(9,6), longitude numeric(9,6), timezone text not null default 'Asia/Kolkata',
 is_active boolean not null default true, created_at timestamptz not null default now()
);
create table public.products (
 id uuid primary key default gen_random_uuid(), sku text not null unique, barcode text, name text not null, category text not null,
 unit text not null default 'unit', default_shelf_life_days integer check (default_shelf_life_days is null or default_shelf_life_days > 0),
 selling_price numeric(12,2) not null check (selling_price >= 0), unit_cost numeric(12,2) not null check (unit_cost >= 0),
 min_margin_percent numeric(5,2) not null default 0 check (min_margin_percent between 0 and 100),
 is_perishable boolean not null default true, is_active boolean not null default true,
 created_at timestamptz not null default now(), updated_at timestamptz not null default now()
);
create index products_category_idx on public.products(category);

create table public.inventory_batches (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_code text not null,
 received_at timestamptz not null default now(), expiry_date date not null,
 quantity_received integer not null check (quantity_received >= 0), quantity_on_hand integer not null check (quantity_on_hand >= 0),
 source_receipt_ref text, last_counted_at timestamptz, created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(), unique(store_id, product_id, batch_code),
 check (quantity_on_hand <= quantity_received)
);
create index inventory_batches_store_expiry_idx on public.inventory_batches(store_id, expiry_date);
create index inventory_batches_product_idx on public.inventory_batches(product_id);

create table public.promotions (
 id uuid primary key default gen_random_uuid(), store_id uuid references public.stores(id), product_id uuid references public.products(id),
 name text not null, discount_percent numeric(5,2) not null check (discount_percent between 0 and 100),
 starts_at timestamptz not null, ends_at timestamptz not null,
 status text not null default 'draft' check (status in ('draft','pending_approval','approved','active','paused','completed','cancelled')),
 created_by uuid references public.profiles(id), approved_by uuid references public.profiles(id), created_at timestamptz not null default now(),
 check (ends_at > starts_at)
);
create table public.sales_records (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_id uuid references public.inventory_batches(id),
 sold_at timestamptz not null, quantity integer not null check (quantity > 0),
 unit_price numeric(12,2) not null check (unit_price >= 0), promotion_id uuid references public.promotions(id),
 source_ref text, created_at timestamptz not null default now()
);
create index sales_store_product_time_idx on public.sales_records(store_id, product_id, sold_at desc);
create table public.purchase_receipts (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_id uuid references public.inventory_batches(id),
 supplier_name text, received_at timestamptz not null default now(), quantity integer not null check (quantity > 0),
 unit_cost numeric(12,2) check (unit_cost is null or unit_cost >= 0), receipt_ref text, created_at timestamptz not null default now()
);
create table public.waste_records (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_id uuid references public.inventory_batches(id),
 quantity integer not null check (quantity > 0),
 reason_code text not null check (reason_code in ('expired','damaged','temperature_excursion','quality_issue','overproduction','other')),
 estimated_cost numeric(12,2) not null default 0 check (estimated_cost >= 0),
 recorded_by uuid references public.profiles(id), occurred_at timestamptz not null default now(), notes text
);
create table public.demand_forecasts (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), forecast_date date not null,
 horizon_days integer not null check (horizon_days > 0), forecast_units numeric(12,2) not null check (forecast_units >= 0),
 lower_bound numeric(12,2), upper_bound numeric(12,2), model_name text not null, model_version text,
 generated_at timestamptz not null default now(), metrics jsonb not null default '{}'::jsonb,
 unique(store_id, product_id, forecast_date, horizon_days, model_name)
);
create table public.recommendations (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid references public.products(id), batch_id uuid references public.inventory_batches(id),
 action public.recommendation_action not null, status public.recommendation_status not null default 'proposed',
 proposed_quantity integer check (proposed_quantity is null or proposed_quantity >= 0),
 discount_percent numeric(5,2) check (discount_percent is null or discount_percent between 0 and 100),
 scheduled_for timestamptz, confidence numeric(5,4) check (confidence is null or confidence between 0 and 1),
 confidence_type text not null default 'heuristic' check (confidence_type in ('calibrated','model_estimate','heuristic','not_available')),
 expected_effect jsonb not null default '{}'::jsonb, evidence jsonb not null default '[]'::jsonb,
 rationale text not null, alternatives jsonb not null default '[]'::jsonb, created_by_agent text,
 reviewed_by uuid references public.profiles(id), reviewed_at timestamptz, review_note text, executed_at timestamptz,
 execution_result jsonb not null default '{}'::jsonb, expires_at timestamptz, created_at timestamptz not null default now(),
 updated_at timestamptz not null default now()
);
create index recommendations_status_created_idx on public.recommendations(status, created_at desc);
create table public.stock_movements (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_id uuid references public.inventory_batches(id),
 movement public.movement_type not null, quantity integer not null check (quantity > 0),
 reference_type text, reference_id uuid, idempotency_key text unique, notes text,
 performed_by uuid references public.profiles(id), occurred_at timestamptz not null default now(), created_at timestamptz not null default now()
);
create index stock_movements_store_time_idx on public.stock_movements(store_id, occurred_at desc);
create table public.decision_logs (
 id uuid primary key default gen_random_uuid(), recommendation_id uuid not null references public.recommendations(id),
 actor_id uuid references public.profiles(id), event_type text not null check (event_type in ('created','edited','approved','rejected','executed','failed','cancelled')),
 before_state jsonb, after_state jsonb, note text, created_at timestamptz not null default now()
);
create table public.bundles (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id), name text not null, description text,
 status text not null default 'proposed' check (status in ('proposed','pending_approval','approved','active','paused','completed','rejected')),
 proposed_price numeric(12,2) not null check (proposed_price >= 0), estimated_unit_cost numeric(12,2) not null check (estimated_unit_cost >= 0),
 estimated_margin_percent numeric(5,2), rationale text, approved_by uuid references public.profiles(id), approved_at timestamptz,
 starts_at timestamptz, ends_at timestamptz, created_at timestamptz not null default now(),
 check (ends_at is null or starts_at is null or ends_at > starts_at)
);
create table public.bundle_items (
 bundle_id uuid not null references public.bundles(id) on delete cascade, product_id uuid not null references public.products(id),
 batch_id uuid references public.inventory_batches(id), quantity_per_bundle integer not null default 1 check (quantity_per_bundle > 0),
 primary key (bundle_id, product_id, batch_id)
);
create table public.customers (
 id uuid primary key default gen_random_uuid(), external_ref text unique, display_name text, email text, phone text, created_at timestamptz not null default now()
);
create table public.customer_consents (
 id uuid primary key default gen_random_uuid(), customer_id uuid not null references public.customers(id) on delete cascade,
 channel text not null check (channel in ('email','sms','whatsapp','push')), purpose text not null default 'marketing',
 status public.consent_status not null default 'unknown', captured_at timestamptz, source text, withdrawn_at timestamptz,
 updated_at timestamptz not null default now(), unique(customer_id, channel, purpose)
);
create table public.customer_preferences (
 customer_id uuid primary key references public.customers(id) on delete cascade, preferred_categories text[] not null default '{}',
 preferred_store_id uuid references public.stores(id), locale text, updated_at timestamptz not null default now()
);
create table public.campaigns (
 id uuid primary key default gen_random_uuid(), store_id uuid references public.stores(id), product_id uuid references public.products(id),
 promotion_id uuid references public.promotions(id), name text not null, channel text not null check (channel in ('email','sms','whatsapp','push','simulated')),
 status text not null default 'draft' check (status in ('draft','pending_approval','approved','scheduled','running','paused','completed','cancelled')),
 audience_rules jsonb not null default '{}'::jsonb, message_template text not null, starts_at timestamptz, ends_at timestamptz,
 approved_by uuid references public.profiles(id), approved_at timestamptz, sent_count integer not null default 0 check (sent_count >= 0),
 redemption_count integer not null default 0 check (redemption_count >= 0), opt_out_count integer not null default 0 check (opt_out_count >= 0),
 created_at timestamptz not null default now(), check (ends_at is null or starts_at is null or ends_at > starts_at)
);
create table public.campaign_deliveries (
 id uuid primary key default gen_random_uuid(), campaign_id uuid not null references public.campaigns(id) on delete cascade,
 customer_id uuid not null references public.customers(id), channel text not null,
 status text not null default 'queued' check (status in ('queued','simulated_sent','sent','failed','redeemed','opted_out','suppressed')),
 offer_code text, sent_at timestamptz, redeemed_at timestamptz, suppression_reason text, created_at timestamptz not null default now(),
 unique(campaign_id, customer_id, channel)
);
create table public.donation_partners (
 id uuid primary key default gen_random_uuid(), name text not null, contact_name text, contact_email text, contact_phone text,
 accepted_categories text[] not null default '{}', is_active boolean not null default true, eligibility_notes text, created_at timestamptz not null default now()
);
create table public.donation_disposal_records (
 id uuid primary key default gen_random_uuid(), store_id uuid not null references public.stores(id),
 product_id uuid not null references public.products(id), batch_id uuid references public.inventory_batches(id),
 partner_id uuid references public.donation_partners(id), quantity integer not null check (quantity > 0),
 disposition public.food_disposition not null default 'pending_review', eligibility_checked_at timestamptz,
 eligibility_checked_by uuid references public.profiles(id), eligibility_basis text, handover_at timestamptz,
 disposal_reason text, proof_reference text, created_by uuid references public.profiles(id), created_at timestamptz not null default now(),
 check (disposition <> 'donated' or (partner_id is not null and eligibility_checked_at is not null))
);
create table public.ai_runs (
 id uuid primary key default gen_random_uuid(), run_type text not null check (run_type in ('demand','freshness','replenishment','markdown','transfer','orchestration','copilot','bundle','campaign','donation')),
 store_id uuid references public.stores(id), input_summary jsonb not null default '{}'::jsonb, output_summary jsonb not null default '{}'::jsonb,
 model_name text, model_version text, status text not null default 'completed' check (status in ('queued','running','completed','failed')),
 error_message text, started_at timestamptz not null default now(), completed_at timestamptz
);
create table public.evaluation_runs (
 id uuid primary key default gen_random_uuid(), name text not null, scenario jsonb not null default '{}'::jsonb,
 baseline_metrics jsonb not null default '{}'::jsonb, agent_metrics jsonb not null default '{}'::jsonb, notes text, created_at timestamptz not null default now()
);

create or replace function public.set_updated_at() returns trigger language plpgsql as $$
begin new.updated_at = now(); return new; end; $$;
create trigger products_set_updated_at before update on public.products for each row execute function public.set_updated_at();
create trigger batches_set_updated_at before update on public.inventory_batches for each row execute function public.set_updated_at();
create trigger recommendations_set_updated_at before update on public.recommendations for each row execute function public.set_updated_at();

create or replace function public.handle_new_user() returns trigger language plpgsql security definer set search_path = ''
as $$
begin
 insert into public.profiles (id, display_name) values (new.id, coalesce(new.raw_user_meta_data ->> 'full_name', new.email));
 return new;
end; $$;
create trigger on_auth_user_created after insert on auth.users for each row execute procedure public.handle_new_user();

do $$
declare t text;
begin
 foreach t in array array[
 'profiles','stores','products','inventory_batches','sales_records','purchase_receipts','promotions','waste_records',
 'demand_forecasts','recommendations','stock_movements','decision_logs','bundles','bundle_items','customers',
 'customer_consents','customer_preferences','campaigns','campaign_deliveries','donation_partners',
 'donation_disposal_records','ai_runs','evaluation_runs'
 ] loop execute format('alter table public.%I enable row level security', t); end loop;
end $$;

-- Starter read policies for authenticated hackathon users. Mutations are deliberately not open by default.
create policy "read own profile" on public.profiles for select to authenticated using (id = auth.uid());
create policy "authenticated read stores" on public.stores for select to authenticated using (true);
create policy "authenticated read products" on public.products for select to authenticated using (true);
create policy "authenticated read batches" on public.inventory_batches for select to authenticated using (true);
create policy "authenticated read sales" on public.sales_records for select to authenticated using (true);
create policy "authenticated read receipts" on public.purchase_receipts for select to authenticated using (true);
create policy "authenticated read promotions" on public.promotions for select to authenticated using (true);
create policy "authenticated read waste" on public.waste_records for select to authenticated using (true);
create policy "authenticated read forecasts" on public.demand_forecasts for select to authenticated using (true);
create policy "authenticated read recommendations" on public.recommendations for select to authenticated using (true);
create policy "authenticated read movements" on public.stock_movements for select to authenticated using (true);
create policy "authenticated read decision logs" on public.decision_logs for select to authenticated using (true);
create policy "authenticated read bundles" on public.bundles for select to authenticated using (true);
create policy "authenticated read bundle items" on public.bundle_items for select to authenticated using (true);
create policy "authenticated read customers" on public.customers for select to authenticated using (true);
create policy "authenticated read consents" on public.customer_consents for select to authenticated using (true);
create policy "authenticated read preferences" on public.customer_preferences for select to authenticated using (true);
create policy "authenticated read campaigns" on public.campaigns for select to authenticated using (true);
create policy "authenticated read deliveries" on public.campaign_deliveries for select to authenticated using (true);
create policy "authenticated read donation partners" on public.donation_partners for select to authenticated using (true);
create policy "authenticated read donation records" on public.donation_disposal_records for select to authenticated using (true);
create policy "authenticated read ai runs" on public.ai_runs for select to authenticated using (true);
create policy "authenticated read evaluation runs" on public.evaluation_runs for select to authenticated using (true);

-- Before real data: replace broad authenticated read policies with store/role-aware policies.
-- Do not expose service-role secrets to the browser. Use controlled server-side mutation endpoints.
