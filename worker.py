#!/usr/bin/env python3
"""
養鶏場用停電・復電通知システム
Gmail APIを使用してメールを監視し、停電/復電関連のキーワードを検知したら
Pushover Emergency通知を送信する Background Worker
"""

import os
import json
import time
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

import requests
from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google.auth.oauthlib.flow import InstalledAppFlow
from google.api_core.exceptions import GoogleAPIError
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('worker.log')
    ]
)
logger = logging.getLogger(__name__)

# 定数
KEYWORDS = [
    '停電',
    '復電',
    '通電',
    '電源断',
    '異常',
    '電圧',
    '発電機'
]

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
NOTIFICATION_HISTORY_FILE = 'notification_history.json'


class GmailMonitor:
    """Gmail APIを使用してメールを監視するクラス"""
    
    def __init__(self):
        """Gmail Monitorを初期化"""
        self.service = None
        self.user_id = 'me'
        self._authenticate()
    
    def _authenticate(self):
        """Gmail APIの認証"""
        try:
            # 環境変数からサービスアカウントの認証情報を取得
            credentials_json = os.getenv('GMAIL_CREDENTIALS_JSON')
            
            if not credentials_json:
                logger.error("GMAIL_CREDENTIALS_JSON environment variable not set")
                raise ValueError("GMAIL_CREDENTIALS_JSON environment variable not set")
            
            # JSON文字列をパース
            credentials_info = json.loads(credentials_json)
            
            # サービスアカウント認証情報を使用
            credentials = service_account.Credentials.from_service_account_info(
                credentials_info,
                scopes=SCOPES
            )
            
            self.service = build('gmail', 'v1', credentials=credentials)
            logger.info("Gmail API authentication successful")
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse GMAIL_CREDENTIALS_JSON: {e}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_unread_messages(self) -> List[Dict]:
        """未読メールを取得"""
        try:
            results = self.service.users().messages().list(
                userId=self.user_id,
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} unread messages")
            return messages
            
        except HttpError as e:
            logger.error(f"An error occurred: {e}")
            return []
    
    def get_message_details(self, message_id: str) -> Dict:
        """メールの詳細情報を取得"""
        try:
            message = self.service.users().messages().get(
                userId=self.user_id,
                id=message_id,
                format='full'
            ).execute()
            
            headers = message['payload'].get('headers', [])
            subject = next(
                (h['value'] for h in headers if h['name'] == 'Subject'),
                'No Subject'
            )
            from_addr = next(
                (h['value'] for h in headers if h['name'] == 'From'),
                'Unknown'
            )
            
            # メール本文を取得
            body = self._get_message_body(message)
            
            return {
                'id': message_id,
                'subject': subject,
                'from': from_addr,
                'body': body,
                'snippet': message.get('snippet', '')
            }
            
        except HttpError as e:
            logger.error(f"Failed to get message details: {e}")
            return {}
    
    def _get_message_body(self, message: Dict) -> str:
        """メール本文を抽出"""
        try:
            if 'parts' in message['payload']:
                # マルチパート形式
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            return base64.urlsafe_b64decode(
                                part['body']['data']
                            ).decode('utf-8')
            else:
                # シンプル形式
                if 'data' in message['payload']['body']:
                    return base64.urlsafe_b64decode(
                        message['payload']['body']['data']
                    ).decode('utf-8')
            return ''
            
        except Exception as e:
            logger.warning(f"Failed to extract message body: {e}")
            return message.get('snippet', '')


class PushoverNotifier:
    """Pushover Emergency通知を送信するクラス"""
    
    def __init__(self):
        """Pushover Notifierを初期化"""
        self.api_url = "https://api.pushover.net/1/messages.json"
        self.user_key = os.getenv('PUSHOVER_USER_KEY')
        self.api_key = os.getenv('PUSHOVER_API_KEY')
        
        if not self.user_key or not self.api_key:
            raise ValueError(
                "PUSHOVER_USER_KEY and PUSHOVER_API_KEY environment variables must be set"
            )
    
    def send_emergency_notification(
        self,
        title: str,
        message: str,
        email_from: str = None
    ) -> bool:
        """
        Emergency通知を送信
        
        Args:
            title: 通知のタイトル
            message: 通知メッセージ
            email_from: メール送信者（オプション）
        
        Returns:
            成功時True、失敗時False
        """
        try:
            payload = {
                'user': self.user_key,
                'token': self.api_key,
                'title': title,
                'message': message,
                'priority': 2,  # Emergency priority
                'retry': 300,   # Retry every 5 minutes
                'expire': 3600  # Expire after 1 hour
            }
            
            if email_from:
                payload['message'] = f"送信元: {email_from}\n\n{message}"
            
            response = requests.post(self.api_url, data=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"Pushover notification sent successfully: {title}")
                return True
            else:
                logger.error(
                    f"Pushover notification failed: {response.status_code} - {response.text}"
                )
                return False
                
        except Exception as e:
            logger.error(f"Failed to send Pushover notification: {e}")
            return False


