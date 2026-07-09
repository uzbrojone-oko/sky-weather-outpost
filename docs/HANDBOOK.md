# Sky Weather Outpost Handbook

## Książka na dobranoc dla człowieka, który chciał tylko sprawdzić wilgotność

> Ten dokument tłumaczy, po co istnieje projekt `sky-weather-outpost`, jak ma działać jego architektura i jak myśleć o rozwoju bez zrobienia z małego terminala na strychu potwora klasy enterprise.

---

## 1. Po co nam Sky Weather Outpost

Sky Weather Outpost nie jest zwykłą aplikacją pogodową. To lokalny hub danych: mały posterunek, który zbiera dane z czujników, komputerów, kamer i przyszłych eksperymentów, zapisuje je, normalizuje i wystawia dalej przez API oraz dashboard.

Pierwsza wersja jest skromna:

```text
Kraków Lab:
  czujnik inFactory-TH
  temperatura
  wilgotność
  SQLite
  API
  jedna strona WWW
```

Ale projekt jest zaplanowany szerzej:

```text
Głębokie Field Outpost:
  Bresser 5in1
  all-sky camera
  top zdjęcia nocy
  timelapse
  astro-agent
  garden-node
  lightning sensor
  system metrics
  heartbeat
  NAS archive
```

Najważniejsza zasada:

```text
Build small, design wide.
```

Czyli pierwsza wersja ma być mała, ale fundament nie może blokować przyszłych modułów.

---

## 2. Mentalny model: outpost, nie aplikacja pogodowa

Zwykła aplikacja pogodowa myśli tak:

```text
temperature
humidity
pressure
```

Sky Weather Outpost myśli tak:

```text
site
node
device
event
measurement
media
status
```

To ogromna różnica. Temperatura i wilgotność są tylko jednymi z wielu możliwych metryk. Tak samo można zapisać:

```text
soil_moisture
guiding_rms_total
camera_sensor_temperature
lightning_distance
cpu_usage_percent
cloud_score
```

Dzięki temu projekt nie zamyka się w meteo. Pogoda, astro, ogród, all-sky i monitoring terminala stają się modułami nad tym samym rdzeniem.

---

## 3. Site, node, device — mapa świata

To są trzy najważniejsze pojęcia projektu.

### Site

`site` oznacza lokalizację albo instalację.

Przykłady:

```text
krakow
glebokie
```

Kraków i Głębokie nie muszą ze sobą gadać. Chodzi o to, żeby ta sama aplikacja mogła działać w różnych miejscach z różnym configiem.

### Node

`node` to konkretna maszyna albo urządzenie zbierające dane.

Przykłady:

```text
krakow-lab-t620
glebokie-core-t620
glebokie-media-t620
glebokie-astro-pc
glebokie-garden-node
```

Jeden site może mieć wiele node’ów. Na wsi możesz mieć core hub na jednym terminalu, a drugi terminal jako media worker, eksperymentalny node albo host od all-sky.

### Device

`device` to konkretne źródło danych: czujnik, kamera, montaż, komputer, odbiornik.

Przykłady:

```text
rtl433:inFactory-TH:1:166
rtl433:bresser-5in1:<id>
allsky:t7c
indi:asi533mc-pro
soil:bed-1
lightning:as3935
system:glebokie-core-t620
```

Najważniejsze: `device_key` powinien być stabilny. Jeśli zmienisz go po roku, historia danych będzie wyglądała jak dane z dwóch różnych urządzeń.

---

## 4. JSON jako wspólny język

JSON jest podstawowym formatem wymiany danych w projekcie.

`rtl_433` może wygenerować raw JSON:

```json
{
  "time": "2026-07-09 20:30:05",
  "model": "inFactory-TH",
  "id": 166,
  "channel": 1,
  "battery_ok": 1,
  "temperature_C": 20.06,
  "humidity": 47,
  "mic": "CRC"
}
```

Hub nie powinien jednak traktować tego jako finalnego modelu danych. Najpierw zapisuje raw event, a potem normalizuje go do wspólnego formatu:

