param($version_SB)

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

### ТЕМА ТИКЕТА
$TICKET_SUBJECT = "Обновление BoardMaps $NUMBER_VERSION"

# Oleg = ID - 5
# Dima = ID - 4
# Gleb = ID - 6

### ID ПОЛЬЗОВАТЕЛЯ ОТПРАВЛЯЮЩЕГО ОТВЕТ !!!!!!!!!!!
$USER_ID = "5"

### ID СТАТУСA ТИКЕТА ПРИ ОТВЕТЕ КЛИЕНТУ (Статус Awaiting reply (Client confirmation))
$STATUS_ID = "5"

### СОЗДАДИМ DUE DATE ДЛЯ ТИКЕТА
$DUE_DATE_REPLY = ((Get-Date).AddDays(7)).ToString('yyyy-MM-dd', [cultureinfo]::GetCultureInfo('en-US'))

### ФОРМИРУЕМ ДАННЫЕ ДЛЯ ОТПРАВКИ ПИСЬМА КЛИЕНТУ
$CLIENT_POST_PASS = ConvertTo-SecureString -String "X5k-WFw-7bn-Aq6" -AsPlainText -Force
$CLIENT_POST_CREDS = new-object Management.Automation.PSCredential -ArgumentList “support@boardmaps.ru”, $CLIENT_POST_PASS

