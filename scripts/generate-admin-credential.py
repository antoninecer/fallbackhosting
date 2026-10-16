#!/usr/bin/env python3
"""Generate a lab/Coolify-compatible credential into a NEW private file only."""
import argparse
import json
import os
from pathlib import Path
import secrets
import string

GROUPS = (string.ascii_lowercase, string.ascii_uppercase, string.digits, '!_-')


def generate_password(length=16):
    if type(length) is not int or not 16 <= length <= 128:
        raise ValueError('Generated passwords require 16–128 characters.')
    alphabet = ''.join(GROUPS)
    while True:
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        if all(any(char in group for char in password) for group in GROUPS):
            return password


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--username', default='admin')
    parser.add_argument('--length', type=int, default=16)
    args = parser.parse_args()
    password = generate_password(args.length)
    parent = args.output.parent
    if not parent.is_dir() or parent.stat().st_mode & 0o077:
        parser.error('Output parent must already be a private directory (0700).')
    # Exclusive creation prevents accidental credential replacement; no stdout secret.
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'w') as stream:
        json.dump({'username': args.username, 'password': password}, stream, indent=2)
        stream.write('\n')
    print('Compatible credential saved privately; no account has been changed.')


if __name__ == '__main__':
    main()
