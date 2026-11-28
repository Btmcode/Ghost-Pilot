#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GhostPilot NEX — WINDOWS'A ÖZEL TESTLER (Windows host'ta çalıştırılır).

    python testler_windows.py

Bu betik Linux/Xvfb'de ÇALIŞTIRILAMAZ (PowerShell, taskkill /T, uiautomation,
Hyper-V VMConnect gerektirir). Sonuçlar TEST_RAPORU.md'nin 9. bölümüne
ayrı olarak işlenmelidir.
"""
import os, sys, time, json, platform

SONUC = []
def T(ad, kosul, ek=""):
    SONUC.append({"test": ad, "gecti": bool(kosul), "ek": str(ek)[:120]})
    print(("  ✓ " if kosul else "  ✗ ") + ad + ("  " + str(ek)[:120] if ek else ""))

if platform.system() != "Windows":
    print("BU BETİK YALNIZ WINDOWS'TA ÇALIŞIR. Durduruldu.")
    sys.exit(2)

import ghostpilot as g

print("=== W1 · PowerShell oturumu ===")
r = g.call_tool("start_process", {"command": "powershell -NoLogo -NoProfile", "label": "ps"})
T("PowerShell başladı", bool(r.get("session_id")), r.get("session_id"))
sid = r.get("session_id")
if sid:
    w = g.call_tool("interact_with_process", {"session_id": sid,
                                              "input": "Write-Output 'NEX-PS-HAZIR'"})
    T("PowerShell stdin/cevap", "NEX-PS-HAZIR" in json.dumps(w, ensure_ascii=False))
    o = g.call_tool("read_process_output", {"session_id": sid, "start": 1, "count": 30})
    T("PowerShell çıktı okundu", isinstance(o.get("satirlar"), list), str(o.get("toplam_satir")))
    g.call_tool("terminate_session", {"session_id": sid})

print("\n=== W2 · cmd.exe + süreç ağacı (taskkill /T) ===")
r = g.call_tool("start_process", {"command": "cmd /K", "label": "cmd"})
T("cmd başladı", bool(r.get("session_id")))
if r.get("session_id"):
    k = g.call_tool("kill_process", {"session_id": r["session_id"]})
    T("kill_process süreç ağacı", bool(k.get("ok")), k.get("yontem"))

print("\n=== W3 · Windows API: sınıf / PID / junction ===")
b = g.call_tool("get_window_info", {"title": "Not Defteri"})
if not b.get("ok"):
    b = g.call_tool("get_window_info", {"title": ""})
T("get_window_info PID", bool(b.get("pid")), b.get("pid"))
T("get_window_info süreç adı", bool(b.get("process")), b.get("process"))
T("get_window_info pencere sınıfı", bool(b.get("class")), b.get("class"))

print("\n=== W4 · Gerçek nesne ağacı + tıklama doğrulama ===")
b = g.call_tool("get_window_info", {"title": ""})
f = g.call_tool("find_ui_element", {"text": "Dosya"})   # Not Defteri menüsü
T("nesne ağacı öğe buldu", f.get("ok") is True, str(f.get("oge"))[:100])
if f.get("ok"):
    t = g.call_tool("interact_with_ui_element", {"text": "Dosya", "action": "click", "verify": True})
    T("tıklama yapıldı", bool(t.get("clicked")))
    T("tıklama DOĞRULANDI (ekran değişti)", (t.get("dogrulama") or {}).get("degisti") is True)

print("\n=== W5 · Fiziksel imleç testi (kabul kriteri 1) ===")
try:
    import ctypes
    pt = ctypes.wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    once = (pt.x, pt.y)
except Exception:
    once = None
time.sleep(0.2)
try:
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    sonra = (pt.x, pt.y)
except Exception:
    sonra = None
ctypes.windll.user32.SetCursorPos(200, 200)     # fareyi bilerek kenara koy
time.sleep(0.1)
t = g.call_tool("interact_with_ui_element", {"text": "Dosya", "action": "click", "verify": False})
ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
son = (pt.x, pt.y)
T("tıklama sırasında fiziksel imleç HAREKET ETMEDİ", son == (200, 200),
  "önce=%s sonra=%s" % ((200, 200), son))

print("\n=== W6 · Hyper-V / VMConnect + gerçek Ubuntu ekranı (kriter 4) ===")
v = g.call_tool("get_window_info", {"title": "Virtual Machine Connection"})
if not v.get("ok"):
    v = g.call_tool("get_window_info", {"title": "Sanal Makine"})
T("VMConnect penceresi bulundu", v.get("ok") is True, v.get("title"))
if v.get("ok"):
    T("VM olarak tanındı", bool(v.get("virtual_machine")), str(v.get("virtual_machine"))[:100])
    r = v.get("rect") or {}
    istemci = [r.get("x", 0), r.get("y", 0), r.get("w", 0), r.get("h", 0)]
    m = g.call_tool("vm_coordinates", {"x": 960, "y": 540, "client": istemci,
                                       "guest_width": 1920, "guest_height": 1080})
    T("misafir→host eşleme", bool(m.get("ok")), m)
    h = g.call_tool("vm_coordinates", {"direction": "host_to_guest",
                                       "x": m.get("host_x"), "y": m.get("host_y"),
                                       "client": istemci,
                                       "guest_width": 1920, "guest_height": 1080})
    T("gidiş-dönüş tutarlı", (h.get("guest_x"), h.get("guest_y")) == (960, 540),
      "(%s,%s)" % (h.get("guest_x"), h.get("guest_y")))

print("\n=== W7 · İzin politikası (Windows yolları) ===")
p = g.call_tool("policy_test", {})
T("policy_test 28/28", p.get("gecen") == 28, "%s/%s" % (p.get("gecen"), p.get("toplam")))
r = g.call_tool("start_process", {"command": "shutdown /s /t 0"})
T("Windows kapatma komutu engellendi", r.get("blocked") is True)
r = g.call_tool("start_process", {"command": "format c:"})
T("C: biçimlendirme engellendi", r.get("blocked") is True)

print("\n=== W8 · Maskeleme ===")
T("mask_test sızıntısız", g.call_tool("mask_test", {}).get("ok") is True)
a = g.call_tool("get_audit_log", {"count": 50})
T("audit sızıntısız", a.get("gizli_sizinti_tespit") == "yok", a.get("gizli_sizinti_tespit"))

gecen = sum(1 for z in SONUC if z["gecti"])
print("\n" + "=" * 60)
print("  WINDOWS SONUÇ: %d geçti, %d başarısız" % (gecen, len(SONUC) - gecen))
json.dump({"gecti": gecen, "toplam": len(SONUC), "testler": SONUC},
          open("windows_test_sonuc.json", "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("  Ayrıntı: windows_test_sonuc.json")
