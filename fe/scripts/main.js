// DOM элементы
const fileInput = document.getElementById('file-input');
const selectFileBtn = document.getElementById('select-file-btn');
const uploadBtn = document.getElementById('upload-btn');
const fileNameDisplay = document.getElementById('file-name');
const responseDiv = document.getElementById('response');

// Текущий выбранный файл
let selectedFile = null;

// Обработчик клика по кнопке выбора файла
selectFileBtn.addEventListener('click', () => {
    fileInput.click();
});

// Обработчик изменения выбранного файла
fileInput.addEventListener('change', (event) => {
    selectedFile = event.target.files[0];
    updateFileDisplay();
});

// Обновление отображения информации о файле
function updateFileDisplay() {
    if (selectedFile) {
        fileNameDisplay.textContent = `Выбран файл: ${selectedFile.name}`;
        fileNameDisplay.style.color = '#4CAF50';
        uploadBtn.disabled = false;
    } else {
        fileNameDisplay.textContent = 'Файл не выбран';
        fileNameDisplay.style.color = '#666';
        uploadBtn.disabled = true;
    }
}

// Отправка файла на сервер
uploadBtn.addEventListener('click', async () => {
    if (!selectedFile) return;

    // Показываем индикатор загрузки
    uploadBtn.disabled = true;
    uploadBtn.textContent = 'Отправка...';
    responseDiv.textContent = '';
    responseDiv.className = '';

    try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        // Отправляем файл на сервер
        const response = await fetch('http://localhost:8000/api/student-projects/assign', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Ошибка сервера: ${response.status}`);
        }

        const result = await response.json();

        // Успешная обработка
        responseDiv.className = 'success';
        responseDiv.innerHTML = `
            <strong>Файл успешно загружен!</strong><br>
            Имя файла: ${result.filename}<br>
            Тип: ${result.content_type}<br>
            Строк: ${result.rows_count}<br>
            <details>
                <summary>Первая строка данных:</summary>
                <pre>${JSON.stringify(result.first_row, null, 2)}</pre>
            </details>
        `;
    } catch (error) {
        // Обработка ошибок
        responseDiv.className = 'error';
        responseDiv.textContent = `Ошибка при загрузке: ${error.message}`;
        console.error('Ошибка:', error);
    } finally {
        // Восстанавливаем состояние кнопки
        uploadBtn.disabled = false;
        uploadBtn.textContent = 'Отправить на сервер';
    }
});

// Drag and Drop функциональность
document.addEventListener('DOMContentLoaded', () => {
    const uploadContainer = document.querySelector('.upload-container');

    uploadContainer.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadContainer.style.borderColor = '#4CAF50';
        uploadContainer.style.backgroundColor = '#f0fff0';
    });

    uploadContainer.addEventListener('dragleave', () => {
        uploadContainer.style.borderColor = '#ccc';
        uploadContainer.style.backgroundColor = '';
    });

    uploadContainer.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadContainer.style.borderColor = '#ccc';
        uploadContainer.style.backgroundColor = '';

        if (e.dataTransfer.files.length) {
            fileInput.files = e.dataTransfer.files;
            selectedFile = e.dataTransfer.files[0];
            updateFileDisplay();
        }
    });
});
