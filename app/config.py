import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'change-me-in-production')
    DATABASE_URL = os.environ.get(
        'DATABASE_URL',
        'postgresql://bingo:bingo@localhost:5432/conference_bingo',
    )
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'change-me')
