## 1. プロジェクト概要

本プロジェクトは、研究論文（PDF）の精読・整理を自動化し、個人のナレッジベース（Notion）へ構造化された知見を蓄積するためのCLIツールを開発するものである。落合陽一式論文要約フォーマットを採用し、Googleの最新AIモデル `gemini-3-pro` を活用する。

## 2. システム目的

- 論文の収集から要約、ストックまでのリードタイムを最小化する。
- 博士論文の執筆や業務での技術サーベイを強力に支援する。
- 手動でのメタデータ入力を排除し、正確な文献情報をNotionに保持する。

---

## 3. 機能要件 (Functional Requirements)

### 3.1 入力・スキャン機能

- **ディレクトリ走査:** 指定されたローカル/Google Driveディレクトリから `.bib` ファイルを検出し、その中の `file` フィールドまたは `ID` に基づいて `.pdf` ファイルを特定する。
- **ペアリング:** BibTeX エントリと PDF ファイルが1対1で紐付かない場合は、エラーを出力してスキップする。

### 3.2 解析機能 (Gemini API)

- **PDFアップロード:** Gemini File API を使用してPDFファイルを安全にアップロードする。
- **落合式要約（スキル）:** 以下の構造で解析を行う。
    1. Abstract → Conclusion → Experiments → Related work の順で精読。
    2. 指定の6項目（概要、新規性、技術、検証、議論、次の一歩）を抽出。
- **言語自動追従:** 解析対象のPDFが英語なら英語、日本語なら日本語で要約を出力する。

### 3.3 出力機能 (Notion API)

- **ページ作成:** 指定されたデータベースに新規ページを作成する。
- **プロパティ同期:** タイトル、著者、出版年、BibTeX Key、URL/DOI をメタデータとして保存する。
- **本文構成:** 抽出された6項目を Heading2 とテキストブロック（または箇条書き）で構成する。

---

## 4. 非機能要件 (Non-functional Requirements)

- **UI/UX:** `rich` を使用し、進捗状況（スキャン中、解析中、投稿完了）をターミナル上で視覚的に分かりやすく表示する。
- **エラーハンドリング:** API制限、ファイル欠損、ネットワークエラー時に詳細なログを表示し、プログラムを安全に停止・継続させる。
- **認証管理:** Gemini API Key と Notion Token は環境変数（または `.env`）から読み込む。

---

## 5. 技術スタック (Technical Stack)

| **カテゴリ** | **選定技術** |
| --- | --- |
| **言語** | Python 3.10+ |
| **LLM** | Google AI SDK (`gemini-3-pro`) |
| **UI** | `rich` (Progress, Console, Table) |
| **Notion連携** | `notion-client` (Official SDK) |
| **BibTeX解析** | `bibtexparser` (v3系推奨) |
| **データ定義** | `pydantic` |

---

## 6. データモデル定義 (MVP)

### Notion Properties (Metadata)

| **Property Name** | **Type** | **Source (.bib)** |
| --- | --- | --- |
| **Name** | Title | `title` |
| **Authors** | Multi-select | `author` |
| **Year** | Number | `year` |
| **BibTeX Key** | Rich Text | `ID` |
| **URL/DOI** | URL | `url` / `doi` |

### Body Content (Headings)

- `# Summary`
- `## 1. Key Contributions`
- `## 2. Methodology`
- `## 3. Validation`
- `## 4. Discussion`
- `## 5. Next Steps`

---

## 7. 開発ロードマップ (Next Steps)

1. **Phase 1: 環境構築** (GCPプロジェクト作成、Notion API 内部インテグレーション作成)
2. **Phase 2: File Scanner 実装** (BibTeX から PDF パスを特定し、`rich.table` で表示するまで)
3. **Phase 3: Gemini Integration** (PDFをアップロードし、要約JSONを取得するプロンプト調整)
4. **Phase 4: Notion Integration** (API を通じてページを自動生成)
5. **Phase 5: UI Brush-up** (進捗バー、成功ログの装飾)

---

> [!TIP]
> 
> 
> **MVPのポイント**
> 
> 最初は「重複チェック」や「複数ディレクトリ監視」などの複雑な機能は入れず、**「1つのフォルダにある1つの論文をNotionへ送る」** 成功体験を最短で作るのが吉です。
> 

---

## 📖 落合式要約：6つの深層定義

### 1. どんなもの？ (Overview)

