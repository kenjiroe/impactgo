-- ImpactGo — SQLite schema (MVP)
-- ใช้ SQLite เพราะข้อมูล < 10k แถว/ปี, ไฟล์เดียว, backup ง่าย
-- วันที่เก็บเป็น TEXT 'YYYY-MM-DD' (ISO) เวลา 'HH:MM'
-- เวลาในระบบทั้งหมดเป็น Asia/Bangkok

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------------
-- 1) ทะเบียนแหล่งข้อมูล
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS source (
    id              INTEGER PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,          -- impact | ttm | ticketmaster | exhibition | mtthani | manual | holiday
    name            TEXT NOT NULL,
    base_url        TEXT,
    kind            TEXT NOT NULL CHECK (kind IN ('scrape','manual','static')),
    trust_rank      INTEGER NOT NULL DEFAULT 3,    -- 1 = สูงสุด
    fetch_freq      TEXT NOT NULL DEFAULT 'daily', -- daily | twice_daily | weekly | never
    enabled         INTEGER NOT NULL DEFAULT 1 CHECK (enabled IN (0,1)),
    notes           TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------------
-- 2) เอกสารดิบ (snapshot) — เก็บ hash ไว้ตรวจการเปลี่ยนแปลง
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS raw_document (
    id              INTEGER PRIMARY KEY,
    source_id       INTEGER NOT NULL REFERENCES source(id),
    url             TEXT NOT NULL,
    fetched_at      TEXT NOT NULL,
    http_status     INTEGER,
    content_hash    TEXT NOT NULL,                 -- sha256
    storage_path    TEXT,                          -- data/snapshots/...
    bytes           INTEGER,
    UNIQUE (source_id, url, content_hash)
);
CREATE INDEX IF NOT EXISTS ix_raw_source_time ON raw_document(source_id, fetched_at DESC);

-- ---------------------------------------------------------------------------
-- 3) ข้อมูลก่อนแปลง
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_raw (
    id              INTEGER PRIMARY KEY,
    raw_document_id INTEGER NOT NULL REFERENCES raw_document(id) ON DELETE CASCADE,
    title_raw       TEXT NOT NULL,
    date_text       TEXT,
    venue_text      TEXT,
    time_text       TEXT,
    price_text      TEXT,
    category_text   TEXT,
    detail_url      TEXT,
    parse_warnings  TEXT                           -- JSON array ของปัญหาที่พบ
);
CREATE INDEX IF NOT EXISTS ix_rawdoc ON event_raw(raw_document_id);

-- ---------------------------------------------------------------------------
-- 4) สถานที่ + ความจุ
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS venue (
    id              INTEGER PRIMARY KEY,
    code            TEXT NOT NULL UNIQUE,          -- ARENA | CHALLENGER | EXHIBITION | FORUM | THUNDER | LAKESIDE | SPEEDPARK | PORTAL | OTHER
    name_th         TEXT NOT NULL,
    name_en         TEXT,
    building_weight REAL NOT NULL DEFAULT 0.8,     -- ใช้ในสูตรคะแนน
    capacity_seat   INTEGER,                       -- ที่นั่ง (ถ้ามี)
    capacity_est    INTEGER,                       -- ประมาณการคนต่อวัน
    hall_from       INTEGER,
    hall_to         INTEGER,
    parking_note    TEXT,
    notes           TEXT
);

-- ---------------------------------------------------------------------------
-- 5) งาน (canonical)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event (
    id              INTEGER PRIMARY KEY,
    identity_hash   TEXT NOT NULL UNIQUE,          -- sha1(title_norm|venue|start_date)
    title           TEXT NOT NULL,
    title_norm      TEXT NOT NULL,
    venue_id        INTEGER NOT NULL REFERENCES venue(id),
    hall_from       INTEGER,
    hall_to         INTEGER,
    hall_confidence TEXT NOT NULL DEFAULT 'low' CHECK (hall_confidence IN ('high','medium','low')),
    start_date      TEXT NOT NULL,
    end_date        TEXT NOT NULL,
    start_time      TEXT,
    end_time        TEXT,
    time_confidence TEXT NOT NULL DEFAULT 'default' CHECK (time_confidence IN ('high','medium','default')),
    category        TEXT NOT NULL DEFAULT 'unknown'
                    CHECK (category IN ('concert','public_fair','trade','congress','exam','sport','family','special','unknown')),
    audience        TEXT NOT NULL DEFAULT 'unknown'
                    CHECK (audience IN ('public','trade_only','mixed','unknown')),
    is_free         INTEGER CHECK (is_free IN (0,1)),
    price_min       INTEGER,
    price_max       INTEGER,
    organizer       TEXT,
    detail_url      TEXT,
    description     TEXT,                          -- สรุปจาก og/meta ของหน้างาน (ดึงโดย app/details.py)
    status          TEXT NOT NULL DEFAULT 'confirmed'
                    CHECK (status IN ('confirmed','tentative','cancelled','past')),
    confidence      TEXT NOT NULL DEFAULT 'medium' CHECK (confidence IN ('high','medium','low')),
    verified_by     TEXT,
    last_verified_at TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    CHECK (end_date >= start_date)
);
CREATE INDEX IF NOT EXISTS ix_event_dates ON event(start_date, end_date);
CREATE INDEX IF NOT EXISTS ix_event_venue ON event(venue_id, start_date);

