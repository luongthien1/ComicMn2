import { AiApi } from "@/api/ai";
import type { TraceDetail, TraceStep, TraceSummary } from "@/api/ai";
import {
  ArrowLeftOutlined,
  BranchesOutlined,
  DatabaseOutlined,
  MessageOutlined,
  NodeIndexOutlined,
  ReloadOutlined,
} from "@ant-design/icons";
import { Button, Empty, Spin, Tag, Tooltip, Typography } from "antd";
import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";

const { Text, Paragraph } = Typography;
const aiApi = new AiApi();

/** Mỗi loại bước có màu và icon riêng để quét nhanh bằng mắt. */
const STEP_STYLE: Record<
  TraceStep["kind"],
  { color: string; icon: React.ReactNode; label: string }
> = {
  decision: { color: "#722ed1", icon: <BranchesOutlined />, label: "Quyết định" },
  cypher: { color: "#1677ff", icon: <DatabaseOutlined />, label: "Truy vấn đồ thị" },
  embed: { color: "#13c2c2", icon: <NodeIndexOutlined />, label: "Nhúng vector" },
  llm: { color: "#fa8c16", icon: <MessageOutlined />, label: "Gọi mô hình" },
};

const ROUTE_LABEL: Record<string, string> = {
  global: "Toàn truyện",
  chapter: "Giới hạn một chương",
  scene: "Theo cảnh",
};

