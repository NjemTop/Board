param($ticket_id)
### ФУНКЦИЯ ВЫВОДА ВРЕМЕНИ
Function Get-TimeSpanPretty {
    <#
    .Synopsis
       Displays the time span between two dates in a single line, in an easy-to-read format
    .DESCRIPTION
       Only non-zero weeks, days, hours, minutes and seconds are displayed.
       If the time span is less than a second, the function display "Less than a second."
    .PARAMETER TimeSpan
       Uses the TimeSpan object as input that will be converted into a human-friendly format
    .EXAMPLE
       Get-TimeSpanPretty -TimeSpan $TimeSpan
       Displays the value of $TimeSpan on a single line as number of weeks, days, hours, minutes, and seconds.
    .EXAMPLE
       $LongTimeSpan | Get-TimeSpanPretty
       A timeline object is accepted as input from the pipeline. 
       The result is the same as in the previous example.
    .OUTPUTS
       String(s)
    .NOTES
       Last changed on 28 July 2022
    #>
    
        [CmdletBinding()]
        Param
        (
            # Param1 help description
            [Parameter(Mandatory,ValueFromPipeline)][ValidateNotNull()][timespan]$TimeSpan
        )
    
        Begin {}
        Process{
    
            # Initialize $TimeSpanPretty, in case there is more than one timespan in the input via pipeline
            [string]$TimeSpanPretty = ""
        
            $Ts = [ordered]@{
                Weeks   = [math]::Floor($TimeSpan.Days / 7)
                Days    = [int]$TimeSpan.Days % 7
                Hours   = [int]$TimeSpan.Hours
                Minutes = [int]$TimeSpan.Minutes
                Seconds = [int]$TimeSpan.Seconds
            } 
    
            # Process each item in $Ts (week, day, etc.)
            foreach ($i in $Ts.Keys){
    
                # Skip if zero
                if ($Ts.$i -ne 0) {
                    
                    # Append the value and key to the string
                    $TimeSpanPretty += "{0} {1}, " -f $Ts.$i,$i
                    
                } #Close if
        
            } #Close for
        
        # If the $TimeSpanPretty is not 0 (which could happen if start and end time are identical.)
        if ($TimeSpanPretty.Length -ne 0){
    
            # delete the last coma and space
            $TimeSpanPretty = $TimeSpanPretty.Substring(0,$TimeSpanPretty.Length-2)
        }
        else {
            
            # Display "Less than a second" instead of an empty string.
            $TimeSpanPretty = "Less than a second"
        }
    
        $TimeSpanPretty
    
        } # Close Process
    
        End {}
    
    }