```json
{
  "site": "krakow",
  "node": "krakow-lab-t620",
  "source": "rtl433",
  "events": [
    {
      "type": "measurement",
      "device_key": "rtl433:inFactory-TH:1:166",
      "metric": "temperature",
      "value": 20.06,
      "unit": "C"
    },
    {
      "type": "measurement",
      "device_key": "rtl433:inFactory-TH:1:166",
      "metric": "humidity",
      "value": 47,
      "unit": "%"
    }
  ]
}
```

Ten format jest ważniejszy niż pojedynczy czujnik. W przyszłości astro-agent, garden-node albo allsky-worker mogą wysyłać dane w tym samym stylu.

---

## 5. Raw events kontra measurements

Projekt powinien rozróżniać dwa światy.

### Raw events

Raw event to oryginalny payload, tak jak przyszedł ze źródła. Może pochodzić z:

```text
rtl_433
MQTT
HTTP ingest
JSONL replay
astro-agent
allsky-agent
garden-node
```

Raw events są przydatne do debugowania, replayu i poprawiania parserów.

### Measurements

Measurement to czysta, znormalizowana wartość gotowa do API, wykresów i dashboardu.

Przykład:

```text
site: krakow
node: krakow-lab-t620
device_key: rtl433:inFactory-TH:1:166
metric: temperature
value: 20.06
unit: C
```

Zasada:

```text
Raw events zachowują prawdę źródłową.
Measurements zachowują prawdę użytkową.
```

---

## 6. Dlaczego nie tabela weather_readings

Kuszące byłoby zrobić tabelę:

```text
weather_readings
- temperature
- humidity
```

To byłoby proste, ale za miesiąc zaboli. Dojdzie wiatr, deszcz, Bresser, lightning sensor, wilgotność gleby, temperatura kamery, RMS guidowania, CPU terminala.

Lepszy model:

```text
measurements
- id
- timestamp
- site
- node
- device_key
- metric
- value
- unit
- quality
- metadata_json
```

Dzięki temu nowy czujnik nie wymaga nowej tabeli. Wymaga tylko nowej metryki i ewentualnego normalizera.

---

## 7. Baza danych: SQLite na start

SQLite jest idealne na pierwszą wersję:

```text
- jeden plik
- prosta administracja
- łatwy backup
- działa lokalnie
- wystarczy dla małego huba
```

Aktywna baza powinna być lokalnie na terminalu, nie na NAS-ie.

Dobry układ:

```text
/var/lib/sky-weather-outpost/outpost.sqlite
```

Albo w trybie dev:

```text
./data/outpost.sqlite
```

NAS jest od backupów i archiwum, nie od aktywnej bazy. SQLite na udziale sieciowym może robić problemy z lockami i chwilowymi przerwami w sieci.

---

## 8. Migracje bazy

Baza będzie się zmieniać. Najpierw będą tabele:

```text
nodes
devices
raw_events
measurements
system_events
schema_migrations
```

Potem dojdą:

```text
media_assets
node_heartbeats
archive_jobs
api_tokens
```

Dlatego nie zmieniamy schematu ręcznie na dziko. Potrzebne są migracje:

```text
migrations/
  001_initial.sql
  002_add_media_assets.sql
  003_add_node_heartbeats.sql
```

Nawet proste SQL migracje wystarczą na start. Ważne, żeby projekt wiedział, która wersja schematu została zastosowana.

---

## 9. API-first

Dashboard ma być jedną stroną, ale dane powinny iść przez API.

Przykładowe endpointy:

```text
/api/v1/public/current
/api/v1/public/dashboard
/api/v1/internal/health
/api/v1/internal/system
/api/v1/internal/devices
```

Publiczne API jest bezpieczne i read-only. Internal API pokazuje więcej, ale wymaga tokena albo dostępu lokalnego.

Przykład odpowiedzi publicznej:

```json
{
  "site": "krakow",
  "temperature_C": 20.1,
  "humidity": 47,
  "battery_ok": true,
  "updated_at": "2026-07-09T20:30:05+02:00"
}
```

Publiczne API nie powinno pokazywać:

