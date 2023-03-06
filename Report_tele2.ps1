# Установка модуля PSWriteWord
Install-Module -Name PSWriteWord -Scope CurrentUser

# Импортирование модуля PSWriteWord
Import-Module -Name PSWriteWord

### ТАБЛИЦА ДЛЯ ФОРМИРОВАНИЙ ОШИБОК (ЕСЛИ БУДУТ)
$TABLE_ERRORS = New-Object system.Collections.ArrayList

$TODAY_DAY = (Get-Date).Day
$TODAY_Month = Get-Date -Format MMMM
$TODAY_YEAR = (Get-Date).Year
# создаем документ
$DOCUMENT = New-WordDocument

# получение всех параграфов из документа
$paragraphs = $DOCUMENT.Paragraphs

$headers = $paragraphs | Where-Object {$_.Style.Name -match "^Heading"}

$headers.Count

### СОЗДАДИМ И НАСТРОИМ ОТЧЁТ С ТАБЛИЦЕЙ
try {
    # Создание документа
    $document = New-WordDocument

    # Добавление новой секции в документ
    $section = $document.AddSection()
 
    # Добавление заголовка в секцию
    $header = $section.Headers.Primary
    $headerParagraph1 = $header.AddParagraph("ОТЧЕТ ОБ ОКАЗАННЫХ УСЛУГАХ")
    $headerParagraph1.Style.FontSize = 14
    $headerParagraph1.Style.Bold = $true
    $headerParagraph1.Alignment = "Center"
    $headerParagraph2 = $header.AddParagraph("от $TODAY_DAY $TODAY_Month $TODAY_YEAR г. № 9")
    $headerParagraph2.Style.FontSize = 14
    $headerParagraph2.Style.Bold = $true
    $headerParagraph2.Alignment = "Center"
    $headerParagraph3 = $header.AddParagraph("по Договору № 03/04/20 от «10» апреля 2020г.")
    $headerParagraph3.Style.FontSize = 12
    $headerParagraph3.Style.Bold = $false
    $headerParagraph3.Alignment = "Center"
    $headerParagraph4 = $header.AddParagraph("за период с «___» ___ ___ г. по ««$TODAY_DAY» $TODAY_Month $TODAY_YEAR г.")
    $headerParagraph4.Style.FontSize = 12
    $headerParagraph4.Style.Bold = $false
    $headerParagraph4.Alignment = "Center"



    # Создаем таблицу
    $table = $DOCUMENT.CreateTable(1, 8)
    # Настраиваем ширину столбцов
    $table.Columns.Item(1).Width = 50
    $table.Columns.Item(2).Width = 120
    $table.Columns.Item(3).Width = 50
    $table.Columns.Item(4).Width = 120
    $table.Columns.Item(5).Width = 70
    $table.Columns.Item(6).Width = 70
    $table.Columns.Item(7).Width = 70
    $table.Columns.Item(8).Width = 70
    # Добавляем заголовки таблицы
    $table.Cell(1, 1).Range.Text = "№"
    $table.Cell(1, 2).Range.Text = "Наименование оказанных услуг"
    $table.Cell(1, 3).Range.Text = "Состав оказанных услуг"
    $table.Cell(1, 4).Range.Text = "Количество обращений"
    $table.Cell(1, 5).Range.Text = "Дата начала оказания услуг"
    $table.Cell(1, 6).Range.Text = "Дата окончания оказания услуг"
    $table.Cell(1, 7).Range.Text = "Нарушения сроков оказания услуг"
    $table.Cell(1, 8).Range.Text = "Результат услуг"
    # Настраиваем стиль таблицы
    $table.Style = "Table Grid"

    ### ЗАДАДИМ НАЧАЛО СТРОКИ ЗАПИСИ ДАННЫХ
    $x = 2
    $counter = 0
    $NUBER = 1
}
catch {
    $PS_ERRORS = New-Object PSObject
    $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Формирование документа Word"
    $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
    Write-Host -ForegroundColor Red -Object "Ошибка формирования документа Word"
}