### ФУНКЦИЯ ПОДСЧЁТА ВРЕМЕНИ SLA
function Get-TimeWork {
        param (
            [datetime]$stt, # старт
            [datetime]$ett, # стоп
            [timespan]$start, # начало рабочего периода
            [timespan]$end # конец рабочего периода
        )
        function IsWorkDay([DateTime]$date, [string]$calendarFile) {
            $calendarFile = "C:\Users\Adena\Documents\calendar.xml"
            # Загрузка календаря из файла
            $cal = [xml](Get-Content $calendarFile)
        
            # Проверка, является ли день выходным
            $isHoliday = $cal.calendar.days.day | Where-Object { $_.d -eq $date.ToString("dd.MM.yyyy") -and $_.t -eq "Вых" }
        
            # Проверка, является ли день праздником
            $isProductionHoliday = $cal.calendar.days.day | Where-Object { $_.d -eq $date.ToString("dd.MM.yyyy") -and $_.f }
        
            return !$isHoliday -and !$isProductionHoliday
        }        
        
        function Get-Weekend {
            param (
                [datetime]$sd,
                [datetime]$ed,
                [int[]]$weekend = @(6,0)
            )
            $sub = ($ed.date - $sd.date).days
            $arr = @()
            for ($i = 0; $i -le $sub;$i++){
                #формируем массив выходных за период, для дальнейшего подсчета пар
                if ($sd.adddays($i).dayofweek.value__ -in $weekend){
                    $arr += $sd.adddays($i).dayofweek.value__
                }
            }
            if ($arr){
                $out = ($arr.where({$_ -eq $weekend[0]},5)|ForEach-Object{$_.count}|Sort-Object -d)[0]
            } else {$out = 0}
            return $out
        }
        if ($ett -le $stt) {
            break
        }
        $m = new-timespan -h ($end - $start).totalhours
        $x = ($ett.date - $stt.date).days # количество дней между стартом и стопом
        $w, $h = @(1,2,3,4,5), @(6,0) # будни, выходные (суббота и воскресенье)
        # укорачиваем код до названия переменных:
        $sdw,$edw = $stt.dayofweek.value__,$ett.dayofweek.value__ # номер дня недели для старт и стоп
        $rs,$re = $stt.timeofday.totalminutes,$ett.timeofday.totalminutes
        $s,$e = $start.totalminutes,$end.totalminutes
        $minutes = $m.totalminutes
    
        # Для выходных:
        if ($edw -in $h){
            # Если стоп в выходной день (перенос стопа на пон. 0:00)
            if (!$edw){$ds = 1} else {$ds = 2}
            $ett = $ett.addminutes(-$ett.timeofday.totalminutes)
            $ett = $ett.adddays($ds)
            $edw,$re = $ett.dayofweek.value__,$ett.timeofday.totalminutes
            $x = ($ett.date - $stt.date).days
        }
        if ($sdw -in $h){
            # Если старт в выходной день (перенос старта на пон. 0:00)
            if (!$sdw){$ds = 1} else {$ds = 2}
            $stt = $stt.addminutes(-$stt.timeofday.totalminutes)
            $stt = $stt.adddays($ds)
            $sdw,$rs = $stt.dayofweek.value__,$stt.timeofday.totalminutes
            $x = ($ett.date - $stt.date).days
        }
        $kw = Get-Weekend $stt $ett # количество пар выходных между стартом и стопом
        if ($stt.dayofweek.value__ -in $h -and $kw){$kw--}
        if ($x -and $sdw -in $w -and $edw -in $w){
            # Если есть полный переход через выходные, 
            # старт/стоп в рабочие дни, вычитаем выходные полностью:
            $x = $x - 2*$kw
        }
        
        # Реализация логики подсчета для будней:
        if (!$x -and $sdw -in $w -and $edw -in $w -and $re -ge $rs){
            # Если и старт, и стоп в один день
            if($rs -lt $s -and $re -gt $e){
                $time = new-timespan -min ($minutes)
            } elseif (($rs -ge $s -and $rs -le $e) -and $re -gt $e){
                $time = new-timespan -min ($e - $rs)
            } elseif (($rs -gt $e -and $re -gt $e) -or ($rs -lt $s -and $re -lt $s)){
                $time = new-timespan
            } elseif ($rs -lt $s -and ($re -ge $s -and $re -le $e)) {
                $time = new-timespan -min ($re - $s)
            } elseif (($rs -ge $s -and $rs -le $e) -and ($re -ge $s -and $re -le $e)){
                $time = new-timespan -min ($re - $rs)
            }
        } elseif ($x -and $sdw -in $w -and $edw -in $w) {
            # Если старт и стоп в разные дни,
            if ($rs -lt $s -and $re -gt $e){
                $time = new-timespan -min ($minutes * ($x+1))
            } elseif (($rs -ge $s -and $rs -le $e) -and $re -gt $e){
                $time = new-timespan -min ($e - $rs + $minutes*$x)
            } elseif (($rs -gt $e -and $re -gt $e) -or ($rs -lt $s -and $re -lt $s)){
                $time = new-timespan -min ($minutes * $x)
            } elseif ($rs -lt $s -and ($re -ge $s -and $re -le $e)){
                $time = new-timespan -min ($re - $s + $minutes*$x)
            } elseif (($rs -ge $s -and $rs -le $e) -and ($re -ge $s -and $re -le $e)){
                $time = new-timespan -min ($re - $s + $e - $rs + $minutes*($x-1))
            } elseif ($rs -gt $e -and ($re -ge $s -and $re -le $e)) {
                $time = new-timespan -min ($re - $s + $minutes*($x-1))
            } elseif (($rs -ge $s -and $rs -le $e) -and $re -lt $s){
                $time = new-timespan -min ($e - $rs + $minutes*($x-1))
            } elseif ($rs -gt $e -and $re -lt $s) {
                $time = new-timespan -min ($minutes*($x-1))
            } 
        }
        return $time
    }

### УКАЗЫВАЕМ ПУТЬ К ФАЙЛУ С КРЕДИТАМИ
$CONFIG_FILE = "./Main.config"

### ЧТЕНИЕ СОДЕРЖИМОГО ФАЙЛА И ПРЕОБРАЗОВАНИЕ ЕГО В ОБЪЕКТ
$CONFIG = Get-Content $CONFIG_FILE | ConvertFrom-Json

### ИЗВЛЕКАЕМ ЗНАЧЕНИЕ API_KEY и API_SECRET
$API_KEY = $CONFIG.HAPPYFOX_SETTINGS.API_KEY
$API_SECRET = $CONFIG.HAPPYFOX_SETTINGS.API_SECRET