```text
- raw eventów
- obcych sensorów
- ścieżek na dysku
- logów
- sekretów
- debug info
```

---

## 10. Jedna strona WWW

Dashboard ma być jedną stroną, nie labiryntem podstron.

Na początku:

```text
Kraków Lab
- temperatura
- wilgotność
- ostatni odczyt
- bateria
- status systemu
```

Docelowo:

```text
Głębokie Outpost
- pogoda
- wiatr/deszcz
- all-sky latest
- top 3 zdjęcia nocy
- astro status
- garden status
- lightning status
- node health
```

Mentalnie dashboard składa się z kart:

```text
current_weather
history_preview
system_status
node_status
allsky_latest
top_night
astro_status
garden_status
lightning_status
```

Kraków pokazuje mniej kart, Głębokie więcej. Ten sam core, różny config.

---

## 11. Logowanie jako core feature

Logi nie są dodatkiem. Terminal może stać na strychu, więc gdy coś padnie, logi muszą powiedzieć dlaczego.

Dobre logi odpowiadają na pytania:

```text
Czy aplikacja wystartowała?
Jaki config załadowano?
Czy baza działa?
Czy rtl_433 działa?
Kiedy był ostatni pomiar?
Czy NAS jest dostępny?
Czy backup się udał?
Czy agent wysyła heartbeat?
```

Preferowane są logi strukturalne, np. JSON:

```json
{
  "ts": "2026-07-09T20:30:05+02:00",
  "level": "INFO",
  "logger": "outpost.collector.rtl433",
  "message": "measurement_stored",
  "site": "krakow",
  "node": "krakow-lab-t620",
  "device_key": "rtl433:inFactory-TH:1:166",
  "metric": "temperature",
  "value": 20.06,
  "unit": "C"
}
```

Logi muszą mieć rotację. Terminal nie może umrzeć, bo `collector.log` urósł do 40 GB.

---

## 12. Health, heartbeat i status

Outpost musi umieć odpowiedzieć na pytanie:

```text
Czy to w ogóle żyje?
```

Minimalny health endpoint:

```json
{
  "status": "ok",
  "site": "krakow",
  "node": "krakow-lab-t620",
  "checks": {
    "database": "ok",
    "rtl433_collector": "ok",
    "last_measurement": "ok",
    "disk_space": "ok"
  }
}
```

Docelowo każdy node/agent powinien wysyłać heartbeat:

```json
{
  "site": "glebokie",
  "node": "glebokie-astro-pc",
  "type": "heartbeat",
  "status": "ok",
  "services": {
    "indi": "ok",
    "ekos": "ok",
    "camera": "ok",
    "mount": "ok"
  }
}
```

Hub zapisuje `last_seen` i pokazuje, czy node jest online, stale, warning albo offline.

---

## 13. System metrics terminala

Sam terminal też jest źródłem danych.

Przykładowe metryki:

```text
cpu_usage_percent
ram_usage_percent
disk_free_gb
disk_usage_percent
load_1m
uptime_seconds
temperature_cpu_C
db_size_mb
log_dir_size_mb
last_backup_age_seconds
```

Te dane też mogą wejść do `measurements`:

```text
site: glebokie
node: glebokie-core-t620
device_key: system:glebokie-core-t620
metric: disk_free_gb
value: 183.4
unit: GB
```

Dzięki temu dashboard może pokazać nie tylko pogodę, ale też kondycję posterunku.

---

## 14. Publiczne i wewnętrzne API

Podział jest prosty:

```text
public/share:
  dane bezpieczne do pokazania ludziom

internal/admin:
  debug, raw events, health, system, nodes, logs
```

Przykład:

```text
/api/v1/public/current
/api/v1/public/dashboard
/api/v1/public/media/top-night

/api/v1/internal/health
/api/v1/internal/system
/api/v1/internal/raw-events
/api/v1/internal/nodes
```

Internal API powinno wymagać tokena. Public API może być bez tokena albo z prostym share tokenem, jeśli endpoint ma iść do znajomych.

---

## 15. Security bez paranoi

