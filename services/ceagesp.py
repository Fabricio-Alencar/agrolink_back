import json
import time
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoAlertPresentException
from webdriver_manager.chrome import ChromeDriverManager

def retroceder_para_dia_valido(data_atual):
    """
    Funcao auxiliar para voltar a data para o dia de cotacao anterior valido.
    Regra: Se e Sexta(4)->Volta pra Quarta(2). Se e Qua(2)->Volta pra Seg(0).
    Qualquer outro dia, retrocede 1 dia por garantia.
    """
    if data_atual.weekday() == 4: # Sexta -> Volta para Quarta
        return data_atual - timedelta(days=2)
    elif data_atual.weekday() == 2: # Quarta -> Volta para Segunda
        return data_atual - timedelta(days=2)
    elif data_atual.weekday() == 0: # Segunda -> Volta para a Sexta da semana anterior
        return data_atual - timedelta(days=3)
    else:
        return data_atual - timedelta(days=1)

def obter_cotacao_ceagesp(nome_produto, categoria_produto):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Iniciando busca automatica para: {nome_produto} ({categoria_produto})")
   
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("start-maximized")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Inicializando o Chrome via WebdriverManager...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    resultados = []

    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Robo acessando a pagina da CEAGESP...")
        driver.get("https://ceagesp.gov.br/cotacoes/")
       
        # --- TRATAMENTO DO POP-UP NATIVO DE LOGIN DO PROXY ---
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Verificando se ha pop-up de autenticacao do proxy...")
        time.sleep(2) # Pequena pausa para garantir a abertura do prompt nativo
        try:
            # Alterna o foco para o alerta do sistema operacional
            alerta_proxy = driver.switch_to.alert
            # Se a sua rede exigir usuário/senha preenchidos, descomente as linhas abaixo:
            # alerta_proxy.send_keys("seu_usuario" + "\t" + "sua_senha")
           
            alerta_proxy.accept() # Simula o clique direto no botao azul "Fazer login"
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Pop-up de login do proxy aceito com sucesso.")
            time.sleep(1)
        except NoAlertPresentException:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Nenhum pop-up de proxy nativo travando a tela.")
        # -----------------------------------------------------

        # COOKIES
        try:
            cookie = WebDriverWait(driver, 3).until(EC.element_to_be_clickable((By.ID, "wt-cli-accept-all-btn")))
            cookie.click()
        except:
            pass

        # DATA INICIAL BASEADA NO SITE
        campo_data = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "cot_data")))
        data_site_texto = campo_data.get_attribute("value")
       
        if data_site_texto:
            data_alvo = datetime.strptime(data_site_texto, "%d/%m/%Y")
        else:
            data_alvo = datetime.now()

        # Garante iniciar em uma Seg, Qua ou Sex
        while data_alvo.weekday() not in [0, 2, 4]:
            data_alvo -= timedelta(days=1)

        # Loop de tentativas controladas internamente por data
        for tentativa in range(3):
            data_formatada = data_alvo.strftime("%d/%m/%Y")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Tentativa {tentativa + 1}: Testando data {data_formatada}...")

            try:
                # SELECAO DA CATEGORIA
                select_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "grupo")))
                Select(select_element).select_by_value(categoria_produto.upper())

                campo_data = driver.find_element(By.NAME, "cot_data")
                driver.execute_script("arguments[0].removeAttribute('readonly');", campo_data)
                campo_data.clear()
                campo_data.send_keys(data_formatada)

                # Clicar em Consultar
                botao = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Consultar')]")))
                botao.click()

                # ESPERA DA TABELA REDUZIDA
                tabela_elemento = WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located((By.XPATH, "//table[contains(., 'Produto') or contains(., 'PRODUTO')]"))
                )
               
                time.sleep(2)
                linhas = tabela_elemento.find_elements(By.TAG_NAME, "tr")
               
                if len(linhas) <= 2:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Tabela vazia para o dia {data_formatada}.")
                    data_alvo = retroceder_para_dia_valido(data_alvo)
                    driver.refresh()
                    continue

            except TimeoutException:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] Tempo limite esgotado para o dia {data_formatada} (Dados indisponiveis).")
                data_alvo = retroceder_para_dia_valido(data_alvo)
                driver.get("https://ceagesp.gov.br/cotacoes/")
                continue
           
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Dados encontrados com sucesso para o dia {data_formatada}! Processando...")
           
            for linha in linhas:
                colunas = linha.find_elements(By.TAG_NAME, "td")
                if len(colunas) >= 7:
                    produto_site = colunas[0].text.strip().upper()

                    if nome_produto.upper() in produto_site:
                        classificacao = colunas[1].text.strip()
                        if not classificacao or classificacao == "-":
                            classificacao = "Única"

                        preco_texto = colunas[4].text.strip()

                        try:
                            preco = float(preco_texto.replace(".", "").replace(",", "."))
                            label = f"{produto_site.title()} - {classificacao}" if classificacao != "Única" else produto_site.title()

                            resultados.append({
                                "classificacao": label,
                                "preco": preco,
                                "data": data_formatada
                            })
                            print(f"[{datetime.now().strftime('%H:%M:%S')}] Encontrado: {label} -> R$ {preco}")
                        except:
                            pass
           
            if resultados:
                break

    except Exception as erro:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] ERRO INESPERADO: {erro}")
    finally:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Fechando o navegador...")
        driver.quit()

    return resultados


