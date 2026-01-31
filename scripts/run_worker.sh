#!/bin/bash
# Script to run Celery worker for Assura

celery -A app.celery_app worker --loglevel=info --concurrency=4
