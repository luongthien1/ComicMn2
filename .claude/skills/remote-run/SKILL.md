---
name: remote-run
description: Run any command on a remote machine over Tailscale SSH with per-run logging. Every run gets its own dated folder holding the command, stdout, stderr, exit code and whatever files it produced. Load whenever work needs a machine other than this one — a bigger GPU, more VRAM, more disk — or when asked to run/train/benchmark "on the home machine", "on the desktop", "on the other machine", or to inspect a previous remote run.
user-invocable: true
---

# Remote Run Skill

Chạy lệnh trên máy khác qua Tailscale SSH. **Mọi lần chạy đều được log** vào thư mục riêng theo ngày/giờ.

Wrapper: `.claude/skills/remote-run/scripts/rrun.sh`

## Cách gọi

**Không cần gọi gì** — nói việc bình thường là tự load:

> "chạy benchmark trên máy nhà" · "cái này nặng, đẩy sang GPU 3060" · "xem log run vừa rồi"

**Hoặc gõ tay** `/remote-run` khi muốn chủ động — ví dụ khi việc trông nhẹ nhưng bạn biết nó sẽ nặng, hoặc muốn chắc chắn có log.

---

## Quy tắc bắt buộc

> **Không `ssh` trực tiếp để chạy việc.** Luôn dùng `rrun.sh`.
>
> **Mọi file sinh ra trên máy remote — kể cả file tạm — nằm trong `C:\Me\claude`.** Không ghi vào home dir, không ghi vào `%TEMP%`, không ghi ra Desktop.

`ssh` trực tiếp chỉ dùng để *xem* nhanh (`ssh homegpu "dir ..."`, `ssh homegpu "type ..."`), không dùng để chạy job.

---

## Máy đã cấu hình

| Alias | Host | GPU |
|---|---|---|
| `homegpu` | `100.70.124.98` · `DESKTOP-JMF18RA` · user `ADMIN` | **RTX 3060 12 GB** |

Máy này (laptop): `desktop-fm11opo` · `100.126.196.9` · RTX 3050 **4 GB**.

## Python — dùng venv riêng

```
C:\Me\claude\.venv\Scripts\python.exe        <- DUNG CAI NAY
```

Venv riêng trong thư mục làm việc, py3.12.13. **Không đụng conda env `model` của user** — đó là env của họ, cài thêm vào đó là làm bẩn môi trường người khác.

`rrun.sh` với `-s` tự dùng venv này (biến `REMOTE_PY` ở đầu script).

Đã cài: `torch 2.5.1+cu121` · `torchvision` · `numpy` · `cv2` · `rasterio` · `pillow` · `ultralytics` · `deepforest` · `scikit-image`.

**Không cài `sam2`** — SAM 3 cho polygon tán tốt hơn hẳn (89.8% vs 66.4% trong dải đường kính) và không cần detector ngoài. SAM 2 đã bị loại khỏi hướng đi cho `M02`.

Cài thêm package:

```bash
R=.claude/skills/remote-run/scripts/rrun.sh
VPY='C:\Me\claude\.venv\Scripts\python.exe'
bash $R -b -n pip-install -- "$VPY" -m pip install <packages>
```

**torch phải cài từ index CUDA**, không thì được bản CPU:

```bash
bash $R -b -n pip-torch -- "$VPY" -m pip install torch torchvision \
  --index-url https://download.pytorch.org/whl/cu121
```

Và **cài torch TRƯỚC** các package khác. `deepforest`/`ultralytics` kéo torch bản CPU về ghi đè nếu chưa có — đã xảy ra trên laptop. Kiểm sau mỗi lần cài:

```bash
bash $R -- "$VPY" -c "import torch;print(torch.__version__, torch.cuda.is_available())"
```

Phải ra `+cu121 ... True`. Ra `+cpu` thì cài lại torch từ index CUDA.

---

## Cách dùng

```bash
R=.claude/skills/remote-run/scripts/rrun.sh
```

### Lệnh một dòng

```bash
bash $R -- nvidia-smi
bash $R -- dir C:\Me\claude\data
```

### Script Python — cách khuyên dùng

Upload script rồi chạy. Tránh hết vấn đề quoting, và output của script tự nằm cùng log:

```bash
bash $R -n sam3-fullframe -s scripts/bench.py --sam3 sam3.pt --out out
```

`-s` tự dùng python của venv, không cần khai đường dẫn.

### Việc lâu — background

```bash
bash $R -b -n long-train -s train.py
# tra ve ngay; theo doi bang -c 1
```

Việc quá 2 phút thì dùng `-b`, đừng để ssh treo.

### Xem lại

```bash
bash $R -l        # liet ke 20 run moi nhat + exit code
bash $R -c 1      # doc log run moi nhat
bash $R -c 3      # run thu 3 tu moi nhat
```

### Kéo kết quả về

```bash
scp -r "homegpu:C:/Me/claude/run/2026-09-09/080423_gpu-probe" ./results/
```

Về laptop rồi thì `Read` được bình thường — kể cả xem ảnh.

### Máy khác

```bash
bash $R -h user@100.x.x.x -- hostname
```

Cùng format thư mục. Nếu máy đó khác đường dẫn thì sửa `REMOTE_ROOT` / `REMOTE_PY` ở đầu `rrun.sh`.

