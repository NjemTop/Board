param($version_SB, $support_response_id)

### ТАБЛИЦА ДЛЯ ОТЧЕТА ОТПРАВКИ РАССЫЛКИ КЛИЕНТАМ
$TABLE_REPORT = New-Object system.Collections.ArrayList

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
#, "gleb.chechelnitskiy@boardmaps.ru", "dmitriy.chaban@boardmaps.ru", "tatiana.shindikova@boardmaps.ru", "maxim.sorokin@boardmaps.ru"

### ТОКЕН ДОСТУПА ДЛЯ API К HAPPYFOX
$ACCESS_TOKEN = "45357d176a5f4e25b740aebae58f189c:3b9e5c6cc6f34802ad5ae82bafdab3bd"

### БАЗОВЫЙ URL ДЛЯ API HAPPYFOX
$HF_ENDPOINT = "https://boardmaps.happyfox.com"

### КОДИРОВАНИЕ И СОЗДАНИЕ КОДА АВТОРИЗАЦИЙ HAPPYFOX
$EncodedACCESS_TOKEN = [System.Text.Encoding]::UTF8.GetBytes($ACCESS_TOKEN)
$AuthorizationInfo = [System.Convert]::ToBase64String($EncodedACCESS_TOKEN)

### ЗАГОЛОВОК АВТОРИЗАЦИИ HAPPYFOX
$HEADERS = @{}
$HEADERS.Add("Authorization", "Basic $AuthorizationInfo")

### НОМЕР ВЕРСИИ !!!!!!!!!!!
$NUMBER_VERSION = $version_SB

### ЗАДАДИМ ПУТЬ К HTML ФАЙЛУ РАССЫЛКИ
$templatePath = "$PSScriptRoot\HTML\testBM31.html"

### ТЕМА ТИКЕТА
$TICKET_SUBJECT = "Обновление BoardMaps $NUMBER_VERSION"

# Oleg = ID - 5
# Dima = ID - 4
# Gleb = ID - 6

### ID ПОЛЬЗОВАТЕЛЯ ОТПРАВЛЯЮЩЕГО ОТВЕТ !!!!!!!!!!!
$USER_ID = $support_response_id

### ID СТАТУСA ТИКЕТА ПРИ ОТВЕТЕ КЛИЕНТУ (Статус Awaiting reply (Client confirmation))
$STATUS_ID = "5"

### СОЗДАДИМ DUE DATE ДЛЯ ТИКЕТА
$DUE_DATE_REPLY = ((Get-Date).AddDays(7)).ToString('yyyy-MM-dd', [cultureinfo]::GetCultureInfo('en-US'))

### ФОРМИРУЕМ ДАННЫЕ ДЛЯ ОТПРАВКИ ПИСЬМА КЛИЕНТУ
$CLIENT_POST_PASS = ConvertTo-SecureString -String "X5k-WFw-7bn-Aq6" -AsPlainText -Force
$CLIENT_POST_CREDS = new-object Management.Automation.PSCredential -ArgumentList “support@boardmaps.ru”, $CLIENT_POST_PASS

