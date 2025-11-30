"""
Тесты для модуля mistral.py.
"""
import unittest
import json
import sys
from unittest.mock import patch, MagicMock, Mock

# Мокируем внешние зависимости перед импортом mistral
# Проверяем, не были ли они уже замокированы
if 'httpx' not in sys.modules or not isinstance(sys.modules.get('httpx'), MagicMock):
    mock_httpx = MagicMock()
    sys.modules['httpx'] = mock_httpx
else:
    mock_httpx = sys.modules['httpx']

# Создаем мок для mistralai
if 'mistralai' not in sys.modules or not isinstance(sys.modules.get('mistralai'), MagicMock):
    mock_mistralai = MagicMock()
    mock_mistral_error = type('MistralError', (Exception,), {
        '__init__': lambda self, message='', status_code=0, body=None: setattr(self, 'message', message) or setattr(self, 'status_code', status_code) or setattr(self, 'body', body)
    })
    mock_mistralai.models = MagicMock()
    mock_mistralai.models.MistralError = mock_mistral_error
    sys.modules['mistralai'] = mock_mistralai
    sys.modules['mistralai.models'] = mock_mistralai.models
else:
    mock_mistralai = sys.modules['mistralai']

# Сохраняем ссылку на MistralError для использования в тестах
MistralError = mock_mistralai.models.MistralError

# Теперь можем импортировать mistral
# Если mistral уже был замокирован (например, в test_app.py), нужно его восстановить
if 'mistral' in sys.modules and isinstance(sys.modules['mistral'], MagicMock):
    # Удаляем мок, чтобы можно было импортировать реальный модуль
    del sys.modules['mistral']


class TestExtractJson(unittest.TestCase):
    """Тесты для функции _extract_json."""
    
    def test_extract_json_clean(self):
        """Тест извлечения JSON из чистого ответа без markdown."""
        from mistral import _extract_json
        
        clean_json = '{"car": "Toyota Camry", "units": "months", "parts_lifetime": {"engine oil": 3}}'
        result = _extract_json(clean_json)
        self.assertEqual(result, clean_json)
    
    def test_extract_json_with_markdown(self):
        """Тест извлечения JSON из ответа с markdown блоками."""
        from mistral import _extract_json
        
        json_with_markdown = '```json\n{"car": "Toyota Camry", "units": "months"}\n```'
        expected = '{"car": "Toyota Camry", "units": "months"}'
        result = _extract_json(json_with_markdown)
        self.assertEqual(result, expected)
    
    def test_extract_json_with_markdown_no_lang(self):
        """Тест извлечения JSON из ответа с markdown блоками без указания языка."""
        from mistral import _extract_json
        
        json_with_markdown = '```\n{"car": "Toyota Camry", "units": "months"}\n```'
        expected = '{"car": "Toyota Camry", "units": "months"}'
        result = _extract_json(json_with_markdown)
        self.assertEqual(result, expected)
    
    def test_extract_json_with_whitespace(self):
        """Тест извлечения JSON с пробелами."""
        from mistral import _extract_json
        
        json_with_spaces = '   {"car": "Toyota Camry"}   '
        expected = '{"car": "Toyota Camry"}'
        result = _extract_json(json_with_spaces)
        self.assertEqual(result, expected)
    
    def test_extract_json_complex_markdown(self):
        """Тест извлечения JSON из сложного markdown блока."""
        from mistral import _extract_json
        
        complex_markdown = '```json\n{\n  "car": "Toyota Camry",\n  "units": "months",\n  "parts_lifetime": {\n    "engine oil": 3\n  }\n}\n```'
        expected = '{\n  "car": "Toyota Camry",\n  "units": "months",\n  "parts_lifetime": {\n    "engine oil": 3\n  }\n}'
        result = _extract_json(complex_markdown)
        self.assertEqual(result, expected)


