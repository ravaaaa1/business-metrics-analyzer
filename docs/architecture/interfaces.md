# Контракты компонентов
Все сценарии принимают ActorContext с серверными role, department, auth_version. `Period(start, end)` включителен. AccessScope вычисляет сервер, клиент не может расширить его параметром department.

| Компонент | Интерфейс | Ключевые методы |
|---|---|---|
| AuthService | IAuthService | login(credentials) -> TokenPair; refresh(token) -> TokenPair; authorize(actor, action) -> AccessScope |
| UserService | IUserService | create(dto, actor) -> UserDto; change_access(id, role, department, actor); block(id, actor) |
| SalesImportService | ISalesImportService | import_csv(file_ref, actor) -> ImportJobDto; validate(stream) -> ValidationResult; publish(job_id, expected_version) -> ImportResult |
| KpiService | IKpiService | calculate_period(period, scope, version) -> KpiResult; get_dashboard(period, actor) -> DashboardDto |
| ReportService | IReportService | generate(type, period, actor) -> ReportJobDto; export_excel(report_id, actor) -> bytes; download(report_id, actor) -> FileStream |
| MetricService | IMetricService | set_target(department, month, amount, actor); compare(period_a, period_b, actor) -> ComparisonDto |
| SaleRepository | ISaleRepository | aggregate(period, scope, version) -> KpiInputs; stage_batch(version, rows); activate(version, expected_version) |
| UserRepository | IUserRepository | get(id) -> User; get_by_login(login); save(user) |
| UnitOfWork | IUnitOfWork | enter(); commit(); rollback(); exit() |
| TokenProvider | ITokenProvider | issue(user_id, auth_version) -> TokenPair; verify(jwt) -> Claims |
| KpiStrategy | IKpiStrategy | calculate(inputs: KpiInputs) -> Decimal or None |
| KpiCache | IKpiCache | get(version, scope, period); put(key, dto, ttl) |
| ReportGenerator | IReportGenerator | render(report_snapshot) -> bytes |
| ObjectStorage | IObjectStorage | put(key, stream); get(key) -> stream; delete_expired() |
| Notifier | INotifier | send(event_id, recipient_id, message) |
| AuditRepository | IAuditRepository | append(actor_id, action, result, timestamp, correlation_id) |
| JobRepository | IJobRepository | enqueue(kind, payload); claim(lease); complete(id); fail(id, errors) |

DTO не содержит ORM-объектов или паролей. DashboardDto: version, loaded_at, period, departments, revenue, average_check, conversion, profitability, units. Decimal передаётся строкой без потери точности, отсутствующее отношение как null. ReportSnapshot фиксирует те же агрегаты и единицы.

Ошибки API: 401 неверная/отозванная аутентификация, 403 запрещённая роль/отдел, 404 недоступный отчёт без раскрытия чужого объекта, 409 повтор или конфликт версии, 422 период/схема/значения, 413 размер, 202 принятие фонового задания. Ошибки содержат correlation_id, но не traceback. GET /imports/{id} проверяет владельца/роль и возвращает pending/running/succeeded/failed и ошибки строк.
