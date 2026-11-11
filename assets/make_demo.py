#!/usr/bin/env python3
"""Self-contained HTML-демка МЕЛЛДЖАМП — с настройками, фонами, кнопками."""
import base64, os

def b64p(p):
    return base64.b64encode(open(p, "rb").read()).decode()

A = "out/assets2"
b64 = {
    "avatar": b64p("out/img/mell_avatar.png"),
    "stars": b64p("out/ai/opt/bg_ai_city.jpg"),
    "space": b64p("out/ai/opt/bg_ai_space.jpg"),
    "sunset": b64p("out/ai/opt/bg_ai_sunset.jpg"),
    "paper": b64p("out/ai/opt/bg_ai_paper.jpg"),
    "city": b64p(f"{A}/bg_city_strip.png"),
    "btn_green": b64p("out/ai/opt/btn_ai_green.png"),
    "btn_blue": b64p("out/ai/opt/btn_ai_blue.png"),
    "btn_purple": b64p("out/ai/opt/btn_ai_purple.png"),
    "btn_orange": b64p("out/ai/opt/btn_ai_orange.png"),
    "btn_gray": b64p("out/ai/opt/btn_ai_gray.png"),
    "btn_red": b64p("out/ai/opt/btn_ai_red.png"),
    "th_paper": b64p("out/ai/opt/thumb_ai_paper.jpg"),
    "th_city": b64p("out/ai/opt/thumb_ai_city.jpg"),
    "th_space": b64p("out/ai/opt/thumb_ai_space.jpg"),
    "th_sunset": b64p("out/ai/opt/thumb_ai_sunset.jpg"),
}
for name in ("gear", "back", "touch", "tilt", "arrows", "play", "restart", "home",
             "sound_on", "sound_off", "music", "check", "plus", "minus"):
    b64["ic_" + name] = b64p(f"{A}/ic_{name}.png")

def mime_for(k):
    return "image/jpeg" if (k.startswith("th_") or k in ("stars","space","sunset","paper")) else "image/png"
data_uri = ",\n".join(f'  "{k}": "data:{mime_for(k)};base64,{v}"' for k, v in b64.items())

