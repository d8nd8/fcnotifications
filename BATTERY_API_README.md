# API для работы с отчетами о батарее

## Обзор

Теперь у вас есть полный API для работы с отчетами о батарее:
- **Отправка отчетов** - `POST /api/mobile/battery`
- **Получение отчетов** - `GET /api/mobile/battery/list`

## 1. Отправка отчета о батарее

### Endpoint
```
POST /api/mobile/battery
```

### Заголовки
```
X-TOKEN: <токен_устройства>
Content-Type: application/json
```

### Тело запроса
```json
{
    "battery_level": 85,
    "date_created": "2024-01-15T14:30:25Z"  // опционально
}
```

### Ответ
```json
{
    "id": "550e8400-e29b-41d4-a716-446655440001",
    "message": "Отчет о батарее успешно создан"
}
```

### Пример использования
```bash
curl -X POST http://localhost:8000/api/mobile/battery \
  -H "X-TOKEN: 6f4d3982-2a0c-460b-95d6-7daaaf2b6f39" \
  -H "Content-Type: application/json" \
  -d '{"battery_level": 75}'
```

## 2. Получение отчетов о батарее

### Endpoint
```
GET /api/mobile/battery/list
```

### Заголовки
```
X-TOKEN: <токен_устройства>
```

### Параметры запроса
- `limit` - максимальное количество отчетов (по умолчанию: 50, максимум: 100)
- `offset` - смещение для пагинации (по умолчанию: 0)
- `days` - количество дней назад для фильтрации (по умолчанию: 30)

### Ответ
```json
{
    "count": 25,
    "results": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440001",
            "battery_level": 85,
            "date_created": "2024-01-15T14:30:25Z",
            "created_at": "2024-01-15T14:30:25Z",
            "device_name": "Мой iPhone",
            "device_token": "6f4d3982-2a0c-460b-95d6-7daaaf2b6f39"
        }
    ]
}
```

### Примеры использования

#### Получить последние 10 отчетов
```bash
curl -X GET "http://localhost:8000/api/mobile/battery/list?limit=10" \
  -H "X-TOKEN: 6f4d3982-2a0c-460b-95d6-7daaaf2b6f39"
```

#### Получить отчеты за последние 7 дней
```bash
curl -X GET "http://localhost:8000/api/mobile/battery/list?days=7" \
  -H "X-TOKEN: 6f4d3982-2a0c-460b-95d6-7daaaf2b6f39"
```

#### Пагинация - получить следующую страницу
```bash
curl -X GET "http://localhost:8000/api/mobile/battery/list?limit=10&offset=10" \
  -H "X-TOKEN: 6f4d3982-2a0c-460b-95d6-7daaaf2b6f39"
```

## 3. Команды для тестирования

### Создание тестовых данных
```bash
# Создать по 3 отчета для всех устройств
python manage.py test_battery_reports --count=3

# Создать 10 отчетов для конкретного устройства
python manage.py test_battery_reports --count=10 --device-id=550e8400-e29b-41d4-a716-446655440000
```

### Тестирование API
```bash
# Тестировать получение отчетов
python manage.py test_battery_api --limit=5 --days=30

# Тестировать отправку отчетов
python manage.py simulate_battery_api --count=5 --interval=10
```

### Проверка статуса устройств
```bash
# Показать статистику устройств
python manage.py update_device_status --show-details

# Показать статистику с порогом 12 часов
python manage.py update_device_status --hours=12 --show-details
```

## 4. Интеграция в мобильное приложение

### Отправка отчета о батарее (Android/Kotlin)
```kotlin
fun sendBatteryReport(batteryLevel: Int, deviceToken: String) {
    val client = OkHttpClient()
    val json = JSONObject().apply {
        put("battery_level", batteryLevel)
    }
    
    val request = Request.Builder()
        .url("http://your-server.com/api/mobile/battery")
        .post(json.toString().toRequestBody("application/json".toMediaType()))
        .addHeader("X-TOKEN", deviceToken)
        .build()
    
    client.newCall(request).enqueue(object : Callback {
        override fun onResponse(call: Call, response: Response) {
            if (response.isSuccessful) {
                println("Battery report sent successfully")
            }
        }
        override fun onFailure(call: Call, e: IOException) {
            println("Failed to send battery report: ${e.message}")
        }
    })
}
```

