Archibald
========

A bot for Yahoo! Fantasy football.

## Features
Currently, Archie is quite simple.  He checks your team for open slots and fills them.  He checks your roster for disabled players and swaps them out with benched players, or recruits free-agents to replace them based on a simple metric.  He drops players he doesn't like.  Don't expect him to win you the league just yet, but he'll do the bare minimum.

## Running Archie
You can run Archibald using the provided run.py.  You'll need to modify some constants to point it at your league / team, and you'll need to set up auth.csv to include you OAuth credentials.  More documentation to come on this later.

Once you do that, you can run:
```
python run.py
```

## Dependencies 
Uses a modified version of [YHandler](https://github.com/mleveck/YHandler) and thus relies on its dependencies.


