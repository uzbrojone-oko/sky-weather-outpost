# Sky Weather Outpost Handbook

> **Language note:** This handbook is intentionally written in Polish as an informal, human-friendly learning companion. The canonical project documentation is maintained in English and remains the source of truth for implementation and architectural decisions. An English version of this handbook may be added later if there is a real need for it.

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
  backup
  energy / PV
  EV charging
  Home Assistant status
  WWW / TLS health
```

Najważniejsza zasada:

```text
Build small, design wide.
```

Czyli pierwsza wersja ma być mała, ale fundament nie może blokować przyszłych modułów.

### Co właściwie znaczy Sky Weather Outpost?

Nazwa projektu jest jednocześnie bardzo dobrym sposobem myślenia o jego zakresie.

```text
SKY WEATHER OUTPOST
│
├── SKY
│   ├── all-sky
│   ├── astro telemetry
│   ├── cloud information
│   ├── observation readiness
│   ├── Astro Score
│   └── sky media
│
├── WEATHER
│   ├── temperature
│   ├── humidity
│   ├── wind
│   ├── rain
│   ├── dew conditions
│   ├── lightning
│   └── garden / environment
│
└── OUTPOST
    ├── nodes / computers
    ├── services / daemon health
    ├── storage / disk
    ├── backup / restore
    ├── NAS
    ├── network / WWW / TLS
    ├── energy / PV
    ├── EV charging
    └── selected smart-home/site state
```

`Sky` mówi, co dzieje się nad posterunkiem.

`Weather` mówi, co dzieje się w jego lokalnym środowisku.

`Outpost` mówi, co dzieje się z samym posterunkiem.

To ostatnie jest ważne. `Outpost` nie oznacza szuflady `inne`. Oznacza fizyczną instalację jako całość. Głębokie Outpost ma swoje komputery, sensory, storage, sieć, zasilanie, usługi i urządzenia. System powinien umieć odpowiedzieć zarówno na pytanie:

```text
Jaka jest pogoda i czy dziś warto wystawić teleskop?
```

jak i:

```text
Czy sam posterunek jest zdrowy i czy wszystko, czego potrzebuje do działania, działa poprawnie?
```

Dlatego informacja o temperaturze powietrza, stanie all-sky, ostatnim backupie, wolnym miejscu na dysku, produkcji PV czy ważności certyfikatu HTTPS może należeć do tego samego systemu. To różne domeny, ale opisują ten sam fizyczny Outpost.

Jednocześnie Outpost nie powinien próbować zostać drugim Home Assistantem. Może obserwować, archiwizować, korelować i prezentować wybrany stan infrastruktury. Automatyka i sterowanie urządzeniami powinny pozostać w osobnej warstwie lub w systemie takim jak Home Assistant.

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
pv_power
backup_age_seconds
tls_certificate_days_remaining
```

Dzięki temu projekt nie zamyka się w meteo. Pogoda, astro, ogród, all-sky, energia i monitoring posterunku stają się modułami nad tym samym rdzeniem.

Najważniejsze jest to, że podział `Sky / Weather / Outpost` jest sposobem prezentacji i rozumienia systemu, a nie trzema osobnymi architekturami. Pod spodem wszystkie domeny korzystają z tego samego modelu danych.

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
/api/v1/internal/status
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

### CLI i WWW są klientami tego samego Outposta

Jeżeli dashboard pokazuje, że baza jest zdrowa, a CLI pokazuje, że baza jest zdrowa, nie powinny istnieć dwa niezależne fragmenty kodu dochodzące do tego wniosku.

Docelowy model:

```text
measurements / devices / services / checks
                 |
                 v
         status/health service
                 |
        +--------+--------+
        |                 |
        v                 v
 internal API         other APIs
        |
   +----+----+
   |         |
   v         v
  WWW       CLI
```

`outpost status` i prywatny panel WWW powinny więc prezentować ten sam snapshot stanu z `/api/v1/internal/status`. Różni się tylko prezentacja: WWW może używać kart i kolorowych kontrolek, CLI tabel i znaków `✓`, `!`, `✗`.

