#!/bin/bash

cd /Users/yashsamtani2/penntennisscraper

/Users/yashsamtani2/anaconda3/bin/python reserve_courts.py >> /Users/yashsamtani2/penntennisscraper/cron.log 2>&1

echo "Run completed at $(date)" >> /Users/yashsamtani2/penntennisscraper/cron.log

