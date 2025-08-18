from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
from io import StringIO
from typing import List, Dict

app = FastAPI()

# Настройка CORS (для разработки)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене укажите конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/student-projects/assign")
async def assign_student_projects(file: UploadFile = File(...)):
    # Проверяем, что файл TSV
    if not file.filename.endswith('.tsv'):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате TSV")

    try:
        # Читаем содержимое файла
        contents = await file.read()
        content_str = contents.decode('utf-8')

        # Парсим TSV
        tsv_reader = csv.DictReader(StringIO(content_str), delimiter='\t')
        rows: List[Dict] = [row for row in tsv_reader]

        # Здесь можно добавить обработку данных
        # Обрабатываем данные
        processor = TeamProcessor()
        result = processor.process_teams(rows)

        return {
            "filename": file.filename,
            "content_type": file.content_type,
            "rows_count": len(rows),
            "first_row": rows[0] if rows else None,
            "detail": "Файл успешно обработан"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке файла: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
