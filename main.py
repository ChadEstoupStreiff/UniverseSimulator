# System
from math import sqrt
import threading
import sys
import numpy as np
import time

# OpenGL
import pygame as pg
from pygame.locals import *

from OpenGL.GL import *
from OpenGL.GLU import *

##############
# Paramètres #
##############

fps = 70  # Number of targeted images
ticks = 40  # Number of ticks

weightScale = 1000  # The univers is X times bigger than weights initialisation variables
distanceScale = 1000  # The univers is X times bigger than distance initialisation variables

G = 6.67408 * pow(10, -11)  # Universe constant

nHistory = 500  # Number of movement history points
showTrace = False  # Show history trace (can be change inside simulation with key 'w')
pause = True  # Put movements in pause mode (can be change inside simulation with 'x' key)


############
# Graphics #
############

class OpenGLVisuals:
    def __init__(self, universe):
        print("Initialisation des graphics")
        self.universe = universe
        pg.init()
        self.display = (1680, 1050)
        pg.display.set_mode(self.display, DOUBLEBUF | OPENGL)

        self.camLocations = [-100000000, -100000000, 40000000]
        self.camAngles = [np.pi / 6, -np.pi / 10]
        self.lastTick = 0

        print("Lancement de la boucle de graphisme")
        self.loop()

    def loop(self):
        global pause, showTrace
        while True:
            for event in pg.event.get():
                if event.type == pg.QUIT:
                    pg.quit()
                    sys.exit()
                if event.type == pg.KEYDOWN:
                    if event.key == pg.K_w:
                        showTrace = not showTrace
                    if event.key == pg.K_x:
                        pause = not pause
                if event.type == pg.MOUSEMOTION:
                    # apply the look up and down
                    self.camAngles[0] -= (event.pos[0] - self.display[0] / 2) / 5000
                    self.camAngles[1] -= (event.pos[1] - self.display[1] / 2) / 5000

                    pg.mouse.set_pos([self.display[0] / 2, self.display[1] / 2])

            # get keys
            keypress = pg.key.get_pressed()

            viewVector = [np.cos(self.camAngles[0]) * np.cos(self.camAngles[1]),
                          np.sin(self.camAngles[0]) * np.cos(self.camAngles[1]),
                          np.sin(self.camAngles[1])]

            a = 20000000 * (time.time() - self.lastTick)
            self.lastTick = time.time()

            if keypress[pg.K_s]:
                self.camLocations[0] += -viewVector[0] * a
                self.camLocations[1] += -viewVector[1] * a
                self.camLocations[2] += -viewVector[2] * a
            if keypress[pg.K_z]:
                self.camLocations[0] += viewVector[0] * a
                self.camLocations[1] += viewVector[1] * a
                self.camLocations[2] += viewVector[2] * a
            if keypress[pg.K_q]:
                self.camLocations[0] += -viewVector[1] * a
                self.camLocations[1] += viewVector[0] * a
            if keypress[pg.K_d]:
                self.camLocations[0] += viewVector[1] * a
                self.camLocations[1] += -viewVector[0] * a
            if keypress[pg.K_SPACE]:
                self.camLocations[2] += a
            if keypress[pg.K_LCTRL]:
                self.camLocations[2] -= a

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

            # Et on place la caméra
            glMatrixMode(GL_MODELVIEW)
            glLoadIdentity()
            gluLookAt(
                self.camLocations[0], self.camLocations[1], self.camLocations[2],  # Coordonnées de la caméra
                self.camLocations[0] + viewVector[0],
                self.camLocations[1] + viewVector[1],
                self.camLocations[2] + viewVector[2],
                0, 0, 1  # Transformations
            )
            glMatrixMode(GL_PROJECTION)
            glLoadIdentity()
            gluPerspective(45, (self.display[0] / self.display[1]), 0.1, 10000000000.0)

            # On dessine
            if showTrace:
                glBegin(GL_LINES)

                glColor3f(255, 0, 0)
                glVertex3f(0.0, 0.0, 0.0)
                glVertex3f(200000000.0, 0.0, 0.0)

                glColor3f(0, 255, 0)
                glVertex3f(0.0, 0.0, 0.0)
                glVertex3f(0.0, 200000000.0, 0.0)

                glColor3f(0, 0, 255)
                glVertex3f(0.0, 0.0, 0.0)
                glVertex3f(0.0, 0.0, 200000000.0)
                glEnd()

            for corps in self.universe.corpsList:
                self.draw(corps)

            pg.display.flip()
            pg.time.wait(int(1 / fps))

    def draw(self, corps):
        coo = np.copy(corps.coordinates)

        glColor3f(corps.color[0], corps.color[1], corps.color[2])

        nLines = 20
        nColomn = 20
        for i in range(0, 360, nLines):  # 20 segments
            for j in range(0, 360, nColomn):  # 20 segments
                glBegin(GL_LINES)
                glVertex3f(
                    coo[0] + np.cos(2 * np.pi * i / 360) * np.cos(2 * np.pi * j / 360) * corps.size * 100000,
                    coo[1] + np.sin(2 * np.pi * i / 360) * np.cos(2 * np.pi * j / 360) * corps.size * 100000,
                    coo[2] + np.sin(2 * np.pi * j / 360) * corps.size * 100000
                )
                glVertex3f(
                    coo[0] + np.cos(2 * np.pi * i / 360 + 2 * np.pi * nLines / 360) * np.cos(
                        2 * np.pi * j / 360 + 2 * np.pi * nColomn / 360) * corps.size * 100000,
                    coo[1] + np.sin(2 * np.pi * i / 360 + 2 * np.pi * nLines / 360) * np.cos(
                        2 * np.pi * j / 360 + 2 * np.pi * nColomn / 360) * corps.size * 100000,
                    coo[2] + np.sin(2 * np.pi * j / 360 + 2 * np.pi * nColomn / 360) * corps.size * 100000
                )
                glEnd()

        if showTrace:
            for i in range(0, len(corps.history) - 1):
                glBegin(GL_LINES)
                glVertex3f(corps.history[i + 1][0], corps.history[i + 1][1], corps.history[i + 1][2])
                glVertex3f(corps.history[i][0], corps.history[i][1], corps.history[i][2])
                glEnd()