To samo może dotyczyć domen takich jak weather, astro, energy czy home/site status. Dane i reguły pozostają wspólne, a interfejs jest tylko klientem API.

`outpost doctor` ma inną rolę: może aktywnie wykonywać głębsze testy i powiedzieć *dlaczego* coś nie działa. Restore albo naprawa niedziałającego daemona również nie mogą zależeć od działającego API.

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
- PV / energy
- backup status
- WWW / TLS status
- selected home/site status
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
energy_status
home_status
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

Docelowo `outpost status` może pokazać ten sam stan, który widzi prywatny dashboard:

```text
Sky Weather Outpost — Głębokie

WEATHER
✓ Bresser             online
✓ Last measurement    18s ago

SKY
✓ All-sky             online
○ Astro node          idle

OUTPOST
✓ Core service        running
✓ Database            healthy
✓ Disk                71% free
✓ Backup              7h ago
✓ WWW                 reachable
✓ HTTPS               valid
✓ TLS certificate     63 days remaining
! NAS                 unavailable (optional)
```

`outpost doctor` idzie krok dalej i wykonuje checklistę diagnostyczną. Zielona kontrolka nie ma oznaczać tylko "proces istnieje", ale "sprawdziliśmy konkretny warunek i przeszedł".

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
/api/v1/internal/status
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
  public access
```

Caddy jest bardzo wygodny, bo automatyzuje certyfikaty TLS.

Nginx daje więcej ręcznej kontroli.

Cloudflare Tunnel może być użyteczny, jeśli nie chcesz wystawiać portów na routerze.

Outpost nie powinien implementować własnego mechanizmu wydawania ani odnawiania certyfikatów. To zadanie Caddy/ACME lub innego reverse proxy. Outpost może natomiast obserwować wynik: czy HTTPS działa, czy certyfikat jest ważny i ile czasu pozostało do jego wygaśnięcia.

---

## 17. NAS — archiwum, nie serce systemu

NAS jest dodatkiem, nie fundamentem działania.

Na NAS można trzymać:

```text
- backup SQLite
- backup configu
- wybrane all-sky images
- timelapse
- top zdjęcia nocy
- wybrane materiały astro
```

Nie powinno się trzymać aktywnej bazy na NAS-ie.

Hub musi działać, nawet jeśli NAS zniknie z sieci na godzinę.

Dobra zasada:

```text
local SSD = runtime
NAS = backup/archive
```

---

## 18. Backup i restore

Backup musi być prosty.

Przykład:

```bash
outpost backup
```

Backup powinien zawierać:

```text
- SQLite DB
- config
- opcjonalnie metadata media
```

Sekrety mogą być backupowane osobno i ostrożniej.

Restore:

```bash
outpost restore backup-2026-07-09.tar.gz
```

Backup SQLite powinien używać bezpiecznej metody, np. SQLite backup API albo `.backup`, a nie zwykłego `cp` działającej bazy.

Docelowo status backupu powinien być częścią stanu Outposta: kiedy wykonano ostatni poprawny backup, gdzie został zapisany i czy jego wiek przekracza skonfigurowany próg ostrzegawczy.

---

## 19. Media — pliki, nie BLOB-y

Zdjęcia all-sky nie powinny trafiać jako BLOB do SQLite.

Lepszy model:

```text
/var/lib/sky-weather-outpost/media/
  allsky/
    2026/
      07/
        09/
          frame-000001.jpg
```

W bazie:

```text
media_assets
- id
- site
- node
- type
- path
- captured_at
- score
- archive_status
```

Baza wie, gdzie jest plik i jakie ma metadata. Sam obraz leży na filesystemie.

---

## 20. All-sky: trzy poziomy "live"

"Live" może znaczyć trzy różne rzeczy.

### Poziom 1: latest.jpg

Najprostsze:

```text
kamera -> latest.jpg -> WWW
```

Odświeżanie co kilka sekund.

### Poziom 2: MJPEG

Pseudo-streaming:

```text
kamera -> JPEG frames -> MJPEG endpoint
```

### Poziom 3: HLS/WebRTC

Prawdziwszy streaming, ale dużo bardziej skomplikowany.

Na start najlepszy jest poziom 1.

---

## 21. Top 3 zdjęcia nocy

Każda noc może generować setki albo tysiące klatek.

Nie chcemy wszystkiego trzymać wiecznie.

Pipeline:

```text
capture
  -> local frames
  -> scoring
  -> top candidates
  -> keep/archive
  -> timelapse
  -> retention cleanup