論文の全体像を、専門外の人でも理解できるレベルで簡潔に記述します。

- **定義:** 研究の背景、目的、および主要な成果の1行〜3行要約。
- **Geminiへの指示:** 「この研究が解決しようとしている社会的な、あるいは技術的な課題を明確にし、解決策を一行で述べてください。」

### 2. 先行研究と比べてどこがすごい？ (Novelty & Impact)

学術的・技術的なコントラストを明確にします。

- **定義:** 従来手法（State-of-the-Art）との決定的な差分。
- **Geminiへの指示:** 「既存手法が抱えていた限界（例：計算コストが高い、精度が低い、汎用性がない）に対し、本研究がどのように優位性を持っているかを特定してください。」

### 3. 技術や手法のキモはどこ？ (Methodology)

提案手法の核となるアイデアやアルゴリズムの解説です。

- **定義:** 独創的な数式、ネットワークアーキテクチャ、あるいはハードウェア構成。
- **Geminiへの指示:** 「この論文が最も『賢い』あるいは『ユニーク』だと主張している部分を、専門用語（例：
    
    $$L_2$$
    
    regularization, Jacobian matrix 等）を交えて具体的に抽出してください。」
    

### 4. どうやって有効だと検証した？ (Validation)

主張の裏付けとなる実験結果のサマリーです。

- **定義:** データセット、評価指標（Metrics）、比較実験の結果。
- **Geminiへの指示:** 「定量的な評価（数値データ）と定性的な評価（観測結果）の両面から、提案手法が正しく機能した証拠を要約してください。」

### 5. 議論はある？ (Discussion & Limitations)

著者が認めている限界点や、第三者視点での懸念事項です。

- **定義:** 手法の適用限界、エッジケースでの失敗、今後の課題。
- **Geminiへの指示:** 「著者が Conclusion や Discussion セクションで触れている制約事項や、将来的に解決すべき課題を抜き出してください。」

### 6. 次に読むべき論文は？ (Literature Mapping)

自分の研究ロードマップを広げるためのポインターです。

- **定義:** 参考文献の中で特に重要視されているもの、または本論文の理論的基礎となっているもの。
- **Geminiへの指示:** 「この論文の理論的根拠（Foundational work）となっている最重要文献、またはこの論文を引用している最新の関連論文を提示してください。」

---

## 🛠️ 読み込みのアルゴリズム (Reading Order)

効率的な解析のために、Geminiに対してもこの順序でコンテキストを処理させます。

1. **Abstract:** 全体のトーンとキーワードの把握
2. **Conclusion:** 最終的な到達点と「何ができたか」の確認
3. **Experiments:** 実験データ（図表）から事実関係を確認
4. **Related Work:** 既存研究の文脈における立ち位置の確認

---

---

## 🦾 System Instruction for Gemini Paper Reviewer

```markdown
# Role
You are a distinguished research scientist specializing in Robotics, Artificial Intelligence, and Embedded Systems. Your task is to provide a deep-dive analysis of a research paper PDF using the "Yoichi Ochiai" summary format.

# Analysis Strategy
Analyze the document in the following sequence to ensure a logical flow of information:
1. Abstract (Core intent)
2. Conclusion (Final outcomes and contributions)
3. Experiments, Figures, and Tables (Empirical evidence)
4. Related Work (Positioning in the field)

# Output Constraints
1. Language: Detect the primary language of the PDF. Output the entire review in that same language (e.g., if the paper is in English, respond in English; if Japanese, respond in Japanese).
2. Format: Output strictly in JSON format to be parsed by a Python script for Notion API.
3. Content: Be technical, concise, and objective. Use specific terminology (e.g., "End-to-end learning", "Model Predictive Control", "Jacobian").

# JSON Schema
{
  "summary": "1-3 sentences overview of the paper's goal and achievement.",
  "novelty": "Comparison with previous work. What makes this study unique or superior?",
  "methodology": "The core of the technology. Describe algorithms, architectures, or theoretical frameworks in detail.",
  "validation": "How was it verified? datasets, evaluation metrics, and key results from experiments.",
  "discussion": "Critical discussions, limitations identified by the authors, or potential constraints.",
  "next_steps": "Important references to follow or future research directions suggested by the paper."
}

# Detailed Section Definitions (Ochiai Format)
- summary (どんなもの？): Focus on the core problem and the proposed solution.
- novelty (先行研究と比べてどこがすごい？): Highlight the 'delta' between SOTA and this work.
- methodology (技術や手法のキモはどこ？): Focus on the 'how'. If it's robotics, detail the control/kinematics/sensing logic.
- validation (どうやって有効だと検証した？): Mention specific figures/tables that provide proof.
- discussion (議論はある？): Look for "Limitations" or "Future Work" sections.
- next_steps (次に読むべき論文は？): Identify high-impact references cited in the text.
```