### ФОРМИРУЕМ HTML ТЕКСТ ДЛЯ СОЗДАНИЯ ТИКЕТА
$HTML_BODY = @"
<body style="margin: 0; padding: 0; ">
    <font style="color: #2f2f2f; font-family: Arial, sans-serif; font-size: 14px; line-height: 16px;" align="justify">
        <table border="0" align="left" width="100%" height="auto" cellpadding="0" cellspacing ="0" background-size= "contain" background-position="left">
        <tr>
        <td>
            <table style="border-collapse:collapse;" border="0" width="95%" cellpadding="0" cellspacing ="0" align="center">
                <tr>
                    <td>
                        <img src="https://i.ibb.co/d09T7vw/logo.png" width="115px" height="70px" align="left" style="display:block;" alt="Logo">
                    </td>
                </tr>
                <tr>
                    <td colspan="3">
                        Здравствуйте!
                        <p>Сообщаем Вам о выходе новой версии серверной части приложения - <b>$NUMBER_VERSION</b>, в которую внесены функциональные улучшения.</p>
                        <p><b>Обращаем Ваше внимание</b>, что перед обновлением серверной части до $NUMBER_VERSION, необходимо обязательное обновление приложения BoardMaps для iPad из AppStore до актуальной версии на всех планшетах.</p>
                        <p>Для скачивания документации и дистрибутива, Вы можете воспользоваться кнопкой ниже:</p>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a href="https://cloud.boardmaps.ru/" target="blank"><img src="https://boardmaps.happyfox.com/get_hdp_inline_attachment/13933/" width="70px" height="35px" align="left" style="display:block;" alt="Скачать дистрибутив" ></a></p>
                    </td>
                </tr>

            </table>
            <table style="border-collapse:collapse;" border="0" width="95%" cellpadding="0" cellspacing ="0" align="center">
                <tr>
                    <td colspan="3">
                        <p>Для получения специалистами технической поддержки BoardMaps обратной связи, нажмите, пожалуйста, на одну из кнопок ниже.</p>
                    </td>
                </tr>
                <tr>
                    <td width="15%" height="30px">
                        <a href="mailto:support@boardmaps.ru?cc=КОПИИ_ПОЧТЫ&subject=Re:%20Обновление%20BoardMaps%20$NUMBER_VERSION%20#BU0000НОМЕР_ТИКЕТА&body=Добрый%20день!%20Обновление%20установлено"><img src="https://boardmaps.happyfox.com/get_hdp_inline_attachment/13931/" width="140px" height="45px" style="display:block;" alt="" ></a>
                    </td>
                    <td width="15%" height="30px">
                        <a href="mailto:support@boardmaps.ru?cc=КОПИИ_ПОЧТЫ&subject=Re:%20Обновление%20BoardMaps%20$NUMBER_VERSION%20#BU0000НОМЕР_ТИКЕТА&body=Пожалуйста,%20оставьте%20ниже%20Ваш%20комментарий%20или%20задайте%20вопрос%20по%20обновлению:%20"><img src="https://boardmaps.happyfox.com/get_hdp_inline_attachment/13932/"  width="140px" height="45px" style="display:block;" alt=""></a>
                    <td width="70%"></td>
                </tr>   
                <tr>
                    <td colspan="3">
                        <p font style="color: #a8a6a6"><br>С уважением,<br>Служба технической поддержки BoardMaps<br></p>
                    </td>
                </tr>  
            </table>
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
    foreach ($ID_GROUP in $GET_JSON_RESPONSE_FULL_GROUP.id){
        ### ИНФОРМАЦИЯ О КОНТАКТЕ
        $GET_JSON_RESPONSE_GROUP = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/contact_group/$($ID_GROUP)/" -Headers $HEADERS -ContentType "application/json"
        ### ПРОВЕРИМ СТАТУС КЛИЕНТА, ЕСЛИ SILVER ИЛИ BRONZE, ТО ОТПРАВИМ СТАНДАРТНУЮ РАССЫЛКУ
        if (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Silver1") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Bronze1")) {
            ### ОБНУЛИМ СПИСОК РАССЫЛКИ КЛИЕНТОВ
            $COPY_EMAIL = $null
            $MAIN_EMAIL = $null
            $MAIN_CONTACT = $null
            Write-Host -ForegroundColor DarkMagenta "Bronze OR Silver $($GET_JSON_RESPONSE_GROUP.name)"
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
                        Write-Host -ForegroundColor Green -Object "Добавлен в основной контакт: $MAIN_CONTACT"
                    }
                    ### СОСТАВИМ СПИСОК ПО КОПИИ
                    elseif ($GET_JSON_RESPONSE_CLIENT.custom_fields.value -cnotmatch "Основной контакт") {
                        $COPY_EMAIL_ADD = $GET_JSON_RESPONSE_CLIENT.email
                        if ($COPY_EMAIL) {
                            $COPY_EMAIL += ', '
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                            Write-Host -ForegroundColor Green -Object "+ COPY: $COPY_EMAIL"
                        }
                        else {
                            $COPY_EMAIL += $COPY_EMAIL_ADD
                            Write-Host -ForegroundColor Green -Object "1st COPY: $COPY_EMAIL"
                        }
                    }
                    ### ЕСЛИ ИНФОРМАЦИЮ О КЛИЕНТЕ НЕ ПОЛУЧИЛОСЬ СОСТАВИТЬ, ЗАПИШЕМ В ТАБЛИЦУ
                    else {
                        $PS = New-Object PSObject
                        $PS | Add-Member -Type NoteProperty "Операция" -Value "Формирования клиента на рассылку"
                        $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
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
                Write-Host -ForegroundColor Yellow -Object "CREATE TICKET $($GET_JSON_RESPONSE_GROUP.name)"

                ### ФОРМИРУЕМ HTML ТЕКСТ ДЛЯ ОТПРАВКИ ОТВЕТА РАССЫЛКИ КЛИЕНТУ
                $HTML_BODY_REPLY = @"
                <style type="text/css">
html, body {
margin: 0 !important;
padding: 0 !important;
height: 100% !important;
width: 100% !important;
}
* {
-ms-text-size-adjust: 100%;
-webkit-text-size-adjust: 100%;
}
.ExternalClass {
width: 100%;
}
div[style*="margin: 16px 0"] {
margin: 0 !important;
}
/* Вот эта штука должна не давать аутлуку делать доп. пробелы в таблицах */
table, td {
mso-table-lspace: 0pt !important;
mso-table-rspace: 0pt !important;
/* mso-line-height-rule: exactly; ВЕРНУТЬ ЕСЛИ ЧЁ*/
}
table {
border-spacing: 0 !important;
border-collapse: collapse !important;
table-layout: fixed !important;
margin: 0 auto !important;
}
table table table {
table-layout: auto;
}
img {
-ms-interpolation-mode: bicubic;
}
.yshortcuts a {
border-bottom: none !important;
}
a[x-apple-data-detectors] {
color: inherit !important;
}
</style>

<style type="text/css">
.button-td, .button-a {
/* transition: all 100ms ease-in; Это переход был
mso-ansi-font-size:13px;
mso-ansi-font-weight:bold;
mso-ascii-font-family: sans-serif;
mso-line-height-alt:50px;
mso-line-height-rule: exactly; */
}
/*.button-td:hover, .button-a:hover {
background: #555555 !important;
border-color: #555555 !important;
} */
/* Попробуем с этой штукой...  */
.center-on-narrow {
text-align: center !important;
display: block !important;
margin-left: auto !important;
margin-right: auto !important;
float: none !important;
}
table.center-on-narrow {
display: inline-block !important;
}
</style>
</head>
<body width="100%" height="100%" bgcolor="#e0e0e0" style="margin: 0;" yahoo="yahoo">
<table cellpadding="0" cellspacing="0" border="0" height="100%" width="100%" bgcolor="#e0e0e0" style="border-collapse:collapse;">
<tr>
<td><center style="width: 100%;">

<div style="display:none;font-size:1px;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;font-family: sans-serif;"> Обновление BoardMaps </div>


<div style="max-width: 600px;"> 
  <!--[if (gte mso 9)|(IE)]>
    <table cellspacing="0" cellpadding="0" border="0" width="600" align="center">
    <tr>
    <td>
    <![endif]--> 
  
  <!-- Header, первая картинка Начало -->
  <table cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px;">
    <tr style="padding: 0px;">
      <!--[if mso]>
        <td style="padding: 0px;" class="full-width-image" align="center"  ><img src="cid:bm_header_600x200.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
      <![endif]-->
      <![if !mso]>
        <td style="padding: 0px;" class="full-width-image" align="center"  ><img src="https://boardmaps.ru/bm_header_600x200.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
      <![endif]>
    </tr>
       <tr style="padding: 0px;">
    <!--[if mso]>
      <td style="padding: 0px; display: block;" class="full-width-image" align="center" ><img src="cid:bm_updateserver_600x100.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
    <![endif]-->
    <![if !mso]>
      <td style="padding: 0px; display: block;" class="full-width-image" align="center" ><img src="https://boardmaps.ru/bm_updateserver_600x100.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
    <![endif]>
    </tr>
      
  </table>
  <!-- Header конец --> 
  
  <!-- Body -->
  <table cellspacing="0" cellpadding="0" border="0" align="center" bgcolor="#ffffff" width="100%" style="max-width: 600px;">
    
    <!-- Вторая картинка (Была)-->
    
    <!-- Начало текста -->
    <tr>
      <td><table cellspacing="0" cellpadding="0" border="0" width="100%">
          <tr>
            <td style="padding: 40px; font-family: sans-serif; font-size: 15px; mso-height-rule: exactly; line-height: 20px; color: #555555;"> 
              <p><b>Здравствуйте!</b>&nbsp;</p>
              <p>Сообщаем о выходе новой версии серверной части приложения - <b>$NUMBER_VERSION</b>, в которую внесены функциональные улучшения:&nbsp;</p>
                <p> ⁃ Добавлена возможность выбора способа трансляции материалов: через сервер PSPDFKit или встроенное решение. <br/>
                     ⁃ Повышена стабильность сервиса работы с фоновыми задачами. <br/>
                     <b>⁃ Реализована отправка Push-уведомлений на устройства Apple без необходимости ежегодной загрузки сертификатов.</b> <br/>
                     ⁃ Выполнена поддержка отправки Push-уведомлений на iPad и iPhone приложение BoardMaps. <br/>
                     ⁃ Множественные улучшения интерфейса при использовании браузера на мобильных устройствах. <br/>
                     ⁃ Обновление встроенных библиотек для защиты от уязвимостей. <br/>
                     ⁃ Прочие исправления. </p>
              <p><b>Обращаем внимание</b>, что перед обновлением серверной части до $NUMBER_VERSION, необходимо обязательное обновление приложения BoardMaps  из AppStore до актуальной версии на всех планшетах.&nbsp;</p>
              <p>Ссылка для скачивания дистрибутива и документации об изменениях в новой версии:&nbsp;</p>
                <!-- "Кнопка" загрузки-->
                <table cellspacing="0" cellpadding="0" border="0" align="center" style="margin: auto;">
                <tr>
                  <td style="border-radius: 3px; background: #d6e7fe; text-align: center;" class="button-td"><a href="https://cloud.boardmaps.ru" style="background: #d6e7fe; border: 10px solid #d6e7fe; padding: 0 10px;color: #000000; font-family: sans-serif; font-size: 13px; text-align: center; text-decoration: none; display: block; border-radius: 3px; font-weight: bold;" class="button-a"> 
                    <!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]-->Загрузить дистрибутив и документацию<!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]--> 
                    </a></td>
                </tr>
              </table>
                 <!-- Продолжение текста -->
              
              <p>Для получения специалистами технической поддержки BoardMaps обратной связи, нажмите, пожалуйста, на одну из кнопок ниже:</p>
                <!-- "Кнопки" действия -->
                <table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: auto; border-collapse: collapse;">
                <tr>
                  <td style="padding-right: 11px; border-radius: 5px; background: #43FF76; text-align: center;" class="button-td"><a href="mailto:support@boardmaps.ru?cc=$($COPY_EMAIL)&subject=Re:%20$($CREATE_TICKET_JSON_RESPONSE.subject)%20$($CREATE_TICKET_JSON_RESPONSE.display_id)&body=Добрый%20день!%20Обновление%20установлено" style="background: #43FF76; border: 10px solid #43FF76; padding: 2px; color: #000000; font-family: sans-serif; font-size: 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 3px; font-weight: bold;" class="button-a"> 
                    <!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]-->&nbsp;&nbsp;&nbsp;Обновление прошло успешно<!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]--> 
                    </a></td>
                    <td >&nbsp;
                    </td>
                    <td style="border-radius: 5px; padding-right: 0px; background: #FF4F4F; text-align: center;" class="button-td"><a href="mailto:support@boardmaps.ru?cc=$($COPY_EMAIL)&subject=Re:%20$($CREATE_TICKET_JSON_RESPONSE.subject)%20$($CREATE_TICKET_JSON_RESPONSE.display_id)&body=Пожалуйста,%20оставьте%20ниже%20Ваш%20комментарий%20или%20задайте%20вопрос%20по%20обновлению:%20" style="background: #FF4F4F; border: 10px solid #FF4F4F; padding: 1px;color: #000000; font-family: sans-serif; font-size: 12px; text-align: center; text-decoration: none; display: inline-block; border-radius: 3px; font-weight: bold;" class="button-a"> 
                    <!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]-->При установке возникла проблема <!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]--> 
                    </a></td>
                </tr>
              </table>
              <p>С уважением,<br/>Служба технической поддержки BoardMaps&nbsp;</p>
              </td>
          </tr>
        </table></td>
    </tr>
    
  </table>
  <!-- Конец Body --> 
  
  <!-- Footer-->
  <table cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 680px;">
    <tr>
      <td style="padding: 10px 10px;width: 100%;font-size: 12px; font-family: sans-serif; mso-height-rule: exactly; text-decoration: none; line-height:18px; text-align: center; color: #888888;"> <!-- <a href="https://cloud.boardmaps.ru"> 
          <webversion style="color:#cccccc; text-decoration:underline; font-weight: bold;">Посмотреть как веб-страницу</webversion></a> -->
        <br>
        <br>BoardMaps<br>