### ФОРМИРУЕМ HTML ТЕКСТ ДЛЯ СОЗДАНИЯ ТИКЕТА
$HTML_BODY = (Get-Content -Path $templatePath -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")

### ЗАПРОСИМ ВЕСЬ СПИСОК ГРУПП ИЗ HAPPYFOX
$GET_JSON_RESPONSE_FULL_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_groups/" -Headers $HEADERS -ContentType "application/json"

### СВОДНЫЙ СБОР ИНФОРМАЦИИ КОМУ ОТПРАВЛЯЕТСЯ РАССЫЛКА
if ($GET_JSON_RESPONSE_FULL_GROUP) {
    foreach ($ID_GROUP in $GET_JSON_RESPONSE_FULL_GROUP.id){
        ### ИНФОРМАЦИЯ О КОНТАКТЕ
        $GET_JSON_RESPONSE_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_group/$($ID_GROUP)/" -Headers $HEADERS -ContentType "application/json"
        ### ПРОВЕРИМ СТАТУС КЛИЕНТА, ЕСЛИ SILVER ИЛИ BRONZE, ТО ОТПРАВИМ СТАНДАРТНУЮ РАССЫЛКУ
        if (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Silver1") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Bronze1")) {
            ### ОБНУЛИМ СПИСОК РАССЫЛКИ КЛИЕНТОВ
            $COPY_EMAIL = $null
            $MAIN_EMAIL = $null
            $MAIN_CONTACT = $null
            ### ПРОЙДЁМСЯ ПО СПИСКУ КОНТАКТОВ(КЛИЕНТОВ) В ГРУППЕ
            foreach ($ID_CONTACT in $GET_JSON_RESPONSE_GROUP.contacts.id){
                ### ВЫТЯНИМ ИНФОРМАЦИЮ О КЛИЕНТЕ
                $GET_JSON_RESPONSE_CLIENT = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/user/$($ID_CONTACT)/" -Headers $HEADERS -ContentType "application/json"
                ### НАЙДЁМ В ГРУППЕ КОНТАКТЫ, КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ
                if ($GET_JSON_RESPONSE_CLIENT.custom_fields.value -cmatch "Да") {
                    ### СОСТАВИМ СПИСОК ПО ОСНОВНЫМ КОНТАКТАМ
                    if ($GET_JSON_RESPONSE_CLIENT.custom_fields.value -cmatch "Основной контакт") {
                        $MAIN_CONTACT = $GET_JSON_RESPONSE_CLIENT.name
                        $MAIN_EMAIL = $GET_JSON_RESPONSE_CLIENT.email
                    }
                    ### СОСТАВИМ СПИСОК ПО КОПИИ
                    elseif ($GET_JSON_RESPONSE_CLIENT.custom_fields.value -cnotmatch "Основной контакт") {
                        $COPY_EMAIL_ADD = $GET_JSON_RESPONSE_CLIENT.email
                        if ($COPY_EMAIL) {
                            $COPY_EMAIL += ', '
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                        }
                        else {
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                        }
                    }
                    ### ЕСЛИ ИНФОРМАЦИЮ О КЛИЕНТЕ НЕ ПОЛУЧИЛОСЬ СОСТАВИТЬ, ЗАПИШЕМ В ТАБЛИЦУ
                    else {
                        $PS = New-Object PSObject
                        $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка формирования клиента на рассылку"
                        $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
                        $PS = $TABLE_REPORT.Add($PS)
                        Write-Host -ForegroundColor Red -Object "ERROR $($GET_JSON_RESPONSE_CLIENT.name)"
                    }
                }
            }
            ### ПРОВЕРИМ, ЧТО У КЛИЕНТА ЕСТЬ КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ
            if ($MAIN_CONTACT) {
                ### ПОПРОБУЕМ ОТПРАВИТЬ POST ЗАПРОС НА СОЗДАНИЕ ТИКЕТА
                try {
                    ### ФОРМИРУЕМ ТЕЛО НА СОЗДАНИЕ ТИКЕТА, КОТОРОЕ УХОДИТ С ЗАПРОСОМ
                    $BODY_CREATE = @{

                        name = "$MAIN_CONTACT";

                        email = "$MAIN_EMAIL";

                        cc = "$COPY_EMAIL";

                        category = 6;

                        priority = "4";

                        subject = "$TICKET_SUBJECT";

                        html = "$HTML_BODY"

                        }
                    ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                    $CREATE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_CREATE | ConvertTo-Json -Depth 5))
                    ### ОТПРАВЛЯЕМ ЗАПРОС НА СОЗДАНИЕ ТИКЕТА
                    $CREATE_TICKET_JSON_RESPONSE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/tickets/" -Headers $HEADERS -Body $CREATE_TICKET -ContentType "application/json"

                    ### ФОРМИРУЕМ HTML ТЕКСТ ДЛЯ ОТПРАВКИ ОТВЕТА РАССЫЛКИ КЛИЕНТУ
                    $HTML_BODY_REPLY = (Get-Content -Path $templatePath -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")
                    ### ПРОБУЕМ ОТПРАВИТЬ ОТВЕТ В ТИКЕТЕ (ОТПРАВЛЯЕМ ПИСЬМО КЛИЕНТУ О НОВОЙ ВЕРСИИ)
                    try {
                        ### ФОРМИРУЕМ ТЕЛО, КОТОРОЕ УХОДИТ С ЗАПРОСОМ
                        $BODY_REPLY = @{

                            html = "$HTML_BODY_REPLY";

                            cc = "$COPY_EMAIL";

                            staff = $USER_ID;

                            status = $STATUS_ID;

                            due_date = $DUE_DATE_REPLY;

                            update_customer = "false"

                            }
                        ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                        $BODY_REPLY = [System.Text.Encoding]::UTF8.GetBytes(($BODY_REPLY | ConvertTo-Json -Depth 5))
                        ### ОТПРАВЛЯЕМ ОТВЕТ В РАНЕЕ СОЗДАННОМ ТИКЕТЕ (ЧТОБЫ УШЛО СООБЩЕНИЕ КЛИЕНТУ)
                        $REPLY_TICKET_JSON_RESPONSE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/staff_update/" -Headers $HEADERS -Body $BODY_REPLY -ContentType "application/json"
                        try {
                            ### СФОРМИРУЕМ ФАЙЛ ОТПРАВКИ
                            $HTML = (Get-Content -Path $templatePath -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")
                            ### ПРОВЕРИМ, ЕСТЬ ЛИ КОПИЯ КОМУ ОТПРАВЛЯТЬ
                            if ($COPY_EMAIL) {
                                ### ПРЕОБРАЗУЕМ СТРОКУ В МАССИВ СТРОК
                                [string[]]$TO_COPY = $COPY_EMAIL.Split(',')
                                ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                                Get-ChildItem -Path "$PSScriptRoot\HTML\Images" | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Cc $TO_COPY -Subject $TICKET_SUBJECT -Body $HTML_BODY_REPLY -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                                -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure' -WarningAction SilentlyContinue
                                Write-Host -ForegroundColor Magenta -Object "Рассылка клиенту $($GET_JSON_RESPONSE_GROUP.name) отправлена.`nОсновной контакт: $MAIN_EMAIL`nКопия: $TO_COPY`n"
                            }
                            ### ЕСЛИ КОПИИ НЕТ, ПРОСТО ОТПРАВИМ РАССЫЛКУ НА ОСНОВНОЙ КОНТАКТ
                            else {
                                ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                                Get-ChildItem -Path "$PSScriptRoot\HTML\Images" | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Subject $TICKET_SUBJECT -Body ($HTML | Out-String) -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                                -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure' -WarningAction SilentlyContinue
                                Write-Host -ForegroundColor Magenta -Object "Рассылка клиенту $($GET_JSON_RESPONSE_GROUP.name) отправлена.`nОсновной контакт: $MAIN_EMAIL`nКопия - отсутствует`n"
                            }
                            
                            ### ДОБАВЛЯЕМ ДАННЫЕ В ТАБЛИЦУ
                            $PS = New-Object PSObject
                            $PS | Add-Member -Type NoteProperty "Операция" -Value "Рассылка клиенту отправлена"
                            $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                            $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                            }
                        catch {
                            $PS = New-Object PSObject
                            $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка отправки письма"
                            $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                            $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                            Write-Host -ForegroundColor Red -Object "ERROR REPLY $($CREATE_TICKET_JSON_RESPONSE.id)"
                            Write-Error -Category AuthenticationError -Message "Ошибка отправки сообщения клиенту"
                        }
                    }
                    ### ЕСЛИ ОШИБКА ОТВЕТА В РАНЕЕ СОЗДАННОМ ТИКЕТЕ, ЗАПИШЕМ В ТАБЛИЦУ
                    catch {
                        $PS = New-Object PSObject
                        $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка отправки письма"
                        $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                        $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                        Write-Host -ForegroundColor Red -Object "ERROR REPLY $($CREATE_TICKET_JSON_RESPONSE.id)"
                    }
                }
                ### ЕСЛИ ОШИБКА СОЗДАНИИ ТИКЕТА, ЗАПИШЕМ В ТАБЛИЦУ
                catch {
                    $PS = New-Object PSObject
                    $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка создания тикета"
                    $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.contact_groups.name)"
                    Write-Host -ForegroundColor Red -Object "ERROR CREATE $($GET_JSON_RESPONSE_CLIENT.contact_groups.name)"
                }
                ### ОТПИШИМСЯ ОТ СОЗДАННОГО ТИКЕТА
                finally {
                    $BODY_UNSUBSCRIBE = @{

                        staff_id = "$USER_ID";

                    }
                    ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                    $UNSUBSCRIBE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_UNSUBSCRIBE | ConvertTo-Json -Depth 5))
                    $GET_JSON_RESPONSE_UNSUBSCRIBE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/unsubscribe/" -Headers $HEADERS -Body $UNSUBSCRIBE_TICKET -ContentType "application/json"
                    $GET_JSON_RESPONSE_UNSUBSCRIBE.name
                    ### ФОРМИРУЕМ ТАБЛИЦУ С ОТЧЁТОМ
                    $PS = $TABLE_REPORT.Add($PS)
                }
            }
            ### ЕСЛИ НЕ НАШЁЛСЯ КОНТАКТ, КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ, ТО ЗАПИШЕМ ЭТО В ТАБЛИЦУ
            else {
                $PS = New-Object PSObject
                $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка поиска контакта на рассылку"
                $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.name)"
                $PS = $TABLE_REPORT.Add($PS)
                Write-Host -ForegroundColor Red -Object "ERROR нет контакта на рассылку $($GET_JSON_RESPONSE_CLIENT.name)"
            }
        }
        ### ПРОВЕРИМ КЛИЕНТА НА ГОЛД ИЛИ ПЛАТИНУМ
        elseif (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Platinum") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Gold")) {
            <# Action when this condition is true #>
        }
        elseif ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Not active") {
            <# Action when this condition is true #>
        }
        ### ЕСЛИ ОШИБКА ПРОВЕРКИ СТАТУС, ЗАПИШЕМ В ТАБЛИЦУ
        else {
            $PS = New-Object PSObject
            $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка проверки статуса клиента"
            $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
            $PS = $TABLE_REPORT.Add($PS)
            Write-Host -ForegroundColor Red -Object "Ошибка проверки статуса клиента $($GET_JSON_RESPONSE_GROUP.name)"
        }
    }
}
### ЕСЛИ ОШИБКА ПОЛУЧЕНИИ ИНФОРМАЦИИ О КЛИЕНТЕ, ЗАПИШЕМ В ТАБЛИЦУ
else {
    $PS = New-Object PSObject
    $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка составления списка клиента"
    $PS | Add-Member -Type NoteProperty "Компания" -Value "ID клиента: $ID_GROUP"
    Write-Host -ForegroundColor Red -Object "ERROR, ID клиента: $ID_GROUP"
}