### ТОКЕН ДОСТУПА ДЛЯ API К HAPPYFOX
$ACCESS_TOKEN = "$($API_KEY):$($API_SECRET)"

# БАЗОВЫЙ URL ДЛЯ API
$HF_ENDPOINT = "https://boardmaps.happyfox.com"

# КОДИРОВАНИЕ И СОЗДАНИЕ КОДА АВТОРИЗАЦИЙ
$EncodedACCESS_TOKEN = [System.Text.Encoding]::UTF8.GetBytes($ACCESS_TOKEN)
$AuthorizationInfo = [System.Convert]::ToBase64String($EncodedACCESS_TOKEN)

# ЗАГОЛОВОК АВТОРИЗАЦИИ
$HEADERS = @{}
$HEADERS.Add("Authorization", "Basic $AuthorizationInfo")

# ПОЛУЧАЕМ ИНФОРМАЦИЮ О ТИКЕТЕ C САЙТА HF
$GET_JSON_RESPONSE_TICKET = Invoke-RestMethod -Method Get -Uri "$HF_ENDPOINT/api/1.1/json/ticket/$($ticket_id)" -Headers $HEADERS -ContentType "application/json"
#!!!!!!! $GET_JSON_RESPONSE_TICKET.updates.timestamp

### БЕРЁМ САМОЕ ПЕРВОЕ ВРЕМЯ, КОГДА БЫЛ СОЗДАН ТИКЕТ
$START_TIME_TICKET = $GET_JSON_RESPONSE_TICKET.updates.timestamp[0]

### ПРОХОДИМСЯ ПО КАЖДОМУ ИЗ ЦИКЛОВ ВРЕМЕНИ
foreach ($CHANGE in $GET_JSON_RESPONSE_TICKET.updates){
    ### НАХОДИМ КОГДА БЫЛО ПРОИЗВЕДЕННО ИЗМЕНЕНИЕ СО СТАТУСА NEW
    if ($CHANGE.status_change.old_name -cmatch "New") {
        $END_TIME_TICKET = $CHANGE.timestamp
        break
    }
    elseif ($CHANGE.status_change.old_name -cmatch "In work") {
        break
    }
}

### КОНВЕРТИРУЕМ НАШ СТРИНГ В ФОРМАТ ОБЪЕТА
$START_TIME_TICKET = [datetime]$START_TIME_TICKET
$END_TIME_TICKET = [datetime]$END_TIME_TICKET

### ДОБАВЛЯЕМ +3 ЧАСА К ВРЕМЕНИ, ТАК КАК НА СЕРВЕРЕ HF -3 ЧАСА
$START_TIME_TICKET = $START_TIME_TICKET.AddHours(3)
$END_TIME_TICKET = $END_TIME_TICKET.AddHours(3)

### ЗАПИШЕМ КОГДА СТАРТ ВРЕМЕНИ РАБОТЫ И КОНЕЦ
$START_TIME = New-TimeSpan -Hours 9
$END_TIME = New-TimeSpan -Hours 19

### ПОСЧИТАЕМ ВРЕМЯ ПЕРВОГО ОТВЕТА 
$FIRST_RESPONSE_TIME = Get-TimeWork -stt $START_TIME_TICKET -ett $END_TIME_TICKET -start $START_TIME -end $END_TIME

$AVERAGE_RESPONSE_TIME = $null
$SCORE_TICKET_RESPONSE = $null
$FULL_AVERAGE_RESPONSE_TIME = $null
$SLA_TICKET_TIME = $null
$FINAL_STAFF_RESPONSE_TIME = $null

