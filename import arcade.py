import cProfile
from pstats import Stats, SortKey
from tkinter.tix import MAIN
import arcade
import math
import sys
import random
import numpy as np


enemytimer = 200
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
BULLET_TIMER = 0
BULLET_SPEED = 15
PLAYER_MOV_SPEED = 2
ENEMY_SPAWN_RATE = 10
ENEMY_SPEED_MULT = 1.2
RIGHT_FACING = 0
LEFT_FACING = 1
CHARACTER_SCALING = 1.5
isProfiling = False
GUNSHOT_SOUND = arcade.load_sound('Gunshot.wav',False)
MAIN_THEME = arcade.load_sound('AimbotMaintheme.wav')
GAME_OVER = arcade.load_sound('gameover.wav')

class Entity(arcade.Sprite):
    def __init__(self, name_file, szise):
        super().__init__()

        self.scale = szise

        

        main_path = name_file

        self.texture = arcade.load_texture(main_path)

        # Hit box will be set based on the first image used. If you want to specify
        # a different hit box, you can do it like the code below.
        self.set_hit_box([[-10, -10], [10, -10], [-10, 10], [10, 10]])

def load_texture_pair_old(filename):
    """
    Load a texture pair, with the second being a mirror image.
    """
    return [
        arcade.load_texture(filename),
        arcade.load_texture(filename, flipped_horizontally=True)
    ]

class Enemy(Entity):
    def __init__(self, name_file, szise):

        # Setup parent class
        super().__init__(name_file, szise)


# TODO: Figure out if this is smart to have the bullet be an entity. It might be less costly to have it be just a sprite.
class Bullet(Entity):
    def __init__(self, name_file, szise):
        
        # Parent class
        super().__init__(name_file, szise)



class Loot(Entity):
    def __init__(self, name_file, szise):
        super().__init__(name_file, szise)

class Rupee(Loot):
    def __init__(self):
        super().__init__("rupee.png", 0.7)

class NormalBullet(Bullet):
    def __init__(self):
        super().__init__("bulletnormal1.png", 2)
        self.textures = [arcade.load_texture('bulletnormal1.png')]
        for i in range(2,5,1):
            self.textures.append(arcade.load_texture(f'bulletnormal{i}.png'))
        self.textureticker = 0
        self.nexttexticker = 0
        
        
    def update_animation(self, delta_time):
        if self.nexttexticker == 10:
            self.texture = self.textures[self.textureticker]
            self.nexttexticker = 0
            if self.textureticker == 3:
                self.textureticker = 0
            else:
                self.textureticker += 1
        self.nexttexticker +=1