```

Na początku scoring może być banalny albo ręczny. Później można dodać:

```text
meteor score
star count
cloud score
brightness anomaly
motion streak
```

---

## 22. Retencja media

Przykład:

```yaml
media:
  raw_retention_days: 7
  keep_top_per_night: 3
  keep_timelapse: true
```

Czyli:

```text
pełne raw frames: 7 dni
najlepsze zdjęcia: długo
finalny timelapse: długo
```

NAS nie powinien zamienić się w śmietnik wszystkich klatek.

---

## 23. Astro agent

Komputer od teleskopu może mieć własnego lekkiego agenta.

Agent może czytać:

```text
INDI
Ekos
system metrics
```

I wysyłać:

```text
camera_temperature
cooler_power
mount_state
guiding_rms_total
filter_name
focuser_position
session_state
```

Do huba przez HTTP albo MQTT.

Najważniejsze: agent nie musi mieć własnej bazy. Może tylko wysyłać telemetry.

---

## 24. Garden node

Ogród może mieć:

```text
soil moisture
soil temperature
air temperature
humidity
```

To dalej są zwykłe measurements.

Nie trzeba robić osobnej aplikacji "garden system".

---

## 25. Lightning sensor

AS3935 albo podobny sensor może generować event:

```json
{
  "type": "lightning",
  "distance_km": 12,
  "energy": 18342
}
```

To może trafić do `events` albo `measurements`.

Dashboard może pokazać:

```text
Last lightning: 12 km, 4 min ago
```

---

## 26. MQTT — kiedy ma sens

MQTT jest świetne dla wielu małych urządzeń.

Przykład:

```text
garden-node -> MQTT -> hub
astro-agent -> MQTT -> hub
rtl_433 -> MQTT -> hub
```

Ale v0.1 nie potrzebuje MQTT.

Najpierw:

```text
JSONL replay
```

Potem:

```text
rtl_433 stdout
```

Dopiero później MQTT.

---

## 27. Dlaczego nie mikroserwisy

Bo mamy kilka terminali, nie Netflixa.

Na start:

```text
modular monolith
```

Czyli jedna aplikacja, ale logicznie podzielona:

```text
app/
  core/
  config/
  storage/
  ingest/
  normalizers/
  api/
  web/
  services/
```

To daje porządek bez kosztu mikroserwisów.

---

## 28. Agent to nie mikroserwis

Agent może być osobnym procesem na innym komputerze, ale nie znaczy, że cały system jest mikroserwisowy.

Agent ma prostą rolę:

```text
read local hardware
normalize or package data
send to hub
heartbeat
retry
```

Hub nadal jest centrum.

---

## 29. Docker — po co później

Docker daje:

```text
powtarzalne środowisko
łatwiejszy deploy
łatwiejsze dependency management
```

Ale sprzęt typu SDR i USB komplikuje kontenery.

Dlatego:

```text
v0.1 -> native systemd
later -> Docker Compose
```

---

## 30. Kubernetes — nie teraz, ale nie blokujmy

Kubernetes nie jest potrzebny na start.

Ale aplikacja może być projektowana tak, żeby później nie bolało:

```text
config outside code
secrets outside code
stdout logs
health endpoint
readiness endpoint
metrics endpoint
persistent data path
stateless API where possible
```

To jest lift-and-shift friendly.

---

## 31. systemd

Na Debianie najlepszy start to systemd.

Przykład:

```bash
sudo systemctl status sky-weather-outpost
sudo systemctl restart sky-weather-outpost
journalctl -u sky-weather-outpost -f
```

Systemd daje:

```text
autostart
automatic restart
logs
service status
```

CLI Outposta może później opakować część tych informacji w wygodniejszą prezentację, ale systemd nadal pozostaje właściwym menedżerem procesu.

---

## 32. Installer

`install.sh` powinien:

```text
- sprawdzić system
- sprawdzić dependencies
- stworzyć usera
- stworzyć katalogi
- stworzyć venv
- zainstalować app
- zainstalować config
- wykonać migracje
- zainstalować systemd unit
- uruchomić healthcheck
```

Installer powinien być idempotentny.

Czyli drugie uruchomienie nie powinno niszczyć instalacji.

---

## 33. Update

`update.sh` może robić:

```text
git pull
backup DB
pip install/update
migrations
restart service
healthcheck
```

Jeśli migracja padnie, update powinien się zatrzymać.

---

## 34. Config jako produkt

Config nie jest tylko plikiem technicznym. To opis konkretnego Outposta.

Przykład:

```yaml
site:
  id: glebokie
  name: Głębokie Outpost

