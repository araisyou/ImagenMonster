import os
import json
import mimetypes
import pygame


def image_to_text(image_path: str, api_key: str | None = None) -> None:
    """画像パスを受け取り、メタ情報と Gemini 要約を JSON に書き込む。

    既に対応する JSON が assets/imagetotext に存在する場合は上書きしないで終了する。
    """
    if not image_path:
        raise ValueError("image_path が空です")
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"画像が見つかりません: {image_path}")

    json_path = _text_json_path(image_path)
    if os.path.isfile(json_path):
        return

    try:
        surface = pygame.image.load(image_path)
    except pygame.error as exc:
        raise RuntimeError(f"画像読み込みに失敗しました: {exc}") from exc

    width, height = surface.get_size()
    ext = os.path.splitext(image_path)[1].lower() or "(不明)"

    avg_color = pygame.transform.average_color(surface)
    avg_text = f"平均色 (概算): R{avg_color[0]} G{avg_color[1]} B{avg_color[2]}"

    lines = [
        f"ファイル: {os.path.basename(image_path)}",
        f"拡張子: {ext}",
        f"画像サイズ: {width} x {height}",
        avg_text,
    ]

    # Gemini API による簡易説明
    try:
        import google.generativeai as genai
    except ImportError:
        lines.append("Gemini: ライブラリ未導入 (google-generativeai)")
        _write_text_json(json_path, lines)
        return lines

    key = api_key or os.getenv("GEMINI_API_KEY")
    if not key:
        lines.append("Gemini: APIキーが設定されていません (環境変数 GEMINI_API_KEY)")
        _write_text_json(json_path, lines)
        return lines

    genai.configure(api_key=key)
    mime = _guess_mime(image_path)
    with open(image_path, "rb") as f:
        data = f.read()

    prompt = "画像の内容を日本語で50文字以内の箇条書きで3点、簡潔に教えてください。"
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content([prompt, {"mime_type": mime, "data": data}])
        text = (resp.text or "").strip()
        if text:
            lines.append(f"Gemini要約: {text}")
        else:
            lines.append("Gemini: 応答が空でした")
    except Exception as exc:  # noqa: BLE001
        lines.append(f"Geminiエラー: {exc}")

    _write_text_json(json_path, lines)


def read_text_from_json(image_path: str) -> list[str]:
    json_path = _text_json_path(image_path)
    if not os.path.isfile(json_path):
        return []
    return _read_text_json(json_path)


def _guess_mime(path: str) -> str:
    mime, _ = mimetypes.guess_type(path)
    return mime or "image/png"


def _text_json_path(image_path: str) -> str:
    base = os.path.splitext(os.path.basename(image_path))[0]
    text_dir = os.path.join("assets", "imagetotext")
    os.makedirs(text_dir, exist_ok=True)
    return os.path.join(text_dir, base + ".json")


def _read_text_json(json_path: str) -> list[str]:
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return [str(x) for x in data]
    except (OSError, json.JSONDecodeError):
        return []
    return []


def _write_text_json(json_path: str, lines: list[str]) -> None:
    try:
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(lines, f, ensure_ascii=False, indent=2)
    except OSError:
        pass
