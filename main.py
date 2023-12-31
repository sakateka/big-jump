import tty
import termios
import select
from textwrap import dedent
from random import random

import math
import time
import io
import sys

escape = "\x1b"
unset = escape + "[0m" # ]
cs = "[1;" # ]

class Object:
    def __init__(self, screen, x, y, frames, moving=True):
        if not screen:
            raise Exception("screen is required")
        self.screen = screen

        self.height = len(frames[0])
        self.width = len(frames[0][0])
        
        self.moving = moving
        self.frames = frames
        self.x_init = x
        self.y_init = y
        self.x = x
        self.y = y
        self.current_frame = 0

    @staticmethod
    def split_pattern(pattern, sep):
        frames = []
        for line in pattern.splitlines():
            if not line:
                continue
            frames_line = [l for l in line.split(sep) if l]
            if not frames:
                frames = [[line] for line in frames_line]
            else:
                for (idx, frame_line) in enumerate(frames_line):
                    frames[idx].append(frame_line)
        return frames

    def draw(self):
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        if self.moving:
            self.x -= 1

        frame_width = len(self.frames[0])
        if self.x < -frame_width:
            self.x = self.x_init + frame_width

        for y in range(self.screen.height):
            for x in range(self.screen.width):
                dot, color = self.dot(x=x, y=y)
                if not dot or dot == ' ':
                    continue
                self.screen.draw_dot(x=x, y=y, brush=dot, color=color)

    def dot(self, x, y):
        frame_width = len(self.frames[0])
        if self.y > y > self.y + frame_width:
            return (None, None)

        half_of_frame = frame_width//2;
        if -half_of_frame > x - self.x > half_of_frame:
            return (None, None)

        frame = self.frames[self.current_frame]
        fy = y - self.y
        fx = x - (self.x - half_of_frame)
        if 0 > fy or fy >= len(frame) or 0 > fx or fx >= len(frame[0]):
            return (None, None)

        color = self.color(x=fx, y=fy)
        return frame[fy][fx], color
    
    def hit(self, _):
        pass

    def color(self, x, y) -> int:
        return 0


class Lightning(Object):
    def __init__(self, screen, x, y):
        pattern = dedent(f"""
            :           /#/:
            :          /#/ :
            :         /#/  :
            :        /#/__ :
            :       /####/ :
            :         /#/  :
            :        /#/   :
            :        /#/   :
            :       /#/    :
            :      /#/__   :
            :     /####/   :
            :       /#/    :
            :      /#/     :
            :     /#/      :
            :    /#/       :
            :   /#/        :
            :🭦 🮆 🮆 🭛       :
            : 🭦 🮆 🭛        :
            :  🭦 🭛         :
        """) 

        frames = Object.split_pattern(pattern, ':')
        super().__init__(screen=screen, x=x, y=y, frames=frames)
        self.redraw = False
        self.light = False

    def color(self, x, y) -> int:
        return 33

    def draw(self):
        r = round(random(), 3)
        if not (0.7 >= r >= 0.6):
            if not self.redraw:
                self.light = False
                return
        else:
            self.redraw = True

        self.light = True
        super().draw()
        self.redraw = False

    def hit(self, other, draw=False):
        if not self.light:
            return False

        bottom = self.y + self.height
        if other.y > bottom:
            return False

        depth = bottom - other.y
        if draw:
            self.screen.draw_dot(x=self.x-6, y=bottom-1, brush='#', color=31)
            self.screen.draw_dot(x=self.x-5, y=bottom-1, brush='#', color=31)
            self.screen.draw_dot(x=self.x-7, y=bottom-2, brush='#', color=31)
            self.screen.draw_dot(x=self.x-6, y=bottom-2, brush='#', color=31)
            self.screen.draw_dot(x=self.x-5, y=bottom-2, brush='#', color=31)
            self.screen.draw_dot(x=self.x-4, y=bottom-2, brush='#', color=31)

            self.screen.draw_dot(x=self.x-8, y=bottom-3, brush='#', color=31)
            self.screen.draw_dot(x=self.x-7, y=bottom-3, brush='#', color=31)
            self.screen.draw_dot(x=self.x-6, y=bottom-3, brush='#', color=31)
            self.screen.draw_dot(x=self.x-5, y=bottom-3, brush='#', color=31)
            self.screen.draw_dot(x=self.x-4, y=bottom-3, brush='#', color=31)
            self.screen.draw_dot(x=self.x-3, y=bottom-3, brush='#', color=31)
        if depth == 1 and 5 <= self.x - other.x <= 6:
            return True
        if depth == 2 and 4 <= self.x - other.x <= 7:
            return True
        if depth >= 3 and 3 <= self.x - other.x <= 8:
            return True
        return False


