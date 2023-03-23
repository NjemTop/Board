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

### ТАБЛИЦА ДЛЯ ОТЧЕТА С ОШИБКАМИ ОТПРАВКИ РАССЫЛКИ КЛИЕНТАМ
$ERROR_TABLE_REPORT = New-Object system.Collections.ArrayList

### СТИЛЬ ДЛЯ ТАБЛИЦЫ ОТЧЕТА С ОШИБКАМИ
$ERROR_CSS_STYLE = @"
    <style>
    th
    {
        background-color: #3366CC;
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

### ПОЧТЫ ДЛЯ ОТПРАВКИ ОТЧЕТА С ОШИБКАМИ
$ERROR_TO = "oleg.eliseev@boardmaps.ru"

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
$TEMPLATEPATH = "$PSScriptRoot\HTML\index.html"

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

### ФОРМИРУЕМ ДАННЫЕ ПОЧТЫ ДЛЯ ОТПРАВКИ ПИСЬМА КЛИЕНТУ
$CLIENT_POST_PASS = ConvertTo-SecureString -String "X5k-WFw-7bn-Aq6" -AsPlainText -Force
$CLIENT_POST_CREDS = new-object Management.Automation.PSCredential -ArgumentList “support@boardmaps.ru”, $CLIENT_POST_PASS

### ФОРМИРУЕМ HTML ТЕКСТ ДЛЯ СОЗДАНИЯ ТИКЕТА
$HTML_BODY = (Get-Content -Path $TEMPLATEPATH -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")

### ЗАПРОСИМ ВЕСЬ СПИСОК ГРУПП ИЗ HAPPYFOX
$GET_JSON_RESPONSE_FULL_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_groups/" -Headers $HEADERS -ContentType "application/json"

### СВОДНЫЙ СБОР ИНФОРМАЦИИ КОМУ ОТПРАВЛЯЕТСЯ РАССЫЛКА
if ($GET_JSON_RESPONSE_FULL_GROUP) {
    foreach ($ID_GROUP in $GET_JSON_RESPONSE_FULL_GROUP.id){
        ### ИНФОРМАЦИЯ О КОНТАКТЕ
        $GET_JSON_RESPONSE_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_group/$($ID_GROUP)/" -Headers $HEADERS -ContentType "application/json"
        ### ПРОВЕРИМ СТАТУС КЛИЕНТА И ОТПРАВИМ СТАНДАРТНУЮ РАССЫЛКУ
        if ($GET_JSON_RESPONSE_GROUP.tagged_domains -in @("Silver1", "Bronze1", "Platinum1", "Gold1")) {
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
                            $COPY_EMAIL += ','
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                        }
                        else {
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                        }
                    }
                    ### ЕСЛИ ИНФОРМАЦИЮ О КЛИЕНТЕ НЕ ПОЛУЧИЛОСЬ СОСТАВИТЬ, ЗАПИШЕМ В ТАБЛИЦУ
                    else {
                        $ERROR_PS = New-Object PSObject
                        $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Формирование клиента на рассылку"
                        $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
                        $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
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
                    $HTML_BODY_REPLY = (Get-Content -Path $TEMPLATEPATH -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")
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
                            $HTML = (Get-Content -Path $TEMPLATEPATH -Raw).Replace("NUMBER_VERSION", "$NUMBER_VERSION")
                            ### ПРОВЕРИМ, ЕСТЬ ЛИ КОПИЯ КОМУ ОТПРАВЛЯТЬ
                            if ($COPY_EMAIL) {
                                ### ПРЕОБРАЗУЕМ СТРОКУ В МАССИВ СТРОК
                                [string[]]$TO_COPY = $COPY_EMAIL.Split(',')
                                ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                                Get-ChildItem -Path "$PSScriptRoot\HTML\Images" | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Cc $TO_COPY -Subject $TICKET_SUBJECT -Body $HTML -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                                -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure' -WarningAction SilentlyContinue
                                Write-Output "$($GET_JSON_RESPONSE_GROUP.name)|$MAIN_EMAIL|$COPY_EMAIL"
                                ### ДОБАВЛЯЕМ ДАННЫЕ В ТАБЛИЦУ 
                                $PS = New-Object PSObject 
                                $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)" 
                                $PS | Add-Member -Type NoteProperty "Основной контакт" -Value "$MAIN_EMAIL" 
                                $PS | Add-Member -Type NoteProperty "Копия" -Value "$COPY_EMAIL".Replace(', ', ' | ') 
                                $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)" 
                                ### ФОРМИРУЕМ ТАБЛИЦУ С ОТЧЁТОМ 
                                $PS = $TABLE_REPORT.Add($PS)
                            }
                            ### ЕСЛИ КОПИИ НЕТ, ПРОСТО ОТПРАВИМ РАССЫЛКУ НА ОСНОВНОЙ КОНТАКТ
                            else {
                                ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                                Get-ChildItem -Path "$PSScriptRoot\HTML\Images" | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Subject $TICKET_SUBJECT -Body $HTML -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                                -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure' -WarningAction SilentlyContinue
                                # Write-Host -ForegroundColor Magenta -Object "Рассылка клиенту $($GET_JSON_RESPONSE_GROUP.name) отправлена.`nОсновной контакт: $MAIN_EMAIL`nКопия - отсутствует`n"
                                Write-Output "$($GET_JSON_RESPONSE_GROUP.name)|$MAIN_EMAIL"
                                ### ДОБАВЛЯЕМ ДАННЫЕ В ТАБЛИЦУ 
                                $PS = New-Object PSObject 
                                $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)" 
                                $PS | Add-Member -Type NoteProperty "Основной контакт" -Value "$MAIN_EMAIL" 
                                $PS | Add-Member -Type NoteProperty "Копия" -Value "Не было" 
                                $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)" 
                                ### ФОРМИРУЕМ ТАБЛИЦУ С ОТЧЁТОМ 
                                $PS = $TABLE_REPORT.Add($PS)
                            }
                        }
                        catch {
                            $ERROR_PS = New-Object PSObject
                            $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Отправка письма на почту"
                            $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                            $ERROR_PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                            $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
                            # Write-Error -Category AuthenticationError -Message "Ошибка отправки сообщения клиенту $($CREATE_TICKET_JSON_RESPONSE.id)"
                        }
                    }
                    ### ЕСЛИ ОШИБКА ОТВЕТА В РАНЕЕ СОЗДАННОМ ТИКЕТЕ, ЗАПИШЕМ В ТАБЛИЦУ
                    catch {
                        $ERROR_PS = New-Object PSObject
                        $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Отправка ответа в тикете"
                        $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                        $ERROR_PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                        $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
                    }
                }
                ### ЕСЛИ ОШИБКА СОЗДАНИИ ТИКЕТА, ЗАПИШЕМ В ТАБЛИЦУ
                catch {
                    $ERROR_PS = New-Object PSObject
                    $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Создание тикета"
                    $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.contact_groups.name)"
                    $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
                }
                ### ВЫПОЛНИМ ПОСЛЕДНЕЕ ДЕЙСТВИЕ ПОСЛЕ ОТПРАВКИ РАССЫЛКИ (ОТПИШЕМСЯ ОТ ТИКЕТА, А ТАКЖЕ ЗАКРОЕМ ЕГО)
                finally {
                    ### ОТПИШИМСЯ ОТ СОЗДАННОГО ТИКЕТА
                    try {
                        $BODY_UNSUBSCRIBE = @{

                            staff_id = "$USER_ID";
    
                        }
                        ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                        $UNSUBSCRIBE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_UNSUBSCRIBE | ConvertTo-Json -Depth 5))
                        $GET_JSON_RESPONSE_UNSUBSCRIBE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/unsubscribe/" -Headers $HEADERS -Body $UNSUBSCRIBE_TICKET -ContentType "application/json"
                        $GET_JSON_RESPONSE_UNSUBSCRIBE.name
                    }
                    catch {
                        $ERROR_PS = New-Object PSObject
                        $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Отписка от тикета"
                        $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                        $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
                    }
                    ### ЗАКРОЕМ ТИКЕТ
                    try {
                        ### ФОРМИРУЕМ ТЕЛО, КОТОРОЕ УХОДИТ С ЗАПРОСОМ
                        $BODY_CLOSE = @{
                                    
                            staff = $USER_ID;
                        
                            status = "4";
                            # Указываем филд "Обновление"
                            "t-cf-26" = "99";
                                        
                        }
                        ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                        $CLOSE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_CLOSE | ConvertTo-Json -Depth 5))
                        ### ОТПРАВЛЯЕМ POST ЗАПРОС НА ЗАКРЫТИЕ ТИКЕТА
                        $CLOSE_TICKET_JSON_RESPONSE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/staff_update/" -Headers $HEADERS -Body $CLOSE_TICKET -ContentType "application/json"
                        $CLOSE_TICKET_JSON_RESPONSE.name
                    }
                    catch {
                        $ERROR_PS = New-Object PSObject
                        $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Закрытие тикета"
                        $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                        $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
                    }
                }
            }
            ### ЕСЛИ НЕ НАШЁЛСЯ КОНТАКТ, КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ, ТО ЗАПИШЕМ ЭТО В ТАБЛИЦУ
            else {
                $ERROR_PS = New-Object PSObject
                $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Поиск контакта на рассылку"
                $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.name)"
                $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
            }
        }
        elseif ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Not active") {
            ### ПРОПУСТИМ И ПОЙДЁМ ДАЛЬШЕ
            continue
        }
        ### ЕСЛИ ОШИБКА ПРОВЕРКИ СТАТУС, ЗАПИШЕМ В ТАБЛИЦУ
        else {
            $ERROR_PS = New-Object PSObject
            $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Проверка статуса клиента"
            $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
            $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
        }
    }
}
### ЕСЛИ ОШИБКА ПОЛУЧЕНИИ ИНФОРМАЦИИ О КЛИЕНТЕ, ЗАПИШЕМ В ТАБЛИЦУ
else {
    $ERROR_PS = New-Object PSObject
    $ERROR_PS | Add-Member -Type NoteProperty "Операция" -Value "Составление списка клиента"
    $ERROR_PS | Add-Member -Type NoteProperty "Компания" -Value "ID клиента: $ID_GROUP"
    $ERROR_PS = $ERROR_TABLE_REPORT.Add($ERROR_PS)
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
        #Write-Host -ForegroundColor Green -Object "Сообщение с информацией о рассылке клиентов Bronze и Silver отправлена на почту"
    }
    catch {
        Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"
    }
}
else {
    Write-Host -ForegroundColor Red -Object "Ошибка. Не правильно сформированно тело отправки запроса"
}

