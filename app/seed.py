"""Seed default bingo squares themed to the conference talk."""
from .db import execute_db, get_db, put_db

SQUARES = [
    "Copilot writes a bash script",
    "A systemctl command appears",
    "A live demo works first try",
    "Azure CLI is used",
    "An Ansible playbook shows up",
    "Copilot suggests a fix for an error",
    'The speaker says "agentic"',
    "A firewall rule is configured",
    "SELinux is mentioned",
    "dnf install is run",
    "Copilot explains a log file",
    "Someone asks a question",
    "The speaker switches desktops",
    "SSL/TLS certificates come up",
    "Copilot generates a config file",
    "A monitoring tool appears",
    "sudo is used",
    "Copilot writes a one-liner",
    "A YAML file is edited",
    "A package gets installed",
    "A permission denied error happens",
    "grep or awk is used",
    "The speaker mentions security",
    "Copilot suggests a different approach",
    "Someone says Red Hat Enterprise Linux",
    "A service is restarted",
    "SSH is used to connect somewhere",
    "Environment variables are set",
    "The speaker opens a browser",
    "A Python script appears",
    "Copilot fixes a typo",
    "The audience laughs",
    'The speaker says "let me show you"',
    "A git command is run",
    "Networking is configured",
    "Copilot SSHs into a server",
    "The speaker mentions Ansible",
    'The speaker says "codify"',
    "The speaker mentions SELinux denials",
    'The speaker says "blast radius"',
    'The speaker says "idempotent"',
    "Grafana dashboard is shown",
    "The speaker checks his phone",
    "CPU usage spikes on screen",
    'The speaker says "judgment"',
    "Copilot kills a runaway process",
    "The app goes live on your phone",
    "A runbook is mentioned",
]


def seed():
    conn = get_db()
    try:
        with conn.cursor() as cur:
            for text in SQUARES:
                cur.execute(
                    'INSERT INTO bingo_squares (text) VALUES (%s) '
                    'ON CONFLICT (text) DO NOTHING',
                    (text,),
                )
        conn.commit()
        print(f'Seeded {len(SQUARES)} bingo squares.')
    finally:
        put_db(conn)


if __name__ == '__main__':
    seed()
