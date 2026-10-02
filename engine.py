"""Deterministic runner simulation. All times advance only while playing."""
from dataclasses import dataclass
import random

@dataclass
class Obstacle:
    lane: int
    kind: str
    z: float = 1.0
    checked: bool = False

class Runner:
    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        self.lane = 1
        self.time = self.distance = 0.0
        self.jump_left = 0.0
        self.duck = False
        self.obstacles = []
        self.spawn_in = 2.0
        self.alive = True
        self.coins = 0

    @property
    def speed(self):
        return min(.31, .15 + self.distance / 12000)

    def update(self, dt, command):
        if not self.alive:
            return
        dt = max(0, min(dt, .1))
        self.time += dt
        self.distance += dt*self.speed*200
        self.lane = max(0, min(2, self.lane + command.move))
        self.duck = command.duck
        self.jump_left = max(0, self.jump_left-dt)
        if command.jump and self.jump_left == 0 and not self.duck:
            self.jump_left = .95
        self.spawn_in -= dt
        if self.spawn_in <= 0:
            # One object per row leaves two escape lanes and avoids impossible rows.
            self.obstacles.append(Obstacle(self.rng.randrange(3),
                                  self.rng.choice(['barrier','beam','train','coin'])))
            self.spawn_in = max(1.45, 2.6-self.distance/1500)
        for obj in self.obstacles:
            obj.z -= self.speed*dt
            if obj.z <= .12 and not obj.checked:
                obj.checked = True
                if obj.lane == self.lane:
                    if obj.kind == 'coin':
                        self.coins += 1
                    elif obj.kind == 'train' or (obj.kind == 'barrier' and self.jump_left <= .15) or (obj.kind == 'beam' and not self.duck):
                        self.alive = False
        self.obstacles = [o for o in self.obstacles if o.z > -.12]

    @property
    def score(self):
        return int(self.distance) + self.coins*25
