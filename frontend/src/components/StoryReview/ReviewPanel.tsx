import { AiApi } from "@/api/ai";
import type { ReviewAspect, ReviewResult } from "@/api/ai";
import { BulbOutlined, WarningOutlined } from "@ant-design/icons";
import { Button, Checkbox, Empty, Segmented, Spin, Tag, Typography } from "antd";
import { useEffect, useState } from "react";

const { Text, Paragraph } = Typography;
const aiApi = new AiApi();

const SCORE_COLOR = ["#cf1322", "#fa8c16", "#faad14", "#52c41a", "#389e0d"];

function ScoreBar({ label, value }: { label: string; value: number }) {
  const v = Math.max(1, Math.min(5, Math.round(value)));
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 6 }}>
      <Text style={{ fontSize: 11, width: 92, color: "#595959" }}>{label}</Text>
      <div style={{ flex: 1, display: "flex", gap: 3 }}>
        {[1, 2, 3, 4, 5].map((i) => (
          <div
            key={i}
            style={{
              flex: 1,
              height: 6,
              borderRadius: 3,
              background: i <= v ? SCORE_COLOR[v - 1] : "#f0f0f0",
            }}
          />
        ))}
      </div>
      <Text style={{ fontSize: 11, width: 16, textAlign: "right" }}>{v}</Text>
    </div>
  );
}

function PointList({
  points,
  kind,
}: {
  points: { point: string; evidence?: string; suggestion?: string }[];
  kind: "strength" | "issue";
}) {
  const isIssue = kind === "issue";
  return (
    <>
      {points.map((p, i) => (
        <div
          key={i}
          style={{
            background: "#fff",
            border: "1px solid #f0f0f0",
            borderLeft: `3px solid ${isIssue ? "#faad14" : "#52c41a"}`,
            borderRadius: 6,
            padding: "10px 12px",
            marginBottom: 8,
          }}
        >
          <div style={{ fontSize: 13, marginBottom: p.evidence || p.suggestion ? 6 : 0 }}>
            {p.point}
          </div>
          {p.evidence && (
            <div
              style={{
                fontSize: 11,
                color: "#595959",
                background: "#fafafa",
                borderRadius: 4,
                padding: "6px 8px",
                lineHeight: 1.6,
              }}
            >
              {p.evidence}
            </div>
          )}
          {p.suggestion && (
            <div style={{ fontSize: 11, color: "#1677ff", marginTop: 6 }}>
              <BulbOutlined /> {p.suggestion}
            </div>
          )}
        </div>
      ))}
    </>
  );
}