<span class="mobile-link--footer"><a href="https://boardmaps.ru">www.boardmaps.ru</a></span> <br>
</td>
    </tr>
  </table>
  <!-- Конец футера --> 
  
  <!--[if (gte mso 9)|(IE)]>
    </td>
    </tr>
    </table>
    <![endif]--> 
</div>
</center></td>
</tr>
</table>
</body>
"@
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
                    Write-Host -ForegroundColor Yellow -Object "REPLY TICKET $($GET_JSON_RESPONSE_GROUP.name)"
                    try {
                        ### СФОРМИРУЕМ ФАЙЛ ОТПРАВКИ
                        #$HTML = Get-Content -Path "D:\Script\BoardMaps\automatic_email-1\HTML\testBM29.html"

                        $HTML = @"
                        <style type="text/css">
html, body {
	margin: 0 !important;
	padding: 0 !important;
	height: 100% !important;
	width: 100% !important;
}
* {
	-ms-text-size-adjust: 100%;
	-webkit-text-size-adjust: 100%;
}
.ExternalClass {
	width: 100%;
}
div[style*="margin: 16px 0"] {
	margin: 0 !important;
}
	/* Вот эта штука должна не давать аутлуку делать доп. пробелы в таблицах */
table, td {
	mso-table-lspace: 0pt !important;
	mso-table-rspace: 0pt !important;
	/* mso-line-height-rule: exactly; ВЕРНУТЬ ЕСЛИ ЧЁ*/
}
table {
	border-spacing: 0 !important;
	border-collapse: collapse !important;
	table-layout: fixed !important;
	margin: 0 auto !important;
}
table table table {
	table-layout: auto;
}
img {
	-ms-interpolation-mode: bicubic;
}
.yshortcuts a {
	border-bottom: none !important;
}
a[x-apple-data-detectors] {
	color: inherit !important;
}
</style>

<style type="text/css">
.button-td, .button-a {
	/* transition: all 100ms ease-in; Это переход был
	mso-ansi-font-size:13px;
	mso-ansi-font-weight:bold;
	mso-ascii-font-family: sans-serif;
	mso-line-height-alt:50px;
	mso-line-height-rule: exactly; */
}
/*.button-td:hover, .button-a:hover {
	background: #555555 !important;
	border-color: #555555 !important;
} */
/* Попробуем с этой штукой...  */
	.center-on-narrow {
	text-align: center !important;
	display: block !important;
	margin-left: auto !important;
	margin-right: auto !important;
	float: none !important;
}
table.center-on-narrow {
	display: inline-block !important;
}
</style>
</head>
<body width="100%" height="100%" bgcolor="#e0e0e0" style="margin: 0;" yahoo="yahoo">
<table cellpadding="0" cellspacing="0" border="0" height="100%" width="100%" bgcolor="#e0e0e0" style="border-collapse:collapse;">
  <tr>
    <td><center style="width: 100%;">
        
        <div style="display:none;font-size:1px;line-height:1px;max-height:0px;max-width:0px;opacity:0;overflow:hidden;mso-hide:all;font-family: sans-serif;"> Обновление BoardMaps </div>
       
        
        <div style="max-width: 600px;"> 
          <!--[if (gte mso 9)|(IE)]>
            <table cellspacing="0" cellpadding="0" border="0" width="600" align="center">
            <tr>
            <td>
            <![endif]--> 
          
          <!-- Header, первая картинка Начало -->
          <table cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 600px;">
            <tr style="padding: 0px;">
              <!--[if mso]>
                <td style="padding: 0px;" class="full-width-image" align="center"  ><img src="cid:bm_header_600x200.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
              <![endif]-->
              <![if !mso]>
                <td style="padding: 0px;" class="full-width-image" align="center"  ><img src="https://boardmaps.ru/bm_header_600x200.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
              <![endif]>
            </tr>
			   <tr style="padding: 0px;">
            <!--[if mso]>
              <td style="padding: 0px; display: block;" class="full-width-image" align="center" ><img src="cid:bm_updateserver_600x100.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
            <![endif]-->
            <![if !mso]>
              <td style="padding: 0px; display: block;" class="full-width-image" align="center" ><img src="https://boardmaps.ru/bm_updateserver_600x100.png" width="600" alt="boardmaps_logo" border="0" style="width: 100%; max-width: 600px; height: auto; display: block;"></td>
            <![endif]>
            </tr>
			  
          </table>
          <!-- Header конец --> 
          
          <!-- Body -->
          <table cellspacing="0" cellpadding="0" border="0" align="center" bgcolor="#ffffff" width="100%" style="max-width: 600px;">
            
            <!-- Вторая картинка (Была)-->
            
            <!-- Начало текста -->
            <tr>
              <td><table cellspacing="0" cellpadding="0" border="0" width="100%">
                  <tr>
                    <td style="padding: 40px; font-family: sans-serif; font-size: 15px; mso-height-rule: exactly; line-height: 20px; color: #555555;"> 
					  <p><b>Здравствуйте!</b>&nbsp;</p>
                      <p>Сообщаем о выходе новой версии серверной части приложения - <b>$NUMBER_VERSION</b>, в которую внесены функциональные улучшения:&nbsp;</p>
						<p> ⁃ Добавлена возможность выбора способа трансляции материалов: через сервер PSPDFKit или встроенное решение. <br/>
 							⁃ Повышена стабильность сервиса работы с фоновыми задачами. <br/>
 							<b>⁃ Реализована отправка Push-уведомлений на устройства Apple без необходимости ежегодной загрузки сертификатов.</b> <br/>
 							⁃ Выполнена поддержка отправки Push-уведомлений на iPad и iPhone приложение BoardMaps. <br/>
 							⁃ Множественные улучшения интерфейса при использовании браузера на мобильных устройствах. <br/>
 							⁃ Обновление встроенных библиотек для защиты от уязвимостей. <br/>
							 ⁃ Прочие исправления. </p>
                      <p><b>Обращаем внимание</b>, что перед обновлением серверной части до $NUMBER_VERSION, необходимо обязательное обновление приложения BoardMaps  из AppStore до актуальной версии на всех планшетах.&nbsp;</p>
                      <p>Ссылка для скачивания дистрибутива и документации об изменениях в новой версии:&nbsp;</p>
						<!-- "Кнопка" загрузки-->
						<table cellspacing="0" cellpadding="0" border="0" align="center" style="margin: auto;">
                        <tr>
                          <td style="border-radius: 3px; background: #d6e7fe; text-align: center;" class="button-td"><a href="https://cloud.boardmaps.ru" style="background: #d6e7fe; border: 10px solid #d6e7fe; padding: 0 10px;color: #000000; font-family: sans-serif; font-size: 13px; text-align: center; text-decoration: none; display: block; border-radius: 3px; font-weight: bold;" class="button-a"> 
                            <!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]-->Загрузить дистрибутив и документацию<!--[if mso]>&nbsp;&nbsp;&nbsp;&nbsp;<![endif]--> 
                            </a></td>
                        </tr>
                      </table>
						 <!-- Продолжение текста -->
                      
                      <p>Для получения специалистами технической поддержки BoardMaps обратной связи, нажмите, пожалуйста, на одну из кнопок ниже:</p>
						<!-- "Кнопки" действия -->
						<table role="presentation" cellspacing="0" cellpadding="0" border="0" align="center" style="margin: 1px; border-collapse: collapse;">
                        <tr>
                          <td style="border-radius: 5px; background: #43FF76; text-align: center;" class="button-td"><a href="mailto:support@boardmaps.ru?cc=$($COPY_EMAIL)&subject=Re:%20Обновление%20BoardMaps%20$NUMBER_VERSION%20#BU0000$($CREATE_TICKET_JSON_RESPONSE.id)&body=Добрый%20день!%20Обновление%20установлено" style="background: #43FF76; border: 10px solid #43FF76; padding: 0px 16px; color: #000000; font-family: sans-serif; font-size: 13px; text-align: center; text-decoration: none; display: inline-block; font-weight: bold;" class="button-a" border-radius: 3px; > 
                            <!--[if mso]>&nbsp;<![endif]-->Обновление прошло успешно<!--[if mso]>&nbsp;<![endif]--> 
                            </a></td>
							<td>&nbsp;
						    </td>
							<td style="border-radius: 5px; background: #FF4F4F; text-align: center;" class="button-td"><a href="mailto:support@boardmaps.ru?cc=$($COPY_EMAIL)&subject=Re:%20Обновление%20BoardMaps%20$NUMBER_VERSION%20#BU0000$($CREATE_TICKET_JSON_RESPONSE.id)&body=Пожалуйста,%20оставьте%20ниже%20Ваш%20комментарий%20или%20задайте%20вопрос%20по%20обновлению:%20" style="background: #FF4F4F; border: 10px solid #FF4F4F; padding: 0px; color: #000000; font-family: sans-serif; font-size: 13px; text-align: center; text-decoration: none; display: inline-block; font-weight: bold;" class="button-a" border-radius: 3px; > 
                            <!--[if mso]>&nbsp;<![endif]-->При установке возникла проблема <!--[if mso]>&nbsp;<![endif]--> 
                            </a></td>
                        </tr>
                      </table>
                      <p>С уважением,<br/>Служба технической поддержки BoardMaps&nbsp;</p>
					  </td>
                  </tr>
                </table></td>
            </tr>
            
          </table>
          <!-- Конец Body --> 
          
          <!-- Footer-->
          <table cellspacing="0" cellpadding="0" border="0" align="center" width="100%" style="max-width: 680px;">
            <tr>
              <td style="padding: 10px 10px;width: 100%;font-size: 12px; font-family: sans-serif; mso-height-rule: exactly; text-decoration: none; line-height:18px; text-align: center; color: #888888;"> <!-- <a href="https://cloud.boardmaps.ru"> 
				  <webversion style="color:#cccccc; text-decoration:underline; font-weight: bold;">Посмотреть как веб-страницу</webversion></a> -->
                <br>
                <br>BoardMaps<br>