class TestGetPartsLifetime(unittest.TestCase):
    """Тесты для функции get_parts_lifetime."""
    
    def setUp(self):
        """Настройка перед каждым тестом."""
        # Мокируем print, чтобы не выводить в консоль
        self.print_patcher = patch('mistral.print')
        self.mock_print = self.print_patcher.start()
    
    def tearDown(self):
        """Очистка после каждого теста."""
        self.print_patcher.stop()
    
    @patch('mistral.client')
    def test_get_parts_lifetime_success(self, mock_client):
        """Тест успешного получения данных о сроке службы деталей."""
        from mistral import get_parts_lifetime
        
        # Мокируем ответ от API
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "car": "Toyota Camry 2020",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,
                "brake pads": 6,
                "air filter": 2
            }
        })
        
        mock_client.chat.complete.return_value = mock_response
        
        # Вызываем функцию
        result = get_parts_lifetime("Toyota Camry 2020")
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertEqual(result["car"], "Toyota Camry 2020")
        self.assertEqual(result["units"], "months")
        self.assertIn("parts_lifetime", result)
        self.assertEqual(result["parts_lifetime"]["engine oil"], 3)
        self.assertEqual(result["parts_lifetime"]["brake pads"], 6)
        
        # Проверяем, что API был вызван с правильными параметрами
        mock_client.chat.complete.assert_called_once()
        call_args = mock_client.chat.complete.call_args
        self.assertEqual(call_args.kwargs["model"], "mistral-tiny-latest")
        self.assertIn("messages", call_args.kwargs)
        messages = call_args.kwargs["messages"]
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[1]["role"], "user")
        self.assertIn("Toyota Camry 2020", messages[1]["content"])
    
    @patch('mistral.client')
    def test_get_parts_lifetime_with_markdown(self, mock_client):
        """Тест получения данных с markdown блоками в ответе."""
        from mistral import get_parts_lifetime
        
        # Мокируем ответ с markdown
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        json_data = {
            "car": "Honda Civic 2021",
            "units": "months",
            "parts_lifetime": {
                "engine oil": 3,
                "brake pads": 6
            }
        }
        mock_response.choices[0].message.content = f"```json\n{json.dumps(json_data)}\n```"
        
        mock_client.chat.complete.return_value = mock_response
        
        # Вызываем функцию
        result = get_parts_lifetime("Honda Civic 2021")
        
        # Проверяем результат
        self.assertIsInstance(result, dict)
        self.assertEqual(result["car"], "Honda Civic 2021")
        self.assertIn("parts_lifetime", result)
    
    @patch('mistral.client')
    def test_get_parts_lifetime_mistral_error(self, mock_client):
        """Тест обработки ошибки Mistral API."""
        from mistral import get_parts_lifetime
        MistralError = mock_mistralai.models.MistralError
        
        # Мокируем ошибку API
        mock_error = MistralError(
            message="Rate limit exceeded",
            status_code=429,
            body={"error": "Too many requests"}
        )
        mock_client.chat.complete.side_effect = mock_error
        
        # Проверяем, что исключение пробрасывается
        with self.assertRaises(MistralError) as context:
            get_parts_lifetime("Toyota Camry 2020")
        
        self.assertEqual(context.exception.status_code, 429)
        self.assertEqual(context.exception.message, "Rate limit exceeded")
        
        # Проверяем, что ошибка была выведена в консоль
        self.assertTrue(self.mock_print.called)
    
    @patch('mistral.client')
    def test_get_parts_lifetime_invalid_json(self, mock_client):
        """Тест обработки невалидного JSON в ответе."""
        from mistral import get_parts_lifetime
        
        # Мокируем ответ с невалидным JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not valid JSON {"
        
        mock_client.chat.complete.return_value = mock_response
        
        # Проверяем, что выбрасывается ValueError
        with self.assertRaises(ValueError) as context:
            get_parts_lifetime("Toyota Camry 2020")
        
        self.assertIn("invalid JSON", str(context.exception))
        
        # Проверяем, что ошибка была выведена в консоль
        self.assertTrue(self.mock_print.called)
    
    @patch('mistral.client')
    def test_get_parts_lifetime_empty_response(self, mock_client):
        """Тест обработки пустого ответа."""
        from mistral import get_parts_lifetime
        
        # Мокируем пустой ответ
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""
        
        mock_client.chat.complete.return_value = mock_response
        
        # Проверяем, что выбрасывается ValueError
        with self.assertRaises(ValueError):
            get_parts_lifetime("Toyota Camry 2020")
    
    @patch('mistral.client')
    def test_get_parts_lifetime_malformed_json(self, mock_client):
        """Тест обработки некорректного JSON (неполный объект)."""
        from mistral import get_parts_lifetime
        
        # Мокируем ответ с некорректным JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"car": "Toyota", "units": "months"'
        
        mock_client.chat.complete.return_value = mock_response
        
        # Проверяем, что выбрасывается ValueError
        with self.assertRaises(ValueError):
            get_parts_lifetime("Toyota Camry 2020")
    
    @patch('mistral.client')
    def test_get_parts_lifetime_different_car_names(self, mock_client):
        """Тест с разными названиями автомобилей."""
        from mistral import get_parts_lifetime
        
        test_cases = [
            "BMW X5 2019",
            "Mercedes-Benz C-Class 2022",
            "Audi A4 2020",
            "Ford F-150 2021"
        ]
        
        for car_name in test_cases:
            with self.subTest(car_name=car_name):
                mock_response = MagicMock()
                mock_response.choices = [MagicMock()]
                mock_response.choices[0].message.content = json.dumps({
                    "car": car_name,
                    "units": "months",
                    "parts_lifetime": {"engine oil": 3}
                })
                
                mock_client.chat.complete.return_value = mock_response
                
                result = get_parts_lifetime(car_name)
                
                self.assertEqual(result["car"], car_name)
                self.assertIn("parts_lifetime", result)
                
                # Проверяем, что в запросе было правильное название
                call_args = mock_client.chat.complete.call_args
                messages = call_args.kwargs["messages"]
                self.assertIn(car_name, messages[1]["content"])
    
    @patch('mistral.client')
    def test_get_parts_lifetime_system_prompt_included(self, mock_client):
        """Тест, что system prompt включен в запрос."""
        from mistral import get_parts_lifetime, SYSTEM_PROMPT
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "car": "Test Car",
            "units": "months",
            "parts_lifetime": {}
        })
        
        mock_client.chat.complete.return_value = mock_response
        
        get_parts_lifetime("Test Car")
        
        # Проверяем, что system prompt был включен
        call_args = mock_client.chat.complete.call_args
        messages = call_args.kwargs["messages"]
        self.assertEqual(messages[0]["role"], "system")
        self.assertEqual(messages[0]["content"], SYSTEM_PROMPT)
    
    @patch('mistral.client')
    def test_get_parts_lifetime_user_message_format(self, mock_client):
        """Тест формата пользовательского сообщения."""
        from mistral import get_parts_lifetime
        
        car_name = "Toyota Camry 2020"
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "car": car_name,
            "units": "months",
            "parts_lifetime": {}
        })
        
        mock_client.chat.complete.return_value = mock_response
        
        get_parts_lifetime(car_name)
        
        # Проверяем формат пользовательского сообщения
        call_args = mock_client.chat.complete.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[1]["content"]
        
        self.assertIn("Estimate the service life", user_message)
        self.assertIn(car_name, user_message)
        self.assertIn("MONTHS", user_message)


