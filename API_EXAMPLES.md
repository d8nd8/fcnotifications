# 📚 Примеры использования FC Phones API

## 🔐 Аутентификация

Все API запросы требуют заголовок `X-TOKEN` с токеном устройства:

```bash
curl -H "X-TOKEN: your-device-token-here" \
     -H "Content-Type: application/json" \
     https://your-domain.com/api/endpoint
```

## 📱 Получение информации об устройстве

### Запрос
```bash
curl -H "X-TOKEN: abc123def456ghi789" \
     -H "Content-Type: application/json" \
     https://your-domain.com/api/device
```

### Ответ
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "external_id": "device_12345",
  "token": "abc123def456ghi789",
  "name": "Мой iPhone",
  "last_seen": "2024-01-15T14:30:25Z",
  "created_at": "2024-01-01T10:00:00Z"
}
```

## 🔋 Отправка отчета о батарее

### Запрос
```bash
curl -X POST \
  -H "X-TOKEN: abc123def456ghi789" \
  -H "Content-Type: application/json" \
  -d '{
    "battery_level": 85
  }' \
  https://your-domain.com/api/mobile/battery
```

### Ответ
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "Отчет о батарее успешно создан"
}
```

### Запрос с указанием времени
```bash
curl -X POST \
  -H "X-TOKEN: abc123def456ghi789" \
  -H "Content-Type: application/json" \
  -d '{
    "battery_level": 75,
    "date_created": "2024-01-15T14:30:25Z"
  }' \
  https://your-domain.com/api/mobile/battery
```

## 🚨 Отправка экстренного сообщения

### Запрос
```bash
curl -X POST \
  -H "X-TOKEN: abc123def456ghi789" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Иван Петров",
    "text": "Помогите! Застрял в лифте на 5 этаже!"
  }' \
  https://your-domain.com/api/mobile/message
```

### Ответ
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440002",
  "message": "Сообщение успешно отправлено"
}
```

### Запрос с указанием времени
```bash
curl -X POST \
  -H "X-TOKEN: abc123def456ghi789" \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Мария Сидорова",
    "text": "Срочно нужна помощь! Попал в аварию на трассе М4",
    "date_created": "2024-01-15T14:30:25Z"
  }' \
  https://your-domain.com/api/mobile/message
```

## 📱 Примеры для мобильных приложений

### JavaScript/React Native
```javascript
const API_BASE_URL = 'https://your-domain.com/api';
const DEVICE_TOKEN = 'your-device-token-here';