### СФОРМИРУЕМ ТЕЛО ДЛЯ ПИСЬМА ЕСЛИ ТАБЛИЦА ЗАПОЛНЕНА
if($TABLE_REPORT) {
    $HTML_REPORT = ($TABLE_REPORT | ConvertTo-Html -Fragment) | Out-String
    $BODY_REPORT = @"
    $CSS_STYLE
    <h1 style="color: #5e9ca0;">Список отправленной рассылки клиентам</h1>
    $HTML_REPORT
"@
}
else {
    $BODY_REPORT = @"
    <h1 style="color: #5e9ca0;">Ошибка составления списка на отправку клиентов</h1>
    <h4><strong>Неудалось составить список</strong></h4>
"@
}

### ФОРМИРУЕМ ДАННЫЕ ДЛЯ ОТПРАВКИ ОТЧЁТА
$POST_PASS = ConvertTo-SecureString -String "rcjtcxvjzfsjglko" -AsPlainText -Force
$POST_CREDS = new-object Management.Automation.PSCredential -ArgumentList “sup-smtp@boardmaps.ru”, $POST_PASS

### ЕСЛИ ТЕЛО ПИСЬМА СФОРМИРОВАНО, ТО ОТПРАВИМ ПИСЬМО
if ($BODY_REPORT){
    ### ПОПРОБУЕМ ОТПРАВИТЬ РЕПОРТ ОТЧЁТА НА ПОЧТУ ОБ ОТПРАВЛЕННЫХ РАССЫЛКАХ КЛИЕНТАМ
    try {
        Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO -Subject "Информация об отправки рассылки Bronze и Silver клиентам (Версия: $NUMBER_VERSION)" -Body $BODY_REPORT -BodyAsHtml -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -WarningAction SilentlyContinue;
        Write-Host -ForegroundColor Green -Object "Сообщение с информацией о рассылке клиентов Bronze и Silver отправлена на почту"
    }
    catch {
        {Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"}
    }
}
else {
    Write-Host -ForegroundColor Red -Object "Ошибка. Не правильно сформированно тело отправки запроса"
}