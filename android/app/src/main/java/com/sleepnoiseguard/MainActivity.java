package com.sleepnoiseguard;

import android.Manifest;
import android.app.Activity;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.media.ToneGenerator;
import android.media.AudioManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.Gravity;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.ScrollView;
import android.widget.TextView;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

public class MainActivity extends Activity {
    private final Handler mainHandler = new Handler(Looper.getMainLooper());
    private volatile boolean running = false;
    private Thread worker;

    private TextView status;
    private TextView currentDb;
    private TextView triggerCountView;
    private TextView hourNoiseView;
    private TextView hourTriggerView;
    private TextView dayNoiseView;
    private TextView dayTriggerView;
    private TextView logView;
    private ProgressBar levelBar;

    private EditText thresholdInput;
    private EditText durationInput;
    private EditText noiseEventsInput;
    private EditText feedbackRepeatsInput;
    private EditText cooldownInput;
    private EditText calibrationInput;
    private EditText logPathInput;

    private int triggerCount = 0;
    private int hourNoise = 0;
    private int hourTrigger = 0;
    private int dayNoise = 0;
    private int dayTrigger = 0;
    private String currentHour = "";
    private String currentDay = "";
    private long aboveSinceMs = -1;
    private long lastTriggeredMs = -1;
    private int noisySamples = 0;

