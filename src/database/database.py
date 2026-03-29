import sqlite3
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
import os

# Database path
DB_DIR = Path(__file__).parent.parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "ping_bot.db"


class PingBotDB:
    """SQLite database manager for Ping Bot"""
    
    def __init__(self, db_path: str = str(DB_PATH)):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Initialize database tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Articles table - stores all articles found
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                publish_date TEXT,
                source TEXT,
                content_snippet TEXT,
                is_controversial INTEGER DEFAULT 0,
                article_hash TEXT UNIQUE NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Sent emails table - tracks notifications sent
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_emails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id INTEGER NOT NULL,
                recipient_email TEXT NOT NULL,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                email_status TEXT DEFAULT 'sent',
                email_hash TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # Runs log - tracks execution history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                articles_found INTEGER DEFAULT 0,
                articles_sent INTEGER DEFAULT 0,
                duplicates_skipped INTEGER DEFAULT 0,
                status TEXT,
                error_message TEXT
            )
        """)
        
        # Create indexes for faster queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_hash ON articles(article_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_article_url ON articles(url)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sent_emails_article ON sent_emails(article_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_run_logs_timestamp ON run_logs(run_timestamp)")
        
        conn.commit()
        conn.close()
        print(f"[Database] Initialized at {self.db_path}")
    
    def get_article_hash(self, url: str, title: str) -> str:
        """Generate unique hash for article based on URL and title"""
        combined = f"{url}_{title}".lower()
        return hashlib.md5(combined.encode()).hexdigest()
    
    def article_exists(self, url: str, title: str) -> bool:
        """Check if article already exists in database"""
        article_hash = self.get_article_hash(url, title)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM articles WHERE article_hash = ?", (article_hash,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def has_been_sent(self, url: str, title: str, recipient_email: str) -> bool:
        """Check if this article URL has already been sent to this recipient - URL-based check only"""
        # Normalize URL for case-insensitive comparison
        normalized_url = url.strip().rstrip('/').lower()
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if URL exists in sent_emails table
        cursor.execute("""
            SELECT se.id FROM sent_emails se
            JOIN articles a ON se.article_id = a.id
            WHERE LOWER(TRIM(a.url, '/')) = ? AND se.recipient_email = ?
        """, (normalized_url, recipient_email))
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def add_article(self, url: str, title: str, publish_date: Optional[str],
                   source: str, content_snippet: str, is_controversial: bool = False) -> Optional[int]:
        """Add article to database, returns article_id if added, None if duplicate"""
        
        if self.article_exists(url, title):
            print(f"[Database] Article already exists: {title[:50]}...")
            return None
        
        article_hash = self.get_article_hash(url, title)
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO articles (url, title, publish_date, source, content_snippet, is_controversial, article_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (url, title, publish_date, source, content_snippet, int(is_controversial), article_hash))
            
            article_id = cursor.lastrowid
            conn.commit()
            print(f"[Database] Added article: {title[:50]}...")
            return article_id
            
        except sqlite3.IntegrityError as e:
            print(f"[Database] Integrity error adding article: {str(e)}")
            return None
        finally:
            conn.close()
    
    def mark_email_sent(self, article_id: int, recipient_email: str, status: str = "sent") -> bool:
        """Mark article as sent to recipient"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO sent_emails (article_id, recipient_email, email_status)
                VALUES (?, ?, ?)
            """, (article_id, recipient_email, status))
            
            conn.commit()
            print(f"[Database] Marked email sent for article_id={article_id}")
            return True
        except Exception as e:
            print(f"[Database] Error marking email sent: {str(e)}")
            return False
        finally:
            conn.close()
    
    def get_unsent_articles(self, recipient_email: str, hours: int = 201) -> List[Dict]:
        """Get articles from last N hours that haven't been sent to recipient"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT a.* FROM articles a
            WHERE a.discovered_at > ?
            AND a.id NOT IN (
                SELECT article_id FROM sent_emails 
                WHERE recipient_email = ?
            )
            ORDER BY a.publish_date DESC
        """, (cutoff_time, recipient_email))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def get_recent_articles(self, hours: int = 201, limit: int = 10) -> List[Dict]:
        """Get recent articles (for display/summary)"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT * FROM articles
            WHERE discovered_at > ?
            ORDER BY publish_date DESC
            LIMIT ?
        """, (cutoff_time, limit))
        
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return results
    
    def log_run(self, articles_found: int = 0, articles_sent: int = 0, 
                duplicates_skipped: int = 0, status: str = "success", 
                error_message: Optional[str] = None):
        """Log a bot execution run"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO run_logs (articles_found, articles_sent, duplicates_skipped, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        """, (articles_found, articles_sent, duplicates_skipped, status, error_message))
        
        conn.commit()
        conn.close()
        print(f"[Database] Run logged: {articles_found} found, {articles_sent} sent, {duplicates_skipped} duplicates")
    
    def get_run_stats(self, hours: int = 201) -> Dict:
        """Get execution statistics for the last N hours"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total_runs,
                SUM(articles_found) as total_found,
                SUM(articles_sent) as total_sent,
                SUM(duplicates_skipped) as total_duplicates,
                SUM(CASE WHEN status='success' THEN 1 ELSE 0 END) as successful_runs
            FROM run_logs
            WHERE run_timestamp > ?
        """, (cutoff_time,))
        
        result = dict(cursor.fetchone())
        conn.close()
        
        return result
    
    def cleanup_old_data(self, days: int = 30):
        """Remove articles and run logs older than N days"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Delete old sent_emails records (orphaned)
        cursor.execute("DELETE FROM sent_emails WHERE sent_at < ?", (cutoff_time,))
        
        # Delete old articles
        cursor.execute("""
            DELETE FROM articles 
            WHERE discovered_at < ? 
            AND id NOT IN (SELECT article_id FROM sent_emails)
        """, (cutoff_time,))
        
        # Delete old run logs
        cursor.execute("DELETE FROM run_logs WHERE run_timestamp < ?", (cutoff_time,))
        
        deleted_count = cursor.total_changes
        conn.commit()
        conn.close()
        
        print(f"[Database] Cleaned up old data, deleted {deleted_count} records")
        return deleted_count


# Global database instance
db = PingBotDB()
