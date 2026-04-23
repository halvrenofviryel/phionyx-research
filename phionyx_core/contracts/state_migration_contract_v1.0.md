# Phionyx State Migration Contract v1.0

**Owner:** Phionyx Core

**Status:** DRAFT → READY FOR INTERNAL RATIFICATION

**Scope:** Persist edilen state şemaları, sürümleme, migrasyon kuralları, geriye/ileri uyumluluk

**Non-Scope:** HTTP/API, ürün adapter'ları, UI, veri taşıma job'ları

---

## 0) Amaç (Neyi garanti eder?)

1. State şeması değişse bile **Kernel determinism**, **45-blok telemetry düzeni**, **privacy invariant'ları** bozulmaz.

2. Eski state'ler **tanımlı kurallarla** yeni şemaya taşınır; "sessiz kırılma" yoktur.

3. Migrasyonlar **kanıt üretir**: hangi state hangi kuralla dönüştü, açıkça kayıt altına alınır.

---

## 1) Tanımlar

* **State Record:** Persist edilen minimal çekirdek durum objesi (Φ hariç).

* **Schema Version:** State'in yapısal versiyonu (ör. `state_schema_version`).

* **Migration:** `Vn → Vn+1` deterministik dönüşüm fonksiyonu.

* **Upgrade Path:** Ardışık migrasyon zinciri (V1→V2→V3).

* **Downgrade:** Ürün açısından **desteklenmez** (kural 6).

---

## 2) State Şema Sürümleme Kuralları

### 2.1 Zorunlu Alanlar

Her state kaydı şu alanları taşır:

* `state_schema_version` (semver benzeri ama integer tercih edilir: 1,2,3)

* `created_at_utc`, `updated_at_utc`

* `participant_id` (scope izolasyonu için)

* `trace_anchor` (minimum causality bağlantısı; PII içermez)

* **Persist edilebilir metrikler:** `entropy`, `amplitude`, `coherence`, `time_pressure`

* **Persist edilemez:** `phi`, ham prompt, ham kullanıcı metni, PII türevleri

### 2.2 Semantik Versiyonlama

* **MAJOR (breaking):** Persist edilen alanların anlamı değişiyorsa veya determinism etkileniyorsa. Normalde **yasak**, gerekiyorsa "Re-certification" gerektirir.

* **MINOR:** Yeni alan eklenir (default ile).

* **PATCH:** Alan isimlendirme/dokümantasyon; davranış değişimi yok.

---

## 3) Migrasyon Politikası (Determinism-First)

### 3.1 Migrasyonlar Deterministiktir

Aynı input state ⇒ aynı output state.

* RNG yasak

* "şu anki zaman" gibi değişkenler migrasyon çıktısını etkileyemez (yalnızca metadata alanlarında kullanılır; içerik dönüşümünde değil).

### 3.2 Migrasyonlar Side-Effect Free'dir

Migrasyon fonksiyonu:

* dış servis çağırmaz

* DB yazmaz (sadece dönüşüm üretir)

* network / filesystem bağımlılığı yoktur

### 3.3 Migrasyonlar İspat Üretir (Evidence)

Her migrasyon çalıştığında şu artefact üretilir:

* `migration_manifest.json` (from_version, to_version, git_sha, ruleset_hash)

* `migration_diff.json` (alan bazında delta; PII-safe)

* `migration_stats.json` (kaç kayıt, kaç default, kaç drop, kaç warning)

---

## 4) Uyumluluk Matrisi

### 4.1 Backward Read Compatibility

Kernel, **en az N-1** sürümü okuyup upgrade edebilmelidir. (Öneri: N-2, enterprise için daha iyi)

* Okuma sırasında: `upgrade_in_memory` desteklenir.

* Persist sırasında: her zaman **current version** yazılır.

### 4.2 Forward Compatibility

Yeni kernel'in eski state'i okuması hedeflenir;

eski kernel'in yeni state'i okuması **garanti edilmez**.

---

## 5) Veri Kaybı ve Alan Yönetimi

### 5.1 Alan Ekleme

* Yeni alanlar **default** ile gelir.

* Default deterministik ve policy'den bağımsız olmalıdır.

### 5.2 Alan Kaldırma (Deprecation)

* "Deprecated" alanlar önce **en az 1 minor** sürüm boyunca tutulur.

* Telemetry'de `state_deprecation_warnings` olarak görünür.

* Sonrasında migrasyon ile kaldırılır; diff artefact'ta kanıtlanır.

### 5.3 Alan Yeniden Adlandırma

* Bir sürüm boyunca alias (read) desteklenir.

* Write her zaman yeni isimle yapılır.

---

## 6) Downgrade Politikası

* **Kural:** State downgrade desteklenmez.

  Gerekirse: export/import üzerinden "fresh bootstrap" yapılır.

---

## 7) Migrasyon Tetikleme Mekanizması

Migrasyon iki yerde tetiklenebilir:

1. **Read-time Upgrade (önerilen default)**

   * Kernel state'i okur, gerekirse RAM'de current'a taşır.

2. **Batch Migration (ops)**

   * Büyük sürüm geçişlerinde offline job.

   * Bridge/ürün değil, ops pipeline yapar.

Her iki durumda da evidence artefact üretimi zorunludur.

---

## 8) Test ve Gate Zorunlulukları (Release Bloklayıcı)

Aşağıdakiler L1/L4 kapsamında **hard gate** olmalıdır:

1. **Deterministic migration test**

   * aynı eski state 100 kez ⇒ aynı hash

2. **Upgrade chain test**

   * V1→V2→…→VN path'i çalışıyor mu?

3. **Non-persistence guard**

   * migrasyon sırasında Φ veya PII persist edilmediğinin kanıtı

4. **Isolation invariant**

   * participant scope dışına taşan alan yok

5. **Telemetry evidence**

   * migrasyon event'leri telemetry_snapshot'ta görünür

---

## 9) Sözleşme İhlali ve Reaksiyon

* **Missing migration for older version:** FAIL FAST (turn reject)

* **Schema mismatch / unknown field risk:** SAFE MODE + explicit telemetry

* **PII/Φ detected in state:** SECURITY FAIL + quarantine

---

## 10) Uygulama Sırası (Core pipeline'a dokunmadan)

1. **State schema version alanını standardize et** (tek kaynak: core state model/schema)

2. **`migrations/` registry**: `Vn_to_Vn1(state) -> state` saf fonksiyonları

3. **Evidence pack**: manifest+diff+stats üretimi (PII-safe)

4. **Hard gate testleri**: determinism + chain + privacy

5. Doküman: `docs/contracts/STATE_MIGRATION_CONTRACT.md` (Core)

---

**Version:** 1.0  
**Date:** 2025-12-29  
**Location:** `echo-server/app/core/contracts/state_migration_contract_v1.0.md`