---

## Cờ

| Cờ | Ý nghĩa | Mặc định |
|---|---|---|
| `-h HOST` | ssh alias hoặc `user@host` | `homegpu` |
| `-n NAME` | slug tên thư mục run | suy từ lệnh |
| `-d WORKDIR` | `cd` vào đây trước khi chạy | `C:\Me\claude` |
| `-s SCRIPT` | upload file này vào run folder rồi chạy bằng python của venv | — |
| `-b` | background, trả về ngay | tắt |
| `-l` | liệt kê run gần đây | — |
| `-c N` | đọc log run thứ N (1 = mới nhất) | `-c 1` |

---

## Cấu trúc trên máy remote

```
C:\Me\claude\
├── run\2026-09-09\080423_gpu-probe\
│   ├── cmd.txt        host, workdir, lenh da go
│   ├── probe_gpu.py   script duoc upload
│   ├── gpu_info.json  output cua script — cung nam day
│   ├── stdout.log
│   ├── stderr.log
│   └── meta.json      exit_code, thoi diem xong
├── storage\           FILE DUNG CHUNG — model weights, dataset, thu tai 1 lan dung nhieu lan
├── code\              code dung lai nhieu lan
└── data\              input/output cua rieng mot viec
```

Script chạy **từ trong run folder của chính nó**, nên file nó sinh ra tự nằm cùng log.

### `storage` — file dùng chung

Thứ **tải/copy một lần, dùng cho nhiều run**. Đặt ở đây, đừng nhét vào run folder:

- Model weights: `sam3.pt` (3.3 GB), `best.pt`, `yolo11s-seg.pt`
- Ortho, ảnh drone gốc
- Dataset đã gán nhãn

Tham chiếu từ script bằng đường dẫn tuyệt đối:

```bash
bash $R -n sam3-full -s bench.py \
  --sam3 'C:\Me\claude\storage\sam3.pt' \
  --ortho 'C:\Me\claude\storage\odm_orthophoto (2).tif'
```

Upload:

```bash
scp "E:/.../sam3.pt" 'homegpu:C:/Me/claude/storage/'
ssh homegpu "dir C:\Me\claude\storage"       # kiem tra da co gi truoc khi tai lai
```

**Kiểm `storage` trước khi upload** — file 3.3 GB tải lại là mất thời gian vô ích.

Phân biệt với `data\`: `storage` là dùng chung nhiều việc; `data` là input/output của riêng một việc đang làm.

---

## Khi nào đẩy việc sang máy remote

| Việc | Laptop 4 GB | **homegpu 12 GB** |
|---|---|---|
| SAM 3 full frame | OOM — phải tile + NMS merge | Chạy được (peak 6.1 GB) |
| SAM 2 batch prompt lớn | batch 32 | batch lớn hơn nhiều |
| Train / fine-tune | Chật | Thoải mái |
| Đọc / edit code | **Ở laptop** | Không cần |

Cách làm: **edit code ở laptop** (có Read/Edit/diff đầy đủ), chỉ đẩy compute sang. Đừng edit qua ssh.

---

## Năm chỗ phải vòng qua

Đã mất thời gian tìm ra. Đừng "sửa cho gọn" rồi vỡ lại:

| Vấn đề | Cách vòng trong `rrun.sh` |
|---|---|
| Shell mặc định là **cmd.exe**, không phải PowerShell | Bọc `powershell -Command "..."` khi cần, hoặc dùng cmd thuần |
| `python` trên PATH là **uv shim hỏng** trong non-interactive shell (`uv trampoline failed to spawn`) | `-s` dùng đường dẫn python tuyệt đối |
| PowerShell here-string `@'...'@` **mất newline** qua ssh | `cmd.txt` ghi bằng redirect cmd.exe |
| PowerShell nhiều dòng + nested quote **vỡ** qua ssh | `-l`/`-c` dùng `dir`/`type` thuần |
| `start /B cmd /c "<chuỗi dài>"` **mất quoting** | Ghi lệnh vào `run.cmd` rồi `start` file đó |
| `%PY%` set và dùng **cùng một dòng** cmd không giãn | `-s` dùng đường dẫn trực tiếp |
| `ssh` trong vòng `while` **ăn stdin** → chỉ đọc dòng đầu | `ssh -n` trong vòng lặp |

Nói chung: **nested quoting qua bash → ssh → cmd.exe rất dễ vỡ.** Cách an toàn nhất là `-s` (upload script), không inline lệnh phức tạp.

---

## Bảo mật

Key `~/.ssh/id_ed25519_home` trên laptop **không có passphrase** — đánh đổi có chủ ý để chạy tự động. Ai lấy được file đó vào được `homegpu` với quyền Administrator.

Đã làm: `PasswordAuthentication no`, DEBUG3 đã tắt.

Chưa làm — nhắc user khi xong hẳn việc:

```powershell
# tren may nha: thu hoi key
$f = "C:\Users\ADMIN\.ssh\authorized_keys"
(Get-Content $f) | Where-Object { $_ -notmatch 'claude-code-worklaptop' } | Set-Content $f
```

Setup chi tiết + cách dựng máy mới: [HOME-GPU-TAILSCALE.md](../../../docs/personal/thien.l/HOME-GPU-TAILSCALE.md)
