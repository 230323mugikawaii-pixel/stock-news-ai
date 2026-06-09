# stock-news-ai

## 🐔 養鶏場用停電・復電通知システム

Gmail APIを使用して停電・復電関連のメールを監視し、Pushover Emergency通知で24時間いつでもアラートを受け取るシステムです。複数人への同時通知にも対応しています。

### ✨ 主な機能

- **24時間監視**: Render Background Workerで継続稼働
- **1分間隔チェック**: カスタマイズ可能な監視頻度
- **自動キーワード検出**: 以下のキーワードを自動検知
  - 停電
  - 復電
  - 通電
  - 電源断
  - 異常
  - 電圧
  - 発電機
- **Emergency通知**: Pushover緊急通知（30秒ごとに最大6時間繰り返し）
- **複数人通知**: カンマ区切りで複数の受信者に通知可能
- **通知ON/OFF切り替え**: ALERT_ENABLED環境変数で簡単に制御
- **テストモード**: 起動時に動作確認用テスト通知を送信
- **重複通知防止**: 同じメールで24時間以内の重複通知なし
- **ログ記録**: すべての動作をログファイルに記録

---

## ⚠️ 重要な注意事項

### 音量について

**Pushover Emergency通知は、スマートフォンの音量設定に依存します。**

- ✅ スマートフォンの**ボリュームを最大に設定**してください
- ✅ 静かなモードは解除してください
- ❌ 50dBなどの固定音量指定はスマートフォン側で保証できません
- ❌ Pushover側で音量を指定することはできません

**推奨設定:**
1. スマートフォンの音量を最大に設定
2. サイレント/マナーモードをOFF
3. Pushoverアプリの通知設定でサウンドをON

---

## 🚀 セットアップガイド

### 前提条件

- Google Cloud アカウント
- Pushover.net アカウント
- Render アカウント（無料プランOK）

---

### Step 1: Google Cloud コンソール設定

#### 1-1. プロジェクト作成

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成（例：`poultry-farm-alerts`）
3. プロジェクトを選択

#### 1-2. Gmail API を有効化

1. 左メニューから「API とサービス」→「ライブラリ」
2. 「Gmail API」を検索
3. 「Gmail API」をクリック
4. 「有効にする」をクリック

#### 1-3. サービスアカウント作成

1. 左メニューから「API とサービス」→「認証情報」
2. 「認証情報を作成」→「サービスアカウント」
3. サービスアカウント名を入力（例：`poultry-farm-worker`）
4. 「作成して続行」をクリック
5. ロール選択で「基本」→「エディタ」を選択
6. 「続行」→「完了」をクリック

#### 1-4. JSON キー生成

1. 作成したサービスアカウントをクリック
2. 「キー」タブを開く
3. 「キーを追加」→「新しいキーを作成」
4. キータイプで「JSON」を選択
5. 「作成」をクリック
6. ダウンロードされたJSONファイルを保存

#### 1-5. Gmail 委譲設定

1. Google Cloud Console で「API とサービス」→「Domain-wide delegation」
2. サービスアカウントのOAuth同意画面設定を完了
3. 監視対象のGmailアカウントでサービスアカウントに閲覧権限を付与

**重要**: Gmail APIを使う場合、監視対象のGmailアカウントのオーナーが、サービスアカウントのクライアントIDに対して閲覧権限を付与する必要があります。

---

### Step 2: Pushover 設定

#### 2-1. アカウント登録

