drop index if exists idx_marketplace_order_by_maker;
CREATE INDEX idx_marketplace_order_by_maker ON public.marketplace_order USING btree (maker, status);