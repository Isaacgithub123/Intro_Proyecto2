import pygame, sys, random, time, json, os
from math import sin

ANCHO_PANTALLA, ALTO_PANTALLA = 1280, 720
FPS = 60
TAMANO_CASILLA = 48


NEON_CIAN = (37, 222, 255)
NEON_VIOLETA = (163, 94, 255)
NEON_ROSA = (255, 83, 164)
FONDO = (12, 14, 20)
FONDO_PANEL = (18, 20, 28)
TEXTO = (230, 230, 240)
COLOR_TILE = {
    0: (40, 44, 52),
    1: (34,183,90),
    2: (110,118,138),
    3: (70,70,90),
}
COLOR_JUGADOR = (255, 200, 70)
COLOR_CAZADOR = (220, 70, 70)
COLOR_CORREDOR = (80, 180, 255)
SCORE_FILE = "scores.json"

def crear_mapa(filas=12, columnas=12):
    mapa = [[3 for _ in range(columnas)] for _ in range(filas)]
    mapa = agregar_camino_principal(mapa, filas, columnas)
    mapa = agregar_caminos_secundarios(mapa, filas, columnas)
    mapa = agregar_red_tuneles(mapa, filas, columnas)
    mapa = agregar_lianas(mapa, filas, columnas)
    mapa[0][0] = 0
    mapa[filas-1][columnas-1] = 0
    return mapa

def agregar_camino_principal(mapa, filas, columnas):
    i, j = 0, 0
    while i < filas-1 or j < columnas-1:
        mapa[i][j] = 0
        if i < filas-1 and j < columnas-1:
            if random.choice([True, False]): i += 1
            else: j += 1
        elif i < filas-1: i += 1
        else: j += 1
    mapa[filas-1][columnas-1] = 0
    return mapa

def agregar_caminos_secundarios(mapa, filas, columnas):
    for _ in range(15):
        i = random.randint(0, filas-1)
        j = random.randint(0, columnas-1)
        if mapa[i][j] == 3: mapa[i][j] = 0
    return mapa

def agregar_red_tuneles(mapa, filas, columnas):
    for _ in range(2):
        i, j = random.randint(1, filas-2), random.randint(1, columnas-2)
        if mapa[i][j] == 3: crear_tunel(mapa, i, j, filas, columnas)
    return mapa

def crear_tunel(mapa, i, j, filas, columnas):
    for _ in range(8):
        if mapa[i][j] == 3: mapa[i][j] = 2
        dirs = [[0,1],[1,0],[0,-1],[-1,0]]
        di, dj = random.choice(dirs)
        i = max(0, min(filas-1, i + di))
        j = max(0, min(columnas-1, j + dj))

def agregar_lianas(mapa, filas, columnas):
    for _ in range(3):
        i, j = random.randint(1, filas-2), random.randint(1, columnas-2)
        if mapa[i][j] == 3: crear_liana(mapa, i, j, filas, columnas)
    return mapa

def crear_liana(mapa, i, j, filas, columnas):
    for _ in range(6):
        if mapa[i][j] == 3: mapa[i][j] = 1
        dirs = [[0,1],[1,0],[0,-1],[-1,0]]
        di, dj = random.choice(dirs)
        i = max(0, min(filas-1, i + di))
        j = max(0, min(columnas-1, j + dj))

def mover_enemigos(mapa, enemigos, objetivo, filas, columnas, modo):
    nuevos = []
    for enemigo in enemigos:
        ei, ej = enemigo
        if modo == "escapa":
            dist_i = objetivo[0] - ei
            dist_j = objetivo[1] - ej
            movimientos = []
            if abs(dist_i) > abs(dist_j):
                if dist_i > 0: movimientos.append([1, 0])
                else: movimientos.append([-1, 0])
                if dist_j > 0: movimientos.append([0, 1])
                else: movimientos.append([0, -1])
            else:
                if dist_j > 0: movimientos.append([0, 1])
                else: movimientos.append([0, -1])
                if dist_i > 0: movimientos.append([1, 0])
                else: movimientos.append([-1, 0])
        else:
            movimientos = [[0,1], [1,0], [0,-1], [-1,0]]
            random.shuffle(movimientos)
        movimientos.extend([[0,1], [1,0], [0,-1], [-1,0]])
        for di, dj in movimientos:
            nueva_i = ei + di
            nueva_j = ej + dj
            nueva_pos = [nueva_i, nueva_j]
            if (0 <= nueva_i < filas and 0 <= nueva_j < columnas and 
                ((modo == "escapa" and mapa[nueva_i][nueva_j] in [0, 1]) or
                 (modo == "cazador" and mapa[nueva_i][nueva_j] in [0, 2])) and
                nueva_pos not in nuevos):
                nuevos.append(nueva_pos)
                break
        else: nuevos.append(enemigo)
    return nuevos

