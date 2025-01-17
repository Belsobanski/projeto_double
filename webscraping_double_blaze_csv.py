import logging
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuração do logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Mapeamento completo de números para cores
numero_para_cor = {
    "": "Branco",
    "1": "Vermelho",
    "2": "Vermelho",
    "3": "Vermelho",
    "4": "Vermelho",
    "5": "Vermelho",
    "6": "Vermelho",
    "7": "Vermelho",
    "8": "Preto",
    "9": "Preto",
    "10": "Preto",
    "11": "Preto",
    "12": "Preto",
    "13": "Preto",
    "14": "Preto"
}

# Configuração do Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")  # Executa sem abrir o navegador
chrome_options.add_argument("--disable-gpu")  # Otimiza o headless
chrome_options.add_argument("--no-sandbox")  # Evita problemas em algumas plataformas
service = Service(executable_path="C:/chromedriver-win64/chromedriver.exe")  # Substitua pelo caminho do chromedriver

# Inicializa o driver
driver = webdriver.Chrome(service=service, options=chrome_options)

# Nome do arquivo CSV
nome_arquivo = "resultados_com_cores.csv"

# Apaga o conteúdo anterior do CSV ao iniciar
with open(nome_arquivo, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file)
    writer.writerow(["Cor", "Número"])  # Escreve o cabeçalho

# Função para salvar no CSV de forma inversa (últimos resultados no final)
def salvar_no_csv(nome_arquivo, dados):
    with open(nome_arquivo, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        for linha in reversed(dados):
            writer.writerow(linha)

def coletar_historico(driver, total_resultados):
    resultados = []
    pagina_atual = 1

    while len(resultados) < total_resultados:
        logging.info(f"Acessando página {pagina_atual}...")
        driver.get(f"https://www.tipminer.com/br/historico/blaze/double?page={pagina_atual}")
        wait = WebDriverWait(driver, 10)
        elementos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cell__result")))

        for elemento in elementos:
            numero = elemento.text.strip()
            cor = numero_para_cor.get(numero, "Desconhecido")
            resultados.append((cor, numero))
            if len(resultados) >= total_resultados:
                break
        
        logging.info(f"Capturados {len(resultados)} resultados até agora.")
        pagina_atual += 1
        time.sleep(2)

    return resultados

def analisar_historico_para_branco(nome_arquivo):
    with open(nome_arquivo, mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        next(reader)
        historico = list(reader)

    numeros_antecederam_branco = {}
    for i in range(1, len(historico)):
        cor_atual, numero_atual = historico[i]
        cor_anterior, numero_anterior = historico[i - 1]
        if cor_atual == "Branco":
            if numero_anterior not in numeros_antecederam_branco:
                numeros_antecederam_branco[numero_anterior] = 1
            else:
                numeros_antecederam_branco[numero_anterior] += 1

    top_3_numeros = sorted(numeros_antecederam_branco.items(), key=lambda x: x[1], reverse=True)[:3]
    logging.info("Top 3 números que mais antecederam o Branco:")
    for numero, freq in top_3_numeros:
        logging.info(f"Número {numero}: {freq} vezes")

    return top_3_numeros

try:
    logging.info("Iniciando a captura de dados...")

    historico = coletar_historico(driver, 484)
    salvar_no_csv(nome_arquivo, historico)
    logging.info("Histórico resultados salvos com sucesso.")

    ultimo_numero_capturado = historico[-1][1] if historico else None

    top_3_numeros = analisar_historico_para_branco(nome_arquivo)

    while True:
        driver.get("https://www.tipminer.com/br/historico/blaze/double")
        wait = WebDriverWait(driver, 10)
        elementos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cell__result")))

        ultimo_elemento = elementos[0]
        numero_atual = ultimo_elemento.text.strip()
        cor_atual = numero_para_cor.get(numero_atual, "Desconhecido")

        logging.info(f"RESULTADO ATUAL: {cor_atual}, {numero_atual}")
        salvar_no_csv(nome_arquivo, [(cor_atual, numero_atual)])

        ultimo_numero_capturado = numero_atual

        top_3_numeros = analisar_historico_para_branco(nome_arquivo)

        if numero_atual in [num for num, _ in top_3_numeros]:
            logging.info(f"Alerta: O número {numero_atual} pode indicar que o Branco está próximo!\n")

        time.sleep(25)

finally:
    logging.info("Encerrando o driver.")
    driver.quit()
