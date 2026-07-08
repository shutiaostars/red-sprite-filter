# Red Sprite Filter v1.0.0

The first downloadable macOS desktop release.

## Download

Download the Release asset below:

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
54a3873b3253c5f10ded084babd1cd58ce5d9722b1cc02be868b097fa2475268
```

## Main features

- Automatically screen suspected red sprite lightning from thunderstorm videos
- Scans the entire video; does not stop at the first candidate
- Single-video and batch folder scanning
- Precise and high-recall screening modes
- Auto-exports candidate keyframes, clips, CSV, HTML report, and contact sheet
- Manual labeling: confirm / suspected / exclude
- Export confirmed candidate list
- Native macOS standalone window, no browser redirect

## Installation

1. Download `red-sprite-filter-1.0.0.dmg`
2. Open the DMG
3. Drag `红色精灵筛选器.app` (shown as "Red Sprite Filter") to Applications or any folder
4. Right-click the app and choose "Open"

## Requirements

The current version requires the following on your Mac:

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

Recommended install:

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS security note

This build is not signed or notarized. On first launch macOS may warn that the developer cannot be verified. Right-click the app, choose "Open", then confirm in the dialog. A future public release should add Apple Developer ID signing and notarization.

## Known limitations

- This is a rule-based tool (color, shape, position, and timing features), not a machine-learning model
- Results still require manual review
- Not all runtime dependencies are bundled; a fresh machine may need them installed first
- Unsigned builds show a security warning on some macOS devices at first launch

## Who it's for

- Thunderstorm photographers
- Astrophotographers
- Transient luminous event (TLE) observation enthusiasts
- Anyone who wants to quickly find red-sprite candidate clips from large amounts of footage

---

# 红色精灵筛选器 v1.0.0

首个可下载的 macOS 桌面版本。

## 下载

请下载本 Release 附件：

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
54a3873b3253c5f10ded084babd1cd58ce5d9722b1cc02be868b097fa2475268
```

## 主要功能

- 从雷暴视频中自动筛选疑似红色精灵闪电
- 扫描完整条视频，不会遇到第一个候选就停止
- 支持单视频和文件夹批量扫描
- 支持精准筛选和高召回筛选
- 自动导出候选关键帧、候选片段、CSV、HTML 报告和 contact sheet
- 支持人工标记：确认、疑似、排除
- 支持导出确认候选列表
- macOS 原生独立窗口，不再跳转系统浏览器

## 安装方法

1. 下载 `red-sprite-filter-1.0.0.dmg`
2. 打开 DMG
3. 将 `红色精灵筛选器.app` 拖到 Applications 或任意文件夹
4. 右键 App，选择“打开”

## 依赖要求

当前版本需要本机已安装：

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

推荐安装命令：

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS 安全提示

当前版本未签名、未公证。首次打开时，macOS 可能提示无法验证开发者。

请右键点击 App，选择“打开”，再在弹窗中确认打开。

后续正式公开版本建议加入 Apple Developer ID 签名和 notarization 公证。

## 已知限制

- 当前版本不是机器学习模型，而是基于颜色、形态、位置和时序特征的候选筛选工具
- 结果仍需要人工复核
- 未内置所有运行依赖，陌生机器上可能需要先安装依赖
- 未签名版本在部分 macOS 设备上首次打开会有安全提示

## 适合谁

- 雷暴摄影师
- 星空摄影师
- 高空瞬态发光事件观测爱好者
- 想从大量素材里快速找红色精灵候选片段的人

---

# Red Sprite Filter v1.0.0（日本語）

最初のダウンロード可能な macOS デスクトップ版です。

## ダウンロード

以下の Release アセットをダウンロードしてください。

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
54a3873b3253c5f10ded084babd1cd58ce5d9722b1cc02be868b097fa2475268
```

## 主な機能

- 雷雲の映像からレッドスプライトの疑いがある稲妻を自動的にふるい分け
- 映像全体をスキャン（最初の候補で止まらない）
- 単一映像とフォルダの一括スキャン
- 精密ふるい分けと高再現ふるい分け
- 候補のキーフレーム・クリップ・CSV・HTML レポート・コンタクトシートを自動書き出し
- 目視ラベル付け：確定 / 疑わしい / 除外
- 確定済み候補リストの書き出し
- macOS ネイティブの独立ウィンドウ（ブラウザへの飛び先なし）

## インストール

1. `red-sprite-filter-1.0.0.dmg` をダウンロード
2. DMG を開く
3. `红色精灵筛选器.app`（表示名 "Red Sprite Filter"）を「アプリケーション」や任意のフォルダにドラッグ
4. アプリを右クリックし「開く」を選択

## 必要環境

現在のバージョンは対象の Mac に以下が必要です。

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

推奨インストール：

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS のセキュリティ注意

このビルドは署名・公証されていません。初回起動時に macOS が「開発元を確認できません」と警告する場合があります。アプリを右クリックし「開く」を選び、ダイアログで確認してください。将来の公開版で Apple Developer ID による署名と公証を追加する予定です。

## 既知の制限

- 機械学習モデルではなく、色・形状・位置・時間的特徴に基づくルールベースのツール
- 結果は引き続き目視確認が必要
- すべての依存関係が同梱されているわけではない（未導入の環境では事前インストールが必要）
- 未署名ビルドは一部の macOS 端末で初回にセキュリティ警告が表示される

## 対象となる方

- 雷雲カメラマン
- 星空撮影者
- TLE（高空急瞬発光現象）観測愛好家
- 大量の素材からレッドスプライトの候補クリップを手早く見つけたい方

---

# Red Sprite Filter v1.0.0 (Español)

Primera versión de escritorio para macOS descargable.

## Descarga

Descarga el asset de la Release:

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
54a3873b3253c5f10ded084babd1cd58ce5d9722b1cc02be868b097fa2475268
```