### ПОСЧИТАЕМ ВРЕМЯ ЗАТРАЧЕННОЕ НА ТИКЕТ
foreach ($STATUS_CHANGE in $GET_JSON_RESPONSE_TICKET.updates){
    ### ЕСЛИ БЫЛ СДЕЛАН Private note, ТО ПРОПУСТИМ ВЕСЬ МАССИВ ПРОВЕРКИ
    if ($STATUS_CHANGE.message.message_type -cmatch "p" ) {
        continue
    }
    ### ЕСЛИ ЗАПУСКАЛСЯ СЧЁТЧИК SLA, ТО СОЗДАДИМ АРГУМЕНТ С ВРЕМЕНЕМ КОГДА ОН НАЧАЛСЯ
    if (($STATUS_CHANGE.status_change.new_name -cmatch "In work") -or ($STATUS_CHANGE.status_change.new_name -cmatch "In Progress") -and ($null -eq $START_SLA_TIME)) {
        $START_SLA_TIME = $STATUS_CHANGE.timestamp
        $START_SLA_TIME = [datetime]$START_SLA_TIME
        $START_SLA_TIME = $START_SLA_TIME.AddHours(3)
    }
    ### ЕСЛИ В ТИКЕТЕ ИЗМЕНИЛСЯ СТАТУС И СЧЁТЧИК SLA ОСТАНОВИЛСЯ, ТО СОЗДАДИМ АРГУМЕНТ С ВРЕМЕНЕМ КОГДА БЫЛ ОСТАНОВЛЕН SLA
    elseif (($STATUS_CHANGE.status_change.old_name -cmatch "In work") -or ($STATUS_CHANGE.status_change.old_name -cmatch "In Progress")) {
        if ((($STATUS_CHANGE.status_change.old_name -cmatch "In Progress") -and ($STATUS_CHANGE.status_change.new_name -cmatch "In work")) -or (($STATUS_CHANGE.status_change.old_name -cmatch "In work") -and ($STATUS_CHANGE.status_change.new_name -cmatch "In Progress"))) {
        }
        else {
            $STOP_SLA_TIME = $STATUS_CHANGE.timestamp
            $STOP_SLA_TIME = [datetime]$STOP_SLA_TIME
            $STOP_SLA_TIME = $STOP_SLA_TIME.AddHours(3)
            
            ### ПОПРОБУЕМ ПОСЧИТАТЬ ВРЕМЯ SLA
            try {
                ### ПОСЧИТАЕМ ВРЕМЯ ПО НАШЕЙ ФОРМУЛЕ
                $RESPONSE_TIME = Get-TimeWork -stt $START_SLA_TIME -ett $STOP_SLA_TIME -start $START_TIME -end $END_TIME
    
                ### СЛОЖИМ НАШЕ ПОЛУЧЕНОЕ ВРЕМЯ С УЖЕ ИМЕЮЩИМСЯ
                $SLA_TICKET_TIME += $RESPONSE_TIME
            }
            ### ЕСЛИ ОШИБКА ПОДСЧЁТА ВРЕМЕНИ, ЗАПИШЕМ
            catch {
            }
            ### ПРОВЕРЯЕМ ЗАПОЛНЕН ЛИ АРГУМЕНТ С ПРОМЕЖУТОЧНЫМ ОТВЕТОМ КЛИЕНТУ
            if ($FINAL_STAFF_RESPONSE_TIME) {
            }
            ### ЕСЛИ КЛИЕНТУ ПРОМЕЖУТОЧНЫЙ ОТВЕТ НЕ ДАВАЛИ, ТО ЗАПИШЕМ ЭТО ВРЕМЯ В АРГУМЕНТ
            else {
                $AVERAGE_RESPONSE_TIME += $RESPONSE_TIME
            }
            ### ПЕРЕСОЗДАДИМ ПУСТОЙ АРГУМЕНТ ВРЕМЕНИ ОТВЕТА КЛИЕНТУ, ЧТОБЫ ОН НЕНАЛОЖИЛСЯ НА ПРОШЛЫЙ
            $FINAL_STAFF_RESPONSE_TIME = $null
            ### ТАК КАК СТОП SLA БЫЛ, ТО И АРГУМЕНТ СТАРТ SLA НАМ УЖЕ НЕ НУЖЕН, ПОЭТОМУ СБРОСИМ ЕГО
            $START_SLA_TIME = $null
        }
    }
    ### ПОСЧИТАЕМ КОЛИЧЕСТВО ОТВЕТОВ СО СТОРОНЫ САППОРТА В ТИКЕТЕ
    if (($STATUS_CHANGE.by.type -cmatch "staff") -and ($null -ne $STATUS_CHANGE.message)) {
        $SCORE_TICKET_RESPONSE += 1
        ### ЕСЛИ ОТВЕТ БЫЛ ДАН БЕЗ ИЗМЕНЕНИЯ ДЕФОЛТНОГО СТАТУСА "In Progress"
        if ($null -eq $FINAL_STAFF_RESPONSE_TIME) {
            ### ПРОВЕРИМ, ЧТО АРГУМЕНТ СТАРТА SLA ЗАПОЛНЕН
            if ($null -ne $START_SLA_TIME) {
                ### ПРОВЕРИМ, ЧТО НЕ БЫЛО ПРОИЗВЕДЕНО ИЗМЕНЕНИЕ СТАТУСА ИЛИ ЕСЛИ БЫЛ ДАН ОТВЕТ С ИЗМЕНЕНИЕМ СТАТУСА ИЗ ДЕФОЛТНОГО "In Progress" НА ВНУТРЕННИЙ "In work"
                if (($null -eq $STATUS_CHANGE.status_change) -or (($STATUS_CHANGE.status_change.old_name -cmatch "In Progress") -and ($STATUS_CHANGE.status_change.new_name -cmatch "In work"))) {
                    ### ПРЕОБРАЗУЕМ ПОЛУЧЕННОЕ ВРЕМЯ В АРГУМЕНТ, ПРИВЕДЁМ ЕГО К ФОРМАТУ ДАТЫ И ВРЕМЕНИ, А ТАКЖЕ ДОБАВИМ +3 ЧАСА
                    $STAFF_RESPONSE_TIME = $STATUS_CHANGE.timestamp
                    $STAFF_RESPONSE_TIME = [datetime]$STAFF_RESPONSE_TIME
                    $STAFF_RESPONSE_TIME = $STAFF_RESPONSE_TIME.AddHours(3)
                    ### ПОПРОБУЕМ ПОСЧИТАТЬ ВРЕМЯ ПЕРВОГО ОТВЕТА
                    try {
                        ### ПОСЧИТАЕМ ВРЕМЯ ПО НАШЕЙ ФОРМУЛЕ
                        $FINAL_STAFF_RESPONSE_TIME = Get-TimeWork -stt $START_SLA_TIME -ett $STAFF_RESPONSE_TIME -start $START_TIME -end $END_TIME
                        $AVERAGE_RESPONSE_TIME += $FINAL_STAFF_RESPONSE_TIME
                    }
                    ### ЕСЛИ ОШИБКА ПОДСЧЁТА ВРЕМЕНИ ОТВЕТА, ЗАПИШЕМ
                    catch {
                    }
                }
            }
        }
    }
}

