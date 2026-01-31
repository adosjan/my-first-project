# Скрипт для автоматической организации скриншотов по датам
# Автор: adosjan

# Путь к папке со скриншотами на рабочем столе
$screenshotsFolder = "$env:USERPROFILE\Desktop\скрин"

# Проверяем, существует ли папка
if (-not (Test-Path $screenshotsFolder)) {
    Write-Host "Ошибка: Папка 'скрин' не найдена на рабочем столе!" -ForegroundColor Red
    Write-Host "Создаю папку..." -ForegroundColor Yellow
    New-Item -Path $screenshotsFolder -ItemType Directory | Out-Null
    Write-Host "Папка создана: $screenshotsFolder" -ForegroundColor Green
}

Write-Host "Мониторинг папки: $screenshotsFolder" -ForegroundColor Cyan
Write-Host "Скриншоты будут автоматически перемещаться в папки по датам" -ForegroundColor Cyan
Write-Host "Нажмите Ctrl+C для остановки" -ForegroundColor Yellow
Write-Host ""

# Создаём наблюдатель за файловой системой
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $screenshotsFolder
$watcher.Filter = "*.*"
$watcher.IncludeSubdirectories = $false
$watcher.EnableRaisingEvents = $true

# Функция для перемещения файла в папку с датой
function Move-ToDateFolder {
    param($filePath)

    Start-Sleep -Milliseconds 500  # Небольшая задержка, чтобы файл полностью записался

    if (-not (Test-Path $filePath)) {
        return
    }

    # Получаем дату создания файла
    $file = Get-Item $filePath
    $dateFolder = $file.CreationTime.ToString("yyyy-MM-dd")

    # Создаём папку с датой, если её нет
    $targetFolder = Join-Path $screenshotsFolder $dateFolder
    if (-not (Test-Path $targetFolder)) {
        New-Item -Path $targetFolder -ItemType Directory | Out-Null
        Write-Host "Создана папка: $dateFolder" -ForegroundColor Green
    }

    # Перемещаем файл
    $targetPath = Join-Path $targetFolder $file.Name

    # Если файл с таким именем уже существует, добавляем номер
    $counter = 1
    while (Test-Path $targetPath) {
        $nameWithoutExt = [System.IO.Path]::GetFileNameWithoutExtension($file.Name)
        $extension = $file.Extension
        $targetPath = Join-Path $targetFolder "$nameWithoutExt`_$counter$extension"
        $counter++
    }

    try {
        Move-Item -Path $filePath -Destination $targetPath -Force
        Write-Host "Перемещён: $($file.Name) -> $dateFolder\" -ForegroundColor Green
    } catch {
        Write-Host "Ошибка при перемещении файла: $_" -ForegroundColor Red
    }
}

# Обработчик события создания нового файла
$action = {
    $path = $Event.SourceEventArgs.FullPath
    $name = $Event.SourceEventArgs.Name

    # Проверяем, что это файл, а не папка
    if (Test-Path $path -PathType Leaf) {
        Move-ToDateFolder -filePath $path
    }
}

# Регистрируем обработчик события
Register-ObjectEvent -InputObject $watcher -EventName "Created" -Action $action | Out-Null

# Также организуем существующие файлы в корне папки
Write-Host "Проверяю существующие файлы..." -ForegroundColor Cyan
$existingFiles = Get-ChildItem -Path $screenshotsFolder -File
foreach ($file in $existingFiles) {
    Move-ToDateFolder -filePath $file.FullName
}

if ($existingFiles.Count -eq 0) {
    Write-Host "Существующих файлов не найдено" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Готово! Жду новые скриншоты..." -ForegroundColor Green

# Бесконечный цикл для поддержания работы скрипта
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    # Очистка при завершении
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Write-Host "Мониторинг остановлен" -ForegroundColor Yellow
}