class SlimeEnemy(Enemy):
    def __init__(self):
        # Set up parent class
        super().__init__("slimemonsteridle1.png", 1)
        self.enemy_face_direction = RIGHT_FACING
        self.scaling = 1.7
        self.iscolliding = False
        main_path = "slimemonsteridle1.png"
        # Load textures for idle standing
        self.textures = load_texture_pair_old(main_path)
        self.texture = self.textures[0]
        # Set the initial texture

    def update_animation(self, delta_time: float = 1/60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.enemy_face_direction == RIGHT_FACING:
            self.enemy_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.enemy_face_direction == LEFT_FACING:
            self.enemy_face_direction = RIGHT_FACING

        self.texture = self.textures[self.enemy_face_direction]

class Arm(Entity):
    def __init__(self, name_file, szise):

        super().__init__(name_file, szise)

class UziArmLeft(Arm):
    def __init__(self):
        super().__init__("pogmanuziarm2.png", 1.7)

class UziArmRight(Arm):
    def __init__(self):
        super().__init__("pogmanuziarm.png", 1.7)

class GameOverView(arcade.View):
    def on_show(self):
        
        arcade.play_sound(GAME_OVER, 0.2,looping= False)

    def on_draw(self):
        self.clear()
        arcade.draw_rectangle_filled(center_x=SCREEN_WIDTH/2,center_y=SCREEN_HEIGHT/2, width=10000, height=10000,color= arcade.color.DARK_RED)
        arcade.draw_text('GAME OVER',start_x= SCREEN_WIDTH/6,start_y= SCREEN_HEIGHT/2, font_name='FONT_HERSHEY_SCRIPT_COMPLEX',font_size= 100)
        


class PlayerCharacter(arcade.Sprite):
    """Player Sprite"""

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = LEFT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        main_path = "Aimbotjim.png"

        # Load textures for idle standing
        self.textures = load_texture_pair_old(main_path)
        self.texture = self.textures[0]
        # Set the initial texture

    def update_animation(self, delta_time: float = 1 / 60):

        # Figure out if we need to flip face left or right
        if self.change_x < 0 and self.character_face_direction != LEFT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction != RIGHT_FACING:
            self.character_face_direction = RIGHT_FACING

        self.texture = self.textures[self.character_face_direction]


class GameView(arcade.View):
    """ Main application class. """

    def __init__(self):
        super().__init__()

        self.camera = None

        self.enemytimer = ENEMY_SPAWN_RATE
        self.enemycollisioncheckticker = 0
        self.bullettimer = BULLET_TIMER
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.space_pressed = False
        self.background = None
        self.aimbotcrazy = False
        self.aimbotcounterleft = 0
        self.aimbotcounterright = 0
        self.habbedingcounter = 0
        arcade.set_background_color(arcade.color.AIR_FORCE_BLUE)


        self.scene = None

 


    def setup(self):
        # Set up your game here
        self.background = arcade.load_texture('Concretebackground.jpg')
        self.gui_camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.enemy_list = arcade.SpriteList()
        self.player_list = arcade.SpriteList()
        
        self.right_arm_list = arcade.SpriteList()
        self.left_arm_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.scene = arcade.Scene()
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = SCREEN_WIDTH/2
        self.player_sprite.center_y = SCREEN_HEIGHT/2
        arm = UziArmLeft()
        self.scene.add_sprite(self.left_arm_list, arm)
        arm = UziArmRight()
        self.scene.add_sprite(self.right_arm_list, arm)
        self.scene.add_sprite(self.player_list, self.player_sprite)
        self.score = 0
        
        self.coinsAlive = 0
        self.bullet_list = arcade.SpriteList()
        self.physics_engine = arcade.PhysicsEngineSimple(self.player_sprite, self.enemy_list)
        self.main_track = arcade.Sound.play(MAIN_THEME, 0.2, True)
        
        pass


    def on_draw(self):
        """ Render the screen. """
        self.clear()
        arcade.start_render()
        arcade.draw_lrwh_rectangle_textured(0, 0, 4000, 4000, self.background)
        self.camera.use()
        self.scene.draw()
        self.left_arm_list.draw()
        self.right_arm_list.draw()
        self.player_list.draw()
        self.enemy_list.draw()
        self.bullet_list.draw()
        self.coin_list.draw()
        score_text = f"GEMZ: {self.score}"
        self.gui_camera.use()
        arcade.draw_text(
            score_text,
            10,
            10,
            arcade.csscolor.DARK_BLUE,
            18,
        )
        

    def on_update(self, delta_time):
        """ All the logic to move, and the game logic goes here. """
        self.physics_engine.update()
        self.camera = arcade.Camera(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.scene.update(self.bullet_list)
        #self.scene.update(self.arm_list)
        # We draw a long line of height^2 + length^2 and then project this line around the player to randomly spawn an enemy, and not getting like a gaussian dist
        # around our borders.
        if (self.enemytimer == ENEMY_SPAWN_RATE): 
            enemy = SlimeEnemy()
            p = random.randint(0, SCREEN_WIDTH*2 + SCREEN_HEIGHT*2)
            if p < (SCREEN_WIDTH + SCREEN_HEIGHT):
                if p < SCREEN_WIDTH:
                    enemy.center_x = p + self.player_sprite.center_x - SCREEN_WIDTH/2
                    enemy.center_y = 0 + self.player_sprite.center_y - SCREEN_HEIGHT/2
                else:
                    enemy.center_x = SCREEN_WIDTH + self.player_sprite.center_x - SCREEN_WIDTH/2
                    enemy.center_y = p - SCREEN_WIDTH + self.player_sprite.center_y - SCREEN_HEIGHT/2
            else:
                p = p - (SCREEN_WIDTH + SCREEN_HEIGHT)
                if p < SCREEN_WIDTH:
                    enemy.center_x = SCREEN_WIDTH - p + self.player_sprite.center_x - SCREEN_WIDTH/2
                    enemy.center_y = SCREEN_HEIGHT + self.player_sprite.center_y - SCREEN_HEIGHT/2
                else:
                    enemy.center_x = 0 + self.player_sprite.center_x - SCREEN_WIDTH/2
                    enemy.center_y = SCREEN_HEIGHT - (p - SCREEN_WIDTH) + self.player_sprite.center_y - SCREEN_HEIGHT/2
            self.scene.add_sprite(self.enemy_list,enemy)
            self.enemytimer = 0
        
        if len(self.scene[self.enemy_list]) > 0:
            if not self.aimbotcrazy:
                lengthguyright = []
                lengthguyleft = []
                closestenemyright = None
                closestenemyleft = None
                for enemy in self.scene[self.enemy_list]:
                    if enemy.center_x > self.player_sprite.center_x:
                        vectorx =  enemy.center_x - self.player_sprite.center_x
                        vectory =  enemy.center_y - self.player_sprite.center_y
                        lengthab = vectorx * vectorx + vectory * vectory
                        lengthguyright.append([lengthab, enemy])
                        lengthguyright.sort(key=lambda x: x[0])
                        closestenemyright = lengthguyright[0]
                    else:
                        vectorx =  enemy.center_x - self.player_sprite.center_x
                        vectory =  enemy.center_y - self.player_sprite.center_y
                        lengthab = vectorx * vectorx + vectory * vectory
                        lengthguyleft.append([lengthab, enemy])
                        lengthguyleft.sort(key=lambda x: x[0])
                        closestenemyleft = lengthguyleft[0]
                
                if closestenemyleft != None:
                    for arm in self.scene[self.left_arm_list]:
                        vectorx = arm.center_x - closestenemyleft[1].center_x
                        vectory = arm.center_y - closestenemyleft[1].center_y
                        
                        inrads = math.atan2(vectorx, vectory)
                        if inrads < 0:
                            inrads = abs(inrads)
                        else:
                            inrads = 2*math.pi-inrads
                        
                        arm.radians = inrads

                if closestenemyright != None:
                    for arm in self.scene[self.right_arm_list]:
                        vectorx = arm.center_x - closestenemyright[1].center_x
                        vectory = arm.center_y - closestenemyright[1].center_y

                        inrads = math.atan2(vectorx, vectory)
                        if inrads < 0:
                            inrads = abs(inrads)
                        else:
                            inrads = 2*math.pi-inrads
                        
                        arm.radians = inrads
                

        # We shoot out bullets at the closest enemy, we don't work with any square roots, as we dont care about the actual distance.
        # So calculation shouldn't be so bad.
        if (self.bullettimer == BULLET_TIMER):
            
            # Checking if theres any enemies alive
            if len(self.scene[self.enemy_list]) > 0:
                
                # If space is not pressed we will shoot continuously at the nearest enemy
                if not self.aimbotcrazy:
                    lengthguyright = []
                    lengthguyleft = []
                    closestenemyright = None
                    closestenemyleft = None
                    for enemy in self.scene[self.enemy_list]:
                        if enemy.center_x > self.player_sprite.center_x:
                            vectorx =  enemy.center_x - self.player_sprite.center_x
                            vectory =  enemy.center_y - self.player_sprite.center_y
                            lengthab = vectorx * vectorx + vectory * vectory
                            lengthguyright.append([lengthab, enemy])
                            lengthguyright.sort(key=lambda x: x[0])
                            closestenemyright = lengthguyright[0]
                        else:
                            vectorx =  enemy.center_x - self.player_sprite.center_x
                            vectory =  enemy.center_y - self.player_sprite.center_y
                            lengthab = vectorx * vectorx + vectory * vectory
                            lengthguyleft.append([lengthab, enemy])
                            lengthguyleft.sort(key=lambda x: x[0])
                            closestenemyleft = lengthguyleft[0]
                        
                    if closestenemyleft != None:
                        for arm in self.scene[self.left_arm_list]:
                            vectorx = arm.center_x - closestenemyleft[1].center_x
                            vectory = arm.center_y - closestenemyleft[1].center_y
                            
                            inrads = math.atan2(vectorx, vectory)
                            if inrads < 0:
                                inrads = abs(inrads)
                            else:
                                inrads = 2*math.pi-inrads
                            
                            arm.radians = inrads
                        self.shoot_bullet_from_arm(self.left_arm_list, closestenemyleft, NormalBullet())
                        self.bullettimer = 0
                    else:
                        self.bullettimer = 0
                        
                    if closestenemyright != None:
                        for arm in self.scene[self.right_arm_list]:
                            vectorx = arm.center_x - closestenemyright[1].center_x
                            vectory = arm.center_y - closestenemyright[1].center_y

                            inrads = math.atan2(vectorx, vectory)
                            if inrads < 0:
                                inrads = abs(inrads)
                            else:
                                inrads = 2*math.pi-inrads
                            
                            arm.radians = inrads
                        self.shoot_bullet_from_arm(self.right_arm_list, closestenemyright, NormalBullet())
                        self.bullettimer = 0
                    else:
                        self.bullettimer = 0
                
                # If space is pressed, the aimbot goes crazy, which can be an advantage sometimes..
                if self.aimbotcrazy:
                    lengthguyright = []
                    lengthguyleft = []
                    closestenemyright = None
                    closestenemyleft = None
                    for enemy in self.scene[self.enemy_list]:
                            if enemy.center_x > self.player_sprite.center_x:
                                vectorx =  enemy.center_x - self.player_sprite.center_x
                                vectory =  enemy.center_y - self.player_sprite.center_y
                                lengthab = vectorx * vectorx + vectory * vectory
                                lengthguyright.append([lengthab, enemy])
                                
                            else:
                                vectorx =  enemy.center_x - self.player_sprite.center_x
                                vectory =  enemy.center_y - self.player_sprite.center_y
                                lengthab = vectorx * vectorx + vectory * vectory
                                lengthguyleft.append([lengthab, enemy])
                                

                    if self.aimbotcounterleft < len(lengthguyleft) and self.aimbotcounterright < len(lengthguyright):
                        
                        closestenemyright = lengthguyright[self.aimbotcounterright]
                        closestenemyleft = lengthguyleft[self.aimbotcounterleft]

                        if closestenemyleft != None:
                            for arm in self.scene[self.left_arm_list]:
                                vectorx = arm.center_x - closestenemyleft[1].center_x
                                vectory = arm.center_y - closestenemyleft[1].center_y
                                
                                inrads = math.atan2(vectorx, vectory)
                                if inrads < 0:
                                    inrads = abs(inrads)
                                else:
                                    inrads = 2*math.pi-inrads
                            
                                arm.radians = inrads
                            self.shoot_bullet_from_arm(self.left_arm_list, closestenemyleft, NormalBullet())
                            self.bullettimer = 0
                            self.aimbotcounterleft += 1
                        else:
                            self.bullettimer = 0
                            # If theres no enemy on the left we reset our target
                            self.aimbotcounterleft = 0
                            
                        if closestenemyright != None:
                            for arm in self.scene[self.right_arm_list]:
                                vectorx = arm.center_x - closestenemyright[1].center_x
                                vectory = arm.center_y - closestenemyright[1].center_y

                                inrads = math.atan2(vectorx, vectory)
                                if inrads < 0:
                                    inrads = abs(inrads)
                                else:
                                    inrads = 2*math.pi-inrads
                                
                                arm.radians = inrads
                            self.shoot_bullet_from_arm(self.right_arm_list, closestenemyright, NormalBullet())
                            self.aimbotcounterright += 1
                            self.bullettimer = 0
                        else:
                            self.bullettimer = 0
                            #If theres no enemy on the right we also reset our target
                            self.aimbotcounterright = 0                        

                        self.bullettimer = 0
                        
                        

                    else:
                        # Assuming we get here we wanna just reset both of our targets on the left and right arm.
                        self.bullettimer = 0
                        self.aimbotcounterleft = 0
                        self.aimbotcounterright = 0        
            


        
        self.scene.update(self.enemy_list)

        # Checking if player collides with enemies
        enemy_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[self.enemy_list]
        )
        
        # If an enemy hits score_text = f"Score: {self.score}"
        #TODO: Make it a bit cooler
        if len(enemy_hit_list) > 0:
            arcade.Sound.stop(MAIN_THEME, self.main_track)
            game_over_view = GameOverView()
            self.window.show_view(game_over_view)
        
        for arm in self.scene[self.left_arm_list]:
            arm.center_x = self.player_sprite.center_x-10
            arm.center_y = self.player_sprite.center_y

        for arm in self.scene[self.right_arm_list]:
            arm.center_x = self.player_sprite.center_x+10
            arm.center_y = self.player_sprite.center_y
        
        # Removing bullets if they hit an enemy, and handling what the enemy should do if a bullet hits them.
        if len(self.scene[self.bullet_list])>0:
            for bullet in self.scene[self.bullet_list]:
                hit_list = arcade.check_for_collision_with_list(bullet, self.scene[self.enemy_list])
                if hit_list:
                    bullet.remove_from_sprite_lists()
                    for enemy in hit_list:
                        loot = Rupee()
                        loot.center_x = enemy.center_x
                        loot.center_y = enemy.center_y
                        self.scene.add_sprite(self.coin_list,loot)
                        enemy.remove_from_sprite_lists()
                        self.coinsAlive += 1
            
        
        # Enemies go towards the players location at a constant speed.
        
        self.move_enemies(self.enemy_list)
            
        # Remove bulletsprites if outside of cameraview
        
        if len(self.scene[self.bullet_list])>0:
            SCREEN_RADIUSW = SCREEN_WIDTH/2
            SCREEN_RADIUSH = SCREEN_HEIGHT/2
            for bullet in self.scene[self.bullet_list]:
                if bullet.center_x > self.player_sprite.center_x + (SCREEN_RADIUSW):
                    bullet.remove_from_sprite_lists()
                elif bullet.center_x < self.player_sprite.center_x - (SCREEN_RADIUSW):
                    bullet.remove_from_sprite_lists()
                elif bullet.center_y > self.player_sprite.center_y + (SCREEN_RADIUSH):
                    bullet.remove_from_sprite_lists()
                elif bullet.center_y < self.player_sprite.center_y - (SCREEN_RADIUSH):
                    bullet.remove_from_sprite_lists()
                
        #print(len(self.scene[self.bullet_list]))
        if self.coinsAlive > 0:
            for loot in self.scene[self.coin_list]:
                vectorx = self.player_sprite.center_x - loot.center_x
                vectory = self.player_sprite.center_y - loot.center_y
                vectorxprime = np.abs(vectorx)
                vectoryprime = np.abs(vectory)

                ratio = 1 / max(vectorxprime, vectoryprime)
                ratio = ratio * (1.29289 - (vectorxprime + vectoryprime) * ratio * 0.29289)

                unitvectorx = vectorx * ratio
                unitvectory = vectory * ratio
                loot.change_x = unitvectorx * 5
                loot.change_y = unitvectory * 5

            coin_hit_list = arcade.check_for_collision_with_list(
            self.player_sprite, self.scene[self.coin_list]
            )

            # Loop through each coin we hit (if any) and remove it
            for coin in coin_hit_list:
                points = 10
                self.score += points
                # Remove the coin
                coin.remove_from_sprite_lists()
                self.coinsAlive -= 1

        
            
        self.center_camera_to_player()
        
        # Incrementing values TODO: Make this happen with a level-up system
        self.enemytimer += 1
        self.enemycollisioncheckticker += 1
        self.bullettimer += 1
        self.scene.update_animation(delta_time, self.player_list)
        pass

    def center_camera_to_player(self):
        screen_center_x = self.player_sprite.center_x - (self.camera.viewport_width / 2)
        screen_center_y = self.player_sprite.center_y - (self.camera.viewport_height / 2)

        player_centered = screen_center_x, screen_center_y

        self.camera.move_to(player_centered)

    def shoot_bullet_from_arm(self, armlist, closestenemy, bullettype):
        #TODO: This list will always contain one value, so maybe add more arms? or make the armlist a single object and delete forloop? :O
        for arm in self.scene[armlist]:
            bullet = bullettype
            
            vectorx = arm.center_x - closestenemy[1].center_x
            vectory = arm.center_y - closestenemy[1].center_y
            
            vectorxprime = np.abs(vectorx)
            vectoryprime = np.abs(vectory)

            ratio = 1 / max(vectorxprime, vectoryprime)
            ratio = ratio * (1.29289 - (vectorxprime + vectoryprime) * ratio * 0.29289)

            unitvectorx = vectorx * ratio
            unitvectory = vectory * ratio

            bullet.center_x = arm.center_x - unitvectorx*35
            bullet.center_y = arm.center_y - unitvectory*35
            
            bullet.change_x = -(unitvectorx * BULLET_SPEED)
            bullet.change_y = -(unitvectory * BULLET_SPEED)
            inrads = math.atan2(vectorx, vectory)
            if inrads < 0:
                inrads = abs(inrads)
            else:
                inrads = 2*math.pi-inrads
            
            bullet.radians = inrads
            self.bullettimer = 0
            arcade.play_sound(GUNSHOT_SOUND, random.randint(50,100)/300)
            self.scene.add_sprite(self.bullet_list, bullet)

    def process_keychange(self):
        # The reason for if and if, and not if and elseif, is because we want to evaluate multiple key inputs at the same time.
        if self.right_pressed:
            self.player_sprite.change_x = PLAYER_MOV_SPEED
        if self.left_pressed:
            self.player_sprite.change_x = -PLAYER_MOV_SPEED
        if self.up_pressed:
            self.player_sprite.change_y = PLAYER_MOV_SPEED
        if self.down_pressed:
            self.player_sprite.change_y = -PLAYER_MOV_SPEED
        if not self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = 0
        if not self.down_pressed and not self.up_pressed:
            self.player_sprite.change_y = 0
        if self.space_pressed:
            self.aimbotcrazy = True
        if not self.space_pressed:
            self.aimbotcrazy = False

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""
        # Handling both arrowkeys and WASD
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        elif key == arcade.key.SPACE:
            self.space_pressed = True
        
        self.process_keychange()

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        # I wonder what happens if u press both W & the up-arrow
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False
        elif key == arcade.key.SPACE:
            self.space_pressed = False
        self.process_keychange()

    def move_enemies(self, listofenemies):
        for enemy in self.scene[listofenemies]:
            enemyinpoint = False
            
            vectorx = self.player_sprite.center_x - enemy.center_x
            vectory = self.player_sprite.center_y - enemy.center_y
            
            vectorxprime = np.abs(vectorx)
            vectoryprime = np.abs(vectory)

            ratio = 1 / max(vectorxprime, vectoryprime)
            ratio = ratio * (1.29289 - (vectorxprime + vectoryprime) * ratio * 0.29289)

            unitvectorx = vectorx * ratio
            unitvectory = vectory * ratio

                # We already project a point from enemy1, we use this and check if it is inside of another
                # hitbox, before we apply the velocity.
                
            
            enemy.change_x = unitvectorx*ENEMY_SPEED_MULT
            enemy.change_y = unitvectory*ENEMY_SPEED_MULT
            

def main():
    if isProfiling == True:
        with cProfile.Profile() as pr:
            game = MyGame(SCREEN_WIDTH, SCREEN_HEIGHT)
            game.setup()
            arcade.run()
        with open('profiling_stats.txt', 'w') as stream:
            stats = Stats(pr, stream=stream)
            stats.strip_dirs()
            stats.sort_stats('time')
            stats.dump_stats('.prof_stats')
            stats.print_stats()
    else:
        window = arcade.Window(SCREEN_WIDTH, SCREEN_HEIGHT, "Pogman")
        startview = GameView()
        window.show_view(startview)
        startview.setup()
        arcade.run()




if __name__ == "__main__":
    main()