###########
# Classes #
###########

# Un corps celeste
class Corps:

    def __init__(self, color=np.array([0, 0, 0]), size=20, weight=10,
                 coordinates=np.array([.0, .0, .0], dtype=np.float64),
                 velocity=np.array([.0, .0, .0], dtype=np.float64)):
        self.color = color
        self.size = size
        self.weight = weight / weightScale
        self.coordinates = np.copy(coordinates) / distanceScale
        self.history = []
        self.velocity = np.copy(velocity)

    def move(self):
        self.history.append(np.copy(self.coordinates))
        if len(self.history) > nHistory:
            self.history.remove(self.history[0])

        self.coordinates = self.coordinates + self.velocity

    def distanceAndDirection(self, corps):
        dis = self.distance(corps)
        dir = np.array([
            corps.coordinates[0] - self.coordinates[0],
            corps.coordinates[1] - self.coordinates[1],
            corps.coordinates[2] - self.coordinates[2]]) / dis
        return dis, dir

    def applyAcceleration(self, a):
        self.velocity = self.velocity + a

    def distance(self, corps):
        return sqrt(
            pow(sqrt(
                pow(self.coordinates[0] - corps.coordinates[0], 2) +
                pow(self.coordinates[1] - corps.coordinates[1], 2)), 2) +
            pow(self.coordinates[2] - corps.coordinates[2], 2))


