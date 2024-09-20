import sys
import time
import numpy as np
import random
import re

# Funções Auxiliares

def read_file(path):
    # Função para ler o arquivo de entrada e criar a matriz de precedência e os custos
    with open(path, "r") as file:
        try:
            total_tarefas = int(file.readline().strip())
            matriz = np.zeros((total_tarefas, total_tarefas), dtype=int)
            custos = []

            for _ in range(total_tarefas):
                custo = int(file.readline().strip())
                custos.append(custo)

            for linha in file:
                linha = linha.strip()

                if not linha or linha == '-1,-1':
                    break

                par = re.split(r',\s*', linha)

                if len(par) != 2:
                    continue

                n1, n2 = map(int, par)

                if n1 == -1 or n2 == -1:
                    break

                matriz[n1 - 1][n2 - 1] = 1

            return matriz, custos, total_tarefas
        except Exception as e:
            print(f"Erro ao ler o arquivo: {e}")
            return None, None, None

def calcular_fo(solucao, custos):
    # Função para calcular a função objetivo (FO)
    maior_ciclo = 0
    for maquina in solucao:
        ciclo = sum(custos[tarefa] for tarefa in maquina)
        maior_ciclo = max(maior_ciclo, ciclo)
    return maior_ciclo

def distribuir_tarefas_aleatoriamente(numero_de_maquinas, numero_de_tarefas):
    # Função para distribuir tarefas aleatoriamente entre as máquinas
    tarefas_por_maquina = np.zeros(numero_de_maquinas, dtype=int)
    for i in range(0, numero_de_tarefas):
        tarefas_por_maquina[i % numero_de_maquinas] += 1
    np.random.shuffle(tarefas_por_maquina)
    return tarefas_por_maquina

def gerar_sequencia(numero_de_tarefas, matriz):
    # Função para gerar uma sequência de tarefas respeitando precedências
    sequencia = []
    matriz_auxiliar = np.copy(matriz)
    for _ in range(numero_de_tarefas):
        candidatos = [j for j in range(numero_de_tarefas) if np.sum(matriz_auxiliar[:, j]) == 0]
        random.shuffle(candidatos)
        escolhido = candidatos.pop(0)
        sequencia.append(escolhido)
        matriz_auxiliar[escolhido, :] = 0
        matriz_auxiliar[:, escolhido] = -1
    return sequencia

def imprime_resultados(solucao, fo, tempo_execucao, titulo, log_file):
    # Função para imprimir os resultados no formato solicitado e gravar no arquivo
    output = []
    output.append(f"______________________________________")
    output.append(f"{titulo}:")
    for i, maquina in enumerate(solucao):
        tarefas = ",".join(str(t + 1) for t in maquina)  # Adiciona +1 para exibir tarefas em base 1
        output.append(f"Máquina {i + 1}: {tarefas}")
    output.append(f"FO: {fo}")
    output.append(f"Tempo de execução: {tempo_execucao:.4f} segundos")
    output.append(f"-------------------------------")

    # Escreve no console e no arquivo de log
    for line in output:
        print(line)
        log_file.write(line + "\n")

def construir_precedencias(matriz):
    numero_de_tarefas = len(matriz)
    precedencias = {i: [] for i in range(numero_de_tarefas)}  # Dicionário vazio

    for i in range(numero_de_tarefas):
        for j in range(numero_de_tarefas):
            if matriz[i][j] == 1:  # Se i precede j
                precedencias[j].append(i)  # Adiciona i à lista de precedências de j

    return precedencias

