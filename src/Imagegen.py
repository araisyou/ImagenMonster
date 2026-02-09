# src/Imagegen.py
# -------------------------------------------------
# pip install google-genai pillow pydantic python-dotenv
#
# .env (プロジェクト直下など):
#   GEMINI_API_KEY=xxxx  (or GOOGLE_API_KEY=xxxx)
#
# Input:
#   Player/skill.json
#   Player/image/input/input.png
#
# Output:
#   Player/image/output/(6 images)
#   Player/output.json
# -------------------------------------------------

import json
import os
import random
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from dotenv import load_dotenv
from PIL import Image
from pydantic import BaseModel, Field

from google import genai
from google.genai import types


# -------------------------
# Structured output schemas
# -------------------------
class KeywordResult(BaseModel):
    description: str = Field(description="画像の特徴を短く要約（日本語）")
    keywords: List[str] = Field(description="重要度順のキーワード10個（重複なし推奨）")


class StatAddResult(BaseModel):
    add_hp: int = Field(description="HPへの加点（0〜30）")
    add_attack: int = Field(description="Attackへの加点（0〜30）")
    add_defense: int = Field(description="Defenseへの加点（0〜30）")
    add_agility: int = Field(description="Agilityへの加点（0〜30）")
    rationale: str = Field(description="なぜその配分にしたか（短く）")


class DesignSpec(BaseModel):
    name: str
    core_concept: str
    palette: List[str]
    motifs: List[str]
    silhouette: str
    common_details: List[str]
    larva_notes: str
    adult_notes: str
    final_notes: str
    negative: List[str]


# -------------------------
# Utils
# -------------------------
def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def require_file(path: Path, label: str) -> None:
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"{label} が見つかりません: {path}")


def strip_code_fences(s: str) -> str:
    if not s:
        return s
    s = s.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", s, flags=re.DOTALL)
    return m.group(1).strip() if m else s


# 参照画像として渡せる型：PIL or Part（生成画像はPartで受け取ってPartのまま回す）
RefImage = Union[Image.Image, types.Part]


def ref_to_part(img: RefImage, mime_type: str = "image/png") -> types.Part:
    """
    参照画像を必ず types.Part に変換する。
    - types.Part はそのまま返す（mime_type/dataが揃っている）
    - PIL.Image は PNG bytes にして Part 化
    """
    if isinstance(img, types.Part):
        return img

    if isinstance(img, Image.Image):
        buf = BytesIO()
        img.save(buf, "PNG")  # formatは位置引数で指定
        return types.Part.from_bytes(data=buf.getvalue(), mime_type=mime_type)

    raise TypeError(f"ref_to_part: 未対応の型です: {type(img)}")


def first_image_part_from_response(resp: Any) -> types.Part:
    """
    生成レスポンスから最初の画像パート(types.Part)を返す。
    ※ types.Image を自作しない（pydantic制約で落ちるため）
    """
    parts = getattr(resp, "parts", None) or []
    for part in parts:
        if getattr(part, "inline_data", None) is not None:
            return part

    try:
        for part in resp.candidates[0].content.parts:
            if getattr(part, "inline_data", None) is not None:
                return part
    except Exception:
        pass

    raise RuntimeError("画像がレスポンスに含まれていませんでした。モデル/プロンプトを見直してください。")


def save_part_image(part: types.Part, path: Path) -> None:
    inline = getattr(part, "inline_data", None)
    if inline is None or getattr(inline, "data", None) is None:
        raise RuntimeError("保存用bytesを取得できませんでした（part.inline_data.data がありません）。")
    path.write_bytes(inline.data)


# -------------------------
# Step 1) Image -> 10 keywords (Gemini)
# -------------------------
def analyze_image_keywords(client: genai.Client, image_pil: Image.Image, model: str) -> KeywordResult:
    prompt = """
あなたはゲームのアートディレクターです。
入力画像の特徴を要約し、重要度順にキーワードを必ず10個抽出してください。

条件:
- keywords は重要度順（上ほど重要）
- 各キーワードは短い名詞/形容詞フレーズ（1〜3語程度）
- できるだけ重複しない（同義語連発しない）
- 要素・質感・雰囲気・色・モチーフを優先
- 出力は指定スキーマのJSONのみ（余計な文章禁止）
"""
    resp = client.models.generate_content(
        model=model,
        contents=[ref_to_part(image_pil), prompt],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": KeywordResult.model_json_schema(),
        },
    )
    raw = strip_code_fences(resp.text or "")
    data = KeywordResult.model_validate_json(raw)

    # 重複除去＆10個に調整
    uniq: List[str] = []
    seen = set()
    for k in data.keywords:
        k = (k or "").strip()
        if k and k not in seen:
            uniq.append(k)
            seen.add(k)
    while len(uniq) < 10:
        uniq.append(f"特徴{len(uniq)+1}")
    data.keywords = uniq[:10]
    return data