Projekt nie potrzebuje OAuth Enterprise Edition, ale potrzebuje podstaw.

Zasady:

```text
- public API jest read-only
- internal API wymaga tokena
- ingest API wymaga tokena
- tokeny nie trafiają do repo
- config i secrets są oddzielone
- TLS robi reverse proxy albo tunel
- aplikacji nie wystawiamy bezpośrednio na świat
```

Sekrety powinny być poza gitem:

```text
/etc/sky-weather-outpost/secrets.env
```

Albo w Docker/Kubernetes jako secrets.

Przykładowy header:

```text
Authorization: Bearer <token>
```

---

## 16. Caddy, Nginx i HTTPS

FastAPI/Uvicorn nie powinno być bezpośrednio wystawiane na internet.

Dobry układ:

```text
FastAPI/Uvicorn
  127.0.0.1:8000

Caddy/Nginx/Cloudflare Tunnel
  HTTPS
  reverse proxy
  public/internal routing
```

Caddy jest wygodny, bo automatycznie ogarnia HTTPS z Let’s Encrypt.

Nginx jest klasyczny i też dobry, ale wymaga więcej konfiguracji.

Apache nie jest tu potrzebny.

---

## 17. NAS jako archiwum, nie aktywna baza

Terminal jest aktywnym mózgiem outpostu. NAS jest selektywnym archiwum i backupem.

Na terminalu:

```text
- aktywna baza SQLite
- aktualny dashboard
- latest.jpg
- tymczasowe klatki all-sky
- runtime/cache/logi
```

Na NAS:

```text
- backup bazy
- backup configów
- najlepsze zdjęcia nocy
- timelapse
- wybrane dumpy nocy
- materiały do późniejszej obróbki
```

NAS nie może być wymagany do normalnego działania. Jeśli NAS padnie:

```text
hub nadal działa
archiwizacja przechodzi w pending
sync wraca, gdy NAS wróci
```

---

## 18. Media: zdjęcia i timelapse

Zdjęć i filmów nie wkładamy do SQLite. Baza trzyma tylko indeks.

Tabela `media_assets` może mieć:

```text
captured_at
site
node
device_key
media_type
local_path
archive_path
thumbnail_path
score
tags_json
archive_status
keep_forever
metadata_json
```

Przykładowy flow all-sky:

```text
noc:
  terminal zbiera klatki lokalnie

rano:
  wybiera top zdjęcia
  generuje miniatury
  robi timelapse
  zapisuje metadane
  wysyła najlepsze rzeczy na NAS

po X dniach:
  usuwa zwykłe raw frames
  zostawia top/timelapse/indeks
```

Zasada:

```text
Nie robimy z NAS-a cyfrowego śmietnika.
```

---

## 19. All-sky live: poziomy trudności

Nie trzeba od razu robić streamu klasy telewizja.

Poziom 1:

```text
latest.jpg odświeżany co kilka sekund
```

Poziom 2:

```text
MJPEG stream
```

Poziom 3:

```text
HLS stream z segmentami wideo
```

MVP all-sky powinien zacząć od `latest.jpg`. To daje efekt live-ish i jest dużo prostsze niż pełny streaming.

---

## 20. Moduły przyszłości

Core nie powinien znać szczegółów każdej domeny. Domeny są modułami.

Przyszłe moduły:

```text
rtl433
weather
system_metrics
media
allsky
astro
garden
lightning
archive
mqtt
agents
observability
```

Dodanie nowego czujnika powinno wyglądać tak:

```text
1. Zobacz raw JSON.
2. Dodaj device do configu.
3. Dodaj mapping metryk, jeśli potrzeba.
4. Uruchom replay/live.
5. Sprawdź measurements.
6. Dodaj kartę dashboardu, jeśli chcesz.
```

---

## 21. Agenty i daemony

Hub zbiera, zapisuje i wystawia dane. Inne maszyny mogą mieć lekkich agentów.

Przykład:

