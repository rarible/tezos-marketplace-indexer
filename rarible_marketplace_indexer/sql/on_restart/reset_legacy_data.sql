--delete from marketplace_order where platform = 'RARIBLE_V1';
--delete from marketplace_activity where platform = 'RARIBLE_V1';
--delete from legacy_orders;
--delete from dipdup_index where name = 'rarible_exchange_legacy_actions';
--delete from dipdup_index where name = 'rarible_exchange_legacy_data_actions';
--delete from indexing_status where index = 'LEGACY_ORDERS';
delete from indexing_status where index = 'V1_CLEANING';