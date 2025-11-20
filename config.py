import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    BOT_USERNAME = os.getenv('BOT_USERNAME', 'your_bot')

    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 5432))
    DB_NAME = os.getenv('DB_NAME', 'crypto_bot_db')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'your_password')

    POINTS_PER_AD_VIEW = int(os.getenv('POINTS_PER_AD_VIEW', 5))
    POINTS_PER_CHANNEL_JOIN = int(os.getenv('POINTS_PER_CHANNEL_JOIN', 15))
    POINTS_PER_REFERRAL = int(os.getenv('POINTS_PER_REFERRAL', 50))
    POINTS_TO_USDT_RATE = int(os.getenv('POINTS_TO_USDT_RATE', 1000))
    MIN_WITHDRAWAL = int(os.getenv('MIN_WITHDRAWAL', 10))

    REFERRAL_BONUS_LEVEL1 = int(os.getenv('REFERRAL_BONUS_LEVEL1', 50))
    REFERRAL_BONUS_LEVEL2 = int(os.getenv('REFERRAL_BONUS_LEVEL2', 20))

    PAYMENT_API_KEY = os.getenv('PAYMENT_API_KEY', '')
    USDT_WALLET = os.getenv('USDT_WALLET', '')

    ADMIN_IDS = [7860963170]  # ضع هنا معرفك أو معرفات المدراء
