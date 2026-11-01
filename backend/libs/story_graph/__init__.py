"""Truy hồi ngữ cảnh truyện từ Neo4j cho chat AI.

Đúc kết từ 14 thử nghiệm trong research/ (xem research/notes/). Những lựa chọn
ở đây đều dựa trên số liệu đo được, không phải suy đoán:

  - Vector làm truy hồi chính (0.76 vs BM25 0.53)            research/notes/03
  - KHÔNG hợp nhất RRF — nó kéo 0.76 xuống 0.56              research/notes/04
  - Giới hạn phạm vi chương khi hỏi về 1 chương: 3/7 -> 7/7  research/notes/09
  - Graph facts có from_ch/to_ch giải câu thời gian 17/17    research/notes/14
  - Định tuyến chunk nhỏ theo ý định, không dùng cho mọi câu research/notes/14

Module này chịu lỗi: nếu Neo4j không chạy, `retrieve()` trả ngữ cảnh rỗng và
chat vẫn hoạt động (chỉ mất phần tra cứu truyện).
"""

from .retriever import StoryContext, StoryRetriever, get_retriever

__all__ = ["StoryContext", "StoryRetriever", "get_retriever"]