# -------------------------
# Step 2) Stats (+30 allocation) by Gemini
# -------------------------
def validate_and_fix_add(add: StatAddResult) -> Tuple[StatAddResult, bool]:
    fixed = False
    vals = {
        "add_hp": int(add.add_hp),
        "add_attack": int(add.add_attack),
        "add_defense": int(add.add_defense),
        "add_agility": int(add.add_agility),
    }

    # clamp 0..30
    for k in list(vals.keys()):
        v0 = vals[k]
        v1 = max(0, min(30, v0))
        if v1 != v0:
            fixed = True
            vals[k] = v1

    total = sum(vals.values())
    if total != 30:
        fixed = True
        diff = 30 - total
        while diff != 0:
            if diff > 0:
                candidates = [k for k, v in vals.items() if v < 30] or list(vals.keys())
                k = max(candidates, key=lambda kk: vals[kk])
                vals[k] += 1
                diff -= 1
            else:
                candidates = [k for k, v in vals.items() if v > 0]
                if not candidates:
                    break
                k = max(candidates, key=lambda kk: vals[kk])
                vals[k] -= 1
                diff += 1

    out = StatAddResult(
        add_hp=vals["add_hp"],
        add_attack=vals["add_attack"],
        add_defense=vals["add_defense"],
        add_agility=vals["add_agility"],
        rationale=add.rationale,
    )
    return out, fixed


def allocate_stats_with_gemini(
    client: genai.Client,
    keywords: List[str],
    description: str,
    model: str,
) -> Tuple[Dict[str, int], Dict[str, int]]:
    """
    返り値:
      stats: {hp, attack, defense, agility}
      add_points: {hp, attack, defense, agility}  (合計30)
    """
    prompt = f"""
あなたはゲームデザイナーです。
次の「キーワード（重要度順）」と「画像要約」から、ステータス配分を決めてください。

前提:
- 基礎値は HP=20, Attack=0, Defense=0, Agility=0
- 追加で「合計30点」を4項目（HP/Attack/Defense/Agility）に振り分ける
- 各 add_* は 0〜30 の整数
- add_hp + add_attack + add_defense + add_agility = 30 を必ず満たす
- キーワードの上位ほど強く反映
- 出力は指定スキーマのJSONのみ（余計な文章禁止）

画像要約:
{description}

キーワード（重要度順10個）:
{keywords}
"""
    resp = client.models.generate_content(
        model=model,
        contents=[prompt],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": StatAddResult.model_json_schema(),
        },
    )
    raw = strip_code_fences(resp.text or "")
    add = StatAddResult.model_validate_json(raw)

    add2, _fixed = validate_and_fix_add(add)

    add_points = {
        "hp": add2.add_hp,
        "attack": add2.add_attack,
        "defense": add2.add_defense,
        "agility": add2.add_agility,
    }
    stats = {
        "hp": 20 + add_points["hp"],
        "attack": add_points["attack"],
        "defense": add_points["defense"],
        "agility": add_points["agility"],
    }
    return stats, add_points