    @Override
    protected void onCreate(Bundle bundle) {
        super.onCreate(bundle);
        buildUi();
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 100);
        }
    }

    private void buildUi() {
        ScrollView scroll = new ScrollView(this);
        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setPadding(32, 28, 32, 28);
        root.setBackgroundColor(0xfff6f8fb);
        scroll.addView(root);

        TextView title = label("睡眠噪音守卫", 28, true);
        root.addView(title);
        status = label("就绪", 14, true);
        root.addView(status);

        currentDb = label("-- 估算分贝", 46, true);
        root.addView(currentDb);
        levelBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        levelBar.setMax(90);
        root.addView(levelBar, matchWrap());

        LinearLayout stats = row();
        triggerCountView = stat(stats, "触发次数", "0");
        hourNoiseView = stat(stats, "本小时噪音", "0");
        hourTriggerView = stat(stats, "本小时触发", "0");
        root.addView(stats);

        LinearLayout stats2 = row();
        dayNoiseView = stat(stats2, "今日噪音", "0");
        dayTriggerView = stat(stats2, "今日触发", "0");
        root.addView(stats2);

        thresholdInput = field(root, "噪音阈值 dB", "45");
        durationInput = field(root, "出现几秒后触发", "");
        noiseEventsInput = field(root, "出现几次后触发", "");
        feedbackRepeatsInput = field(root, "每次反馈播放次数", "");
        cooldownInput = field(root, "冷却时间 秒", "60");
        calibrationInput = field(root, "校准偏移", "94");
        logPathInput = field(root, "日志文件名", "noise_events.csv");

        LinearLayout actions = row();
        Button start = button("开始监听");
        start.setOnClickListener(v -> startListening());
        Button stop = button("停止");
        stop.setOnClickListener(v -> stopListening());
        Button test = button("测试音效");
        test.setOnClickListener(v -> playFeedback(1));
        actions.addView(start);
        actions.addView(stop);
        actions.addView(test);
        root.addView(actions);

        logView = label("运行记录", 13, false);
        root.addView(logView);
        setContentView(scroll);
    }

    private TextView label(String text, int size, boolean bold) {
        TextView view = new TextView(this);
        view.setText(text);
        view.setTextSize(size);
        view.setTextColor(0xff20242c);
        view.setPadding(0, 8, 0, 8);
        if (bold) view.setTypeface(null, 1);
        return view;
    }

    private LinearLayout row() {
        LinearLayout row = new LinearLayout(this);
        row.setOrientation(LinearLayout.HORIZONTAL);
        row.setGravity(Gravity.CENTER_VERTICAL);
        row.setPadding(0, 10, 0, 10);
        return row;
    }

    private TextView stat(LinearLayout parent, String title, String value) {
        TextView view = label(title + "\n" + value, 13, true);
        parent.addView(view, new LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1));
        return view;
    }

    private EditText field(LinearLayout root, String hint, String value) {
        EditText edit = new EditText(this);
        edit.setHint(hint);
        edit.setText(value);
        edit.setSingleLine(true);
        root.addView(edit, matchWrap());
        return edit;
    }

    private Button button(String text) {
        Button button = new Button(this);
        button.setText(text);
        return button;
    }

    private LinearLayout.LayoutParams matchWrap() {
        return new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT);
    }

    private void startListening() {
        if (running) return;
        if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(new String[]{Manifest.permission.RECORD_AUDIO}, 100);
            return;
        }
        running = true;
        status.setText("监听中");
        log("开始监听");
        worker = new Thread(this::recordLoop, "noise-monitor");
        worker.start();
    }

    private void stopListening() {
        running = false;
        status.setText("已停止");
        log("已停止");
    }

    private void recordLoop() {
        int sampleRate = 16000;
        int minBuffer = AudioRecord.getMinBufferSize(sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT);
        int bufferSize = Math.max(minBuffer, sampleRate / 2);
        AudioRecord recorder = new AudioRecord(MediaRecorder.AudioSource.MIC, sampleRate, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, bufferSize);
        short[] buffer = new short[bufferSize];
        recorder.startRecording();
        while (running) {
            int read = recorder.read(buffer, 0, buffer.length);
            if (read > 0) {
                double rms = 0.0;
                for (int i = 0; i < read; i++) rms += buffer[i] * buffer[i];
                rms = Math.sqrt(rms / read) / 32768.0;
                double dbfs = rms <= 0 ? -90.0 : Math.max(20.0 * Math.log10(rms), -90.0);
                double db = dbfs + doubleValue(calibrationInput, 94.0);
                handleLevel(db, dbfs);
            }
        }
        recorder.stop();
        recorder.release();
    }

    private void handleLevel(double db, double dbfs) {
        double threshold = doubleValue(thresholdInput, 45.0);
        long now = System.currentTimeMillis();
        boolean above = db >= threshold;
        boolean triggered = false;

        if (above) {
            if (aboveSinceMs < 0) {
                aboveSinceMs = now;
                noisySamples = 0;
            }
            noisySamples++;
            double minSeconds = optionalDouble(durationInput, 0.0);
            int minEvents = Math.max(1, optionalInt(noiseEventsInput, 1));
            double cooldownMs = doubleValue(cooldownInput, 60.0) * 1000.0;
            boolean enoughTime = now - aboveSinceMs >= minSeconds * 1000.0;
            boolean enoughEvents = noisySamples >= minEvents;
            boolean cooledDown = lastTriggeredMs < 0 || now - lastTriggeredMs >= cooldownMs;
            if (enoughTime && enoughEvents && cooledDown) {
                triggered = true;
                lastTriggeredMs = now;
                triggerCount++;
                int repeats = Math.max(1, optionalInt(feedbackRepeatsInput, 1));
                playFeedback(repeats);
            }
            recordNoise(db, triggered);
        } else {
            aboveSinceMs = -1;
            noisySamples = 0;
        }

        boolean finalTriggered = triggered;
        mainHandler.post(() -> updateStats(db, dbfs, finalTriggered));
    }

    private void recordNoise(double db, boolean triggered) {
        Date date = new Date();
        String hour = new SimpleDateFormat("yyyy-MM-dd HH:00", Locale.US).format(date);
        String day = new SimpleDateFormat("yyyy-MM-dd", Locale.US).format(date);
        if (!hour.equals(currentHour)) {
            currentHour = hour;
            hourNoise = 0;
            hourTrigger = 0;
        }
        if (!day.equals(currentDay)) {
            currentDay = day;
            dayNoise = 0;
            dayTrigger = 0;
        }
        hourNoise++;
        dayNoise++;
        if (triggered) {
            hourTrigger++;
            dayTrigger++;
        }

        File file = new File(getFilesDir(), logPathInput.getText().toString());
        boolean writeHeader = !file.exists();
        try (FileWriter writer = new FileWriter(file, true)) {
            if (writeHeader) writer.write("timestamp,hour,date,db,triggered,trigger_count\n");
            String timestamp = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(date);
            writer.write(timestamp + "," + hour + "," + day + "," + String.format(Locale.US, "%.1f", db) + "," + (triggered ? "1" : "0") + "," + triggerCount + "\n");
        } catch (IOException error) {
            log("日志写入失败：" + error.getMessage());
        }
    }

    private void updateStats(double db, double dbfs, boolean triggered) {
        currentDb.setText(String.format(Locale.CHINA, "%.1f 估算分贝", db));
        levelBar.setProgress((int) Math.max(0, Math.min(90, db)));
        triggerCountView.setText("触发次数\n" + triggerCount);
        hourNoiseView.setText("本小时噪音\n" + hourNoise);
        hourTriggerView.setText("本小时触发\n" + hourTrigger);
        dayNoiseView.setText("今日噪音\n" + dayNoise);
        dayTriggerView.setText("今日触发\n" + dayTrigger);
        if (triggered) log(String.format(Locale.CHINA, "触发反馈：%.1f dB / %.1f dBFS", db, dbfs));
    }

    private void playFeedback(int repeats) {
        new Thread(() -> {
            ToneGenerator tone = new ToneGenerator(AudioManager.STREAM_MUSIC, 80);
            for (int i = 0; i < repeats; i++) {
                tone.startTone(ToneGenerator.TONE_PROP_BEEP, 260);
                try {
                    Thread.sleep(360);
                } catch (InterruptedException ignored) {
                    Thread.currentThread().interrupt();
                }
            }
            tone.release();
        }).start();
    }

    private double doubleValue(EditText input, double fallback) {
        try {
            return Double.parseDouble(input.getText().toString().trim());
        } catch (Exception ignored) {
            return fallback;
        }
    }

    private double optionalDouble(EditText input, double fallback) {
        String text = input.getText().toString().trim();
        if (text.isEmpty()) return fallback;
        return doubleValue(input, fallback);
    }

    private int optionalInt(EditText input, int fallback) {
        try {
            String text = input.getText().toString().trim();
            if (text.isEmpty()) return fallback;
            return Integer.parseInt(text);
        } catch (Exception ignored) {
            return fallback;
        }
    }

    private void log(String line) {
        mainHandler.post(() -> logView.setText(logView.getText() + "\n" + line));
    }

    @Override
    protected void onDestroy() {
        running = false;
        super.onDestroy();
    }
}
