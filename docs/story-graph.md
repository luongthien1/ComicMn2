# Đồ thị tri thức truyện — tra cứu trong chat

Chat trong ChapterEditor giờ tra cứu được nội dung truyện: hỏi "nhân vật X là ai",
"ở chương N có gì", "cảnh nào mô tả …" và nhận câu trả lời kèm số chương để kiểm chứng.

Kiến trúc và các con số ở đây đến từ 14 vòng thử nghiệm trong `research/`.
Đọc `research/README.md` nếu muốn biết vì sao chọn cách này thay vì cách khác.

## Chạy

### 1. Neo4j

```bash
cd comic-graphrag-mcp
docker compose up -d
```

Kiểm tra: http://localhost:7474 (`neo4j` / `change-me`).

### 2. Cấu hình backend

Trong `backend/.env`:

```
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=change-me

AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://192.168.1.11:11435
OLLAMA_TOKEN=<token của reverse proxy>
OLLAMA_MODEL=qwen3.5:latest
EMBED_MODEL=bge-m3
```

**Bỏ trống `NEO4J_URI` thì chat vẫn chạy**, chỉ mất phần tra cứu truyện.
Module chịu lỗi ở mọi tầng: mất Neo4j → không tra cứu; mất embedding → vẫn còn
sự thật từ graph.

### 3. Nạp truyện vào graph

**Từ giao diện:** mở một chương bất kỳ → tab Q&A → thanh trạng thái trên cùng
hiển thị *"Chưa nạp truyện"* kèm nút **Nạp truyện**. Bấm và chờ — tiến độ hiện
theo từng chương, vài phút cho truyện dài.

Nút này lấy chương từ database (`chapters.content`), bỏ HTML, cắt hai tầng chunk
rồi embedding và ghi vào Neo4j. Nạp lại thì ghi đè (`MERGE`), không nhân bản.

Thực thể được quét **cơ học** bằng tần suất tên riêng, không nhờ LLM — đếm chuỗi
là việc máy làm chính xác 100% (`research/notes/05`).

**Nạp đầy đủ hơn (Scene, Entity khái niệm, Fact có nghĩa)** hiện vẫn cần script
trong `research/scripts/`:

```bash
PY=E:/Code/Comic/comic-graphrag-mcp/.venv/Scripts/python.exe
cd research

$PY scripts/extract_docx.py          # .docx -> data/chapters.json
$PY scripts/exp03_vector.py          # tạo embedding (cache lại)
$PY scripts/exp06_neo4j_graph.py     # dựng graph: Chapter, Chunk, Entity, Fact
$PY scripts/exp11_richer_graph.py    # thêm Entity khái niệm + quan hệ có nghĩa
$PY scripts/exp12_scene_graph.py     # trích cảnh -> Scene, Mood, Weather, Location
$PY scripts/fine_chunks.py           # tầng chunk nhỏ cho câu hỏi chi tiết
```

Kiểm tra đã nạp xong:

```bash
curl "http://localhost:8010/api/ai/story-graph/stats?comic_id=1"
```

## API

### `POST /api/ai/chat`

```jsonc
{
  "messages": [{"role": "user", "content": "Ở chương 12, Hari đang làm gì?"}],
  "comic_id": 1,        // bỏ trống -> tắt tra cứu
  "chapter": 12         // chương đang mở -> giới hạn phạm vi
}
```

Trả về thêm `retrieval` để UI hiển thị nguồn:

```jsonc
{
  "answer": "Tại chương 12, Hari KHÔNG xuất hiện...",
  "provider": "ollama",
  "retrieval": {
    "used": true,
    "route": "chapter",      // global | chapter | scene
    "chapters": [12],
    "n_chunks": 2,
    "n_scenes": 0,
    "had_facts": true
  }
}
```

### `POST /api/ai/story-graph/check-conflict`

Kiểm một đoạn nháp có mâu thuẫn với truyện đã viết không — khác `/chat` ở chỗ
không trả lời câu hỏi mà **tìm mâu thuẫn**.

