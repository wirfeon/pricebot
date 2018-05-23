#!/bin/bash


git branch | grep -q "* test" \
    && grep -q 'ENV = "test"' bot.py \
    || sed -i 's/ENV = .*/ENV = "test"/' bot.py

git branch | grep -q "* test" \
    && git add -u \
    && git commit -m "$1" \
    && git push heroku-test test:master