function StepCard({ step, index }: { step: TraceStep; index: number }) {
  const [open, setOpen] = useState(step.kind === "decision");
  const style = STEP_STYLE[step.kind] ?? STEP_STYLE.cypher;
  const expandable = Boolean(step.cypher || step.sample.length > 0);

  return (
    <div
      style={{
        border: "1px solid var(--c-fill)",
        borderLeft: `3px solid ${style.color}`,
        borderRadius: 6,
        marginBottom: 10,
        background: "var(--c-bg)",
      }}
    >
      <div
        onClick={() => expandable && setOpen(!open)}
        style={{
          padding: "10px 14px",
          display: "flex",
          alignItems: "center",
          gap: 10,
          cursor: expandable ? "pointer" : "default",
        }}
      >
        <span style={{ color: "var(--c-text-4)", fontSize: 12, minWidth: 20 }}>{index + 1}</span>
        <span style={{ color: style.color }}>{style.icon}</span>
        <span style={{ fontWeight: 500, fontSize: 13, flex: 1 }}>{step.label}</span>

        {step.n_results !== null && step.n_results !== undefined && (
          <Tag color={step.n_results > 0 ? "blue" : "default"} style={{ marginRight: 0 }}>
            {step.n_results} kết quả
          </Tag>
        )}
        {step.ms !== null && step.ms !== undefined && (
          <Text type="secondary" style={{ fontSize: 11, minWidth: 48, textAlign: "right" }}>
            {step.ms < 1 ? "<1" : Math.round(step.ms)} ms
          </Text>
        )}
      </div>

      {step.note && (
        <div style={{ padding: "0 14px 10px 44px", fontSize: 12, color: "var(--c-text-2)" }}>
          {step.note}
        </div>
      )}

      {open && step.cypher && (
        <div style={{ padding: "0 14px 12px 44px" }}>
          <pre
            style={{
              background: "var(--c-bg-soft)",
              border: "1px solid var(--c-fill)",
              borderRadius: 4,
              padding: "8px 10px",
              fontSize: 11,
              lineHeight: 1.5,
              overflowX: "auto",
              margin: 0,
            }}
          >
            {step.cypher}
          </pre>
          {step.params && Object.keys(step.params).length > 0 && (
            <div style={{ marginTop: 6, fontSize: 11, color: "var(--c-text-3)" }}>
              Tham số:{" "}
              {Object.entries(step.params).map(([k, v]) => (
                <Tag key={k} style={{ fontSize: 10, marginRight: 4 }}>
                  {k} = {typeof v === "object" ? JSON.stringify(v) : String(v)}
                </Tag>
              ))}
            </div>
          )}
        </div>
      )}

      {open && step.sample.length > 0 && (
        <div style={{ padding: "0 14px 12px 44px" }}>
          <Text type="secondary" style={{ fontSize: 11 }}>
            Kết quả (tối đa 3 mẫu):
          </Text>
          {step.sample.map((s, i) => (
            <div
              key={i}
              style={{
                background: "var(--c-bg-soft)",
                borderRadius: 4,
                padding: "6px 10px",
                fontSize: 11,
                marginTop: 4,
                color: "var(--c-text-2)",
                lineHeight: 1.6,
              }}
            >
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function TraceView({ trace }: { trace: TraceDetail }) {
  const [showPrompt, setShowPrompt] = useState(false);
  const cypherCount = trace.steps.filter((s) => s.kind === "cypher").length;
  const totalRows = trace.steps.reduce((n, s) => n + (s.n_results ?? 0), 0);

  return (
    <div>
      <div
        style={{
          background: "var(--c-bg)",
          border: "1px solid var(--c-fill)",
          borderRadius: 6,
          padding: "14px 16px",
          marginBottom: 16,
        }}
      >
        <div style={{ fontSize: 15, fontWeight: 500, marginBottom: 8 }}>{trace.question}</div>
        <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
          {trace.route && <Tag color="purple">{ROUTE_LABEL[trace.route] ?? trace.route}</Tag>}
          {trace.chapter !== null && trace.chapter !== undefined && (
            <Tag>Chương {trace.chapter}</Tag>
          )}
          <Tag>{cypherCount} truy vấn Cypher</Tag>
          <Tag>{totalRows} bản ghi</Tag>
          {trace.total_ms && <Tag>{Math.round(trace.total_ms)} ms</Tag>}
        </div>
      </div>

      <div style={{ marginBottom: 8, fontSize: 12, color: "var(--c-text-3)" }}>
        Bấm vào từng bước để xem câu Cypher và kết quả.
      </div>

      {trace.steps.map((s, i) => (
        <StepCard key={i} step={s} index={i} />
      ))}

      {trace.prompt && (
        <div style={{ marginTop: 16 }}>
          <Button size="small" onClick={() => setShowPrompt(!showPrompt)}>
            {showPrompt ? "Ẩn" : "Xem"} prompt gửi cho mô hình ({trace.prompt.length.toLocaleString()} ký tự)
          </Button>
          {showPrompt && (
            <pre
              style={{
                background: "var(--c-bg-soft)",
                border: "1px solid var(--c-fill)",
                borderRadius: 4,
                padding: 12,
                fontSize: 11,
                lineHeight: 1.6,
                maxHeight: 400,
                overflow: "auto",
                marginTop: 8,
                whiteSpace: "pre-wrap",
              }}
            >
              {trace.prompt}
            </pre>
          )}
        </div>
      )}

      {trace.answer && (
        <div
          style={{
            marginTop: 16,
            background: "var(--c-bg)",
            border: "1px solid var(--c-fill)",
            borderLeft: "3px solid #fa8c16",
            borderRadius: 6,
            padding: "12px 16px",
          }}
        >
          <Text type="secondary" style={{ fontSize: 11 }}>
            Câu trả lời
          </Text>
          <Paragraph style={{ margin: "6px 0 0", fontSize: 13, whiteSpace: "pre-wrap" }}>
            {trace.answer}
          </Paragraph>
        </div>
      )}
    </div>
  );
}

export default function StoryTrace() {
  const { comicId } = useParams<{ comicId: string }>();
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const traceId = params.get("trace");

  const [list, setList] = useState<TraceSummary[]>([]);
  const [detail, setDetail] = useState<TraceDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadList = () => {
    aiApi
      .traces(Number(comicId))
      .then((r) => setList(r.traces))
      .catch(() => setList([]));
  };

  useEffect(loadList, [comicId]);

  useEffect(() => {
    if (!traceId) {
      setDetail(null);
      return;
    }
    setLoading(true);
    setError(null);
    aiApi
      .trace(traceId)
      .then(setDetail)
      .catch((e) => setError(e instanceof Error ? e.message : "Không tải được trace"))
      .finally(() => setLoading(false));
  }, [traceId]);

  return (
    <div style={{ display: "flex", height: "100%", background: "var(--c-bg-soft)" }}>
      {/* Danh sách các lần chat */}
      <div
        style={{
          width: 260,
          borderRight: "1px solid var(--c-fill)",
          background: "var(--c-bg)",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <div
          style={{
            padding: "12px 14px",
            borderBottom: "1px solid var(--c-fill)",
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
        >
          <Button
            type="text"
            size="small"
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate(`/comics/${comicId}`)}
          />
          <span style={{ fontWeight: 500, fontSize: 13, flex: 1 }}>Quá trình suy luận</span>
          <Tooltip title="Tải lại">
            <Button type="text" size="small" icon={<ReloadOutlined />} onClick={loadList} />
          </Tooltip>
        </div>

        <div style={{ flex: 1, overflowY: "auto" }}>
          {list.length === 0 ? (
            <div style={{ padding: 20 }}>
              <Empty
                imageStyle={{ height: 40 }}
                description={
                  <span style={{ fontSize: 12 }}>
                    Chưa có lần chat nào. Hỏi gì đó trong tab Q&amp;A rồi quay lại.
                  </span>
                }
              />
            </div>
          ) : (
            list.map((t) => (
              <div
                key={t.id}
                onClick={() => setParams({ trace: t.id })}
                style={{
                  padding: "10px 14px",
                  borderBottom: "1px solid var(--c-bg-soft)",
                  cursor: "pointer",
                  background: t.id === traceId ? "var(--c-info-bg)" : undefined,
                }}
              >
                <div
                  style={{
                    fontSize: 12,
                    marginBottom: 4,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                  }}
                >
                  {t.question}
                </div>
                <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                  {t.route && (
                    <Tag color="purple" style={{ fontSize: 10, marginRight: 0, lineHeight: "16px" }}>
                      {ROUTE_LABEL[t.route] ?? t.route}
                    </Tag>
                  )}
                  <Text type="secondary" style={{ fontSize: 10 }}>
                    {t.n_steps} bước
                    {t.total_ms ? ` · ${Math.round(t.total_ms)}ms` : ""}
                  </Text>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chi tiết */}
      <div style={{ flex: 1, overflowY: "auto", padding: 20 }}>
        {loading ? (
          <div style={{ textAlign: "center", paddingTop: 60 }}>
            <Spin />
          </div>
        ) : error ? (
          <Empty description={error} style={{ marginTop: 60 }} />
        ) : detail ? (
          <TraceView trace={detail} />
        ) : (
          <Empty
            description="Chọn một lần chat bên trái để xem hệ thống đã truy vấn những gì."
            style={{ marginTop: 60 }}
          />
        )}
      </div>
    </div>
  );
}