### СТИЛЬ ДЛЯ ТАБЛИЦЫ ОТЧЕТА
$CSS_STYLE = @"
    <style>
    th
    {
        background-color: #4CAF50;
        color: white;
    },
    table, td
    {
        border: 1px solid black;
        background-color: #BEBEBE;
    },
    .colortext {
     color: red; 
   }           
    </style>
"@

### ПОЧТЫ ДЛЯ ОТПРАВКИ ОТЧЕТА
$TO = "oleg.eliseev@boardmaps.ru"
#"gleb.chechelnitskiy@boardmaps.ru", "dmitriy.chaban@boardmaps.ru", "tatiana.shindikova@boardmaps.ru", "maxim.sorokin@boardmaps.ru"

### СТИЛЬ ДЛЯ ТАБЛИЦЫ ОТЧЕТА ПО ОШИБКАМ
$CSS_STYLE_ERRORS = @"
    <style>
    th
    {
        background-color: #4CAF50;
        color: white;
    },
    table, td
    {
        border: 1px solid black;
        background-color: #BEBEBE;
    },
    .colortext {
     color: red; 
   }           
    </style>
"@

### ПОЧТЫ ДЛЯ ОТПРАВКИ ОТЧЕТА ПО ОШИБКАМ
$TO_ERRORS = "oleg.eliseev@boardmaps.ru"

# ТОКЕН ДОСТУПА ДЛЯ API
$ACCESS_TOKEN = "45357d176a5f4e25b740aebae58f189c:3b9e5c6cc6f34802ad5ae82bafdab3bd"

# БАЗОВЫЙ URL ДЛЯ API
$HF_ENDPOINT = "https://boardmaps.happyfox.com"

# КОДИРОВАНИЕ И СОЗДАНИЕ КОДА АВТОРИЗАЦИЙ
$EncodedACCESS_TOKEN = [System.Text.Encoding]::UTF8.GetBytes($ACCESS_TOKEN)
$AuthorizationInfo = [System.Convert]::ToBase64String($EncodedACCESS_TOKEN)

# ЗАГОЛОВОК АВТОРИЗАЦИИ
$HEADERS = @{}
$HEADERS.Add("Authorization", "Basic $AuthorizationInfo")

### ТЕЛО ЗАПРОСА ПО АКТИВНОСТИ ТИКЕТОВ
$BODY_STAFF_ACTIVITY = @{
    period_type = "srp";
}

