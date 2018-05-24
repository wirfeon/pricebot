#!/bin/bash

git branch | grep -q "* master" \
    && git add -u && git commit -m "$1" && git push heroku master \
    || git branch | grep -q "* test" \
        && git add -u && git commit -m "$1" && git push heroku-test test:master
