import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://bingo:bingo@localhost:5432/conference_bingo',
    )
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', '')
    ADMIN_ENABLED = os.environ.get('ADMIN_ENABLED', 'false').lower() in ('true', '1', 'yes')