```jsonc
{
  "draft": "Hari chạy đến bên cạnh tôi, đuôi vẫy mừng rỡ.",
  "at_chapter": 20,
  "comic_id": 1
}
```

```jsonc
{
  "available": true,
  "conflict": true,
  "reason": "Nhân vật Hari chưa xuất hiện trong chương 20 (đồ thị cho biết Hari
             lần đầu xuất hiện ở chương 21)...",
  "evidence_chapters": [21],
  "chapters_checked": [16, 21, 22],
  "had_facts": true
}
```

Đo trên 10 ca thử, 6 lần chạy (`research/notes/16`):

```
trung bình     9.2/10
bắt mâu thuẫn  6/6 ở MỌI lần chạy
báo động giả   0-1 mỗi lần
```

Phần bắt mâu thuẫn ổn định hoàn toàn; dao động nằm ở báo động giả. Với công cụ
viết truyện đó là đúng hướng — không bỏ sót, chỉ đôi khi quá nhạy.

### `POST /api/ai/story-graph/review`

Nhận xét chất lượng truyện — khác `/chat` (trả lời câu hỏi) và `/check-conflict`
(tìm mâu thuẫn).

```jsonc
{
  "comic_id": 1,
  "chapter": 16,            // bỏ trống -> đánh giá toàn truyện
  "aspects": ["pacing"]     // bỏ trống -> mọi khía cạnh
}
```

Năm khía cạnh: `pacing` (nhịp), `character` (nhân vật), `worldbuilding`,
`prose` (văn phong), `structure` (cấu trúc). Lấy danh sách qua
`GET /api/ai/story-graph/review-aspects`.

```jsonc
{
  "available": true,
  "scope": "chapter",
  "summary": "…",
  "strengths": [{"point": "…", "evidence": "[ch.16] …"}],
  "issues": [{"point": "…", "evidence": "[ch.16] …", "suggestion": "…"}],
  "score": {"pacing": 4, "character": 3, …}
}
```

Hai nguyên tắc thiết kế:

1. **Dẫn chứng bắt buộc.** Mỗi nhận xét phải kèm `[ch.N]`. Nhận xét chung chung
   ("truyện hay") vô dụng với người viết, nên prompt yêu cầu bỏ đi.
2. **Không bịa số liệu.** Số chương, độ dài, nhân vật xuất hiện bao nhiêu chương —
   lấy từ graph bằng Cypher rồi đưa vào prompt như dữ kiện, không để LLM đoán
   (`research/notes/05`: đếm chuỗi là việc máy làm chính xác 100%).

Script còn tự tính: chương dài/ngắn bất thường (lệch >1.6× hoặc <0.5× trung bình)
và nhân vật xuất hiện vài chương rồi biến mất — hai thứ biên tập viên hay để ý.

### `GET /api/ai/story-graph/trace/{trace_id}`

Toàn bộ quá trình suy luận của một lần chat: định tuyến và **lý do**, từng truy vấn
Cypher kèm tham số và kết quả, prompt cuối, câu trả lời.

`POST /api/ai/chat` trả về `retrieval.trace_id` để tra.

```jsonc
{
  "id": "a1b2c3…",
  "question": "Ở chương 12, Hari đang làm gì?",
  "route": "chapter",
  "total_ms": 2840,
  "steps": [
    {"kind": "decision", "label": "định tuyến",
     "note": "Câu hỏi nêu rõ 'chương 12' → giới hạn truy hồi trong chương đó…"},
    {"kind": "cypher", "label": "tìm thực thể được nhắc trong câu hỏi",
     "cypher": "MATCH (e:Entity {comic_id: $cid})
WHERE …",
     "params": {"cid": 1, "q": "Ở chương 12…"},
     "n_results": 1, "sample": ["Hari"], "ms": 12.4}
  ],
  "prompt": "…",
  "answer": "…"
}
```

