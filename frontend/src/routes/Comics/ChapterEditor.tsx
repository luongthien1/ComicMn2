import { useAlert } from "@/components/Alert/alertContext";
import { ComicApi } from "@/api/comics";
import { AiApi } from "@/api/ai";
import { ReviewPanel } from "@/components/StoryReview/ReviewPanel";
import type { IngestProgress, StoryGraphStats } from "@/api/ai";
import type { Chapter, ChapterDetail } from "@/types/comic";
import {
  ArrowLeftOutlined,
  BoldOutlined,
  BookOutlined,
  CheckOutlined,
  CloseOutlined,
  CopyOutlined,
  DeleteOutlined,
  EditOutlined,
  ItalicOutlined,
  MessageOutlined,
  StarOutlined,
  OrderedListOutlined,
  PictureOutlined,
  PlusOutlined,
  RobotOutlined,
  SaveOutlined,
  SendOutlined,
  StrikethroughOutlined,
  UnderlineOutlined,
  UnorderedListOutlined,
  UploadOutlined,
  UserOutlined,
} from "@ant-design/icons";
import {
  Avatar,
  Button,
  Divider,
  Empty,
  Input,
  Modal,
  Segmented,
  Space,
  Spin,
  Tooltip,
} from "antd";
import { EditorContent, useEditor, type Editor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import TiptapImage from "@tiptap/extension-image";
import Underline from "@tiptap/extension-underline";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import "./editor.css";

const api = new ComicApi();
const aiApi = new AiApi();
const BASE_URL = import.meta.env.VITE_BACKEND_API_URL ?? "";

// ── LocalStorage helpers ──────────────────────────────────────────────────────

interface AssetItem { url: string; name: string }
interface QAItem {
  id: string; q: string; a: string;
  /** Chương mà câu trả lời dựa vào — để người viết kiểm chứng. */
  sources?: number[];
  /** Mã trace để xem hệ thống đã truy vấn những gì. */
  traceId?: string;
}

const ASSETS_KEY = "comic-assets";

const ls = {
  assets: (): AssetItem[] => { try { return JSON.parse(localStorage.getItem(ASSETS_KEY) ?? "[]"); } catch { return []; } },
  saveAssets: (v: AssetItem[]) => localStorage.setItem(ASSETS_KEY, JSON.stringify(v)),
  note: (id: string) => localStorage.getItem(`chapter-note-${id}`) ?? "",
  saveNote: (id: string, v: string) => localStorage.setItem(`chapter-note-${id}`, v),
  qa: (id: string): QAItem[] => { try { return JSON.parse(localStorage.getItem(`chapter-qa-${id}`) ?? "[]"); } catch { return []; } },
  saveQA: (id: string, v: QAItem[]) => localStorage.setItem(`chapter-qa-${id}`, JSON.stringify(v)),
};

// ── Toolbar ───────────────────────────────────────────────────────────────────

function Toolbar({ editor, onInsertUrl }: { editor: Editor; onInsertUrl: () => void }) {
  const getStyle = (name: string, attrs?: object) => {
    const active = editor.isActive(name, attrs);
    return {
      backgroundColor: active ? "#000" : "transparent",
      color: active ? "#fff" : "rgba(0,0,0,0.88)",
      borderColor: "transparent",
      boxShadow: "none"
    };
  };

  return (
    <div style={{ display: "flex", alignItems: "center", gap: 2, padding: "5px 10px", borderBottom: "1px solid #f0f0f0", flexWrap: "wrap", background: "#fafafa" }}>
      <Tooltip title="Đậm (Ctrl+B)">
        <Button size="small" type="text" style={getStyle("bold")} icon={<BoldOutlined />} onClick={() => editor.chain().focus().toggleBold().run()} />
      </Tooltip>
      <Tooltip title="Nghiêng (Ctrl+I)">
        <Button size="small" type="text" style={getStyle("italic")} icon={<ItalicOutlined />} onClick={() => editor.chain().focus().toggleItalic().run()} />
      </Tooltip>
      <Tooltip title="Gạch chân (Ctrl+U)">
        <Button size="small" type="text" style={getStyle("underline")} icon={<UnderlineOutlined />} onClick={() => editor.chain().focus().toggleUnderline().run()} />
      </Tooltip>
      <Tooltip title="Gạch ngang">
        <Button size="small" type="text" style={getStyle("strike")} icon={<StrikethroughOutlined />} onClick={() => editor.chain().focus().toggleStrike().run()} />
      </Tooltip>
      <Divider type="vertical" style={{ margin: "0 4px", height: 18 }} />
      <Tooltip title="Danh sách">
        <Button size="small" type="text" style={getStyle("bulletList")} icon={<UnorderedListOutlined />} onClick={() => editor.chain().focus().toggleBulletList().run()} />
      </Tooltip>
      <Tooltip title="Danh sách số">
        <Button size="small" type="text" style={getStyle("orderedList")} icon={<OrderedListOutlined />} onClick={() => editor.chain().focus().toggleOrderedList().run()} />
      </Tooltip>
      <Divider type="vertical" style={{ margin: "0 4px", height: 18 }} />
      <Tooltip title="Chèn ảnh theo URL">
        <Button size="small" type="text" icon={<PictureOutlined />} onClick={onInsertUrl} />
      </Tooltip>
    </div>
  );
}

// ── Assets Tab ────────────────────────────────────────────────────────────────

function AssetsTab({
  assets, onAssetsChange, onInsert, onError,
}: {
  assets: AssetItem[];
  onAssetsChange: (assets: AssetItem[]) => void;
  onInsert: (url: string) => void;
  onError: (msg: string) => void;
}) {
  const [uploading, setUploading] = useState(false);
  const [copiedUrl, setCopiedUrl] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const res = await api.uploadFile(file);
      const item: AssetItem = { url: BASE_URL + res.url, name: file.name };
      onAssetsChange([item, ...assets]);
    } catch (err: any) {
      onError(err.message);
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  const remove = (url: string) => {
    onAssetsChange(assets.filter((a) => a.url !== url));
  };

  const copyUrl = async (url: string) => {
    try {
      await navigator.clipboard.writeText(url);
      setCopiedUrl(url);
      setTimeout(() => setCopiedUrl((c) => (c === url ? null : c)), 1200);
    } catch (err: any) {
      onError("Không thể copy: " + err.message);
    }
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: 10, height: "100%", overflow: "hidden" }}>
      <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handleUpload} />
      <Button icon={<UploadOutlined />} loading={uploading} onClick={() => fileRef.current?.click()} block size="small">
        Upload ảnh
      </Button>
      <div style={{ flex: 1, overflowY: "auto" }}>
        {assets.length === 0 ? (
          <Empty description="Chưa có ảnh nào" imageStyle={{ height: 40 }} style={{ marginTop: 24 }} />
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 6 }}>
            {assets.map((a) => (
              <div
                key={a.url}
                title={a.name}
                style={{ position: "relative", cursor: "pointer", borderRadius: 4, overflow: "hidden", border: "1px solid #f0f0f0" }}
                onClick={() => onInsert(a.url)}
              >
                <img src={a.url} alt={a.name} style={{ width: "100%", height: 76, objectFit: "cover", display: "block" }} />
                <div
                  style={{ position: "absolute", top: 2, right: 2, display: "flex", gap: 2 }}
                  onClick={(e) => e.stopPropagation()}
                >
                  <Tooltip title={copiedUrl === a.url ? "Đã copy!" : "Sao chép đường dẫn"}>
                    <Button
                      size="small"
                      icon={copiedUrl === a.url ? <CheckOutlined /> : <CopyOutlined />}
                      style={{ padding: "0 4px", minWidth: 0 }}
                      onClick={() => copyUrl(a.url)}
                    />
                  </Tooltip>
                  <Button danger size="small" icon={<DeleteOutlined />} style={{ padding: "0 4px", minWidth: 0 }} onClick={() => remove(a.url)} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Chapters Tab ──────────────────────────────────────────────────────────────

function ChaptersTab({ comicId, currentChapterId }: { comicId: number; currentChapterId: number }) {
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    setLoading(true);
    api.listChapters(comicId).then(setChapters).catch(() => {}).finally(() => setLoading(false));
  }, [comicId]);

  if (loading) return <div style={{ textAlign: "center", padding: 24 }}><Spin size="small" /></div>;

  return (
    <div style={{ height: "100%", overflowY: "auto" }}>
      {chapters.length === 0 ? (
        <Empty description="Không có chương" imageStyle={{ height: 40 }} style={{ padding: 24 }} />
      ) : chapters.map((ch) => (
        <div
          key={ch.id}
          onClick={() => navigate(`/comics/${comicId}/chapters/${ch.id}`)}
          style={{
            padding: "8px 12px",
            cursor: "pointer",
            background: ch.id === currentChapterId ? "#f0f0f0" : undefined,
            borderLeft: ch.id === currentChapterId ? "3px solid #000" : "3px solid transparent",
            fontSize: 13,
          }}
          onMouseEnter={(e) => { if (ch.id !== currentChapterId) (e.currentTarget as HTMLElement).style.background = "#f5f5f5"; }}
          onMouseLeave={(e) => { if (ch.id !== currentChapterId) (e.currentTarget as HTMLElement).style.background = ""; }}
        >
          <span style={{ fontWeight: ch.id === currentChapterId ? 600 : 400 }}>Chương {ch.number}</span>
          {ch.title && <span style={{ color: "#8c8c8c", marginLeft: 6 }}>{ch.title}</span>}
        </div>
      ))}
    </div>
  );
}

// ── Notes Tab ─────────────────────────────────────────────────────────────────

function NotesTab({ chapterId }: { chapterId: string }) {
  const [note, setNote] = useState(() => ls.note(chapterId));
  return (
    <div style={{ padding: 10, height: "100%", display: "flex", flexDirection: "column" }}>
      <Input.TextArea
        value={note}
        onChange={(e) => { setNote(e.target.value); ls.saveNote(chapterId, e.target.value); }}
        placeholder="Ghi chú cho chương này..."
        style={{ flex: 1, resize: "none", border: "none", outline: "none", padding: 0, fontSize: 13, boxShadow: "none" }}
        autoSize={false}
      />
    </div>
  );
}

// ── Q&A Tab ───────────────────────────────────────────────────────────────────

function QATab({ chapterId, comicId, chapterNumber }: {
  chapterId: string; comicId: number; chapterNumber?: number;
}) {
  const navigate = useNavigate();
  const [items, setItems] = useState<QAItem[]>(() => ls.qa(chapterId));
  const [inputVal, setInputVal] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editAnswerVal, setEditAnswerVal] = useState("");
  const [loadingId, setLoadingId] = useState<string | null>(null);

  // Trạng thái đồ thị tri thức — cho biết chat có tra cứu được truyện không
  const [graph, setGraph] = useState<StoryGraphStats | null>(null);
  const [ingest, setIngest] = useState<IngestProgress | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  const refreshGraph = () => {
    aiApi.storyGraphStats(comicId).then(setGraph).catch(() => setGraph(null));
  };

  useEffect(refreshGraph, [comicId]);

  // Hỏi tiến độ trong lúc nạp; dừng khi xong rồi lấy lại thống kê
  useEffect(() => {
    if (!ingest?.running) return;
    const timer = setInterval(() => {
      aiApi.ingestProgress(comicId)
        .then((p) => {
          setIngest(p);
          if (!p.running) refreshGraph();
        })
        .catch(() => setIngest(null));
    }, 2000);
    return () => clearInterval(timer);
  }, [ingest?.running, comicId]);

  const startIngest = async () => {
    setIngest({ running: true, finished: false, stage: "bắt đầu", done: 0, total: 0, percent: 0 });
    try {
      await aiApi.ingestStoryGraph(comicId);
    } catch (e) {
      setIngest({
        running: false, finished: false, stage: "", done: 0, total: 0, percent: 0,
        error: e instanceof Error ? e.message : "Không nạp được truyện",
      });
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [items, editingId, loadingId]);

  const askGemini = async (allItems: QAItem[], targetId: string) => {
    setLoadingId(targetId);
    try {
      // Build conversation history from existing Q&A pairs
      const messages = allItems.flatMap((item) => {
        const turns: { role: "user" | "model"; content: string }[] = [
          { role: "user", content: item.q },
        ];
        if (item.a) turns.push({ role: "model", content: item.a });
        return turns;
      });

      // comic_id bật tra cứu truyện từ đồ thị tri thức; chapter giới hạn
      // phạm vi cho câu hỏi về chương đang mở (research/notes/09: 3/7 -> 7/7).
      const res = await aiApi.chat({
        messages,
        comic_id: comicId,
        chapter: chapterNumber,
      });

      // Fill the answer into the target item
      const filled = allItems.map((item) =>
        item.id === targetId
          ? {
              ...item,
              a: res.answer,
              sources: res.retrieval?.chapters ?? [],
              traceId: res.retrieval?.trace_id ?? undefined,
            }
          : item
      );
      setItems(filled);
      ls.saveQA(chapterId, filled);
    } catch {
      // On error, open manual edit mode so user can type themselves
      setEditingId(targetId);
      setEditAnswerVal("");
    } finally {
      setLoadingId(null);
    }
  };

  const handleSendQuestion = () => {
    if (!inputVal.trim()) return;
    const newItem: QAItem = {
      id: Date.now().toString(),
      q: inputVal.trim(),
      a: "",
    };
    const updated = [...items, newItem];
    setItems(updated);
    ls.saveQA(chapterId, updated);
    setInputVal("");

    // Auto-call Gemini for the new question
    askGemini(updated, newItem.id);
  };

  const startEditing = (item: QAItem) => {
    setEditingId(item.id);
    setEditAnswerVal(item.a);
  };

  const saveAnswer = (id: string) => {
    const updated = items.map((item) =>
      item.id === id ? { ...item, a: editAnswerVal.trim() } : item
    );
    setItems(updated);
    ls.saveQA(chapterId, updated);
    setEditingId(null);
  };

  const remove = (id: string) => {
    const updated = items.filter((i) => i.id !== id);
    setItems(updated);
    ls.saveQA(chapterId, updated);
    if (editingId === id) setEditingId(null);
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", overflow: "hidden", background: "#f8f9fa" }}>
      {/* Trạng thái đồ thị tri thức */}
      <div
        style={{
          padding: "6px 10px",
          borderBottom: "1px solid #f0f0f0",
          background: "#fff",
          fontSize: 11,
          color: "#8c8c8c",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 8,
        }}
      >
        {ingest?.running ? (
          <span>
            Đang nạp truyện… {ingest.stage}
            {ingest.total > 0 ? ` (${ingest.done}/${ingest.total})` : ""}
          </span>
        ) : ingest?.error ? (
          <span style={{ color: "#cf1322" }}>{ingest.error}</span>
        ) : graph?.available && (graph.chunks ?? 0) > 0 ? (
          <span>
            Tra cứu truyện: {graph.chapters} chương · {graph.entities} nhân vật
            {(graph.scenes ?? 0) > 0 ? ` · ${graph.scenes} cảnh` : ""}
          </span>
        ) : graph?.available ? (
          <span>Chưa nạp truyện — chat sẽ không tra cứu được nội dung.</span>
        ) : (
          <span>Chưa kết nối đồ thị tri thức.</span>
        )}

        {graph?.available && !ingest?.running && (
          <Button size="small" type="link" style={{ fontSize: 11, padding: 0 }} onClick={startIngest}>
            {(graph.chunks ?? 0) > 0 ? "Nạp lại" : "Nạp truyện"}
          </Button>
        )}
      </div>

      {/* Chat Area */}
      <div style={{ flex: 1, overflowY: "auto", padding: "12px 10px" }}>
        {items.length === 0 ? (
          <Empty 
            description="Chưa có câu hỏi. Hãy bắt đầu cuộc hội thoại bằng cách đặt câu hỏi ở ô bên dưới!" 
            imageStyle={{ height: 50 }} 
            style={{ marginTop: 40, padding: "0 10px" }} 
          />
        ) : (
          items.map((item) => (
            <div key={item.id} style={{ marginBottom: 16 }}>
              {/* Question Bubble (Right aligned) */}
              <div style={{ display: "flex", justifyContent: "flex-end", alignItems: "flex-start", gap: 8, marginBottom: 8 }}>
                <Tooltip title="Xóa câu hỏi">
                  <Button 
                    size="small" 
                    type="text" 
                    danger 
                    icon={<DeleteOutlined />} 
                    style={{ opacity: 0.5, alignSelf: "center" }} 
                    onClick={() => remove(item.id)}
                  />
                </Tooltip>
                <div style={{ 
                  background: "#000", 
                  color: "#fff", 
                  padding: "8px 12px", 
                  borderRadius: "12px 12px 2px 12px", 
                  fontSize: 13, 
                  maxWidth: "75%", 
                  wordBreak: "break-word",
                  boxShadow: "0 2px 4px rgba(0, 0, 0, 0.15)"
                }}>
                  {item.q}
                </div>
                <Avatar size="small" icon={<UserOutlined />} style={{ backgroundColor: "#262626", flexShrink: 0 }} />
              </div>

              {/* Answer Bubble (Left aligned) */}
              <div style={{ display: "flex", justifyContent: "flex-start", alignItems: "flex-start", gap: 8 }}>
                <Avatar size="small" icon={<RobotOutlined />} style={{ backgroundColor: "#595959", flexShrink: 0 }} />
                {editingId === item.id ? (
                  <div style={{ 
                    flex: 1, 
                    maxWidth: "75%", 
                    background: "#fff", 
                    border: "1px solid #d9d9d9", 
                    borderRadius: "12px 12px 12px 2px", 
                    padding: 8, 
                    boxShadow: "0 2px 8px rgba(0,0,0,0.08)" 
                  }}>
                    <Input.TextArea
                      value={editAnswerVal}
                      onChange={(e) => setEditAnswerVal(e.target.value)}
                      placeholder="Nhập câu trả lời..."
                      autoSize={{ minRows: 2, maxRows: 6 }}
                      style={{ fontSize: 13, border: "none", outline: "none", padding: 0, boxShadow: "none", resize: "none" }}
                      autoFocus
                    />
                    <div style={{ display: "flex", justifyContent: "flex-end", gap: 4, marginTop: 6, borderTop: "1px solid #f0f0f0", paddingTop: 6 }}>
                      <Button size="small" type="primary" icon={<CheckOutlined />} onClick={() => saveAnswer(item.id)} style={{ backgroundColor: "#000", borderColor: "#000", color: "#fff" }}>Lưu</Button>
                      <Button size="small" icon={<CloseOutlined />} onClick={() => setEditingId(null)}>Hủy</Button>
                    </div>
                  </div>
                ) : loadingId === item.id ? (
                  <div style={{ 
                    background: "#fff", 
                    color: "#8c8c8c", 
                    padding: "8px 12px", 
                    borderRadius: "12px 12px 12px 2px", 
                    fontSize: 13, 
                    maxWidth: "75%", 
                    border: "1px solid #f0f0f0",
                    boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
                    display: "flex",
                    alignItems: "center",
                    gap: 8
                  }}>
                    <Spin size="small" />
                    <span>Gemini đang trả lời...</span>
                  </div>
                ) : item.a ? (
                  <div 
                    onClick={() => startEditing(item)}
                    style={{ 
                      background: "#fff", 
                      color: "#262626", 
                      padding: "8px 12px", 
                      borderRadius: "12px 12px 12px 2px", 
                      fontSize: 13, 
                      maxWidth: "75%", 
                      wordBreak: "break-word",
                      cursor: "pointer",
                      boxShadow: "0 2px 4px rgba(0,0,0,0.05)",
                      position: "relative",
                      border: "1px solid #f0f0f0"
                    }}
                    title="Click để chỉnh sửa câu trả lời"
                  >
                    {item.a}
                    {(item.sources?.length || item.traceId) && (
                      <div
                        style={{
                          marginTop: 6,
                          paddingTop: 6,
                          borderTop: "1px solid #f5f5f5",
                          fontSize: 11,
                          color: "#8c8c8c",
                          display: "flex",
                          alignItems: "center",
                          gap: 8,
                          flexWrap: "wrap",
                        }}
                      >
                        {item.sources && item.sources.length > 0 && (
                          <span title="Câu trả lời dựa trên các chương này">
                            Nguồn: {item.sources.map((c) => `ch.${c}`).join(", ")}
                          </span>
                        )}
                        {item.traceId && (
                          <a
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/comics/${comicId}/trace?trace=${item.traceId}`);
                            }}
                            style={{ fontSize: 11 }}
                            title="Xem hệ thống đã truy vấn node và quan hệ nào"
                          >
                            Xem suy luận →
                          </a>
                        )}
                      </div>
                    )}
                    <div style={{ position: "absolute", bottom: 2, right: 4, fontSize: 10, color: "#bfbfbf" }}>
                      <EditOutlined />
                    </div>
                  </div>
                ) : (
                  <div 
                    onClick={() => startEditing(item)}
                    style={{ 
                      border: "1px dashed #d9d9d9", 
                      color: "#8c8c8c", 
                      padding: "8px 12px", 
                      borderRadius: "12px 12px 12px 2px", 
                      fontSize: 13, 
                      maxWidth: "75%", 
                      cursor: "pointer",
                      background: "#fff",
                      userSelect: "none"
                    }}
                  >
                    <Space size={4}>
                      <PlusOutlined style={{ fontSize: 11 }} />
                      <span>Thêm câu trả lời...</span>
                    </Space>
                  </div>
                )}
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div style={{ borderTop: "1px solid #f0f0f0", padding: "10px 12px", flexShrink: 0, background: "#fff", display: "flex", gap: 8, alignItems: "center" }}>
        <Input 
          placeholder="Nhập câu hỏi..." 
          value={inputVal} 
          onChange={(e) => setInputVal(e.target.value)} 
          onPressEnter={handleSendQuestion}
          style={{ borderRadius: 16 }}
        />
        <Button 
          type="primary" 
          shape="circle" 
          icon={<SendOutlined />} 
          onClick={handleSendQuestion} 
          disabled={!inputVal.trim()} 
          style={{ 
            flexShrink: 0, 
            backgroundColor: inputVal.trim() ? "#000" : undefined, 
            borderColor: inputVal.trim() ? "#000" : undefined 
          }}
        />
      </div>
    </div>
  );
}

// ── Sidebar ───────────────────────────────────────────────────────────────────

type TabKey = "assets" | "chapters" | "notes" | "qa" | "review";

const TABS: { key: TabKey; label: string; icon: React.ReactNode }[] = [
  { key: "assets",   label: "Ảnh", icon: <PictureOutlined /> },
  { key: "chapters", label: "Chương", icon: <BookOutlined /> },
  { key: "notes",    label: "Ghi chú", icon: <EditOutlined /> },
  { key: "qa",       label: "Hỏi đáp", icon: <MessageOutlined /> },
  { key: "review",   label: "Đánh giá", icon: <StarOutlined /> },
];

function Sidebar({
  comicId, chapterId, chapterNumber, assets, onAssetsChange, onInsert, onError, isOpen, setIsOpen
}: {
  comicId: number; chapterId: number; chapterNumber?: number;
  assets: AssetItem[];
  onAssetsChange: (assets: AssetItem[]) => void;
  onInsert: (url: string) => void;
  onError: (msg: string) => void;
  isOpen: boolean;
  setIsOpen: (open: boolean) => void;
}) {
  const [active, setActive] = useState<TabKey>("assets");

  const handleTabClick = (key: TabKey) => {
    if (active === key) {
      setIsOpen(!isOpen);
    } else {
      setActive(key);
      setIsOpen(true);
    }
  };

  return (
    <div style={{ 
      position: "relative", 
      display: "flex", 
      flexDirection: "row", 
      height: "100%",
      flexShrink: 0,
      // Always keep enough space for the protruding tab buttons (37px wide)
      width: isOpen ? 287 : 37,
      transition: "width 0.2s cubic-bezier(0.2, 0.8, 0.2, 1)",
    }}>
      {/* Protruding tab buttons — always visible */}
      <div style={{
        width: "37px",
        flexShrink: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: "6px",
        paddingTop: "16px",
      }}>
        {TABS.map((tab) => {
          const isActive = active === tab.key && isOpen;
          return (
            <Tooltip key={tab.key} title={tab.label} placement="left">
              <button
                onClick={() => handleTabClick(tab.key)}
                style={{
                  width: "36px",
                  height: "36px",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  background: isActive ? "#000" : "#fff",
                  color: isActive ? "#fff" : "#000",
                  border: "1px solid #d9d9d9",
                  borderRight: isActive ? "1px solid transparent" : "1px solid #d9d9d9",
                  borderRadius: "6px 0 0 6px",
                  cursor: "pointer",
                  fontSize: "16px",
                  boxShadow: "-2px 2px 4px rgba(0,0,0,0.05)",
                  transition: "all 0.15s ease",
                  outline: "none",
                  position: "relative",
                  zIndex: 2,
                }}
                onMouseEnter={(e) => {
                  if (!isActive) e.currentTarget.style.background = "#f5f5f5";
                }}
                onMouseLeave={(e) => {
                  if (!isActive) e.currentTarget.style.background = "#fff";
                }}
              >
                {tab.icon}
              </button>
            </Tooltip>
          );
        })}
      </div>

      {/* Main Sidebar Content Area */}
      <div style={{
        flex: 1,
        opacity: isOpen ? 1 : 0,
        visibility: isOpen ? "visible" : "hidden",
        transition: "opacity 0.15s ease, visibility 0.2s",
        border: isOpen ? "1px solid #d9d9d9" : "none",
        borderLeft: "none",
        borderRadius: "0 4px 4px 0",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        background: "#fff",
        height: "100%",
        boxSizing: "border-box",
      }}>
        {/* Header/Title of Active Tab */}
        <div style={{ 
          padding: "10px 12px", 
          fontWeight: 600, 
          fontSize: "13px", 
          borderBottom: "1px solid #f0f0f0", 
          background: "#fafafa",
          color: "#262626",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexShrink: 0,
        }}>
          <span>{TABS.find(t => t.key === active)?.label}</span>
          <Button 
            size="small" 
            type="text" 
            icon={<CloseOutlined style={{ fontSize: 10 }} />} 
            onClick={() => setIsOpen(false)}
            style={{ color: "#8c8c8c" }}
          />
        </div>

        <div style={{ flex: 1, overflow: "hidden" }}>
          {active === "assets"   && <AssetsTab assets={assets} onAssetsChange={onAssetsChange} onInsert={onInsert} onError={onError} />}
          {active === "chapters" && <ChaptersTab comicId={comicId} currentChapterId={chapterId} />}
          {active === "notes"    && <NotesTab chapterId={String(chapterId)} />}
          {active === "qa"       && <QATab chapterId={String(chapterId)} comicId={comicId} chapterNumber={chapterNumber} />}
          {active === "review"   && <ReviewPanel comicId={comicId} chapterNumber={chapterNumber} />}
        </div>
      </div>
    </div>
  );
}

// ── Main ──────────────────────────────────────────────────────────────────────

export default function ChapterEditor() {
  const { comicId, chapterId } = useParams<{ comicId: string; chapterId: string }>();
  const navigate = useNavigate();
  const { show } = useAlert();

  const [chapter, setChapter] = useState<ChapterDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [urlModalOpen, setUrlModalOpen] = useState(false);
  const [imageUrl, setImageUrl] = useState("");
  const [insertTab, setInsertTab] = useState<"url" | "upload">("url");
  const [modalUploading, setModalUploading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [assets, setAssets] = useState<AssetItem[]>(ls.assets);
  const modalFileRef = useRef<HTMLInputElement>(null);

  const updateAssets = useCallback((updated: AssetItem[]) => {
    ls.saveAssets(updated);
    setAssets(updated);
  }, []);

  const editor = useEditor({
    extensions: [
      StarterKit,
      TiptapImage.configure({ inline: false, allowBase64: false }),
      Underline,
    ],
    editorProps: { attributes: { class: "comic-editor" } },
  });

  useEffect(() => {
    if (!comicId || !chapterId) return;
    setLoading(true);
    api.getChapter(Number(comicId), Number(chapterId))
      .then((data) => { setChapter(data); })
      .catch((e) => show("error", e.message))
      .finally(() => setLoading(false));
  }, [comicId, chapterId]);

  useEffect(() => {
    if (chapter && editor) editor.commands.setContent(chapter.content ?? "");
  }, [chapter, editor]);

  const handleSave = async () => {
    if (!editor) return;
    setSaving(true);
    try {
      await api.updateChapter(Number(comicId), Number(chapterId), { content: editor.getHTML() });
      show("success", "Đã lưu nội dung");
    } catch (e: any) {
      show("error", e.message);
    } finally {
      setSaving(false);
    }
  };

  const insertImage = useCallback((url: string) => {
    if (!editor) return;
    editor
      .chain()
      .focus()
      .setImage({ src: url })
      .insertContent({ type: "paragraph" })
      .run();
  }, [editor]);

  const closeInsertModal = () => {
    setUrlModalOpen(false);
    setImageUrl("");
    setInsertTab("url");
  };

  const insertImageByUrl = () => {
    const url = imageUrl.trim();
    if (!url) return;
    insertImage(url);
    closeInsertModal();
  };

  const handleModalUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setModalUploading(true);
    try {
      const res = await api.uploadFile(file);
      const item: AssetItem = { url: BASE_URL + res.url, name: file.name };
      updateAssets([item, ...assets]);
      insertImage(item.url);
      closeInsertModal();
    } catch (err: any) {
      show("error", err.message);
    } finally {
      setModalUploading(false);
      if (modalFileRef.current) modalFileRef.current.value = "";
    }
  };

  if (loading) return <div style={{ textAlign: "center", paddingTop: 80 }}><Spin size="large" /></div>;
  if (!chapter) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "calc(100vh - 92px)" }}>
      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12, flexShrink: 0 }}>
        <Space>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(`/comics/${comicId}`)}>Quay lại</Button>
          <span style={{ fontWeight: 600, fontSize: 15 }}>
            Chương {chapter.number}{chapter.title ? `: ${chapter.title}` : ""}
          </span>
        </Space>
        <Button 
          type="primary" 
          icon={<SaveOutlined />} 
          loading={saving} 
          onClick={handleSave}
          style={{ backgroundColor: "#000", borderColor: "#000", color: "#fff" }}
        >
          Lưu
        </Button>
      </div>

      {/* Body */}
      <div style={{ display: "flex", gap: 8, flex: 1, overflow: "hidden" }}>
        {/* Editor */}
        <div style={{ flex: 1, border: "1px solid #d9d9d9", borderRadius: 4, overflow: "hidden", display: "flex", flexDirection: "column", background: "#fff" }}>
          {editor && <Toolbar editor={editor} onInsertUrl={() => setUrlModalOpen(true)} />}
          <div style={{ flex: 1, overflowY: "auto" }}>
            <EditorContent editor={editor} />
          </div>
        </div>

        <Sidebar
          comicId={Number(comicId)}
          chapterId={Number(chapterId)}
          chapterNumber={chapter?.number}
          assets={assets}
          onAssetsChange={updateAssets}
          onInsert={insertImage}
          onError={(msg) => show("error", msg)}
          isOpen={sidebarOpen}
          setIsOpen={setSidebarOpen}
        />
      </div>

      <Modal
        title="Chèn ảnh minh họa"
        open={urlModalOpen}
        onCancel={closeInsertModal}
        footer={insertTab === "url" ? undefined : null}
        onOk={insertTab === "url" ? insertImageByUrl : undefined}
        okText="Chèn"
        cancelText="Hủy"
        okButtonProps={{ disabled: !imageUrl.trim() }}
        width={480}
      >
        <Segmented
          value={insertTab}
          onChange={(v) => setInsertTab(v as "url" | "upload")}
          options={[
            { value: "url", label: "Dán URL" },
            { value: "upload", label: "Upload từ máy" },
          ]}
          block
          style={{ marginTop: 8, marginBottom: 12 }}
        />

        {insertTab === "url" ? (
          <Input
            placeholder="Nhập URL ảnh..."
            value={imageUrl}
            onChange={(e) => setImageUrl(e.target.value)}
            onPressEnter={insertImageByUrl}
            autoFocus
          />
        ) : (
          <div style={{ textAlign: "center", padding: "12px 0" }}>
            <input ref={modalFileRef} type="file" accept="image/*" style={{ display: "none" }} onChange={handleModalUpload} />
            <Button icon={<UploadOutlined />} loading={modalUploading} onClick={() => modalFileRef.current?.click()} block>
              Chọn ảnh từ máy...
            </Button>
            <div style={{ fontSize: 12, color: "#8c8c8c", marginTop: 8 }}>
              Ảnh sẽ được upload, chèn vào bài viết và lưu vào sidebar "Ảnh".
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
