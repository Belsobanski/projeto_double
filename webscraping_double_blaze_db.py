# Importação de bibliotecas necessárias
import logging  # Para registrar logs de eventos
import mysql.connector  # Para conexão com banco de dados MySQL
import time  # Para pausar a execução entre as ações
from selenium import webdriver  # Para controlar o navegador
from selenium.webdriver.common.by import By  # Para localizar elementos na página
from selenium.webdriver.chrome.service import Service  # Para configurar o serviço do ChromeDriver
from selenium.webdriver.chrome.options import Options  # Para definir opções do navegador
from selenium.webdriver.support.ui import WebDriverWait  # Para aguardar elementos na página
from selenium.webdriver.support import expected_conditions as EC  # Para condições específicas ao aguardar elementos
from selenium.common.exceptions import TimeoutException, WebDriverException  # Para tratar exceções do Selenium

# Configuração do logging para registrar eventos com data, nível e mensagem
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Dicionário para mapear números retornados pelo site às respectivas cores
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

# Configuração do Selenium para controle do navegador em modo headless (sem interface gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")  # Executa sem abrir a janela do navegador
chrome_options.add_argument("--disable-gpu")  # Desabilita uso da GPU
chrome_options.add_argument("--no-sandbox")  # Necessário para contêineres
service = Service(executable_path="C:/chromedriver-win64/chromedriver.exe")
driver = webdriver.Chrome(service=service, options=chrome_options)

# Configuração de conexão com banco de dados MySQL
db_config = {
    'database': 'resultados_db',
    'user': 'mysql',
    'password': 'mysql',
    'host': 'localhost',
    'port': 3306
}

# Função para criar a tabela no banco de dados
def criar_tabela():
    try:
        # Conexão com o banco de dados
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        # Remoção e criação da tabela 'resultados'
        cursor.execute("DROP TABLE IF EXISTS resultados;")
        cursor.execute("""
            CREATE TABLE resultados (
                id INT AUTO_INCREMENT PRIMARY KEY,
                Cor VARCHAR(20),
                Numero VARCHAR(1000) DEFAULT NULL,
                Data_captura DATETIME DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        cursor.close()
        conn.close()
        logging.info("Tabela 'resultados' criada com sucesso.")
    except mysql.connector.Error as e:
        logging.error(f"Erro ao criar/verificar a tabela: {e}")

# Função para salvar os dados capturados no banco de dados
def salvar_no_banco(dados):
    try:
        conn = mysql.connector.connect(**db_config)
        sql = "INSERT INTO resultados (Cor, Numero) VALUES (%s, %s)"
        cursor = conn.cursor()
        cursor.executemany(sql, dados)  # Inserção em lote
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as e:
        logging.error(f"Erro ao salvar no banco de dados: {e}")

# Função para analisar o histórico de resultados no banco
def analisar_historico_para_branco():
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT Cor, Numero FROM resultados ORDER BY id DESC")
        historico = cursor.fetchall()

        # Identifica quais números antecedem o Branco
        numeros_antecederam_branco = {}
        for i in range(1, len(historico)):
            cor_atual, numero_atual = historico[i]
            cor_anterior, numero_anterior = historico[i - 1]
            if cor_atual == "Branco":
                if numero_anterior not in numeros_antecederam_branco:
                    numeros_antecederam_branco[numero_anterior] = 1
                else:
                    numeros_antecederam_branco[numero_anterior] += 1

        # Seleciona os 3 números mais frequentes antes do Branco
        top_3_numeros = sorted(numeros_antecederam_branco.items(), key=lambda x: x[1], reverse=True)[:3]
        logging.info("Top 3 números que mais antecederam o Branco:")
        for numero, freq in top_3_numeros:
            logging.info(f"Número {numero}: {freq} vezes")

        cursor.close()
        conn.close()
        return [numero for numero, freq in top_3_numeros]
    except mysql.connector.Error as e:
        logging.error(f"Erro ao analisar o histórico: {e}")
        return []

# Função para emitir alertas se o número atual estiver entre os top 3 que antecedem o Branco
def emitir_alerta_para_top_3(numero_atual, top_3_numeros):
    if numero_atual in top_3_numeros:
        logging.warning(f"ALERTA: O número {numero_atual} está entre os top 3 que mais antecedem o Branco!")

# Função para coletar resultados históricos do site com tentativas de reconexão
def coletar_historico(driver, total_resultados, tentativas=3):
    resultados = []
    pagina_atual = 1

    while len(resultados) < total_resultados:
        try:
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
        except TimeoutException:
            tentativas -= 1
            if tentativas > 0:
                logging.warning(f"Timeout ao acessar a página. Tentando novamente ({tentativas} tentativas restantes)...")
                time.sleep(5)
            else:
                logging.error("Falha ao coletar dados após várias tentativas.")
                break

    return resultados[::-1]  # Retorna resultados na ordem cronológica

# Função principal de execução do script
try:
    logging.info("Iniciando a captura de dados...")
    criar_tabela()  # Cria a tabela no banco

    historico = coletar_historico(driver, 363)  # Coleta histórico inicial
    salvar_no_banco(historico)  # Salva no banco de dados
    logging.info("Histórico de resultados salvos no banco de dados com sucesso.")

    top_3_numeros = analisar_historico_para_branco()  # Analisa histórico para determinar os top 3

    while True:
        try:
            # Coleta o último resultado
            driver.get("https://www.tipminer.com/br/historico/blaze/double")
            wait = WebDriverWait(driver, 10)
            elementos = wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, "cell__result")))

            ultimo_elemento = elementos[0]
            numero_atual = ultimo_elemento.text.strip()
            cor_atual = numero_para_cor.get(numero_atual, "Desconhecido")

            logging.info(f"RESULTADO ATUAL: {cor_atual}, {numero_atual}")
            salvar_no_banco([(cor_atual, numero_atual)])  # Salva o resultado atual no banco

            # Atualiza a análise e emite alertas se necessário
            top_3_numeros = analisar_historico_para_branco()
            emitir_alerta_para_top_3(numero_atual, top_3_numeros)

            time.sleep(25)  # Aguarda antes de coletar novamente
        except (TimeoutException, WebDriverException) as e:
            logging.error(f"Erro durante a execução: {e}")
            time.sleep(10)

finally:
    logging.info("Encerrando o driver.")
    driver.quit()  # Fecha o navegador
