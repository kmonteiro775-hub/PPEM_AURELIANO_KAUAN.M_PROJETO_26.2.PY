import pygame
import random
import sys
import os
from collections import deque

pygame.init()

MAPA = [

    "#############################",
    "#P.........................F#",
    "#.###.#.#####.#########.#.#.#",
    "#...#.#.............#...#.#.#",
    "###.#.#############.#.###.#.#",
    "#...#.#...#.......#.#.#...#.#",
    "#.#.#.#.#.#.#####.#.#.#.###.#",
    "#.#.....#......F..#.........#",
    "#.###.#######.#######.#####.#",
    "#.#.....#...#...#.....#...#.#",
    "#.#.###.#.#.###.#.#####.#.#.#",
    "#.#...#.#.#...#...#...#.#.#.#",
    "#.#.#.#.#.#.#.##.##.#.#.#.#.#",
    "#F....#.....#.......#...#..S#",
    "#############################",
]



T = 40
QTD_MINAS = 6
VIDAS_INICIAIS = 3


QTD_CURA = 2             
QTD_NITRO = 2          
QTD_GELO = 2             
DURACAO_NITRO = 4000     
DURACAO_GELO = 4000      
DELAY_NITRO = 70         
DURACAO_MSG = 2200      
DELAY_ZUMBI_TROLL = 330  
MOEDAS_PARA_SAIDA = 50   
CHANCE_TROLL = 0.5       

LARGURA = len(MAPA[0]) * T
ALTURA = len(MAPA) * T + 40

tela = pygame.display.set_mode((LARGURA, ALTURA))
pygame.display.set_caption("labirinto")
relogio = pygame.time.Clock()
fonte = pygame.font.SysFont(None, 28)
fonte_grande = pygame.font.SysFont(None, 56)

PASTA_IMAGENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "imagens")


def carregar_imagem(nome, tamanho):
    caminho = os.path.join(PASTA_IMAGENS, nome)
    imagem = pygame.image.load(caminho).convert_alpha()
    return pygame.transform.smoothscale(imagem, (tamanho, tamanho))