node:
  id: glebokie-core-t620

modules:
  rtl433:
    enabled: true

  allsky:
    enabled: true

  system_metrics:
    enabled: true
```

Inny site może używać tego samego kodu z innym YAML-em.

---

## 35. JSONL replay — genialnie prosty dev mode

Zamiast programować z SDR-em podpiętym do desktopa:

```text
rtl_433 capture
   -> JSONL file
   -> copy to dev PC
   -> replay
```

To daje deterministyczne testy.

Możesz odpalać ten sam payload 100 razy.

---

## 36. Deduplikacja

Sensory radiowe często wysyłają ten sam frame kilka razy.

Nie chcemy:

```text
20.1 C
20.1 C
20.1 C
```

jako trzech pomiarów w sekundę.

Dedupe może używać:

```text
device_key
metric
value
time window
```

Raw eventy można zachować wszystkie, a measurements deduplikować.

---

## 37. Unknown devices

SDR usłyszy sąsiadów.

Nie chcemy pokazywać ich publicznie.

Ale warto je logować wewnętrznie:

```text
unknown rtl433 device detected
model=Nexus-TH
id=93
```

To może być ciekawe diagnostycznie.

---

## 38. Jednostki

W środku warto trzymać jednostki jawnie:

```text
temperature C
wind_speed m/s
rain mm
pressure hPa
humidity %
```

Nie zakładać, że `20.1` zawsze znaczy stopnie Celsjusza.

---

## 39. Czas i timezone

Site ma timezone:

```yaml
site:
  timezone: Europe/Warsaw
