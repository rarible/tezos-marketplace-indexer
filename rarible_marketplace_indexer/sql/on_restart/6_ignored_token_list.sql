update royalties set royalties_retries = 0, royalties_synced = false;
update metadata_token
set metadata_retries = 5
where contract in ('KT1GBZmSxmnKJXGMdMLbugPfLyUPmuLSMwKS',
                   'KT19hzFPbMW9cYgUhLNghytkWEymMKsPrdfX',
                   'KT1BtmMAnmTGHAA9ZV8xPzuwZu4ibL7f5qb3',
                   'KT1CJAbNconerFWduN9zp6xBtSTwZTZmphry',
                   'KT1FVbyctinHvVJNyMWeueCzXFFX2MCqsYDj',
                   'KT1TnVQhjxeNvLutGvzwZvYtC7vKRpwPWhc6',
                   'KT1KVfQzyjxoKx2WjcVAatknW3YsR37cCA6s',
                   'KT1Up463qVJqtW5KF7dQZz5SsWMiS32GtBrw',
                   'KT1SnRKkheSvY6jfvvuVufqWPiAhiyaPhn65',
                   'KT1VBe538e2ucXhdWdoaFnLpyCiTkvsPkyZm',
                   'KT1NXC6Yj9uGiYMbkwTaoRjqwzFLEG57ki5c',
                   'KT1TybJgA4Tm2Lv2ZKj4kwjGTLoACywKbmhg',
                   'KT1Tt7bLkYnJnug7irtYEDK4qCq5twyZCEAV');
update royalties
set royalties_retries = 5
where contract in ('KT1GBZmSxmnKJXGMdMLbugPfLyUPmuLSMwKS',
                   'KT19hzFPbMW9cYgUhLNghytkWEymMKsPrdfX',
                   'KT1BtmMAnmTGHAA9ZV8xPzuwZu4ibL7f5qb3',
                   'KT1CJAbNconerFWduN9zp6xBtSTwZTZmphry',
                   'KT1FVbyctinHvVJNyMWeueCzXFFX2MCqsYDj',
                   'KT1TnVQhjxeNvLutGvzwZvYtC7vKRpwPWhc6',
                   'KT1KVfQzyjxoKx2WjcVAatknW3YsR37cCA6s',
                   'KT1Up463qVJqtW5KF7dQZz5SsWMiS32GtBrw',
                   'KT1SnRKkheSvY6jfvvuVufqWPiAhiyaPhn65',
                   'KT1VBe538e2ucXhdWdoaFnLpyCiTkvsPkyZm',
                   'KT1NXC6Yj9uGiYMbkwTaoRjqwzFLEG57ki5c',
                   'KT1TybJgA4Tm2Lv2ZKj4kwjGTLoACywKbmhg',
                   'KT1Tt7bLkYnJnug7irtYEDK4qCq5twyZCEAV');