import tty
import termios
import select

import math
import time
import io
import sys

escape = "\x1b"
unset = escape + "[0m" # ]
cs = "[1;" # ]


class Man:
    def __init__(self, health=5, oxygen=5, x=18, y=24):
        self.head_init = y
        self.x = x
        self.y = y
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

    def head_y(self) -> int:
        return self.y

    def head_x(self) -> int:
        return self.x

    def respawn(self):
        self.health = 5
        self.oxygen = 7

    def dead(self) -> bool:
        return self.health <= 0

    def right(self):
        self.x += 1

    def left(self):
        self.x -= 1

    def jump(self):
        if not self.in_jump:
            self.in_jump = True

    def do_jump(self):
        if self.in_jump:
            self.jump_position += 1
        else:
            self.y = self.head_init
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
        self.y = self.head_init
        self.in_jump = False

    def check_oxygen(self, screen):
        if self.head_y() > len(screen):
            if self.under >= 30:
                self.under = 0;
                self.oxygen -= 1
                if self.oxygen < 0:
                    self.health -= 1
            else:
                self.under += 1
        else:
            self.oxygen = self.oxygen_init

    def draw(self, screen):
        self.do_jump()
        self.check_oxygen(screen)
        y = self.y
        if self.dead():
            y = len(screen) - 3
        #draw_dot(screen, x=self.x, y=y+1,    brush='👺')
        draw_dot(screen, x=self.x, y=y+1,    brush='ج')
        draw_dot(screen, x=self.x, y=y+2,    brush='|')
        draw_dot(screen, x=self.x+1, y=y+2,  brush='^')
        draw_dot(screen, x=self.x-1, y=y+2,  brush='^')
        if self.in_jump:
            draw_dot(screen, x=self.x+1, y=y+2,  brush='/')
            draw_dot(screen, x=self.x-1, y=y+2,  brush='\\')
        else:
            draw_dot(screen, x=self.x+2, y=y+2,  brush='\\')
            draw_dot(screen, x=self.x-2, y=y+2,  brush='/')
        if self.dead():
            return
        draw_dot(screen,     x=self.x, y=y+3,    brush='❂')
        if self.in_jump:
            draw_dot(screen, x=self.x, y=y+4,  brush='|')
            draw_dot(screen, x=self.x+1, y=y+4,  brush='\\')

            draw_dot(screen, x=self.x, y=y+5,  brush='/')
            draw_dot(screen, x=self.x+1, y=y+5,  brush='/')
        else:
            if self.step == 0:
                draw_dot(screen, x=self.x-1, y=y+4,  brush='/')
                draw_dot(screen, x=self.x-2, y=y+5,  brush='/')

                draw_dot(screen,     x=self.x+1, y=y+4,  brush='\\')
                draw_dot(screen, x=self.x+2, y=y+5,  brush='/')
                self.step = 1
            elif self.step == 1:
                self.step = 2;
                draw_dot(screen, x=self.x, y=y+4,  brush='|')
                draw_dot(screen, x=self.x, y=y+4,  brush='|')
                draw_dot(screen, x=self.x, y=y+5,  brush='/')
                draw_dot(screen, x=self.x, y=y+5,  brush='/')
            else:
                draw_dot(screen, x=self.x, y=y+4,  brush='|')
                draw_dot(screen, x=self.x+1, y=y+5,  brush='/')

                draw_dot(screen, x=self.x, y=y+4,  brush='|')
                draw_dot(screen, x=self.x-1, y=y+5,  brush='/')
                self.step = 0


def make_screen():
    screen = [[" " for _ in range(80)] for _ in range(30)]
    return screen

def print_screen(screen):
    ss = io.StringIO("")
    first_line = screen[0]
    num1 = []
    num2 = []
    for (idx, _) in enumerate(first_line):
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
    for (idx, line) in enumerate(screen):
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


def draw_rock(screen, x=57, y=28, brush='#'):
    draw_dot(screen, x,   y,   brush)
    draw_dot(screen, x+1, y,   brush)
    draw_dot(screen, x,   y+1, brush)
    draw_dot(screen, x,   y-1, brush)
    draw_dot(screen, x+1, y+1, brush)
    draw_dot(screen, x+1, y-1, brush)

def draw_dot(screen, x, y, brush, color=0):
    if y < 0 or y >= len(screen):
        return
    if x < 0 or x >= len(screen[y]):
        return
    if color > 0:
        screen[y][x] = f"{escape}{cs}{color}m{brush}{unset}"
    else:
        screen[y][x] = brush

def drow_vertical_line(screen, x, y, lenght, brush, color):
  for y in range(y, y+lenght):
      draw_dot(screen, x, y, brush, color)


def get_pressed_key(moment=0.1):
    """
    Detects which arrow key is pressed on the keyboard and returns the corresponding direction.
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
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
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return None

if __name__ == '__main__':
    rock = 0
    rock_position = 80

    rock_hit = False
    chr = None

    jump_duration = 10
    head_init = 24
    head=head_init
    jump=0

    moment = 0.1

    man = Man(health=5, oxygen=7, x=18, y=24)

    while True:
        screen = make_screen()
        man.draw(screen)
        draw_rock(screen, x=rock_position)
        drow_vertical_line(screen, x=2, y=1, lenght=man.health, brush='❤️', color=31)

        drow_vertical_line(screen, x=4, y=1, lenght=man.oxygen, brush='🗭', color=34)
        print_screen(screen)

        if chr in ['space', 'up', 'page-up']:
            man.jump()
        elif chr == 'right':
            man.right()
        elif chr == 'left':
            man.left()
        elif chr == 'exit':
            # print("Игра завершена")
            #sys.exit(0)
            pass
        elif chr == 'r':
            man.up()
        elif chr == 's':
            moment += 0.02
        elif chr == 'z':
            man.respawn()

        elif chr == 'S':
            moment = max(moment - 0.02, 0.05)


        if rock_position == man.head_x() + 10:
            rock_hit = True

        rock_distance = rock_position - man.head_x()
        if (-2 < rock_distance < 2) and len(screen) > man.head_y() > 22:
            # print("rock_hit")
            if rock_hit:
                man.health -= 1
                rock_hit = False

        rock_position -= 1
        if rock_position < 0:
            rock += 1
            rock_position = len(screen[0])

        chr = get_pressed_key(moment)

