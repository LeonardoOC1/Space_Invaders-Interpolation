import socket
import threading
import pickle
import random
import time

class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.connections = []
        self.game_state = {
            'players': {},
            'asteroids': [],
            'vencedor': None,
            'jogo_iniciado': False,
            'contagem_regressiva': -1
        }
        self.lock = threading.Lock()
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(('0.0.0.0', port))
        self.server.listen()
        print(f"[SERVER] Aguardando jogadores em {host}:{port}")

    def client_handler(self, conn, addr, player_id):
        print(f"[NOVA CONEXAO] {addr} conectou como Player {player_id}")
        with self.lock:
            self.game_state['players'][player_id] = {'x': 300, 'score': 0}
        conn.sendall(pickle.dumps({'id': player_id}))

        try:
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                comando = pickle.loads(data)
                with self.lock:
                    if comando['tipo'] == 'mover':
                        if player_id in self.game_state['players']:
                            self.game_state['players'][player_id]['x'] = comando['x']
        finally:
            with self.lock:
                if player_id in self.game_state['players']:
                    del self.game_state['players'][player_id]
            self.connections.remove(conn)
            conn.close()

    def gerar_asteroides(self):
        while True:
            with self.lock:
                if self.game_state['jogo_iniciado'] and self.game_state['vencedor'] is None:
                    x = random.randint(0, 600)
                    self.game_state['asteroids'].append({'x': x, 'y': 0})
            time.sleep(2.5)

    def atualizar_asteroides(self):
        while True:
            with self.lock:
                if not self.game_state['jogo_iniciado']:
                    continue
                novos = []
                for ast in self.game_state['asteroids']:
                    ast['y'] += 5
                    if len(self.game_state['asteroids']) < 10:
                        novos.append(ast)
                self.game_state['asteroids'] = novos
            time.sleep(0.1)

    def verificar_colisoes(self):
        while True:
            with self.lock:
                if not self.game_state['jogo_iniciado'] or self.game_state['vencedor'] is not None:
                    continue
                for player_id, jogador in self.game_state['players'].items():
                    nave_x = jogador['x']
                    nave_y = 550
                    for ast in self.game_state['asteroids']:
                        if (nave_x < ast['x'] < nave_x + 40) and (nave_y < ast['y'] < nave_y + 20):
                            ids = list(self.game_state['players'].keys())
                            perdedor = player_id
                            vencedor = [i for i in ids if i != perdedor]
                            if vencedor:
                                self.game_state['vencedor'] = vencedor[0]
                            else:
                                self.game_state['vencedor'] = perdedor
                            print(f"[COLISAO] Player {perdedor} perdeu. Player {self.game_state['vencedor']} venceu.")
                            break
            time.sleep(0.05)

    def enviar_estado(self):
        while True:
            with self.lock:
                if len(self.connections) >= 2 and not self.game_state['jogo_iniciado']:
                    if self.game_state['contagem_regressiva'] == -1:
                        print("[JOGO] Dois jogadores conectados. Iniciando contagem regressiva...")
                        self.game_state['contagem_regressiva'] = 3
                    elif self.game_state['contagem_regressiva'] > 0:
                        self.game_state['contagem_regressiva'] -= 1
                    elif self.game_state['contagem_regressiva'] == 0:
                        self.game_state['jogo_iniciado'] = True
                        self.game_state['contagem_regressiva'] = -2
                        print("[JOGO] Jogo iniciado!")

                data = pickle.dumps(self.game_state)
                for conn in self.connections:
                    try:
                        conn.sendall(data)
                    except:
                        pass
            time.sleep(1)

    def start(self):
        threading.Thread(target=self.gerar_asteroides, daemon=True).start()
        threading.Thread(target=self.atualizar_asteroides, daemon=True).start()
        threading.Thread(target=self.enviar_estado, daemon=True).start()
        threading.Thread(target=self.verificar_colisoes, daemon=True).start()

        player_id = 0
        while True:
            conn, addr = self.server.accept()
            self.connections.append(conn)
            threading.Thread(target=self.client_handler, args=(conn, addr, player_id), daemon=True).start()
            player_id += 1

if __name__ == '__main__':
    GameServer().start()