class Cloud(Object):
    def __init__(self, screen, x, y):
        pattern = dedent("""
         |   ###   |   ###   |
         | ####### | ####### |
         |#########|#########|
         | ####### | ####### |
         |  🌢🌢🌢🌢🌢  | 🌢 🌢 🌢 🌢 |
         | 🌢 🌢 🌢 🌢 |  🌢🌢🌢🌢🌢  |
         |  🌢🌢🌢🌢🌢  | 🌢 🌢 🌢 🌢 |
        """)

        frames = Object.split_pattern(pattern, '|')
        super().__init__(screen=screen, x=x, y=y, frames=frames)

        self.lightning = Lightning(screen=screen, x=x, y=y+self.height)

    def color(self, x, y) -> int:
        if y >= 4:
            return 34
        return 0

    def draw(self):
        
        super().draw()
        self.lightning.x = self.x - 1
        self.lightning.draw()
        pass

    def hit(self, other, draw=False):
        if self.lightning.hit(other, draw):
            if not draw:
                other.health -= 1

class Rock(Object):
    def __init__(self, screen, x, y):
        pattern = dedent("""
         | ## |
         |####|
        """)

        frames = Object.split_pattern(pattern, '|')
        super().__init__(screen=screen, x=x, y=y, frames=frames)
        self.rock_hit = True

    def hit(self, other):
        if self.x == other.x + 10:
            self.rock_hit = True

        rock_distance = self.x - other.x
        if (-1 < rock_distance < 1) and self.screen.height > other.y > 23:
            if self.rock_hit:
                other.health -= 1
                self.rock_hit = False

class Man(Object):
    def __init__(self, screen, health=5, oxygen=5, water=10, x=18, y=24):
        pattern = dedent(r"""
            :  ج  :  ج  :  ج  :
            :/^|^\:/^|^\:/^|^\:
            :  ❂  :  ❂  :  ❂  :
            : / \ :  |  :  |  :
            :/   /: / / :  /  :
        """)

        jump_pattern = dedent(r"""
            :  ج  :
            : \|/ :
            :  ❂  :
            : _|\ :
            :   ` :
        """)

        sit_pattern = dedent(r"""
            :  ج  :
            : \|/ :
            :  ❂/|:
        """)

        self.run_frames = Object.split_pattern(pattern, ':')
        super().__init__(
            screen=screen,
            x=x,
            y=y,
            frames=self.run_frames,
            moving=False
        )

        self.jump_frames = Object.split_pattern(jump_pattern, ':')
        self.sit_frames = Object.split_pattern(sit_pattern, ':')

        self.screen = screen

        self.health = health
        self.oxygen_init = oxygen
        self.oxygen = oxygen
        self.under = 0

        self.jump_duration = 10
        self.jump_height = 5
        self.jump_down = 8
        self.jump_position = 0
        self.in_jump = False
        self.step = True

        self.in_sit_down = False
        
        self.water = water
        self.water_counter = 0

    def respawn(self):
        self.health = 5
        self.oxygen = 7
        self.water = 10

    def dead(self) -> bool:
        return self.health <= 0

    def right(self):
        self.x += 1

    def left(self):
        self.x -= 1

    def jump(self):
        if not self.in_jump:
            self.in_jump = True
            if self.in_sit_down:
                self.y -= 1
            self.in_sit_down = False

    def sit_down(self):
        self.in_sit_down = not self.in_sit_down

    def do_jump(self):
        if not self.in_jump:
            self.jump_position = 0
            return

        if self.jump_position == self.jump_duration:
            self.in_jump = False
        elif self.jump_position == self.jump_height:
            pass
        elif self.jump_position > self.jump_duration - self.jump_height:
            self.y += 1
        elif self.jump_position < self.jump_height:
            self.y -= 1

    def up(self):
        self.y = self.y_init
        self.in_jump = False

    def check_oxygen(self):
        if self.y > self.screen.height:
            if self.under >= 30:
                self.under = 0;
                self.oxygen -= 1
                if self.oxygen < 0:
                    self.health -= 1
            else:
                self.under += 1
        else:
            self.oxygen = self.oxygen_init

    def check_water(self):
        if self.water_counter == 20:
            self.water -= 1
            self.water_counter = 0
        self.water_counter += 1

    def draw(self):
        self.check_oxygen()
        self.check_water()

        if self.in_jump:
            self.jump_position += 1
            self.frames = self.jump_frames
        elif self.in_sit_down:
            self.y = self.y_init + 2
            self.frames = self.sit_frames
        else:
            self.y = self.y_init
            self.frames = self.run_frames

        self.do_jump()
        if self.dead():
            self.y = self.screen.height - 2
        super().draw()

