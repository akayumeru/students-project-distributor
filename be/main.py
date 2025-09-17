from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import csv
from io import StringIO
from typing import List, Dict

from fastapi.responses import JSONResponse

from processor import TeamProcessor
from tsv_validator import validate_tsv

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
    if not file.filename.endswith(('.tsv', '.csv')):
        raise HTTPException(status_code=400, detail="Файл должен быть в формате TSV")

    try:
        # Читаем содержимое файла
        contents = await file.read()
        content_str = contents.decode('utf-8')

        validation_result = validate_tsv(content_str)

        if not validation_result["ok"]:
            return JSONResponse(status_code=422, content=validation_result)

        # Парсим TSV
        tsv_reader = csv.DictReader(StringIO(content_str), delimiter='\t')
        rows: List[Dict] = [row for row in tsv_reader]

        # Здесь можно добавить обработку данных
        # Обрабатываем данные
        processor = TeamProcessor()
        result = processor.process_teams(rows)

        return {
            "result": result,
            "rows_processed": len(rows),
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