## Funciones principales

- Criba automáticamente destellos sospechosos de duendes rojos desde vídeos de tormentas
- Analiza el vídeo completo; no se detiene en el primer candidato
- Escaneo de un solo vídeo y en lote de carpetas
- Modos de cribado preciso y de alta recuperación
- Exporta automáticamente fotogramas clave, clips, CSV, informe HTML y contact sheet
- Etiquetado manual: confirmar / sospechoso / descartar
- Exporta la lista de candidatos confirmados
- Ventana macOS nativa independiente, sin redirección al navegador

## Instalación

1. Descarga `red-sprite-filter-1.0.0.dmg`
2. Abre la DMG
3. Arrastra `红色精灵筛选器.app` (mostrado como "Red Sprite Filter") a Aplicaciones o cualquier carpeta
4. Clic derecho en la app y elige "Abrir"

## Requisitos

La versión actual requiere en tu Mac:

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

Instalación recomendada:

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## Nota de seguridad en macOS

Este build no está firmado ni notarizado. En el primer arranque macOS puede avisar de que no se puede verificar el desarrollador. Clic derecho en la app, elige "Abrir" y confirma en el diálogo. Una futura versión pública debería añadir firma y notarización con Apple Developer ID.

## Limitaciones conocidas

- Es una herramienta basada en reglas (color, forma, posición y características temporales), no un modelo de aprendizaje automático
- Los resultados siguen requiriendo revisión manual
- No todas las dependencias están incluidas; una máquina nueva puede necesitar instalarlas primero
- Los builds sin firmar muestran un aviso de seguridad en algunos dispositivos macOS al primer arranque

## A quién va dirigido

- Fotógrafos de tormentas
- Astrofotógrafos
- Aficionados a la observación de eventos luminosos transitorios (TLE)
- Cualquiera que quiera encontrar rápidamente clips candidatos de duendes rojos en gran cantidad de material

---

# Red Sprite Filter v1.0.0 (Deutsch)

Der erste herunterladbare macOS-Desktop-Release.

## Download

Lade das Release-Asset herunter:

```text
red-sprite-filter-1.0.0.dmg
```

SHA-256:

```text
54a3873b3253c5f10ded084babd1cd58ce5d9722b1cc02be868b097fa2475268
```

## Hauptfunktionen

- Automatisches Filtern verdächtiger Red-Sprite-Blitze aus Gewittervideos
- Scannt das gesamte Video; stoppt nicht beim ersten Kandidaten
- Scan einzelner Videos und von Ordnern im Stapel
- Präziser Filter und Filter mit hohem Recall
- Exportiert automatisch Kandidaten-Schlüsselframes, Clips, CSV, HTML-Bericht und Kontaktbild
- Manuelle Kennzeichnung: Bestätigen / Verdächtig / Ausschließen
- Export der bestätigten Kandidatenliste
- Native, eigenständige macOS-Fenster-App, kein Browser-Wechsel

## Installation

1. Lade `red-sprite-filter-1.0.0.dmg` herunter
2. Öffne die DMG
3. Ziehe `红色精灵筛选器.app` (angezeigt als "Red Sprite Filter") in die Programme oder einen beliebigen Ordner
4. Rechtsklick auf die App und „Öffnen" wählen

## Voraussetzungen

Die aktuelle Version benötigt auf deinem Mac:

- `python3`
- `ffmpeg`
- `ffprobe`
- `numpy`
- `Pillow`

Empfohlene Installation:

```bash
brew install ffmpeg
python3 -m pip install numpy Pillow
```

## macOS-Sicherheitshinweis

Dieser Build ist nicht signiert oder notariisiert. Beim ersten Start kann macOS warnen, dass der Entwickler nicht verifiziert werden kann. Rechtsklick auf die App, „Öffnen" wählen und im Dialog bestätigen. Ein künftiger öffentlicher Release sollte Signierung und Notarisierung mit Apple Developer ID ergänzen.

## Bekannte Einschränkungen

- Dies ist ein regelbasiertes Werkzeug (Farbe, Form, Position und zeitliche Merkmale), kein Machine-Learning-Modell
- Die Ergebnisse erfordern weiterhin eine manuelle Überprüfung
- Nicht alle Laufzeitabhängigkeiten sind gebündelt; eine frische Maschine muss sie ggf. zuerst installieren
- Nicht signierte Builds zeigen bei manchen macOS-Geräten beim ersten Start eine Sicherheitswarnung

## Für wen es ist

- Gewitterfotografen
- Astrofotografen
- Enthusiasten für die Beobachtung transluzenter Höhenereignisse (TLE)
- Alle, die aus großen Mengen Material schnell Kandidatenclips von Red Sprites finden wollen
