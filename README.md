# AI Racing Simulator

A small project where cars, controlled by neural networks, learn to drive around a track using a genetic algorithm. Built with **Python** and **Pygame**.

---

## How it works

* You draw a track with the mouse.
* A population of cars tries to drive around it.
* Each car is controlled by a simple neural network with distance sensors.
* At the end of each generation, the best cars are kept and used to create the next generation.
* Over time, cars learn to follow the track better.

---

## Requirements

* Python 3.9+
* Pygame

Install with:

```bash
pip install pygame
```

---

## Run

```bash
python app.py
```

Draw a track with the left mouse button, then release to start the simulation.

---

## Controls

* **Left mouse**: Draw track
* **Close window**: Quit

---

## Files

* `app.py` – main program
* `car.py` – car logic and sensors
* `track.py` – track drawing
* `environment.py` – population and evolution
* `neural.py` – neural network
