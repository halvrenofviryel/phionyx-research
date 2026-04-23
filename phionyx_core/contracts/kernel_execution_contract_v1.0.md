# Phionyx Kernel Execution Contract v1.0

**Status:** DRAFT → READY FOR INTERNAL RATIFICATION

**Scope:** Phionyx Core (Kernel)

**Non-Scope:** Product logic, HTTP/API, UI, client SDK'lar

---

## 0. Tanımlar

* **Kernel:** Ürünlerden ve taşıyıcı protokollerden bağımsız, deterministik bilişsel yürütme motoru.

* **Bridge:** Kernel'e zarf (envelope) taşıyan ve I/O yapan katman.

* **Capability Profile:** Kernel'in davranışını belirleyen, ürün kimliği içermeyen profil.

* **31-Blok Pipeline:** Canonical yürütme sırası; değişmez.

---

## 1. Değişmez Mimari İlkeler (Non-Negotiable)

### 1.1 Kernel Ürün Bilmez

* **Kural:** Kernel kodunda ürün adı, ürün türü, adapter adı **olamaz**.

* **Kanıt:** Core dizininde ürün string'i/branch'i bulunmaması (static scan).

* **İhlal Sonucu:** Build FAIL.

### 1.2 31-Blok Sözleşmesi Değişmezdir

* **Kural:** 31 blok **her turn** initialize edilir.

* **Durumlar:** `executed | skipped_by_policy | not_executed`.

* **Kanıt:** Telemetry snapshot'ta 31 blok görünürlüğü.

* **İhlal:** Audit FAIL.

### 1.3 Determinizm Zorunludur

* **Kural:** Aynı `state + trace + capability` ⇒ aynı bilişsel yol.

* **Kanıt:** Replay/Fork testleri (100x).

* **İhlal:** Release BLOCK.

---

## 2. Yürütme Döngüsü (Tek Turn – Zorunlu Adımlar)

```
Input

 → State Reconstruction

 → Energy Field Update

 → Deterministic Cognitive Path Selection

 → Pre-Response Damping & Governance

 → Response Commit

 → State Normalization (NO Φ persistence)
```

* **Hiçbir adım opsiyonel değildir.**

---

## 3. Durum ve Bellek İlkeleri

### 3.1 Φ (Phi) Non-Persistence

* **Kural:** Φ **hesaplanır**, **persist edilmez**.

* **Persist Edilebilir:** entropy, amplitude, coherence, time-pressure.

* **Kanıt:** State schema + storage scan.

* **İhlal:** Security FAIL.

### 3.2 İzolasyon

* **Kural:** Participant'lar arası state sızıntısı **imkânsız**.

* **Kanıt:** Cross-participant replay testleri.

* **İhlal:** Critical.

---

## 4. Pre-Response Damping (Filtre Değil, Sönümleme)

* **Eşikler:** enerji, entropi, zaman baskısı, güven.

* **Aksiyonlar:** sadeleştir | yavaşlat | güvenli moda çek.

* **Kural:** Yanıt **üretilmeden önce** uygulanır.

* **Kanıt:** Telemetry'de pre-response kayıtları.

* **İhlal:** Trust FAIL.

---

## 5. Zamanın Fiziksel Yorumu (Semantic Time)

* **Kural:** Zaman yalnızca timestamp değildir; bilişsel kuvvettir.

* **Kanıt:** Time-pressure metriklerinin path selection'a etkisi.

* **İhlal:** Determinizm riski.

---

## 6. Capability Gating

* **Kural:** Bloklar **silinmez**; policy ile **bypass** edilir.

* **Girdi:** `CapabilityProfileID` (ürün kimliği yok).

* **Kanıt:** Telemetry status alanları.

* **İhlal:** Audit FAIL.

---

## 7. Hata Tanımı (Net)

| Durum                       | Kabul |
| --------------------------- | ----- |
| Yanıt gecikmesi / sadeleşme | ✅     |
| Güvenli moda geçiş          | ✅     |
| Yanlış ama ikna edici cevap | ❌     |
| Determinizm kırılması       | ❌     |
| Φ persist                   | ❌     |
| İzlenemeyen karar           | ❌     |

---

## 8. Kanıt & Test Zorunlulukları

* **Invariant Suite:** Determinizm, Φ non-persistence, izolasyon, 46-blok.

* **Replay/Fork:** Zaman/yük/model varyasyonu.

* **Degradation:** Timeout, hallucination spike, spam.

* **No Silent Failure:** Her risk telemetry'de görünür.

---

## 9. Sürümleme ve Uyumluluk

* **MAJOR:** İnvariant değişimi (normalde yasak).

* **MINOR:** Yeni capability, geriye uyumlu.

* **PATCH:** Bugfix, davranış değişimi yok.

---

## 10. Yürürlük

Bu sözleşme **Core'a girdiği an** tüm bridge'ler ve ürünler için bağlayıcıdır.

---

**Version:** 1.0  
**Date:** 2025-12-29  
**Location:** `echo-server/app/core/contracts/kernel_execution_contract_v1.0.md`