class NotificationManager:
    """通知履歴を管理して重複通知を防ぐクラス"""
    
    def __init__(self, history_file: str = NOTIFICATION_HISTORY_FILE):
        """
        Notification Managerを初期化
        
        Args:
            history_file: 通知履歴ファイルのパス
        """
        self.history_file = history_file
        self.history = self._load_history()
    
    def _load_history(self) -> Dict:
        """通知履歴をファイルから読み込む"""
        if Path(self.history_file).exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load notification history: {e}")
                return {}
        return {}
    
    def _save_history(self):
        """通知履歴をファイルに保存"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump(self.history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save notification history: {e}")
    
    def is_already_notified(self, message_id: str) -> bool:
        """
        同じメールで既に通知済みかチェック
        
        Args:
            message_id: メールID
        
        Returns:
            通知済みならTrue、未通知ならFalse
        """
        if message_id not in self.history:
            return False
        
        # 24時間以内の通知なら重複として扱う
        last_notified = self.history[message_id]
        notification_time = datetime.fromisoformat(last_notified)
        if datetime.now() - notification_time < timedelta(hours=24):
            return True
        
        return False
    
    def record_notification(self, message_id: str):
        """
        通知を記録
        
        Args:
            message_id: メールID
        """
        self.history[message_id] = datetime.now().isoformat()
        self._save_history()
        logger.info(f"Recorded notification for message: {message_id}")
    
    def cleanup_old_records(self, days: int = 7):
        """
        古い通知履歴を削除
        
        Args:
            days: 何日以上前のレコードを削除するか
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        expired_ids = []
        
        for message_id, notified_date in self.history.items():
            notification_time = datetime.fromisoformat(notified_date)
            if notification_time < cutoff_date:
                expired_ids.append(message_id)
        
        for message_id in expired_ids:
            del self.history[message_id]
        
        if expired_ids:
            self._save_history()
            logger.info(f"Cleaned up {len(expired_ids)} old notification records")


class PoultryFarmAlertSystem:
    """養鶏場用停電・復電通知システムのメインクラス"""
    
    def __init__(self):
        """システムを初期化"""
        self.gmail_monitor = GmailMonitor()
        self.notifier = PushoverNotifier()
        self.notification_manager = NotificationManager()
        self.check_interval = int(os.getenv('CHECK_INTERVAL_SECONDS', 60))
    
    def check_keywords(self, text: str) -> Optional[str]:
        """
        テキストにキーワードが含まれているかチェック
        
        Args:
            text: チェック対象のテキスト
        
        Returns:
            マッチしたキーワード、またはNone
        """
        text_lower = text.lower()
        for keyword in KEYWORDS:
            if keyword in text_lower:
                return keyword
        return None
    
    def process_message(self, message_id: str) -> bool:
        """
        メッセージを処理
        
        Args:
            message_id: メールID
        
        Returns:
            通知を送信したらTrue、そうでなければFalse
        """
        # 重複通知チェック
        if self.notification_manager.is_already_notified(message_id):
            logger.info(f"Message {message_id} already notified within 24 hours")
            return False
        
        # メール詳細を取得
        message_details = self.gmail_monitor.get_message_details(message_id)
        if not message_details:
            return False
        
        subject = message_details.get('subject', '')
        body = message_details.get('body', '')
        from_addr = message_details.get('from', '')
        
        # キーワード検索
        keyword_in_subject = self.check_keywords(subject)
        keyword_in_body = self.check_keywords(body)
        
        if keyword_in_subject or keyword_in_body:
            matched_keyword = keyword_in_subject or keyword_in_body
            
            notification_title = f"🚨 養鶏場アラート: {matched_keyword}を検知"
            notification_message = f"件名: {subject}\n\n本文:\n{body[:500]}"
            
            if self.notifier.send_emergency_notification(
                title=notification_title,
                message=notification_message,
                email_from=from_addr
            ):
                self.notification_manager.record_notification(message_id)
                return True
        
        return False
    
    def run(self):
        """メインループを実行"""
        logger.info("=" * 60)
        logger.info("Poultry Farm Alert System started")
        logger.info(f"Check interval: {self.check_interval} seconds")
        logger.info("=" * 60)
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                logger.info(f"[{datetime.now()}] Checking for new emails...")
                
                # 未読メールを取得
                messages = self.gmail_monitor.get_unread_messages()
                
                if messages:
                    for message in messages:
                        message_id = message['id']
                        self.process_message(message_id)
                else:
                    logger.info("No unread messages found")
                
                # 古い通知履歴をクリーンアップ
                self.notification_manager.cleanup_old_records()
                
                consecutive_errors = 0
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error occurred: {e} (consecutive errors: {consecutive_errors})")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(
                        f"Too many consecutive errors ({consecutive_errors}). "
                        "System will retry after a longer interval."
                    )
                    time.sleep(300)  # 5分待機
                    consecutive_errors = 0
            
            # 指定された間隔で待機
            time.sleep(self.check_interval)


def main():
    """メイン関数"""
    try:
        system = PoultryFarmAlertSystem()
        system.run()
    except KeyboardInterrupt:
        logger.info("System stopped by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        raise


if __name__ == '__main__':
    main()
