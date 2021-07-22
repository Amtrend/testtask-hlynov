#!/usr/bin/env python
import xml.etree.cElementTree as ET
from os import path, mkdir
from sys import argv
import shutil
import csv
from datetime import datetime
from dateutil.parser import parse
from itertools import permutations
import re
import logging


script, path_to_file = argv

full_filename = path.basename(path_to_file)
dir_filename = path.dirname(path_to_file)
name_filename = path.splitext(full_filename)[0]
type_file = path.splitext(full_filename)[1]

try:
    mkdir(f"{path.join(dir_filename, 'log')}")
except FileExistsError:
    pass

logfile = path.join(dir_filename, 'log') + '/logs.txt'
log = logging.getLogger("logs")
log.setLevel(logging.INFO)
FH = logging.FileHandler(logfile)
basic_formatter = logging.Formatter('%(asctime)s : [%(levelname)s] : %(message)s', datefmt='%d-%b-%y %H:%M:%S')
FH.setFormatter(basic_formatter)
log.addHandler(FH)

log.info(f"Обрабатывается файл {full_filename}, расположенный в {dir_filename}")

with open(path_to_file, 'r') as file:
    if type_file == '.xml':
        input_file = file.read()

        try:
            encoding_matches = re.search(r'(?<=encoding=")[^"]+', input_file)
            encoding = encoding_matches[0]
            log.info(f"Для исходного файла выбрана кодировка {encoding}")
        except:
            encoding = 'utf-8'
            log.info("Для исходного файла выбрана кодировка по умолчанию (utf-8)")

        tree = ET.parse(path_to_file)
        xml_data = tree.getroot()

        all_rows = []
        count = 0
        for word in xml_data.iter('Плательщик'):
            count += 1
            row = []
            row.append(name_filename)
            try:
                date = xml_data.find('СлЧаст/ОбщСвСч/ИдФайл/ДатаФайл').text
                date_parse = parse(date)
                date_res = datetime.strftime(date_parse, '%m.%d.%Y')
                row.append(date_res)
            except:
                log.error(f"Cтрока номер {count} не имеет одного из ключевых реквизитов (даты)")

            l_score = word.find('ЛицСч').text
            if l_score != None:
               row.append(l_score)
            else:
                log.error(f"Cтрока номер {count} не имеет одного из ключевых реквизитов (лицевого счёта)")

            fio = word.find('ФИО').text
            row.append(fio)
            address = word.find('Адрес').text
            row.append(address)

            period = word.find('Период').text
            try:
                valid_period = datetime.strptime(period, '%m%Y')
                row.append(period)
            except:
                log.error(f"Не верный формат Период - {period}. Строка Плательщика с ЛицСч - {l_score}")

            summ = word.find('Сумма').text
            try:
                if len(summ.split('.')[1]) == 2:
                    row.append(summ)
            except:
                log.error(f"Не верный формат Сумма - {summ}. Строка Плательщика с ЛицСч - {l_score}")

            all_rows.append(row)

        not_unique_values = []
        all_lists = list(permutations(all_rows, 2))
        for ls in all_lists:
            if ls[0][2] == ls[1][2] and ls[0][5] == ls[1][5]:
                not_unique_values.extend(ls)

        not_unique_values = list(set([tuple(i) for i in not_unique_values]))
        unique_values = [some_list for some_list in all_rows if tuple(some_list) not in not_unique_values]

        count_res = -1
        for i in not_unique_values:
            count_res += 1
            del_res_l_score = all_rows[all_rows.index(list(not_unique_values[count_res]))][2]
            del_res_period = all_rows[all_rows.index(list(not_unique_values[count_res]))][5]
            log.error(f"Найдены записи с одинаковыми ЛицСч {del_res_l_score} и Периодом {del_res_period}. Данные записи не добавлены в исходный файл")

        with open(f"{dir_filename}/{name_filename}.csv", 'w', encoding=encoding, newline='') as res_file:
            csv_writer = csv.writer(res_file, delimiter=';')
            for res_row in unique_values:
                csv_writer.writerow(res_row)

        try:
            mkdir(f"{path.join(dir_filename, 'arh')}")
        except FileExistsError:
            pass
        arh_path = path.join(dir_filename, 'arh')
        file.close()
        arh_movie = shutil.move(path_to_file, arh_path)
        log.info(f"Файл {full_filename} обработан и перемещён в {arh_path}. В директории {dir_filename} создан итоговый файл {name_filename}.csv")

    else:
        file.close()
        try:
            mkdir(f"{path.join(dir_filename, 'bad')}")
        except FileExistsError:
            pass
        bad_path = path.join(dir_filename, 'bad')
        bad_movie = shutil.move(path_to_file, bad_path)
        log.error(f"Файл {full_filename} не будет обработан, т.к. формат файла не xml. Файл перемещён в {bad_path}")
