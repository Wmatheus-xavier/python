#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
👁️❤️  OLHO APAIXONADO
---------------------------------------------------------------
Um olho cheio de amor que te acompanha com o olhar (mova o mouse).
A cada ciclo, a câmera mergulha dentro do globo ocular, atravessa a
pupila... e lá no fundo existe um coração pulsando.

Requisitos:  pip install pygame
Executar  :  python olho_apaixonado.py

Controles :  MOUSE   -> o olho acompanha o cursor
             ESPAÇO  -> reinicia a animação (volta ao início do ciclo)
             ESC     -> sair
"""
import math
import random
import sys

import pygame
import pygame.gfxdraw as gfx

# ----------------------------------------------------------------- config
W, H = 960, 640
CX, CY = W // 2, H // 2
FPS = 60

EYE_W = 360        # meia-largura do olho (mundo)
EYE_H = 190        # meia-altura da pálpebra superior
IRIS_R = 125
PUPIL_R = 52

ZMAX = 12.0        # zoom máximo (mergulho dentro da pupila)
CYCLE = 18.0       # duração total do ciclo, em segundos

BG_TOP = (22, 5, 38)
BG_BOT = (72, 10, 62)
LIM = 30000        # limite seguro de coordenadas p/ gfxdraw

# ---------------------------------------------------------------- helpers
def clamp(x, lo=0.0, hi=1.0):
    return lo if x < lo else hi if x > hi else x


def lerp(a, b, t):
    return a + (b - a) * t


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = clamp(t)
    return (int(a[0] + (b[0] - a[0]) * t),
            int(a[1] + (b[1] - a[1]) * t),
            int(a[2] + (b[2] - a[2]) * t))


def aa_circle(surf, color, x, y, r):
    x, y, r = int(x), int(y), int(r)
    if r < 1:
        return
    if abs(x) < LIM and abs(y) < LIM and r < LIM:
        gfx.filled_circle(surf, x, y, r, color)
        gfx.aacircle(surf, x, y, r, color)
    else:
        pygame.draw.circle(surf, color, (x, y), r)


def aa_poly(surf, color, pts):
    ip = [(int(px), int(py)) for px, py in pts]
    if all(abs(px) < LIM and abs(py) < LIM for px, py in ip):
        gfx.filled_polygon(surf, ip, color)
        gfx.aapolygon(surf, ip, color)
    else:
        pygame.draw.polygon(surf, color, ip)


# ----------------------------------------------------------------- coração
HEART = []
for _i in range(100):
    _a = 2 * math.pi * _i / 100
    HEART.append((
        16 * math.sin(_a) ** 3 / 17,
        -(13 * math.cos(_a) - 5 * math.cos(2 * _a)
          - 2 * math.cos(3 * _a) - math.cos(4 * _a)) / 17 - 0.16,
    ))


def heart_pts(cx, cy, s):
    return [(cx + x * s, cy + y * s) for x, y in HEART]


def draw_heart(surf, cx, cy, s, dark, light, layers=9):
    """Coração com degradê (camadas sobrepostas) e brilho."""
    for k in range(layers):
        tt = k / (layers - 1)
        aa_poly(surf, mix(dark, light, tt),
                heart_pts(cx - 0.07 * s * tt, cy - 0.08 * s * tt, s * (1 - 0.5 * tt)))
    aa_circle(surf, (255, 236, 246), cx - 0.40 * s, cy - 0.44 * s, max(1, 0.09 * s))


def draw_star(surf, color, cx, cy, r):
    pts = []
    for k in range(8):
        ang = k * math.pi / 4
        rr = r if k % 2 == 0 else r * 0.22
        pts.append((cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    aa_poly(surf, color, pts)


# ------------------------------------------------------------ pré-render
def make_background():
    s = pygame.Surface((W, H))
    for y in range(H):
        pygame.draw.line(s, mix(BG_TOP, BG_BOT, y / H), (0, y), (W, y))
    return s


def make_vignette():
    s = pygame.Surface((W, H), pygame.SRCALPHA)
    s.fill((0, 0, 0, 225))
    R = math.hypot(CX, CY)
    N = 48
    for k in range(N):
        f = 1 - k / N
        a = int(225 * clamp((f - 0.40) / 0.60) ** 1.7)
        pygame.draw.circle(s, (8, 0, 14, a), (CX, CY), int(R * f))
    return s


# ---------------------------------------------------------------- timeline
def zoom_progress(t):
    t %= CYCLE
    if t < 3:
        return 0.0
    if t < 9:
        return smooth((t - 3) / 6)
    if t < 12:
        return 1.0
    if t < 15:
        return 1 - smooth((t - 12) / 3)
    return 0.0


def heartbeat(t):
    ph = (t * 1.1) % 1.0
    return max(math.exp(-((ph - 0.10) / 0.06) ** 2),
               0.6 * math.exp(-((ph - 0.30) / 0.07) ** 2))


# -------------------------------------------------------------------- main
def main():
    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Olho apaixonado")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 15)
    hud = font.render("ESPAÇO reinicia  •  ESC sai  •  mexa o mouse", True, (205, 150, 185))

    bg = make_background()
    vignette = make_vignette()
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    mask = pygame.Surface((W, H), pygame.SRCALPHA)

    rnd = random.Random(7)
    float_hearts = [[rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(8, 26),
                     rnd.uniform(14, 38), rnd.uniform(0, 6.28)] for _ in range(18)]
    sparkles = [(rnd.choice([-1, 1]) * rnd.uniform(300, 450),
                 rnd.choice([-1, 1]) * rnd.uniform(150, 280),
                 rnd.uniform(5, 13), rnd.uniform(0, 6.28)) for _ in range(14)]
    inner_hearts = [(rnd.uniform(-1, 1), rnd.random(),
                     rnd.uniform(0.05, 0.12), rnd.uniform(0.06, 0.13)) for _ in range(18)]

    t = 0.0
    gx = gy = 0.0
    mouse_moved = False
    running = True

    while running:
        dt = clock.tick(FPS) / 1000.0
        t += dt

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    running = False
                elif e.key == pygame.K_SPACE:
                    t = 0.0
            elif e.type == pygame.MOUSEMOTION:
                mouse_moved = True

        # ---------------- estado da animação
        p = zoom_progress(t)
        z = math.exp(math.log(ZMAX) * p)
        beat = heartbeat(t)

        # olhar: segue o mouse (ou vagueia sozinho)
        if mouse_moved:
            mx, my = pygame.mouse.get_pos()
            tx = clamp((mx - CX) / CX, -1, 1) * 150
            ty = clamp((my - CY) / CY, -1, 1) * 48
        else:
            tx = 60 * math.sin(t * 0.6)
            ty = 18 * math.sin(t * 0.9 + 1)
        gx += (tx - gx) * min(1.0, dt * 6)
        gy += (ty - gy) * min(1.0, dt * 6)
        s_in = clamp(p * 3)                 # iris centraliza ao mergulhar
        ix, iy = gx * (1 - s_in), gy * (1 - s_in)

        # piscadinha
        tb = t % 4.3
        blink = math.sin(math.pi * tb / 0.2) if tb < 0.2 else 0.0
        blink *= (1 - clamp(p * 20))
        openness = (0.93 + 0.02 * math.sin(t * 1.3)) * (1 - 0.96 * blink)

        def S(x, y):
            return CX + x * z, CY + y * z

        # ---------------- fundo
        screen.blit(bg, (0, 0))
        for h in float_hearts:
            h[1] -= h[3] * dt
            if h[1] < -40:
                h[1] = H + 40
                h[0] = rnd.uniform(0, W)
            hx = h[0] + math.sin(t * 0.8 + h[4]) * 18
            col = mix(mix(BG_TOP, BG_BOT, h[1] / H), (255, 95, 150), 0.18 + 0.25 * h[2] / 26)
            aa_poly(screen, col, heart_pts(hx, h[1], h[2]))

        # ---------------- contorno do olho (amendoado)
        n = 64
        up, lo = [], []
        for i in range(n + 1):
            u = -1 + 2 * i / n
            sh = (1 - u * u) ** 0.85
            up.append(S(u * EYE_W, -EYE_H * openness * sh))
            lo.append(S(u * EYE_W, EYE_H * 0.80 * openness * sh))
        outline = up + lo[::-1]

        # ---------------- camada interna do olho
        layer.fill((246, 150, 175, 255))
        N = 16
        for k in range(N):                                   # esclera rosada
            f = 1 - k / N
            col = mix((246, 150, 175), (255, 250, 252), smooth(k / (N * 0.55)))
            pygame.draw.circle(layer, col, (CX, CY), int(EYE_W * 1.12 * f * z))

        ic = S(ix, iy)
        ri = IRIS_R * z
        rp_w = PUPIL_R * (1 + 0.07 * beat)                   # pupila dilata
        pr = rp_w * z

        aa_circle(layer, (60, 8, 48), ic[0], ic[1], ri)      # anel límbico
        Ni = 34
        for k in range(Ni):                                  # íris em degradê
            tt = k / (Ni - 1)
            if tt < 0.5:
                col = mix((130, 20, 95), (232, 55, 135), tt / 0.5)
            else:
                col = mix((232, 55, 135), (255, 185, 210), (tt - 0.5) / 0.5)
            pygame.draw.circle(layer, col, (int(ic[0]), int(ic[1])), int(ri * (0.96 - 0.96 * k / Ni)))
        fw = max(1, int(z ** 0.5))
        for a in range(0, 360, 6):                           # fibras da íris
            ang = math.radians(a)
            col = (150, 25, 100) if (a // 6) % 2 == 0 else (255, 175, 208)
            c, s_ = math.cos(ang), math.sin(ang)
            pygame.draw.line(layer, col,
                             (ic[0] + c * pr * 1.08, ic[1] + s_ * pr * 1.08),
                             (ic[0] + c * ri * 0.92, ic[1] + s_ * ri * 0.92), fw)

        # pupila: fundo escuro + brilho vermelho vindo do coração
        aa_circle(layer, (35, 5, 35), ic[0], ic[1], pr)
        Ng = 22
        for k in range(Ng):
            tt = (k / (Ng - 1)) ** 1.5
            col = mix((35, 5, 35), (200, 35, 110), tt * (0.75 + 0.25 * beat))
            pygame.draw.circle(layer, col, (int(ic[0]), int(ic[1])), int(pr * 0.97 * (1 - k / Ng)))

        # coraçõezinhos flutuando dentro da pupila
        if z > 1.6:
            vis = smooth((z - 1.6) / 2)
            for u, ph, sp, sz in inner_hearts:
                v = (t * sp + ph) % 1
                ox = (u * 0.75 + 0.1 * math.sin(t * 1.7 + ph * 9)) * pr
                oy = lerp(0.8, -0.8, v) * pr
                if ox * ox + oy * oy > (0.8 * pr) ** 2:
                    continue
                a = math.sin(math.pi * v) * vis
                aa_poly(layer, mix((120, 20, 80), (255, 205, 228), a),
                        heart_pts(ic[0] + ox, ic[1] + oy, sz * pr))

        # >>> o coração, lá no fundo da pupila <<<
        hs = pr * 0.60 * (1 + 0.14 * beat)
        draw_heart(layer, ic[0], ic[1] + math.sin(t * 2) * 0.03 * pr, hs,
                   (150, 8, 55), (255, 120, 170))

        # brilhos (um deles em forma de coração)
        draw_heart(layer, ic[0] - 0.40 * ri, ic[1] - 0.42 * ri, ri * 0.17,
                   (255, 215, 235), (255, 255, 255), layers=3)
        aa_circle(layer, (255, 255, 255), ic[0] + 0.32 * ri, ic[1] + 0.34 * ri, ri * 0.075)

        # recorta tudo no formato do olho
        mask.fill((0, 0, 0, 0))
        pygame.draw.polygon(mask, (255, 255, 255, 255), outline)
        layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        screen.blit(layer, (0, 0))

        # ---------------- pálpebras, cílios e delineado
        w_lid = max(3, int(7 * z ** 0.5))
        pygame.draw.lines(screen, (70, 14, 52), False, up, w_lid)
        pygame.draw.lines(screen, (190, 90, 130), False, lo, max(2, w_lid // 2))
        wing = [S(EYE_W * 0.96, -4), S(EYE_W + 55, -34 * openness - 6), S(EYE_W * 0.86, -EYE_H * 0.12 * openness)]
        pygame.draw.polygon(screen, (70, 14, 52), wing)
        for u in (-0.88, -0.74, -0.60, -0.45, -0.30, -0.15, 0.0, 0.15, 0.30, 0.45, 0.60, 0.74, 0.88):
            sh = (1 - u * u) ** 0.85
            bx, by = u * EYE_W, -EYE_H * openness * sh
            L = 34 + 14 * (1 - abs(u))
            tip = S(bx + u * 28, by - L * (0.4 + 0.6 * openness))
            mid = S(bx + u * 10, by - L * 0.55 * openness)
            pygame.draw.line(screen, (70, 14, 52), S(bx, by), mid, max(2, w_lid // 2))
            pygame.draw.line(screen, (70, 14, 52), mid, tip, max(1, w_lid // 3))

        # ---------------- brilhinhos mágicos
        fade = 1 - clamp(p * 4)
        if fade > 0:
            for sx, sy, sr, ph in sparkles:
                b = (0.5 + 0.5 * math.sin(t * 2.4 + ph)) * fade
                col = mix(mix(BG_TOP, BG_BOT, 0.5), (255, 225, 238), b)
                draw_star(screen, col, CX + sx * z, CY + sy * z, sr * (0.5 + b))

        # ---------------- vinheta quando estamos "dentro"
        va = int(255 * smooth((p - 0.35) / 0.65) * 0.85)
        if va > 0:
            vignette.set_alpha(va)
            screen.blit(vignette, (0, 0))

        screen.blit(hud, (14, H - 26))
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
