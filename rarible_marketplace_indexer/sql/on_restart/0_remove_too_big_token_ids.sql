delete from token_transfer where length(token_id) > 256;
delete from token where length(token_id) > 256;
delete from ownership where length(token_id) > 256;
delete from royalties where length(token_id) > 256;
delete from metadata_token where length(token_id) > 256;
delete from marketplace_order where length(make_token_id) > 256;
delete from marketplace_order where length(take_token_id) > 256;
delete from marketplace_activity where length(make_token_id) > 256;
delete from marketplace_activity where length(take_token_id) > 256;





