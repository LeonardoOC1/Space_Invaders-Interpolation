#!/usr/bin/python3

import time
import queue
import pygame
import socket
import random
import threading
from pygame.locals import *
from random import randrange

g_list = []

host = socket.gethostname()
myip = socket.gethostbyname(host)

port = 16161          # porta para conectar ao servidor/ seu valor vai provavelmente mudar durante a execução do programa
#s_ip = '192.168.0.12' # ip do servidor
port_to_play = 12345

synchronized_queue  = queue.Queue(100)
colidiu_2           = False
colidiu_1           = False
vel_dificul         = 1
explodir_nave	    = False 
collided	    = False
pontos		    = 0 #VARIAVEL PONTUACAO
pontuacaototal	    = 0 #VARIAVEL DE CONTROLE DE NIVEIS
tick_musica	    = 0 #VARIAVEL CONTROLADORA DE MUSICA
spawn_de_asteroides = 30 #SPAWN DE ASTEROIDES DE ACORDO COM PONTUAÇÃO TOTAL
asteroides	    = [] #LISTA DE ASTEROIDES
background_filename = './Assets/galaxy2.png' 


def create_asteroide(vel_dificul):
	return {
		'tela': pygame.image.load('./Assets/asteroide1.png').convert_alpha(),
		'posicao': [randrange(1200), -64],#POSIÇÃO DE ONDE COMEÇA O ASTEROIDE
		'velocidade': randrange(vel_dificul,vel_dificul + 1)
	}

def nave_collided():
	nave_rect = get_rect(nave)
	for asteroide in asteroides:
		if nave_rect.colliderect(get_rect(asteroide)):
			return True

	return False

def mover_asteroides():
	for asteroide in asteroides:
		asteroide['posicao'][1] += 8

def get_rect(obj): 
	return Rect(obj['posicao'][0],obj['posicao'][1],obj['tela'].get_width(),obj['tela'].get_height())

def render_scene():
	global screen
	global score_font
	global asteroides
	global pontuacaototal
	global dificuldade_font

	screen.blit(background, (0, 0)) 
	textopontos = score_font.render('PONTUAÇÃO:'+str(pontos)+' ',1 ,(250,250,250))

	for asteroide in asteroides: #BLIT DOS ASTEROIDES NA TELA
		screen.blit(asteroide['tela'], asteroide['posicao'])

	if collided == False:
		screen.blit(textopontos, (0,0)) #TXT DO SCORE
	else:
		screen.blit(textopontos, (450, 300)) #TXT DO SCORE QUANDO ACABA O JOGO


	if (pontuacaototal<=9999): #CORES DOS LETREIROS DE DIFICULDADE
		dif1 = dificuldade_font.render('Dificuldade: Iniciante', 1, (255, 255, 255))
		screen.blit(dif1, (0, 22))
	elif (pontuacaototal<=20000):
		dif1 = dificuldade_font.render('Dificuldade: Amador', 1, (30,144,255))
		screen.blit(dif1, (0, 22))
	elif (pontuacaototal<=30000):
		dif1 = dificuldade_font.render('Dificuldade: Intermediário ', 1, (255,255,0))
		screen.blit(dif1, (0, 22))
	elif (pontuacaototal<=40000):
		dif1 = dificuldade_font.render('Dificuldade: Profissional', 1, (255,0,255))
		screen.blit(dif1, (0, 22))
	elif (pontuacaototal<=60000):
		dif1 = dificuldade_font.render('Dificuldade: Star Wars', 1, (255,0,0))
		screen.blit(dif1, (0, 22))

	nave['posicao'][0]  += nave['velocidade']['x'] 

	screen.blit(nave['tela'], nave['posicao'])

def raise_difficulty():
	global vel_dificul
	global pontuacaototal

	if(pontuacaototal >= 1000):
		vel_dificul = 1
	if (pontuacaototal >= 10000):
		vel_dificul = 2
	if (pontuacaototal >= 20000):
		vel_dificul = 3
	if (pontuacaototal >= 30000):
		vel_dificul = 4
	if (pontuacaototal >= 40000):
		vel_dificul = 5
	if (pontuacaototal >= 60000):
		vel_dificul = 6

def block_ship():
	global nave

	#POSIÇÃO PARA BARRAR A NAVE
	if(nave['posicao'][0] > 1150):
		nave['posicao'][0] = 1150
	if(nave['posicao'][0] < 0):
		nave['posicao'][0] = 0

def mov_ship():
	global nave

	if pygame.key.get_pressed()[K_a] : 
#		nave['posicao'][0] += -1.5
		nave['posicao'][0] += -7
	elif pygame.key.get_pressed()[K_d] :