```text
Głębokie core hub:
  API
  WWW
  DB
  rtl_433
  storage

Astro PC:
  outpost-agent
  zbiera INDI/Ekos/system stats
  wysyła dane do huba

Garden node:
  soil moisture
  lightning sensor
  heartbeat
```

Agent wysyła JSON do huba przez HTTP ingest albo MQTT.

Najprostszy wariant:

```text
agent → HTTP POST /api/v1/ingest → hub
```

Docelowy wariant IoT:

```text
agent → MQTT → hub subscriber
```

---

## 22. MQTT

MQTT nie musi być w v0.1, ale warto pamiętać, że bardzo dobrze pasuje do tego projektu.

Docelowy przepływ:

```text
rtl_433
  ↓
MQTT broker
  ↓
Sky Weather Outpost
  ↓
SQLite/API/dashboard
```

Zaleta: aplikacja nie musi bezpośrednio odpalać `rtl_433` ani dotykać SDR-a. Odbiera tylko wiadomości.

Na start wygodniejszy jest jednak JSONL replay i `rtl_433 -F json -C si`.

---

## 23. Docker, systemd i Kubernetes

Projekt powinien być gotowy na różne sposoby uruchamiania.

### Local dev

```text
uvicorn / fastapi dev
config lokalny
JSONL replay
```

### Native edge

```text
systemd + Python venv + SQLite
```

### Docker Compose

```text
outpost
mosquitto
prometheus
grafana
caddy
```

### Kubernetes

Kubernetes nie jest celem v0.1, ale aplikacja powinna być gotowa na:

```text
/healthz
/readyz
/metrics
config przez env/config file
dane na volume
logi na stdout
graceful shutdown
```

Nie implementujemy Kubernetesa od razu. Projektujemy tak, żeby kiedyś nie bolało.

---

## 24. Deployment i katalogi

W trybie systemowym dobry układ to:

```text
/opt/sky-weather-outpost/          kod aplikacji
/etc/sky-weather-outpost/          config i secrets
/var/lib/sky-weather-outpost/      baza, runtime, cache
/var/log/sky-weather-outpost/      logi
/mnt/nas/outpost/                  archiwum/backup
```

W trybie Docker:

```text
/app
/config
/data
/logs
/archive
```

Dzięki temu migracja jest prosta: kod jest osobno, dane są osobno, config jest osobno.

---

## 25. Instalator i skrypty

Projekt powinien mieć skrypty:

```text
scripts/install.sh
scripts/update.sh
scripts/backup.sh
scripts/restore.sh
scripts/healthcheck.sh
scripts/capture-rtl433.sh
```

Cel instalatora:

```text
sudo ./scripts/install.sh --config config/examples/glebokie.yaml
```

Skrypt powinien:

```text
- sprawdzić zależności
- utworzyć katalogi
- utworzyć użytkownika systemowego
- przygotować venv
- zainstalować zależności
- skopiować config
- uruchomić migracje
- stworzyć systemd service
- odpalić aplikację
```

To nie musi być gotowe w pierwszym commicie, ale musi być przewidziane.

---

## 26. Konfiguracja

YAML jest dobry do configu, bo łatwo go czytać i edytować.

Przykład:

```yaml
site:
  id: krakow
  name: "Kraków Lab"
  type: lab
  timezone: Europe/Warsaw

node:
  id: krakow-lab-t620
  role: hub

modules:
  rtl433:
    enabled: true
    mode: jsonl_replay
    replay_path: ./data/raw_data/rtl433-live.jsonl

  system_metrics:
    enabled: true
    interval_seconds: 60

storage:
  sqlite_path: ./data/outpost.sqlite

devices:
  - key: rtl433:inFactory-TH:1:166
    name: "Kraków weather shield"
    type: weather_sensor
    public: true
    metrics:
      - temperature
      - humidity
```

Zasada:

```text
Nie hardcodujemy Krakowa, Głębokiego ani ID czujnika w core.
```

---

## 27. JSONL replay

Tryb replay jest bardzo ważny dla developmentu.

Masz plik:

```text
data/raw_data/rtl433-live.jsonl
```

W nim jeden JSON na linię.