### СФОРМИРУЕМ ИНФОРМАЦИЮ О ТИКЕТАХ И ДОБАВИМ В ТАБЛИЦУ WORD
try {
    $GET_JSON_REPORT_TELE2 = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/report/9/tabulardata/?size=50&page=1" -Headers $HEADERS -Body $BODY_STAFF_ACTIVITY -ContentType "application/json"
    ### ЕСЛИ СТРАНИЦ БЫЛО НЕСКОЛЬКО (БОЛЬШЕ 50 ТИКЕТОВ В ОТЧЁТНЫЙ ПЕРИОД), ТО ПРОЙДЁМСЯ ПО ВСЕМИ СТРАНИЦАМ
    for ($PAGE = 1; $PAGE -le $GET_JSON_REPORT_TELE2.page_count; $PAGE++) {
        $GET_JSON_REPORT_TELE2 = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/report/9/tabulardata/?size=50&page=$PAGE" -Headers $HEADERS -Body $BODY_STAFF_ACTIVITY -ContentType "application/json"
        try {
            ### ПРОЙДЁМСЯ ЦИКЛОМ ПО ВСЕМ ТИКЕТАМ ИЗ СПИСКА
            foreach ($TICKET_ID in $GET_JSON_REPORT_TELE2.Rows.id){
                $GET_JSON_RESPONSE_TICKET = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($TICKET_ID)" -Headers $HEADERS -ContentType "application/json"
                ### СОЗДАДИМ АРГУМЕНТЫ, ЧТОБЫ ИЗ ЧИСЛОВОГО ПРЕОБРАЗОВАТЬ В ФОРМАТ СТРОКИ (WORD НЕ ПРИНИМАЕТ ЗАПИСИ В ЧИСЛОВОМ ФОРМАТЕ)
                $TICKET_CREATED = $GET_JSON_RESPONSE_TICKET.created_at
                $TICKET_CLOSED = $GET_JSON_RESPONSE_TICKET.last_modified
                ### СОЗДАДИМ СТОЛБЕЦ В ТАБЛИЦЕ ДЛЯ ЗАПИСИ ТИКИТА
                $Table.Rows.Add()
                $Table.Cell($x,1).Range.Text = [string]$NUBER
                $Table.Cell($x,2).Range.Text = "Услуги по технической поддержке Программы для ЭВМ"
                $Table.Cell($x,3).Range.Text = $GET_JSON_RESPONSE_TICKET.subject
                $Table.Cell($x,4).Range.Text = "1"
                $Table.Cell($x,5).Range.Text = ([datetime]$TICKET_CREATED).ToString('dd.MM.yyyy')
                ### ПРОВЕРИМ СТАТУС ЗАЯВКИ 
                if ($GET_JSON_RESPONSE_TICKET.status.name -cmatch "Closed") {
                    $Table.Cell($x,6).Range.Text = ([datetime]$TICKET_CLOSED).ToString('dd.MM.yyyy')
                }
                else {
                    $Table.Cell($x,6).Range.Text = "-"
                }
                ### ПРОВЕРИМ ЕСТЬ ЛИ ПРОСРОЧКА В ТИКЕТЕ
                if ($GET_JSON_RESPONSE_TICKET.sla_breaches -eq 0) {
                    $Table.Cell($x,7).Range.Text = "Нет"
                }
                else {
                    $Table.Cell($x,7).Range.Text = "Да"
                }
                ### ПРОВЕРИМ БЫЛ ЛИ ТИКЕТ ЗАКРЫТ
                foreach ($RESOULT in $GET_JSON_RESPONSE_TICKET.custom_fields){
                    if ($RESOULT.id -eq 26 -and $RESOULT.value) {
                        $Table.Cell($x,8).Range.Text = "Выполнено"
                    }
                    elseif ($RESOULT.id -eq 26 -and $null -eq $RESOULT.value){
                        $Table.Cell($x,8).Range.Text = "В работе"
                    }
                }
                ### ДОБАВИМ К КОЛИЧЕСТВУ ТИКЕТА +1
                $NUBER = $NUBER + 1
                ### ИНКРЕМЕНТИРУЕМ СЧЁТЧИКИ
                $x = $x + 1
                $counter = $counter + 1
            }
        }
        catch {
            $PS_ERRORS = New-Object PSObject
            $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Получение информации о тикетах"
            $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
            Write-Host -ForegroundColor Red -Object "Ошибка получения информации о тикетах"
        }
    }
}
catch {
    $PS_ERRORS = New-Object PSObject
    $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Формирование документа Word"
    $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
    Write-Host -ForegroundColor Red -Object "Ошибка формирования документа Word"
}

# Сохраняем документ
$DOCUMENT.SaveAs("отчет.docx")


# ### АВТОМАТИЧЕСКИМ ФОРМИРОВАНИЕМ ПРИВЕДЁМ ТАБЛИЦУ В КРАСИВЫЙ ВИД
# $Table.AutoFormat(16)

# ### УВЕЛИЧИМ РАЗМЕР ВТОРОГО И ТРЕТЬЕГО СТОЛБЦА
# $table.Columns(2).Width = 85
# $table.Columns(3).Width = 90

