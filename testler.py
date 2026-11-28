#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""GhostPilot NEX — bütünleşik test koşucusu (Faz 1-7).

Çalıştırma:
    python3 testler.py            # hepsi
    python3 testler.py --modul    # yalnız modül testleri (arama/dosya/cihaz/güvenlik)

NOT: Linux/Xvfb testleridir. Windows'a özgü testler (PowerShell, Hyper-V,
gerçek nesne ağacı, VMConnect) AYRI raporlanır ve burada ÇALIŞTIRILMAZ.
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ghostpilot as g
g.CFG["read_roots"] = [os.path.expanduser("~"), os.getcwd()]
g.CFG["write_roots"] = [os.path.expanduser("~")]
gecen=0; basarisiz=[]
def T(ad, kosul, ek=""):
    global gecen
    if kosul: gecen+=1; print(f"  ✓ {ad} {ek}")
    else: basarisiz.append(ad); print(f"  ✗ {ad} {ek}")

print("=== A · ARAÇ SAYISI / ALIAS ===")
T("araç sayısı 81", len(g.TOOLS)==81, f"({len(g.TOOLS)})")
T("alias 33", len(g.ALIAS)==33, f"({len(g.ALIAS)})")
k = [a for a,t in g.ALIAS.items() if t not in g.TOOLS]
T("tüm aliaslar geçerli", not k, str(k))

print("\n=== B · FAZ 1 TERMİNAL ===")
r = g.call_tool("start_process", {"command":"python3 -q -i","label":"repl"})
T("start_process", bool(r.get("session_id")), r.get("session_id",""))
sid=r["session_id"]
w = g.call_tool("interact_with_process", {"session_id":sid,"input":"print('NEX hazir')"})
T("interact_with_process", "NEX hazir" in json.dumps(w, ensure_ascii=False))
o = g.call_tool("read_process_output", {"session_id":sid,"start":1,"count":20})
T("read_process_output", isinstance(o.get("satirlar"), list), f"toplam={o.get('toplam_satir')}")
T("list_sessions", any(x["session_id"]==sid for x in g.call_tool("list_sessions",{})["oturumlar"]))
T("terminate_session", g.call_tool("terminate_session", {"session_id":sid}).get("ok") is not False)

print("\n=== C · FAZ 2 ARAMA ===")
r = g.call_tool("start_search", {"pattern":"*.py","path":os.getcwd(),"mode":"isim"})
T("start_search", bool(r.get("arama_id")), r.get("arama_id",""))
s1 = g.call_tool("get_more_search_results", {"search_id":r["arama_id"],"count":3,"wait_s":2})
T("sayfa 1 (3 sonuç)", len(s1.get("sonuclar",[]))==3, f"toplam={s1.get('toplam_sonuc')}")
s2 = g.call_tool("get_more_search_results", {"search_id":r["arama_id"],"start":s1["sonraki_baslangic"],"count":3})
T("sayfa 2 farklı", [z["yol"] for z in s2["sonuclar"]] != [z["yol"] for z in s1["sonuclar"]])
T("list_searches", any(x["arama_id"]==r["arama_id"] for x in g.call_tool("list_searches",{})["aramalar"]))
T("stop_search", g.call_tool("stop_search", {"search_id":r["arama_id"]}).get("ok") is not False)

print("\n=== D · FAZ 3 DOSYA ===")
import dosya as D
ws=os.path.expanduser("~/ws"); os.makedirs(ws,exist_ok=True)
for i in range(3): D.atomik_yaz(f"{ws}/f{i}.txt", f"deger={i}\n")
r = g.call_tool("read_multiple_files", {"paths":[f"{ws}/f{i}.txt" for i in range(3)]})
T("read_multiple_files", r.get("okunan")==3, f"{r.get('okunan')}/{r.get('istenen')}")
D.atomik_yaz(f"{ws}/k.py","a=1\nb=2\n")
r = g.call_tool("edit_block", {"path":f"{ws}/k.py","blocks":[{"old":"a=1","new":"a=10"},{"old":"b=2","new":"b=20"}]})
T("edit_block çoklu", bool(r.get("degisti")) and "a=10" in open(f"{ws}/k.py").read() and "b=20" in open(f"{ws}/k.py").read())
once=open(f"{ws}/k.py").read()
r = g.call_tool("edit_block", {"path":f"{ws}/k.py","blocks":[{"old":"a=10","new":"a=99"},{"old":"YOKBU","new":"x"}]})
T("blok tutmazsa ATOMİK", not r.get("ok") and open(f"{ws}/k.py").read()==once)
link=f"{ws}/dis"
if not os.path.lexists(link): os.symlink("/etc/passwd", link)
T("link_check dışarı reddi", g.call_tool("link_check", {"path":link})["izinli"] is False)