-- ---------------------------------------------------------------------------
-- 6) หลักฐานแหล่งที่มา (many-to-many)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_source (
    id              INTEGER PRIMARY KEY,
    event_id        INTEGER NOT NULL REFERENCES event(id) ON DELETE CASCADE,
    source_id       INTEGER NOT NULL REFERENCES source(id),
    source_ref      TEXT,                          -- URL หรือ id ในต้นทาง
    source_title    TEXT,
    first_seen_at   TEXT NOT NULL DEFAULT (datetime('now')),
    last_seen_at    TEXT NOT NULL DEFAULT (datetime('now')),
    is_primary      INTEGER NOT NULL DEFAULT 0 CHECK (is_primary IN (0,1)),
    conflict        INTEGER NOT NULL DEFAULT 0 CHECK (conflict IN (0,1)),
    UNIQUE (event_id, source_id, source_ref)
);
CREATE INDEX IF NOT EXISTS ix_es_event ON event_source(event_id);

-- ---------------------------------------------------------------------------
-- 7) วันของงาน (1 แถวต่อวัน) — ใช้คำนวณคะแนน
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS event_day (
    event_id        INTEGER NOT NULL REFERENCES event(id) ON DELETE CASCADE,
    date            TEXT NOT NULL,
    PRIMARY KEY (event_id, date)
);
CREATE INDEX IF NOT EXISTS ix_day_date ON event_day(date);

-- ---------------------------------------------------------------------------
-- 8) คะแนนรายวัน
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS day_score (
    date            TEXT PRIMARY KEY,
    event_count     INTEGER NOT NULL DEFAULT 0,
    building_count  INTEGER NOT NULL DEFAULT 0,
    buildings       TEXT,                          -- JSON array
    raw_score       REAL NOT NULL DEFAULT 0,
    level           INTEGER NOT NULL DEFAULT 0 CHECK (level BETWEEN 0 AND 4),
    headline        TEXT,
    explanation     TEXT,                          -- JSON: รายละเอียดที่มาของคะแนน
    computed_at     TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS hour_risk (
    id              INTEGER PRIMARY KEY,
    date            TEXT NOT NULL REFERENCES day_score(date) ON DELETE CASCADE,
    time_from       TEXT NOT NULL,                 -- 'HH:MM'
    time_to         TEXT NOT NULL,
    direction       TEXT NOT NULL CHECK (direction IN ('in','out')),
    level           INTEGER NOT NULL CHECK (level BETWEEN 0 AND 4),
    reason          TEXT,
    UNIQUE (date, time_from, time_to, direction)
);

-- ---------------------------------------------------------------------------
-- 9) ประวัติการเปลี่ยนแปลง (audit trail)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS change_log (
    id              INTEGER PRIMARY KEY,
    entity          TEXT NOT NULL,                 -- event | event_source | day_score
    entity_id       INTEGER NOT NULL,
    change_type     TEXT NOT NULL CHECK (change_type IN ('insert','update','cancel','merge','verify','override')),
    field           TEXT,
    old_value       TEXT,
    new_value       TEXT,
    reason          TEXT,
    actor           TEXT NOT NULL DEFAULT 'system',-- system | curator:<name>
    changed_at      TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS ix_change_entity ON change_log(entity, entity_id, changed_at DESC);

-- ---------------------------------------------------------------------------
-- 10) ข้อความที่ส่งออก
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS digest (
    id              INTEGER PRIMARY KEY,
    channel         TEXT NOT NULL CHECK (channel IN ('line','email','web')),
    audience        TEXT NOT NULL CHECK (audience IN ('merchant','visitor','commuter')),
    period          TEXT NOT NULL,                 -- 2026-W45
    payload         TEXT NOT NULL,                 -- JSON / ข้อความ
    sent_at         TEXT,
    status          TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft','sent','failed')),
    external_id     TEXT,
    UNIQUE (channel, audience, period)
);

-- ---------------------------------------------------------------------------
-- 11) วันหยุด (ใช้ถ่วงคะแนน)
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS holiday (
    date            TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    kind            TEXT NOT NULL DEFAULT 'public' CHECK (kind IN ('public','observed','special')),
    fetched         TEXT
);