# ### ПРОЙДЁМСЯ ПО ВСЕМ КОЛОНКАМ, ЧТОБЫ ВЫРОВНИТЬ ВЕСЬ ЦЕКСТ ПО ЦЕНТРУ И ПО ВЕРТИКАЛЕ, А ТАКЖЕ ЗАДАДИМ РАЗМЕР ШРИФТА 10
# try {
#     For ($i = 1; $i -le $Number_Of_Columns; $i++) {
#         $a = $document.Tables.Item(1).Columns.Item($i).Select()
#         $a.name
#         $Selection.Cells.VerticalAlignment = 1
#         $Table.cell(1,$i).range.Bold=1
#         $Selection.Font.Size = 10
#     }
# }
# catch {
#     $PS_ERRORS = New-Object PSObject
#     $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Форматирование документа Word"
#     $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#     Write-Host -ForegroundColor Red -Object "Ошибка форматирования документа Word"
# }

# ### СОЗДАДИМ НИЖНЮЮ ЧАСТЬ ДОКУМЕНТА (ПОДПИСИ)
# try {
#     ### ЗАКРОЕМ ТЕКЩУЮ ТАБЛИЦУ
#     $SELECTION.EndKey(6,0)

#     $SELECTION.TypeParagraph()
#     $SELECTION.TypeParagraph()
#     ### СОЗДАДИМ ВТОРУЮ, НЕВИДИМУЮ, ТАБЛИЦУ ДЛЯ ПОДПИСЕЙ
#     $range_2 = $paragraph.Range
#     $table_2 = $DOCUMENT.Tables.Add($range_2,1,2) 
#     $table_2 = $DOCUMENT.Tables.item(2)
#     ### ТЕКСТ ЖИРНЫЙ
#     $Selection.Font.Size = 12
#     $table_2.Cell($x,1).Range.Text = "ЗАКАЗЧИК:


#     __________/______________/
#     (подпись, фамилия и инициалы)"
#     $Table_2.Cell($x,2).Range.Text = "ИСПОЛНИТЕЛЬ:
#     Генеральный директор


#     ___________/Р.А. Василенко/
#     (подпись, фамилия и инициалы)"
# }
# catch {
#     $PS_ERRORS = New-Object PSObject
#     $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Создание нижней части документа Word"
#     $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#     Write-Host -ForegroundColor Red -Object "Ошибка создания нижней части документа Word"
# }

# ### СОХРАНЯЕМ ДОКУМЕНТ И ЗАКРЫВАЕМ ЕГО
# try {
#     ### ЗАДИДИМ ДАТУ СЕГОДНЯ
#     $TODAY = (Get-Date).ToString('dd.MM.yyyy')
#     ### ВРЕМЕННО СОХРАНЯЕМ ДОКУМЕНТ НА ЛОКАЛ МАШИНУ
#     $TEMP_WORD_FILE = "$env:LOCALAPPDATA\Отчёт клиента Теле2($TODAY).docx"
#     $DOCUMENT.SaveAs([ref]$TEMP_WORD_FILE)

#     ### ЗАКРЫВАЕМ ДОКУМЕНТ
#     $DOCUMENT.Close()

#     ### ЗАКРЫВАЕМ ПРИЛОЖЕНИЕ
#     $WORD.Quit()
# }
# catch {
#     $PS_ERRORS = New-Object PSObject
#     $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Сохранение документа Word"
#     $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#     Write-Host -ForegroundColor Red -Object "Ошибка сохранения документа Word"
# }

# ### СФОРМИРУЕМ ТЕЛО ДЛЯ ПИСЬМА ЕСЛИ ТАБЛИЦА ЗАПОЛНЕНА
# try {
#     $BODY = @"
#     $CSS_STYLE
#     <h4 style="color: #5e9ca0;">Во вложении отчёт клиента РЭЦ</h4>
# "@
# }
# catch {
#     $PS_ERRORS = New-Object PSObject
#     $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Формирование тела письма"
#     $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#     Write-Host -ForegroundColor Red -Object "Ошибка формирования тела письма"
# }

