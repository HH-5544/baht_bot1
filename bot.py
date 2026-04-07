"""
BAHT RESIDENCE — Telegram Bot + Mini App
"""
import asyncio, json, logging, os
from pathlib import Path
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

BOT_TOKEN  = os.getenv("BOT_TOKEN",  "")
CHANNEL_ID = os.getenv("CHANNEL_ID", "@bahtresidence")
ADMIN_IDS  = [int(x) for x in os.getenv("ADMIN_IDS", "0").split(",") if x.strip()]
MINIAPP_URL= os.getenv("MINIAPP_URL","https://example.railway.app")
PORT       = int(os.getenv("PORT", 8080))
DATA_FILE  = Path("/tmp/properties.json")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Miniapp HTML (встроен в код) ──────────────────────────────
MINIAPP_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>BAHT RESIDENCE</title>
<script src="https://telegram.org/js/telegram-web-app.js"></script>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
html,body{height:100%;overflow:hidden}
/* Центрирование для браузера (в Telegram игнорируется) */
@media(min-width:500px){
  body{align-items:center;background:#e8e8e8}
  body>*{max-width:420px;width:100%}
  .overlay,.sheet{max-width:420px;left:50%;transform:translateX(-50%)}
  .sheet.on{transform:translateX(-50%) translateY(0)}
  .sheet{transform:translateX(-50%) translateY(100%)}
}
body{font-family:-apple-system,'Roboto','Segoe UI',Arial,sans-serif;font-size:14px;background:#f4f4f4;color:#111;display:flex;flex-direction:column}

.header{background:#0a0a0a;padding:10px 16px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0;border-bottom:2px solid #C9A84C}
.logo-wrap{display:flex;flex-direction:column;line-height:1}
.logo-main{font-size:16px;font-weight:800;color:#C9A84C;letter-spacing:.12em}
.logo-sub{font-size:8px;color:rgba(201,168,76,0.55);letter-spacing:.35em;text-transform:uppercase;margin-top:2px}
.header-icons{display:flex;gap:10px;align-items:center}
.h-icon{width:32px;height:32px;display:flex;align-items:center;justify-content:center;color:rgba(255,255,255,0.5);cursor:pointer;font-size:18px;border-radius:8px;transition:background .2s}
.h-icon:active{background:rgba(201,168,76,0.15);color:#C9A84C}

.location-bar{background:#fff;border-bottom:1px solid #e8e8e8;padding:10px 16px;display:flex;align-items:center;gap:8px;cursor:pointer;flex-shrink:0}
.location-bar svg{width:14px;height:14px;fill:#C9A84C;flex-shrink:0}
.location-bar span{font-size:13px;color:#333;flex:1;font-weight:500}
.location-bar .arr{font-size:10px;color:#aaa}

.search-wrap{background:#fff;border-bottom:1px solid #e8e8e8;padding:8px 14px;flex-shrink:0;display:none}
.search-inner{display:flex;align-items:center;background:#f2f2f2;border-radius:10px;padding:0 11px;gap:8px;height:38px;border:1.5px solid transparent;transition:border-color .2s,background .2s}
.search-inner.focused{border-color:#C9A84C;background:#fff}
.search-inner svg{width:15px;height:15px;fill:#aaa;flex-shrink:0}
.s-input{flex:1;border:none;background:transparent;font-size:14px;color:#111;outline:none;font-family:inherit}
.s-input::placeholder{color:#bbb}
.s-clear{width:18px;height:18px;background:#ccc;border-radius:50%;display:none;align-items:center;justify-content:center;cursor:pointer;color:#fff;font-size:10px;flex-shrink:0}
.s-clear.on{display:flex}

.chips-wrap{background:#fff;border-bottom:1px solid #e8e8e8;padding:9px 0;flex-shrink:0}
.chips{display:flex;gap:7px;overflow-x:auto;padding:0 14px;scrollbar-width:none}
.chips::-webkit-scrollbar{display:none}
.chip{flex-shrink:0;padding:5px 13px;border-radius:20px;font-size:12px;font-weight:500;border:1.5px solid #e2e2e2;background:#fff;color:#666;cursor:pointer;white-space:nowrap;transition:all .2s}
.chip.on{border-color:#C9A84C;background:#C9A84C;color:#000;font-weight:700}

.rhead{background:#fff;padding:8px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e8e8e8;flex-shrink:0}
.rcount{font-size:12px;color:#999}.rcount b{color:#111}
.rsort{display:flex;align-items:center;gap:5px;font-size:12px;color:#999;cursor:pointer}
.rsort svg{width:13px;height:13px;fill:#bbb}

.list{flex:1;overflow-y:auto;-webkit-overflow-scrolling:touch;background:#f4f4f4}
.list::-webkit-scrollbar{width:3px}.list::-webkit-scrollbar-thumb{background:#ddd}

/* Card */
.card{background:#fff;margin:8px 10px 0;border-radius:12px;overflow:hidden;border:1px solid #ebebeb}
.card:last-child{margin-bottom:80px}
.card-top{display:flex;gap:11px;padding:12px 12px 0}
.c-thumb{width:88px;height:88px;border-radius:8px;object-fit:cover;background:#f0ece3;flex-shrink:0;display:flex;align-items:center;justify-content:center;font-size:30px;overflow:hidden;border:1px solid #ebebeb}
.c-thumb img{width:100%;height:100%;object-fit:cover;display:block}
.c-info{flex:1;min-width:0}
.c-name{font-size:14px;font-weight:700;color:#111;line-height:1.3;margin-bottom:2px;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.c-addr{font-size:11px;color:#999;margin-bottom:6px;line-height:1.4;overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical}
.c-badge{display:inline-flex;align-items:center;font-size:10px;font-weight:700;padding:2px 9px;border-radius:4px;letter-spacing:.04em}
.b-new{background:#111;color:#C9A84C;border:1px solid #333}
.b-sale{background:#fffbe6;color:#9a7a30;border:1px solid #ead98a}
.b-rent{background:#e8f4ff;color:#0077bb;border:1px solid #b3d9f7}
.b-comm{background:#f0fff0;color:#2a8a2a;border:1px solid #b3e8b3}

.c-mid{padding:8px 12px 0;display:flex;align-items:flex-end;justify-content:space-between}
.c-price{font-size:17px;font-weight:800;color:#111;line-height:1}
.c-price small{display:block;font-size:10px;color:#aaa;font-weight:400;margin-top:2px}
.c-rooms{font-size:11px;color:#999;text-align:right;line-height:1.5}

.c-agent{margin:9px 12px 0;padding:8px 10px;background:#f9f6ee;border-radius:8px;display:flex;align-items:center;gap:9px;border:1px solid #ede6d3}
.av-sm{width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#C9A84C,#9A7A30);display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:800;color:#000;flex-shrink:0}
.an-sm{flex:1;min-width:0}
.an-name{font-size:11px;font-weight:700;color:#444;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}
.an-role{font-size:10px;color:#aaa}

.c-btns{display:grid;grid-template-columns:1fr 1fr;gap:8px;padding:10px 12px 12px}
.c-btn{padding:10px 0;font-size:12px;font-weight:700;border-radius:8px;text-align:center;cursor:pointer;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:5px;transition:opacity .15s;border:none;font-family:inherit}
.c-btn:active{opacity:.7}
.cb-dark{background:#0a0a0a;color:#C9A84C}
.cb-gold{background:#C9A84C;color:#000}
.c-btn-full{grid-column:span 2;padding:9px 0;font-size:12px;font-weight:600;border-radius:8px;text-align:center;cursor:pointer;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;background:#f5f5f5;color:#555;border:1px solid #e5e5e5;font-family:inherit;transition:opacity .15s}
.c-btn-full:active{opacity:.7}

/* States */
.state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;text-align:center;background:#fff;margin:8px 10px;border-radius:12px}
.state-ico{font-size:46px;margin-bottom:14px}
.state-t{font-size:16px;font-weight:700;margin-bottom:6px}
.state-s{font-size:13px;color:#999;line-height:1.5}
.spinner{width:30px;height:30px;border:3px solid #eee;border-top-color:#C9A84C;border-radius:50%;animation:spin .7s linear infinite;margin:0 auto 14px}
@keyframes spin{to{transform:rotate(360deg)}}

/* Sheet */
.overlay{position:fixed;inset:0;z-index:200;background:rgba(0,0,0,0);pointer-events:none;transition:background .3s}
.overlay.on{background:rgba(0,0,0,.55);pointer-events:all}
.sheet{position:fixed;bottom:0;left:0;right:0;z-index:201;background:#fff;border-radius:18px 18px 0 0;max-height:92vh;display:flex;flex-direction:column;transform:translateY(100%);transition:transform .35s cubic-bezier(.4,0,.2,1)}
.sheet.on{transform:translateY(0)}
.sh-handle{width:38px;height:4px;background:#e0e0e0;border-radius:2px;margin:10px auto 0;flex-shrink:0}
.sh-head{padding:12px 16px 10px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #f0f0f0;flex-shrink:0}
.sh-title{font-size:16px;font-weight:700;padding-right:8px}
.sh-close{width:30px;height:30px;background:#f4f4f4;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;font-size:14px;color:#888;flex-shrink:0}
.sh-scroll{overflow-y:auto;flex:1;-webkit-overflow-scrolling:touch}

.sh-photo{width:100%;height:210px;object-fit:cover;background:#f0ece3;display:flex;align-items:center;justify-content:center;font-size:60px;overflow:hidden}
.sh-photo img{width:100%;height:100%;object-fit:cover;display:block}
.sh-body{padding:16px 16px 4px}
.sh-brow{display:flex;gap:7px;flex-wrap:wrap;margin-bottom:10px}
.sh-name{font-size:21px;font-weight:800;line-height:1.2;margin-bottom:6px}
.sh-price{font-size:27px;font-weight:800;color:#0a0a0a;margin-bottom:14px}
.sh-grid{display:grid;grid-template-columns:1fr 1fr;gap:7px;margin-bottom:14px}
.sg{background:#f8f8f8;border-radius:8px;padding:10px 12px;border:1px solid #efefef}
.sg-l{font-size:9px;color:#aaa;text-transform:uppercase;letter-spacing:.12em;margin-bottom:3px}
.sg-v{font-size:13px;font-weight:700;color:#111;line-height:1.3}
.sh-desc{font-size:13px;color:#777;line-height:1.75;background:#f9f9f9;border-radius:8px;padding:12px;margin-bottom:16px;border:1px solid #f0f0f0}

.agent-box{border:1.5px solid #ede6d3;border-radius:12px;overflow:hidden;margin-bottom:8px}
.agent-hd{background:#0a0a0a;padding:10px 14px;display:flex;align-items:center;gap:8px}
.agent-hd svg{width:14px;height:14px;fill:#C9A84C}
.agent-hd span{font-size:11px;font-weight:700;color:#C9A84C;letter-spacing:.1em;text-transform:uppercase}
.agent-bd{padding:14px}
.agent-row{display:flex;align-items:center;gap:14px;margin-bottom:14px}
.av-lg{width:54px;height:54px;border-radius:50%;background:linear-gradient(135deg,#C9A84C,#9A7A30);display:flex;align-items:center;justify-content:center;font-size:20px;font-weight:800;color:#000;flex-shrink:0}
.ag-name{font-size:15px;font-weight:800;margin-bottom:3px}
.ag-role{font-size:11px;color:#aaa;font-weight:600;text-transform:uppercase;letter-spacing:.08em}
.ag-phone{font-size:13px;color:#555;margin-top:4px}
.agent-cta{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.ag-btn{padding:12px 0;font-size:13px;font-weight:700;border-radius:9px;text-align:center;text-decoration:none;display:flex;align-items:center;justify-content:center;gap:6px;transition:opacity .15s;font-family:inherit}
.ag-btn:active{opacity:.7}
.ab-dark{background:#0a0a0a;color:#C9A84C}
.ab-gold{background:#C9A84C;color:#000}

.sh-actions{padding:12px 16px 20px;border-top:1px solid #f0f0f0;flex-shrink:0}
.sh-main-btn{width:100%;padding:14px;background:#C9A84C;color:#000;font-size:14px;font-weight:800;border-radius:10px;border:none;cursor:pointer;font-family:inherit;letter-spacing:.03em;transition:opacity .15s}
.sh-main-btn:active{opacity:.8}
</style>
</head>
<body>

<div class="header">
  <div class="logo-wrap">
    <div class="logo-main">BAHT RESIDENCE</div>
    <div class="logo-sub">Недвижимость Ташкента</div>
  </div>
  <div class="header-icons">
    <div class="h-icon" id="search-toggle" title="Поиск">
      <svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:none;stroke:currentColor;stroke-width:2.2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.35-4.35"/></svg>
    </div>
    <div class="h-icon" onclick="window.open('https://t.me/bahtresidence','_blank')" title="Telegram">
      <svg viewBox="0 0 24 24" style="width:19px;height:19px;fill:currentColor"><path d="M12 0C5.37 0 0 5.37 0 12s5.37 12 12 12 12-5.37 12-12S18.63 0 12 0zm5.56 8.25-2.03 9.57c-.15.66-.54.82-1.08.51l-3-2.21-1.45 1.39c-.16.16-.3.3-.61.3l.21-3.05 5.56-5.02c.24-.21-.05-.33-.37-.12L7.06 14.28l-2.95-.92c-.64-.2-.65-.64.14-.95l11.53-4.44c.53-.2 1 .13.78.28z"/></svg>
    </div>
  </div>
</div>

<div class="location-bar" id="loc-bar">
  <svg viewBox="0 0 24 24"><path d="M12 2C8.1 2 5 5.1 5 9c0 5.2 7 13 7 13s7-7.8 7-13c0-3.9-3.1-7-7-7zm0 9.5c-1.4 0-2.5-1.1-2.5-2.5S10.6 6.5 12 6.5s2.5 1.1 2.5 2.5-1.1 2.5-2.5 2.5z"/></svg>
  <span id="loc-label">Все районы Ташкента</span>
  <span class="arr">▾</span>
</div>

<div class="search-wrap" id="swrap">
  <div class="search-inner" id="sinner">
    <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.47 6.47 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 5L20.49 19l-5-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
    <input class="s-input" id="sinput" placeholder="Поиск по названию, адресу..." autocomplete="off">
    <div class="s-clear" id="sclear">✕</div>
  </div>
</div>

<div class="chips-wrap">
  <div class="chips" id="chips">
    <div class="chip on" data-f="all">Все</div>
    <div class="chip" data-f="new">🏗 Новостройки</div>
    <div class="chip" data-f="secondary">🏠 Вторичное</div>
    <div class="chip" data-f="rent">🔑 Аренда</div>
    <div class="chip" data-f="commercial">🏢 Коммерция</div>
    <div class="chip" data-f="house">🏡 Дом / Вилла</div>
  </div>
</div>

<div class="rhead">
  <div class="rcount">Объектов: <b id="cnt">0</b></div>
  <div class="rsort" id="rsort">
    <svg viewBox="0 0 24 24"><path d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z"/></svg>
    <span id="sort-lbl">По умолчанию</span>
  </div>
</div>

<div class="list" id="list">
  <div class="state"><div class="spinner"></div><div class="state-t">Загружаем объекты</div><div class="state-s">Пожалуйста, подождите...</div></div>
</div>

<div class="overlay" id="overlay" onclick="closeSheet()"></div>
<div class="sheet" id="sheet">
  <div class="sh-handle"></div>
  <div class="sh-head">
    <div class="sh-title" id="sh-title">Объект</div>
    <div class="sh-close" onclick="closeSheet()">✕</div>
  </div>
  <div class="sh-scroll" id="sh-body"></div>
  <div class="sh-actions" id="sh-actions">
    <button class="sh-main-btn" onclick="contactMain()">📞 Связаться с агентом</button>
  </div>
</div>

<script>
const tg = window.Telegram?.WebApp;
if(tg){tg.ready();tg.expand();}

let ALL=[], filtered=[], activeFil='all', activeSearch='', activeDist='all', sortM='default', curProp=null, sheetMode='prop';

const AGENTS={
  nikitina:   {name:'Никитина Анастасия',          role:'Руководитель',      phone:'+998887263399',tg:'https://t.me/anastasiyabahtresidence',init:'НА'},
  karabaev:   {name:'Карабаев Достон',             role:'Риэлтор',           phone:'+998947283399',tg:'https://t.me/dostonbahtresidence',    init:'КД'},
  sayfullaev: {name:'Сайфуллаев Абдулазиз',        role:'Риэлтор',           phone:'+998950851177',tg:'https://t.me/aza_bahtresidence',      init:'СА'},
  khudoyarov: {name:'Худояров Сиявуш',             role:'Риэлтор',           phone:'+998887473399',tg:'https://t.me/timurflyhomes',          init:'ХС'},
  bokhodirov: {name:'Боходиров Олим',              role:'Риэлтор',           phone:'+998888843399',tg:'https://t.me/olimfly_homes',          init:'БО'},
  abdukhakimova:{name:'Абдухакимова Нодирабегим',  role:'Помощник риэлтора', phone:'+998887474488',tg:'https://t.me/nodira_br',             init:'АН'},
  jumaeva:    {name:'Жумаева Дилнура',             role:'Помощник риэлтора', phone:'+998933067711',tg:'https://t.me/DinaBaxtResidence',      init:'ЖД'},
  efimova:    {name:'Ефимова Анна',                role:'Помощник риэлтора', phone:'+998888143399',tg:'https://t.me/anna1bahtresidence',     init:'ЕА'},
  tillyabaeva:{name:'Тиллябаева Валерия',          role:'Помощник риэлтора', phone:'+998888677117',tg:'https://t.me/valeriya_baht',          init:'ТВ'},
  sarkisov:   {name:'Саркисов Руслан',             role:'Помощник риэлтора', phone:'+998880379933',tg:'https://t.me/ruslan_eldarovich',      init:'СР'},
};

const DEMO=[
  {id:1,name:'Sky Residence',type:'🏗 Новостройка',type_key:'new',price:'$850 000',address:'Мирзо-Улугбекский р-н, ул. Амира Темура, 107',rooms:'280 м² · 4 комн',district:'mirzo',description:'Пентхаус на 22 этаже с панорамным видом на город. Чистовая отделка, закрытая парковка, консьерж.',agent_key:'nikitina',photo:''},
  {id:2,name:'Golden Garden Villa',type:'🏡 Дом / Вилла',type_key:'house',price:'$1 200 000',address:'Юнусабадский р-н, ул. Боги Шамол',rooms:'450 м² · 6 комн · 12 сот',district:'yunusabad',description:'Элитная вилла в закрытом охраняемом посёлке. Бассейн, сад, гараж на 2 машины.',agent_key:'karabaev',photo:''},
  {id:3,name:'Baht Tower — 3BR',type:'🏗 Новостройка',type_key:'new',price:'$290 000',address:'Шайхантахурский р-н, центр города',rooms:'140 м² · 3 комн',district:'shahantahur',description:'Новостройка в центре. Рассрочка 24 месяца от застройщика. Сдача 2025 год.',agent_key:'sayfullaev',photo:''},
  {id:4,name:'Business Plaza Office',type:'🏢 Коммерция',type_key:'commercial',price:'$8 000/мес',address:'Мирабадский р-н, ул. Навои',rooms:'320 м² · Open space',district:'mirabad',description:'Офис класса А. Парковка 5 мест, охрана 24/7, переговорные комнаты.',agent_key:'khudoyarov',photo:''},
  {id:5,name:'City View Residences',type:'🔑 Аренда',type_key:'rent',price:'$4 500/мес',address:'Яшнабадский р-н, пр. Шахрисабз',rooms:'180 м² · 3 комн',district:'yashnabad',description:'Полностью меблированные апартаменты. Этаж 14/18, панорамный вид на город.',agent_key:'bokhodirov',photo:''},
  {id:6,name:'Prestige Townhouse',type:'🏠 Вторичное',type_key:'secondary',price:'$620 000',address:'Чиланзарский р-н, ул. Буюк Ипак Йули',rooms:'320 м² · 5 комн',district:'chilanzar',description:'Двухэтажный таунхаус. Ремонт 2023. Тихий двор, школа и парк рядом.',agent_key:'abdukhakimova',photo:''},
  {id:7,name:'Мирабад — 4 комн.',type:'🏠 Вторичное',type_key:'secondary',price:'$320 000',address:'Мирабадский р-н, ул. Мирабад',rooms:'148 м² · 4 комн',district:'mirabad',description:'Отличное состояние, перепланировка согласована. Возможна ипотека.',agent_key:'sarkisov',photo:''},
  {id:8,name:'Riverside Apartments',type:'🔑 Аренда',type_key:'rent',price:'$1 200/мес',address:'Яшнабадский р-н, ул. Чимкентская',rooms:'65 м² · 2 комн',district:'yashnabad',description:'Уютная квартира с мебелью и техникой. Рядом метро, школы, магазины.',agent_key:'efimova',photo:''},
  {id:9,name:'Tashkent Business Center',type:'🏢 Коммерция',type_key:'commercial',price:'$12 000/мес',address:'Мирабадский р-н, ул. Кичик Халка Йули',rooms:'600 м² · Этаж 5/12',district:'mirabad',description:'БЦ класса А+. Собственный генератор, конференц-зал на 50 чел.',agent_key:'tillyabaeva',photo:''},
  {id:10,name:'Imperial Plaza 2BR',type:'🏠 Вторичное',type_key:'secondary',price:'$185 000',address:'Юнусабадский р-н, 19-й квартал',rooms:'88 м² · 2 комн',district:'yunusabad',description:'Хорошее состояние, евроремонт. Тихий двор, развитая инфраструктура.',agent_key:'jumaeva',photo:''},
];

const DISTRICTS=[
  {k:'all',l:'Все районы Ташкента'},
  {k:'mirabad',l:'Мирабадский'},
  {k:'yunusabad',l:'Юнусабадский'},
  {k:'mirzo',l:'Мирзо-Улугбекский'},
  {k:'chilanzar',l:'Чиланзарский'},
  {k:'yashnabad',l:'Яшнабадский'},
  {k:'shahantahur',l:'Шайхантахурский'},
];

async function fetchProps(){
  try{
    const r=await fetch(location.origin+'/api/properties',{signal:AbortSignal.timeout(4000)});
    if(!r.ok)throw 0;
    const d=await r.json();
    if(d.length)return d;
    throw 0;
  }catch{return DEMO;}
}

function bClass(k){if(k==='new')return 'b-new';if(k==='rent')return 'b-rent';if(k==='commercial')return 'b-comm';return 'b-sale';}
function bText(p){if(p.type_key==='rent')return 'Аренда';if(p.type_key==='new')return 'Новостройка';if(p.type_key==='commercial')return 'Коммерция';return 'Продажа';}
function pxNum(s){const m=(s||'').replace(/\\s/g,'').match(/\\d+/g);return m?parseInt(m.join('')):0;}
function pUrl(f){if(!f)return '';if(f.startsWith('http'))return f;return location.origin+'/api/photo/'+f;}

function thumbHTML(p){
  const url=pUrl(p.photo||'');
  const ico={new:'🏗',secondary:'🏠',commercial:'🏢',rent:'🔑',house:'🏡'}[p.type_key]||'🏠';
  if(url)return `<div class="c-thumb"><img src="${url}" loading="lazy" onerror="this.parentNode.innerHTML='${ico}'" alt=""></div>`;
  return `<div class="c-thumb">${ico}</div>`;
}

function applyFilter(){
  let l=ALL.slice();
  if(activeDist!=='all') l=l.filter(p=>p.district===activeDist);
  if(activeFil!=='all')  l=l.filter(p=>p.type_key===activeFil);
  if(activeSearch){const q=activeSearch.toLowerCase();l=l.filter(p=>(p.name+' '+p.address+' '+(p.description||'')).toLowerCase().includes(q));}
  if(sortM==='asc')  l.sort((a,b)=>pxNum(a.price)-pxNum(b.price));
  if(sortM==='desc') l.sort((a,b)=>pxNum(b.price)-pxNum(a.price));
  filtered=l;
  render();
}

function render(){
  document.getElementById('cnt').textContent=filtered.length;
  const el=document.getElementById('list');
  if(!filtered.length){
    el.innerHTML=`<div class="state"><div class="state-ico">🔍</div><div class="state-t">Ничего не найдено</div><div class="state-s">Попробуйте другой район или фильтр</div></div>`;
    return;
  }
  el.innerHTML=filtered.map(p=>{
    const ag=AGENTS[p.agent_key]||AGENTS.nikitina;
    return `<div class="card">
      <div class="card-top">
        ${thumbHTML(p)}
        <div class="c-info">
          <div class="c-name">${p.name}</div>
          <div class="c-addr">${p.address}</div>
          <span class="c-badge ${bClass(p.type_key)}">${bText(p)}</span>
        </div>
      </div>
      <div class="c-mid">
        <div class="c-price">${p.price}<small>${p.rooms}</small></div>
      </div>
      <div class="c-agent">
        <div class="av-sm">${ag.init}</div>
        <div class="an-sm"><div class="an-name">${ag.name}</div><div class="an-role">${ag.role}</div></div>
      </div>
      <div class="c-btns">
        <button class="c-btn cb-dark" onclick="openProp(${p.id})">📋 Подробнее</button>
        <a class="c-btn cb-gold" href="tel:${ag.phone}">📞 Позвонить</a>
        <a class="c-btn-full" href="${ag.tg}" target="_blank">✈️ Написать агенту в Telegram</a>
      </div>
    </div>`;
  }).join('');
}

function openProp(id){
  curProp=ALL.find(p=>p.id===id)||filtered.find(p=>p.id===id);
  if(!curProp)return;
  sheetMode='prop';
  const ag=AGENTS[curProp.agent_key]||AGENTS.nikitina;
  const url=pUrl(curProp.photo||'');
  const ico={new:'🏗',secondary:'🏠',commercial:'🏢',rent:'🔑',house:'🏡'}[curProp.type_key]||'🏠';

  document.getElementById('sh-title').textContent=curProp.name;
  document.getElementById('sh-actions').style.display='';

  let photoH=url
    ?`<div class="sh-photo"><img src="${url}" alt="" onerror="this.parentNode.innerHTML='${ico}'"></div>`
    :`<div class="sh-photo" style="font-size:62px">${ico}</div>`;

  document.getElementById('sh-body').innerHTML=`
    ${photoH}
    <div class="sh-body">
      <div class="sh-brow">
        <span class="c-badge ${bClass(curProp.type_key)}">${bText(curProp)}</span>
        <span class="c-badge" style="background:#f5f5f5;color:#666;border:1px solid #e5e5e5">${curProp.type}</span>
      </div>
      <div class="sh-name">${curProp.name}</div>
      <div class="sh-price">${curProp.price}</div>
      <div class="sh-grid">
        <div class="sg"><div class="sg-l">Площадь / Комнаты</div><div class="sg-v">${curProp.rooms}</div></div>
        <div class="sg"><div class="sg-l">Тип сделки</div><div class="sg-v">${bText(curProp)}</div></div>
        <div class="sg" style="grid-column:span 2"><div class="sg-l">Адрес</div><div class="sg-v">${curProp.address}</div></div>
      </div>
      ${curProp.description?`<div class="sh-desc">${curProp.description}</div>`:''}
      <div class="agent-box">
        <div class="agent-hd">
          <svg viewBox="0 0 24 24"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8v2.4h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>
          <span>Ответственный агент</span>
        </div>
        <div class="agent-bd">
          <div class="agent-row">
            <div class="av-lg">${ag.init}</div>
            <div>
              <div class="ag-name">${ag.name}</div>
              <div class="ag-role">${ag.role}</div>
              <div class="ag-phone">${ag.phone}</div>
            </div>
          </div>
          <div class="agent-cta">
            <a class="ag-btn ab-dark" href="tel:${ag.phone}">📞 Позвонить</a>
            <a class="ag-btn ab-gold" href="${ag.tg}" target="_blank">✈️ Telegram</a>
          </div>
        </div>
      </div>
    </div>`;

  showSheet();
}

function showSheet(){
  document.getElementById('overlay').classList.add('on');
  document.getElementById('sheet').classList.add('on');
  if(tg){tg.BackButton.show();tg.BackButton.onClick(closeSheet);}
}

function closeSheet(){
  document.getElementById('overlay').classList.remove('on');
  document.getElementById('sheet').classList.remove('on');
  if(tg){tg.BackButton.hide();}
  curProp=null;
}

function contactMain(){
  if(!curProp)return;
  const ag=AGENTS[curProp.agent_key]||AGENTS.nikitina;
  window.open(ag.tg,'_blank');
}

// District picker
document.getElementById('loc-bar').onclick=function(){
  sheetMode='district';
  document.getElementById('sh-title').textContent='Выберите район';
  document.getElementById('sh-actions').style.display='none';
  document.getElementById('sh-body').innerHTML=`<div style="padding:4px 0 20px">`+
    DISTRICTS.map(d=>`<div onclick="pickDistrict('${d.k}','${d.l}')" style="padding:14px 18px;border-bottom:1px solid #f5f5f5;font-size:14px;cursor:pointer;display:flex;align-items:center;justify-content:space-between">
      <span style="font-weight:${activeDist===d.k?'700':'400'};color:${activeDist===d.k?'#C9A84C':'#111'}">${d.l}</span>
      ${activeDist===d.k?'<span style="color:#C9A84C;font-size:16px">✓</span>':''}
    </div>`).join('')+`</div>`;
  showSheet();
};

function pickDistrict(k,l){
  activeDist=k;
  document.getElementById('loc-label').textContent=k==='all'?'Все районы Ташкента':l+' р-н';
  closeSheet();
  document.getElementById('sh-actions').style.display='';
  applyFilter();
}

// Search
let searchOn=false;
document.getElementById('search-toggle').onclick=function(){
  searchOn=!searchOn;
  document.getElementById('swrap').style.display=searchOn?'block':'none';
  if(searchOn)document.getElementById('sinput').focus();
  else{document.getElementById('sinput').value='';activeSearch='';document.getElementById('sclear').classList.remove('on');applyFilter();}
};
document.getElementById('sinput').addEventListener('input',function(){
  activeSearch=this.value.trim();
  document.getElementById('sclear').classList.toggle('on',!!activeSearch);
  document.getElementById('sinner').classList.toggle('focused',!!activeSearch);
  applyFilter();
});
document.getElementById('sclear').onclick=function(){
  document.getElementById('sinput').value='';activeSearch='';
  this.classList.remove('on');
  document.getElementById('sinner').classList.remove('focused');
  applyFilter();
};

// Chips
document.getElementById('chips').addEventListener('click',function(e){
  const c=e.target.closest('.chip');if(!c)return;
  document.querySelectorAll('.chip').forEach(x=>x.classList.remove('on'));
  c.classList.add('on');activeFil=c.dataset.f;applyFilter();
});

// Sort
const SORTS=['default','asc','desc'];
const SLBLS=['По умолчанию','Цена: дешевле','Цена: дороже'];
document.getElementById('rsort').onclick=function(){
  sortM=SORTS[(SORTS.indexOf(sortM)+1)%3];
  document.getElementById('sort-lbl').textContent=SLBLS[SORTS.indexOf(sortM)];
  applyFilter();
};

(async()=>{ALL=await fetchProps();applyFilter();})();
</script>
</body>
</html>
"""

# ── Data ─────────────────────────────────────────────────────
def load():
    try:
        if DATA_FILE.exists():
            return json.loads(DATA_FILE.read_text("utf-8"))
    except: pass
    return []

def save(data):
    try: DATA_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    except Exception as e: log.error(f"Save error: {e}")

def next_id(data): return max((p["id"] for p in data), default=0) + 1

# ── FSM ───────────────────────────────────────────────────────
class Add(StatesGroup):
    photo = State(); name = State(); prop_type = State()
    price = State(); address = State(); rooms = State(); description = State()

TYPES = {"new":"🏗 Новостройка","secondary":"🏠 Вторичное","commercial":"🏢 Коммерция","rent":"🔑 Аренда","house":"🏡 Дом / Вилла"}
router = Router()

# ── Handlers ──────────────────────────────────────────────────
@router.message(Command("start"))
async def cmd_start(msg: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="🏠 Открыть каталог", web_app=WebAppInfo(url=MINIAPP_URL))
    ]])
    await msg.answer("👋 Добро пожаловать в <b>BAHT RESIDENCE</b>!\n\nНажмите кнопку ниже чтобы открыть каталог:", parse_mode="HTML", reply_markup=kb)

@router.message(Command("help"))
async def cmd_help(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    await msg.answer("<b>Команды:</b>\n/add — добавить объект\n/list — список\n/delete [ID] — удалить\n/stats — статистика", parse_mode="HTML")

@router.message(Command("add"))
async def cmd_add(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("❌ Нет доступа."); return
    await msg.answer("📸 Отправьте фото объекта:")
    await state.set_state(Add.photo)

@router.message(Add.photo, F.photo)
async def add_photo(msg: Message, state: FSMContext):
    await state.update_data(photo=msg.photo[-1].file_id)
    await msg.answer("🏷 Название объекта:\n<i>Пример: Sky Residence</i>", parse_mode="HTML")
    await state.set_state(Add.name)

@router.message(Add.photo)
async def add_photo_wrong(msg: Message): await msg.answer("❌ Отправьте фото.")

@router.message(Add.name)
async def add_name(msg: Message, state: FSMContext):
    await state.update_data(name=msg.text.strip())
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏗 Новостройка", callback_data="t:new"),
         InlineKeyboardButton(text="🏠 Вторичное",  callback_data="t:secondary")],
        [InlineKeyboardButton(text="🏢 Коммерция",  callback_data="t:commercial"),
         InlineKeyboardButton(text="🔑 Аренда",     callback_data="t:rent")],
        [InlineKeyboardButton(text="🏡 Дом / Вилла",callback_data="t:house")],
    ])
    await msg.answer("📂 Тип объекта:", reply_markup=kb)
    await state.set_state(Add.prop_type)

@router.callback_query(Add.prop_type, F.data.startswith("t:"))
async def add_type(cb: CallbackQuery, state: FSMContext):
    key = cb.data.split(":")[1]
    await state.update_data(prop_type=TYPES[key], prop_type_key=key)
    await cb.message.answer("💰 Цена:\n<i>Пример: $150 000 или $2 500/мес</i>", parse_mode="HTML")
    await state.set_state(Add.price); await cb.answer()

@router.message(Add.price)
async def add_price(msg: Message, state: FSMContext):
    await state.update_data(price=msg.text.strip())
    await msg.answer("📍 Адрес:\n<i>Пример: Мирабадский р-н, ул. Навои, 45</i>", parse_mode="HTML")
    await state.set_state(Add.address)

@router.message(Add.address)
async def add_address(msg: Message, state: FSMContext):
    await state.update_data(address=msg.text.strip())
    await msg.answer("📐 Площадь и комнаты:\n<i>Пример: 95 м² · 3 комн</i>", parse_mode="HTML")
    await state.set_state(Add.rooms)

@router.message(Add.rooms)
async def add_rooms(msg: Message, state: FSMContext):
    await state.update_data(rooms=msg.text.strip())
    await msg.answer("👤 Ключ агента (или '-' если не нужно):\n<i>nikitina / karabaev / sayfullaev / khudoyarov / bokhodirov / abdukhakimova / jumaeva / efimova / tillyabaeva / sarkisov</i>", parse_mode="HTML")
    await state.set_state(Add.description)

@router.message(Add.description)
async def add_desc(msg: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    txt  = msg.text.strip()
    agent_key = "nikitina"
    desc = ""
    AGENT_KEYS = ["nikitina","karabaev","sayfullaev","khudoyarov","bokhodirov","abdukhakimova","jumaeva","efimova","tillyabaeva","sarkisov"]
    if txt in AGENT_KEYS: agent_key = txt
    elif txt != "-": desc = txt
    props = load()
    prop  = {"id": next_id(props), "name": data["name"], "type": data["prop_type"],
             "type_key": data["prop_type_key"], "price": data["price"],
             "address": data["address"], "rooms": data["rooms"],
             "description": desc, "photo": data["photo"],
             "agent_key": agent_key, "active": True}
    props.append(prop); save(props)
    caption = f"🏠 <b>{prop['name']}</b>\n\n📂 {prop['type']}\n💰 {prop['price']}\n📍 {prop['address']}\n📐 {prop['rooms']}"
    if desc: caption += f"\n\n{desc}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Каталог", web_app=WebAppInfo(url=MINIAPP_URL))],
        [InlineKeyboardButton(text="📞 Связаться", url="https://t.me/bahtresidence")],
    ])
    try: await bot.send_photo(CHANNEL_ID, prop["photo"], caption=caption, parse_mode="HTML", reply_markup=kb)
    except Exception as e: log.error(f"Channel post error: {e}")
    await msg.answer(f"✅ Объект <b>«{prop['name']}»</b> (ID:{prop['id']}) добавлен!", parse_mode="HTML")
    await state.clear()

@router.message(Command("list"))
async def cmd_list(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    props = [p for p in load() if p.get("active")]
    if not props: await msg.answer("📭 Каталог пуст."); return
    lines = [f"#{p['id']} <b>{p['name']}</b> — {p['price']}" for p in props]
    await msg.answer(f"📋 <b>Каталог ({len(props)}):</b>\n\n" + "\n".join(lines), parse_mode="HTML")

@router.message(Command("delete"))
async def cmd_delete(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    parts = msg.text.split()
    if len(parts) < 2 or not parts[1].isdigit():
        await msg.answer("Использование: /delete [ID]"); return
    pid = int(parts[1]); props = load()
    for p in props:
        if p["id"] == pid and p.get("active"):
            p["active"] = False; save(props)
            await msg.answer(f"✅ Объект #{pid} удалён."); return
    await msg.answer(f"❌ Объект #{pid} не найден.")

@router.message(Command("stats"))
async def cmd_stats(msg: Message):
    if msg.from_user.id not in ADMIN_IDS: return
    all_p = load(); active = [p for p in all_p if p.get("active")]
    by_type = {}
    for p in active: by_type[p.get("type","—")] = by_type.get(p.get("type","—"),0)+1
    lines = "\n".join(f"  {k}: {v}" for k,v in by_type.items())
    await msg.answer(f"📊 Всего: {len(all_p)}\nАктивных: {len(active)}\n\n{lines}")

# ── Web handlers ──────────────────────────────────────────────
async def handle_root(request):
    return web.Response(text=MINIAPP_HTML, content_type="text/html",
                        headers={"Cache-Control":"no-cache","Access-Control-Allow-Origin":"*"})

async def handle_props(request):
    props = [p for p in load() if p.get("active")]
    return web.json_response(props, headers={"Access-Control-Allow-Origin":"*"})

async def handle_photo(request):
    file_id = request.match_info["file_id"]
    bot: Bot = request.app["bot"]
    try:
        file = await bot.get_file(file_id)
        url  = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"
        async with ClientSession() as s:
            async with s.get(url) as r:
                data = await r.read()
                ct   = r.headers.get("Content-Type","image/jpeg")
        return web.Response(body=data, content_type=ct,
                            headers={"Access-Control-Allow-Origin":"*","Cache-Control":"public,max-age=86400"})
    except Exception as e:
        log.error(f"Photo error: {e}"); return web.Response(status=404)

async def handle_health(request):
    return web.Response(text="OK")

# ── Main ──────────────────────────────────────────────────────
async def run_web(bot_instance):
    app = web.Application()
    app["bot"] = bot_instance
    app.router.add_get("/",                    handle_root)
    app.router.add_get("/api/properties",      handle_props)
    app.router.add_get("/api/photo/{file_id}", handle_photo)
    app.router.add_get("/health",              handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info(f"🌐 Web server running on port {PORT}")
    return runner

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "":
        log.error("❌ BOT_TOKEN не задан!"); return

    bot = Bot(token=BOT_TOKEN)
    dp  = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    runner = await run_web(bot)
    log.info("🤖 Starting bot polling...")

    try:
        await dp.start_polling(bot, allowed_updates=["message","callback_query"])
    finally:
        await runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