<span class="mobile-link--footer"><a href="https://boardmaps.ru">www.boardmaps.ru</a></span> <br>
</td>
            </tr>
          </table>
          <!-- Конец футера --> 
          
          <!--[if (gte mso 9)|(IE)]>
            </td>
            </tr>
            </table>
            <![endif]--> 
        </div>
      </center></td>
  </tr>
</table>
</body>
"@
                        
                        ### ПРОВЕРИМ, ЕСТЬ ЛИ КОПИЯ КОМУ ОТПРАВЛЯТЬ
                        if ($COPY_EMAIL) {
                            ### ПРЕОБРАЗУЕМ СТРОКУ В МАССИВ СТРОК
                            [string[]]$TO_COPY = $COPY_EMAIL.Split(',')
                            ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                            Get-ChildItem -Path 'D:\Script\BoardMaps\automatic_email-1\HTML\Images' | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Cc $TO_COPY -Subject $TICKET_SUBJECT -Body ($HTML | Out-String) -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                            -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure'
                        }
                        ### ЕСЛИ КОПИИ НЕТ, ПРОСТО ОТПРАВИМ РАССЫЛКУ НА ОСНОВНОЙ КОНТАКТ
                        else {
                            ### ОТПРАВИМ СООБЩЕНИЕ КЛИЕНТУ
                            Get-ChildItem -Path '.\' | Send-MailMessage -From "support@boardmaps.ru" -To $MAIN_EMAIL -Subject $TICKET_SUBJECT -Body ($HTML | Out-String) -BodyAsHtml -Credential $CLIENT_POST_CREDS `
                            -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8) -DeliveryNotificationOption 'OnFailure'
                        }
                        Write-Host -ForegroundColor Magenta -Object "Рассылка клиенту $($GET_JSON_RESPONSE_GROUP.name) отправлена"
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
                Write-Host -ForegroundColor Green -Object "DONE CLIENT $($GET_JSON_RESPONSE_GROUP.name)"
            }
        }
        ### ПРОВЕРИМ КЛИЕНТА НА ГОЛД ИЛИ ПЛАТИНУМ
        elseif (($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Platinum") -or ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Gold")) {
            Write-Host -ForegroundColor DarkMagenta "Gold OR Platinum $($GET_JSON_RESPONSE_GROUP.name)"
        }
        elseif ($GET_JSON_RESPONSE_GROUP.tagged_domains -cmatch "Not active ") {
            <# Action when this condition is true #>
        }
        ### ЕСЛИ ОШИБКА ПРОВЕРКИ СТАТУС, ЗАПИШЕМ В ТАБЛИЦУ
        else {
            $PS = New-Object PSObject
            $PS | Add-Member -Type NoteProperty "Операция" -Value "Ошибка проверки статуса клиента"
            $PS | Add-Member -Type NoteProperty "Компания" -Value "$($GET_JSON_RESPONSE_GROUP.name)"
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
        Send-MailMessage -From sup-smtp@boardmaps.ru -To $TO -Subject "Информация об отправки рассылки Bronze и Silver клиентам" -Body $BODY_REPORT -BodyAsHtml -Credential $POST_CREDS -SmtpServer smtp.yandex.com -Port 587 –UseSsl -Encoding ([System.Text.Encoding]::UTF8);
        Write-Host -ForegroundColor Green -Object "Рассылка Bronze и Silver клиентам отправлена"
    }
    catch {
        {Write-Host -ForegroundColor Red -Object "Ошибка отправки сообщения"}
    }
}
else {
    Write-Host -ForegroundColor Red -Object "Ошибка. Не правильно сформированно тело отправки запроса"
}