print("\n=== E · FAZ 4 GUI ===")
b = g.call_tool("get_window_info", {"title":"XXXX"})
T("get_window_info (pencere yok → temiz hata)", b.get("ok") is False and bool(b.get("error")))
v = g.call_tool("vm_coordinates", {"x":960,"y":540,"client":[0,0,800,600],"guest_width":1920,"guest_height":1080})
T("vm_coordinates ölçek", bool(v.get("ok")) and v.get("olcek")==0.4167, str(v.get("olcek")))
h = g.call_tool("vm_coordinates", {"direction":"host_to_guest","x":v["host_x"],"y":v["host_y"],"client":[0,0,800,600],"guest_width":1920,"guest_height":1080})
T("vm gidiş-dönüş tutarlı", (h["guest_x"],h["guest_y"])==(960,540), f"({h['guest_x']},{h['guest_y']})")
f = g.call_tool("find_ui_element", {"text":"OlmayanDugme"})
T("bulunamazsa TAHMİN YOK", f.get("ok") is False and f.get("bulunamadi") is True)

print("\n=== F · FAZ 5 AUDIT ===")
T("mask_test sızıntısız", g.call_tool("mask_test", {})["ok"])
c = g.call_tool("get_recent_tool_calls", {"count":5})
T("get_recent_tool_calls", c["sayi"]>0, f"{c['sayi']} kayıt")
u = g.call_tool("get_usage_stats", {"period":"gun"})
T("get_usage_stats", u["toplam_cagri"]>0, f"{u['toplam_cagri']} çağrı, ort {u['ortalama_ms']} ms")
a = g.call_tool("get_audit_log", {"count":20})
T("get_audit_log sızıntısız", a["gizli_sizinti_tespit"]=="yok")
hud = g.call_tool("nex_hud", {})["hud"]
T("nex_hud canlı", bool(hud.get("action")), str(hud.get("action")))
kayit = g._izleme()._satirlar(30)
zengin = [k for k in kayit if k.get("sure_ms") is not None and k.get("device_id")]
T("kayıtta cihaz+session+süre", len(zengin)>0, f"{len(zengin)} kayıt yapılandırılmış")

print("\n=== G · FAZ 6 CİHAZ ===")
import cihaz as C
r = g.call_tool("add_device", {"device_id":"ubuntu-ai","url":"http://127.0.0.1:17391","name":"Ubuntu AI-Workstation"})
T("add_device", bool(r.get("ok")) and bool(r.get("anahtar")))
anahtar = C._yukle()["ubuntu-ai"]["anahtar"]
C.sunucu_yap("ubuntu-ai", anahtar, lambda t,a: {"ok":True,"tool":t,"cihaz":"ubuntu-ai"}, port=17391)
time.sleep(0.4)
T("device_health online", g.call_tool("device_health", {"device_id":"ubuntu-ai"})["durum"]=="online")
T("device_call izinli", g.call_tool("device_call", {"device_id":"ubuntu-ai","tool":"status"})["ok"])
T("device_call izinsiz RED", g.call_tool("device_call", {"device_id":"ubuntu-ai","tool":"start_process"}).get("reddedildi") is True)
T("list_devices", g.call_tool("list_devices", {})["sayi"]>=1)

print("\n=== H · FAZ 7 GÜVENLİK ===")
p = g.call_tool("policy_test", {})
T("policy_test 28/28", p["gecen"]==28 and bool(p["ok"]), f"{p['gecen']}/{p['toplam']}")
r = g.call_tool("start_process", {"command":"rm -rf /"})
T("tehlikeli komut ENGELLENDİ", r.get("blocked") is True)
o = g.call_tool("approve_action", {"tool":"run_shell","args":{"command":"rm -rf ~/arsiv"}})
T("onay belirteci üretildi", bool(o.get("approval_id")))
r2 = g.call_tool("check_action", {"tool":"run_shell","args":{"command":"rm -rf ~/arsiv"}})
T("check_action onay istiyor", r2["onay_gerekli"] is True)
T("sandbox dışı yazma RED", g.call_tool("edit_block", {"path":"/etc/passwd","old":"a","new":"b"}).get("blocked") is True)
T("salt okunur araç engellenmiyor", g.call_tool("read_multiple_files", {"paths":[ws+"/f0.txt"]}).get("ok") is True)

