# Bot_tg

Дефолтно билдим образ командой: 
- docker build -t hf_bot_tg .

Создаём и запускаем контейнер с мапингом логов на локал машину командой: 
- docker run -d -e TZ=Europe/Moscow --name hf_bot -p 3030:3030 -v $(pwd)/logs:/app/logs -v prod_hf_bot_tg:/app hf_bot_tg
