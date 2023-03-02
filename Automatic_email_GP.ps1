param($version_GP, $support_response_id)

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
#"gleb.chechelnitskiy@boardmaps.ru", "dmitriy.chaban@boardmaps.ru"

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
$NUMBER_VERSION = $version_GP

### ТЕМА ТИКЕТА
$TICKET_SUBJECT = "Обновление BoardMaps $NUMBER_VERSION"

# Oleg = ID - 5
# Dima = ID - 4
# Gleb = ID - 6

### ID ПОЛЬЗОВАТЕЛЯ ОТПРАВЛЯЮЩЕГО ОТВЕТ !!!!!!!!!!!
$USER_ID = $support_response_id

### ID СТАТУСA ТИКЕТА
$STATUS_ID = "5"

### СОЗДАДИМ DUE DATE ДЛЯ ТИКЕТА
$DUE_DATE_REPLY = ((Get-Date).AddDays(7)).ToString('yyyy-MM-dd', [cultureinfo]::GetCultureInfo('en-US'))

### ФОРМИРУЕМ HTML ТЕКСТ СОЗДАНИЯ ТИКЕТА VIP КЛИЕНТА
$HTML_BODY_VIP = @"
<body style="margin: 0; padding: 0;">
    <font style="color: #2f2f2f; font-family: Arial, sans-serif; font-size: 14px; line-height: 16px;" align="justify">
        <table border="0" align="left" width="100%" height="auto" cellpadding="0" cellspacing ="0" background-size= "contain" background-repeat="no-repeat" background-position="left">
        <tr>
        <td>
            <table style="border-collapse:collapse;" border="0" width="95%" cellpadding="0" cellspacing ="0" align="center">
                <tr>
                    <td>
                        Здравствуйте!<br>
                        <p>Сообщаем Вам о выходе новой версии серверной части приложения - <b>$NUMBER_VERSION</b>, в которую внесены функциональные улучшения.</p>
                        <p><ins>Просим согласовать сервисное окно, для установки обновления.</ins></p>
                        <p>Для скачивания документации и дистрибутива, Вы можете воспользоваться ссылкой: <a href="https://cloud.boardmaps.ru" target="_blank" rel="noopener noreferrer">https://cloud.boardmaps.ru</a> </p>
                    </td>
                </tr>
            </td>
        </tr>
        <tr>
            <td>
                <p font style="color: #a8a6a6"><br>С уважением,<br>Служба технической поддержки BoardMaps<br></p>
            </td>
        </tr>
        </table>
    </font>
</body>
"@

### ЗАПРОСИМ ВЕСЬ СПИСОК ГРУПП ИЗ HAPPYFOX
$GET_JSON_RESPONSE_FULL_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_groups/" -Headers $HEADERS -ContentType "application/json"