# Un univer contenant plusieurs corps
class Universe(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)

        print("Initialisation de l'univers")
        self.corpsList = []

    def appendCorps(self, c):
        self.corpsList.append(c)

    def run(self):
        while 1:
            dt = 1 / ticks
            if not pause:
                # On boucle tous les astres
                for i in range(len(self.corpsList) - 1):
                    corps = self.corpsList[i]

                    # Sur cet astre, on applique les formules avec les astres suivants
                    for j in range(i + 1, len(self.corpsList)):
                        corpsBis = self.corpsList[j]
                        if corps != corpsBis:
                            dis, dir = corps.distanceAndDirection(corpsBis)
                            a = G * corpsBis.weight / pow(dis, 2) / dt * dir
                            aBis = -G * corps.weight / pow(dis, 2) / dt * dir

                            corps.applyAcceleration(a)
                            corpsBis.applyAcceleration(aBis)

                # On fait bouger tous les astres
                for corps in self.corpsList:
                    corps.move()

            time.sleep(dt)

    def launch(self):
        self.start()
        OpenGLVisuals(self)


###########
# PRESETS #
###########
def star(universe):
    universe.appendCorps(Corps(np.array([0, 255, 0]), 10, 5.972 * pow(10, 30),
                               np.array([-2 * pow(10, 10), -2 * pow(10, 10), 0]),
                               np.array([4 * pow(10, 5), -4 * pow(10, 5), 0])))
    universe.appendCorps(Corps(np.array([0, 0, 255]), 10, 5.972 * pow(10, 30),
                               np.array([2 * pow(10, 10), 2 * pow(10, 10), 0]),
                               np.array([-4 * pow(10, 5), 4 * pow(10, 5), 0])))
    universe.appendCorps(Corps(np.array([255, 0, 0]), 10, 5.972 * pow(10, 30),
                               np.array([-2 * pow(10, 10), 2 * pow(10, 10), 0]),
                               np.array([-4 * pow(10, 5), -4 * pow(10, 5), 0])))
    universe.appendCorps(Corps(np.array([255, 255, 255]), 10, 5.972 * pow(10, 30),
                               np.array([2 * pow(10, 10), -2 * pow(10, 10), 0]),
                               np.array([4 * pow(10, 5), 4 * pow(10, 5), 0])))


def solar(universe):
    universe.appendCorps(Corps(np.array([0, 0, 255]), 10, 5.972 * pow(10, 24),
                               np.array([1.49 * pow(10, 11), 0, 0]),
                               np.array([0, -6e+04, -1e+05])))
    universe.appendCorps(Corps(np.array([0, 255, 255]), 10, 5.972 * pow(10, 24),
                               np.array([0.8 * pow(10, 11), 0, 0]),
                               np.array([0, -5e+04, -1e+05])))
    universe.appendCorps(Corps(np.array([0, 255, 0]), 10, 5.972 * pow(10, 24),
                               np.array([1.49 * pow(10, 10), 0, 0]),
                               np.array([0, -6e+04, -7e+05])))
    universe.appendCorps(Corps(np.array([255, 0, 0]), 10, 5.972 * pow(10, 24),
                               np.array([9 * pow(10, 9), 0, 0]),
                               np.array([-8e+03, -6e+04, -8e+05])))
    universe.appendCorps(Corps(np.array([255, 255, 0]), 10, 5.972 * pow(10, 24),
                               np.array([5 * pow(10, 9), 0, 0]),
                               np.array([0, -6e+04, -8e+05])))
    universe.appendCorps(Corps(np.array([255, 255, 255]), 20, 1.989 * pow(10, 30),
                               np.array([0, 0, 0]),
                               np.array([0, -6e+04, 0])))


def heart(universe):
    universe.appendCorps(Corps(np.array([255, 0, 0]), 10, 5.972 * pow(10, 24),
                               np.array([100000000, 0, 1.49 * pow(10, 10)]),
                               np.array([3e+05, 0, 5e+05])))
    universe.appendCorps(Corps(np.array([255, 0, 0]), 10, 5.972 * pow(10, 24),
                               np.array([-100000000, 0, 1.49 * pow(10, 10)]),
                               np.array([-3e+05, 0, 5e+05])))
    universe.appendCorps(Corps(np.array([255, 255, 255]), 20, 1.989 * pow(10, 30),
                               np.array([0, 0, 0]),
                               np.array([0, 0, 0])))


########
# MAIN #
########

if __name__ == "__main__":
    u = Universe()
    solar(u)
    u.launch()
