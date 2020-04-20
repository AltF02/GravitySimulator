import random
import traceback
from math import *

import pygame
from pygame.locals import *
import logging
logging.basicConfig(filename='ErrorLog.log', level=logging.DEBUG)

pygame.display.init()
pygame.font.init()

num_particles = int(input("How many particles so you want to simulate?: "))
collisions = True
edge_clamp = True
radius_scale = 2.0
max_initial_speed = 100.0
# The gravitational constant in this universe in pixels^3 kg^-1 s^-2.  The real one is 6.67384*(10^-11) m^3 kg^-1 s^-2
G = 50000.0
movement_substeps = 1
target_fps = 60.0
dt = 1.0 / target_fps

if num_particles == -1:
    while True:
        try:
            num_particles = int(input("Number of particles: "))
            break
        except:
            print("Could not parse number.")

num_particles_orig = num_particles

screen_size = [800, 600]
icon = pygame.Surface((1, 1))
icon.set_alpha(0)
pygame.display.set_icon(icon)
pygame.display.set_caption("Gravity Simulation")
surface = pygame.display.set_mode(screen_size)


def rndint(num): return int(round(num))


class Particle(object):
    def __init__(self, pos=None, vel=None, mass=None):
        if pos is None:
            self.pos = [random.uniform(10.0, screen_size[0] - 10.0), random.uniform(10.0, screen_size[1] - 10.0)]
        else:
            self.pos = pos
        if vel is None:
            angle = random.uniform(0.0, 2.0 * pi)
            r = random.uniform(0.0, max_initial_speed)
            self.vel = [r * cos(angle), r * sin(angle)]
        else:
            self.vel = vel
        if mass is None:
            self.mass = 1.0
        else:
            self.mass = mass
        self.forces = [0.0, 0.0]

    def get_radius(self):
        return radius_scale * (self.mass ** (1.0 / 3.0))

    @staticmethod
    def add_forces(particle1, particle2):
        try:
            dx = particle2.pos[0] - particle1.pos[0]
            dy = particle2.pos[1] - particle1.pos[1]
            r_squared = dx * dx + dy * dy
            r = r_squared ** 0.5
            force_magnitude = (G * particle1.mass * particle2.mass) / r_squared  # F=G*M1*M2/(r^2)
            dx_normalized_scaled = (dx / r) * force_magnitude
            dy_normalized_scaled = (dy / r) * force_magnitude
            particle1.forces[0] += dx_normalized_scaled
            particle1.forces[1] += dy_normalized_scaled
            particle2.forces[0] -= dx_normalized_scaled
            particle2.forces[1] -= dy_normalized_scaled
        except ZeroDivisionError:
            logging.warning(' ZeroDivisionError')

    @staticmethod
    def get_collided(part1, part2):
        r1 = part1.get_radius()
        r2 = part2.get_radius()
        both = r1 + r2
        abs_dx = abs(part2.pos[0] - part1.pos[0])
        if abs_dx > both:
            return False
        abs_dy = abs(part2.pos[1] - part1.pos[1])
        if abs_dy > both:
            return False
        if abs_dx * abs_dx + abs_dy * abs_dy > both * both:
            return False
        return True

    def move(self, dt):
        self.pos[0] += dt * self.vel[0]
        self.pos[1] += dt * self.vel[1]
        a_x = dt * self.forces[0] / self.mass  # F=MA -> A=F/M
        a_y = dt * self.forces[1] / self.mass
        while abs(a_x) > 1000.0:
            a_x /= 10.0
        while abs(a_y) > 1000.0:
            a_y /= 10.0
        self.vel[0] += a_x
        self.vel[1] += a_y
        self.forces[0] = 0.0
        self.forces[1] = 0.0

    def draw(self, surf):
        pygame.draw.circle(
            surf,
            (255, 255, 255),
            (rndint(self.pos[0]), rndint(screen_size[1] - self.pos[1])),
            rndint(self.get_radius()),
            0
        )


def setup_particles():
    global particles
    global num_particles
    num_particles = num_particles_orig
    particles = [Particle() for i in range(num_particles)]


def get_input():
    for event in pygame.event.get():
        if event.type == QUIT:
            return False
        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                return False
            elif event.key == K_r:
                setup_particles()  # reset
    return True


def move():
    for i in range(movement_substeps):
        for j in range(0, num_particles, 1):
            for k in range(j + 1, num_particles, 1):
                Particle.add_forces(particles[j], particles[k])
        for p in particles:
            p.move(dt / float(movement_substeps))


def collision_detect():
    global particles
    global num_particles
    new_particles = []
    dead_particles = []
    for i in range(0, num_particles, 1):
        for j in range(i + 1, num_particles, 1):
            p1 = particles[i]
            p2 = particles[j]
            if Particle.get_collided(p1, p2):
                # Remove colliding particles
                dead_particles.append(p1)
                dead_particles.append(p2)
                # Replace with a single particle with their properties
                mv_x = p1.mass * p1.vel[0] + p2.mass * p2.vel[0]
                mv_y = p1.mass * p1.vel[1] + p2.mass * p2.vel[1]
                mass = p1.mass + p2.mass
                new_particles.append(Particle(
                    [(p1.pos[0] * p1.mass + p2.pos[0] * p2.mass) / mass,
                     (p1.pos[1] * p1.mass + p2.pos[1] * p2.mass) / mass],  # center of mass
                    [mv_x / mass, mv_y / mass],  # momentum is conserved but not kinetic energy
                    mass
                ))
    if len(dead_particles) != 0:
        temp = []
        for p in particles:
            if p in dead_particles:
                continue
            temp.append(p)
        particles = temp
    particles += new_particles
    num_particles = len(particles)


def clamp_to_edges():
    for p in particles:
        r = p.get_radius()
        if p.pos[0] <= r:
            p.vel[0] = abs(p.vel[0])
        if p.pos[1] <= r:
            p.vel[1] = abs(p.vel[1])
        if p.pos[0] >= screen_size[0] - r:
            p.vel[0] = -abs(p.vel[0])
        if p.pos[1] >= screen_size[1] - r:
            p.vel[1] = -abs(p.vel[1])


def draw():
    surface.fill((0, 0, 0))

    for p in particles:
        p.draw(surface)

    pygame.display.flip()


def main():
    setup_particles()
    clock = pygame.time.Clock()
    while True:
        if not get_input():
            break
        move()
        if collisions:
            collision_detect()
        if edge_clamp:
            clamp_to_edges()
        draw()
        clock.tick(target_fps)
    pygame.quit()


if __name__ == "__main__":
    try:
        main()
    except:
        traceback.print_exc()
        pygame.quit()
        input()