class Screen():
    def __init__(self, height, width, moment):
        self.moment_init = moment
        self.moment = moment

        self.height = height
        self.width = width
        self.pixels = [[" " for _ in range(width)] for _ in range(height)]

    def clean(self):
        for line in self.pixels:
            for idx in range(self.width):
                line[idx] = " "

    def reset(self):
        self.moment = self.moment_init

    def slow_down(self):
        self.moment += 0.02

    def speed_up(self):
        self.moment = max(self.moment - 0.02, 0.02)

    def print(self):
        ss = io.StringIO("")
        num1 = []
        num2 = []
        for idx in range(self.width):
            tens = idx // 10
            if tens > 0:
                num1.append(tens)
            else:
                num1.append(' ')
            num2.append(idx % 10)
        ss.write(f"{escape}{cs}30m   ")
        ss.write("".join(str(i) for i in num1))
        ss.write(f"{unset}\n")
        ss.write(f"{escape}{cs}30m   ")
        ss.write("".join(str(i) for i in num2))
        ss.write(f"{unset}\n")

        ss.write(f"{escape}{cs}34m")
        ss.write("-" * 84)
        ss.write(f"{unset}")
        ss.write("\n")
        for (idx, line) in enumerate(self.pixels):
            ss.write(f'{escape}{cs}30m{idx: >2}|{unset}')
            for chr in line:
                ss.write(chr)
            ss.write(f"{escape}{cs}30m|{unset}\n")
        ss.write(f"{escape}{cs}32m")
        ss.write("-" * 84)
        ss.write(f"{unset}")
        ss.write("\n")
        ss.seek(0)
        print(ss.read())


    def draw_dot(self, x, y, brush, color=0):
        if y < 0 or y >= self.height:
            return
        if x < 0 or x >= self.width:
            return
        if color > 0:
            self.pixels[y][x] = f"{escape}{cs}{color}m{brush}{unset}"
        else:
            self.pixels[y][x] = brush

    def vertical_line(self, x, y, lenght, brush, color):
      for y in range(y, y+lenght):
          self.draw_dot(x, y, brush, color)

    def string(self, text, x, y):
        for idx, chr in enumerate(text):
            self.draw_dot(x=x + idx, y=y, brush=chr)

get_pressed_key_init = False
def get_pressed_key(moment=0.1):
    """
    Detects which arrow key is pressed on the keyboard and returns the corresponding direction.
    """
    fd = sys.stdin.fileno()
    if not get_pressed_key_init:
        tty.setcbreak(sys.stdin.fileno())  # Set the terminal to cbreak mode
    ch = None
    if sys.stdin in select.select([sys.stdin], [], [], moment)[0]:  # Adjust delay value here
        ch = sys.stdin.read(1)
        if ch == '\x1b':  # Escape key
            ch = sys.stdin.read(2)
            if ch == '[A':  # ]
                return "up"
            elif ch == '[B':  # ]
                return "down"
            elif ch == '[C':  # ]
                return "right"
            elif ch == '[D':  # ]
                return "left"
            elif ch == '[5':  # ]
                ch = sys.stdin.read(1)
                return "page-up"
            elif ch == '[6':  # ]
                ch = sys.stdin.read(1)
                return "page-down"
        elif ch == '\r' or ch == '\n':  # Enter key
            return "enter"
        elif ch == 'e':
            return "exit"
        elif ch == ' ':  # Space key
            return "space"
        else:
            return ch
    return None

if __name__ == '__main__':
    width=80
    height=30
    screen = Screen(width=width, height=height, moment=0.1)
    man = Man(health=5, oxygen=7, x=18, y=25, screen=screen)
    cloud = Cloud(y=1, x=73, screen=screen)
    rocks = [Rock(y=28, x=79, screen=screen), Rock(y=28, x=89, screen=screen)]

    chr = None
    while True:
        screen.clean()
        man.draw()
        cloud.draw()
        for rock in rocks:
            rock.draw()
        screen.vertical_line(x=2, y=1, lenght=man.health, brush='❤', color=31)

        screen.vertical_line(x=4, y=1, lenght=man.oxygen, brush='Ꝍ', color=34)
        screen.vertical_line(x=6, y=1, lenght=man.water, brush='🌢', color=34)
        # cloud.hit(man, draw=True)
        screen.string(f"ɱ : {screen.moment:.2f}", y=0, x=0)
        screen.print()

        if chr in ['space', 'up', 'page-up']:
            man.jump()
        elif chr == 'right':
            man.right()
        elif chr == 'left':
            man.left()
        elif chr == 'exit':
            print("Game over")
            sys.exit(0)
            pass
        elif chr == 'r':
            man.up()
        elif chr == 'c':
            man.sit_down()
        elif chr == 'z':
            man.respawn()
            screen.reset()

        elif chr == '+':
            screen.slow_down()
        elif chr == '-':
            screen.speed_up()


        cloud.hit(man)
        for rock in rocks:
            rock.hit(man)
        chr = get_pressed_key(screen.moment)

