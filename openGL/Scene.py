from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from pyglet.gl import *

from functions import *
from game.Particles import Particles
from game.blocks.DestroyBlock import DestroyBlock
from game.entity.Inventory import Inventory
from game.entity.Zombie import Zombie
from game.world.worldGenerator import worldGenerator
from openGL.CubeHandler import CubeHandler


class Scene:
    def __init__(self):
        print("Init Scene class...")

        self.WIDTH, self.HEIGHT = WIDTH, HEIGHT
        self.allowEvents = {
            "movePlayer": True,
            "grabMouse": True,
            "keyboard": True,
            "showCrosshair": True,
        }

        self.worldSp = spiral(CHUNKS_RENDER_DISTANCE)
        self.chunkg = len(self.worldSp)
        self.drawCounter = 0
        self.in_water = False
        self.worldGen = worldGenerator(self, randint(434, 434343454))
        self.particles = Particles(self)
        self.destroy = DestroyBlock(self)
        self.gui = None
        self.sound = None
        self.blockSound = None
        self.player = None
        self.texture, self.block, self.texture_dir, self.inventory_textures = {}, {}, {}, {}
        self.fov = FOV
        self.updateEvents = []
        self.entity = []
        self.time = 200
        self.skyColor = [128, 179, 255]
        self.mskyColor = [128, 179, 255]
        self.nskyColor = [4, 6, 10]
        self.lightingColor = 200
        self.startPlayerPos = [0, -90, 0]
        self.panorama = {}

    def loadPanoramaTextures(self):
        print("Loading panorama textures...")
        for e, i in enumerate(os.listdir("gui/bg/")):
            self.panorama[e] = \
                pyglet.graphics.TextureGroup(pyglet.image.load("gui/bg/" + i).get_mipmapped_texture())
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

    def vertexList(self):
        x, y, w, h = self.WIDTH / 2, self.HEIGHT / 2, self.WIDTH, self.HEIGHT
        self.reticle = pyglet.graphics.vertex_list(4, ('v2f', (x - 10, y, x + 10, y, x, y - 10, x, y + 10)),
                                                   ('c3f', (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)))

    def initScene(self):
        print("Init OpenGL scene...")

        glClearColor(0.5, 0.7, 1, 1)
        glClearDepth(1.0)
        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LESS)
        glShadeModel(GL_SMOOTH)
        glMatrixMode(GL_PROJECTION)
        glDepthFunc(GL_LEQUAL)
        glAlphaFunc(GL_GEQUAL, 1)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_FOG)
        glHint(GL_FOG_HINT, GL_DONT_CARE)
        glFogi(GL_FOG_MODE, GL_LINEAR)
        glEnable(GL_TEXTURE_2D)

        glLoadIdentity()
        load_textures(self)
        self.loadPanoramaTextures()
        self.vertexList()

        self.transparent = pyglet.graphics.Batch()
        self.opaque = pyglet.graphics.Batch()
        self.stuffBatch = pyglet.graphics.Batch()
        self.player.inventory = Inventory(self)
        self.cubes = CubeHandler(self.opaque, self.block, self.opaque,
                                 ('leaves_taiga', 'leaves_oak', 'tall_grass', 'nocolor'), self)

        self.zombie = Zombie(self)
        self.zombie.position = [0, 53, 0]
        self.entity.append(self.zombie)

        self.set3d()

    def set2d(self):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluOrtho2D(0, self.WIDTH, 0, self.HEIGHT)

    def set3d(self):
        glLoadIdentity()
        gluPerspective(self.fov, (self.WIDTH / self.HEIGHT), 0.1, RENDER_DISTANCE)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def resizeCGL(self, w, h, changeRes=True):
        if changeRes:
            self.WIDTH = w
            self.HEIGHT = h
        self.vertexList()
        glViewport(0, 0, w, h)

    def drawPanorama(self):
        # self.resizeCGL(256, 256, changeRes=False)

        pp = self.player.position
        sx, sy, sz = 60, 60, 60

        x, y, z = pp[0] - (sx // 2), -(sy // 2), pp[2] - (sz // 2)
        X, Y, Z = x + sx, y + sy, z + sz

        vertexes = [
            (X, y, z, x, y, z, x, Y, z, X, Y, z),
            (x, y, Z, X, y, Z, X, Y, Z, x, Y, Z),
            (x, y, z, x, y, Z, x, Y, Z, x, Y, z),
            (X, y, Z, X, y, z, X, Y, z, X, Y, Z),
            (x, y, z, X, y, z, X, y, Z, x, y, Z),
            (x, Y, Z, X, Y, Z, X, Y, z, x, Y, z),
        ]

        tex_coords = ('t2f', (0, 0, 1, 0, 1, 1, 0, 1))
        mode = GL_QUADS
        self.stuffBatch.add(4, mode, self.panorama[2], ('v3f', vertexes[0]),
                            tex_coords)  # back
        self.stuffBatch.add(4, mode, self.panorama[0], ('v3f', vertexes[1]),
                            tex_coords)  # front

        self.stuffBatch.add(4, mode, self.panorama[3], ('v3f', vertexes[2]),
                            tex_coords)  # left
        self.stuffBatch.add(4, mode, self.panorama[1], ('v3f', vertexes[3]),
                            tex_coords)  # right

        self.stuffBatch.add(4, mode, self.panorama[5], ('v3f', vertexes[4]),
                            tex_coords)  # bottom

        self.stuffBatch.add(4, mode, self.panorama[4], ('v3f', vertexes[5]),
                            tex_coords)  # top

        # glCopyTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, 0, 0, 256, 256)
        # self.resizeCGL(self.WIDTH, self.HEIGHT, changeRes=False)

    def genWorld(self):
        self.drawCounter += 1
        if self.drawCounter > 1 and self.chunkg > 0:
            self.drawCounter = 0
            x, y = self.worldSp[self.chunkg]
            self.chunkg -= 1
            self.worldGen.genChunk(CHUNKS_RENDER_DISTANCE // 2 - x, CHUNKS_RENDER_DISTANCE // 2 - y, self.player)

    def updateScene(self):
        # self.time += 1 * clock.get_fps() / 1000
        # print(self.time)
        if 200 < self.time < 320:
            self.lightingColor = 200 - self.time + 200
        if 500 < self.time < 620:
            self.lightingColor = 700 - self.time

        self.genWorld()
        if self.in_water:
            glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0, 0, 0, 1))
            glFogf(GL_FOG_START, 10)
            glFogf(GL_FOG_END, 35)
        else:
            glFogfv(GL_FOG_COLOR, (GLfloat * 4)(0.5, 0.7, 1, 1))
            glFogf(GL_FOG_START, 60)
            glFogf(GL_FOG_END, 120)

        self.set3d()
        glClearColor(self.skyColor[0] / 255, self.skyColor[1] / 255, self.skyColor[2] / 255, 1)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        glColor3d(self.lightingColor / 255, self.lightingColor / 255, self.lightingColor / 255)

        self.player.update()
        self.draw()

        for i in self.entity:
            i.update()

        self.particles.drawParticles()

        blockByVec = self.cubes.hitTest(self.player.position, self.player.get_sight_vector())
        if blockByVec[0]:
            self.destroy.drawDestroy(*blockByVec[0])

            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glColor3d(0, 0, 0)
            pyglet.graphics.draw(24, GL_QUADS, ('v3f/static', flatten(cube_vertices(blockByVec[0], 0.51))))
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            glColor3d(1, 1, 1)

        glColor3d(1, 1, 1)
        glPopMatrix()
        self.set2d()

        for i in self.updateEvents:
            i()

    def draw(self):
        glEnable(GL_ALPHA_TEST)
        self.opaque.draw()
        glDisable(GL_ALPHA_TEST)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)
        self.transparent.draw()
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)
        self.transparent.draw()

        self.stuffBatch.draw()
        self.stuffBatch = pyglet.graphics.Batch()
