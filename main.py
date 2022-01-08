import arcade
import pathlib
from pyglet.gl import GL_NEAREST
from random import choice, randint
from enum import Enum
from sys import exit


DEBUG = False
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 150
WINDOW_TITLE = "Dino Game"
BACKGROUND_COLOR = (247, 247, 247)  # Grey background
ASSETS_PATH = pathlib.Path(__file__).resolve().parent / "assets"
GROUND_WIDTH = 600
LEVEL_WIDTH_PIXELS = GROUND_WIDTH * ((SCREEN_WIDTH * 4) // GROUND_WIDTH)
ALL_TEXTURES = [
    "dino-run-1",
    "dino-run-2",
    "dino-crash-1",
    "dino-duck-1",
    "dino-duck-2",
    "bird-1",
    "bird-2",
]
PLAYER_SPEED = 2.0
MAX_CLOUDS = 3
CLOUD_YPOS_MIN = 100
CLOUD_YPOS_MAX = 140
CLOUD_SPEED = -0.5

DinoStates = Enum("DinoStates", "IDLING RUNNING JUMPING DUCKING CRASHING")
GameStates = Enum("GameStates", "PLAYING GAMEOVER")


class DinoGame(arcade.Window):
    def __init__(self, width, height, title):
        super().__init__(width, height, title)

        self.dino_state = DinoStates.IDLING
        self.camera_sprites = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.camera_gui = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)

        self.set_mouse_visible(False)
        arcade.set_background_color(BACKGROUND_COLOR)

    def setup(self):
        self.elapsed_time = 0.0
        self.score = 0
        self.textures = {
            tex: arcade.load_texture(ASSETS_PATH / f"{tex}.png") for tex in ALL_TEXTURES
        }
        self.game_state = GameStates.PLAYING

        # Scene setup
        self.scene = arcade.Scene()

        # Clouds Setup
        self.clouds_list = arcade.SpriteList()
        for i in range(MAX_CLOUDS):
            cloud_sprite = arcade.Sprite(ASSETS_PATH / "cloud.png")
            cloud_sprite.left = randint(0, SCREEN_WIDTH)
            cloud_sprite.top = randint(CLOUD_YPOS_MIN, CLOUD_YPOS_MAX)
            self.clouds_list.append(cloud_sprite)

        # Horizon setup
        self.horizon_list = arcade.SpriteList()
        for col in range(LEVEL_WIDTH_PIXELS // GROUND_WIDTH):
            horizon_type = choice(["1", "2"])
            horizon_sprite = arcade.Sprite(ASSETS_PATH / f"horizon-{horizon_type}.png")
            horizon_sprite.hit_box = [[-300, -10], [300, -10], [300, -6], [-300, -6]]
            horizon_sprite.left = GROUND_WIDTH * col
            horizon_sprite.bottom = 23
            self.horizon_list.append(horizon_sprite)
        self.scene.add_sprite_list("horizon", False, self.horizon_list)

        # Player setup
        self.player_sprite = arcade.Sprite()
        self.player_sprite.center_x = 200
        self.player_sprite.center_y = 44
        self.player_sprite.texture = self.textures["dino-run-1"]
        self.player_list = arcade.SpriteList()
        self.player_list.append(self.player_sprite)
        self.scene.add_sprite("player", self.player_sprite)
        self.dino_state = DinoStates.RUNNING

        # Obstacles setup
        self.obstacles_list = arcade.SpriteList()
        self.bird_sprite = arcade.Sprite(ASSETS_PATH / "bird-1.png")
        self.bird_sprite.bottom = 100
        self.bird_sprite.right = LEVEL_WIDTH_PIXELS - 100
        self.obstacles_list.append(self.bird_sprite)
        self.add_obstacles(SCREEN_WIDTH * 0.8, LEVEL_WIDTH_PIXELS)
        self.scene.add_sprite_list("obstacles", True, self.obstacles_list)

        # Physics engine
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player_sprite, self.horizon_list, gravity_constant=0.4
        )

    def add_obstacles(self, xmin, xmax):
        xpos = xmin
        if self.bird_sprite.right < self.camera_sprites.goal_position[0]:
            is_bird_off_camera = True
        else:
            is_bird_off_camera = False

        while xpos < xmax:
            if randint(1, 5) == 1 and is_bird_off_camera:
                self.bird_sprite.bottom = randint(40, 80)
                self.bird_sprite.left = xpos
                xpos += self.bird_sprite.width + randint(200, 400)
            else:
                cactus_size = choice(["large", "small"])
                variant = choice(["1", "2", "3"])
                obstacle_sprite = arcade.Sprite(
                    ASSETS_PATH / f"cactus-{cactus_size}-{variant}.png"
                )
                obstacle_sprite.left = xpos
                obstacle_sprite.bottom = 20 if cactus_size == "large" else 24
                xpos += (
                    obstacle_sprite.width + randint(200, 400) + obstacle_sprite.width
                )
                self.obstacles_list.append(obstacle_sprite)

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.dino_state = DinoStates.JUMPING
            self.physics_engine.jump(6)
        elif key == arcade.key.DOWN:
            self.dino_state = DinoStates.DUCKING
            self.player_sprite.hit_box = self.textures["dino-duck-1"].hit_box_points
        elif key == arcade.key.ESCAPE:
            exit()

    def on_key_release(self, key, modifiers):
        if key == arcade.key.SPACE or key == arcade.key.DOWN:
            self.dino_state = DinoStates.RUNNING
            self.player_sprite.hit_box = self.textures["dino-run-1"].hit_box_points
            if self.player_sprite.center_y < 44:
                self.player_sprite.center_y = 44
        if self.game_state == GameStates.GAMEOVER:
            self.setup()

    def on_update(self, delta_time):
        if self.game_state == GameStates.GAMEOVER:
            self.player_sprite.change_x = 0
            self.player_sprite.texture = self.textures["dino-crash-1"]
            return
        self.elapsed_time += delta_time
        self.offset = int(self.elapsed_time * 10)
        dino_frame = 1 + self.offset % 2
        self.player_list.update()
        self.physics_engine.update()
        # Check for collisions
        collisions = self.player_sprite.collides_with_list(self.obstacles_list)
        if len(collisions) > 0 and not DEBUG:
            self.dino_state = DinoStates.CRASHING
            self.game_state = GameStates.GAMEOVER
        if self.dino_state == DinoStates.DUCKING:
            self.player_sprite.texture = self.textures[f"dino-duck-{dino_frame}"]
        else:
            self.player_sprite.texture = self.textures[f"dino-run-{dino_frame}"]
        self.player_sprite.change_x = PLAYER_SPEED
        self.camera_sprites.move((self.player_sprite.left - 30, 0))
        self.score = int(self.player_sprite.left) // 10
        # Bird animation
        bird_frame = 1 + (self.offset // 2) % 2
        self.bird_sprite.texture = self.textures[f"bird-{bird_frame}"]
        # Extend horizon if first horizon sprite goes off camera
        if self.horizon_list[0].right < self.camera_sprites.goal_position[0]:
            horizon_sprite = self.horizon_list.pop(0)
            horizon_sprite.left = self.horizon_list[-1].left + GROUND_WIDTH
            self.add_obstacles(self.horizon_list[-1].right, horizon_sprite.right)
            self.horizon_list.append(horizon_sprite)
        # Shift clouds for parallax effect and spawn new ones
        self.clouds_list.move(CLOUD_SPEED, 0)
        for c in self.clouds_list:
            if c.right < 0:
                c.right = SCREEN_WIDTH + randint(0, SCREEN_WIDTH * 0.25)
                c.top = randint(CLOUD_YPOS_MIN, CLOUD_YPOS_MAX)
                break

    def on_draw(self):
        arcade.start_render()
        # GUI camera for parallax effect of clouds
        self.camera_gui.use()
        self.clouds_list.draw(filter=GL_NEAREST)
        # Game camera
        self.camera_sprites.use()
        self.scene.draw(filter=GL_NEAREST)
        if DEBUG:
            self.player_list.draw_hit_boxes(arcade.color.BANGLADESH_GREEN)
            self.obstacles_list.draw_hit_boxes(arcade.color.BARN_RED)
            self.horizon_list.draw_hit_boxes(arcade.color.CATALINA_BLUE)
        # GUI camera
        self.camera_gui.use()
        arcade.draw_text(
            f"{self.score:05}",
            SCREEN_WIDTH - 2,
            SCREEN_HEIGHT - 10,
            arcade.color.BLACK,
            20,
            font_name="Kenney High",
            anchor_x="right",
            anchor_y="top",
        )
        if self.game_state == GameStates.GAMEOVER:
            arcade.draw_text(
                "G A M E   O V E R",
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT - 30,
                arcade.color.BLACK,
                24,
                font_name="Kenney High",
                anchor_x="center",
                anchor_y="top",
            )


def main():
    window = DinoGame(SCREEN_WIDTH, SCREEN_HEIGHT, WINDOW_TITLE)
    window.setup()
    arcade.run()


main()