html = r"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no,viewport-fit=cover">
<title>МЕЛЛДЖАМП — демка</title>
<style>
  html,body{margin:0;padding:0;background:#141020;height:100%;overflow:hidden;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;
    -webkit-user-select:none;user-select:none;touch-action:none}
  #wrap{position:fixed;inset:0;display:flex;align-items:center;justify-content:center}
  canvas{display:block;max-width:100%;max-height:100%;box-shadow:0 0 60px rgba(0,0,0,.5);background:#FBF7EC}
</style>
</head>
<body>
<div id="wrap"><canvas id="cv"></canvas></div>
<script>
const IMG = {
__DATA__
};
const images = {};
for (const k in IMG) { const im = new Image(); im.src = IMG[k]; images[k] = im; }

const cv = document.getElementById('cv'), ctx = cv.getContext('2d');
const VW = 720, VH = 1280;
let kx=1, ky=1, tx=1;

const STEP=1/120, GRAVITY=2100, JUMP=-1210, SPRING=-1850, MAXFALL=1300,
      BOX=92, PLAT_H=30, CAM_LINE=VH*0.40;

const CTRL_TOUCH=0, CTRL_TILT=1, CTRL_BUTTONS=2;

let state='home', px=0,py=0,vel=0,vx=0,camY=0,height=0,score=0,best=0,
    plats=[], parts=[], animT=0, shake=0, platTop=0, hardStreak=0,
    touchX=-1, keys={}, btnDir=0, landSquashT=0, squash=0, acc=0;

// настройки
const S = {
  control: CTRL_TOUCH,
  sensitivity: 1.0,
  gameSpeed: 1.0,
  vibration: true,
  sound: true,
  bg: 0,           // 0 бумага 1 город 2 космос 3 закат
  best: 0
};
let returnFromSettings = 'home', uiBtns = [], sliderDrag = 0;
const rnd = Math.random;

function loadSettings(){
  try{
    const raw = localStorage.getItem('dj_settings');
    if(raw){ const o = JSON.parse(raw); Object.assign(S, o); }
    best = S.best || 0;
  }catch(e){}
}
function saveSettings(){
  S.best = best;
  try{ localStorage.setItem('dj_settings', JSON.stringify(S)); }catch(e){}
}

function resize(){
  const s=Math.min(innerWidth/VW, innerHeight/VH);
  cv.width=Math.floor(VW*s); cv.height=Math.floor(VH*s);
  cv.style.width=cv.width+'px'; cv.style.height=cv.height+'px';
  kx=cv.width/VW; ky=cv.height/VH; tx=Math.min(kx,ky);
  buildUi();
}
addEventListener('resize', resize);

/* ================= ФИЗИКА ================= */
function reset(){
  plats=[]; parts=[]; px=VW/2; py=VH-300; vel=0; vx=0; camY=0; height=0; score=0;
  hardStreak=0; touchX=-1; btnDir=0; landSquashT=0; squash=0; acc=0;
  const p0={x:VW/2-110, y:VH-170, w:220, type:0, vx:0, spring:false, dead:false, springT:0};
  plats.push(p0); platTop=p0.y; spawnAbove();
}
function spawnAbove(){
  const diff=Math.min(1,height/28000), base=150+62*diff;
  while(platTop > camY-320){
    const gap=base*(0.90+rnd()*0.22); platTop-=gap;
    const pl={y:platTop,w:152,type:0,vx:0,spring:false,dead:false,springT:0};
    const mc=0.10+0.28*diff, bc=0.12+0.24*diff, r=rnd();
    if(r<mc){ pl.type=1; pl.w=134; pl.vx=(rnd()<0.5?1:-1)*(80+110*diff); }
    else if(r<mc+bc){ pl.type=2; pl.w=120; }
    if(pl.type!==0){ hardStreak++; if(hardStreak>2){ pl.type=0; pl.w=152; pl.vx=0; hardStreak=0; } }
    else hardStreak=0;
    const prev = plats.length ? plats[plats.length-1].x+plats[plats.length-1].w/2 : VW/2;
    const maxdx = 240+90*(1-diff);
    let cx=prev+(rnd()*2-1)*maxdx;
    cx=Math.max(pl.w/2+10, Math.min(VW-pl.w/2-10, cx));
    pl.x=cx-pl.w/2;
    pl.spring = pl.type===0 && rnd()<0.08+0.05*diff;
    plats.push(pl);
  }
}
function startGame(){
  reset(); state='play'; uiBtns=[]; vel=JUMP; sfxFlap();
  if(S.vibration && navigator.vibrate) navigator.vibrate(20);
}
function goHome(){ reset(); state='home'; buildUi(); }
function die(){
  if(state!=='play') return;
  state='dead'; buildUi(); shake=14; sfxHit();
  if(S.vibration && navigator.vibrate) navigator.vibrate(160);
  if(score>best){ best=score; saveSettings(); }
  for(let i=0;i<26;i++){
    const a=rnd()*6.2832, s=120+rnd()*320;
    parts.push({x:px,y:py+camY,vx:Math.cos(a)*s,vy:Math.sin(a)*s,
      life:0.6+rnd()*0.5,max:1.1,size:5+rnd()*12,
      color:['#3A4A22','#4CD964','#8FD14F','#C97A3B'][i%4]});
  }
  parts.forEach(p=>p.max=p.life);
}

/* ================= ЗВУК ================= */
let ac=null, musicTimer=null, beat=0;
function actx(){ if(!ac){ try{ ac=new (AudioContext||webkitAudioContext)(); }catch(e){} } return ac; }
function tone(f,d,v,type,slide){
  if(!S.sound) return;
  const a=actx(); if(!a) return;
  const o=a.createOscillator(), g=a.createGain();
  o.type=type||'square'; o.frequency.setValueAtTime(f,a.currentTime);
  if(slide) o.frequency.exponentialRampToValueAtTime(slide,a.currentTime+d);
  g.gain.setValueAtTime(v,a.currentTime);
  g.gain.exponentialRampToValueAtTime(0.0001,a.currentTime+d);
  o.connect(g); g.connect(a.destination); o.start(); o.stop(a.currentTime+d);
}
function sfxFlap(){ tone(520,0.09,0.07,'square',1400); }
function sfxHit(){ tone(160,0.3,0.14,'sawtooth',40); }
function startMusic(){
  if(musicTimer) return;
  const bass=[110,110,131,131,98,98,110,110], mel=[440,523,659,523,440,392,440,523];
  musicTimer=setInterval(()=>{
    if(!S.sound) return;
    tone(bass[beat%8],0.2,0.03,'square');
    if(beat%2===0) tone(mel[(beat/2)%8],0.18,0.02,'sawtooth');
    beat++;
  },250);
}

/* ================= ШАГ ================= */
function step(dt){
  const spd = S.gameSpeed;
  for(const pl of plats){
    if(pl.type===1){
      pl.x+=pl.vx*dt*spd;
      if(pl.x<0){ pl.x=0; pl.vx=-pl.vx; }
      if(pl.x+pl.w>VW){ pl.x=VW-pl.w; pl.vx=-pl.vx; }
    }
    if(pl.springT>0) pl.springT=Math.max(0,pl.springT-dt*3.0);
  }
  plats = plats.filter(pl=>pl.y-camY <= VH+160);

  if(state!=='play'){
    if(state==='dead'){ vel+=GRAVITY*dt; py+=vel*dt; }
    return;
  }
  if(landSquashT>0) landSquashT=Math.max(0,landSquashT-dt*4);

  // горизонталь
  const maxSpeed = 560*S.sensitivity;
  let desired = 0;
  if(S.control===CTRL_BUTTONS){ desired = btnDir*maxSpeed; }
  else if(S.control===CTRL_TILT){
    const g = tiltVal;
    if(Math.abs(g)>0.04) desired = Math.max(-1,Math.min(1,g))*maxSpeed;
  } else {
    if(touchX>=0){
      let dx=touchX-px;
      if(dx>VW/2) dx-=VW;
      if(dx<-VW/2) dx+=VW;
      if(Math.abs(dx)>6) desired=Math.sign(dx)*maxSpeed;
    }
  }
  vx += (desired-vx)*Math.min(1,dt*20);
  if(Math.abs(vx)<2) vx=0;
  px += vx*dt;
  if(px<-BOX*0.5) px+=VW;
  if(px>VW+BOX*0.5) px-=VW;

  // вертикаль
  const prevFeet=py+camY+BOX*0.40;
  vel += GRAVITY*spd*dt;
  if(vel>MAXFALL*spd) vel=MAXFALL*spd;
  py += vel*dt;
  const feet=py+camY+BOX*0.40;

  if(vel>0){
    let hit=null, bestY=-1e9;
    for(const pl of plats){
      if(pl.dead) continue;
      if(!(feet>=pl.y && prevFeet<=pl.y+2)) continue;
      const l=px-BOX*0.30, r=px+BOX*0.30;
      const ok=(r>pl.x&&l<pl.x+pl.w)||(r>pl.x-VW&&l<pl.x+pl.w-VW)||(r>pl.x+VW&&l<pl.x+pl.w+VW);
      if(!ok) continue;
      if(pl.y>bestY){ bestY=pl.y; hit=pl; }
    }
    if(hit){
      if(hit.type===2){
        // коричневая: прыжок отталкивает и платформа сразу ломается
        py = hit.y - camY - BOX*0.40;
        vel = JUMP*(0.85+0.15*spd);
        hit.dead = true;
        hit.springT = 0;
        landSquashT = 1; squash = 0.7;
        debris(hit); sfxHit();
        if(S.vibration && navigator.vibrate) navigator.vibrate(35);
      } else {
        py = hit.y - camY - BOX*0.40;
        vel = (hit.spring?SPRING:JUMP)*(0.85+0.15*spd);
        hit.springT = hit.spring?1:0;
        landSquashT=1; squash=hit.spring?0.55:0.85;
        if(hit.spring) shake=5;
        sfxFlap();
      }
    }
  }
  if(py<CAM_LINE){ const d=CAM_LINE-py; py=CAM_LINE; camY-=d; height+=d; }
  if(platTop>camY-320) spawnAbove();
  score=Math.floor(height/30);
  if(score>best) best=score;
  if(py>VH+BOX) die();

  if(vel<0 && rnd()<0.06){
    parts.push({x:px+rnd()*24-12, y:py+BOX*0.36+camY, vx:-20-rnd()*30, vy:40+rnd()*30,
      life:0.4,max:0.4,size:3+rnd()*5,color:'rgba(51,74,34,0.33)'});
  }
}
let tiltVal = 0;
function debris(pl){
  for(let i=0;i<10;i++)
    parts.push({x:pl.x+rnd()*pl.w, y:pl.y, vx:(rnd()*2-1)*150, vy:-100-rnd()*140,
      life:0.55,max:0.55,size:4+rnd()*6,color:'#B07B4A'});
}
function updateParticles(dt){
  for(let i=parts.length-1;i>=0;i--){
    const q=parts[i]; q.life-=dt;
    if(q.life<=0){ parts.splice(i,1); continue; }
    q.vy+=900*dt; q.x+=q.vx*dt; q.y+=q.vy*dt;
  }
}

/* ================= РИСОВАНИЕ ================= */
function roundRect(x,y,w,h,r,fill,stroke,sw){
  ctx.beginPath();
  const rr=Math.min(r,w/2,h/2);
  ctx.moveTo(x+rr,y); ctx.arcTo(x+w,y,x+w,y+h,rr); ctx.arcTo(x+w,y+h,x,y+h,rr);
  ctx.arcTo(x,y+h,x,y,rr); ctx.arcTo(x,y,x+w,y,rr); ctx.closePath();
  if(fill){ ctx.fillStyle=fill; ctx.fill(); }
  if(stroke){ ctx.strokeStyle=stroke; ctx.lineWidth=sw||3*tx; ctx.stroke(); }
}
function drawImg(key, x,y,w,h, alpha){
  const im = images[key];
  if(!im || !im.complete || !im.naturalWidth) return false;
  ctx.globalAlpha = alpha===undefined?1:alpha;
  ctx.drawImage(im, x,y,w,h);
  ctx.globalAlpha = 1;
  return true;
}

function drawBackground(){
  const w=cv.width,h=cv.height;
  if(S.bg===0){
    const im=images['paper'];
    if(im && im.complete && im.naturalWidth){
      const scale=Math.max(w/im.naturalWidth, h/im.naturalHeight);
      const dw=im.naturalWidth*scale, dh=im.naturalHeight*scale;
      let scroll=((-camY)*0.55*ky)%dh; if(scroll<0) scroll+=dh;
      for(let y=scroll-dh; y<h; y+=dh) ctx.drawImage(im,(w-dw)/2,y,dw,dh+1);
      ctx.fillStyle='rgba(0,0,0,0.05)'; ctx.fillRect(0,0,w,h);
    } else { ctx.fillStyle='#FBF7EC'; ctx.fillRect(0,0,w,h); }
  } else {
    const map={1:'stars',2:'space',3:'sunset'};
    const key=map[S.bg];
    const im=images[key];
    if(im && im.complete && im.naturalWidth){
      const scale=Math.max(w/im.naturalWidth, h/im.naturalHeight);
      const dw=im.naturalWidth*scale, dh=im.naturalHeight*scale;
      let scroll=((-camY)*0.55*ky)%dh; if(scroll<0) scroll+=dh;
      for(let y=scroll-dh; y<h; y+=dh){
        ctx.drawImage(im,(w-dw)/2,y,dw,dh+1);
      }
      ctx.fillStyle='rgba(0,0,0,0.13)'; ctx.fillRect(0,0,w,h);
      if(S.bg===1 && images['city'] && images['city'].complete){
        const cityTopWorld = VH+300-620;
        const cityTopScreen = cityTopWorld-camY;
        if(cityTopScreen<VH){
          const cityH=620*ky;
          ctx.globalAlpha=0.95;
          ctx.drawImage(images['city'],0,cityTopScreen*ky,w,cityH);
          ctx.globalAlpha=1;
        }
      }
    } else { ctx.fillStyle='#150f38'; ctx.fillRect(0,0,w,h); }
  }
}

function doodles(){
  const tint = S.bg===0 ? '#C9D7E4' : 'rgba(255,255,255,0.16)';
  const k0=Math.floor((camY-VH)/420)-1, k1=Math.ceil((camY+60)/420)+1;
  ctx.strokeStyle=tint; ctx.lineWidth=2.6*kx;
  for(let k=k0;k<=k1;k++){
    const sy=k*420-camY;
    if(sy<-160||sy>VH+160) continue;
    const hash=(k*1103515245+12345)&0x7fffffff;
    const x=70+(hash%560), type=Math.floor(hash/97)%5, s=16*kx;
    ctx.beginPath();
    if(type===0){
      for(let i=0;i<5;i++){
        const a1=-Math.PI/2+i*2*Math.PI/5, a2=a1+Math.PI/5;
        const x1=x*kx+Math.cos(a1)*s, y1=sy*ky+Math.sin(a1)*s;
        const x2=x*kx+Math.cos(a2)*s*0.45, y2=sy*ky+Math.sin(a2)*s*0.45;
        if(i===0) ctx.moveTo(x1,y1); else ctx.lineTo(x1,y1);
        ctx.lineTo(x2,y2);
      }
      ctx.closePath();
    } else if(type===1){
      for(let i=0;i<26;i++){
        const a=i*0.42, rr=2+i*0.7*kx;
        const xx=x*kx+Math.cos(a)*rr, yy=sy*ky+Math.sin(a)*rr;
        if(i===0) ctx.moveTo(xx,yy); else ctx.lineTo(xx,yy);
      }
    } else if(type===2){
      ctx.moveTo(x*kx,sy*ky+s); ctx.lineTo(x*kx,sy*ky-s);
      ctx.moveTo(x*kx-s*0.55,sy*ky-s*0.35); ctx.lineTo(x*kx,sy*ky-s); ctx.lineTo(x*kx+s*0.55,sy*ky-s*0.35);
    } else if(type===3){
      ctx.arc(x*kx,sy*ky,s*0.7,0,6.2832);
      ctx.moveTo(x*kx+s*0.9+s*0.55,sy*ky+s*0.15);
      ctx.arc(x*kx+s*0.9,sy*ky+s*0.15,s*0.55,0,6.2832);
      ctx.moveTo(x*kx-s*0.9+s*0.45,sy*ky+s*0.2);
      ctx.arc(x*kx-s*0.9,sy*ky+s*0.2,s*0.45,0,6.2832);
    } else {
      ctx.moveTo(x*kx-s,sy*ky); ctx.lineTo(x*kx-s*0.4,sy*ky+s*0.6); ctx.lineTo(x*kx+s,sy*ky-s*0.8);
    }
    ctx.stroke();
  }
}

function drawPlats(){
  for(const pl of plats){
    const y=pl.y-camY;
    if(y<-90||y>VH+90) continue;
    drawOne(pl,y,0);
    if(pl.x<VW*0.35) drawOne(pl,y,VW);
    if(pl.x+pl.w>VW*0.65) drawOne(pl,y,-VW);
  }
}
function drawOne(pl,y,off){
  const x=pl.x+off, w=pl.w, th=PLAT_H;
  let body='#8FD14F', hi='#BCE983', dark='#5E9B32';
  if(pl.type===2){ body='#D08B4E'; hi='#EDB47B'; dark='#9A5A28'; }
  else if(pl.type===1){ body='#6FB6E8'; hi='#A9D7F7'; dark='#3C7FAF'; }
  ctx.globalAlpha = pl.dead?0.27:1;
  roundRect((x+3)*kx,(y+6)*ky,w*kx,th*ky,12*kx,'rgba(47,58,36,0.16)');
  roundRect(x*kx,y*ky,w*kx,th*ky,12*kx,body,'#2F3A24',3.2*kx);
  roundRect((x+5)*kx,(y+4)*ky,(w-10)*kx,th*0.45*ky,9*kx,hi);
  roundRect((x+5)*kx,(y+th*0.72)*ky,(w-10)*kx,th*0.22*ky,8*kx,dark);
  if(pl.type===2){
    ctx.strokeStyle='rgba(122,67,24,0.8)'; ctx.lineWidth=2.6*kx;
    ctx.beginPath(); ctx.moveTo((x+w*0.36)*kx,(y+2)*ky); ctx.lineTo((x+w*0.48)*kx,(y+th*0.55)*ky); ctx.lineTo((x+w*0.38)*kx,(y+th-2)*ky); ctx.stroke();
    ctx.beginPath(); ctx.moveTo((x+w*0.72)*kx,(y+2)*ky); ctx.lineTo((x+w*0.63)*kx,(y+th*0.5)*ky); ctx.stroke();
  }
  if(pl.type===1){
    ctx.strokeStyle='rgba(31,90,128,0.9)'; ctx.lineWidth=3*kx;
    const cy2=(y+th/2)*ky;
    ctx.beginPath();
    ctx.moveTo((x+w*0.30)*kx,cy2-6*ky); ctx.lineTo((x+w*0.22)*kx,cy2); ctx.lineTo((x+w*0.30)*kx,cy2+6*ky);
    ctx.moveTo((x+w*0.70)*kx,cy2-6*ky); ctx.lineTo((x+w*0.78)*kx,cy2); ctx.lineTo((x+w*0.70)*kx,cy2+6*ky);
    ctx.stroke();
  }
  if(pl.spring && !pl.dead){
    const cx=(x+w*0.5)*kx, comp=pl.springT*9*ky, baseY=(y-2)*ky+comp;
    ctx.strokeStyle='#2F3A24'; ctx.lineWidth=4.2*kx; ctx.beginPath();
    ctx.moveTo(cx-13*kx,baseY); ctx.lineTo(cx-6*kx,baseY-10*ky+comp*0.3);
    ctx.lineTo(cx+3*kx,baseY-2*ky); ctx.lineTo(cx+12*kx,baseY-12*ky+comp*0.3); ctx.stroke();
    roundRect(cx-19*kx,baseY-20*ky+comp*0.4,38*kx,8*ky,5*kx,'#E0574C','#2F3A24',2.4*kx);
  }
  ctx.globalAlpha=1;
}

function drawAvatarLocal(size){
  const r=size/2*kx;
  ctx.fillStyle='rgba(0,0,0,0.16)'; ctx.beginPath(); ctx.arc(4*kx,7*ky,r,0,6.2832); ctx.fill();
  ctx.fillStyle='#fff'; ctx.beginPath(); ctx.arc(0,0,r,0,6.2832); ctx.fill();
  if(images['avatar'].complete && images['avatar'].naturalWidth){
    ctx.save(); ctx.beginPath(); ctx.arc(0,0,r,0,6.2832); ctx.clip();
    ctx.drawImage(images['avatar'],-r,-r,r*2,r*2); ctx.restore();
  }
  ctx.strokeStyle = S.bg===0 ? '#2F3A24' : '#ffffff';
  ctx.lineWidth=4*kx;
  ctx.beginPath(); ctx.arc(0,0,r,0,6.2832); ctx.stroke();
}
function drawPlayer(){
  let rot=Math.max(-14,Math.min(16,vel/55));
  if(S.control===CTRL_TOUCH && touchX>=0) rot+=Math.max(-10,Math.min(10,(touchX-px)*0.02));
  if(S.control===CTRL_BUTTONS) rot+=btnDir*8;
  let st;
  if(vel<0) st=1+Math.min(0.22,-vel/5200);
  else st=1-Math.min(0.16,vel/6200);
  if(landSquashT>0) st=1-0.22*landSquashT*squash;
  ctx.save(); ctx.translate(px*kx,py*ky); ctx.rotate(rot*Math.PI/180);
  ctx.scale(1/Math.max(0.7,st),st); drawAvatarLocal(BOX); ctx.restore();
}

function label(s,x,y,size,color){
  ctx.font='bold '+size+'px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
  ctx.textAlign='center'; ctx.textBaseline='alphabetic';
  ctx.lineWidth=size*0.14; ctx.strokeStyle='rgba(0,0,0,0.35)'; ctx.strokeText(s,x,y);
  ctx.fillStyle=color; ctx.fillText(s,x,y);
}
function inkText(s,x,y,size,color,align){
  ctx.font='bold '+size+'px -apple-system,Segoe UI,Roboto,Arial,sans-serif';
  ctx.textAlign=align||'center'; ctx.textBaseline='alphabetic';
  ctx.fillStyle=color; ctx.fillText(s,x,y);
}
function inkColor(){ return S.bg===0 ? '#2F3A24' : '#ffffff'; }
function softColor(){ return S.bg===0 ? '#7C8A6E' : 'rgba(255,255,255,0.78)'; }

/* ---------- кнопки ---------- */
function buildUi(){
  uiBtns=[];
  const w=cv.width,h=cv.height,Sz=tx;
  const B=(x,y,bw,bh,text,icon,fill,id)=>uiBtns.push({x,y,w:bw,h:bh,text,icon,fill,id});
  if(state==='home'){
    B(w/2-210*Sz, h*0.60, 420*Sz, 116*Sz, 'ИГРАТЬ','play','btn_green',10);
    B(w/2-150*Sz, h*0.735, 300*Sz, 92*Sz, 'НАСТРОЙКИ','gear','btn_blue',12);
    B(w-86*Sz, 40*Sz, 64*Sz, 64*Sz, null, S.sound?'sound_on':'sound_off',
      S.sound?'btn_green':'btn_gray',13);
  } else if(state==='dead'){
    const cy=h*0.34;
    B(w/2-210*Sz, cy+250*Sz, 420*Sz, 96*Sz, 'ЕЩЁ РАЗ','restart','btn_green',11);
    B(w/2-150*Sz, cy+362*Sz, 300*Sz, 76*Sz, 'В МЕНЮ','home','btn_gray',15);
  } else if(state==='settings'){
    const top=h*0.155, rowH=104*Sz;
    const bw=180*Sz, bh=84*Sz, gap=12*Sz;
    const totalW=bw*3+gap*2, x0=(w-totalW)/2;
    B(x0, top, bw, bh, 'ПАЛЕЦ','touch', S.control===CTRL_TOUCH?'btn_green':'btn_gray', 20);
    B(x0+bw+gap, top, bw, bh, 'НАКЛОН','tilt', S.control===CTRL_TILT?'btn_green':'btn_gray', 21);
    B(x0+2*(bw+gap), top, bw, bh, 'КНОПКИ','arrows', S.control===CTRL_BUTTONS?'btn_green':'btn_gray', 22);
    const y1=top+rowH;
    B(x0, y1+8*Sz, 62*Sz, 62*Sz, null,'minus','btn_gray',30);
    B(x0+totalW-62*Sz, y1+8*Sz, 62*Sz, 62*Sz, null,'plus','btn_gray',31);
    const y2=y1+rowH;
    B(x0, y2+8*Sz, 62*Sz, 62*Sz, null,'minus','btn_gray',32);
    B(x0+totalW-62*Sz, y2+8*Sz, 62*Sz, 62*Sz, null,'plus','btn_gray',33);
    const y3=y2+rowH;
    B(x0, y3, bw, bh, S.vibration?'ВИБРАЦИЯ':'БЕЗ ВИБР.', null, S.vibration?'btn_green':'btn_gray',40);
    B(x0+bw+gap, y3, bw, bh, S.sound?'ЗВУК ВКЛ':'ЗВУК ВЫКЛ', S.sound?'sound_on':'sound_off', S.sound?'btn_green':'btn_gray',41);
    B(x0+2*(bw+gap), y3, bw, bh, 'СБРОС', null,'btn_red',42);
    const ty=y3+rowH+34*Sz, tw=(totalW-gap)/2, thh=118*Sz;
    B(x0, ty, tw, thh, null, 'th_paper', S.bg===0?'btn_green':'btn_gray', 50);
    B(x0+tw+gap, ty, tw, thh, null, 'th_city', S.bg===1?'btn_green':'btn_gray', 51);
    B(x0, ty+thh+gap, tw, thh, null, 'th_space', S.bg===2?'btn_green':'btn_gray', 52);
    B(x0+tw+gap, ty+thh+gap, tw, thh, null, 'th_sunset', S.bg===3?'btn_green':'btn_gray', 53);
    B(w-86*Sz, 40*Sz, 64*Sz, 64*Sz, null,'back','btn_gray',16);
  } else if(state==='play'){
    B(w-78*Sz, 44*Sz, 54*Sz, 54*Sz, null,'gear','btn_gray',12);
  }
}
function drawButton(b){
  const Sz=tx;
  roundRect(b.x+3*Sz,b.y+5*Sz,b.w,b.h,22*Sz,'rgba(0,0,0,0.25)');
  if(!drawImg(b.fill,b.x,b.y,b.w,b.h)){
    roundRect(b.x,b.y,b.w,b.h,22*Sz,'#8FD14F');
  }
  const ic = b.icon;
  if(ic){
    if(!b.text){
      const s=Math.min(b.w,b.h)*0.56;
      drawImg(ic, b.x+b.w/2-s/2, b.y+b.h/2-s/2, s, s);
    } else {
      const s=Math.min(b.h*0.52,46*Sz);
      drawImg(ic, b.x+16*Sz, b.y+b.h/2-s/2, s, s);
      const ts=b.h<80?26*Sz:42*Sz;
      label(b.text, b.x+b.w/2+s*0.35, b.y+b.h/2+ts*0.36, ts, '#fff');
    }
  } else if(b.text){
    const ts=b.h<80?24*Sz:42*Sz;
    label(b.text, b.x+b.w/2, b.y+b.h/2+ts*0.36, ts, '#fff');
  }
}
function drawSliders(){
  const w=cv.width,h=cv.height,Sz=tx;
  const top=h*0.155,rowH=104*Sz;
  const bw=180*Sz, gap=12*Sz, totalW=bw*3+gap*2, x0=(w-totalW)/2;
  const sx=x0+74*Sz, sw=totalW-148*Sz;
  drawSlider(sx, top+rowH+20*Sz, sw, 16*Sz, (S.sensitivity-0.5)/1.1);
  drawSlider(sx, top+rowH*2+20*Sz, sw, 16*Sz, (S.gameSpeed-0.5)/1.0);
}
function drawSlider(x,y,w,h,t){
  t=Math.max(0,Math.min(1,t));
  roundRect(x,y,w,h,h/2,'rgba(0,0,0,0.35)');
  roundRect(x,y,Math.max(h,w*t),h,h/2,'#8FD14F');
  ctx.fillStyle='#fff'; ctx.beginPath();
  ctx.arc(x+Math.max(h/2,w*t), y+h/2, h*1.15, 0, 6.2832); ctx.fill();
  ctx.strokeStyle='#2F3A24'; ctx.lineWidth=3*tx; ctx.stroke();
}

/* ---------- экраны ---------- */
function drawHome(){
  const w=cv.width,h=cv.height,Sz=tx,cx=w/2;
  inkText('МЕЛЛДЖАМП',cx,h*0.115,90*Sz,inkColor());
  inkText('прыгай, да?',cx,h*0.165,40*Sz,S.bg===0?'#3E7A2E':'#B6F09A');
  const size=200*Sz, top=h*0.205;
  roundRect(cx-size/2-12,top-12,size+24,size+24,16*Sz,'rgba(0,0,0,0.25)');
  roundRect(cx-size/2-12,top-12,size+24,size+24,16*Sz,'#fff');
  drawImg('avatar',cx-size/2,top,size,size);
  inkText('прыгай, да?',cx,top+size+44*Sz,30*Sz,inkColor());
  inkText('Рекорд: '+best+' м',cx,h*0.855,32*Sz,inkColor());
  inkText('Управление: '+ctrlName()+' · фон: '+bgName(),cx,h*0.895,20*Sz,softColor());
}
function ctrlName(){ return S.control===CTRL_TOUCH?'палец':S.control===CTRL_TILT?'наклон':'кнопки'; }
function bgName(){ return ['тетрадь','город','космос','закат'][S.bg]||'тетрадь'; }

function drawDead(){
  const w=cv.width,h=cv.height,Sz=tx,cx=w/2;
  ctx.fillStyle='rgba(0,0,0,0.35)'; ctx.fillRect(0,0,w,h);
  const cy=h*0.34;
  roundRect(40*Sz,cy-190*Sz,w-80*Sz,490*Sz,30*Sz,'rgba(255,253,246,0.96)','#2F3A24',3.4*Sz);
  const s=112*Sz;
  roundRect(cx-s/2-7,cy-164*Sz-7,s+14,s+14,14*Sz,'#fff');
  drawImg('avatar',cx-s/2,cy-164*Sz,s,s);
  inkText('УПАЛ, ДА?',cx,cy+26*Sz,44*Sz,'#2F3A24');
  inkText(score+' м',cx,cy+126*Sz,84*Sz,'#2F3A24');
  inkText('рекорд: '+best+' м',cx,cy+172*Sz,26*Sz,'#7C8A6E');
}

function drawSettings(){
  const w=cv.width,h=cv.height,Sz=tx;
  ctx.fillStyle='rgba(0,0,0,0.45)'; ctx.fillRect(0,0,w,h);
  const top=h*0.155,rowH=104*Sz;
  const bw=180*Sz,gap=12*Sz,totalW=bw*3+gap*2,x0=(w-totalW)/2;
  inkText('НАСТРОЙКИ',w/2,h*0.095,58*Sz,'#fff');
  inkText('УПРАВЛЕНИЕ',x0,top-14*Sz,22*Sz,'rgba(255,255,255,0.82)','left');
  inkText('ЧУВСТВИТЕЛЬНОСТЬ  '+Math.round(S.sensitivity*100)+'%',x0,top+rowH-18*Sz,22*Sz,'rgba(255,255,255,0.82)','left');
  inkText('СКОРОСТЬ  '+Math.round(S.gameSpeed*100)+'%',x0,top+rowH*2-18*Sz,22*Sz,'rgba(255,255,255,0.82)','left');
  inkText('ЗВУК И ПРОЧЕЕ',x0,top+rowH*3-14*Sz,22*Sz,'rgba(255,255,255,0.82)','left');
  drawSliders();
  const ty=top+rowH*3+rowH+34*Sz;
  inkText('ФОН ИГРЫ',x0,ty-18*Sz,22*Sz,'rgba(255,255,255,0.82)','left');
  inkText('Doodle Jump: Mellstroy · open source',x0,h-28*Sz,18*Sz,'rgba(255,255,255,0.55)','left');
}

function drawControlButtons(){
  if(S.control!==CTRL_BUTTONS || state!=='play') return;
  const Sz=tx, size=108*Sz, y=cv.height-size-40*Sz;
  const left={x:30*Sz,y,w:size,h:size,icon:null,fill:'btn_gray',text:null};
  const right={x:cv.width-30*Sz-size,y,w:size,h:size,icon:null,fill:'btn_gray',text:null};
  drawButton(left); drawButton(right);
  function tri(cx,cy,d){
    ctx.beginPath();
    ctx.moveTo(cx+d*26*Sz,cy); ctx.lineTo(cx-d*16*Sz,cy-21*Sz); ctx.lineTo(cx-d*16*Sz,cy+21*Sz);
    ctx.closePath(); ctx.fillStyle='rgba(0,0,0,0.65)'; ctx.fill();
  }
  tri(left.x+size/2, y+size/2, -1);
  tri(right.x+size/2, y+size/2, 1);
}

function draw(){
  ctx.setTransform(1,0,0,1,0,0);
  ctx.fillStyle='#FBF7EC'; ctx.fillRect(0,0,cv.width,cv.height);
  ctx.save();
  if(shake>0) ctx.translate((rnd()*2-1)*shake*kx,(rnd()*2-1)*shake*ky);
  drawBackground(); if(S.bg!==0) doodles(); drawPlats();
  for(const q of parts){
    ctx.globalAlpha=Math.max(0,q.life/q.max); ctx.fillStyle=q.color;
    ctx.beginPath(); ctx.arc(q.x*kx,(q.y-camY)*ky,q.size*kx*(0.4+0.6*q.life/q.max),0,6.2832); ctx.fill();
  }
  ctx.globalAlpha=1;
  if(state==='home'){
    const y=VH*0.42+Math.sin(animT*2.4)*16;
    ctx.save(); ctx.translate(VW*0.5*kx,y*ky); ctx.rotate(Math.sin(animT*2.4)*6*Math.PI/180);
    drawAvatarLocal(BOX*1.45); ctx.restore();
  } else if(state==='play'||state==='dead'){ drawPlayer(); }
  ctx.restore();

  const w=cv.width;
  if(state==='play'){
    label(''+score,w/2,150*ky,96*tx,inkColor());
    inkText('м',w/2+58*tx,150*ky,32*tx,softColor(),'left');
    inkText('РЕКОРД '+best,w/2,200*ky,28*tx,softColor());
  }
  if(state==='home') drawHome();
  if(state==='dead') drawDead();
  if(state==='settings') drawSettings();

  for(const b of uiBtns) drawButton(b);
  drawControlButtons();
}

/* ================= ЦИКЛ ================= */
let lastT=performance.now();
function loop(t){
  let dt=(t-lastT)/1000; lastT=t;
  if(dt>0.10) dt=0.10;
  animT+=dt;
  if(shake>0) shake=Math.max(0,shake-dt*55);
  acc+=dt;
  let guard=0;
  while(acc>=STEP && guard<12){ step(STEP); acc-=STEP; guard++; }
  if(guard>=12) acc=0;
  updateParticles(dt);
  draw();
  requestAnimationFrame(loop);
}

/* ================= ВВОД ================= */
function hit(b,x,y){ return x>=b.x&&x<=b.x+b.w&&y>=b.y&&y<=b.y+b.h; }
function onButton(id,x,y){
  switch(id){
    case 10: case 11: startGame(); startMusic(); break;
    case 12: returnFromSettings = (state==='play')?'play':'home'; state='settings'; buildUi(); break;
    case 13: S.sound=!S.sound; saveSettings(); buildUi(); break;
    case 15: goHome(); break;
    case 16:
      state = returnFromSettings==='play' ? 'play' : 'home';
      saveSettings(); buildUi(); break;
    case 20: S.control=CTRL_TOUCH; saveSettings(); buildUi(); break;
    case 21: S.control=CTRL_TILT; saveSettings(); buildUi(); break;
    case 22: S.control=CTRL_BUTTONS; saveSettings(); buildUi(); break;
    case 30: S.sensitivity=Math.max(0.5,Math.round((S.sensitivity-0.1)*20)/20); saveSettings(); buildUi(); break;
    case 31: S.sensitivity=Math.min(1.6,Math.round((S.sensitivity+0.1)*20)/20); saveSettings(); buildUi(); break;
    case 32: S.gameSpeed=Math.max(0.5,Math.round((S.gameSpeed-0.1)*20)/20); saveSettings(); buildUi(); break;
    case 33: S.gameSpeed=Math.min(1.5,Math.round((S.gameSpeed+0.1)*20)/20); saveSettings(); buildUi(); break;
    case 40: S.vibration=!S.vibration; saveSettings(); buildUi(); break;
    case 41: S.sound=!S.sound; saveSettings(); buildUi(); break;
    case 42: best=0; saveSettings(); buildUi(); break;
    case 50: S.bg=0; saveSettings(); buildUi(); break;
    case 51: S.bg=1; saveSettings(); buildUi(); break;
    case 52: S.bg=2; saveSettings(); buildUi(); break;
    case 53: S.bg=3; saveSettings(); buildUi(); break;
  }
}
function sliderHit(x,y){
  if(state!=='settings') return 0;
  const w=cv.width,h=cv.height,Sz=tx;
  const top=h*0.155,rowH=104*Sz;
  const bw=180*Sz,gap=12*Sz,totalW=bw*3+gap*2,x0=(w-totalW)/2;
  const sx=x0+74*Sz, sw=totalW-148*Sz;
  const y1=top+rowH+20*Sz, y2=top+rowH*2+20*Sz;
  if(y>y1-26*Sz && y<y1+34*Sz && x>sx-24 && x<sx+sw+24){
    applySlider(1,x,sx,sw); return 1;
  }
  if(y>y2-26*Sz && y<y2+34*Sz && x>sx-24 && x<sx+sw+24){
    applySlider(2,x,sx,sw); return 2;
  }
  return 0;
}
function applySlider(id,x,sx,sw){
  const t=Math.max(0,Math.min(1,(x-sx)/sw));
  if(id===1) S.sensitivity=Math.round((0.5+t*1.1)*20)/20;
  else S.gameSpeed=Math.round((0.5+t*1.0)*20)/20;
  saveSettings(); buildUi();
}

cv.addEventListener('pointerdown', e=>{
  const r=cv.getBoundingClientRect(); e.preventDefault();
  const x=e.clientX-r.left, y=e.clientY-r.top;
  cv.setPointerCapture && cv.setPointerCapture(e.pointerId);

  for(const b of uiBtns){ if(hit(b,x,y)){ onButton(b.id,x,y); return; } }
  const sl=sliderHit(x,y); if(sl){ sliderDrag=sl; return; }

  if(state==='play'){
    if(S.control===CTRL_BUTTONS){
      const Sz=tx,size=108*Sz,by=cv.height-size-40*Sz;
      if(x>30*Sz&&x<30*Sz+size&&y>by&&y<by+size){ btnDir=-1; return; }
      if(x>cv.width-30*Sz-size&&x<cv.width-30*Sz&&y>by&&y<by+size){ btnDir=1; return; }
    }
    if(S.control===CTRL_TOUCH) touchX=x/kx;
  }
});
cv.addEventListener('pointermove', e=>{
  const r=cv.getBoundingClientRect();
  const x=e.clientX-r.left, y=e.clientY-r.top;
  if(sliderDrag){ 
    const w=cv.width,Sz=tx;
    const top=cv.height*0.155,rowH=104*Sz;
    const bw=180*Sz,gap=12*Sz,totalW=bw*3+gap*2,x0=(w-totalW)/2;
    const sx=x0+74*Sz, sw=totalW-148*Sz;
    applySlider(sliderDrag,x,sx,sw); return;
  }
  if(state==='play'){
    if(S.control===CTRL_TOUCH) touchX=x/kx;
    else if(S.control===CTRL_BUTTONS){
      const Sz=tx,size=108*Sz,by=cv.height-size-40*Sz;
      if(x>30*Sz&&x<30*Sz+size&&y>by&&y<by+size) btnDir=-1;
      else if(x>cv.width-30*Sz-size&&x<cv.width-30*Sz&&y>by&&y<by+size) btnDir=1;
    }
  }
});
cv.addEventListener('pointerup', ()=>{ sliderDrag=0; touchX=-1; btnDir=0; });
cv.addEventListener('pointercancel', ()=>{ sliderDrag=0; touchX=-1; btnDir=0; });
addEventListener('keydown',e=>{
  keys[e.key]=true;
  if(e.key===' '||e.key==='Enter'){
    e.preventDefault();
    if(state==='home'){ startGame(); startMusic(); }
    else if(state==='dead') startGame();
  }
  if(e.key==='Escape' && state==='settings'){ onButton(16); }
});
addEventListener('keyup',e=>{ keys[e.key]=false; });
addEventListener('deviceorientation',ev=>{
  const g=ev.gamma||0;
  if(Math.abs(g)>2) tiltVal=Math.max(-1,Math.min(1,g/25));
});

loadSettings(); resize(); reset(); buildUi(); requestAnimationFrame(loop);
</script>
</body>
</html>
"""
html = html.replace("__DATA__", data_uri)
open("out/dudle_jump_demo.html", "w").write(html)
print("written", len(html), "bytes;", len(b64), "images")
