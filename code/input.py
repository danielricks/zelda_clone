import pygame

def get_joystick():
    pygame.joystick.init()
    joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
    print(joysticks)
    if len(joysticks) == 0:
        print('No controller')
        return None
    else:
        joystick = joysticks[0]
        joystick.init()
        name = joystick.get_name()
        print('Using:', name)
    return joystick

def get_keyboard_input():
    pressed = pygame.key.get_pressed()
    up = pressed[pygame.K_UP]
    down = pressed[pygame.K_DOWN]
    left = pressed[pygame.K_LEFT]
    right = pressed[pygame.K_RIGHT]
    space = pressed[pygame.K_SPACE]
    left_cntrl = pressed[pygame.K_LCTRL]
    e = pressed[pygame.K_e]
    m = pressed[pygame.K_m]
    q = pressed[pygame.K_q]
    return up, down, left, right, space, left_cntrl, e, m, q

def get_xbox_controller_input(joystick):
    x_axis = joystick.get_axis(0)
    y_axis = joystick.get_axis(1)
    a = joystick.get_button(0)
    b = joystick.get_button(1)
    x = joystick.get_button(2)
    y = joystick.get_button(3)
    left_bumper = joystick.get_button(4)
    right_bumper = joystick.get_button(5)
    back = joystick.get_button(6) # select
    start = joystick.get_button(7)
    guide = joystick.get_button(8) # xbox
    left_axis_down = joystick.get_button(9)
    right_axis_down = joystick.get_button(10)
    left_trigger = joystick.get_axis(2)
    right_trigger = joystick.get_axis(5)
    return x_axis, y_axis, a, b, x, y, left_bumper, right_bumper, back, start, guide, left_axis_down, right_axis_down, left_trigger, right_trigger

def get_current_input(joystick):
    up, down, left, right, space, left_cntrl, e, m, q = get_keyboard_input()
    attack_1 = space
    attack_2 = left_cntrl
    switch_1 = q
    switch_2 = e
    menu = m
    if joystick != None:
        x_axis, y_axis, a, b, x, y, left_bumper, right_bumper, back, start, guide, left_axis_down, right_axis_down, left_trigger, right_trigger = get_xbox_controller_input(joystick)
        up = y_axis < -0.5
        down = y_axis > 0.5
        left = x_axis < -0.5
        right = x_axis > 0.5
        attack_1 = a
        attack_2 = b
        switch_1 = y
        switch_2 = x
        menu = start
        left_trigger_pushed = left_trigger > -1.0
        right_trigger_pushed = right_trigger > -1.0
    return up, down, left, right, attack_1, attack_2, switch_1, switch_2, menu