def verifica_precedencia(solucao, precedencias):
    """
    Verifica se a solução atual respeita as precedências definidas.
    
    Parâmetros:
    - solucao: A solução atual, onde cada sublista representa as tarefas atribuídas a uma máquina.
    - precedencias: Dicionário que contém, para cada tarefa, uma lista de tarefas que a precedem.
    
    Retorna:
    - True se as precedências forem respeitadas, False caso contrário.
    """
    tarefas_concluidas = set()  # Conjunto para armazenar as tarefas que já foram concluídas

    # Itera sobre as máquinas e suas respectivas tarefas
    for maquina in solucao:
        for tarefa in maquina:
            # Verifica se todas as tarefas que precedem a tarefa atual foram concluídas
            if not all(precedencia in tarefas_concluidas for precedencia in precedencias[tarefa]):
                return False  # Retorna False se alguma precedência não for respeitada
            
            # Adiciona a tarefa atual ao conjunto de tarefas concluídas
            tarefas_concluidas.add(tarefa)

    return True  # Todas as precedências foram respeitadas

# Solução Inicial

def cria_solucao_inicial(numero_de_maquinas, custos, matriz):
    # Função para criar a solução inicial aleatória respeitando as precedências
    
    numero_de_tarefas = len(matriz)
    solucao = []
    
    # Distribui as tarefas aleatoriamente entre as máquinas
    numero_de_tarefas_por_maquina = distribuir_tarefas_aleatoriamente(numero_de_maquinas, numero_de_tarefas)
    
    # Gera uma sequência de tarefas respeitando as precedências
    sequencia_de_tarefas = gerar_sequencia(numero_de_tarefas, matriz)

    # Distribui as tarefas para cada máquina com base na sequência gerada
    for maquina in range(numero_de_maquinas):
        tarefas_por_maquina = []
        for _ in range(int(numero_de_tarefas_por_maquina[maquina])):
            if sequencia_de_tarefas:
                tarefas_por_maquina.append(sequencia_de_tarefas.pop(0))
        solucao.append(tarefas_por_maquina)

    fo_inicial = calcular_fo(solucao, custos)  # Calcula o FO da solução inicial
    return solucao, fo_inicial

# Heurísticas

def busca_local(solucao, custos, precedencias):
    """
    Aplica uma busca local para tentar melhorar a solução atual.
    Troca tarefas entre máquinas e verifica se a nova solução é melhor.
    """
    solucao_melhorada = [maquina[:] for maquina in solucao]  # Copia a solução atual
    fo_melhorada = calcular_fo(solucao_melhorada, custos)

    numero_de_maquinas = len(solucao)
    melhor_fo = fo_melhorada
    melhor_solucao = solucao_melhorada

    # Tenta trocar tarefas entre pares de máquinas para melhorar o FO
    for i in range(numero_de_maquinas):
        for j in range(i + 1, numero_de_maquinas):
            for t1 in solucao_melhorada[i]:
                for t2 in solucao_melhorada[j]:

                    # Cria uma nova solução a partir da troca de tarefas
                    nova_solucao = [maquina[:] for maquina in solucao_melhorada]
                    
                    # Troca as tarefas entre as máquinas
                    nova_solucao[i].remove(t1)
                    nova_solucao[j].remove(t2)
                    nova_solucao[i].append(t2)
                    nova_solucao[j].append(t1)

                    if not verifica_precedencia(nova_solucao, precedencias):
                        continue  # Se a nova solução violar precedências, ignora

                    nova_fo = calcular_fo(nova_solucao, custos)

                    if nova_fo < melhor_fo:
                        melhor_fo = nova_fo  # Atualiza o melhor FO encontrado
                        melhor_solucao = nova_solucao  # Atualiza a melhor solução

    return melhor_solucao, melhor_fo

