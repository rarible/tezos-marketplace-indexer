update royalties set royalties_retries = 0 where royalties_synced = false and royalties_retries = 5;