Dzięki replay możesz testować parser, bazę, API i dashboard bez czekania na nowe ramki z radia.

Kolejność implementacji powinna być:

```text
1. JSONL replay
2. live rtl_433 stdout
3. MQTT
```

To ogranicza liczbę rzeczy debugowanych naraz.

---

## 28. Deduplication

Czujniki radiowe często wysyłają tę samą ramkę kilka razy.

Przykład:

```text
20:30:04 inFactory-TH ID 166
20:30:05 inFactory-TH ID 166
20:30:05 inFactory-TH ID 166
```

Raw events mogą to zapisać, ale measurements nie powinny mieć pięciu identycznych kropek na wykresie.

Deduplication może działać po:

```text
device_key
metric/value set
krótkie okno czasu, np. 5-10 sekund
```

---

## 29. Unknown devices

`rtl_433` łapie wszystko z eteru. Obce czujniki są normalne.

Zasada:

```text
unknown device może wejść do raw/debug,
ale nie do public API i nie do głównych measurements.
```

Statusy urządzeń:

```text
unknown_seen
ignored
known
public
private
```

To chroni dashboard przed śmietnikiem i przypadkowym pokazywaniem cudzych sensorów.

---

## 30. Jednostki i normalizacja

Baza powinna używać standardowych jednostek:

```text
temperature: C
humidity: %
pressure: hPa
rain: mm
wind_speed: m/s albo km/h
distance: km
battery_ok: bool
battery_voltage: V
soil_moisture: %
```

Raw event zostaje nietknięty. Measurement jest normalizowany.

Jeśli przyjdzie:

```json
{"temperature_F": 68.1}
```

measurement zapisuje:

```text
metric: temperature
value: 20.06
unit: C
```

---

## 31. Timezone i timestampy

Czas jest ważny.

Warto rozróżniać:

```text
measured_at  - czas według źródła
received_at  - czas, kiedy hub dostał dane
stored_at    - czas zapisu w bazie
```

W bazie najlepiej trzymać ISO z offsetem albo UTC. W UI można pokazywać lokalny czas site’u.

Config site’u powinien mieć timezone:

```yaml
site:
  timezone: Europe/Warsaw
```

---

## 32. Retencja danych

Nie wszystkie dane trzymamy wiecznie.

Przykład:

```text
measurements:
  długo

raw_events:
  7-30 dni

logs:
  rotacja

allsky raw frames:
  3-7 dni lokalnie

top photos:
  długo na NAS

timelapse:
  długo na NAS

backups:
  według miejsca na NAS
```

To chroni przed sytuacją, w której all-sky zapełni dysk po miesiącu.

---

## 33. Backup i restore

Backup bez restore to zaklęcie ochronne, nie system.

Minimum:

```text
backup SQLite
backup configów
backup ważnych metadanych
backup top zdjęć/timelapse
```

Restore powinien umieć:

```text
- odtworzyć config
- odtworzyć bazę
- uruchomić migracje
- sprawdzić health
```

Dobrze mieć skrypty:

```text
scripts/backup.sh
scripts/restore.sh
```

---

## 34. Observability: Grafana i Prometheus

Grafana nie jest głównym dashboardem użytkowym. Jest panelem technicznym.

Główny dashboard:

```text
ładny, prosty, jedna strona
pogoda/media/status
```

Grafana:

```text
monitoring techniczny
system metrics
alerty
historia operacyjna
```

W przyszłości aplikacja powinna mieć endpoint:

```text
/metrics
```

w formacie Prometheus.

Przykładowe metryki:

```text
outpost_node_online{site="glebokie",node="glebokie-core-t620"} 1
outpost_measurement_age_seconds{site="krakow",device="rtl433:inFactory-TH:1:166"} 42
outpost_disk_free_bytes{site="glebokie",node="glebokie-core-t620"} 183400000000
```

---

## 35. MVP v0.1

Pierwszy milestone ma być mały.

Zakres:

```text
Kraków Lab
inFactory-TH id 166
JSONL replay
SQLite
raw_events
measurements
devices
nodes
basic logging
/api/v1/public/current
/api/v1/internal/health
prosty dashboard
```