### ПРОВЕРИМ, НАХОДИТСЯ ЛИ ТИКЕТ ЕЩЁ В РАБОТЕ
if (($GET_JSON_RESPONSE_TICKET.status.name -cmatch "In Progress") -or ($GET_JSON_RESPONSE_TICKET.status.name -cmatch "In Work")) {
    $SLA_TIME = $GET_JSON_RESPONSE_TICKET.last_updated_at
    $SLA_TIME = [datetime]$SLA_TIME
    $SLA_TIME = $SLA_TIME.AddHours(3)
    $NOW = Get-Date

    ### ПОСЧИТАЕМ ВРЕМЯ SLA ДЛЯ ТИКЕТА С ИДУЩИМ ВРЕМЕНЕМ SLA
    $SLA_RESPONSE_TIME = Get-TimeWork -stt $SLA_TIME -ett $NOW -start $START_TIME -end $END_TIME

    ### ПРОВЕРИМ, ЧЕЙ БЫЛ ПОСЛЕДНИЙ ОТВЕТ, ЕСЛИ ОТВЕТ БЫЛ ПОСЛЕДНИЙ ОТ КЛИЕНТА, А НЕ ОТ САППОРТА, ЗАПИШЕМ ВРЕМЯ БЕЗ ОТВЕТА
    if ($GET_JSON_RESPONSE_TICKET.unresponded) {
        $NO_RESPONSE_TIME = Get-TimeWork -stt $SLA_TIME -ett $NOW -start $START_TIME -end $END_TIME
        ### СЛОЖИМ ВРЕМЯ БЕЗ ОТВЕТА С УЖЕ ИМЕЮЩИМСЯ
        $SLA_TICKET_TIME += $NO_RESPONSE_TIME
    }
    else {
        $RESPONSE = $GET_JSON_RESPONSE_TICKET.last_staff_reply_at
        $RESPONSE = [datetime]$RESPONSE
        $RESPONSE = $RESPONSE.AddHours(3)
    }

    ### СЛОЖИМ ВРЕМЯ, ЕСЛИ ТИКЕТ ЕЩЁ В РАБОТЕ
    $SLA_TICKET_TIME += $SLA_RESPONSE_TIME
    
}

### ДОБАВИМ К ОБЩЕМУ ИТОГУ РАБОТЫ НАД ТИКЕТОМ ПЕРВЫЙ ОТВЕТ И ПОЛУЧИМ ОБЩЕЕ ВРЕМЯ РАБОТЫ НАД ТИКЕТОМ
$SLA_TICKET_TIME += $FIRST_RESPONSE_TIME
$FULL_AVERAGE_RESPONSE_TIME += $FIRST_RESPONSE_TIME
$FULL_AVERAGE_RESPONSE_TIME += $AVERAGE_RESPONSE_TIME

Write-Host -ForegroundColor Red $SLA_TICKET_TIME
