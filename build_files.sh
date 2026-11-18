#!/bin/bash
echo "=== VERCEL BUILD START ==="
python3 -m pip install -r requirements.txt || python3.12 -m pip install -r requirements.txt || pip install -r requirements.txt
python3 manage.py collectstatic --noinput || python3.12 manage.py collectstatic --noinput || python manage.py collectstatic --noinput
echo "=== VERCEL BUILD END ==="
