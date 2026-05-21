# BrandProposAI RU — информационная система для курсового проекта

Проект реализует прототип ИС формирования коммерческих предложений:

- фронтенд: `static/1.html` и `static/2.html`;
- бэкенд: Python + FastAPI;
- хранение истории генераций: SQLite (`data/app.db`);
- редактируемый документ: блок `contenteditable` на второй странице;
- экспорт результата: DOCX и PDF;
- внешний вид итогового DOCX приближен к примеру `РЦ_Коммерческое_предложение_ВятГУ_стенд.doc`.

## Как запустить

```bash
cd brandproposai_project
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Откройте в браузере:

```text
http://127.0.0.1:8000/1.html
```

После заполнения формы на первой странице нажмите «Сгенерировать коммерческое предложение». Система отправит данные на Python-бэкенд и автоматически откроет `2.html` с редактируемым документом.

## Структура

```text
brandproposai_project/
├── main.py                         # FastAPI-приложение и REST API
├── requirements.txt
├── README.md
├── data/                           # SQLite создаётся автоматически
├── generated_docs/                 # DOCX/PDF экспорты
├── services/
│   └── document_service.py         # генерация HTML, DOCX и PDF
└── static/
    ├── 1.html                      # первая страница
    ├── 2.html                      # редактирование и экспорт
    ├── logo-header.png
    └── logo.png
```

## API

- `POST /api/generate` — создаёт коммерческое предложение и возвращает ID;
- `GET /api/proposals/{id}` — возвращает сохранённое предложение;
- `POST /api/proposals/{id}` — сохраняет правки из редактора;
- `POST /api/export/docx` — экспортирует редактируемый документ в DOCX;
- `POST /api/export/pdf` — экспортирует редактируемый документ в PDF.

