import os
import time


import pyodbc
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
# from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from flashscore import Flashscore
from conexion_BBDD import Conexion_BBDD
from datetime import datetime
import scrap_statistics

DRIVER = "Chrome"

if DRIVER == "Chrome":
    chrome_driver_path = "D:\\Python\\SeleniumDriver\\chromedriver.exe"
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)
else:
    mozilla_driver_path = "D:\\Python\\SeleniumDriver\\geckodriver.exe"
    service = Service(mozilla_driver_path)
    driver = webdriver.Firefox(service=service)

years = [""]
for year in years:

    # ['alemania'-'bundesliga', 'alemania'-'2-bundesliga', 'paises-bajos'-'eredivisie','espana-laliga',
    # 'espana,laliga-smartbank','inglaterra-premier-league', 'inglaterra-championship' ,'italia-serie-a',
    # 'francia-ligue-1', 'belgica-jupiler-pro-league'],

    flashscore = Flashscore()
    conexion = Conexion_BBDD()
    conexion = conexion.conexion()
    cursor = conexion.cursor()

    modo = "normal"  # ("normal" o "calendario")
    tipo_scrap = "jornada"  # ("competition","ayer","calendario","jornada")
    country = "belgica"
    competition = "jupiler-pro-league"
    year = year
    stage_area = "StageArea.Matches"  # ("StageArea.Calendario" o "StageArea.Matches")
    start = datetime.now()

    if tipo_scrap == "competition":
        list_matches = flashscore.scrap_competition(driver, country, competition, year)
    elif tipo_scrap == "ayer":
        list_matches = flashscore.scrap_yesterday(driver)
    elif tipo_scrap == "calendario":
        list_matches = flashscore.scrap_today(driver)
    elif tipo_scrap == "jornada":
        list_matches = flashscore.scrap_last_jornada(driver, country, competition, year)

    # Probar un partido
    # list_matches = ["6FOrKt0F"]

    count = 1
    if modo == "normal":
        for match_id in list_matches:
            percentage = str(round((count / len(list_matches)) * 100, 2)) + ' %]'
            print('[' + percentage + '\n')
            try:
                url = "https://www.flashscore.es/partido/" + match_id + "/#/resumen-del-partido/resumen-del-partido"
                driver.get(url)
                driver.implicitly_wait(2)
                try:
                    tab_group = driver.find_element(By.CLASS_NAME, "tabs__detail--nav")
                    tabs = [tab.text for tab in tab_group.find_elements(By.CLASS_NAME, "tabs__tab")]
                    score = driver.find_elements(By.CLASS_NAME, "section__title")
                    # Tiene Estadisticas completas ó Estadisticas en el Resumen
                    if "ESTADÍSTICAS" in tabs:
                        scrap_statistics.all_statistics(driver, match_id, year, conexion, cursor, stage_area)
                    else:
                        scrap_statistics.only_resume(driver, match_id, year, conexion, cursor, stage_area)
                except NoSuchElementException:
                    # No tiene estadisticas
                    try:
                        anulado = driver.find_element(By.CLASS_NAME, "detailScore__status").text
                        if anulado == "APLAZADO" or anulado == "ANULADO":
                            scrap_statistics.incident_match(driver, match_id, year, conexion, cursor, stage_area)
                        else:
                            scrap_statistics.only_score(driver, match_id, year, conexion, cursor, stage_area)
                    except NoSuchElementException:
                        pass
            except Exception as e:
                flashscore.save_log_error(country, competition, year, match_id, e)
            count += 1
            if tipo_scrap == "jornada":
                if count > 25:
                    break
    else:
        for match_id in list_matches:
            percentage = str(round((count / len(list_matches)) * 100, 2)) + ' %]'
            print('[' + percentage + '\n')
            try:
                url = "https://www.flashscore.es/partido/" + match_id + "/#/resumen-del-partido/resumen-del-partido"
                driver.get(url)
                driver.implicitly_wait(2)
                scrap_statistics.calendario(driver, match_id, year, conexion, cursor, stage_area)
            except Exception as e:
                flashscore.save_log_error(country, competition, year, match_id, e)
            count += 1
    runtime = str(datetime.now() - start)
    print('[ ' + country.upper() + ' ' + competition.upper() + ' ' + str(year) + ' FINISHED IN: ' + runtime + ']')
    driver.quit()