Nie robimy w v0.1:

```text
all-sky
MQTT
Grafana
Kubernetes
NAS archive
agents
astro telemetry
garden sensors
actions/rules
```

To nie znaczy, że o nich zapominamy. One są w roadmapie, ale nie w pierwszej warstwie lakieru.

---

## 36. Jak pracować z Copilotem/Claude

Copilot/Claude powinien dostaawać małe zadania.

Dobry prompt:

```text
Read README.md, ARCHITECTURE.md, ROADMAP.md, MVP.md and copilot-instructions.md.
Do not implement features outside MVP v0.1.
Create the initial Python/FastAPI project skeleton with config loading, SQLite migration foundation, structured logging, health endpoint and public current placeholder endpoint.
```

Zły prompt:

```text
Zrób cały projekt.
```

Zasada:

```text
1 task = 1 mały branch = 1 sensowny commit
```

Przykładowe branche:

```text
feature/v0.1-app-skeleton
feature/config-loader
feature/sqlite-migrations
feature/jsonl-replay
feature/public-current-api
```

---

## 37. Jak myśleć o rozwoju

Projekt ma rosnąć przez dokładanie modułów, nie przez przepisywanie core.

Nowy czujnik:

```text
config + normalizer + optional dashboard card
```

Nowy site:

```text
nowy config
```

Nowy node:

```text
node registry + heartbeat + ingest token
```

Nowe media:

```text
media_assets + storage path + dashboard card
```

Nowa automatyka:

```text
events + rules + commands
```

Ale actions/rules są tematem na później.

---

## 38. Analogia warsztatowa

Dzisiejsze repo to podkład pod malowanie.

```text
oczyszczona rama      → rozmowa i wymagania
epoksyd              → architektura
szpachla             → roadmapa i MVP
grunt                → copilot-instructions
maskowanie           → security/config/deployment/runbook
pierwszy lakier      → v0.1 app skeleton
klar                 → dashboard i operacyjność
```

Nie malujemy na rdzę. Najpierw fundament.

---

## 39. Najważniejsze zasady projektu

```text
1. Core is a generic local hub, not a weather app.
2. Build small, design wide.
3. Use JSON for ingest.
4. Use YAML for config.
5. Use site/node/device everywhere.
6. Store raw events separately from measurements.
7. Keep measurements generic: metric/value/unit.
8. Keep media as files, indexed in DB.
9. Keep secrets out of repo.
10. Public API is read-only and safe.
11. Internal API requires token.
12. Logging, health and heartbeat are core features.
13. NAS is archive/backup, not active DB.
14. SQLite is enough for v0.1.
15. Docker/Kubernetes-ready does not mean Kubernetes-first.
16. Kraków is lab, Głębokie is field outpost.
17. Every milestone must end with a working system.
```

---

## 40. Co dalej

Najbliższy realny krok:

```text
feature/v0.1-app-skeleton
```

Pierwszy kod powinien stworzyć:

```text
- FastAPI app
- config loader
- domain models
- SQLite migration foundation
- structured logging
- health endpoint
- public current placeholder endpoint
- minimal tests
```

Potem:

```text
JSONL replay → normalize inFactory-TH → SQLite → current API → dashboard
```

Dopiero gdy Kraków Lab pokazuje temperaturę i wilgotność z własnej stacji, projekt dostaje prawo do kolejnych bajerów.

---

## 41. Dobranoc

Sky Weather Outpost zaczyna jako mały terminal, czujnik temperatury i wilgotności oraz plik SQLite.

Ale mentalnie jest posterunkiem:

```text
widzi pogodę,
widzi niebo,
widzi swoje node’y,
widzi zdrowie systemu,
przechowuje historię,
wystawia API,
i z czasem przyjmie wszystko, co sobie jeszcze wymyślisz.
```

Nie trzeba budować wszystkiego naraz. Trzeba zbudować pierwszy działający kawałek tak, żeby następny nie wymagał rozbiórki do gołej ramy.

Koniec rozdziału. Terminal na strychu czeka.