### Получение отчетов о батарее (Android/Kotlin)
```kotlin
fun getBatteryReports(deviceToken: String, limit: Int = 50) {
    val client = OkHttpClient()
    val request = Request.Builder()
        .url("http://your-server.com/api/mobile/battery/list?limit=$limit")
        .addHeader("X-TOKEN", deviceToken)
        .build()
    
    client.newCall(request).enqueue(object : Callback {
        override fun onResponse(call: Call, response: Response) {
            if (response.isSuccessful) {
                val json = JSONObject(response.body?.string())
                val count = json.getInt("count")
                val results = json.getJSONArray("results")
                
                for (i in 0 until results.length()) {
                    val report = results.getJSONObject(i)
                    val batteryLevel = report.getInt("battery_level")
                    val dateCreated = report.getString("date_created")
                    println("Battery: $batteryLevel% at $dateCreated")
                }
            }
        }
        override fun onFailure(call: Call, e: IOException) {
            println("Failed to get battery reports: ${e.message}")
        }
    })
}
```

### Отправка отчета о батарее (iOS/Swift)
```swift
func sendBatteryReport(batteryLevel: Int, deviceToken: String) {
    let url = URL(string: "http://your-server.com/api/mobile/battery")!
    var request = URLRequest(url: url)
    request.httpMethod = "POST"
    request.setValue("application/json", forHTTPHeaderField: "Content-Type")
    request.setValue(deviceToken, forHTTPHeaderField: "X-TOKEN")
    
    let json = ["battery_level": batteryLevel]
    request.httpBody = try? JSONSerialization.data(withJSONObject: json)
    
    URLSession.shared.dataTask(with: request) { data, response, error in
        if let error = error {
            print("Error: \(error)")
        } else if let data = data {
            print("Response: \(String(data: data, encoding: .utf8) ?? "")")
        }
    }.resume()
}
```

## 5. Мониторинг и администрирование

### В админке Django
- Откройте http://localhost:8000/admin/
- Перейдите в раздел "Battery reports" для просмотра всех отчетов
- Используйте фильтры по дате, уровню батареи и устройству

### В Swagger UI
- Откройте http://localhost:8000/api/docs/
- Найдите раздел "Мониторинг батареи"
- Протестируйте API endpoints интерактивно

### Статистика в дашборде
- Общее количество устройств
- Количество онлайн устройств (активных за последние 24 часа)
- Количество устройств с низким зарядом батареи (< 20%)
- Последние отчеты о батарее

## 6. Обработка ошибок

### Коды ответов
- `200` - Успешное получение данных
- `201` - Успешное создание отчета
- `400` - Ошибка валидации данных
- `401` - Неверный или отсутствующий токен
- `404` - Ресурс не найден
- `500` - Внутренняя ошибка сервера

### Примеры ошибок
```json
// 400 - Неверный уровень батареи
{
    "battery_level": ["Уровень батареи должен быть от 0 до 100"]
}

// 401 - Неверный токен
{
    "detail": "Authentication credentials were not provided."
}
```

## 7. Рекомендации по использованию

### Частота отправки отчетов
- **Рекомендуется**: каждые 15-30 минут
- **Минимум**: каждые 2 часа для keep-alive
- **Максимум**: не чаще чем каждые 5 минут

### Оптимизация
- Используйте пагинацию для больших объемов данных
- Фильтруйте по дням для получения актуальных данных
- Кэшируйте данные на клиенте для уменьшения запросов

### Безопасность
- Храните токены устройств в безопасном месте
- Используйте HTTPS в продакшене
- Регулярно обновляйте токены устройств
