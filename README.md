# stock-news-ai

## 🐔 養鶏場用停電・復電通知システム

Gmail APIを使用して停電・復電関連のメールを監視し、Pushover Emergency通知で24時間いつでもアラートを受け取るシステムです。

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
- **Emergency通知**: Pushover緊急通知（確認まで繰り返し）
- **重複通知防止**: 同じメールで24時間以内の重複通知なし
- **ログ記録**: すべての動作をログファイルに記録

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
3. Render から通知が来ることを確認

---

### Step 3: Render デプロイ

#### 3-1. Render に接続

1. [Render Dashboard](https://dashboard.render.com/) にアクセス
2. GitHub アカウントで接続
3. リポジトリ `stock-news-ai` を選択

#### 3-2. 環境変数を設定

Render Dashboard で「Environment」から以下を追加:

```
CHECK_INTERVAL_SECONDS=60
GMAIL_CREDENTIALS_JSON=<JSONの全文を1行で貼り付け>
PUSHOVER_USER_KEY=<Pushover User Key>
PUSHOVER_API_KEY=<Pushover API Token>
```

**GMAIL_CREDENTIALS_JSON の設定方法:**

1. ダウンロードしたサービスアカウント JSON ファイルをテキストエディタで開く
2. 全文をコピー（改行を含む）
3. Render の環境変数に貼り付け
4. Render は自動的に改行を処理します

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

### Step 4: 動作確認

#### 4-1. テスト用メール送信

監視対象の Gmail に以下の件名でテストメールを送信:

```
テスト: 停電が発生しました
```

#### 4-2. 通知確認

スマートフォンの Pushover アプリで通知を確認してください。

#### 4-3. ログ確認

Render Dashboard で該当 Worker のログを確認:
- ✅ メール受信検出
- ✅ キーワード検知
- ✅ Pushover 通知送信成功

---

## 📋 環境変数リファレンス

| 環境変数名 | 説明 | 例/デフォルト |
|-----------|------|------------|
| `GMAIL_CREDENTIALS_JSON` | Google Service Account JSON（1行） | `{"type":"service_account",...}` |
| `PUSHOVER_USER_KEY` | Pushover ユーザーキー | `u1234567890abcdef` |
| `PUSHOVER_API_KEY` | Pushover API トークン | `app1234567890abcdef` |
| `CHECK_INTERVAL_SECONDS` | メール監視の間隔（秒） | `60` |

---

## 🔧 ローカル開発

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

## 📊 通知ログ

Worker は以下のファイルにログを記録します:
- `worker.log` - すべての監視動作、通知送信記録

---

## 🔒 セキュリティに関する注意

⚠️ **重要**: 

- `GMAIL_CREDENTIALS_JSON` は秘密鍵です。決してコードに直接記載しないでください
- `.env` ファイルは `.gitignore` に含めてコミットしないでください
- サービスアカウントキーはセキュアに管理してください
- Pushover API キーも秘密情報です

---

## 🛠️ トラブルシューティング

### 通知が来ない場合

1. **Render ログ確認**
   ```
   Dashboard → Background Worker → Logs
   ```
   エラーメッセージを確認

2. **Gmail API 設定確認**
   - サービスアカウントが正しく作成されているか
   - Gmail API が有効化されているか
   - 委譲設定が完了しているか

3. **Pushover 設定確認**
   - User Key が正しいか
   - API Token が正しいか
   - スマートフォンアプリがログイン状態か

### メール検出されない場合

1. テストメールに[対応キーワード](#-主な機能)が含まれているか確認
2. メールがアーカイブ/削除されていないか確認
3. `CHECK_INTERVAL_SECONDS` が適切に設定されているか確認

### "GMAIL_CREDENTIALS_JSON not set" エラー

1. Render Dashboard で環境変数が設定されているか確認
2. 改行が含まれていないか確認（1行のJSON）
3. 間違った認証情報ではないか確認

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

**最終更新**: 2026年6月8日
