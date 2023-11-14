from bs4 import BeautifulSoup
import json

def update_html_for_release(version, release_notes):
    try:
        # Открываем HTML файл
        with open('HTML/index.html', 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()

        # Создаем объект BeautifulSoup
        soup = BeautifulSoup(html_content, 'lxml')

        # Находим все места для вставки данных
        server_blocks = soup.find_all('h2')
        mobile_blocks = soup.find_all('h2', text='Обновление мобильного приложения')

        print("Вывод сервер блока:",server_blocks)

        # Первый блок "Обновление сервера"
        for block in server_blocks:
            if 'Обновление сервера' in block.text:
                server_block = block.find_next('tbody')
                # Вставляем данные
                for note in release_notes[0]:
                    tr = soup.new_tag('tr')
                    td1 = soup.new_tag('td')
                    td1.string = '—'
                    td2 = soup.new_tag('td')
                    td2.string = note
                    tr.append(td1)
                    tr.append(td2)
                    server_block.append(tr)

        # Второй блок "Обновление мобильного приложения"
        for block in mobile_blocks:
            if 'Обновление мобильного приложения' in block.text:
                mobile_block = block.find_next('tbody')
                # Вставляем данные
                for note in release_notes[0]:
                    tr = soup.new_tag('tr')
                    td1 = soup.new_tag('td')
                    td1.string = '—'
                    td2 = soup.new_tag('td')
                    td2.string = note
                    tr.append(td1)
                    tr.append(td2)
                    mobile_block.append(tr)

        # Сохраняем обновленное содержимое в HTML файл
        with open('HTML/index.html', 'w', encoding='utf-8') as html_file:
            html_file.write(str(soup))
    except Exception as error_message:
        print(f"Произошла ошибка при обновлении HTML файла: {error_message}")