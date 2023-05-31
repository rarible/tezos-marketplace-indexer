drop index CONCURRENTLY if exists idx_marketplace_order_by_maker;
CREATE INDEX CONCURRENTLY idx_marketplace_order_by_maker ON public.marketplace_order USING btree (maker, status);