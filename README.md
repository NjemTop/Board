# Bot_tg

Дефолтно билдим образ командой: 
- docker build -t hf_bot_tg .

Создаём и запускаем контейнер с мапингом логов на локал машину командой: 
- docker run -d --rm -e TZ=Europe/Moscow --name bot_tg -p 3030:3030 -v $(pwd)/logs:/app/logs hf_bot_tg