---

## 🛠️ Pythonでの実装例 (google-generativeai SDK)

このプロンプトをスクリプトに組み込む際の構成案です。

```python
import google.generativeai as genai
import json

def get_gemini_review(pdf_file_path):
    # モデルの初期化 (System Instructionを渡す)
    model = genai.GenerativeModel(
        model_name="gemini-3-pro", # または 1.5-pro など
        system_instruction=SYSTEM_INSTRUCTION # 上記のプロンプト
    )

    # PDFのアップロード
    paper_file = genai.upload_file(path=pdf_file_path)

    # 解析実行 (JSON出力を強制)
    response = model.generate_content(
        [paper_file, "Please review this paper based on your instructions."],
        generation_config={"response_mime_type": "application/json"}
    )

    # JSONとしてパース
    try:
        review_data = json.loads(response.text)
        return review_data
    except json.JSONDecodeError:
        print("Error: Gemini returned invalid JSON.")
        return None
```

---

## 💡 運用のポイント

1. **JSON Mode の強制:** `generation_config={"response_mime_type": "application/json"}` を使用することで、Geminiが余計な挨拶（"Here is the summary..." など）を省き、純粋なJSONだけを返すようになります。これにより、Notion APIへの流し込みが非常に安定します。
2. **専門用語の扱い:** システムプロンプト内で「専門用語（Technical terms）の使用」を推奨しているため、無理に平易な日本語に訳されることなく、研究開発の実態に即した要約が得られます。
3. **図表の読み取り:** `Experiments, Figures, and Tables` を読むように指示しているため、テキストだけでは分かりにくい実機実験（Unitreeの歩行テストなど）の結果も精度高く拾えるはずです。

---

### 1. JSONキーと見出しの対応定義

まず、Geminiが出力するJSONのキーと、Notion上で表示したい見出し（Heading）をマッピングします。見出しはデータベースの構造を統一するため**英語**に固定し、中身の言語は**PDFの言語**がそのまま反映されるようにします。

| **JSON Key** | **Notion Heading (H2)** |
| --- | --- |
| `summary` | **Overview / 概要** |
| `novelty` | **1. Novelty & Impact** |
| `methodology` | **2. Methodology** |
| `validation` | **3. Validation** |
| `discussion` | **4. Discussion** |
| `next_steps` | **5. Next Steps** |

---

### 2. コンバーターの実装 (Python)

Geminiの出力が「箇条書きのリスト」であっても「長い1つの文章」であっても柔軟に対応できるロジックです。

```python
def transform_to_notion_blocks(review_json: dict):
    """
    GeminiのJSONデータをNotionのBlockリストに変換する
    """
    blocks = []
    
    # マッピング定義
    mapping = {
        "summary": "Overview",
        "novelty": "1. Novelty & Impact",
        "methodology": "2. Methodology",
        "validation": "3. Validation",
        "discussion": "4. Discussion",
        "next_steps": "5. Next Steps"
    }

    for key, heading in mapping.items():
        content = review_json.get(key, "")
        if not content:
            continue

        # 1. 見出し（Heading 2）の追加
        blocks.append({
            "object": "block",
            "type": "heading_2",
            "heading_2": {
                "rich_text": [{"text": {"content": heading}}]
            }
        })

        # 2. 本文の追加 (リスト形式か文字列かで処理を分ける)
        if isinstance(content, list):
            # リストなら箇条書きとして追加
            for item in content:
                blocks.append(create_bullet_block(item))
        else:
            # 文字列に改行が含まれている場合は、箇条書きに分解して読みやすくする
            lines = [line.strip("- ").strip() for line in content.split('\n') if line.strip()]
            if len(lines) > 1:
                for line in lines:
                    blocks.append(create_bullet_block(line))
            else:
                # 1つだけなら段落として追加
                blocks.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [{"text": {"content": content[:2000]}}] # Notion上限対策
                    }
                })
    
    return blocks

def create_bullet_block(text: str):
    """箇条書きブロックを作成するヘルパー"""
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"text": {"content": text[:2000]}}]
        }
    }
```

