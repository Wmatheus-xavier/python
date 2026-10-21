
import math
import os
import random
import shutil
import sys
import time

# ----------------------------------------------------------------- config
EYE_W, EYE_H = 360, 190     # meia-largura / meia-altura do olho (mundo)
IRIS_R = 125
PUPIL_R = 70
ZMAX = 6.5                  # zoom máximo (mergulho na pupila)
CYCLE = 18.0                # duração do ciclo (s)
FPS = 30
RAMP = " .:-=+*#%@"         # do mais vazio ao mais denso


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


def heart_f(dx, dy, s):
    """Função implícita do coração: <= 0 significa 'dentro'."""
    x = dx / s * 1.1
    y = -dy / s * 1.1 + 0.12
    a = x * x + y * y - 1
    return a * a * a - x * x * y * y * y


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


# ------------------------------------------------------------ elementos fixos
rnd = random.Random(7)
BG_HEARTS = [(rnd.uniform(-520, 520), rnd.uniform(0, 760), rnd.uniform(18, 46),
              rnd.uniform(14, 34), rnd.uniform(0, 6.28)) for _ in range(9)]
SPARKS = [(rnd.choice([-1, 1]) * rnd.uniform(300, 460),
           rnd.choice([-1, 1]) * rnd.uniform(130, 290),
           rnd.uniform(0, 6.28)) for _ in range(16)]
INNER = [(rnd.uniform(-1, 1), rnd.random(),
          rnd.uniform(0.05, 0.12), rnd.uniform(0.06, 0.13)) for _ in range(16)]
LASH_U = [-0.88, -0.74, -0.60, -0.45, -0.30, -0.15, 0.0,
          0.15, 0.30, 0.45, 0.60, 0.74, 0.88]


