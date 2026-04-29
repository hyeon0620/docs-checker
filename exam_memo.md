あなたのコードの動き

```
def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

```
password_hash # str: "$2b$12$abc...xyz" ← DBから読み込んだ瞬間はこれ（str）
password_hash.encode() # bytes: b"$2b$12$abc...xyz" ← bcrypt に渡せる形に変換
DB に保存されてる時点では str（テキスト） で、bcrypt のライブラリは bytes しか受け取らないから変換してる。中身は変わらない、書き方が変わるだけ。
```

sessionはDBと繋ぐために必要。
