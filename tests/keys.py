from pytezos.crypto.key import Key

key = Key.from_encoded_key("edpkv8Wo2t5ALJLx8ie3znraLDTk7myLSuPofh55XTmRcphH7wQ4hx")
print(key.public_key_hash())