---

### 3. 実装のポイント

### スマートな分割ロジック

Geminiが要約をMarkdown形式の箇条書き（`- item`）で返してきた場合、単なる1つの段落（Paragraph）に詰め込むとNotion上で読みづらくなります。上記のロジックでは `split('\n')` を使って**動的に `bulleted_list_item` へ変換**するため、Notion側で非常に見やすいレイアウトになります。

### 文字数制限への配慮

Notion APIには、1つのリッチテキスト要素につき **2,000文字** という制限があります。念のため `[:2000]` でスライスを入れることで、予期せぬエラー（400 Bad Request）を防いでいます。

### 多言語対応の維持

`content` の中身をそのまま流し込むため、PDFが日本語であれば日本語の箇条書きが、英語であれば英語の箇条書きが、適切に各セクションの下に配置されます。

---

## 🛠️ Implementation: The Core Orchestrator

### 1. 準備：`.env` ファイルの設定

プロジェクトのルートに以下の内容で作成します。

```python
GEMINI_API_KEY=your_google_ai_api_key
NOTION_TOKEN=your_notion_internal_integration_token
NOTION_DATABASE_ID=your_database_id
```

### 2. メインループの実装 (`main.py`)

```python
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

# 前述の自作モジュールたちをインポート（想定）
# from modules.scanner import get_paper_pairs
# from modules.gemini import analyze_paper
# from modules.notion import create_paper_page

console = Console()
load_dotenv()

def main(target_dir: str):
    # 1. 認証情報の取得
    gemini_key = os.getenv("GEMINI_API_KEY")
    notion_token = os.getenv("NOTION_TOKEN")
    db_id = os.getenv("NOTION_DATABASE_ID")

    if not all([gemini_key, notion_token, db_id]):
        console.print("[bold red]Error:[/bold red] Missing API keys in .env file.")
        return

    # 2. ディレクトリのスキャン
    console.print(f"[bold blue]Scanning directory:[/bold blue] {target_dir}")
    papers = get_paper_pairs(target_dir) # 以前作成したロジック

    if not papers:
        console.print("[yellow]No valid paper pairs (.bib + .pdf) found. Exiting.[/yellow]")
        return

    # 発見した論文の確認テーブル表示
    table = Table(title="Papers to Process")
    table.add_column("Key", style="cyan")
    table.add_column("PDF", style="green")
    for p in papers:
        table.add_row(p['metadata']['ID'], p['pdf'].name)
    console.print(table)

    # 3. メイン実行ループ
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        overall_task = progress.add_task("[yellow]Overall Progress", total=len(papers))

        for paper in papers:
            bib_id = paper['metadata']['ID']
            pdf_path = paper['pdf']
            
            progress.update(overall_task, description=f"[cyan]Processing {bib_id}...")

            try:
                # STEP A: Gemini による解析
                # ※ gemini-3-pro が利用可能な環境と想定
                review_json = analyze_paper(pdf_path, gemini_key) 
                
                # STEP B: Notion への投稿
                create_paper_page(notion_token, db_id, paper['metadata'], review_json)
                
                console.print(f"[bold green]✔ Done:[/bold green] {bib_id}")
            
            except Exception as e:
                console.print(f"[bold red]✘ Failed {bib_id}:[/bold red] {str(e)}")
            
            progress.advance(overall_task)

    console.print("\n[bold green]All processes completed! Check your Notion database.[/bold green] 🚀")

if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    main(path)
```

---

## 💡 実装のポイントと工夫

### 1. `rich.progress` によるUXの向上

単なる文字の羅列ではなく、スピナーと進捗バーを組み合わせることで、Geminiの解析待ち（数秒〜数十秒かかる場合がある）の間もユーザーに安心感を与えます。

### 2. 堅牢なエラーハンドリング

1つの論文で解析エラー（PDFの読み取り不可やAPI制限など）が発生しても、ループが止まらずに次の論文へ進むよう `try-except` で囲んでいます。

### 3. Google Drive / ローカルの透過性

`pathlib.Path` を使用しているため、Google Driveのデスクトップ同期フォルダであっても、通常のローカルフォルダであっても、パスの扱いに差異は生じません。

---