def safe_load_scores():
    if not os.path.exists(SCORE_FILE):
        return {"escapa": [], "cazador": []}
    try:
        with open(SCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"escapa": [], "cazador": []}

def safe_save_scores(scores):
    try:
        with open(SCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("No se pudo guardar scores:", e)


class Juego:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
        pygame.display.set_caption("Escapa / Cazador - Completo")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 26)
        self.large_font = pygame.font.Font(None, 40)
        self.big_font = pygame.font.Font(None, 64)


        self.state = "registro"
        self.name = ""
        self.input_active = False

        self.filas = 12; self.columnas = 12
        self.mapa = None
        self.mode = "escapa"
        self.player = [0,0]
        self.exit = None
        self.cazadores = []
        self.corredores = []
        self.traps = []
        self.max_traps = 3
        self.trap_cooldown = 5.0
        self.last_trap_time = -999.0
        self.respawn_delay = 10.0
        self.respawn_queue = []
        self.game_time = 0.0
        self.moves = 0
        self.captured = 0
        self.score = 0

        self.final_state = None
        self.final_score = 0
        self.final_time = 0
        self.final_msg_timer = 0.0

        self.energy = 100
        self.max_energy = 100
        self.sprint_cost = 20
        self.energy_regen_rate = 8.0

        self.scores = safe_load_scores()

    def dibujar_texto(self, text, x, y, color=TEXTO, center=False, size="small"):
        f = self.font if size=="small" else self.large_font if size=="large" else self.big_font
        surf = f.render(text, True, color)
        if center:
            rect = surf.get_rect(center=(x,y))
            self.screen.blit(surf, rect)
        else:
            self.screen.blit(surf, (x,y))

    def rect_redondeado(self, surf, rect, color, r=10, border=0, border_color=(0,0,0)):
        pygame.draw.rect(surf, color, rect, border_radius=r)
        if border>0:
            pygame.draw.rect(surf, border_color, rect, width=border, border_radius=r)

    def manejar_eventos(self):
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if self.state == "registro":
                self.manejar_registro(e)
            elif self.state == "menu":
                self.manejar_menu(e)
            elif self.state == "puntajes":
                self.manejar_puntajes(e)
            elif self.state == "juego":
                self.manejar_juego(e)
            elif self.state == "fin_partida":
                self.manejar_fin_partida(e)

    def manejar_registro(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN:
            box = pygame.Rect(ANCHO_PANTALLA//2-200, ALTO_PANTALLA//2, 400, 44)
            self.input_active = box.collidepoint(e.pos)
        if e.type == pygame.KEYDOWN and self.input_active:
            if e.key == pygame.K_RETURN:
                if self.name.strip() != "":
                    self.state = "menu"
            elif e.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            else:
                if len(self.name) < 18 and e.unicode.isprintable():
                    self.name += e.unicode

    def manejar_menu(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            mx,my = e.pos
            bx = ANCHO_PANTALLA//2 - 180
            r1 = pygame.Rect(bx, 220, 360, 56)
            r2 = pygame.Rect(bx, 300, 360, 56)
            r3 = pygame.Rect(bx, 380, 360, 56)
            r4 = pygame.Rect(bx, 460, 360, 56)
            if r1.collidepoint(mx,my):
                self.iniciar_juego("escapa")
            elif r2.collidepoint(mx,my):
                self.iniciar_juego("cazador")
            elif r3.collidepoint(mx,my):
                self.state = "puntajes"
            elif r4.collidepoint(mx,my):
                pygame.quit(); sys.exit()

    def manejar_puntajes(self, e):
        if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            self.state = "menu"
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            self.state = "menu"

    def manejar_juego(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            if self.mode == "escapa":
                mx,my = e.pos
                tile = self.pantalla_a_casilla(mx,my)
                if tile:
                    i,j = tile
                    now = time.time()
                    if now - self.last_trap_time < self.trap_cooldown:
                        self.mostrar_mensaje_temporal("Trampa en recarga", 1.0)
                    elif len(self.traps) >= self.max_traps:
                        self.mostrar_mensaje_temporal("Máx. trampas colocadas", 1.0)
                    elif not (0 <= i < self.filas and 0 <= j < self.columnas):
                        self.mostrar_mensaje_temporal("Fuera del mapa", 0.8)
                    elif self.mapa[i][j] != 0:
                        self.mostrar_mensaje_temporal("Solo se pueden colocar trampas en camino", 1.0)
                    else:
                        self.colocar_trampa(i,j)
                        self.last_trap_time = now
                        self.mostrar_mensaje_temporal("Trampa colocada", 0.8)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                self.finalizar_y_guardar()
                self.state = "menu"
                return
            if e.key in (pygame.K_w, pygame.K_UP, pygame.K_s, pygame.K_DOWN,
                         pygame.K_a, pygame.K_LEFT, pygame.K_d, pygame.K_RIGHT):
                di,dj = 0,0
                if e.key in (pygame.K_w, pygame.K_UP): di = -1
                elif e.key in (pygame.K_s, pygame.K_DOWN): di = 1
                elif e.key in (pygame.K_a, pygame.K_LEFT): dj = -1
                elif e.key in (pygame.K_d, pygame.K_RIGHT): dj = 1
                sprint = pygame.key.get_mods() & pygame.KMOD_SHIFT
                self.intentar_mover(di,dj, bool(sprint))

    def manejar_fin_partida(self, e):
        if (e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN) or (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1):
            self.finalizar_y_guardar(final=True)
            self.state = "menu"
            self.final_state = None
            self.final_msg_timer = 0.0

    def pantalla_a_casilla(self, mx, my):
        center_col = self.player[1]; center_row = self.player[0]
        offset_x = ANCHO_PANTALLA//2 - center_col * TAMANO_CASILLA
        offset_y = ALTO_PANTALLA//2 - center_row * TAMANO_CASILLA
        tx = (mx - offset_x) // TAMANO_CASILLA
        ty = (my - offset_y) // TAMANO_CASILLA
        try:
            return int(ty), int(tx)
        except Exception:
            return None

    def colocar_trampa(self, i, j):
        t = {'pos':[i,j], 'placed_at': time.time()}
        self.traps.append(t)

    def intentar_mover(self, di, dj, sprint=False):
        if not self.mapa: return
        steps = 2 if sprint and self.energy >= self.sprint_cost else 1
        ni, nj = self.player[0], self.player[1]
        for step in range(steps):
            ni += di; nj += dj
            if not (0 <= ni < self.filas and 0 <= nj < self.columnas):
                self.mostrar_mensaje_temporal("Movimiento fuera del mapa", 0.6)
                return
            celda = self.mapa[ni][nj]
            allowed = (self.mode == "escapa" and celda in [0,2]) or (self.mode == "cazador" and celda in [0,2])
            if not allowed:
                self.mostrar_mensaje_temporal("Movimiento bloqueado", 0.6)
                return
        if steps == 2:
            self.energy = max(0, self.energy - self.sprint_cost)
        self.player = [ni, nj]
        self.moves += 1
        self.despues_de_mover_jugador()

    def despues_de_mover_jugador(self):
        if self.mode == "escapa":
            if self.player == self.exit:
                t = int(self.game_time)
                self.score = max(0, 1000 - t*8 + self.captured*200)
                self.final_state = "victoria"
                self.final_score = int(self.score)
                self.final_time = int(self.game_time)
                self.final_msg_timer = 4.0
                self.state = "fin_partida"
                return
            self.cazadores = mover_enemigos(self.mapa, self.cazadores, self.player, self.filas, self.columnas, "escapa")
            remaining = []
            for epos in self.cazadores:
                if any(t['pos']==epos for t in self.traps):
                    self.captured += 1
                    self.score += 200
                    self.traps = [t for t in self.traps if t['pos'] != epos]
                    self.respawn_queue.append( (time.time() + self.respawn_delay, "escapa") )
                else:
                    remaining.append(epos)
            self.cazadores = remaining
            for epos in self.cazadores:
                if epos == self.player:
                    self.score = max(0, int(500 - int(self.game_time)*2))
                    self.final_state = "derrota"
                    self.final_score = int(self.score)
                    self.final_time = int(self.game_time)
                    self.final_msg_timer = 4.0
                    self.state = "fin_partida"
                    return

        else:
            caught = [c for c in self.corredores if c == self.player]
            for c in caught:
                self.corredores.remove(c)
                self.captured += 1
                self.score += 300
                self.respawn_queue.append( (time.time() + self.respawn_delay, "cazador") )
            if self.captured >= 3:
                self.final_state = "victoria"
                self.final_score = int(self.score)
                self.final_time = int(self.game_time)
                self.final_msg_timer = 4.0
                self.state = "fin_partida"
                return
            self.corredores = mover_enemigos(self.mapa, self.corredores, self.player, self.filas, self.columnas, "cazador")
            exits = [[0,0], [0,self.columnas-1], [self.filas-1,0]]
            escaped = [c for c in self.corredores if c in exits]
            if escaped:
                self.score = max(0, self.score - len(escaped)*150)
            self.corredores = [c for c in self.corredores if c not in exits]
            if len(self.corredores) == 0 and self.captured < 3:
                self.final_state = "derrota"
                self.final_score = int(self.score)
                self.final_time = int(self.game_time)
                self.final_msg_timer = 4.0
                self.state = "fin_partida"
                return

    def actualizar_tareas_de_fondo(self, dt):
        now = time.time()
        pending = []
        for ts, modo in list(self.respawn_queue):
            if now >= ts:
                if modo == "escapa":
                    self.generar_cazador()
                else:
                    self.generar_corredor()
            else:
                pending.append((ts,modo))
        self.respawn_queue = pending

        if self.energy < self.max_energy:
            self.energy = min(self.max_energy, self.energy + self.energy_regen_rate * dt)

        self.game_time += dt

    def generar_cazador(self):
        tries = 0
        while tries < 200:
            i = random.randint(1, self.filas-2)
            j = random.randint(1, self.columnas-2)
            if self.mapa[i][j] in [0,1] and [i,j] != self.player and [i,j] != self.exit and [i,j] not in self.cazadores:
                self.cazadores.append([i,j]); return
            tries += 1

    def generar_corredor(self):
        tries = 0
        while tries < 200:
            i = random.randint(1, self.filas-2)
            j = random.randint(1, self.columnas-2)
            if self.mapa[i][j] in [0,2] and [i,j] != self.player and [i,j] not in self.corredores:
                if [i,j] not in [[0,0],[0,self.columnas-1],[self.filas-1,0]]:
                    self.corredores.append([i,j]); return
            tries += 1

    def finalizar_y_guardar(self, final=False):
        if not self.final_score:
            t = int(self.game_time)
            if self.mode == "escapa":
                self.final_score = max(0, 1000 - t*8 + self.captured*200)
            else:
                self.final_score = max(0, self.captured*300 - t*2)

        mode_key = "escapa" if self.mode=="escapa" else "cazador"
        entry = {"name": self.name or "Anon", "score": int(self.final_score)}
        lst = self.scores.get(mode_key, [])
        lst.append(entry)
        lst = sorted(lst, key=lambda x: x['score'], reverse=True)[:5]
        self.scores[mode_key] = lst
        safe_save_scores(self.scores)

        self.traps = []
        self.respawn_queue = []
        self.cazadores = []
        self.corredores = []
        self.game_time = 0.0
        self.moves = 0
        self.captured = 0
        self.score = 0
        self.energy = self.max_energy
        self.final_score = 0
        self.final_time = 0
        self.final_state = None

    def mostrar_mensaje(self, text, duration=2.5):
        self.msg = text
        self.msg_t = duration

    def mostrar_mensaje_temporal(self, text, duration=1.0):
        self.mostrar_mensaje(text, duration)

    def dibujar_mapa(self):
        center_col = self.player[1]; center_row = self.player[0]
        offset_x = ANCHO_PANTALLA//2 - center_col * TAMANO_CASILLA
        offset_y = ALTO_PANTALLA//2 - center_row * TAMANO_CASILLA
        for r in range(self.filas):
            for c in range(self.columnas):
                x = offset_x + c*TAMANO_CASILLA
                y = offset_y + r*TAMANO_CASILLA
                rect = pygame.Rect(x,y,TAMANO_CASILLA,TAMANO_CASILLA)
                color = COLOR_TILE.get(self.mapa[r][c], (50,50,50))
                pygame.draw.rect(self.screen, color, rect)
                pygame.draw.rect(self.screen, (8,8,8), rect, 1)

    def dibujar_entidades(self):
        cx = ANCHO_PANTALLA//2
        cy = ALTO_PANTALLA//2

        tile_center_x = cx + TAMANO_CASILLA//2
        tile_center_y = cy + TAMANO_CASILLA//2

        if self.mode == "escapa" and self.exit:
            sx = cx - (self.player[1] - self.exit[1]) * TAMANO_CASILLA
            sy = cy - (self.player[0] - self.exit[0]) * TAMANO_CASILLA
            pygame.draw.rect(self.screen, (240,200,80), (sx+8, sy+8, TAMANO_CASILLA-16, TAMANO_CASILLA-16), border_radius=6)

        for t in self.traps:
            i,j = t['pos']
            tx = cx - (self.player[1] - j) * TAMANO_CASILLA
            ty = cy - (self.player[0] - i) * TAMANO_CASILLA
            r = pygame.Rect(tx+12, ty+12, TAMANO_CASILLA-24, TAMANO_CASILLA-24)
            s = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
            s.fill((*NEON_ROSA, 140))
            self.screen.blit(s, (r.left, r.top))
            pygame.draw.rect(self.screen, (200,40,100), r, 2, border_radius=6)

        if self.mode == "escapa":
            for e in self.cazadores:
                ex = cx - (self.player[1] - e[1]) * TAMANO_CASILLA
                ey = cy - (self.player[0] - e[0]) * TAMANO_CASILLA
                pygame.draw.circle(self.screen, COLOR_CAZADOR, (int(ex+TAMANO_CASILLA/2), int(ey+TAMANO_CASILLA/2)), max(6, TAMANO_CASILLA//4))
        else:
            for e in self.corredores:
                ex = cx - (self.player[1] - e[1]) * TAMANO_CASILLA
                ey = cy - (self.player[0] - e[0]) * TAMANO_CASILLA
                pygame.draw.circle(self.screen, COLOR_CORREDOR, (int(ex+TAMANO_CASILLA/2), int(ey+TAMANO_CASILLA/2)), max(5, TAMANO_CASILLA//5))

        pygame.draw.circle(self.screen, COLOR_JUGADOR, (tile_center_x, tile_center_y), max(6, TAMANO_CASILLA//4))
        pygame.draw.circle(self.screen, (14,16,20), (tile_center_x, tile_center_y), max(6, TAMANO_CASILLA//4), 2)

    def dibujar_hud(self):
        p = pygame.Rect(14, 12, 360, 72)
        self.rect_redondeado(self.screen, p, FONDO_PANEL, r=12, border=2, border_color=(30,30,40))
        self.dibujar_texto(f"Jugador: {self.name or 'Anon'}", p.left+12, p.top+8)
        self.dibujar_texto(f"Modo: {self.mode.capitalize()}", p.left+12, p.top+34, color=(180,200,220))
        eb = pygame.Rect(14, 92, 260, 20)
        pygame.draw.rect(self.screen, (22,24,30), eb, border_radius=8)
        inner_w = int((self.energy/self.max_energy) * (eb.width-6))
        if inner_w > 0:
            inner = pygame.Rect(eb.left+3, eb.top+3, inner_w, eb.height-6)
            pygame.draw.rect(self.screen, NEON_CIAN, inner, border_radius=6)
        pygame.draw.rect(self.screen, (38,38,46), eb, 2, border_radius=8)
        self.dibujar_texto(f"Energía: {int(self.energy)}%", eb.right+8, eb.top+1)

        tp = pygame.Rect(ANCHO_PANTALLA - 260, 12, 240, 72)
        self.rect_redondeado(self.screen, tp, FONDO_PANEL, r=12, border=2, border_color=(30,30,40))
        self.dibujar_texto(f"Trampas: {len(self.traps)}/{self.max_traps}", tp.left+12, tp.top+8)
        cd = max(0.0, self.trap_cooldown - max(0.0, time.time() - self.last_trap_time))
        self.dibujar_texto(f"Recarga: {cd:.1f}s", tp.left+12, tp.top+36, color=(200,200,210))

        self.dibujar_texto(f"Tiempo: {int(self.game_time)}s", ANCHO_PANTALLA - 140, 18)
        self.dibujar_texto(f"Movimientos: {self.moves}", ANCHO_PANTALLA - 140, 44)
        self.dibujar_texto(f"Puntos: {int(self.score)}", ANCHO_PANTALLA//2 - 40, 18)
        if self.mode == "cazador":
            self.dibujar_texto(f"Atrapados: {self.captured}", ANCHO_PANTALLA//2 - 40, 44)

        if hasattr(self, "msg") and getattr(self, "msg", ""):
            f = self.big_font
            surf = f.render(self.msg, True, (240,240,240))
            rect = surf.get_rect(center=(ANCHO_PANTALLA//2, ALTO_PANTALLA//2 - 140))
            bg = pygame.Surface((rect.width+30, rect.height+18), pygame.SRCALPHA)
            bg.fill((6,6,8, 200))
            self.rect_redondeado(bg, bg.get_rect(), (10,10,12,200), r=10)
            self.screen.blit(bg, (rect.left-15, rect.top-8))
            self.screen.blit(surf, rect.topleft)

    def dibujar_registro(self):
        self.dibujar_texto("Registro - Ingrese su nombre y presione ENTER", ANCHO_PANTALLA//2, 120, center=True, size="large")
        box = pygame.Rect(ANCHO_PANTALLA//2-240, ALTO_PANTALLA//2, 480, 48)
        pygame.draw.rect(self.screen, (28,28,34), box, border_radius=10)
        pygame.draw.rect(self.screen, (60,60,70), box, 2, border_radius=10)
        txt = self.font.render(self.name or "Escriba aquí...", True, (200,200,210))
        self.screen.blit(txt, (box.x+14, box.y+12))
        self.dibujar_texto("Clic en el recuadro para activar escritura", ANCHO_PANTALLA//2, box.y+64, center=True)

    def dibujar_menu(self):
        for i in range(12):
            alpha = 10 + int(8*sin(time.time()*0.8 + i))
            line = pygame.Surface((ANCHO_PANTALLA, 2), pygame.SRCALPHA)
            line.fill((*NEON_VIOLETA, max(0,alpha)))
            self.screen.blit(line, (0, 120 + i*28))
        self.dibujar_texto("Escapa / Cazador", ANCHO_PANTALLA//2, 72, center=True, size="large")
        self.dibujar_texto(f"Jugador: {self.name or 'Anon'}", ANCHO_PANTALLA//2, 120, center=True)
        bx = ANCHO_PANTALLA//2 - 180
        r1 = pygame.Rect(bx, 220, 360, 56)
        r2 = pygame.Rect(bx, 300, 360, 56)
        r3 = pygame.Rect(bx, 380, 360, 56)
        r4 = pygame.Rect(bx, 460, 360, 56)
        for r, text in [(r1,"Iniciar - Escapa"), (r2,"Iniciar - Cazador"), (r3,"Puntajes"), (r4,"Salir")]:
            pygame.draw.rect(self.screen, (30,30,36), r, border_radius=12)
            pygame.draw.rect(self.screen, (60,60,80), r, 2, border_radius=12)
            self.dibujar_texto(text, r.centerx, r.centery, center=True)

    def dibujar_puntajes(self):
        self.dibujar_texto("Top 5 - Puntajes", ANCHO_PANTALLA//2, 72, center=True, size="large")
        left = ANCHO_PANTALLA//2 - 260
        top = 140
        self.dibujar_texto("Escapa", left+120, top, center=True)
        for i,entry in enumerate(self.scores.get("escapa",[])):
            self.dibujar_texto(f"{i+1}. {entry['name']} - {entry['score']}", left+120, top+40 + i*30)
        left2 = ANCHO_PANTALLA//2 + 20
        self.dibujar_texto("Cazador", left2+120, top, center=True)
        for i,entry in enumerate(self.scores.get("cazador",[])):
            self.dibujar_texto(f"{i+1}. {entry['name']} - {entry['score']}", left2+120, top+40 + i*30)
        self.dibujar_texto("Presione ESC o clic para volver", ANCHO_PANTALLA//2, ALTO_PANTALLA-40, center=True)

    def dibujar_pantalla_final(self):
        overlay = pygame.Surface((ANCHO_PANTALLA, ALTO_PANTALLA), pygame.SRCALPHA)
        overlay.fill((6,6,8,160))
        self.screen.blit(overlay, (0,0))

        ancho, alto = 520, 260
        x = ANCHO_PANTALLA//2 - ancho//2
        y = ALTO_PANTALLA//2 - alto//2
        panel = pygame.Rect(x, y, ancho, alto)
        self.rect_redondeado(self.screen, panel, FONDO_PANEL, r=16)
        pygame.draw.rect(self.screen, NEON_CIAN, panel, 2, border_radius=16)

        fuente_t = pygame.font.Font(None, 64)
        fuente = pygame.font.Font(None, 30)

        if self.final_state == "victoria":
            titulo = "¡GANASTE!"
            color = (120,255,180)
        else:
            titulo = "¡PERDISTE!"
            color = (255,120,120)

        txt_t = fuente_t.render(titulo, True, color)
        self.screen.blit(txt_t, (panel.centerx - txt_t.get_width()//2, panel.top + 28))

        txt_p = fuente.render(f"Puntuación: {self.final_score}", True, TEXTO)
        txt_tm = fuente.render(f"Tiempo: {self.final_time} s", True, TEXTO)
        self.screen.blit(txt_p, (panel.centerx - txt_p.get_width()//2, panel.top + 120))
        self.screen.blit(txt_tm, (panel.centerx - txt_tm.get_width()//2, panel.top + 160))

        hint = "Presione ENTER o haga clic para volver al menú"
        txt_c = fuente.render(hint, True, (180,200,220))
        self.screen.blit(txt_c, (panel.centerx - txt_c.get_width()//2, panel.bottom - 44))

    def iniciar_juego(self, mode):
        self.mode = mode
        self.mapa = crear_mapa(self.filas, self.columnas)
        self.player = [0,0] if mode=="escapa" else [self.filas-1, self.columnas-1]
        self.exit = [self.filas-1, self.columnas-1] if mode=="escapa" else None
        self.cazadores = []; self.corredores = []
        self.traps = []; self.respawn_queue = []
        self.moves = 0; self.captured = 0; self.score = 0
        self.game_time = 0.0
        if mode=="escapa":
            for _ in range(3):
                self.generar_cazador()
        else:
            for _ in range(3):
                self.generar_corredor()
        self.last_trap_time = -999.0
        self.energy = self.max_energy
        self.state = "juego"
        self.msg = ""; self.msg_t = 0.0

    def ejecutar(self):
        while True:
            dt = self.clock.tick(FPS)/1000.0
            self.manejar_eventos()
            if self.state == "juego":
                self.actualizar_tareas_de_fondo(dt)

            if hasattr(self, "msg_t") and getattr(self, "msg_t", 0) > 0:
                self.msg_t -= dt
                if self.msg_t <= 0:
                    self.msg = ""
                    self.msg_t = 0

            if self.state == "fin_partida" and self.final_msg_timer > 0:
                self.final_msg_timer -= dt
                if self.final_msg_timer <= 0:
                    self.finalizar_y_guardar(final=True)
                    self.state = "menu"
                    self.final_state = None

            self.screen.fill(FONDO)
            if self.state == "registro":
                self.dibujar_registro()
            elif self.state == "menu":
                self.dibujar_menu()
            elif self.state == "puntajes":
                self.dibujar_puntajes()
            elif self.state == "juego":
                if self.mapa:
                    self.dibujar_mapa()
                    self.dibujar_entidades()
                    self.dibujar_hud()
            elif self.state == "fin_partida":
                if self.mapa:
                    self.dibujar_mapa()
                    self.dibujar_entidades()
                    self.dibujar_hud()
                self.dibujar_pantalla_final()

            pygame.display.flip()

if __name__ == "__main__":
    Juego().ejecutar()