# ### ФОРМИРУЕМ ДАННЫЕ ДЛЯ ОТПРАВКИ ОТЧЁТА
# $POST_PASS = ConvertTo-SecureString -String "rcjtcxvjzfsjglko" -AsPlainText -Force
# $POST_CREDS = new-object Management.Automation.PSCredential -ArgumentList “sup-smtp@boardmaps.ru”, $POST_PASS

# try {
#     ### ЕСЛИ ТЕЛО ПИСЬМА СФОРМИРОВАНО, ТО ОТПРАВИМ ПИСЬМО
#     if ($BODY) {
#         Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO -Subject "Статистика по тикетам клиента Теле2" -Body $BODY -BodyAsHtml -Attachments $TEMP_WORD_FILE -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8);
#         Write-Host -ForegroundColor Green -Object "Список тикетов отправлен на почту(ы): $TO"
#         ### ПОПРОБУЕМ СОХРАНИТЬ WORD ФАЙЛ НА ШАРУ
#         try {
#             $SHARE_SAVE = "\\corp.boardmaps.com\data\TechSupport\Report HappyFox\Теле2"
#             Copy-Item -Path $TEMP_WORD_FILE -Destination $SHARE_SAVE
#         }
#         catch {
#             $PS_ERRORS = New-Object PSObject
#             $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Сохранение WORD файла на шару"
#             $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#         }
#         finally {
#             ### УДАЛИМ ВРЕМЕННЫЙ ФАЙЛ WORD ОТЧЁТА ПО ТИКЕТАМ
#             Remove-Item -Path $TEMP_WORD_FILE -Recurse -Force
#         }
#     }
#     else {
#         $PS_ERRORS = New-Object PSObject
#         $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Проверка формирования тела письма"
#         $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#         Write-Host -ForegroundColor Red -Object "Ошибка проверки формирования тела письма"
#     }
# }
# catch {
#     $PS_ERRORS = New-Object PSObject
#     $PS_ERRORS | Add-Member -Type NoteProperty "Действие" -Value "Отправка письма"
#     $PS_ERRORS = $TABLE_ERRORS.Add($PS_ERRORS)
#     Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"
# }

# ### ПРОВЕРИМ БЫЛА ЛИ ЗАПОЛНЕНА ТАБЛИЦА С ОШИБКАМИ
# if ($TABLE_ERRORS) {
#     try {
#         $HTML_ERRORS = ($TABLE_ERRORS | ConvertTo-Html -Fragment) | Out-String
#         $BODY_ERRORS = @"
#         $CSS_STYLE_ERRORS
#         <h1 style="color: #5e9ca0;">Ошибки составления списка отчёта клиента Теле2:</h1>
#         $HTML_ERRORS
# "@
#     }
#     catch {
#         Write-Host -ForegroundColor Red -Object "Ошибка формирования тела запроса"
#     }
#     ### ПОПРОБУЕМ ОТПРАВИМ СООБЩЕНИЕ С ОШИБКАМИ
#     try {
#         ### ПРОВЕРИМ ЗАПОЛНЕНО ЛИ ТЕЛО ОТПРАВИ ЗАПРОСА И ОТПРАВИМ ПИСЬМО НА ПОЧТУ
#         if ($BODY_ERRORS) {
#             Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO_ERRORS -Subject "Ошибки формирования отчёта клиента Теле2" -Body $BODY_ERRORS -BodyAsHtml -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8);
#             Write-Host -ForegroundColor Green -Object "Список ошибок отправлен на почту(ы): $TO_ERRORS"
#         }
#         else {
#             Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO_ERRORS -Subject "Ошибки формирования тела" -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8);
#             Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения формирования тела запроса"
#         }
#     }
#     catch {
#         Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения с ошибками"
#     }
# }
# else {
#     Write-Host -ForegroundColor Green -Object "Ошибок при составлении списка не было"
# }