### СФОРМИРУЕМ ТЕЛО ПИСЬМА С ОШИБКАМИ ЕСЛИ ОНИ БЫЛИ ЗАПОЛНЕНЫ В ТАБЛИЦЕ
if($ERROR_TABLE_REPORT) {
    $ERROR_HTML_REPORT = ($ERROR_TABLE_REPORT | ConvertTo-Html -Fragment) | Out-String
    $ERROR_BODY_REPORT = @"
    $ERROR_CSS_STYLE
    <h1 style="color: #5e9ca0;">Список с ошибками отправки рассылки клиентам</h1>
    $ERROR_HTML_REPORT
"@
}
### ЕСЛИ ТЕЛО ПИСЬМА СФОРМИРОВАНО, ТО ОТПРАВИМ ПИСЬМО
if ($ERROR_BODY_REPORT){
    ### ПОПРОБУЕМ ОТПРАВИТЬ РЕПОРТ ОТЧЁТА НА ПОЧТУ ОБ ОТПРАВЛЕННЫХ РАССЫЛКАХ КЛИЕНТАМ
    try {
        Send-MailMessage -From sup-smtp@boardmaps.ru -To $ERROR_TO -Subject "Информация об отправке рассылки клиентам (Версия: $NUMBER_VERSION)" -Body $ERROR_BODY_REPORT -BodyAsHtml -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -WarningAction SilentlyContinue;
        #Write-Host -ForegroundColor Green -Object "Сообщение с информацией о рассылке клиентов Bronze и Silver отправлена на почту"
    }
    catch {
        # Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"
    }
}
else {
    # Write-Host -ForegroundColor Red -Object "Ошибка. Не правильно сформированно тело отправки запроса"
}
