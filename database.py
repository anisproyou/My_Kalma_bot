import psycopg2
from psycopg2.extras import RealDictCursor
from config import Config

class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD
        )
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # جدول المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id BIGINT PRIMARY KEY,
            username VARCHAR(255),
            first_name VARCHAR(255),
            points INTEGER DEFAULT 0,
            total_earned INTEGER DEFAULT 0,
            referrer_id BIGINT,
            referral_count INTEGER DEFAULT 0,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_banned BOOLEAN DEFAULT FALSE,
            withdrawal_address VARCHAR(255)
        )
        ''')
        # جدول المهام المكتملة
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS completed_tasks (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            task_type VARCHAR(50),
            task_id VARCHAR(100),
            points_earned INTEGER,
            completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        # جدول عمليات السحب
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS withdrawals (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            amount_usdt DECIMAL(10,2),
            amount_points INTEGER,
            wallet_address VARCHAR(255),
            status VARCHAR(20) DEFAULT 'pending',
            requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP,
            tx_hash VARCHAR(255),
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
        ''')
        self.conn.commit()
        cursor.close()

    def get_or_create_user(self, user_id, username, first_name, referrer_id=None):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))
        user = cursor.fetchone()
        if not user:
            cursor.execute('''
            INSERT INTO users (user_id, username, first_name, referrer_id)
            VALUES (%s,%s,%s,%s)
            ''', (user_id, username, first_name, referrer_id))
            if referrer_id:
                cursor.execute('UPDATE users SET points=points+%s,total_earned=total_earned+%s WHERE user_id=%s',
                               (Config.REFERRAL_BONUS_LEVEL1, Config.REFERRAL_BONUS_LEVEL1, referrer_id))
            self.conn.commit()
            cursor.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))
            user = cursor.fetchone()
        cursor.close()
        return dict(user)

    def get_user(self, user_id):
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute('SELECT * FROM users WHERE user_id=%s', (user_id,))
        user = cursor.fetchone()
        cursor.close()
        return dict(user) if user else None

    def add_points(self, user_id, points, task_type=None, task_id=None):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET points=points+%s,total_earned=total_earned+%s,last_active=CURRENT_TIMESTAMP WHERE user_id=%s',
                       (points, points, user_id))
        if task_type:
            cursor.execute('INSERT INTO completed_tasks (user_id, task_type, task_id, points_earned) VALUES (%s,%s,%s,%s)',
                           (user_id, task_type, task_id, points))
        self.conn.commit()
        cursor.close()

    def create_withdrawal(self, user_id, amount_usdt, wallet_address):
        cursor = self.conn.cursor()
        amount_points = int(amount_usdt * Config.POINTS_TO_USDT_RATE)
        cursor.execute('UPDATE users SET points=points-%s WHERE user_id=%s AND points>=%s',
                       (amount_points, user_id, amount_points))
        if cursor.rowcount == 0:
            cursor.close()
            return None
        cursor.execute('INSERT INTO withdrawals (user_id, amount_usdt, amount_points, wallet_address) VALUES (%s,%s,%s,%s) RETURNING id',
                       (user_id, amount_usdt, amount_points, wallet_address))
        withdrawal_id = cursor.fetchone()[0]
        self.conn.commit()
        cursor.close()
        return withdrawal_id

    def close(self):
        self.conn.close()