### СВОДНЫЙ СБОР ИНФОРМАЦИИ КОМУ ОТПРАВЛЯЕТСЯ РАССЫЛКА
if ($GET_JSON_RESPONSE_FULL_GROUP) {
    ### ПРОЙДЁМСЯ ПО КАЖДОМУ СПИСКУ КОНТАКТОВ ГРУПП
    foreach ($ID_GROUP in $GET_JSON_RESPONSE_FULL_GROUP.id){
        ### ВЫТЯНИМ ИНФОРМАЦИЮ О КОНТАКТ ГРУППЕ
        $GET_JSON_RESPONSE_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_group/$($ID_GROUP)/" -Headers $HEADERS -ContentType "application/json"
        ### ПРОВЕРИМ КЛИЕНТА НА ГОЛД ИЛИ ПЛАТИНУМ
        if (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Platinum1") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Gold1")) {
            ### ОБНУЛИМ СПИСОК РАССЫЛКИ КЛИЕНТОВ
            $COPY_EMAIL = $null
            $MAIN_EMAIL = $null
            $MAIN_CONTACT = $null
            Write-Host -ForegroundColor DarkMagenta "Gold OR Platinum $($GET_JSON_RESPONSE_GROUP.name)"
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
                        Write-Host -ForegroundColor Green -Object "MAIN $MAIN_CONTACT"
                    }
                    ### СОСТАВИМ СПИСОК ПО КОПИИ
                    elseif ($GET_JSON_RESPONSE_CLIENT.custom_fields.value -cnotmatch "Основной контакт") {
                        $COPY_EMAIL_ADD = $GET_JSON_RESPONSE_CLIENT.email
                        $COPY_EMAIL += $COPY_EMAIL_ADD
                        $COPY_EMAIL += ', '
                        Write-Host -ForegroundColor Green -Object "COPY $COPY_EMAIL"
                    }
                    ### ЕСЛИ ИНФОРМАЦИЮ О КЛИЕНТЕ НЕ ПОЛУЧИЛОСЬ СОСТАВИТЬ, ЗАПИШЕМ В ТАБЛИЦУ
                    else {
                        $PS = New-Object PSObject
                        $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка формирования клиента на рассылку"
                        $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.name)"
                        $PS = $TABLE_REPORT.Add($PS)
                        Write-Host -ForegroundColor Red -Object "ERROR $($GET_JSON_RESPONSE_CLIENT.name)"
                    }
                }
            }
            ### ПРОВЕРИМ, ЧТО У КЛИЕНТА ЕСТЬ КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ
            if ($MAIN_CONTACT) {
                Write-Host -ForegroundColor Cyan -Object "Основной контакт: $MAIN_CONTACT"
            }
            ### ЕСЛИ НЕ НАШЁЛСЯ КОНТАКТ, КОМУ ОТПРАВЛЯТЬ РАССЫЛКУ, ТО ЗАПИШЕМ ЭТО В ТАБЛИЦУ
            else {
                $PS = New-Object PSObject
                $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка поиска контакта на рассылку"
                $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_CLIENT.name)"
                $PS = $TABLE_REPORT.Add($PS)
                Write-Host -ForegroundColor Red -Object "ERROR нет контакта на рассылку $($GET_JSON_RESPONSE_CLIENT.name)"
            }
            try {
                ### ФОРМИРУЕМ ТЕЛО НА СОЗДАНИЕ ТИКЕТА, КОТОРОЕ УХОДИТ С ЗАПРОСОМ
                $BODY_CREATE = @{

                    name = "$MAIN_CONTACT";
                    
                    email = "$MAIN_EMAIL";

                    cc = "$COPY_EMAIL";
                    
                    category = 6;

                    priority = "4";
                    
                    subject = "$TICKET_SUBJECT";
                    
                    html = "$HTML_BODY_VIP";
                    
                    }
                ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                $CREATE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_CREATE | ConvertTo-Json -Depth 5))
                ### ОТПРАВЛЯЕМ ЗАПРОС НА СОЗДАНИЕ ТИКЕТА
                $CREATE_TICKET_JSON_RESPONSE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/tickets/" -Headers $HEADERS -Body $CREATE_TICKET -ContentType "application/json"
                Write-Host -ForegroundColor Yellow -Object "CREATE TICKET $($GET_JSON_RESPONSE_GROUP.name)"

                ### ПРОБУЕМ ОТПРАВИТЬ ОТВЕТ В ТИКЕТЕ (ОТПРАВЛЯЕМ ПИСЬМО КЛИЕНТУ О НОВОЙ ВЕРСИИ)
                try {
                    ### ФОРМИРУЕМ ТЕЛО, КОТОРОЕ УХОДИТ С ЗАПРОСОМ
                    $BODY_REPLY = @{

                        html = "$HTML_BODY_VIP";

                        cc = "$COPY_EMAIL";
                        
                        staff = $USER_ID;

                        status = $STATUS_ID;

                        update_customer = "true";

                        due_date = "$DUE_DATE_REPLY";
                        
                        }
                    ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                    $REPLY_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_REPLY | ConvertTo-Json -Depth 5))
                    ### ОТПРАВЛЯЕМ POST ЗАПРОС НА ОТВЕТ В HF
                    $REPLY_TICKET_JSON_RESPONSE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/staff_update/" -Headers $HEADERS -Body $REPLY_TICKET -ContentType "application/json"
                    Write-Host -ForegroundColor Yellow -Object "REPLY TICKET $($GET_JSON_RESPONSE_GROUP.name)"
                    ### ДОБАВЛЯЕМ ДАННЫЕ В ТАБЛИЦУ
                    $PS = New-Object PSObject
                    $PS | Add-Member -Type NoteProperty "Операция" -Value "Рассылка клиенту отправлена"
                    $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                    $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                }
                catch {
                    ### ЕСЛИ ОШИБКА ОТВЕТА В РАНЕЕ СОЗДАННОМ ТИКЕТЕ, ЗАПИШИМ В ТАБЛИЦУ
                    $PS = New-Object PSObject
                    $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка отправки письма"
                    $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                    $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "$($CREATE_TICKET_JSON_RESPONSE.id)"
                    Write-Host -ForegroundColor Red -Object "ERROR REPLY"
                }
            }
            catch {
                ### ЕСЛИ ОШИБКА СОЗДАНИИ ТИКЕТА, ЗАПИШИМ В ТАБЛИЦУ
                $PS = New-Object PSObject
                $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка создания тикета"
                $PS | Add-Member -Type NoteProperty "Компания" -Value "$($REPLY_TICKET_JSON_RESPONSE.user.contact_groups.name)"
                $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "Тикет не был создан"
                Write-Host -ForegroundColor Red -Object "ERROR CREATE"
            }
            finally {
                ### ОТПИШИМСЯ ОТ СОЗДАННОГО ТИКЕТА
                $BODY_UNSUBSCRIBE = @{

                    staff_id = "$USER_ID";

                }
                ### ПРЕОБРАЗУЕМ В JSON И ПРИВЕДЕМ К БАЙТОВОМУ МАССИВУ
                $UNSUBSCRIBE_TICKET = [System.Text.Encoding]::UTF8.GetBytes(($BODY_UNSUBSCRIBE | ConvertTo-Json -Depth 5))
                $GET_JSON_RESPONSE_UNSUBSCRIBE = Invoke-RestMethod -Method Post -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($CREATE_TICKET_JSON_RESPONSE.id)/unsubscribe/" -Headers $HEADERS -Body $UNSUBSCRIBE_TICKET -ContentType "application/json"
                $GET_JSON_RESPONSE_UNSUBSCRIBE.name
                ### ФОРМИРУЕМ ТАБЛИЦУ С ОТЧЁТОМ
                $PS = $TABLE_REPORT.Add($PS)
                Write-Host -ForegroundColor Green -Object "DONE CLIENT $($GET_JSON_RESPONSE_GROUP.name)"
            }
        }
        ### ПРОВЕРИМ КЛИЕНТА НА СИЛЬВЕР ИЛИ БРОНЗУ
        elseif (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Silver") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Bronze")) {
            <# Action when this condition is true #>
        }
        elseif ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Not active ") {
            <# Action when this condition is true #>
        }
        ### ЕСЛИ НЕТ СТАТУС ПЛАНА, ТО ЗАПИШЕМ В ТАБЛИЦУ
        else {
            $PS = New-Object PSObject
            $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка проверки статус плана клиента"
            $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
            $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "Тикет не был создан"
            $PS = $TABLE_REPORT.Add($PS)
            Write-Host -ForegroundColor Red -Object "ERROR! Клиент без статус плана $($GET_JSON_RESPONSE_GROUP.name)"
        }
    }
}
### ЕСЛИ ОШИБКА ПОЛУЧЕНИИ ИНФОРМАЦИИ О КЛИЕНТЕ, ЗАПИШЕМ В ТАБЛИЦУ
else {
    $PS = New-Object PSObject
    $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка составления списка клиента"
    $PS | Add-Member -Type NoteProperty "Компания" -Value "ID клиента: $ID_GROUP"
    $PS | Add-Member -Type NoteProperty "Номер тикета" -Value "Тикет не был создан"
    $PS = $TABLE_REPORT.Add($PS)
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
        Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO -Subject "Информация об отправки рассылки Gold и Platinum клиентам" -Body $BODY_REPORT -BodyAsHtml -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8);
        Write-Host -ForegroundColor Green -Object "Рассылка Gold и Platinum клиентам отправлена"
    }
    catch {
        {Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"}
    }
}
else {
    Write-Host -ForegroundColor Red -Object "Ошибка. Не правильно сформированно тело отправки запроса"
}