-- ---------------------------------------------------------------------------
-- 12) คิวตรวจสอบสำหรับ curator
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS review_queue (
    id              INTEGER PRIMARY KEY,
    event_id        INTEGER NOT NULL REFERENCES event(id) ON DELETE CASCADE,
    reason          TEXT NOT NULL,                 -- missing_hall | conflict | low_confidence | new_event | cancelled
    priority        INTEGER NOT NULL DEFAULT 2 CHECK (priority BETWEEN 1 AND 3),
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
    resolved_at     TEXT,
    resolved_by     TEXT
);
CREATE INDEX IF NOT EXISTS ix_queue_open ON review_queue(resolved_at, priority);

-- ---------------------------------------------------------------------------
-- Views
-- ---------------------------------------------------------------------------
DROP VIEW IF EXISTS v_event_full;
CREATE VIEW v_event_full AS
SELECT
    e.id, e.title, e.start_date, e.end_date, e.start_time, e.end_time,
    v.code AS venue_code, v.name_th AS venue_name,
    e.hall_from, e.hall_to, e.hall_confidence,
    e.category, e.audience, e.is_free, e.price_min, e.price_max,
    e.status, e.confidence, e.last_verified_at,
    (SELECT group_concat(s.code, ',')
       FROM event_source es JOIN source s ON s.id = es.source_id
      WHERE es.event_id = e.id) AS sources
FROM event e JOIN venue v ON v.id = e.venue_id;

DROP VIEW IF EXISTS v_calendar;
CREATE VIEW v_calendar AS
SELECT d.date,
       d.level,
       d.event_count,
       d.buildings,
       d.headline,
       (SELECT group_concat(e.title, ' | ')
          FROM event_day ed JOIN event e ON e.id = ed.event_id
         WHERE ed.date = d.date AND e.status = 'confirmed') AS events
FROM day_score d
ORDER BY d.date;

-- ---------------------------------------------------------------------------
-- Seed: สถานที่ (ค่าน้ำหนักอ้างอิง ARCHITECTURE.md §7.2)
-- ---------------------------------------------------------------------------
INSERT OR IGNORE INTO venue (code, name_th, name_en, building_weight, capacity_seat, capacity_est) VALUES
 ('ARENA',      'อิมแพ็ค อารีน่า',                    'IMPACT Arena',             3.0, 12000, 12000),
 ('CHALLENGER', 'อิมแพ็ค ชาเลนเจอร์',                 'IMPACT Challenger',        2.5, NULL,  9000),
 ('EXHIBITION', 'ศูนย์แสดงสินค้า อิมแพ็ค เมืองทองธานี','IMPACT Exhibition Center', 2.0, NULL,  12000),
 ('THUNDER',    'ธันเดอร์โดม',                        'Thunder Dome',             1.5, NULL,  3500),
 ('FORUM',      'อิมแพ็ค ฟอรั่ม',                     'IMPACT Forum',             1.2, NULL,  3000),
 ('LAKESIDE',   'ริมทะเลสาบ เมืองทองธานี',            'IMPACT Lakeside',          0.8, NULL,  2000),
 ('SPEEDPARK',  'อิมแพ็ค สปีด พาร์ค',                 'IMPACT Speed Park',        0.8, NULL,  1500),
 ('PORTAL',     'เดอะ พอร์ทอล ไลฟ์สไตล์ คอมเพล็กซ์',  'The Portal',               0.8, NULL,  1000),
 ('OTHER',      'อื่น ๆ ในเมืองทองธานี',              'Other',                    0.8, NULL,  NULL);

INSERT OR IGNORE INTO source (code, name, base_url, kind, trust_rank, fetch_freq, notes) VALUES
 ('impact',      'IMPACT Event Calendar',   'https://www.impact.co.th/th/visitors/event-calendar', 'scrape', 1, 'twice_daily', 'แหล่งหลัก; 2 หน้า; ไม่มีฮอลล์'),
 ('ttm',         'ThaiTicketMajor',         'https://m.thaiticketmajor.com',                        'scrape', 2, 'daily',       'คอนเสิร์ต/งานบันเทิง'),
 ('ticketmaster','Ticketmaster TH',         'https://ticketmaster.co.th',                           'scrape', 2, 'weekly',      'งานประกาศล่วงหน้านาน'),
 ('exhibition',  'ThailandExhibition',      'https://www.thailandexhibition.com',                   'scrape', 3, 'daily',       'งานแสดงสินค้า; ต้องใช้ Playwright'),
 ('mtthani',     'Muang Thong Thani site',  'https://www.muangthongthani.com',                      'scrape', 4, 'weekly',      'ใช้เฉพาะ hall/time; ข้อมูลค้าง'),
 ('manual',      'Curator (FB/LINE/แจ้งงาน)','',                                                    'manual', 2, 'daily',       'งานที่ไม่มีในระบบ'),
 ('holiday',     'ปฏิทินวันหยุดราชการ',      '',                                                    'static', 1, 'weekly',      'ใช้ถ่วงคะแนน');
