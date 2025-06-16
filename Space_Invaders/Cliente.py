import pygame
import socket
import pickle
import sys
import time

class GameClient:
    def __init__(self, host='10.0.0.10', port=5555):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((host, port))
        data = self.client.recv(1024)
        resposta = pickle.loads(data)
        self.id = resposta['id']
        self.x = 300
        self.estado = {}

        self.interpolado = {}  # {player_id: {'x_atual': ..., 'x_destino': ..., 'ultimo_update': ...}}
        self.asteroides_interp = {}  # {index: {'y_atual': ..., 'y_destino': ..., 'x': ..., 'tempo': ...}}

    def enviar_movimento(self):
        comando = {'tipo': 'mover', 'x': self.x}
        self.client.sendall(pickle.dumps(comando))

    def receber_estado(self):
        data = self.client.recv(4096)
        novo_estado = pickle.loads(data)

        # Atualiza jogadores
        for pid, jogador in novo_estado['players'].items():
            pid = str(pid)
            if pid not in self.interpolado:
                self.interpolado[pid] = {
                    'x_atual': jogador['x'],
                    'x_destino': jogador['x'],
                    'ultimo_update': time.time()
                }
            else:
                self.interpolado[pid]['x_atual'] = self.interpolado[pid]['x_destino']
                self.interpolado[pid]['x_destino'] = jogador['x']
                self.interpolado[pid]['ultimo_update'] = time.time()

        # Atualiza asteroides
        novos_asts = novo_estado['asteroids']
        for i, ast in enumerate(novos_asts):
            if i not in self.asteroides_interp:
                self.asteroides_interp[i] = {
                    'y_atual': ast['y'],
                    'y_destino': ast['y'],
                    'x': ast['x'],
                    'tempo': time.time()
                }
            else:
                self.asteroides_interp[i]['y_atual'] = self.asteroides_interp[i]['y_destino']
                self.asteroides_interp[i]['y_destino'] = ast['y']
                self.asteroides_interp[i]['x'] = ast['x']
                self.asteroides_interp[i]['tempo'] = time.time()

        # Remove asteroides que saíram
        for i in list(self.asteroides_interp.keys()):
            if i >= len(novos_asts):
                del self.asteroides_interp[i]

        self.estado = novo_estado

    def executar(self):
        pygame.init()
        tela = pygame.display.set_mode((600, 600))
        pygame.display.set_caption(f"Player {self.id}")
        fonte = pygame.font.SysFont(None, 36)
        clock = pygame.time.Clock()

        rodando = True
        while rodando:
            tela.fill((0, 0, 0))
            for evento in pygame.event.get():
                if evento.type == pygame.QUIT:
                    rodando = False

            self.receber_estado()

            if str(self.id) in self.estado['players']:
                self.x = self.estado['players'][str(self.id)]['x']

            if not self.estado.get('jogo_iniciado', False):
                contagem = self.estado.get('contagem_regressiva', -1)
                if contagem == -1:
                    mensagem = "Aguardando outro jogador..."
                elif contagem >= 0:
                    mensagem = "GO!" if contagem == 0 else str(contagem)
                else:
                    mensagem = "Preparando jogo..."
                texto = fonte.render(mensagem, True, (255, 255, 0))
                tela.blit(texto, (250, 250))
                pygame.display.flip()
                clock.tick(1 if contagem >= 0 else 30)
                continue

            teclas = pygame.key.get_pressed()
            if teclas[pygame.K_LEFT]:
                self.x -= 10
            if teclas[pygame.K_RIGHT]:
                self.x += 10
            self.x = max(0, min(self.x, 560))

            self.enviar_movimento()

            agora = time.time()

            # Desenhar jogadores interpolados
            for pid, dados in self.interpolado.items():
                t = min((agora - dados['ultimo_update']) / 0.1, 1.0)
                x_interp = int(dados['x_atual'] * (1 - t) + dados['x_destino'] * t)
                cor = (0, 255, 0) if int(pid) == self.id else (0, 0, 255)
                pygame.draw.rect(tela, cor, (x_interp, 550, 40, 20))

            # Desenhar asteroides interpolados
            for i, ast in self.asteroides_interp.items():
                t = min((agora - ast['tempo']) / 0.1, 1.0)
                y_interp = int(ast['y_atual'] * (1 - t) + ast['y_destino'] * t)
                pygame.draw.rect(tela, (255, 0, 0), (ast['x'], y_interp, 20, 20))

            if self.estado.get('vencedor') is not None:
                msg = "Você venceu!" if int(self.estado['vencedor']) == self.id else "Você perdeu!"
                texto = fonte.render(msg, True, (255, 255, 255))
                tela.blit(texto, (220, 300))

            pygame.display.flip()
            clock.tick(30)

if __name__ == '__main__':
    host = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    GameClient().executar()
