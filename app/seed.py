"""Seed default bingo squares themed to the conference talk."""
from .db import execute_db, get_db, put_db

SQUARES = [
    "Copilot writes a bash script",
    "A systemctl command appears",
    "Someone mentions RHEL 9",
    "A live demo works first try",
    "Azure CLI is used",
    "An Ansible playbook shows up",
    "Copilot suggests a fix for an error",
    'The speaker says "agentic"',
    "A firewall rule is configured",
    "SELinux is mentioned",
    "A VM is provisioned on Azure",
    "dnf or yum install is run",
    "Copilot explains a log file",
    "Someone asks a question",
    "The speaker switches terminals",
    "A container is involved",
    "SSL/TLS certificates come up",
    "Copilot generates a config file",
    'The speaker says "shift left"',
    "A monitoring tool appears",
    "sudo is used",
    'The speaker says "inner loop"',
    "A GitHub Actions workflow appears",
    "Copilot writes a one-liner",
    "Kubernetes or OpenShift is mentioned",
    "A YAML file is edited",
    "Someone mentions subscription-manager",
    "A package gets installed",
    "Copilot autocompletes a command",
    "Azure Portal is shown",
    "A permission denied error happens",
    "grep or awk is used",
    "The speaker mentions security",
    "A JSON file is parsed",
    "Copilot suggests a different approach",
    "Someone says Red Hat Enterprise Linux",
    "A service is restarted",
    "SSH is used to connect somewhere",
    "Environment variables are set",
    "The speaker opens a browser",
    "A Python script appears",
    "Copilot fixes a typo",
    "Cloud-init is mentioned",
    "A disk or storage is configured",
    "The audience laughs",
    'The speaker says "let me show you"',
    "A git command is run",
    "Networking is configured",
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