imagem_jogador = carregar_imagem("jogador.png", T)
imagem_mina = carregar_imagem("mina.png", T)
imagem_zumbi = carregar_imagem("zumbi.png", T)
imagem_explosao = carregar_imagem("explosao.png", T + 20)
imagem_bolinha = carregar_imagem("bolinha.png", T // 2)
imagem_saida = carregar_imagem("saida.png", T)
imagem_coracao = carregar_imagem("coracao.png", 28)
imagem_coracao_vazio = carregar_imagem("coracao_vazio.png", 28)

paredes = set()
livres = []
inicio_jogador = None
inicio_zumbi = []
saida = None

for y, linha in enumerate(MAPA):
    for x, c in enumerate(linha):
        pos = (x, y)
        if c == "#":
            paredes.add(pos)
        else:
            livres.append(pos)
            if c == "P":
                inicio_jogador = pos
            elif c == "F":
                inicio_zumbi.append(pos)
            elif c == "S":
                saida = pos


def distancia(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


candidatos = [
    p for p in livres
    if p != saida and distancia(p, inicio_jogador) > 3 and p not in inicio_zumbi
]


def preparar():
    minas = {pos: False for pos in random.sample(candidatos, QTD_MINAS)}
    bolinhas = {p for p in livres if p != inicio_jogador and p != saida}

    
    sobrando = [p for p in candidatos if p not in minas]
    random.shuffle(sobrando)

    
    modo_troll = random.random() < CHANCE_TROLL
    troll = None
    if modo_troll:
        
        longe = [p for p in sobrando if distancia(p, inicio_jogador) > 10]
        troll = random.choice(longe)
        sobrando.remove(troll)

    itens = {}
    for tipo, qtd in (("cura", QTD_CURA), ("nitro", QTD_NITRO), ("gelo", QTD_GELO)):
        for _ in range(qtd):
            itens[sobrando.pop()] = tipo

    return minas, inicio_jogador, list(inicio_zumbi), VIDAS_INICIAIS, bolinhas, 0, itens, troll, modo_troll


def vizinhos(pos):
    x, y = pos
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        novo = (x + dx, y + dy)
        if novo not in paredes:
            yield novo


def proximo_passo(origem, destino):
    if origem == destino:
        return origem
    fila = deque([origem])
    veio_de = {origem: None}
    while fila:
        atual = fila.popleft()
        if atual == destino:
            break
        for v in vizinhos(atual):
            if v not in veio_de:
                veio_de[v] = atual
                fila.append(v)
    if destino not in veio_de:
        return origem
    atual = destino
    while veio_de[atual] != origem:
        atual = veio_de[atual]
    return atual



imagens_itens = {
    "cura": carregar_imagem("cura.png", T - 6),
    "nitro": carregar_imagem("nitro.png", T - 6),
    "gelo": carregar_imagem("gelo.png", T - 6),
}


minas, jogador, zumbi, vidas, bolinhas, pontos, itens, troll, modo_troll = preparar()
estado = "jogando"
explosao = None
ultimo_mov_jogador = 0
ultimo_mov_zumbi = 0
DELAY_JOGADOR = 150
DELAY_ZUMBI = 250
delay_zumbi = DELAY_ZUMBI   
nitro_ate = 0        
gelo_ate = 0         
troll_ativada = False
saida_liberada = False
msg_ate = 0          
msg_texto = ""
msg_sub = ""
msg_cor = (255, 160, 0)


while True:
    agora = pygame.time.get_ticks()

    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if evento.type == pygame.KEYDOWN and evento.key == pygame.K_r and estado != "jogando":
            minas, jogador, zumbi, vidas, bolinhas, pontos, itens, troll, modo_troll = preparar()
            estado = "jogando"
            explosao = None
            nitro_ate = 0
            gelo_ate = 0
            troll_ativada = False
            saida_liberada = False
            delay_zumbi = DELAY_ZUMBI
            msg_ate = 0

    if estado == "jogando":
        teclas = pygame.key.get_pressed()
        
        delay_jogador = DELAY_NITRO if agora < nitro_ate else DELAY_JOGADOR
        if agora - ultimo_mov_jogador > delay_jogador:
            dx = dy = 0
            if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
                dx = -1
            elif teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
                dx = 1
            elif teclas[pygame.K_UP] or teclas[pygame.K_w]:
                dy = -1
            elif teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
                dy = 1
            if dx != 0 or dy != 0:
                novo = (jogador[0] + dx, jogador[1] + dy)
                if novo not in paredes:
                    jogador = novo
                ultimo_mov_jogador = agora

        
        if agora - ultimo_mov_zumbi > delay_zumbi and agora >= gelo_ate:
            novos = []
            for i, z in enumerate(zumbi):
                prox = proximo_passo(z, jogador)
                ocupadas = set(novos) | set(zumbi[i + 1:])
                if prox in ocupadas and prox != jogador:
                    prox = z
                novos.append(prox)
            zumbi = novos
            ultimo_mov_zumbi = agora


        if jogador in minas and not minas[jogador]:
            minas[jogador] = True
            vidas -= 1
            explosao = (jogador, agora)

        if jogador in bolinhas:
            bolinhas.remove(jogador)
            pontos += 1

        
        if jogador in itens:
            tipo = itens[jogador]
            if tipo == "cura":
                if vidas < VIDAS_INICIAIS:      
                    vidas += 1
                    del itens[jogador]
            elif tipo == "nitro":
                nitro_ate = agora + DURACAO_NITRO
                del itens[jogador]
            elif tipo == "gelo":
                gelo_ate = agora + DURACAO_GELO
                del itens[jogador]

        
        if modo_troll and jogador == troll and not troll_ativada:
            troll_ativada = True
            minas.clear()
            delay_zumbi = DELAY_ZUMBI_TROLL
            msg_texto, msg_sub = "SAÍDA TROLL!", "As minas sumiram e os zumbis ficaram mais lentos!"
            msg_cor = (255, 160, 0)
            msg_ate = agora + DURACAO_MSG

        if jogador in zumbi:
            vidas -= 1
            jogador = inicio_jogador
            zumbi = list(inicio_zumbi)

        
        if modo_troll and not saida_liberada and troll_ativada and (pontos >= MOEDAS_PARA_SAIDA or not bolinhas):
            saida_liberada = True
            msg_texto, msg_sub = "A SAÍDA APARECEU!", "Corra até ela!"
            msg_cor = (60, 220, 90)
            msg_ate = agora + DURACAO_MSG

        if jogador == saida and (not modo_troll or saida_liberada):
            estado = "venceu"
        elif vidas <= 0:
            estado = "perdeu"


    tela.fill((15, 15, 25))

    for (x, y) in paredes:
        r = pygame.Rect(x * T, y * T, T, T)
        pygame.draw.rect(tela, (90, 5, 105), r)

    for (x, y) in bolinhas:
        tela.blit(imagem_bolinha, (x * T + T // 4, y * T + T // 4))

    
    if not modo_troll or saida_liberada:
        tela.blit(imagem_saida, (saida[0] * T, saida[1] * T))

    
    if modo_troll:
        tela.blit(imagem_saida, (troll[0] * T, troll[1] * T))
    if troll_ativada:
        
        r = pygame.Rect(troll[0] * T, troll[1] * T, T, T)
        pygame.draw.line(tela, (230, 60, 60), r.topleft, r.bottomright, 4)
        pygame.draw.line(tela, (230, 60, 60), r.topright, r.bottomleft, 4)

    for (x, y), tipo in itens.items():
        tela.blit(imagens_itens[tipo], (x * T + 3, y * T + 3))

    for (x, y), revelada in minas.items():
        if revelada:
            tela.blit(imagem_mina, (x * T, y * T))

    for (x, y) in zumbi:
        tela.blit(imagem_zumbi, (x * T, y * T))
        if agora < gelo_ate:
            # zumbi congelado fica com uma camada azul por cima
            gelo = pygame.Surface((T, T), pygame.SRCALPHA)
            gelo.fill((120, 200, 255, 110))
            tela.blit(gelo, (x * T, y * T))

    tela.blit(imagem_jogador, (jogador[0] * T, jogador[1] * T))

    if explosao is not None and agora - explosao[1] < 400:
        ex, ey = explosao[0]
        tela.blit(imagem_explosao, (ex * T - 10, ey * T - 10))

    for i in range(VIDAS_INICIAIS):
        img = imagem_coracao if i < vidas else imagem_coracao_vazio
        tela.blit(img, (10 + i * 32, len(MAPA) * T + 6))
    texto = fonte.render("Pontos: " + str(pontos), True, (255, 255, 255))
    tela.blit(texto, (20 + VIDAS_INICIAIS * 32, len(MAPA) * T + 10))

    
    x_efeito = 260
    if agora < nitro_ate:
        t = fonte.render("NITRO %.1fs" % ((nitro_ate - agora) / 1000), True, (255, 220, 0))
        tela.blit(t, (x_efeito, len(MAPA) * T + 10))
        x_efeito += t.get_width() + 20
    if agora < gelo_ate:
        t = fonte.render("GELO %.1fs" % ((gelo_ate - agora) / 1000), True, (150, 220, 255))
        tela.blit(t, (x_efeito, len(MAPA) * T + 10))


    if troll_ativada and not saida_liberada:
        t = fonte.render("Moedas p/ saída: %d/%d" % (min(pontos, MOEDAS_PARA_SAIDA), MOEDAS_PARA_SAIDA), True, (255, 255, 255))
        tela.blit(t, (LARGURA - t.get_width() - 15, len(MAPA) * T + 10))

    if agora < msg_ate and estado == "jogando":
        t1 = fonte_grande.render(msg_texto, True, msg_cor)
        t2 = fonte.render(msg_sub, True, (255, 255, 255))
        fundo = pygame.Surface((LARGURA, 110), pygame.SRCALPHA)
        fundo.fill((0, 0, 0, 160))
        tela.blit(fundo, (0, ALTURA // 2 - 60))
        tela.blit(t1, (LARGURA // 2 - t1.get_width() // 2, ALTURA // 2 - 45))
        tela.blit(t2, (LARGURA // 2 - t2.get_width() // 2, ALTURA // 2 + 10))

    if estado != "jogando":
        msg = "VOCÊ VENCEU!" if estado == "venceu" else "GAME OVER"
        cor = (60, 220, 90) if estado == "venceu" else (230, 60, 60)
        t1 = fonte_grande.render(msg, True, cor)
        t2 = fonte.render("Pressione R para jogar de novo", True, (255, 255, 255))
        tela.blit(t1, (LARGURA // 2 - t1.get_width() // 2, ALTURA // 2 - 40))
        tela.blit(t2, (LARGURA // 2 - t2.get_width() // 2, ALTURA // 2 + 10))

    pygame.display.flip()
    relogio.tick(60)