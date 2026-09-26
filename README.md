### Cтек технологии: 

- PostgreSQL 16.15
- python3.12
- DRF
- RabbitMQ (message broker)
- Valkey (in-memory key-value data store)
- SqlAlchemy
- Alembic
- pytest

### Описание реализации авторизации пользователей к ресурсам:

Правила доступа к ресурсам приложения контролируются данными в трех таблицах
- *roles_permissions* (список правил для роли и ресурсов)
- *roles* (список ролей, поддерживаемые системой)
- *application_resources* (список ресурсов системы)

Доступ к ресурсу текущей роли определяется следующими полями таблицы roles_permissions.

**mode** - перечесление значений own, nonown, null говорит к какому типу рекорда ресурса для текущей роли применяются правила. 
       К собственному - own, к чужому - nonown. Если null - правила применяются одновременно для обоих режимов, т.о. null предотвращает дублирования одинаковых правил.

правила:
**allow_enumerate** правило определяет доступ на чтение списков ресурса (например, при получении списка пользователей, если false для nonown mode, то записи кроме собственной должны быть отфильтрованы в выборке)

**allow_read** правило определяет доступ на чтение записи ресурса

**allow_create** правило определяет доступ на создание записи ресурса

**allow_edit** правило определяет доступ на редактрирование записи ресурса

**allow_delete** правило определяет доступ на удаление записи ресурса для чтения

**role_id** - хранит id роли, для которой применяются правила (если значение null, правила применяются ко всем ролям т.о. null предотвращает дублирования одинаковых правил)

**resource_id** - хранит id ресурса, для которого применяются правила (если значение null, правила применяются ко всем ресурсам т.о. null предотвращает дублирования одинаковых правил)

В таблице могут быть несколько записей правил (для роли и ресурсов). Каждая записль правила имеет вес определяющийся **weigh_role_permission** функцией
Наименьший вес имеет больший приоритет для применения правила

1 - *specific permission* (role_id is not null and resource_id is not null and mode is not null)

2 - *specific permission for all mode* (role_id is not null and resource_id is not null and mode is null)

3 - *default role permission* (role_id is null and resource_id is not null and mode is not null)

4 - *default role permission for all mode* (role_id is null and resource_id is not null and mode is null)

5 - *default resource permission* (role_id is not null and resource_id is null and mode is not null)

6 - *default resource permission for all mode* (role_id is not null and resource_id is null and mode is null)

### Некоторые детали реализации:

Для реализация функции Logout используется Valkey server для помещения JWT access token в черный список cо значением TTL равным времени жизни токена.
Этот же подход используется, когда пользователя удаляют или пользователь инициирует удаление. Юзер временно помещается в черный список со значением ТТL равным значению опции времени жизни jwt токена.

В приложении реализована двухфакторная аутентификация по имейл. Отправка временых числовых кодов осуществляется воркером брокера сообщений rabbit mq.

### Зависимости и настройки:

Зависимости решения зафиксированы в файле requirements.txt (а также в pyproject.toml файле пакетов)
Для настройки "внутренних" зависимостей нужно выполнить:
```
>>> pip install -e ./core_contracts
>>> pip install -e ./core
>>> pip install -e ./repo_sqlalchemy
>>> pip install -e ./queue_publishers
>>> pip install -e ./queue_workers
```

Команда для применения миграций базы данных (в проекте repo_migrations) выполняется после установления зависимостей:
```
>>> alembic upgrade head
```

Настройки конфигурационных файлов:
- в проекте api_drf (api_drf/setup/settings.py):
	- VALKEY_URL - опция подключения к valkey-server
	- RABBITMQ - опции подключения к rabbitmq
	- DATABASES[PIZZA_APP][ENV1] - опция подключения к базе данных
	- SECURITY_AUTH - опции шифрования jwt токена доступа
	- SECURITY_AUTH_2FA - опции двухфакторной аутентификации по имейл
- в проекте queue_workers (queue_workers/src/queue_workers/config.ini)
	- [rabbitmq] - опции подключения к rabbitmq
	- [database] - опции подключения к базе данных
	- [mail] - опции подключения к smtp server

Для запуска приложения в Дебаг режиме:
```
cd api_drf
python3 manage.py runserver
```

### Тесты
в проекте core (core/tests) небольшое покрытие юнит тестами


Буду рад после ревью любым замечаниям, критике.
С найлучшими пожеланиями,
Антон
