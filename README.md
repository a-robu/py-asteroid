# Introduction

This is an asteroids game I made in 2012, around the time I started my first year in university.

![gameplay-screenshot](gameplay-screenshot.png)

The game is really just a prototype, but it does have the benefits of a smooth gameplay and physics based movement.

# Launching the Game

This game is written in Python 2 and requires `pygame`.

```bash
virtualenv venv
. venv/bin/activate
pip install pygame # (known to work with pygame==1.9.6)
python asteroids.py
```

Be aware that the game will launch directly into fullscreen mode.