#		nave['posicao'][0] +=  1.5
		nave['posicao'][0] +=  7

	block_ship()

#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# thread que recebe mensagens do servidor e coloca elas em uma fila bloqueantes
#  Uso de protocolo UDP
#  Seems like it'working
#  Obs .: Há a possibilidade da primeira mensagem não estar sendo recebida
def receive_messages():
	global host
	global g_list
	global port_to_play

	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM) # Socket para receber dados do jogo
	sock.bind((host,port_to_play))

	while True:
		data, addr = sock.recvfrom(4096)
		d_list = data.decode().split(";")

	# Mudar para inserir em uma fila bloqueante

		synchronized_queue.put({
			'asteroide' : int(d_list[0]),
			'nave1'     : int(d_list[1]),
			'nave2'     : int(d_list[2]),
			'colidiu_p1': d_list[3],
			'colidiu_p2': d_list[4],
		})

		print("I received : ",int(d_list[0]))

	sock.close()

# thread de envio de mensagens
#   Acrescentar campo colidiu na mensagem e o modo do servidor lidar com isso
#   Função deve ser invocada quando o player usa uma tecla para mover
#   Função deve ser chamada a cada milesimo de segundo
def send_message():
	sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
	data = str(nave['posicao'][0])
	print("I sent : ",data)
	sent = sock.sendto(data.encode(),(host,port))


#---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

pygame.init() 
pygame.font.init()

explosion_sound  = pygame.mixer.Sound('./Assets/boom.wav')
musica_fundo	 = pygame.mixer.Sound('./Assets/boom.wav')

pygame.display.set_caption('Space Invaders') 

font_name	 = pygame.font.get_default_font()
game_font	 = pygame.font.SysFont(font_name, 72) 
score_font	 = pygame.font.SysFont(font_name, 35) 
level_font	 = pygame.font.SysFont(font_name, 40)
dificuldade_font = pygame.font.SysFont(font_name, 30)
screen           = pygame.display.set_mode((1200, 700)) 
background       = pygame.image.load(background_filename).convert()

nave  = {
	'tela': pygame.image.load('./Assets/nave.png').convert_alpha(),
	'posicao': [1200/2, 700 - 60], 
	'velocidade': {
		'x': 0,
	}
}

nave2 =  {
	'tela': pygame.image.load('./Assets/nave.png').convert_alpha(),
	'posicao': [1200/2, 700 - 60], 
	'velocidade': {
		'x': 0,
	}
}

#----------------------------------------------------------------------------------------------------------------------------------------------
# Estabelece conexão : Envia ip e porta de comunicação para o servidor
#
#s = socket.socket() # Socket para estabelecer conexão com servidor
#
#s.connect((host, port))
#s.send(myip.encode())
#data = s.recv(1024)
#port = int(data.decode())
#s.close()
#
#----------------------------------------------------------------------------------------------------------------------------------------------
#
#while True:
#	try:
#		r_mesg = threading.Thread(target=receive_messages)
#		r_mesg.start()
#		break
#	except:
#		print("Error")
#		pass
#
#----------------------------------------------------------------------------------------------------------------------------------------------

while True:
	ini = time.process_time()	

	for event in pygame.event.get():
		if event.type == QUIT:
			exit()

	if not spawn_de_asteroides:
		spawn_de_asteroides = 30
		asteroides.append(create_asteroide(vel_dificul))
	else:
		spawn_de_asteroides -= 1

	render_scene()
	raise_difficulty()
	mover_asteroides()
	mov_ship()

	collided = nave_collided() 
	if collided :
		break
			
	pontuacaototal += 1 #PONTUAÇÃO SENDO ADICIONADA DENTRO DE UMA VARIAVEL, ANINHADA COM WHILE
	pontos         += 1

	pygame.display.update()
	end = time.process_time()

	print("DT : ",end - ini)

	idle = 0.0167 - (end - ini)
	print(idle)
	time.sleep(idle)

while True :
	for event in pygame.event.get():
		if event.type == QUIT:
			exit()
	render_scene()

	if not explodir_nave: #CONDIÇÃO DO SISTEMA SONORO CASO A NAVE EXPLODA
		musica_fundo.stop()
		explodir_nave = True 
		explosion_sound.play() 
		nave['posicao'][0] += nave['velocidade']['x']
		
		
		screen.blit(nave['tela'], nave['posicao'])
	else:
		text = game_font.render('VOCE PERDEU!!', 1, (255, 0, 0)) 			
		screen.blit(text, (450, 350)) #TXT DO GAME OVER APOS O JOGO

	pygame.display.update()