export function ReviewPanel({
  comicId,
  chapterNumber,
}: {
  comicId: number;
  chapterNumber?: number;
}) {
  const [scope, setScope] = useState<"chapter" | "story">(
    chapterNumber !== undefined ? "chapter" : "story"
  );
  const [aspectDefs, setAspectDefs] = useState<ReviewAspect[]>([]);
  const [picked, setPicked] = useState<string[]>([]);
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    aiApi
      .reviewAspects()
      .then((r) => {
        setAspectDefs(r.aspects);
        setPicked(r.aspects.map((a) => a.key));
      })
      .catch(() => setAspectDefs([]));
  }, []);

  const run = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const r = await aiApi.review({
        comic_id: comicId,
        chapter: scope === "chapter" ? chapterNumber : undefined,
        aspects: picked.length && picked.length < aspectDefs.length ? picked : undefined,
      });
      setResult(r);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Không đánh giá được");
    } finally {
      setLoading(false);
    }
  };

  const labelOf = (key: string) => aspectDefs.find((a) => a.key === key)?.label ?? key;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#f8f9fa" }}>
      <div style={{ padding: "10px 12px", background: "#fff", borderBottom: "1px solid #f0f0f0" }}>
        <Segmented
          size="small"
          block
          value={scope}
          onChange={(v) => setScope(v as "chapter" | "story")}
          options={[
            {
              label: chapterNumber !== undefined ? `Chương ${chapterNumber}` : "Chương này",
              value: "chapter",
              disabled: chapterNumber === undefined,
            },
            { label: "Toàn truyện", value: "story" },
          ]}
        />

        <div style={{ marginTop: 10, display: "flex", flexWrap: "wrap", gap: 4 }}>
          {aspectDefs.map((a) => (
            <Checkbox
              key={a.key}
              checked={picked.includes(a.key)}
              onChange={(e) =>
                setPicked(
                  e.target.checked
                    ? [...picked, a.key]
                    : picked.filter((k) => k !== a.key)
                )
              }
              style={{ fontSize: 11, marginRight: 8 }}
            >
              <span title={a.guide}>{a.label}</span>
            </Checkbox>
          ))}
        </div>

        <Button
          type="primary"
          size="small"
          block
          style={{ marginTop: 10 }}
          loading={loading}
          disabled={picked.length === 0}
          onClick={run}
        >
          {loading ? "Đang đọc và nhận xét…" : "Đánh giá"}
        </Button>
        {scope === "story" && (
          <Text type="secondary" style={{ fontSize: 10, display: "block", marginTop: 6 }}>
            Đánh giá toàn truyện mất vài phút — đọc số liệu và mạch truyện từng chương.
          </Text>
        )}
      </div>

      <div style={{ flex: 1, overflowY: "auto", padding: 12 }}>
        {loading ? (
          <div style={{ textAlign: "center", paddingTop: 40 }}>
            <Spin />
            <div style={{ marginTop: 10, fontSize: 12, color: "#8c8c8c" }}>
              Đang phân tích…
            </div>
          </div>
        ) : error ? (
          <Empty description={<span style={{ fontSize: 12 }}>{error}</span>} imageStyle={{ height: 40 }} />
        ) : !result ? (
          <Empty
            imageStyle={{ height: 40 }}
            description={
              <span style={{ fontSize: 12 }}>
                Chọn phạm vi và khía cạnh rồi bấm Đánh giá. Mỗi nhận xét sẽ kèm dẫn chứng [ch.N].
              </span>
            }
          />
        ) : (
          <>
            {result.truncated && (
              <div
                style={{
                  background: "#fffbe6",
                  border: "1px solid #ffe58f",
                  borderRadius: 4,
                  padding: "6px 10px",
                  fontSize: 11,
                  marginBottom: 10,
                }}
              >
                Mô hình trả lời dài quá nên phần cuối bị cắt — nội dung dưới đây chưa đầy đủ.
              </div>
            )}

            {result.summary && (
              <Paragraph style={{ fontSize: 13, lineHeight: 1.7, marginBottom: 14 }}>
                {result.summary}
              </Paragraph>
            )}

            {result.score && Object.keys(result.score).length > 0 && (
              <div
                style={{
                  background: "#fff",
                  border: "1px solid #f0f0f0",
                  borderRadius: 6,
                  padding: "12px 14px",
                  marginBottom: 14,
                }}
              >
                {Object.entries(result.score).map(([k, v]) => (
                  <ScoreBar key={k} label={labelOf(k)} value={Number(v)} />
                ))}
              </div>
            )}

            {result.stats && (
              <div style={{ marginBottom: 14, display: "flex", gap: 4, flexWrap: "wrap" }}>
                <Tag>{result.stats.n_chapters} chương</Tag>
                <Tag>{result.stats.total_chars.toLocaleString()} ký tự</Tag>
                <Tag>TB {result.stats.avg_chars.toLocaleString()}/chương</Tag>
                {result.stats.outliers_long.length > 0 && (
                  <Tag color="orange">
                    {result.stats.outliers_long.length} chương dài bất thường
                  </Tag>
                )}
              </div>
            )}

            {result.strengths.length > 0 && (
              <>
                <Text strong style={{ fontSize: 12, color: "#389e0d" }}>
                  Điểm mạnh
                </Text>
                <div style={{ marginTop: 8, marginBottom: 14 }}>
                  <PointList points={result.strengths} kind="strength" />
                </div>
              </>
            )}

            {result.issues.length > 0 && (
              <>
                <Text strong style={{ fontSize: 12, color: "#d46b08" }}>
                  <WarningOutlined /> Cần xem lại
                </Text>
                <div style={{ marginTop: 8 }}>
                  <PointList points={result.issues} kind="issue" />
                </div>
              </>
            )}

            {result.strengths.length === 0 && result.issues.length === 0 && !result.summary && (
              <Empty
                imageStyle={{ height: 40 }}
                description={<span style={{ fontSize: 12 }}>Mô hình không đưa ra nhận xét nào.</span>}
              />
            )}
          </>
        )}
      </div>
    </div>
  );
}