# -------------------------
# Step 3) skill.json -> pick 3 skills (evo=1/2/3)
# -------------------------
def load_skills_dict(skill_path: Path) -> Dict[str, Dict[str, Any]]:
    data = json.loads(skill_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("skill.json は dict 形式（キー=スキルID）を想定しています。")

    out: Dict[str, Dict[str, Any]] = {}
    for sid, s in data.items():
        if not isinstance(s, dict):
            continue
        out[str(sid)] = {
            "id": str(sid),
            "name": str(s.get("name", sid)),
            "power": int(s.get("power", 0)),
            "evo": int(s.get("evo", 1)),
            "cost": int(s.get("cost", 0)),
            "description": str(s.get("description", "")),
        }
    if not out:
        raise ValueError("skill.json からスキルを読み取れませんでした。")
    return out


def score_skill(skill: Dict[str, Any], keywords: List[str]) -> float:
    blob = " ".join([skill.get("name", ""), skill.get("description", "")]).lower()
    score = 0.0
    for i, kw in enumerate(keywords):
        w = float(10 - i)
        if kw.lower() in blob:
            score += w
    score += float(skill.get("power", 0)) * 0.01
    return score


def pick_skills_by_evo(
    skills: Dict[str, Dict[str, Any]],
    keywords: List[str],
    rng: random.Random,
) -> Dict[int, Dict[str, Any]]:
    by_evo: Dict[int, List[Dict[str, Any]]] = {1: [], 2: [], 3: []}
    for s in skills.values():
        e = int(s.get("evo", 1))
        if e in by_evo:
            by_evo[e].append(s)

    chosen: Dict[int, Dict[str, Any]] = {}
    used = set()

    for evo in (1, 2, 3):
        candidates = by_evo.get(evo, [])
        if not candidates:
            candidates = list(skills.values())

        ranked = sorted(candidates, key=lambda s: score_skill(s, keywords), reverse=True)

        pick = None
        for s in ranked[:30]:
            if s["id"] not in used:
                pick = s
                break
        if pick is None:
            pick = rng.choice(ranked)

        chosen[evo] = pick
        used.add(pick["id"])

    return chosen


# -------------------------
# Step 4) design bible (Gemini)
# -------------------------
def build_design_spec(
    client: genai.Client,
    keywords: List[str],
    stats: Dict[str, int],
    stage_skills: Dict[int, Dict[str, Any]],
    model: str,
) -> DesignSpec:
    prompt = f"""
あなたはモンスターのデザイン設定資料を作るプロです。
次の情報をもとに、同一キャラクターが「幼生→成体→完全体」と進化していくための一貫したデザイン指針を作ってください。

重要キーワード（重要度順・10個）:
{keywords}

最終ステータス:
HP={stats["hp"]}, Attack={stats["attack"]}, Defense={stats["defense"]}, Agility={stats["agility"]}

進化段階ごとのスキル:
- 幼生(evo=1): {stage_skills[1]["name"]} / power={stage_skills[1]["power"]} / cost={stage_skills[1]["cost"]} / {stage_skills[1]["description"]}
- 成体(evo=2): {stage_skills[2]["name"]} / power={stage_skills[2]["power"]} / cost={stage_skills[2]["cost"]} / {stage_skills[2]["description"]}
- 完全体(evo=3): {stage_skills[3]["name"]} / power={stage_skills[3]["power"]} / cost={stage_skills[3]["cost"]} / {stage_skills[3]["description"]}

条件:
- 進化しても「同一個体」と分かる共通要素を明確に
- 幼生はシンプルで幼く、成体は器官/装備/構造が増え、完全体は象徴性と威圧感が完成
- 出力は指定スキーマのJSONのみ（余計な文章禁止）
"""
    resp = client.models.generate_content(
        model=model,
        contents=[prompt],
        config={
            "response_mime_type": "application/json",
            "response_json_schema": DesignSpec.model_json_schema(),
        },
    )
    raw = strip_code_fences(resp.text or "")
    return DesignSpec.model_validate_json(raw)


# -------------------------
# Step 5) Generate images
# -------------------------
def make_stage_prompt(
    stage_label_ja: str,
    stage_keywords: List[str],
    spec: DesignSpec,
    view: str,
    stage_skill: Dict[str, Any],
    use_reference_hint: str,
) -> str:
    view_ja = "正面（全身）" if view == "front" else "背面（後ろ姿・全身）"
    stage_notes = {"幼生": spec.larva_notes, "成体": spec.adult_notes, "完全体": spec.final_notes}.get(stage_label_ja, "")
    kw_line = "、".join(stage_keywords)
    neg = " / ".join(spec.negative + ["文字", "ロゴ", "透かし", "UI", "署名"])

    return f"""
{use_reference_hint}

あなたはゲームのモンスター原画家です。
「デザインバイブル」を守りつつ、進化段階「{stage_label_ja}」のキャラクター画像を1枚生成してください。

【デザインバイブル（共通設定）】
- 名前: {spec.name}
- コアコンセプト: {spec.core_concept}
- 色パレット: {", ".join(spec.palette)}
- モチーフ: {", ".join(spec.motifs)}
- シルエット: {spec.silhouette}
- 共通の識別要素: {", ".join(spec.common_details)}

【この段階の重要キーワード（上位 {len(stage_keywords)} 個）】
{kw_line}

【この段階のスキル（必ず“それっぽさ”を形状/器官/武装で表現）】
- {stage_skill["name"]} (power={stage_skill["power"]}, cost={stage_skill["cost"]})
- {stage_skill["description"]}

【進化段階メモ】
{stage_notes}

【構図】
- {view_ja}
- 1体のみ、全身が画面内に収まる
- 中央配置、背景は単色〜簡素
- アニメ調/ゲームコンセプトアート風

【制約（絶対）】
- 画像内に文字を入れない
- ロゴ/透かし/フレーム/UIを入れない
- 複数体を出さない
- NG: {neg}

出力は画像のみ。
""".strip()


def generate_one_image(
    client: genai.Client,
    model: str,
    ref_images: List[RefImage],
    prompt: str,
    aspect_ratio: str,
) -> types.Part:
    ref_parts = [ref_to_part(img) for img in ref_images]

    resp = client.models.generate_content(
        model=model,
        contents=[*ref_parts, prompt],
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        ),
    )
    return first_image_part_from_response(resp)