# ----------------------------------------------------------------- render
def render(cols, rows, t, mono):
    p = zoom_progress(t)
    z = math.exp(math.log(ZMAX) * p)
    beat = heartbeat(t)

    s_in = clamp(p * 3)                       # íris centraliza ao mergulhar
    ix = 60 * math.sin(t * 0.6) * (1 - s_in)
    iy = 18 * math.sin(t * 0.9 + 1) * (1 - s_in)

    tb = t % 4.3                              # piscadinha
    blink = math.sin(math.pi * tb / 0.2) if tb < 0.2 else 0.0
    blink *= 1 - clamp(p * 20)
    op = (0.93 + 0.02 * math.sin(t * 1.3)) * (1 - 0.96 * blink)

    sx = 960.0 / cols                         # largura de uma célula (mundo)
    sy = 2 * sx                               # caractere é ~2x mais alto que largo
    cwx, chy = sx / z, sy / z
    th = 16 / z ** 0.5                        # espessura da pálpebra

    pr = PUPIL_R * (1 + 0.07 * beat)          # pupila dilata no ritmo do coração
    hs = pr * 0.48 * (1 + 0.14 * beat)
    hby = math.sin(t * 2) * 0.03 * pr
    vig = smooth((p - 0.35) / 0.65)

    # cílios
    lashes = []
    for uk in LASH_U:
        shk = (1 - uk * uk) ** 0.85
        L = (34 + 14 * (1 - abs(uk))) * (0.4 + 0.6 * op) * 1.6
        lashes.append((uk * EYE_W, -EYE_H * op * shk, uk, L))

    # corações de fundo
    bgh = []
    for x0, y0, sz, spd, ph in BG_HEARTS:
        y = ((y0 - t * spd) % 760) - 380
        bgh.append((x0 + 18 * math.sin(t * 0.8 + ph), y, sz))

    # brilhinhos
    sparks = []
    for x0, y0, ph in SPARKS:
        b = 0.5 + 0.5 * math.sin(t * 2.4 + ph)
        if b > 0.25:
            sparks.append((x0, y0, b))

    # coraçõezinhos dentro da pupila
    minis = []
    if z > 1.4:
        vis = smooth((z - 1.4) / 1.5)
        for u, ph, sp, sz in INNER:
            v = (t * sp + ph) % 1
            ox = (u * 0.75 + 0.1 * math.sin(t * 1.7 + ph * 9)) * pr
            oy = lerp(0.8, -0.8, v) * pr
            if ox * ox + oy * oy > (0.8 * pr) ** 2:
                continue
            a = math.sin(math.pi * v) * vis
            if a > 0.08:
                minis.append((ox, oy, sz * pr * 2.0, a))

    hl_s = 0.20 * IRIS_R
    WHITE = (255, 238, 246)

    def sample(wx, wy):
        u = wx / EYE_W
        if -1 <= u <= 1:
            sh = (1 - u * u) ** 0.85
            yt = -EYE_H * op * sh
            yb = 0.8 * EYE_H * op * sh
            if yt <= wy <= yb:
                if wy - yt < th:                       # pálpebra superior
                    return '#', (175, 45, 130), 1.0
                if yb - wy < th * 0.6:                 # pálpebra inferior
                    return '=', (235, 120, 170), 0.9
                dx, dy = wx - ix, wy - iy
                d = math.sqrt(dx * dx + dy * dy)
                if d <= IRIS_R:
                    if d <= pr:                        # ---- PUPILA
                        hy = dy - hby
                        if abs(dx) < 1.1 * hs and abs(hy) < 1.1 * hs:
                            fh = heart_f(dx, hy, hs)
                            if fh <= 0:                # >>> o coração <<<
                                x, y = dx / hs, hy / hs
                                hl = clamp(1 - math.hypot(x + 0.35, y + 0.35) / 2.4)
                                lum = 0.50 + 0.48 * hl
                                if fh > -0.03:         # contorno mais escuro
                                    lum *= 0.75
                                return None, mix((205, 20, 85), (255, 150, 195), hl), lum
                        for ox, oy, ms, a in minis:
                            if (abs(dx - ox) < 1.1 * ms and abs(dy - oy) < 1.1 * ms
                                    and heart_f(dx - ox, dy - oy, ms) <= 0):
                                return None, (255, 195, 225), 0.55 + 0.45 * a
                        glow = (1 - d / pr) ** 1.5 * (0.8 + 0.2 * beat)
                        return None, (225, 35, 105), 0.03 + 0.2 * glow
                    tt = (d - pr) / (IRIS_R - pr)      # ---- ÍRIS
                    if (abs(dx + 0.40 * IRIS_R) < 1.1 * hl_s and abs(dy + 0.42 * IRIS_R) < 1.1 * hl_s
                            and heart_f(dx + 0.40 * IRIS_R, dy + 0.42 * IRIS_R, hl_s) <= 0):
                        return '@', WHITE, 1.0         # brilho em formato de coração
                    if (dx - 0.32 * IRIS_R) ** 2 + (dy - 0.34 * IRIS_R) ** 2 < (0.08 * IRIS_R) ** 2:
                        return '@', WHITE, 1.0
                    if tt > 0.92:
                        return None, (120, 20, 85), 0.35
                    fib = math.sin(math.atan2(dy, dx) * 22)
                    lum = lerp(0.72, 0.40, tt ** 0.8) + 0.10 * fib
                    return None, mix((255, 185, 212), (190, 40, 120), tt), lum
                return None, mix((255, 248, 250), (246, 150, 175), u * u), 0.13   # esclera
            # fora do olho, perto da pálpebra de cima: cílios
            if wy < 0 and wy > -EYE_H * op - 90:
                for bx, by, uk, L in lashes:
                    s_ = by - wy
                    if 0 < s_ < L and abs(wx - (bx + uk * 0.9 * s_)) < cwx * 0.9:
                        c = '/' if uk > 0.25 else '\\' if uk < -0.25 else '|'
                        return c, (215, 70, 150), 0.9
        for hx, hy_, hsz in bgh:                       # corações flutuando
            if abs(wx - hx) < 1.1 * hsz and abs(wy - hy_) < 1.1 * hsz and heart_f(wx - hx, wy - hy_, hsz) <= 0:
                return None, (255, 95, 150), 0.38
        for px, py, b in sparks:                       # brilhinhos
            if abs(wx - px) < cwx * 0.6 and abs(wy - py) < chy * 0.6:
                return ('*' if b > 0.7 else '+' if b > 0.45 else '.'), (255, 225, 238), 0.9
        return ' ', None, 0

    lines = []
    ramp_max = len(RAMP) - 1
    for r in range(rows):
        wy = (r + 0.5 - rows / 2) * chy
        row = []
        prev = None
        for c in range(cols):
            wx = (c + 0.5 - cols / 2) * cwx
            ch, col, lum = sample(wx, wy)
            if vig > 0:                                 # vinheta: "estamos dentro"
                dist = math.hypot((c + 0.5 - cols / 2) / (cols / 2), (r + 0.5 - rows / 2) / (rows / 2))
                lum *= 1 - 0.8 * vig * clamp((dist - 0.45) / 0.7)
            if ch is None:
                ch = RAMP[int(clamp(lum) * ramp_max + 0.5)]
            if ch == ' ':
                row.append(' ')
                continue
            if not mono:
                k = 0.45 + 0.55 * clamp(lum)
                rgb = (int(col[0] * k), int(col[1] * k), int(col[2] * k))
                if rgb != prev:
                    row.append("\x1b[38;2;%d;%d;%dm" % rgb)
                    prev = rgb
            row.append(ch)
        lines.append(''.join(row))
    return lines


# -------------------------------------------------------------------- main
def main():
    mono = "--mono" in sys.argv
    if os.name == "nt":
        os.system("")                                   # habilita ANSI no Windows

    out = sys.stdout
    out.write("\x1b[?25l\x1b[2J")
    last_size = None
    t0 = time.time()
    try:
        while True:
            frame_start = time.time()
            size = shutil.get_terminal_size((120, 40))
            cols = max(60, min(size.columns, 160))
            rows = max(20, min(size.lines - 2, 52))
            if (cols, rows) != last_size:
                out.write("\x1b[2J")
                last_size = (cols, rows)

            t = frame_start - t0
            lines = render(cols, rows, t, mono)
            caption = "<3  olho apaixonado  -  Ctrl+C para sair"
            out.write("\x1b[H" + "\x1b[0m\x1b[K\n".join(lines) + "\x1b[0m\x1b[K\n")
            out.write("\x1b[2m" + caption + "\x1b[0m\x1b[K")
            out.flush()

            delay = 1.0 / FPS - (time.time() - frame_start)
            if delay > 0:
                time.sleep(delay)
    except KeyboardInterrupt:
        pass
    finally:
        out.write("\x1b[0m\x1b[?25h\n")
        out.flush()


if __name__ == "__main__":
    main()