// Получение информации об устройстве
async function getDeviceInfo() {
  try {
    const response = await fetch(`${API_BASE_URL}/device`, {
      method: 'GET',
      headers: {
        'X-TOKEN': DEVICE_TOKEN,
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log('Device info:', data);
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
}

// Отправка отчета о батарее
async function sendBatteryReport(batteryLevel) {
  try {
    const response = await fetch(`${API_BASE_URL}/mobile/battery`, {
      method: 'POST',
      headers: {
        'X-TOKEN': DEVICE_TOKEN,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        battery_level: batteryLevel
      })
    });
    
    const data = await response.json();
    console.log('Battery report sent:', data);
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
}

// Отправка экстренного сообщения
async function sendEmergencyMessage(sender, message) {
  try {
    const response = await fetch(`${API_BASE_URL}/mobile/message`, {
      method: 'POST',
      headers: {
        'X-TOKEN': DEVICE_TOKEN,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        sender: sender,
        text: message
      })
    });
    
    const data = await response.json();
    console.log('Emergency message sent:', data);
    return data;
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### Python
```python
import requests
import json

API_BASE_URL = 'https://your-domain.com/api'
DEVICE_TOKEN = 'your-device-token-here'

headers = {
    'X-TOKEN': DEVICE_TOKEN,
    'Content-Type': 'application/json'
}

# Получение информации об устройстве
def get_device_info():
    response = requests.get(f'{API_BASE_URL}/device', headers=headers)
    return response.json()

# Отправка отчета о батарее
def send_battery_report(battery_level):
    data = {'battery_level': battery_level}
    response = requests.post(f'{API_BASE_URL}/mobile/battery', 
                           headers=headers, 
                           data=json.dumps(data))
    return response.json()

# Отправка экстренного сообщения
def send_emergency_message(sender, text):
    data = {'sender': sender, 'text': text}
    response = requests.post(f'{API_BASE_URL}/mobile/message', 
                           headers=headers, 
                           data=json.dumps(data))
    return response.json()

# Примеры использования
if __name__ == '__main__':
    # Получить информацию об устройстве
    device_info = get_device_info()
    print(f"Device: {device_info['name']}")
    
    # Отправить отчет о батарее
    battery_result = send_battery_report(85)
    print(f"Battery report: {battery_result['message']}")
    
    # Отправить экстренное сообщение
    message_result = send_emergency_message(
        "Иван Петров", 
        "Помогите! Застрял в лифте!"
    )
    print(f"Emergency message: {message_result['message']}")
```

### Swift/iOS
```swift
import Foundation

class FCPhonesAPI {
    private let baseURL = "https://your-domain.com/api"
    private let deviceToken = "your-device-token-here"
    
    private func makeRequest(endpoint: String, method: String, body: Data? = nil) -> URLRequest? {
        guard let url = URL(string: "\(baseURL)\(endpoint)") else { return nil }
        
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue(deviceToken, forHTTPHeaderField: "X-TOKEN")
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = body
        
        return request
    }
    
    func getDeviceInfo(completion: @escaping (Result<[String: Any], Error>) -> Void) {
        guard let request = makeRequest(endpoint: "/device", method: "GET") else {
            completion(.failure(NSError(domain: "Invalid URL", code: 0)))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                completion(.success(json ?? [:]))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func sendBatteryReport(batteryLevel: Int, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let body = ["battery_level": batteryLevel]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: body),
              let request = makeRequest(endpoint: "/mobile/battery", method: "POST", body: jsonData) else {
            completion(.failure(NSError(domain: "Invalid request", code: 0)))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                completion(.success(json ?? [:]))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
    
    func sendEmergencyMessage(sender: String, text: String, completion: @escaping (Result<[String: Any], Error>) -> Void) {
        let body = ["sender": sender, "text": text]
        
        guard let jsonData = try? JSONSerialization.data(withJSONObject: body),
              let request = makeRequest(endpoint: "/mobile/message", method: "POST", body: jsonData) else {
            completion(.failure(NSError(domain: "Invalid request", code: 0)))
            return
        }
        
        URLSession.shared.dataTask(with: request) { data, response, error in
            if let error = error {
                completion(.failure(error))
                return
            }
            
            guard let data = data else { return }
            
            do {
                let json = try JSONSerialization.jsonObject(with: data) as? [String: Any]
                completion(.success(json ?? [:]))
            } catch {
                completion(.failure(error))
            }
        }.resume()
    }
}

// Пример использования
let api = FCPhonesAPI()

// Получить информацию об устройстве
api.getDeviceInfo { result in
    switch result {
    case .success(let deviceInfo):
        print("Device: \(deviceInfo["name"] ?? "Unknown")")
    case .failure(let error):
        print("Error: \(error)")
    }
}

// Отправить отчет о батарее
api.sendBatteryReport(batteryLevel: 85) { result in
    switch result {
    case .success(let response):
        print("Battery report: \(response["message"] ?? "Unknown")")
    case .failure(let error):
        print("Error: \(error)")
    }
}

// Отправить экстренное сообщение
api.sendEmergencyMessage(sender: "Иван Петров", text: "Помогите! Застрял в лифте!") { result in
    switch result {
    case .success(let response):
        print("Emergency message: \(response["message"] ?? "Unknown")")
    case .failure(let error):
        print("Error: \(error)")
    }
}
```

## 🔍 Коды ответов

| Код | Описание | Пример |
|-----|----------|--------|
| 200 | Успешный запрос | Получение информации об устройстве |
| 201 | Ресурс создан | Создание отчета о батарее или сообщения |
| 400 | Ошибка валидации | Неверные данные в запросе |
| 401 | Неверный токен | Отсутствует или неверный X-TOKEN |
| 500 | Внутренняя ошибка | Ошибка сервера |

## ⚠️ Обработка ошибок

### Ошибка валидации (400)
```json
{
  "battery_level": ["Уровень батареи должен быть от 0 до 100"]
}
```

### Ошибка аутентификации (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### Ошибка сервера (500)
```json
{
  "error": "Internal server error"
}
```

## 📝 Примечания

1. **Токен устройства** получается при создании устройства через админку Django
2. **Все даты** должны быть в формате ISO 8601 (например: `2024-01-15T14:30:25Z`)
3. **Keep-alive** - рекомендуется отправлять отчеты о батарее каждые 5-10 минут
4. **Экстренные сообщения** автоматически отправляются в Telegram администратору
5. **Rate limiting** - избегайте слишком частых запросов (рекомендуется не чаще 1 раза в секунду)