# -------------------------
# Public API: imagegen()
# -------------------------
def imagegen(
    seed: int = 42,
    analysis_model: str = "gemini-2.5-flash",
    image_model: str = "gemini-2.5-flash-image",
    aspect_ratio: str = "1:1",
) -> None:
    
    print("Imagegen started...")
#     """
#     この関数を呼ぶと生成が始まる。
#     - 入力:  Player/skill.json, Player/image/input/input.png
#     - 出力:  Player/image/output/*png (6枚), Player/output.json
#     """
    load_dotenv()
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        raise RuntimeError("APIキーが見つかりません。.env に GEMINI_API_KEY か GOOGLE_API_KEY を設定してください。")

    rng = random.Random(seed)

    # src と Player が同階層
    src_dir = Path(__file__).resolve().parent          # .../src
    player_dir = src_dir.parent / "Player"            # .../Player

    skill_path = player_dir / "skill.json"
    image_path = player_dir / "image" / "input" / "input.png"
    out_img_dir = player_dir / "image" / "output"
    out_json_path = player_dir / "output.json"

    ensure_dir(out_img_dir)

    require_file(skill_path, "Player/skill.json")
    require_file(image_path, "Player/image/input/input.png")

    client = genai.Client()

    # Load input image (PIL)
    base_pil = Image.open(image_path).convert("RGB")

    # Load skills
    skills = load_skills_dict(skill_path)

    # 1) keywords
    kw_res = analyze_image_keywords(client, base_pil, analysis_model)
    keywords = kw_res.keywords

    # 2) stats (+30) by Gemini
    stats, _add_points = allocate_stats_with_gemini(client, keywords, kw_res.description, analysis_model)

    # 3) skills (evo=1/2/3)
    stage_skills = pick_skills_by_evo(skills, keywords, rng)

    # 4) design spec
    spec = build_design_spec(client, keywords, stats, stage_skills, analysis_model)

    # 5) images (6枚)
    stages = [
        ("幼生", "larva", 1, 3),
        ("成体", "adult", 2, 6),
        ("完全体", "final", 3, 10),
    ]

    prev_front_part: types.Part | None = None

    for stage_ja, stage_en, evo, n_kw in stages:
        stage_kws = keywords[:n_kw]
        skill = stage_skills[evo]

        # 進化連続性：前段の正面も参照
        front_refs: List[RefImage] = [base_pil] if prev_front_part is None else [base_pil, prev_front_part]

        front_prompt = make_stage_prompt(
            stage_label_ja=stage_ja,
            stage_keywords=stage_kws,
            spec=spec,
            view="front",
            stage_skill=skill,
            use_reference_hint="【参照画像あり】参照の雰囲気/質感/モチーフを抽象化して取り込み、オリジナルキャラとして再構成すること。",
        )
        front_part = generate_one_image(client, image_model, front_refs, front_prompt, aspect_ratio)
        front_path = out_img_dir / f"{stage_en}_front.png"
        save_part_image(front_part, front_path)

        back_prompt = make_stage_prompt(
            stage_label_ja=stage_ja,
            stage_keywords=stage_kws,
            spec=spec,
            view="back",
            stage_skill=skill,
            use_reference_hint="【参照画像あり】正面画像と同一個体として、背面（後ろ姿）を生成。色/体型/装飾の一致を最優先。",
        )
        back_part = generate_one_image(client, image_model, [front_part], back_prompt, aspect_ratio)
        back_path = out_img_dir / f"{stage_en}_back.png"
        save_part_image(back_part, back_path)

        prev_front_part = front_part

    # ✅ 指定の形で output.json を出力
    out_data = {
        "hp": int(stats["hp"]),
        "attack": int(stats["attack"]),
        "defense": int(stats["defense"]),
        "agility": int(stats["agility"]),
        "skill": [stage_skills[1]["name"], stage_skills[2]["name"], stage_skills[3]["name"]],
    }
    out_json_path.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print("OK")
    print(f"- images: {out_img_dir}")
    print(f"- json:   {out_json_path}")


# 直接実行もできるようにしておく（不要なら消してOK）
if __name__ == "__main__":
    try:
        imagegen()
    except Exception as e:
        print(str(e), file=sys.stderr)
        raise
