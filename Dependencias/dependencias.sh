#!/bin/bash

echo Atualizando repositórios
if ! apt-get update
then 
	echo "Não foi possível atualizar os repositorios!"
	exit 1

fi
echo "atualização feita com sucesso!!"

echo "Instalando Dependencias"

if ! apt-get install python3
then 
	echo "Não foi possível instalar python3"
	exit1
fi

if ! apt-get install python3-pip
then 
	echo "Não foi possivel instalar pip"
	exit1

fi

python3 -m pip install -U pygame --user
 

echo "Todas dependencias baixadas com sucesso!!" 