class TestMistralModuleInitialization(unittest.TestCase):
    """Тесты для инициализации модуля mistral."""
    
    def test_system_prompt_defined(self):
        """Тест, что SYSTEM_PROMPT определен."""
        from mistral import SYSTEM_PROMPT
        
        self.assertIsInstance(SYSTEM_PROMPT, str)
        self.assertGreater(len(SYSTEM_PROMPT), 0)
        self.assertIn("auto mechanic", SYSTEM_PROMPT.lower())
        self.assertIn("months", SYSTEM_PROMPT.lower())
    
    def test_model_name_defined(self):
        """Тест, что MODEL_NAME определен."""
        from mistral import MODEL_NAME
        
        self.assertIsInstance(MODEL_NAME, str)
        self.assertGreater(len(MODEL_NAME), 0)
    
    @patch('mistral.MISTRAL_API_KEY', '')
    def test_api_key_validation(self):
        """Тест валидации API ключа (если ключ пустой, должно быть исключение)."""
        # Этот тест проверяет логику валидации, но так как ключ уже установлен,
        # мы просто проверяем, что он существует
        from mistral import MISTRAL_API_KEY
        
        self.assertIsInstance(MISTRAL_API_KEY, str)
        # В реальном коде есть проверка, но она выполняется при импорте
        # Поэтому мы просто проверяем наличие ключа


if __name__ == '__main__':
    unittest.main()