def perturbacao(historico, solucao_atual, precedencias, max_tentativas=200):

    numero_de_maquinas = len(solucao_atual)

    for tentativa in range(max_tentativas):

        nova_solucao = [maquina[:] for maquina in solucao_atual]

        # 30% das tarefas são trocadas de máquina
        numero_de_trocas = max(1, ((len(nova_solucao)*3)//10))

        for _ in range(numero_de_trocas):

            # Escolhe duas máquinas aleatórias
            maquina1, maquina2 = random.sample(range(numero_de_maquinas), 2)

            if not nova_solucao[maquina1] or not nova_solucao[maquina2]:
                continue

            tarefa1 = random.choice(nova_solucao[maquina1])
            tarefa2 = random.choice(nova_solucao[maquina2])

            nova_solucao[maquina1].remove(tarefa1)
            nova_solucao[maquina2].remove(tarefa2)

            nova_solucao[maquina1].append(tarefa2)
            nova_solucao[maquina2].append(tarefa1)

            # Verifica se a nova solução respeita as precedências após a troca
            if not verifica_precedencia(nova_solucao, precedencias):
                # Se não respeitar, desfaz a troca
                nova_solucao[maquina1].remove(tarefa2)
                nova_solucao[maquina2].remove(tarefa1)
                nova_solucao[maquina1].append(tarefa1)
                nova_solucao[maquina2].append(tarefa2)
                continue  # Continua para a próxima troca

        if nova_solucao not in historico:
            return nova_solucao

    return solucao_atual

def aceitacao(S, S_perturbada, custos, historico):
    # Função de aceitação da nova solução
    if calcular_fo(S_perturbada, custos) < calcular_fo(S, custos):
        return S_perturbada
    if S_perturbada not in historico:
        return S_perturbada
    return S

def ils(numero_de_maquinas, custos, matriz, log_file):
    # Inicia o tempo de execução
    tempo_inicio = time.time()
    
    # Define o tempo máximo de execução para o ILS (Iterated Local Search)
    ILSmax = 60
    
    # Constrói as precedências a partir da matriz fornecida
    precedencias = construir_precedencias(matriz)

    # Gera a solução inicial e calcula o tempo para encontrá-la
    inicio_solucao_inicial = time.time()
    solucao_inicial, fo_inicial = cria_solucao_inicial(numero_de_maquinas, custos, matriz)
    tempo_solucao_inicial = time.time() - inicio_solucao_inicial
    
    # Inicializa as variáveis com a melhor solução encontrada (que inicialmente é a solução inicial)
    melhor_solucao = solucao_inicial
    melhor_fo = fo_inicial
    tempo_para_melhor_fo = tempo_solucao_inicial  # Tempo para encontrar o melhor FO (inicialmente o tempo da solução inicial)

    # Imprime os resultados da solução inicial
    imprime_resultados(solucao_inicial, fo_inicial, tempo_solucao_inicial, "Solução Inicial", log_file)

    # Realiza busca local a partir da solução inicial
    inicio_busca_local = time.time()
    solucao_atual, fo_busca_local = busca_local(solucao_inicial, custos, precedencias)
    tempo_busca_local = time.time() - inicio_busca_local

    # Atualiza a melhor solução se a busca local encontrar uma solução com FO menor
    if fo_busca_local < melhor_fo:
        melhor_solucao = solucao_atual
        melhor_fo = fo_busca_local
        tempo_para_melhor_fo = tempo_solucao_inicial + tempo_busca_local  # Atualiza o tempo para o melhor FO

    # Inicializa o histórico de soluções com a solução atual
    historico = [solucao_atual]
    tempo_execucao_total = tempo_solucao_inicial + tempo_busca_local  # Calcula o tempo total até o momento
    lista_tempo_melhor_fo = [tempo_para_melhor_fo]  # Lista com tempos em que o melhor FO foi encontrado

    # Histórico com FO e o tempo em que ele foi encontrado
    historico_fo_tempo = {fo_inicial: tempo_solucao_inicial}

    # Loop principal do algoritmo ILS
    while True:
        tempo_decorrido = time.time() - tempo_inicio  # Verifica o tempo decorrido

        # Verifica se o tempo máximo foi atingido
        if tempo_decorrido >= ILSmax:
            print("\nTempo limite atingido.")
            break

        # Aplica uma perturbação na solução atual para explorar outras áreas do espaço de busca
        solucao_perturbada = perturbacao(historico, solucao_atual, precedencias)

        # Realiza busca local a partir da solução perturbada
        solucao_perturbada, fo_perturbada_busca_local = busca_local(solucao_perturbada, custos, precedencias)

        # Aplica o critério de aceitação para definir a nova solução atual
        solucao_atual = aceitacao(solucao_atual, solucao_perturbada, custos, historico)

        # Adiciona a nova solução ao histórico
        historico.append(solucao_atual)

        # Atualiza o tempo de execução total
        tempo_execucao_total = time.time() - tempo_inicio
        historico_fo_tempo[fo_perturbada_busca_local] = tempo_execucao_total  # Registra o FO e o tempo de execução

        # Atualiza a melhor solução se a nova solução for melhor
        if fo_perturbada_busca_local < melhor_fo:
            melhor_solucao = solucao_atual
            melhor_fo = fo_perturbada_busca_local
            tempo_para_melhor_fo = tempo_execucao_total  # Atualiza o tempo para o melhor FO
            lista_tempo_melhor_fo.append(tempo_para_melhor_fo)  # Armazena o tempo em que a solução foi encontrada

    # Imprime os resultados da melhor solução encontrada durante a execução
    imprime_resultados(melhor_solucao, melhor_fo, tempo_execucao_total, "Melhor Solução Encontrada", log_file)

    # Calcula o tempo médio para encontrar o melhor FO
    tempo_medio_para_melhor_fo = sum(lista_tempo_melhor_fo) / len(lista_tempo_melhor_fo) if lista_tempo_melhor_fo else 0

    # Retorna a melhor solução, o melhor FO, o tempo para encontrar o melhor FO, o tempo total de execução, e o tempo médio


def executar_analise(melhores_fos, tempos_para_melhor_fo, tempos_totais, log_file):
    
    # Cálculo das métricas solicitadas
    melhor_fo_final = min(melhores_fos)
    fo_media = sum(melhores_fos) / len(melhores_fos)
    desvio = ((fo_media - melhor_fo_final) / melhor_fo_final) * 100
    tempo_melhor_fo = min(tempos_para_melhor_fo)  # Aqui queremos o menor tempo necessário para encontrar o melhor FO
    tempo_medio_execucoes = sum(tempos_totais) / len(tempos_totais)

    # Gerar o relatório
    log_file.write("\n*** Relatório de Execuções ***\n")
    log_file.write(f"Melhor FO: {melhor_fo_final}\n")
    log_file.write(f"FO Média: {fo_media:.2f}\n")
    log_file.write(f"Desvio: {desvio:.2f}%\n")
    log_file.write(f"T. Melhor (seg.): {tempo_melhor_fo:.4f} segundos\n")
    log_file.write(f"Tempo Médio (seg.): {tempo_medio_execucoes:.4f} segundos\n")
    
    print("\n*** Relatório de Execuções ***")
    print(f"Melhor FO: {melhor_fo_final}")
    print(f"FO Média: {fo_media:.2f}")
    print(f"Desvio: {desvio:.2f}%")
    print(f"T. Melhor (seg.): {tempo_melhor_fo:.4f} segundos")
    print(f"Tempo Médio (seg.): {tempo_medio_execucoes:.4f} segundos")


def main():

    path = "HAHN.IN2"
    log_file_path = "log_execucao.txt"
    
    with open(log_file_path, "w", encoding='utf-8') as log_file:
        
        matriz, custos, _ = read_file(path)
        instancias = [("Instância 6 Máquinas", 6), ("Instância 8 Máquinas", 8), ("Instância 10 Máquinas", 10)]

        for nome_instancia, maquinas in instancias:
            print(f"\nRodando {nome_instancia}:")
            
            melhores_fos = []
            tempos_para_melhor_fo = []
            tempos_totais = []

            for i in range(5):
                print(f"\nExecução {i + 1}:")
                melhor_solucao, melhor_fo, tempo_para_melhor_fo, tempo_total , tempo_medio_para_melhor_fo= ils(maquinas, custos, matriz, log_file)

                melhores_fos.append(melhor_fo)
                tempos_para_melhor_fo.append(tempo_para_melhor_fo)
                tempos_totais.append(tempo_total)
            
            executar_analise(melhores_fos, tempos_para_melhor_fo, tempos_totais, log_file)

if __name__ == "__main__":
    main()
