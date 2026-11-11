package com.arena.dudlejump;

import android.app.Activity;
import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Canvas;
import android.graphics.Color;
import android.graphics.LinearGradient;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.Rect;
import android.graphics.RectF;
import android.graphics.Shader;
import android.graphics.Typeface;
import android.hardware.Sensor;
import android.hardware.SensorEvent;
import android.hardware.SensorEventListener;
import android.hardware.SensorManager;
import android.media.AudioAttributes;
import android.media.AudioManager;
import android.media.MediaPlayer;
import android.media.SoundPool;
import android.os.Bundle;
import android.os.Vibrator;
import android.view.MotionEvent;
import android.view.View;
import android.view.Window;
import android.view.WindowManager;

import java.util.ArrayList;
import java.util.Random;

public class GameActivity extends Activity {

    GameView game;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        requestWindowFeature(Window.FEATURE_NO_TITLE);
        getWindow().setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN,
                WindowManager.LayoutParams.FLAG_FULLSCREEN);
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        game = new GameView(this);
        setContentView(game);
        hideSystemUi();
    }

    private void hideSystemUi() {
        try {
            View d = getWindow().getDecorView();
            d.setSystemUiVisibility(View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN);
        } catch (Throwable ignored) {}
    }

    @Override public void onWindowFocusChanged(boolean has) {
        super.onWindowFocusChanged(has);
        if (has) hideSystemUi();
    }

    @Override protected void onResume() { super.onResume(); hideSystemUi(); game.resume(); }
    @Override protected void onPause() { game.pause(); super.onPause(); }
    @Override public void onBackPressed() {
        if (game.state == game.STATE_SETTINGS) game.closeSettings();
        else if (game.state == game.STATE_HOME) super.onBackPressed();
        else game.goHome();
    }

    // =====================================================================
    //  МЕЛЛДЖАМП (Doodle Jump x Mellstroy)
    //  Настройки: управление (палец/наклон/кнопки), чувствительность,
    //  скорость, вибрация, звук, 4 фона. Рендер через View (без мерцания).
    // =====================================================================
    static class GameView extends View implements SensorEventListener {

        static final int STATE_HOME = 0, STATE_PLAY = 1, STATE_DEAD = 2, STATE_SETTINGS = 3;
        int state = STATE_HOME;
        int returnFromSettings = STATE_HOME;
        boolean running = false;

        static final float VW = 720f, VH = 1280f;
        float kx = 1f, ky = 1f, tx = 1f;

        // физика
        static final float STEP = 1f / 120f;
        static final float GRAVITY = 2100f;
        static final float JUMP = -1210f;
        static final float SPRING_JUMP = -1850f;
        static final float MAX_FALL = 1300f;
        static final float BOX = 92f;
        static final float PLAT_H = 30f;
        static final float CAM_LINE = VH * 0.40f;

        // настройки
        static final int CTRL_TOUCH = 0, CTRL_TILT = 1, CTRL_BUTTONS = 2;
        int controlMode = CTRL_TOUCH;
        float sensitivity = 1.0f;      // 0.5 .. 1.6
        float gameSpeed = 1.0f;        // 0.5 .. 1.5 (множитель гравитации)
        boolean vibration = true;
        boolean soundOn = true;
        int bgIndex = 0;               // 0 бумага, 1 город, 2 космос, 3 закат

        float px, py, vel, vx;
        float camY, height, platTop;
        int score, best, hardStreak;
        float landSquashT, squash;
        float tilt;
        boolean hasAccel;
        float touchX = -1;
        int btnDir = 0;                 // -1/0/+1 от кнопок

        final ArrayList<Plat> plats = new ArrayList<>();
        final ArrayList<Particle> parts = new ArrayList<>();
        final Random rnd = new Random();

        static class Plat {
            float x, y, w, vx;
            int type;
            boolean dead, spring;
            float springT;
        }
        static class Particle {
            float x, y, vx, vy, life, max, size;
            int color;
        }
        static class Btn {
            RectF r;
            String text;
            Bitmap icon;
            Bitmap fill;
            int id;
            boolean small;
            Btn copy() { Btn b = new Btn(); b.r = new RectF(r); b.text = text; b.icon = icon; b.fill = fill; b.id = id; b.small = small; return b; }
        }

        // рендер
        Paint p = new Paint(Paint.ANTI_ALIAS_FLAG);
        Paint ink = new Paint(Paint.ANTI_ALIAS_FLAG);
        Paint textPaint = new Paint(Paint.ANTI_ALIAS_FLAG);
        Bitmap avatar;
        Bitmap icGear, icBack, icTouch, icTilt, icArrows, icPlay, icRestart, icHome,
                icSoundOn, icSoundOff, icMusic, icCheck, icPlus, icMinus;
        Bitmap bgAiPaper, bgAiCity, bgAiSpace, bgAiSunset;
        Bitmap[] btnAi = new Bitmap[6];
        Bitmap thAiPaper, thAiCity, thAiSpace, thAiSunset;
        Path clipPath = new Path();
        Rect srcRect = new Rect();

        // кнопки (пересобираются в layoutUi)
        final ArrayList<Btn> btns = new ArrayList<>();
        boolean uiReady = false;
        float sliderDragX = -1;
        int sliderDragId = -1;

        // звук
        SoundPool sp;
        int sFlap = -1, sPoint = -1, sHit = -1;
        MediaPlayer music;
        Vibrator vib;
        SensorManager sm;
        Sensor accelSensor;

        long lastNano;
        float animT, shake, physicsAcc;

        // ------------------------------------------------------------------
        public GameView(Context c) {
            super(c);
            setFocusable(true);
            setKeepScreenOn(true);

            avatar = dec(R.drawable.mell_avatar);


            icGear = dec(R.drawable.ic_gear);
            icBack = dec(R.drawable.ic_back);
            icTouch = dec(R.drawable.ic_touch);
            icTilt = dec(R.drawable.ic_tilt);
            icArrows = dec(R.drawable.ic_arrows);
            icPlay = dec(R.drawable.ic_play);
            icRestart = dec(R.drawable.ic_restart);
            icHome = dec(R.drawable.ic_home);
            icSoundOn = dec(R.drawable.ic_sound_on);
            icSoundOff = dec(R.drawable.ic_sound_off);
            icMusic = dec(R.drawable.ic_music);
            icCheck = dec(R.drawable.ic_check);
            icPlus = dec(R.drawable.ic_plus);
            icMinus = dec(R.drawable.ic_minus);

            // AI-сгенерированные фоны и кнопки
            bgAiPaper = dec(R.drawable.bg_ai_paper);
            bgAiCity = dec(R.drawable.bg_ai_city);
            bgAiSpace = dec(R.drawable.bg_ai_space);
            bgAiSunset = dec(R.drawable.bg_ai_sunset);
            btnAi[0] = dec(R.drawable.btn_ai_green);
            btnAi[1] = dec(R.drawable.btn_ai_blue);
            btnAi[2] = dec(R.drawable.btn_ai_purple);
            btnAi[3] = dec(R.drawable.btn_ai_orange);
            btnAi[4] = dec(R.drawable.btn_ai_gray);
            btnAi[5] = dec(R.drawable.btn_ai_red);
            thAiPaper = dec(R.drawable.thumb_ai_paper);
            thAiCity = dec(R.drawable.thumb_ai_city);
            thAiSpace = dec(R.drawable.thumb_ai_space);
            thAiSunset = dec(R.drawable.thumb_ai_sunset);


            textPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            ink.setStyle(Paint.Style.STROKE);
            ink.setStrokeCap(Paint.Cap.ROUND);
            ink.setStrokeJoin(Paint.Join.ROUND);

            vib = (Vibrator) c.getSystemService(Context.VIBRATOR_SERVICE);

            AudioAttributes attrs = new AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_GAME)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build();
            sp = new SoundPool.Builder().setMaxStreams(8).setAudioAttributes(attrs).build();
            sFlap = sp.load(c, R.raw.sfx_flap, 1);
            sPoint = sp.load(c, R.raw.sfx_point, 1);
            sHit = sp.load(c, R.raw.sfx_hit, 1);

            sm = (SensorManager) c.getSystemService(Context.SENSOR_SERVICE);
            if (sm != null) accelSensor = sm.getDefaultSensor(Sensor.TYPE_ACCELEROMETER);
            hasAccel = accelSensor != null;

            loadSettings();
            resetGame();
        }

        Bitmap dec(int id) {
            try { return BitmapFactory.decodeResource(getResources(), id); }
            catch (Throwable t) { return null; }
        }

        boolean isHome() { return state == STATE_HOME; }

        // ------------------------------------------------------------------
        // настройки
        void loadSettings() {
            best = getContext().getSharedPreferences("dj", 0).getInt("best", 0);
            controlMode = getContext().getSharedPreferences("dj", 0).getInt("ctrl", CTRL_TOUCH);
            sensitivity = getContext().getSharedPreferences("dj", 0).getFloat("sens", 1f);
            gameSpeed = getContext().getSharedPreferences("dj", 0).getFloat("speed", 1f);
            vibration = getContext().getSharedPreferences("dj", 0).getBoolean("vib", true);
            soundOn = getContext().getSharedPreferences("dj", 0).getBoolean("snd", true);
            bgIndex = getContext().getSharedPreferences("dj", 0).getInt("bg", 0);
        }

        void saveSettings() {
            getContext().getSharedPreferences("dj", 0).edit()
                    .putInt("ctrl", controlMode)
                    .putFloat("sens", sensitivity)
                    .putFloat("speed", gameSpeed)
                    .putBoolean("vib", vibration)
                    .putBoolean("snd", soundOn)
                    .putInt("bg", bgIndex)
                    .apply();
        }

        void openSettings() {
            returnFromSettings = (state == STATE_PLAY) ? STATE_PLAY
                    : (state == STATE_DEAD) ? STATE_HOME : state;
            state = STATE_SETTINGS;
            uiReady = false;
        }

        void closeSettings() {
            saveSettings();
            state = returnFromSettings;
            uiReady = false;
            lastNano = 0;
            physicsAcc = 0;
            touchX = -1;
            btnDir = 0;
        }

        // ------------------------------------------------------------------
        void resetGame() {
            plats.clear();
            parts.clear();
            px = VW / 2f;
            py = VH - 300f;
            vel = 0;
            vx = 0;
            camY = 0;
            height = 0;
            score = 0;
            hardStreak = 0;
            touchX = -1;
            btnDir = 0;
            squash = 0;
            landSquashT = 0;

            Plat p0 = new Plat();
            p0.x = VW / 2f - 110f;
            p0.y = VH - 170f;
            p0.w = 220f;
            p0.type = 0;
            plats.add(p0);
            platTop = p0.y;
            spawnAbove();
        }

        void goHome() { state = STATE_HOME; uiReady = false; resetGame(); }

        void start() {
            resetGame();
            state = STATE_PLAY;
            uiReady = false;
            vel = JUMP;
            playSfx(0);
            postInvalidateOnAnimation();
        }

        void die() {
            if (state != STATE_PLAY) return;
            state = STATE_DEAD;
            uiReady = false;
            shake = 14f;
            playSfx(2);
            if (vibration && vib != null && vib.hasVibrator()) {
                try { vib.vibrate(160); } catch (Exception ignored) {}
            }
            score = (int) (height / 30f);
            if (score > best) {
                best = score;
                getContext().getSharedPreferences("dj", 0).edit().putInt("best", best).apply();
            }
            for (int i = 0; i < 26; i++) {
                Particle q = new Particle();
                q.x = px;
                q.y = py + camY;
                float a = rnd.nextFloat() * 6.2832f, spd = 120 + rnd.nextFloat() * 320;
                q.vx = (float) Math.cos(a) * spd;
                q.vy = (float) Math.sin(a) * spd;
                q.max = q.life = 0.6f + rnd.nextFloat() * 0.5f;
                q.size = 5 + rnd.nextFloat() * 12;
                q.color = new int[]{0xFF3A4A22, 0xFF4CD964, 0xFF8FD14F, 0xFFC97A3B}[i % 4];
                parts.add(q);
            }
        }

        void playSfx(int which) {
            if (!soundOn || sp == null) return;
            int id = which == 0 ? sFlap : which == 1 ? sPoint : sHit;
            if (id > 0) sp.play(id, 0.85f, 0.85f, 1, 0, 1f);
        }

        // ------------------------------------------------------------------
        void spawnAbove() {
            float diff = Math.min(1f, height / 28000f);
            float gapBase = 150f + 62f * diff;
            while (platTop > camY - 320f) {
                float gap = gapBase * (0.90f + rnd.nextFloat() * 0.22f);
                platTop -= gap;
                Plat pl = new Plat();
                pl.y = platTop;
                pl.w = 152f;
                float moveCh = 0.10f + 0.28f * diff;
                float breakCh = 0.12f + 0.24f * diff;
                float r = rnd.nextFloat();
                if (r < moveCh) {
                    pl.type = 1;
                    pl.w = 134f;
                    pl.vx = (rnd.nextBoolean() ? 1 : -1) * (80f + 110f * diff);
                } else if (r < moveCh + breakCh) {
                    pl.type = 2;
                    pl.w = 120f;
                } else pl.type = 0;
                if (pl.type != 0) {
                    hardStreak++;
                    if (hardStreak > 2) { pl.type = 0; pl.w = 152f; pl.vx = 0; hardStreak = 0; }
                } else hardStreak = 0;

                float prevCx = plats.isEmpty() ? VW / 2f
                        : plats.get(plats.size() - 1).x + plats.get(plats.size() - 1).w / 2f;
                float maxDx = 240f + 90f * (1f - diff);
                float cxT = clamp(prevCx + (rnd.nextFloat() * 2f - 1f) * maxDx,
                        pl.w / 2f + 10f, VW - pl.w / 2f - 10f);
                pl.x = cxT - pl.w / 2f;
                pl.spring = pl.type == 0 && rnd.nextFloat() < 0.08f + 0.05f * diff;
                plats.add(pl);
            }
        }

        // ==================================================================
        // ЦИКЛ
        // ==================================================================
        @Override protected void onDraw(Canvas c) {
            super.onDraw(c);
            long now = System.nanoTime();
            if (lastNano == 0) lastNano = now;
            float dt = (now - lastNano) / 1e9f;
            lastNano = now;
            if (dt > 0.10f) dt = 0.10f;

            if (running) {
                physicsAcc += dt;
                int guard = 0;
                while (physicsAcc >= STEP && guard < 12) {
                    step(STEP);
                    physicsAcc -= STEP;
                    guard++;
                    if (!running) break;
                }
                if (guard >= 12) physicsAcc = 0;
                animT += dt;
                if (shake > 0) shake = Math.max(0, shake - dt * 55f);
                updateParticles(dt);
            }
            renderAll(c);
            if (running) postInvalidateOnAnimation();
        }

        void updateParticles(float dt) {
            for (int i = parts.size() - 1; i >= 0; i--) {
                Particle q = parts.get(i);
                q.life -= dt;
                if (q.life <= 0) { parts.remove(i); continue; }
                q.vy += 900 * dt;
                q.x += q.vx * dt;
                q.y += q.vy * dt;
            }
        }

        void step(float dt) {
            float spd = gameSpeed;
            for (Plat pl : plats) {
                if (pl.type == 1) {
                    pl.x += pl.vx * dt * spd;
                    if (pl.x < 0) { pl.x = 0; pl.vx = -pl.vx; }
                    if (pl.x + pl.w > VW) { pl.x = VW - pl.w; pl.vx = -pl.vx; }
                }
                if (pl.springT > 0) pl.springT = Math.max(0, pl.springT - dt * 3.0f);
            }
            for (int i = plats.size() - 1; i >= 0; i--)
                if (plats.get(i).y - camY > VH + 160f) plats.remove(i);

            if (state != STATE_PLAY) {
                if (state == STATE_DEAD) { vel += GRAVITY * dt; py += vel * dt; }
                return;
            }
            if (landSquashT > 0) landSquashT = Math.max(0, landSquashT - dt * 4f);

            // --- горизонталь: единая, аккуратная модель для всех режимов ---
            float maxSpeed = 560f * sensitivity;
            float desired = 0f;
            switch (controlMode) {
                case CTRL_BUTTONS:
                    desired = btnDir * maxSpeed;
                    break;
                case CTRL_TILT:
                    if (hasAccel) desired = clamp(tilt, -1f, 1f) * maxSpeed;
                    break;
                default: { // CTRL_TOUCH
                    if (touchX >= 0) {
                        float dx = touchX - px;
                        if (dx > VW / 2f) dx -= VW;
                        if (dx < -VW / 2f) dx += VW;
                        if (Math.abs(dx) > 6f) desired = Math.signum(dx) * maxSpeed;
                    }
                }
            }
            vx += (desired - vx) * Math.min(1f, dt * 20f);
            if (Math.abs(vx) < 2f) vx = 0;
            px += vx * dt;
            if (px < -BOX * 0.5f) px += VW;
            if (px > VW + BOX * 0.5f) px -= VW;

            // --- вертикаль ---
            float prevFeetWorld = py + camY + BOX * 0.40f;
            vel += GRAVITY * spd * dt;
            if (vel > MAX_FALL * spd) vel = MAX_FALL * spd;
            py += vel * dt;
            float feetWorld = py + camY + BOX * 0.40f;

            if (vel > 0) {
                Plat hit = null;
                float bestY = -1e9f;
                for (int i = 0; i < plats.size(); i++) {
                    Plat pl = plats.get(i);
                    if (pl.dead) continue;
                    if (!(feetWorld >= pl.y && prevFeetWorld <= pl.y + 2f)) continue;
                    if (!overlapX(px, pl)) continue;
                    if (pl.y > bestY) { bestY = pl.y; hit = pl; }
                }
                if (hit != null) {
                    if (hit.type == 2) {
                        // коричневая: прыжок отталкивает и платформа сразу ломается
                        py = hit.y - camY - BOX * 0.40f;
                        vel = JUMP * (0.85f + 0.15f * spd);
                        hit.dead = true;
                        hit.springT = 0;
                        landSquashT = 1f;
                        squash = 0.7f;
                        debris(hit);
                        playSfx(2);
                        if (vibration && vib != null && vib.hasVibrator()) {
                            try { vib.vibrate(35); } catch (Exception ignored) {}
                        }
                    } else {
                        py = hit.y - camY - BOX * 0.40f;
                        vel = (hit.spring ? SPRING_JUMP : JUMP) * (0.85f + 0.15f * spd);
                        hit.springT = hit.spring ? 1f : 0f;
                        landSquashT = 1f;
                        squash = hit.spring ? 0.55f : 0.85f;
                        if (hit.spring) shake = 5f;
                        playSfx(hit.spring ? 1 : 0);
                    }
                }
            }

            if (py < CAM_LINE) {
                float d = CAM_LINE - py;
                py = CAM_LINE;
                camY -= d;
                height += d;
            }

            if (platTop > camY - 320f) spawnAbove();
            int sc = (int) (height / 30f);
            if (sc != score) score = sc;
            if (score > best) {
                best = score;
                getContext().getSharedPreferences("dj", 0).edit().putInt("best", best).apply();
            }

            if (py > VH + BOX) die();

            if (vel < 0 && rnd.nextFloat() < 0.06f) {
                Particle q = new Particle();
                q.x = px + rnd.nextFloat() * 24 - 12;
                q.y = py + BOX * 0.36f + camY;
                q.vx = -20 - rnd.nextFloat() * 30;
                q.vy = 40 + rnd.nextFloat() * 30;
                q.max = q.life = 0.4f;
                q.size = 3 + rnd.nextFloat() * 5;
                q.color = 0x55334A22;
                parts.add(q);
            }
        }

        boolean overlapX(float cx, Plat pl) {
            float l = cx - BOX * 0.30f, r = cx + BOX * 0.30f;
            if (r > pl.x && l < pl.x + pl.w) return true;
            if (r > pl.x - VW && l < pl.x + pl.w - VW) return true;
            if (r > pl.x + VW && l < pl.x + pl.w + VW) return true;
            return false;
        }

        void debris(Plat pl) {
            for (int i = 0; i < 10; i++) {
                Particle q = new Particle();
                q.x = pl.x + rnd.nextFloat() * pl.w;
                q.y = pl.y;
                q.vx = (rnd.nextFloat() * 2 - 1) * 150;
                q.vy = -100 - rnd.nextFloat() * 140;
                q.max = q.life = 0.55f;
                q.size = 4 + rnd.nextFloat() * 6;
                q.color = 0xFFB07B4A;
                parts.add(q);
            }
        }

        float clamp(float v, float a, float b) { return v < a ? a : (v > b ? b : v); }

        // ==================================================================
        // РЕНДЕР
        // ==================================================================
        void renderAll(Canvas c) {
            kx = getWidth() / VW;
            ky = getHeight() / VH;
            tx = Math.min(kx, ky);

            int paperColor = 0xFFFBF7EC;
            c.drawColor(paperColor);

            float sx = 0, sy = 0;
            if (shake > 0) {
                sx = (rnd.nextFloat() * 2 - 1) * shake * kx;
                sy = (rnd.nextFloat() * 2 - 1) * shake * ky;
            }
            c.save();
            c.translate(sx, sy);

            drawBackground(c);
            drawPaperOverlayIfNeeded(c);
            drawDoodles(c);
            drawPlats(c);
            drawParts(c);
            if (state == STATE_HOME) drawPlayerHome(c);
            else if (state == STATE_PLAY || state == STATE_DEAD) drawPlayer(c);

            c.restore();

            if (!uiReady) layoutUi();
            drawUi(c);
        }

        // ---------- фоны ----------
        void drawBackground(Canvas c) {
            int w = getWidth(), h = getHeight();
            Bitmap bg = null;
            switch (bgIndex) {
                case 1: bg = bgAiCity; break;
                case 2: bg = bgAiSpace; break;
                case 3: bg = bgAiSunset; break;
                default: bg = bgAiPaper; break;
            }
            if (bg == null || bgIndex == 0) {
                if (bg != null) {
                    // AI-фон тетрадного листа: прокрутка как у остальных
                    drawScrollingBg(c, bg);
                    p.setColor(0x0D000000);
                    c.drawRect(0, 0, w, h, p);
                    return;
                }
                // бумага + сетка
                p.setStyle(Paint.Style.STROKE);
                p.setStrokeWidth(Math.max(1f, 1.6f * kx));
                p.setColor(0xFFD5E2EE);
                float gx = 60f * kx, gy = 60f * ky;
                for (float x = 0; x <= w + 1; x += gx) c.drawLine(x, 0, x, h, p);
                float off = ((-camY) * ky) % gy;
                if (off < 0) off += gy;
                for (float y = off - gy; y <= h + gy; y += gy) c.drawLine(0, y, w, y, p);
                p.setStyle(Paint.Style.FILL);
                p.setColor(0x33E08B7A);
                c.drawRect(42f * kx, 0, 46f * kx, h, p);
                p.setShader(new LinearGradient(0, 0, 90f * kx, 0, 0x14000000, 0x00000000, Shader.TileMode.CLAMP));
                c.drawRect(0, 0, 90f * kx, h, p);
                p.setShader(null);
            } else {
                drawScrollingBg(c, bg);
                p.setColor(0x22000000);
                c.drawRect(0, 0, w, h, p);
            }
        }

        void drawScrollingBg(Canvas c, Bitmap bg) {
            int w = getWidth(), h = getHeight();
            float scale = Math.max(w / (float) bg.getWidth(), h / (float) bg.getHeight());
            float dw = bg.getWidth() * scale;
            float dh = bg.getHeight() * scale;
            float scroll = ((-camY) * 0.55f * ky) % dh;
            if (scroll < 0) scroll += dh;
            float startY = scroll - dh;
            int guard = 0;
            srcRect.set(0, 0, bg.getWidth(), bg.getHeight());
            for (float y = startY; y < h && guard < 4; y += dh, guard++) {
                Rect dst = new Rect((int) ((w - dw) / 2f), (int) y, (int) ((w + dw) / 2f), (int) (y + dh + 1));
                c.drawBitmap(bg, srcRect, dst, p);
            }
        }

        void drawPaperOverlayIfNeeded(Canvas c) {
            // на цветных фонах поля и клетку не рисуем — только дудлы
        }

        int colorForBg() {
            return bgIndex == 0 ? 0xFF2F3A24 : 0xFFFFFFFF;
        }

        void drawDoodles(Canvas c) {
            int tint = bgIndex == 0 ? 0xFFC9D7E4 : 0x33FFFFFF;
            int k0 = (int) Math.floor((camY - VH) / 420f) - 1;
            int k1 = (int) Math.ceil((camY + 60f) / 420f) + 1;
            p.setStyle(Paint.Style.STROKE);
            p.setStrokeWidth(2.6f * kx);
            p.setColor(tint);
            for (int k = k0; k <= k1; k++) {
                float wy = k * 420f;
                float sy = wy - camY;
                if (sy < -160 || sy > VH + 160) continue;
                int hash = (k * 1103515245 + 12345) & 0x7fffffff;
                float x = 70f + (hash % 560);
                int type = (hash / 97) % 5;
                float s = 16f * kx;
                clipPath.reset();
                switch (type) {
                    case 0:
                        for (int i = 0; i < 5; i++) {
                            double a1 = -Math.PI / 2 + i * 2 * Math.PI / 5;
                            double a2 = a1 + Math.PI / 5;
                            float x1 = x * kx + (float) Math.cos(a1) * s;
                            float y1 = sy * ky + (float) Math.sin(a1) * s;
                            float x2 = x * kx + (float) Math.cos(a2) * s * 0.45f;
                            float y2 = sy * ky + (float) Math.sin(a2) * s * 0.45f;
                            if (i == 0) clipPath.moveTo(x1, y1); else clipPath.lineTo(x1, y1);
                            clipPath.lineTo(x2, y2);
                        }
                        clipPath.close();
                        c.drawPath(clipPath, p);
                        break;
                    case 1:
                        for (int i = 0; i < 26; i++) {
                            double a = i * 0.42;
                            float rr = 2f + i * 0.7f * kx;
                            float xx = x * kx + (float) Math.cos(a) * rr;
                            float yy = sy * ky + (float) Math.sin(a) * rr;
                            if (i == 0) clipPath.moveTo(xx, yy); else clipPath.lineTo(xx, yy);
                        }
                        c.drawPath(clipPath, p);
                        break;
                    case 2:
                        clipPath.moveTo(x * kx, sy * ky + s);
                        clipPath.lineTo(x * kx, sy * ky - s);
                        clipPath.moveTo(x * kx - s * 0.55f, sy * ky - s * 0.35f);
                        clipPath.lineTo(x * kx, sy * ky - s);
                        clipPath.lineTo(x * kx + s * 0.55f, sy * ky - s * 0.35f);
                        c.drawPath(clipPath, p);
                        break;
                    case 3:
                        c.drawCircle(x * kx, sy * ky, s * 0.7f, p);
                        c.drawCircle(x * kx + s * 0.9f, sy * ky + s * 0.15f, s * 0.55f, p);
                        c.drawCircle(x * kx - s * 0.9f, sy * ky + s * 0.2f, s * 0.45f, p);
                        break;
                    default:
                        clipPath.moveTo(x * kx - s, sy * ky);
                        clipPath.lineTo(x * kx - s * 0.4f, sy * ky + s * 0.6f);
                        clipPath.lineTo(x * kx + s, sy * ky - s * 0.8f);
                        c.drawPath(clipPath, p);
                }
            }
            p.setStyle(Paint.Style.FILL);
        }

        void drawPlats(Canvas c) {
            for (Plat pl : plats) {
                float y = pl.y - camY;
                if (y < -90 || y > VH + 90) continue;
                drawPlatX(c, pl, y, 0);
                if (pl.x < VW * 0.35f) drawPlatX(c, pl, y, VW);
                if (pl.x + pl.w > VW * 0.65f) drawPlatX(c, pl, y, -VW);
            }
        }

        void drawPlatX(Canvas c, Plat pl, float y, float off) {
            float x = pl.x + off, w = pl.w, th = PLAT_H;
            int body = 0xFF8FD14F, hi = 0xFFBCE983, dark = 0xFF5E9B32;
            if (pl.type == 2) { body = 0xFFD08B4E; hi = 0xFFEDB47B; dark = 0xFF9A5A28; }
            else if (pl.type == 1) { body = 0xFF6FB6E8; hi = 0xFFA9D7F7; dark = 0xFF3C7FAF; }
            int alpha = pl.dead ? 70 : 255;
            body = withAlpha(body, alpha);
            hi = withAlpha(hi, alpha);
            dark = withAlpha(dark, alpha);

            p.setStyle(Paint.Style.FILL);
            p.setColor(withAlpha(0xFF2F3A24, pl.dead ? 25 : 40));
            c.drawRoundRect(new RectF((x + 3) * kx, (y + 6) * ky, (x + w + 3) * kx, (y + th + 8) * ky), 12 * kx, 12 * kx, p);

            p.setColor(body);
            c.drawRoundRect(new RectF(x * kx, y * ky, (x + w) * kx, (y + th) * ky), 12 * kx, 12 * kx, p);
            p.setColor(hi);
            c.drawRoundRect(new RectF((x + 5) * kx, (y + 4) * ky, (x + w - 5) * kx, (y + th * 0.45f) * ky), 9 * kx, 9 * kx, p);
            p.setColor(dark);
            c.drawRoundRect(new RectF((x + 5) * kx, (y + th * 0.72f) * ky, (x + w - 5) * kx, (y + th - 3) * ky), 8 * kx, 8 * kx, p);

            ink.setStyle(Paint.Style.STROKE);
            ink.setStrokeWidth(3.2f * kx);
            ink.setColor(withAlpha(0xFF2F3A24, pl.dead ? 60 : 210));
            c.drawRoundRect(new RectF(x * kx, y * ky, (x + w) * kx, (y + th) * ky), 12 * kx, 12 * kx, ink);

            if (pl.type == 2) {
                ink.setStrokeWidth(2.6f * kx);
                ink.setColor(withAlpha(0xFF7A4318, 200));
                clipPath.reset();
                clipPath.moveTo((x + w * 0.36f) * kx, (y + 2) * ky);
                clipPath.lineTo((x + w * 0.48f) * kx, (y + th * 0.55f) * ky);
                clipPath.lineTo((x + w * 0.38f) * kx, (y + th - 2) * ky);
                c.drawPath(clipPath, ink);
                clipPath.reset();
                clipPath.moveTo((x + w * 0.72f) * kx, (y + 2) * ky);
                clipPath.lineTo((x + w * 0.63f) * kx, (y + th * 0.5f) * ky);
                c.drawPath(clipPath, ink);
            }
            if (pl.type == 1) {
                ink.setStrokeWidth(3f * kx);
                ink.setColor(withAlpha(0xFF1F5A80, 220));
                float cy2 = (y + th / 2f) * ky;
                clipPath.reset();
                clipPath.moveTo((x + w * 0.30f) * kx, cy2 - 6 * ky);
                clipPath.lineTo((x + w * 0.22f) * kx, cy2);
                clipPath.lineTo((x + w * 0.30f) * kx, cy2 + 6 * ky);
                clipPath.moveTo((x + w * 0.70f) * kx, cy2 - 6 * ky);
                clipPath.lineTo((x + w * 0.78f) * kx, cy2);
                clipPath.lineTo((x + w * 0.70f) * kx, cy2 + 6 * ky);
                c.drawPath(clipPath, ink);
            }
            if (pl.spring && !pl.dead) {
                float cx = (x + w * 0.5f) * kx;
                float comp = pl.springT * 9f * ky;
                float baseY = (y - 2) * ky + comp;
                ink.setStyle(Paint.Style.STROKE);
                ink.setStrokeWidth(4.2f * kx);
                ink.setColor(0xFF3A4A22);
                clipPath.reset();
                clipPath.moveTo(cx - 13 * kx, baseY);
                clipPath.lineTo(cx - 6 * kx, baseY - 10 * ky + comp * 0.3f);
                clipPath.lineTo(cx + 3 * kx, baseY - 2 * ky);
                clipPath.lineTo(cx + 12 * kx, baseY - 12 * ky + comp * 0.3f);
                c.drawPath(clipPath, ink);
                p.setStyle(Paint.Style.FILL);
                p.setColor(0xFFE0574C);
                c.drawRoundRect(new RectF(cx - 19 * kx, baseY - 20 * ky + comp * 0.4f,
                        cx + 19 * kx, baseY - 12 * ky + comp * 0.4f), 5 * kx, 5 * kx, p);
            }
            p.setStyle(Paint.Style.FILL);
        }

        int withAlpha(int color, int a) { return (color & 0x00FFFFFF) | (a << 24); }

        void drawParts(Canvas c) {
            for (Particle q : parts) {
                p.setColor(q.color);
                p.setAlpha((int) (255 * Math.max(0, q.life / q.max)));
                c.drawCircle(q.x * kx, (q.y - camY) * ky, q.size * kx * (0.4f + 0.6f * q.life / q.max), p);
            }
            p.setAlpha(255);
        }

        void drawPlayer(Canvas c) {
            float rot = clamp(vel / 55f, -14f, 16f);
            if (controlMode == CTRL_TOUCH && touchX >= 0) rot += clamp((touchX - px) * 0.02f, -10f, 10f);
            if (controlMode == CTRL_BUTTONS) rot += btnDir * 8f;
            float st;
            if (vel < 0) st = 1f + Math.min(0.22f, -vel / 5200f);
            else st = 1f - Math.min(0.16f, vel / 6200f);
            if (landSquashT > 0) st = 1f - 0.22f * landSquashT * squash;
            c.save();
            c.translate(px * kx, py * ky);
            c.rotate(rot);
            c.scale(1f / Math.max(0.7f, st), st);
            drawAvatarLocal(c, BOX);
            c.restore();
        }

        void drawPlayerHome(Canvas c) {
            float y = VH * 0.42f + (float) Math.sin(animT * 2.4f) * 16f;
            c.save();
            c.translate(VW * 0.5f * kx, y * ky);
            c.rotate((float) Math.sin(animT * 2.4f) * 6f);
            drawAvatarLocal(c, BOX * 1.45f);
            c.restore();
        }

        void drawAvatarLocal(Canvas c, float size) {
            float r = size / 2f * kx;
            p.setStyle(Paint.Style.FILL);
            p.setColor(0x33000000);
            c.drawCircle(4 * kx, 7 * ky, r, p);
            p.setColor(0xFFFFFFFF);
            c.drawCircle(0, 0, r, p);
            if (avatar != null) {
                c.save();
                clipPath.reset();
                clipPath.addCircle(0, 0, r, Path.Direction.CW);
                c.clipPath(clipPath);
                c.drawBitmap(avatar, null, new RectF(-r, -r, r, r), p);
                c.restore();
            }
            ink.setStyle(Paint.Style.STROKE);
            ink.setStrokeWidth(4f * kx);
            ink.setColor(bgIndex == 0 ? 0xFF2F3A24 : 0xFFFFFFFF);
            c.drawCircle(0, 0, r, ink);
            p.setStyle(Paint.Style.FILL);
        }

        // ------------------------------------------------------------------
        // UI: разметка + отрисовка
        // ------------------------------------------------------------------
        void layoutUi() {
            uiReady = true;
            btns.clear();
            float w = getWidth(), h = getHeight();
            float S = tx;

            if (state == STATE_HOME) {
                addBtn(centered(w, h * 0.60f, 420 * S, 116 * S), "ИГРАТЬ", icPlay, btnAi[0], 10, false);
                addBtn(centered(w, h * 0.735f, 300 * S, 92 * S), "НАСТРОЙКИ", icGear, btnAi[1], 12, false);
                // иконки-кнопки в углу
                addSmall(w - 86 * S, 74 * S, 64 * S, soundOn ? icSoundOn : icSoundOff, soundOn ? btnAi[0] : btnAi[4], 13);
            } else if (state == STATE_DEAD) {
                float cy = h * 0.34f;
                addBtn(rect(w / 2f - 210 * S, cy + 250 * S, 420 * S, 96 * S), "ЕЩЁ РАЗ", icRestart, btnAi[0], 11, false);
                addBtn(rect(w / 2f - 150 * S, cy + 362 * S, 300 * S, 76 * S), "В МЕНЮ", icHome, btnAi[4], 15, false);
            } else if (state == STATE_SETTINGS) {
                float top = h * 0.155f;
                float rowH = 104 * S;
                // 1) управление — три кнопки
                float bw = 180 * S, bh = 84 * S, gap = 12 * S;
                float totalW = bw * 3 + gap * 2;
                float x0 = (w - totalW) / 2f;
                addBtn(rect(x0, top, bw, bh), "ПАЛЕЦ", icTouch, controlMode == CTRL_TOUCH ? btnAi[0] : btnAi[4], 20, true);
                addBtn(rect(x0 + bw + gap, top, bw, bh), "НАКЛОН", icTilt, controlMode == CTRL_TILT ? btnAi[0] : btnAi[4], 21, true);
                addBtn(rect(x0 + 2 * (bw + gap), top, bw, bh), "КНОПКИ", icArrows, controlMode == CTRL_BUTTONS ? btnAi[0] : btnAi[4], 22, true);

                // 2) чувствительность
                float y1 = top + rowH;
                addSmall(x0 - 0, y1 + 8 * S, 62 * S, icMinus, btnAi[4], 30);
                addSmall(x0 + totalW - 62 * S, y1 + 8 * S, 62 * S, icPlus, btnAi[4], 31);

                // 3) скорость игры
                float y2 = y1 + rowH;
                addSmall(x0, y2 + 8 * S, 62 * S, icMinus, btnAi[4], 32);
                addSmall(x0 + totalW - 62 * S, y2 + 8 * S, 62 * S, icPlus, btnAi[4], 33);

                // 4) тумблеры
                float y3 = y2 + rowH;
                addBtn(rect(x0, y3, bw, bh), vibration ? "ВИБРАЦИЯ ВКЛ" : "ВИБРАЦИЯ ВЫКЛ", null, vibration ? btnAi[0] : btnAi[4], 40, true);
                addBtn(rect(x0 + bw + gap, y3, bw, bh), soundOn ? "ЗВУК ВКЛ" : "ЗВУК ВЫКЛ", soundOn ? icSoundOn : icSoundOff, soundOn ? btnAi[0] : btnAi[4], 41, true);
                addBtn(rect(x0 + 2 * (bw + gap), y3, bw, bh), "СБРОС РЕКОРДА", null, btnAi[5], 42, true);

                // 5) фоны — 4 миниатюры
                float ty = y3 + rowH + 34 * S;
                float tw = (totalW - gap) / 2f, thh = 118 * S;
                float thh2 = thh * 1.55f;   // вертикальные превью под 9:16
                addBtn(rect(x0, ty, tw, thh2), "", thAiPaper, bgIndex == 0 ? btnAi[0] : btnAi[4], 50, true);
                addBtn(rect(x0 + tw + gap, ty, tw, thh2), "", thAiCity, bgIndex == 1 ? btnAi[0] : btnAi[4], 51, true);
                addBtn(rect(x0, ty + thh2 + gap, tw, thh2), "", thAiSpace, bgIndex == 2 ? btnAi[0] : btnAi[4], 52, true);
                addBtn(rect(x0 + tw + gap, ty + thh2 + gap, tw, thh2), "", thAiSunset, bgIndex == 3 ? btnAi[0] : btnAi[4], 53, true);

                addSmall(w - 86 * S, 74 * S, 64 * S, icBack, btnAi[4], 16);
            }
        }

        RectF rect(float x, float y, float w, float h) { return new RectF(x, y, x + w, y + h); }

        RectF centered(float w, float y, float bw, float bh) {
            return new RectF(w / 2f - bw / 2f, y, w / 2f + bw / 2f, y + bh);
        }

        Bitmap pickBtn(boolean green, boolean blue, boolean red) {
            if (green) return btnAi[0];
            if (blue) return btnAi[1];
            if (red) return btnAi[5];
            return btnAi[4];
        }

        void addBtn(RectF r, String text, Bitmap icon, Bitmap fill, int id, boolean small) {
            Btn b = new Btn();
            b.r = r;
            b.text = text;
            b.icon = icon;
            b.fill = fill;
            b.id = id;
            b.small = small;
            btns.add(b);
        }

        void addSmall(float x, float y, float size, Bitmap icon, Bitmap fill, int id) {
            addBtn(new RectF(x, y, x + size, y + size), null, icon, fill, id, true);
        }

        void drawUi(Canvas c) {
            int w = getWidth(), h = getHeight();
            float S = tx;

            if (state == STATE_HOME) drawHome(c);
            else if (state == STATE_PLAY) drawHud(c);
            else if (state == STATE_DEAD) drawDead(c);
            else if (state == STATE_SETTINGS) drawSettings(c);

            // общая отрисовка кнопок
            for (Btn b : btns) drawButton(c, b);

            // кнопка настроек в игре (верхний правый угол)
            if (state == STATE_PLAY) {
                RectF gr = rect(w - 78 * S, 44 * S, 54 * S, 54 * S);
                p.setStyle(Paint.Style.FILL);
                p.setColor(0x44000000);
                c.drawRoundRect(gr, 16 * S, 16 * S, p);
                if (icGear != null) {
                    RectF ir = rect(gr.left + 9 * S, gr.top + 9 * S, 36 * S, 36 * S);
                    p.setAlpha(230);
                    c.drawBitmap(icGear, null, ir, p);
                    p.setAlpha(255);
                }
            }
        }

        void drawButton(Canvas c, Btn b) {
            float S = tx;
            RectF r = b.r;
            // тень
            p.setStyle(Paint.Style.FILL);
            p.setColor(0x33000000);
            c.drawRoundRect(new RectF(r.left + 3 * S, r.top + 5 * S, r.right + 3 * S, r.bottom + 5 * S),
                    22 * S, 22 * S, p);
            // фон-картинка кнопки (9-патч)
            if (b.fill != null) {
                drawCover(c, b.fill, r);
            } else {
                p.setColor(0xFF8FD14F);
                c.drawRoundRect(r, 22 * S, 22 * S, p);
            }

            float iconSize = Math.min(r.height() * 0.52f, 46 * S);
            float textSize = b.small ? 26 * S : 44 * S;

            // иконка слева от текста
            if (b.icon != null) {
                if (b.text == null || b.text.length() == 0) {
                    // превью фонов — заполняем кнопку целиком, иконки — по центру
                    boolean isThumb = (b.id >= 50 && b.id <= 53);
                    if (isThumb) {
                        drawCover(c, b.icon, r);
                    } else {
                        float ic = Math.min(r.width(), r.height()) * 0.56f;
                        RectF ir = new RectF(r.centerX() - ic / 2f, r.centerY() - ic / 2f,
                                r.centerX() + ic / 2f, r.centerY() + ic / 2f);
                        p.setAlpha(245);
                        c.drawBitmap(b.icon, null, ir, p);
                        p.setAlpha(255);
                    }
                } else {
                    RectF ir = new RectF(r.left + 16 * S, r.centerY() - iconSize / 2f,
                            r.left + 16 * S + iconSize, r.centerY() + iconSize / 2f);
                    p.setAlpha(245);
                    c.drawBitmap(b.icon, null, ir, p);
                    p.setAlpha(255);
                    drawLabel(c, b.text, r.centerX() + iconSize * 0.35f, r.centerY() + textSize * 0.36f,
                            textSize, 0xFFFFFFFF);
                }
            } else if (b.text != null && b.text.length() > 0) {
                drawLabel(c, b.text, r.centerX(), r.centerY() + textSize * 0.36f, textSize, 0xFFFFFFFF);
            }
        }

        // рисует картинку «по размеру» (аналог centerCrop), без искажений
        void drawCover(Canvas c, Bitmap bm, RectF dst) {
            float bw = bm.getWidth(), bh = bm.getHeight();
            float sc = Math.max(dst.width() / bw, dst.height() / bh);
            float sw = dst.width() / sc, sh = dst.height() / sc;
            float sx = (bw - sw) / 2f, sy = (bh - sh) / 2f;
            srcRect.set((int) sx, (int) sy, (int) (sx + sw), (int) (sy + sh));
            c.drawBitmap(bm, srcRect, dst, p);
        }

        void drawInside(Canvas c, Bitmap bm, RectF dst) {
            float bw = bm.getWidth(), bh = bm.getHeight();
            float sc = Math.min(dst.width() / bw, dst.height() / bh);
            float w = bw * sc, h = bh * sc;
            RectF d = new RectF(dst.centerX() - w / 2f, dst.centerY() - h / 2f,
                    dst.centerX() + w / 2f, dst.centerY() + h / 2f);
            c.drawBitmap(bm, null, d, p);
        }

        void drawLabel(Canvas c, String s, float x, float y, float size, int color) {
            textPaint.setTextSize(size);
            textPaint.setTextAlign(Paint.Align.CENTER);
            textPaint.setTypeface(Typeface.create(Typeface.DEFAULT, Typeface.BOLD));
            textPaint.setStyle(Paint.Style.STROKE);
            textPaint.setStrokeWidth(size * 0.14f);
            textPaint.setColor(0x55000000);
            c.drawText(s, x, y, textPaint);
            textPaint.setStyle(Paint.Style.FILL);
            textPaint.setColor(color);
            c.drawText(s, x, y, textPaint);
        }

        void drawHud(Canvas c) {
            int w = getWidth();
            int inkCol = colorForBg();
            drawLabel(c, "" + score, w / 2f, 150 * ky, 104 * tx, inkCol);
            textPaint.setTextSize(36 * tx);
            textPaint.setTextAlign(Paint.Align.LEFT);
            textPaint.setStyle(Paint.Style.FILL);
            textPaint.setColor(inkCol);
            c.drawText("м", w / 2f + 62 * tx, 150 * ky, textPaint);
            drawLabel(c, "РЕКОРД " + best, w / 2f, 200 * ky, 30 * tx, inkCol);

            // кнопки управления (режим «КНОПКИ»)
            if (controlMode == CTRL_BUTTONS) {
                float S = tx;
                float size = 108 * S;
                float y = getHeight() - size - 40 * S;
                RectF left = rect(30 * S, y, size, size);
                RectF right = rect(getWidth() - 30 * S - size, y, size, size);
                drawButton(c, mk(left, null, btnAi[4], -1));
                drawButton(c, mk(right, null, btnAi[4], 1));
                drawTri(c, left.centerX(), left.centerY(), -1, 26 * S);
                drawTri(c, right.centerX(), right.centerY(), 1, 26 * S);
            }
        }

        void drawTri(Canvas c, float cx, float cy, int dir, float s) {
            clipPath.reset();
            clipPath.moveTo(cx + dir * s, cy);
            clipPath.lineTo(cx - dir * s * 0.6f, cy - s * 0.8f);
            clipPath.lineTo(cx - dir * s * 0.6f, cy + s * 0.8f);
            clipPath.close();
            p.setStyle(Paint.Style.FILL);
            p.setColor(0xAA000000);
            c.drawPath(clipPath, p);
        }

        Btn mk(RectF r, Bitmap icon, Bitmap fill, int id) {
            Btn b = new Btn();
            b.r = r; b.icon = icon; b.fill = fill; b.id = id;
            return b;
        }

        void drawHome(Canvas c) {
            int w = getWidth(), h = getHeight();
            float cx = w / 2f;
            int inkCol = colorForBg();

            drawLabel(c, "МЕЛЛДЖАМП", cx, h * 0.115f, 92 * tx, inkCol);
            drawLabel(c, "прыгай, да?", cx, h * 0.168f, 42 * tx, bgIndex == 0 ? 0xFF3E7A2E : 0xFFB6F09A);

            if (avatar != null) {
                float size = 210 * tx;
                float top = h * 0.215f;
                RectF card = new RectF(cx - size / 2 - 12, top - 12, cx + size / 2 + 12, top + size + 12);
                p.setStyle(Paint.Style.FILL);
                p.setColor(0x33000000);
                c.drawRoundRect(new RectF(card.left + 5, card.top + 7, card.right + 5, card.bottom + 7), 16, 16, p);
                p.setColor(0xFFFFFFFF);
                c.drawRoundRect(card, 16, 16, p);
                c.drawBitmap(avatar, null, new RectF(card.left + 10, card.top + 10, card.right - 10, card.bottom - 10), p);
                ink.setStyle(Paint.Style.STROKE);
                ink.setStrokeWidth(3f * tx);
                ink.setColor(inkCol);
                c.drawRoundRect(card, 16, 16, ink);
                drawLabel(c, "он не против", cx, card.bottom + 46 * tx, 30 * tx, inkCol);
            }

            drawLabel(c, "Рекорд: " + best + " м", cx, h * 0.845f, 34 * tx, inkCol);
            textPaint.setTextSize(22 * tx);
            textPaint.setTextAlign(Paint.Align.CENTER);
            textPaint.setStyle(Paint.Style.FILL);
            textPaint.setColor(withAlpha(inkCol, 170));
            c.drawText("Управление: " + ctrlName() + " · фон: " + bgName(),
                    cx, h * 0.885f, textPaint);
        }

        String ctrlName() {
            switch (controlMode) {
                case CTRL_TILT: return "наклон";
                case CTRL_BUTTONS: return "кнопки";
                default: return "палец";
            }
        }

        String bgName() {
            switch (bgIndex) {
                case 1: return "город";
                case 2: return "космос";
                case 3: return "закат";
                default: return "тетрадь";
            }
        }

        void drawDead(Canvas c) {
            int w = getWidth(), h = getHeight();
            float cx = w / 2f;
            int inkCol = colorForBg();

            p.setStyle(Paint.Style.FILL);
            p.setColor(0x55000000);
            c.drawRect(0, 0, w, h, p);

            float cy = h * 0.34f;
            RectF pan = new RectF(40 * tx, cy - 190 * tx, w - 40 * tx, cy + 300 * tx);
            p.setColor(0xF2FFFDF6);
            c.drawRoundRect(pan, 30, 30, p);
            ink.setStyle(Paint.Style.STROKE);
            ink.setStrokeWidth(3.4f * tx);
            ink.setColor(0xFF2F3A24);
            c.drawRoundRect(pan, 30, 30, ink);

            if (avatar != null) {
                float s = 112 * tx;
                RectF dst = new RectF(cx - s / 2, cy - 164 * tx, cx + s / 2, cy - 164 * tx + s);
                p.setColor(0xFFFFFFFF);
                c.drawRoundRect(new RectF(dst.left - 7, dst.top - 7, dst.right + 7, dst.bottom + 7), 14, 14, p);
                c.drawBitmap(avatar, null, dst, p);
            }
            drawLabel(c, "УПАЛ, ДА?", cx, cy + 26 * tx, 46 * tx, 0xFF2F3A24);
            drawLabel(c, score + " м", cx, cy + 130 * tx, 88 * tx, 0xFF2F3A24);
            textPaint.setTextSize(28 * tx);
            textPaint.setTextAlign(Paint.Align.CENTER);
            textPaint.setStyle(Paint.Style.FILL);
            textPaint.setColor(0xFF7C8A6E);
            c.drawText("рекорд: " + best + " м", cx, cy + 176 * tx, textPaint);
        }

        void drawSettings(Canvas c) {
            int w = getWidth(), h = getHeight();
            int inkCol = colorForBg();

            p.setStyle(Paint.Style.FILL);
            p.setColor(0x66000000);
            c.drawRect(0, 0, w, h, p);

            drawLabel(c, "НАСТРОЙКИ", w / 2f, h * 0.095f, 62 * tx, 0xFFFFFFFF);

            float top = h * 0.155f;
            float rowH = 104 * tx;
            float bw = 180 * tx, gap = 12 * tx;
            float totalW = bw * 3 + gap * 2;
            float x0 = (w - totalW) / 2f;

            smallText(c, "УПРАВЛЕНИЕ", x0, top - 14 * tx, 24 * tx, 0xCCFFFFFF);
            smallText(c, "ЧУВСТВИТЕЛЬНОСТЬ  " + Math.round(sensitivity * 100) + "%", x0, top + rowH - 18 * tx, 24 * tx, 0xCCFFFFFF);
            smallText(c, "СКОРОСТЬ  " + Math.round(gameSpeed * 100) + "%", x0, top + rowH * 2 - 18 * tx, 24 * tx, 0xCCFFFFFF);

            // полоски-индикаторы
            float sy1 = top + rowH + 20 * tx;
            float sy2 = top + rowH * 2 + 20 * tx;
            drawSlider(c, x0 + 74 * tx, sy1, totalW - 148 * tx, 16 * tx, (sensitivity - 0.5f) / 1.1f);
            drawSlider(c, x0 + 74 * tx, sy2, totalW - 148 * tx, 16 * tx, (gameSpeed - 0.5f) / 1.0f);

            float y3 = top + rowH * 3;
            smallText(c, "ЗВУК И ПРОЧЕЕ", x0, y3 - 14 * tx, 24 * tx, 0xCCFFFFFF);
            float ty = y3 + rowH + 26 * tx;
            smallText(c, "ФОН ИГРЫ", x0, ty - 18 * tx, 24 * tx, 0xCCFFFFFF);

            // подпись версии
            smallText(c, "Doodle Jump: Mellstroy · open source", x0, h - 40 * tx, 20 * tx, 0x88FFFFFF);
        }

        void smallText(Canvas c, String s, float x, float y, float size, int color) {
            textPaint.setTextSize(size);
            textPaint.setTextAlign(Paint.Align.LEFT);
            textPaint.setStyle(Paint.Style.FILL);
            textPaint.setColor(color);
            c.drawText(s, x, y, textPaint);
        }

        void drawSlider(Canvas c, float x, float y, float w, float h, float t) {
            t = clamp(t, 0f, 1f);
            p.setStyle(Paint.Style.FILL);
            p.setColor(0x55000000);
            c.drawRoundRect(new RectF(x, y, x + w, y + h), h / 2, h / 2, p);
            p.setColor(0xFF8FD14F);
            c.drawRoundRect(new RectF(x, y, x + Math.max(h, w * t), y + h), h / 2, h / 2, p);
            p.setColor(0xFFFFFFFF);
            c.drawCircle(x + Math.max(h / 2, w * t), y + h / 2, h * 1.15f, p);
            ink.setStyle(Paint.Style.STROKE);
            ink.setStrokeWidth(3 * tx);
            ink.setColor(0xFF2F3A24);
            c.drawCircle(x + Math.max(h / 2, w * t), y + h / 2, h * 1.15f, ink);
            p.setStyle(Paint.Style.FILL);
        }

        // ------------------------------------------------------------------
        // ВВОД
        // ------------------------------------------------------------------
        @Override public boolean onTouchEvent(MotionEvent e) {
            int a = e.getActionMasked();
            float x = e.getX(), y = e.getY();
            float vx2 = x / Math.max(0.0001f, kx);
            float vy2 = y / Math.max(0.0001f, ky);

            if (!uiReady) layoutUi();

            switch (a) {
                case MotionEvent.ACTION_DOWN: {
                    // кнопки UI
                    for (Btn b : btns) {
                        if (b.r.contains(x, y)) { onButton(b.id); return true; }
                    }
                    // кнопка настроек в игре
                    if (state == STATE_PLAY) {
                        RectF gr = rect(getWidth() - 78 * tx, 44 * tx, 54 * tx, 54 * tx);
                        if (gr.contains(x, y)) { openSettings(); return true; }
                    }
                    // слайдеры в настройках
                    if (state == STATE_SETTINGS) {
                        float top = getHeight() * 0.155f, rowH = 104 * tx;
                        float bw = 180 * tx, gap = 12 * tx;
                        float totalW = bw * 3 + gap * 2;
                        float x0 = (getWidth() - totalW) / 2f;
                        float sx = x0 + 74 * tx, sw = totalW - 148 * tx;
                        float sy1 = top + rowH + 20 * tx, sy2 = top + rowH * 2 + 20 * tx;
                        RectF r1 = rect(sx - 20, sy1 - 26 * tx, sw + 40, 60 * tx);
                        RectF r2 = rect(sx - 20, sy2 - 26 * tx, sw + 40, 60 * tx);
                        if (r1.contains(x, y)) { sliderDragId = 1; onSlider(1, x, sx, sw); return true; }
                        if (r2.contains(x, y)) { sliderDragId = 2; onSlider(2, x, sx, sw); return true; }
                    }
                    // управление в игре
                    if (state == STATE_PLAY) {
                        if (controlMode == CTRL_BUTTONS) {
                            float S = tx, size = 108 * S, by = getHeight() - size - 40 * S;
                            if (rect(30 * S, by, size, size).contains(x, y)) { btnDir = -1; return true; }
                            if (rect(getWidth() - 30 * S - size, by, size, size).contains(x, y)) { btnDir = 1; return true; }
                        }
                        if (controlMode == CTRL_TOUCH) touchX = vx2;
                    }
                    return true;
                }
                case MotionEvent.ACTION_MOVE: {
                    if (sliderDragId > 0 && state == STATE_SETTINGS) {
                        float top = getHeight() * 0.155f, rowH = 104 * tx;
                        float bw = 180 * tx, gap = 12 * tx;
                        float totalW = bw * 3 + gap * 2;
                        float x0 = (getWidth() - totalW) / 2f;
                        float sx = x0 + 74 * tx, sw = totalW - 148 * tx;
                        onSlider(sliderDragId, x, sx, sw);
                        return true;
                    }
                    if (state == STATE_PLAY) {
                        if (controlMode == CTRL_TOUCH) touchX = vx2;
                        else if (controlMode == CTRL_BUTTONS) {
                            float S = tx, size = 108 * S, by = getHeight() - size - 40 * S;
                            if (rect(30 * S, by, size, size).contains(x, y)) btnDir = -1;
                            else if (rect(getWidth() - 30 * S - size, by, size, size).contains(x, y)) btnDir = 1;
                        }
                    }
                    return true;
                }
                case MotionEvent.ACTION_UP:
                case MotionEvent.ACTION_CANCEL:
                    sliderDragId = 0;
                    if (state == STATE_PLAY) { touchX = -1; btnDir = 0; }
                    return true;
            }
            return true;
        }

        void onSlider(int id, float x, float sx, float sw) {
            float t = clamp((x - sx) / sw, 0f, 1f);
            if (id == 1) {
                sensitivity = 0.5f + t * 1.1f;
                sensitivity = Math.round(sensitivity * 20f) / 20f;
            } else {
                gameSpeed = 0.5f + t * 1.0f;
                gameSpeed = Math.round(gameSpeed * 20f) / 20f;
            }
            uiReady = false;
            saveSettings();
        }

        void onButton(int id) {
            switch (id) {
                case 10: start(); break;
                case 11: start(); break;
                case 12: openSettings(); break;
                case 13: soundOn = !soundOn; applySound(); saveSettings(); uiReady = false; break;
                case 15: goHome(); break;
                case 16: closeSettings(); break;
                case 20: controlMode = CTRL_TOUCH; saveSettings(); uiReady = false; break;
                case 21: controlMode = CTRL_TILT; saveSettings(); uiReady = false; break;
                case 22: controlMode = CTRL_BUTTONS; saveSettings(); uiReady = false; break;
                case 30: sensitivity = Math.max(0.5f, sensitivity - 0.1f); saveSettings(); uiReady = false; break;
                case 31: sensitivity = Math.min(1.6f, sensitivity + 0.1f); saveSettings(); uiReady = false; break;
                case 32: gameSpeed = Math.max(0.5f, gameSpeed - 0.1f); saveSettings(); uiReady = false; break;
                case 33: gameSpeed = Math.min(1.5f, gameSpeed + 0.1f); saveSettings(); uiReady = false; break;
                case 40: vibration = !vibration; saveSettings(); uiReady = false; break;
                case 41: soundOn = !soundOn; applySound(); saveSettings(); uiReady = false; break;
                case 42:
                    best = 0;
                    getContext().getSharedPreferences("dj", 0).edit().putInt("best", 0).apply();
                    uiReady = false;
                    break;
                case 50: bgIndex = 0; saveSettings(); uiReady = false; break;
                case 51: bgIndex = 1; saveSettings(); uiReady = false; break;
                case 52: bgIndex = 2; saveSettings(); uiReady = false; break;
                case 53: bgIndex = 3; saveSettings(); uiReady = false; break;
            }
            invalidate();
        }

        void applySound() {
            if (music == null) return;
            if (soundOn) { music.setVolume(0.42f, 0.42f); if (!music.isPlaying()) startMusic(); }
            else music.setVolume(0f, 0f);
        }

        // ------------------------------------------------------------------
        void startMusic() {
            if (music != null && soundOn) { try { music.start(); } catch (Exception ignored) {} }
        }

        void mediaInit() {
            if (music == null) {
                try {
                    music = MediaPlayer.create(getContext(), R.raw.music);
                    if (music != null) {
                        music.setLooping(true);
                        music.setVolume(soundOn ? 0.42f : 0f, soundOn ? 0.42f : 0f);
                    }
                } catch (Exception ignored) {}
            }
        }

        void resume() {
            mediaInit();
            if (sm != null && accelSensor != null)
                sm.registerListener(this, accelSensor, SensorManager.SENSOR_DELAY_GAME);
            lastNano = 0;
            physicsAcc = 0;
            running = true;
            startMusic();
            postInvalidateOnAnimation();
        }

        void pause() {
            if (sm != null) sm.unregisterListener(this);
            running = false;
            if (music != null && music.isPlaying()) music.pause();
        }

        @Override public void onSensorChanged(SensorEvent ev) {
            if (ev.sensor.getType() == Sensor.TYPE_ACCELEROMETER) {
                float v = -ev.values[0] / 9.81f;
                tilt = clamp(v, -1f, 1f);
            }
        }

        @Override public void onAccuracyChanged(Sensor s, int acc) {}
    }
}