1. [Pushover.net](https://pushover.net/) にアクセス
2. アカウント登録（メールアドレスで登録）
3. ダッシュボードで「User Key」をコピー（後で使用）

#### 2-2. アプリケーション登録

1. 「Create an Application/API Token」をクリック
2. アプリケーション名を入力（例：`Poultry Farm Alerts`）
3. 説明を入力
4. 「Create Application」をクリック
5. 生成された「API Token」をコピー（後で使用）

#### 2-3. 通知デバイス設定

1. Pushover アプリをスマートフォンにインストール（iOS/Android）
2. Pushover アカウントでログイン
3. **スマートフォンの音量を最大に設定**
4. Render から通知が来ることを確認

---

### Step 3: Render デプロイ

#### 3-1. Render に接続

1. [Render Dashboard](https://dashboard.render.com/) にアクセス
2. GitHub アカウントで接続
3. リポジトリ `stock-news-ai` を選択

#### 3-2. 環境変数を設定

Render Dashboard で「Environment」から以下を追加:

```
GMAIL_CREDENTIALS_JSON=<JSONの全文を1行で貼り付け>
ALERT_ENABLED=true
TEST_MODE=false
TEST_EMAIL_TO=
PUSHOVER_USER_KEY=<Pushover User Key>
PUSHOVER_API_KEY=<Pushover API Token>
CHECK_INTERVAL_SECONDS=60
```

**GMAIL_CREDENTIALS_JSON の設定方法:**

1. ダウンロードしたサービスアカウント JSON ファイルをテキストエディタで開く
2. 全文をコピー（改行を含む）
3. Render の環境変数に貼り付け
4. Render は自動的に改行を処理します

**複数人への通知を設定する場合（PUSHOVER_USER_KEY）:**

```
PUSHOVER_USER_KEY=user1_key,user2_key,user3_key
```

カンマ区切りで複数のキーを指定すると、すべてのユーザーに通知が送信されます。

#### 3-3. render.yaml でデプロイ

このリポジトリに `render.yaml` が含まれているため、自動的に Background Worker として設定されます。

```bash
git push  # render.yaml が自動検出されます
```

または Render Dashboard で:
1. 「Create +」→「Background Worker」
2. リポジトリを選択
3. 「Create Background Worker」

---

### Step 4: テストモード で動作確認

#### 4-1. テストモードの有効化

Render Dashboard で以下の環境変数を設定:

```
TEST_MODE=true
TEST_EMAIL_TO=your-email@gmail.com
```

#### 4-2. Worker を再起動

- Render Dashboard でWorkerを再起動
- ログに以下が表示されることを確認:
  ```
  TEST MODE: Sending test notifications...
  TEST MODE: Sending test email to your-email@gmail.com
  TEST MODE: Test notifications sent, system will continue normally
  ```

#### 4-3. 通知確認

- Pushover アプリでテスト通知を確認
- Gmailで「停電 テスト通知」メールを確認

#### 4-4. テストモード を無効化

テスト完了後、テストモードをOFFにします:

```
TEST_MODE=false
TEST_EMAIL_TO=
```

Worker を再起動します。

---

### Step 5: 運用開始

#### 5-1. 通知の有効/無効切り替え

**通知を一時的に無効にしたい場合:**

```
ALERT_ENABLED=false
```

**通知を再開する場合:**

```
ALERT_ENABLED=true
```

環境変数を変更後、Worker を再起動してください。

#### 5-2. 実メールで動作確認

監視対象の Gmail に以下の件名でメールを送信:

```
テスト: 停電が発生しました
```

Pushover アプリで通知を受信することを確認してください。

---

## 📋 環境変数リファレンス

| 環境変数名 | 説明 | 例/デフォルト | 必須 |
|-----------|------|------------|------|
| `GMAIL_CREDENTIALS_JSON` | Google Service Account JSON（1行） | `{"type":"service_account",...}` | ✅ |
| `ALERT_ENABLED` | 通知の有効/無効 | `true` または `false` | - |
| `TEST_MODE` | テストモード有効化 | `true` または `false` | - |
| `TEST_EMAIL_TO` | テストメール送信先（TEST_MODEがtrueのみ） | メールアドレス | - |
| `PUSHOVER_USER_KEY` | Pushover ユーザーキー（カンマ区切り対応） | `u1234567890abcdef` | ✅ |
| `PUSHOVER_API_KEY` | Pushover API トークン | `app1234567890abcdef` | ✅ |
| `CHECK_INTERVAL_SECONDS` | メール監視の間隔（秒） | `60` | - |

---

## 📊 通知の動作

### Emergency通知の特性

- **Priority**: 2（Emergency）
- **Retry**: 30秒ごと
- **Expire**: 6時間後に自動停止
- **サウンド**: スマートフォン側の設定に従う

**例:** 停電通知が来たら、6時間以内に確認するまで30秒ごとに鳴り続けます。

### 重複通知の防止

- 同じメールIDで24時間以内に複数回の通知は送信されません
- 別のメールからの通知は24時間以内でも送信されます

---

## 🧪 ローカル開発

### セットアップ

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 環境変数設定

```bash
cp .env.example .env
# .env をエディタで開いて、実際の値を入力
```

### 実行

```bash
python worker.py
```

---

## 📝 ログファイル

Worker は以下のファイルにログを記録します:
- `worker.log` - すべての監視動作、通知送信記録、エラー情報

---

## 🔒 セキュリティに関する注意

⚠️ **重要**: 

- `GMAIL_CREDENTIALS_JSON` は秘密鍵です。決してコードに直接記載しないでください
- `.env` ファイルは `.gitignore` に含めてコミットしないでください
- サービスアカウントキーはセキュアに管理してください
- Pushover API キーも秘密情報です
- Render の環境変数は暗号化されて保存されます

---

## 🛠️ トラブルシューティング

### 通知が来ない場合

1. **Render ログ確認**
   ```
   Dashboard → Background Worker → Logs
   ```
   エラーメッセージを確認

2. **スマートフォン設定確認**
   - 音量が最大か
   - サイレント/マナーモードがONになっていないか
   - Pushover アプリが最新版か

3. **Gmail API 設定確認**
   - サービスアカウントが正しく作成されているか
   - Gmail API が有効化されているか
   - 委譲設定が完了しているか

4. **Pushover 設定確認**
   - User Key が正しいか
   - API Token が正しいか
   - Pushover アプリがログイン状態か

### メール検出されない場合

1. テストメールに[対応キーワード](#-主な機能)が含まれているか確認
2. メールがアーカイブ/削除されていないか確認
3. `CHECK_INTERVAL_SECONDS` が適切に設定されているか確認
4. `ALERT_ENABLED=true` に設定されているか確認

### "GMAIL_CREDENTIALS_JSON not set" エラー

1. Render Dashboard で環境変数が設定されているか確認
2. 改行が含まれていないか確認（1行のJSON）
3. 間違った認証情報ではないか確認

### 複数人に通知されない場合

1. `PUSHOVER_USER_KEY` がカンマ区切りで設定されているか確認
   ```
   user1_key,user2_key,user3_key  # 正しい
   user1_key, user2_key, user3_key # スペース入っていないか確認
   ```
2. 各ユーザーキーが正しいか確認

---

## 📞 サポート

問題が発生した場合:

1. `worker.log` を確認
2. Render Dashboard のログを確認
3. Google Cloud Console で API の状態を確認
4. Pushover.net でアカウント状態を確認

---

## 📝 ライセンス

MIT License

---

## 🤝 貢献

バグ報告や機能提案は Issue/PR でお願いします。

---

**最終更新**: 2026年6月9日