```

W bazie najlepiej trzymać timestamp w UTC albo timezone-aware ISO8601.

Dashboard może konwertować na lokalny czas site.

To ważne przy zmianie czasu lato/zima.

---

## 40. Retencja danych

Nie wszystko musi być przechowywane wiecznie.

Przykład:

```text
raw_events: 7-30 dni
measurements: długo
system metrics high resolution: 30 dni
aggregates: długo
media raw: 7 dni
selected media: długo
```

Retencja powinna być konfigurowalna.

---

## 41. Backup

Backup powinien być automatyczny i sprawdzalny.

Nie wystarczy:

```text
backup istnieje
```

Lepiej:

```text
backup timestamp
backup size
backup status
backup destination
```

I okresowo testować restore.

---

## 42. Grafana i Prometheus

To przyszłość, nie MVP.

Prometheus zbiera metrics:

```text
outpost_sensor_last_seen_seconds
outpost_disk_free_bytes
outpost_node_up
outpost_backup_age_seconds
```

Grafana robi techniczne dashboardy.

Ale publiczny dashboard Outposta nadal jest własny.

---

## 43. Energy, PV i EV charging

Energia dobrze pasuje do części `Outpost`, bo opisuje kondycję i przepływy energii fizycznej instalacji.

Przykładowe przyszłe dane:

```text
pv_power
pv_energy_today
grid_import_power
grid_export_power
battery_state_of_charge
battery_charge_power
ev_charging_power
ev_session_energy
```

Integracje powinny być adapterami lub agentami. Core nie powinien wiedzieć, czy falownik jest konkretnego producenta.

Na początku integracja jest read-only: Outpost obserwuje i zapisuje. Sterowanie ładowaniem czy energią należy do późniejszej, jawnie zaprojektowanej warstwy control/automation.

---

## 44. Home Assistant i smart-home

Home Assistant może być bardzo dobrym źródłem informacji o stanie fizycznego Outposta.

Outpost może pobierać wybrane encje, np.:

```text
shutter_position
switch_state
technical_temperature
integration_health
```

i mapować je na własne generic measurements/status/events.

W drugą stronę HA może dostać z Outposta np. pogodę, Astro Score, stan all-sky czy node health.

Granica odpowiedzialności jest ważna:

```text
Sky Weather Outpost = telemetry / history / correlation / presentation
Home Assistant      = home automation / device control
```

Dzięki temu nie budujemy drugiego Home Assistanta tylko dlatego, że chcemy zobaczyć stan rolety obok produkcji PV.

---

## 45. Jak rozwijać projekt bez chaosu

Każdy nowy pomysł powinien przejść pytania:

```text
Czy to należy do Sky, Weather albo fizycznego Outpostu?
Czy da się to opisać jako device / measurement / event / media / status?
Czy to wymaga nowego core concept?
Czy wystarczy adapter/module?
Czy to jest potrzebne w obecnym milestone?
```

Jeśli odpowiedź brzmi:

```text
"fajny pomysł, ale nie teraz"
```

to trafia do Future Modules.

---

## 46. Jak pracować z Copilotem

Przed większym zadaniem Copilot powinien przeczytać:

```text
README.md
ARCHITECTURE.md
ROADMAP.md
MVP.md
TECH_STACK.md
copilot-instructions.md
```

Dobry prompt:

```text
Read the project architecture and roadmap first.
Implement only MVP v0.1 scope.
Do not introduce MQTT, Docker, Kubernetes, media processing or future modules.
Keep the core generic and configurable.
Add tests.
```

---

## 47. Najważniejsze zasady projektu

Jeśli masz zapamiętać tylko kilkanaście rzeczy:

```text
1. Build small, design wide.
2. Sky / Weather / Outpost opisują trzy widoki tej samej fizycznej instalacji.
3. Core jest generic.
4. Site, node, device są podstawą świata.
5. Raw events i measurements są osobno.
6. JSON jest kontraktem danych.
7. YAML jest configiem.
8. SQLite jest lokalne.
9. NAS jest backup/archive.
10. Media są plikami.
11. API jest versioned.
12. Public i internal są rozdzielone.
13. CLI i WWW korzystają z tego samego modelu/API stanu.
14. Logi, health i backup są core features.
15. Hardware-specific logic siedzi w adapterach/agentach.
16. Home Assistant steruje; Outpost obserwuje i koreluje.
17. Native systemd first.
18. Docker/Kubernetes later.
19. MVP ma być naprawdę MVP.
20. Future Modules nie rozszerzają v0.1.
```

---

## 48. Ostateczny mentalny model

```text
                      SKY WEATHER OUTPOST
                               |
            +------------------+------------------+
            |                  |                  |
           SKY              WEATHER            OUTPOST
            |                  |                  |
      sky / astro         environment        site health
      observations        and weather        infrastructure
            |                  |                  |
            +------------------+------------------+
                               |
                        generic core
                               |
             site / node / device / event
          measurement / media_asset / status
                               |
              SQLite / API / services / agents
                               |
                   +-----------+-----------+
                   |                       |
                  WWW                     CLI
```

Jeśli ten obraz pozostanie prawdziwy, projekt może rosnąć bardzo długo bez zmiany swojej tożsamości.

Na początku będzie to termometr z API.

Potem stacja pogodowa.

Potem all-sky.

Potem astro-agent.

Potem być może energia, Home Assistant i kolejne elementy infrastruktury.

Ale nadal będzie to ten sam system:

```text
Sky Weather Outpost
```

czyli mały cyfrowy posterunek, który wie, co dzieje się nad nim, wokół niego i z nim samym.