print("\n=== I · PTY KALICI YAZMA (yeniden başlatma sonrası) ===")
import oturum as O
r = g.call_tool("start_process", {"command": "bash", "label": "pty-kalici"})
sid_pty = r.get("session_id")
o_pty = O.al(sid_pty) if sid_pty else None
T("PTY modu etkin", bool(o_pty and o_pty.get("mod") == "pty"),
  (o_pty.get("mod") if o_pty else "yok"))
w = g.call_tool("interact_with_process", {"session_id": sid_pty,
                                          "input": "echo pty-oncesi"})
T("PTY canlı yazma", "pty-oncesi" in json.dumps(w, ensure_ascii=False))
# sunucu yeniden başlatma benzetimi
O._OTURUMLAR.clear(); O._YUKLENDI = False
k = O.kurtar()
T("kurtarma: oturum geri geldi", k.get("sayi", 0) >= 1, "elle=%s" % k.get("elle_baglanan"))
lst = [z for z in g.call_tool("list_sessions", {})["oturumlar"]
       if z["session_id"] == sid_pty]
T("kurtarılan oturum YAZILABİLİR", bool(lst and lst[0].get("yazilabilir")))
w2 = g.call_tool("interact_with_process", {"session_id": sid_pty,
                                           "input": "echo pty-sonrasi"})
T("KURTARMA SONRASI YAZMA çalışıyor",
  "pty-sonrasi" in json.dumps(w2, ensure_ascii=False))
g.call_tool("interact_with_process", {"session_id": sid_pty, "input": "exit 7"})
time.sleep(2.5)
d = g.call_tool("read_process_output", {"session_id": sid_pty, "start": 1, "count": 5})
T("PTY exit kodu (7)", d.get("exit_code") == 7, "exit=%s" % d.get("exit_code"))

print("\n=== J · SINIRSIZ MOD ===")
sinirsiz_once = bool(g.CFG.get("kota_sinirsiz"))
g.CFG["kota_sinirsiz"] = True
_limit = g.KOTA_UCRETSIZ
g.KOTA_UCRETSIZ = 2
g.kota_sifirla()
kabul = sum(1 for _ in range(6) if g.kota_say())
T("sınırsız modda sınır YOK", kabul == 6, "%d/6 kabul" % kabul)
g.CFG["kota_sinirsiz"] = False
g.kota_sifirla()
kabul2 = sum(1 for _ in range(6) if g.kota_say())
T("sınırsız kapalı → sınır uygulanıyor", kabul2 == 2, "%d/6 kabul" % kabul2)
g.KOTA_UCRETSIZ = _limit
g.kota_sifirla()
g.CFG["kota_sinirsiz"] = sinirsiz_once
kd = g.kota_durum()
T("kota_durum sinirsiz_mod alanı", "sinirsiz_mod" in kd)

print("\n=== K · MODÜLLER ve PANEL ===")
import moduller
mb = moduller.surum_bilgi()
T("8/8 modül yüklü", not mb.get("eksik"), str(mb.get("eksik")))
T("yetenek raporu", "pty_kalici_yazma" in (mb.get("yetenekler") or {}))
pay = g.panel_payload()
T("panel nex payload", bool(pay.get("nex")))
for _k in ("hud", "sessions", "devices", "usage", "security", "modules", "quota"):
    T("panel.nex.%s" % _k, _k in (pay.get("nex") or {}))
h = g.PANEL_HTML
T("panel HTML NEX bölümü", "NEX · canlı durum" in h)
T("panel HTML NEX alanları",
  all(z in h for z in ("nexCihaz", "nexIslem", "nexOturum", "nexArama")))

print(f"\n{'='*60}\n  SONUÇ: {gecen} geçti, {len(basarisiz)} başarısız")
print("  BAŞARISIZ: "+str(basarisiz) if basarisiz else "  TÜM TESTLER GEÇTİ ✓")