Vector 1024 chiều trong `params` được thay bằng `<vector 1024 chiều>` cho dễ đọc.

Trace lưu **trong bộ nhớ**, giữ 50 lần gần nhất, mất khi backend khởi động lại —
đây là công cụ chẩn đoán, không phải dữ liệu nghiệp vụ.
`GET /api/ai/story-graph/traces?comic_id=1` liệt kê các lần gần đây.

**Vì sao cần:** câu trả lời có thể đúng vì lý do sai. `research/notes/03` ghi lại ca
hệ thống trả lời "không tìm thấy" — đúng, nhưng vì **mù**, không phải vì hiểu.
Không nhìn được quá trình thì không phân biệt được hai thứ đó.

### `GET /api/ai/story-graph/stats?comic_id=1`

```json
{"available": true, "chapters": 64, "chunks": 942,
 "entities": 303, "facts": 79, "scenes": 264}
```

## Cách nó định tuyến

Không trộn mọi nguồn — đó là sai lầm đã đo được (`research/notes/04`: hợp nhất RRF
kéo recall 0.76 xuống 0.56). Thay vào đó chọn nguồn theo dạng câu hỏi:

| câu hỏi | route | nguồn |
|---|---|---|
| "cảnh nào mô tả…", "không khí…" | `scene` | Scene graph + vector + chunk nhỏ |
| "ở chương N…", hoặc đang mở chương N | `chapter` | vector giới hạn trong chương đó |
| còn lại | `global` | vector toàn truyện + graph facts |

Chunk nhỏ (~96 ký tự) chỉ dùng cho câu **tìm chi tiết** ("cảnh nào có mùi máu").
Câu **định nghĩa/gộp** ("X là gì", "gồm những gì") thì không — chunk vụn làm loãng
ngữ cảnh và hạ điểm (`research/notes/14` vòng 9).

## Kết quả đo (bộ 100 câu)

| loại | n | đúng |
|---|---|---|
| temporal | 20 | **17/17** |
| fact | 25 | 14-15/15 |
| negative | 8 | 7/7 |
| per-chapter | 5 | 5/5 |
| relation | 15 | 5/5 |
| aggregation | 12 | 4-5/5 |
| semantic | 15 | 6/7 |

`temporal` là loại khó nhất — câu mà đáp án **thay đổi theo chương**
("ở chương 20 nhân vật chính tên gì?" khác "ở chương 40…"). Không retriever văn bản
nào giải được; phải có `first_ch`/`last_ch` ở tầng dữ liệu.

## Hạn chế đã biết

- **Scene/Fact vẫn cần script.** Nút trong UI mới nạp Chapter, Chunk, Entity.
  Phần Scene graph và Fact có nghĩa chưa đưa vào đường ingest của app.
- **`comic_id` đang cố định là 1** trong graph. Nhiều truyện cần sửa phần dựng graph.
- **Trích cảnh không ổn định.** LLM diễn đạt khác nhau giữa các lần chạy, nên
  full-text trên Scene có thể trúng hôm nay, trượt mai (`research/notes/14` vòng 5).
- **Đánh giá truyện chưa có số liệu kiểm chứng.** Khác tra cứu và kiểm mâu thuẫn,
  chất lượng nhận xét là chủ quan — chưa có bộ thử để đo. Hai ràng buộc (dẫn chứng
  bắt buộc, số liệu lấy từ graph) giảm bịa nhưng chưa đo được giảm bao nhiêu.
- **Kiểm mâu thuẫn mới có 10 ca thử.** Quá ít để kết luận, và cả 10 do tôi viết —
  mô phỏng lỗi tôi *nghĩ* người viết sẽ mắc. Lỗi thật có thể khác hẳn.
  Chưa có UI cho `check-conflict`.
- **Ground truth từng sai.** Xem `research/notes/12` — bài học: khi hệ thống "sai"
  một cách nhất quán và có trích dẫn, hãy nghi ngờ đáp án chuẩn trước.
